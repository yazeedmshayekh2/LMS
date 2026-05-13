from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from ai.llms.config import PROVIDER_DEFAULTS
from pipeline.ingestion.config import IngestionConfig
from pipeline.ingestion.extract.io import load_extract_report
from pipeline.ingestion.normalize.llm import (
    create_normalizer_llm,
    provider_from_name,
    provider_is_configured,
)
from pipeline.ingestion.normalize.reader_export import (
    export_readable_document,
    strip_chunk_frontmatter,
)
from pipeline.ingestion.normalize.readable_postprocess import (
    parse_batch_id,
    postprocess_readable_markdown,
)
from pipeline.ingestion.normalize.toc import build_outline, render_outline_context

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ReadableExportReport:
    section_count: int
    document_path: Path
    section_paths: list[Path]
    dry_run: bool
    provider: str
    model: str


def _page_types_for_range(
    pages_by_number: dict[int, str],
    page_start: int,
    page_end: int,
) -> list[str]:
    return [
        pages_by_number.get(page_number, "unknown")
        for page_number in range(page_start, page_end + 1)
    ]


def _load_outline_context(config: IngestionConfig) -> str:
    report_path = config.normalized_markdown_dir / "normalize_report.json"
    if report_path.is_file():
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        entries = payload.get("outline", {}).get("entries", [])
        if entries:
            from pipeline.ingestion.normalize.models import BookOutline, TocEntry

            outline = BookOutline(
                book_title=payload.get("outline", {}).get("book_title", "علوم"),
                grade=payload.get("outline", {}).get("grade"),
                semester=payload.get("outline", {}).get("semester"),
                entries=[TocEntry(**entry) for entry in entries],
            )
            return render_outline_context(outline)

    if not config.extract_report_path.is_file():
        return "Outline unavailable."

    extract_report = load_extract_report(config.extract_report_path)
    pages = extract_report.pages
    if config.max_pages is not None:
        pages = [page for page in pages if page.page_number <= config.max_pages]
    return render_outline_context(build_outline(pages))


def run_readable_export(
    config: IngestionConfig,
    *,
    provider_name: str,
    model: str | None = None,
    dry_run: bool = False,
) -> ReadableExportReport:
    sections_dir = config.normalized_sections_dir
    if not sections_dir.is_dir():
        raise FileNotFoundError(
            f"Normalized sections not found: {sections_dir}. Run the normalize stage first."
        )

    readable_sections_dir = config.normalized_markdown_dir / "readable" / "sections"
    readable_sections_dir.mkdir(parents=True, exist_ok=True)

    pages_by_number: dict[int, str] = {}
    if config.extract_report_path.is_file():
        extract_report = load_extract_report(config.extract_report_path)
        pages_by_number = {
            page.page_number: page.page_type for page in extract_report.pages
        }

    outline_context = _load_outline_context(config)
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

    section_paths: list[Path] = []
    for source in sorted(sections_dir.glob("p*.md")):
        if source.name.endswith(".prompt.md"):
            continue

        batch_id = source.stem
        page_start, page_end = parse_batch_id(batch_id)
        stripped = strip_chunk_frontmatter(source.read_text(encoding="utf-8"))
        page_types = _page_types_for_range(pages_by_number, page_start, page_end)

        if use_dry_run:
            readable = stripped
            prompt_path = readable_sections_dir / f"{batch_id}.prompt.md"
            from pipeline.ingestion.normalize.readable_prompts import (
                build_readable_system_prompt,
                build_readable_user_prompt,
            )

            prompt_path.write_text(
                build_readable_system_prompt()
                + "\n\n"
                + build_readable_user_prompt(
                    page_start=page_start,
                    page_end=page_end,
                    page_types=page_types,
                    outline_context=outline_context,
                    markdown=stripped,
                )
                + "\n",
                encoding="utf-8",
            )
        else:
            assert llm is not None
            logger.info(
                "Postprocessing readable section %s (pages %s-%s)",
                batch_id,
                page_start,
                page_end,
            )
            readable = postprocess_readable_markdown(
                llm,
                page_start=page_start,
                page_end=page_end,
                page_types=page_types,
                outline_context=outline_context,
                markdown=stripped,
            )

        target = readable_sections_dir / source.name
        target.write_text(readable.strip() + "\n", encoding="utf-8")
        section_paths.append(target)

    document_path = export_readable_document(
        readable_sections_dir,
        output_path=config.normalized_markdown_dir / "readable" / "document.md",
    )

    return ReadableExportReport(
        section_count=len(section_paths),
        document_path=document_path,
        section_paths=section_paths,
        dry_run=use_dry_run,
        provider=provider.value,
        model=resolved_model,
    )
