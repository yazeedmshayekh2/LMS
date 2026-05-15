from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from ai.llms.config import PROVIDER_DEFAULTS
from pipeline.ingestion.config import IngestionConfig
from pipeline.ingestion.extract.io import load_extract_report
from pipeline.ingestion.normalize.batching import build_batches
from pipeline.ingestion.normalize.toc import build_outline
from pipeline.ingestion.normalize.llm import (
    create_normalizer_llm,
    normalize_batch_markdown,
    provider_from_name,
    provider_is_configured,
)
from pipeline.ingestion.normalize.models import NormalizedSection, NormalizeReport
from pipeline.ingestion.normalize.prompts import build_system_prompt, build_user_prompt
from pipeline.ingestion.normalize.validate import load_reference_text, validate_normalized_markdown

logger = logging.getLogger(__name__)


def _dry_run_markdown(batch_id: str, page_start: int, page_end: int) -> str:
    return (
        "---\n"
        "book_title: علوم\n"
        "grade: 8\n"
        "semester: 1\n"
        "subject: science\n"
        "unit_no: null\n"
        "unit_title: null\n"
        "lesson_no: null\n"
        "lesson_title: null\n"
        "content_kind: front_matter\n"
        f"page_start: {page_start}\n"
        f"page_end: {page_end}\n"
        "heading_path: []\n"
        f"chunk_id: {batch_id}-pending\n"
        "---\n\n"
        "<!-- normalization_pending: dry_run -->\n"
    )


def run_normalization(
    config: IngestionConfig,
    *,
    provider_name: str,
    model: str | None = None,
    dry_run: bool = False,
) -> NormalizeReport:
    if not config.extract_report_path.is_file():
        raise FileNotFoundError(
            f"Stage-2 extract report not found: {config.extract_report_path}"
        )

    config.ensure_normalized_dirs()
    extract_report = load_extract_report(config.extract_report_path)
    pages = extract_report.pages
    if config.max_pages is not None:
        pages = [page for page in pages if page.page_number <= config.max_pages]

    outline = build_outline(pages)
    batches = build_batches(pages, outline, batch_size=config.normalize_batch_size)

    provider = provider_from_name(provider_name)
    use_dry_run = dry_run or not provider_is_configured(provider)
    llm = None
    resolved_model = model or PROVIDER_DEFAULTS[provider]["model"]
    if not use_dry_run:
        llm, provider, resolved_model = create_normalizer_llm(
            provider_name,
            model=model,
            temperature=0.0,
        )

    logger.info(
        "Stage 3 normalization: %s batch(es), provider=%s, dry_run=%s",
        len(batches),
        provider.value,
        use_dry_run,
    )

    sections: list[NormalizedSection] = []
    document_parts: list[str] = []
    for batch in batches:
        prompt_path = config.normalized_sections_dir / f"{batch.batch_id}.prompt.md"
        prompt_path.write_text(
            build_system_prompt() + "\n\n" + build_user_prompt(batch) + "\n",
            encoding="utf-8",
        )

        if use_dry_run:
            markdown = _dry_run_markdown(batch.batch_id, batch.page_start, batch.page_end)
        else:
            assert llm is not None
            logger.info(
                "Normalizing batch %s (pages %s-%s)",
                batch.batch_id,
                batch.page_start,
                batch.page_end,
            )
            markdown = normalize_batch_markdown(llm, batch)

        reference_parts = [
            load_reference_text(config.output_dir, page_number)
            for page_number in range(batch.page_start, batch.page_end + 1)
        ]
        reference_text = "\n\n".join(part for part in reference_parts if part)
        validation = validate_normalized_markdown(
            markdown,
            reference_text=reference_text or None,
        )
        if use_dry_run:
            validation.warnings.append("Normalization ran in dry-run mode.")

        section_path = config.normalized_sections_dir / f"{batch.batch_id}.md"
        section_path.write_text(markdown, encoding="utf-8")
        document_parts.append(markdown)

        sections.append(
            NormalizedSection(
                batch_id=batch.batch_id,
                page_start=batch.page_start,
                page_end=batch.page_end,
                markdown=markdown,
                validation=validation,
                prompt_path=str(prompt_path),
                provider=provider.value,
                model=resolved_model,
            )
        )

    document_path = config.normalized_markdown_dir / "document.md"
    document_path.write_text("\n\n".join(document_parts) + "\n", encoding="utf-8")

    qc_report_path = config.normalized_markdown_dir / "qc_report.json"
    qc_payload = {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider.value,
        "model": resolved_model,
        "dry_run": use_dry_run,
        "sections": [section.to_dict() for section in sections],
    }
    qc_report_path.write_text(
        json.dumps(qc_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    notes = [
        "Schema-first normalization with TOC outline context.",
        "QC tracks frontmatter completeness, heading depth, and approximate CER vs PyMuPDF reference.",
        "Run the readable stage for body-only LLM postprocessed export.",
    ]
    if use_dry_run:
        notes.append("Dry-run mode wrote prompts and placeholder normalized sections.")

    report = NormalizeReport(
        source_extract_report=str(config.extract_report_path),
        written_at=datetime.now(timezone.utc).isoformat(),
        processed_pages=max(page.page_number for page in pages) if pages else 0,
        provider=provider.value,
        model=resolved_model,
        dry_run=use_dry_run,
        outline=outline,
        sections=sections,
        document_markdown_path=str(document_path),
        qc_report_path=str(qc_report_path),
        notes=notes,
    )
    report_path = config.normalized_markdown_dir / "normalize_report.json"
    report_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report
