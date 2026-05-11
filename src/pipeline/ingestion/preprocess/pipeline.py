from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.ingestion.backends.docling import extract_docling_markdown
from pipeline.ingestion.backends.pdfplumber import extract_pdfplumber_page
from pipeline.ingestion.backends.pymupdf import (
    extract_pymupdf_page,
    extract_pymupdf_structure,
    page_geometry,
    render_pymupdf_structure_text,
)
from pipeline.ingestion.backends.pypdf import extract_pypdf_page
from pipeline.ingestion.config import IngestionConfig
from pipeline.ingestion.models import (
    BackendExtraction,
    LayoutSignals,
    PageGeometry,
    PageProfile,
    PreprocessReport,
)
from pipeline.ingestion.preprocess.classify import classify_page
from pipeline.ingestion.preprocess.reporting import (
    write_backend_preview,
    write_json_report,
    write_page_profile,
    write_summary_markdown,
)
from pipeline.ingestion.text_utils import (
    analyze_text,
    format_extracted_text,
    quality_score,
    similarity,
)

logger = logging.getLogger(__name__)


def _document_metadata(pdf_path: Path) -> dict[str, Any]:
    import fitz

    with fitz.open(pdf_path) as doc:
        metadata = doc.metadata or {}
        return {
            "page_count": doc.page_count,
            "title": metadata.get("title") or "",
            "author": metadata.get("author") or "",
            "subject": metadata.get("subject") or "",
            "creator": metadata.get("creator") or "",
            "producer": metadata.get("producer") or "",
            "format": metadata.get("format") or "",
        }


