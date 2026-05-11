from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from pipeline.ingestion.backends.docling import extract_docling_markdown
from pipeline.ingestion.backends.pymupdf import (
    extract_page_image_blocks,
    extract_page_layout_blocks,
)
from pipeline.ingestion.config import IngestionConfig
from pipeline.ingestion.extract.bilingual import extract_bilingual_pairs
from pipeline.ingestion.extract.load_preprocess import resolve_page_profiles
from pipeline.ingestion.extract.markdown import render_raw_page_markdown
from pipeline.ingestion.extract.models import (
    BlockRegion,
    ExtractReport,
    LayoutBlock,
    RawPageMarkdown,
)
from pipeline.ingestion.extract.regions import classify_block_region
from pipeline.ingestion.extract.tables import extract_page_tables
from pipeline.ingestion.extract.vision import build_vision_placeholders
from pipeline.ingestion.models import PageProfile, PageType
from pipeline.ingestion.preprocess.pipeline import _document_metadata

logger = logging.getLogger(__name__)


def _extract_page(
    pdf_path: Path,
    profile: PageProfile,
    *,
    include_docling: bool,
) -> RawPageMarkdown:
    layout_blocks = extract_page_layout_blocks(pdf_path, profile.page_number)
    image_blocks = extract_page_image_blocks(pdf_path, profile.page_number)
    tables = extract_page_tables(
        pdf_path,
        profile.page_number,
        page_type=profile.page_type,
    )

    blocks: list[LayoutBlock] = []
    for layout_block in layout_blocks:
        region = classify_block_region(
            page_type=profile.page_type,
            bbox=layout_block.bbox,
            page_width=profile.geometry.width_pt,
            page_height=profile.geometry.height_pt,
            max_font_size=layout_block.max_font_size,
            median_font_size=profile.layout.median_font_size_pt,
            line_count=len(layout_block.lines),
        )
        bilingual_pairs = extract_bilingual_pairs(layout_block.lines)
        if (
            bilingual_pairs
            and profile.page_type in {PageType.LESSON, PageType.GLOSSARY}
            and (
                region == BlockRegion.SIDEBAR
                or len(bilingual_pairs) >= max(2, len(layout_block.lines) // 2)
            )
        ):
            region = BlockRegion.TERMS

        blocks.append(
            LayoutBlock(
                index=layout_block.index,
                region=region,
                bbox=layout_block.bbox,
                lines=layout_block.lines,
                bilingual_pairs=bilingual_pairs,
            )
        )

    vision_placeholders = build_vision_placeholders(profile, image_blocks)
    notes: list[str] = []
    if profile.page_type == PageType.TOC:
        notes.append("TOC tables extracted on a dedicated table path.")
    if vision_placeholders:
        notes.append(
            "Vision OCR placeholders emitted for image-heavy regions; "
            "text layer retained for body copy."
        )
    if include_docling and profile.page_type == PageType.TOC:
        notes.append("Docling appendix attached at document level when enabled.")

    page = RawPageMarkdown(
        page_number=profile.page_number,
        page_type=profile.page_type.value,
        recommended_backends=profile.recommended_backends,
        flags=profile.flags,
        blocks=blocks,
        tables=tables,
        vision_placeholders=vision_placeholders,
        markdown="",
        notes=notes,
    )
    page.markdown = render_raw_page_markdown(page, pdf_path)
    return page


def run_extraction(config: IngestionConfig) -> ExtractReport:
    if not config.pdf_path.is_file():
        raise FileNotFoundError(config.pdf_path)

    config.ensure_raw_markdown_dirs()
    metadata = _document_metadata(config.pdf_path)
    page_count = int(metadata["page_count"])
    last_page = page_count if config.max_pages is None else min(page_count, config.max_pages)
    profiles = resolve_page_profiles(config, last_page=last_page)

    logger.info(
        "Stage 2 extraction: %s (pages 1-%s of %s)",
        config.pdf_path.name,
        last_page,
        page_count,
    )

    pages: list[RawPageMarkdown] = []
    for page_number in range(1, last_page + 1):
        logger.info("Extracting page %s/%s", page_number, last_page)
        profile = profiles[page_number]
        page = _extract_page(
            config.pdf_path,
            profile,
            include_docling=config.extract_include_docling,
        )
        pages.append(page)
        page_path = config.raw_markdown_pages_dir / f"page_{page_number:03d}.md"
        page_path.write_text(page.markdown, encoding="utf-8")

    document_markdown_path = config.raw_markdown_dir / "document.md"
    document_lines = [page.markdown for page in pages]
    if config.extract_include_docling:
        logger.info("Running Docling appendix for pages 1-%s", last_page)
        try:
            docling_markdown = extract_docling_markdown(
                config.pdf_path,
                first_page=1,
                last_page=last_page,
            )
            document_lines.extend(
                [
                    "",
                    "<!-- docling_appendix: layout_reference_only -->",
                    docling_markdown,
                    "",
                ]
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Docling appendix failed: %s", exc)

    document_markdown_path.write_text("\n".join(document_lines), encoding="utf-8")

    preprocess_report = (
        str(config.preprocess_report_path)
        if config.preprocess_report_path.is_file()
        else None
    )
    report = ExtractReport(
        source_pdf=str(config.pdf_path),
        preprocess_report=preprocess_report,
        written_at=datetime.now(timezone.utc).isoformat(),
        page_count=page_count,
        processed_pages=last_page,
        pages=pages,
        document_markdown_path=str(document_markdown_path),
        notes=[
            "Hybrid extraction: PyMuPDF layout blocks + dedicated table path.",
            "No full-book OCR in this stage.",
        ],
    )
    report_path = config.raw_markdown_dir / "extract_report.json"
    report_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report