def _backend_extraction(
    backend: str,
    text: str,
    *,
    reference: str | None,
    preview_chars: int | None,
    rtl_penalty: float = 0.0,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> BackendExtraction:
    if error is not None:
        return BackendExtraction(
            backend=backend,
            ok=False,
            char_count=0,
            text_signals=None,
            text="",
            quality_score=0.0,
            error=error,
            extra=extra or {},
        )

    signals = analyze_text(text)
    return BackendExtraction(
        backend=backend,
        ok=True,
        char_count=signals.char_count,
        text_signals=signals,
        text=format_extracted_text(text, preview_chars),
        quality_score=quality_score(
            text,
            reference=reference,
            rtl_penalty=rtl_penalty,
        ),
        extra=extra or {},
    )


def _recommend_backends(
    page_type: str,
    backends: list[BackendExtraction],
    *,
    table_count: int,
    flags: list[str],
) -> list[str]:
    ranked = sorted(
        [item for item in backends if item.ok],
        key=lambda item: item.quality_score,
        reverse=True,
    )
    if not ranked:
        return []

    recommendations: list[str] = []
    for item in ranked:
        if item.backend not in recommendations:
            recommendations.append(item.backend)

    if (
        table_count > 0
        and "pdfplumber" in recommendations
        and "pdfplumber_rtl_suspect" not in flags
    ):
        recommendations = ["pdfplumber", *[
            name for name in recommendations if name != "pdfplumber"
        ]]
    if "pdfplumber_rtl_suspect" in flags and "pdfplumber" in recommendations:
        recommendations = [
            name for name in recommendations if name != "pdfplumber"
        ] + ["pdfplumber"]
    if page_type in {"toc", "lesson", "inquiry", "enrichment"} and "pymupdf" in recommendations:
        recommendations = ["pymupdf", *[
            name for name in recommendations if name != "pymupdf"
        ]]

    return recommendations[:3]


def _profile_page(
    pdf_path: Path,
    page_number: int,
    config: IngestionConfig,
) -> PageProfile:
    geometry_data = page_geometry(pdf_path, page_number)
    geometry = PageGeometry(
        width_pt=geometry_data["width_pt"],
        height_pt=geometry_data["height_pt"],
        rotation=geometry_data["rotation"],
        mediabox=geometry_data["mediabox"],
    )

    structure = extract_pymupdf_structure(pdf_path, page_number)
    layout = LayoutSignals(
        text_block_count=structure.text_block_count,
        non_text_block_count=structure.non_text_block_count,
        image_block_count=structure.image_block_count,
        table_count=structure.table_count,
        line_count=structure.line_count,
        span_count=structure.span_count,
        unique_fonts=structure.unique_fonts,
        median_font_size_pt=structure.median_font_size_pt,
    )

    backends: list[BackendExtraction] = []
    flags: list[str] = []
    reference_text = ""

    if config.include_pymupdf:
        try:
            reference_text = extract_pymupdf_page(pdf_path, page_number)
            backends.append(
                _backend_extraction(
                    "pymupdf",
                    reference_text,
                    reference=reference_text,
                    preview_chars=config.preview_chars,
                    extra={
                        "extraction_mode": "dict_blocks_sorted_top_to_bottom_rtl",
                        "structure": {
                            "table_count": structure.table_count,
                            "text_block_count": structure.text_block_count,
                        },
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            backends.append(
                _backend_extraction(
                    "pymupdf",
                    "",
                    reference=None,
                    preview_chars=config.preview_chars,
                    error=repr(exc),
                )
            )

    if config.include_pypdf:
        try:
            pypdf_text = extract_pypdf_page(pdf_path, page_number)
            backends.append(
                _backend_extraction(
                    "pypdf",
                    pypdf_text,
                    reference=reference_text or None,
                    preview_chars=config.preview_chars,
                )
            )
        except Exception as exc:  # noqa: BLE001
            backends.append(
                _backend_extraction(
                    "pypdf",
                    "",
                    reference=None,
                    preview_chars=config.preview_chars,
                    error=repr(exc),
                )
            )

    if config.include_pdfplumber:
        try:
            pdfplumber_text, pdfplumber_tables = extract_pdfplumber_page(
                pdf_path,
                page_number,
            )
            rtl_penalty = 0.0
            if reference_text and similarity(reference_text, pdfplumber_text) < 0.35:
                rtl_penalty = 0.35
                flags.append("pdfplumber_rtl_suspect")
            pdfplumber_extra: dict[str, Any] = {"table_count": len(pdfplumber_tables)}
            if rtl_penalty:
                pdfplumber_extra["note"] = (
                    "Arabic often appears reversed in pdfplumber output; "
                    "use PyMuPDF for readable Arabic prose."
                )
            backends.append(
                _backend_extraction(
                    "pdfplumber",
                    pdfplumber_text,
                    reference=reference_text or None,
                    preview_chars=config.preview_chars,
                    rtl_penalty=rtl_penalty,
                    extra=pdfplumber_extra,
                )
            )
        except Exception as exc:  # noqa: BLE001
            backends.append(
                _backend_extraction(
                    "pdfplumber",
                    "",
                    reference=None,
                    preview_chars=config.preview_chars,
                    error=repr(exc),
                )
            )

    if config.include_structure:
        structure_text = render_pymupdf_structure_text(pdf_path, page_number)
        backends.append(
            _backend_extraction(
                "pymupdf_structure",
                structure_text,
                reference=None,
                preview_chars=config.preview_chars,
                extra={
                    "text_block_count": structure.text_block_count,
                    "image_block_count": structure.image_block_count,
                    "table_count": structure.table_count,
                    "unique_fonts": structure.unique_fonts[:8],
                    "median_font_size_pt": structure.median_font_size_pt,
                    "tables": structure.tables,
                },
            )
        )

    primary_text = reference_text
    if not primary_text:
        for item in backends:
            if item.ok and item.text:
                primary_text = item.text
                break

    page_type, confidence, reasons = classify_page(
        page_number,
        primary_text,
        table_count=layout.table_count,
        image_block_count=layout.image_block_count,
    )
    primary_signals = analyze_text(primary_text)

    if layout.table_count > 0:
        flags.append("has_tables")
    if layout.image_block_count > 0:
        flags.append("has_images")
    if primary_signals.replacement_char_count > 0:
        flags.append("replacement_chars_present")

    recommended = _recommend_backends(
        page_type.value,
        backends,
        table_count=layout.table_count,
        flags=flags,
    )

    return PageProfile(
        page_number=page_number,
        page_type=page_type,
        classification_confidence=confidence,
        classification_reasons=reasons,
        geometry=geometry,
        layout=layout,
        primary_text_signals=primary_signals,
        backends=backends,
        recommended_backends=recommended,
        flags=flags,
    )


def _summarize_backends(pages: list[PageProfile]) -> dict[str, Any]:
    summary: dict[str, Any] = defaultdict(
        lambda: {
            "pages_attempted": 0,
            "pages_ok": 0,
            "avg_quality_score": 0.0,
            "avg_char_count": 0.0,
        }
    )
    for page in pages:
        for backend in page.backends:
            bucket = summary[backend.backend]
            bucket["pages_attempted"] += 1
            if backend.ok:
                bucket["pages_ok"] += 1
                bucket["avg_quality_score"] += backend.quality_score
                bucket["avg_char_count"] += backend.char_count

    for backend, bucket in summary.items():
        ok_pages = bucket["pages_ok"] or 1
        bucket["avg_quality_score"] = round(bucket["avg_quality_score"] / ok_pages, 4)
        bucket["avg_char_count"] = round(bucket["avg_char_count"] / ok_pages, 2)

    return dict(summary)


def run_preprocessing(config: IngestionConfig) -> PreprocessReport:
    if not config.pdf_path.is_file():
        raise FileNotFoundError(config.pdf_path)

    config.ensure_output_dirs()
    metadata = _document_metadata(config.pdf_path)
    page_count = int(metadata["page_count"])
    last_page = page_count if config.max_pages is None else min(page_count, config.max_pages)

    logger.info(
        "Preprocessing %s (pages 1-%s of %s)",
        config.pdf_path.name,
        last_page,
        page_count,
    )

    pages: list[PageProfile] = []
    for page_number in range(1, last_page + 1):
        logger.info("Profiling page %s/%s", page_number, last_page)
        profile = _profile_page(config.pdf_path, page_number, config)
        pages.append(profile)

        page_path = config.pages_dir / f"page_{page_number:03d}.json"
        write_page_profile(profile, page_path)
        for backend in profile.backends:
            preview_path = (
                config.backends_dir
                / backend.backend
                / f"page_{page_number:03d}.txt"
            )
            preview_path.parent.mkdir(parents=True, exist_ok=True)
            write_backend_preview(backend.backend, page_number, backend, preview_path)

    docling_markdown_path: str | None = None
    notes: list[str] = []
    if config.include_docling:
        logger.info("Running Docling for pages 1-%s", last_page)
        try:
            markdown = extract_docling_markdown(
                config.pdf_path,
                first_page=1,
                last_page=last_page,
            )
            docling_path = config.backends_dir / "docling" / "document.md"
            docling_path.parent.mkdir(parents=True, exist_ok=True)
            docling_path.write_text(markdown + "\n", encoding="utf-8")
            docling_markdown_path = str(docling_path)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"Docling failed: {exc!r}")

    report = PreprocessReport(
        source_pdf=str(config.pdf_path),
        written_at=datetime.now(timezone.utc).isoformat(),
        page_count=page_count,
        processed_pages=last_page,
        document_metadata=metadata,
        backend_summary=_summarize_backends(pages),
        pages=pages,
        docling_markdown_path=docling_markdown_path,
        notes=notes,
    )

    write_json_report(report, config.output_dir / "preprocess_report.json")
    write_summary_markdown(report, config.output_dir / "preprocess_summary.md")
    return report
