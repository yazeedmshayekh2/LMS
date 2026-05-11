from __future__ import annotations

import json
from pathlib import Path

from pipeline.ingestion.models import BackendExtraction, PageProfile, PreprocessReport


def write_json_report(report: PreprocessReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_page_profile(profile: PageProfile, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(profile.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_backend_preview(
    backend: str,
    page_number: int,
    extraction: BackendExtraction,
    path: Path,
) -> None:
    lines = [
        f"backend: {backend}",
        f"page: {page_number}",
        f"ok: {extraction.ok}",
        f"quality_score: {extraction.quality_score}",
        f"char_count: {extraction.char_count}",
    ]
    note = extraction.extra.get("note")
    if note:
        lines.append(f"note: {note}")
    lines.extend(["", extraction.text, ""])
    if extraction.error:
        lines.insert(4, f"error: {extraction.error}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary_markdown(report: PreprocessReport, path: Path) -> None:
    lines = [
        "# PDF preprocessing summary",
        "",
        f"- Source: `{report.source_pdf}`",
        f"- Written: {report.written_at}",
        f"- Pages in document: {report.page_count}",
        f"- Pages processed: {report.processed_pages}",
        "",
        "## Backend summary",
        "",
    ]

    for backend, stats in report.backend_summary.items():
        lines.append(f"### {backend}")
        for key, value in stats.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    lines.extend(["## Page profiles", ""])
    for page in report.pages:
        backend_scores = ", ".join(
            f"{item.backend}={item.quality_score:.2f}" for item in page.backends
        )
        recommended = ", ".join(page.recommended_backends) or "none"
        lines.extend(
            [
                f"### Page {page.page_number} — {page.page_type}",
                f"- Confidence: {page.classification_confidence}",
                f"- Reasons: {', '.join(page.classification_reasons) or 'n/a'}",
                f"- Layout: {page.layout.text_block_count} text blocks, "
                f"{page.layout.table_count} tables, "
                f"{page.layout.image_block_count} image blocks",
                f"- Backend scores: {backend_scores}",
                f"- Recommended: {recommended}",
                f"- Flags: {', '.join(page.flags) or 'none'}",
                "",
            ]
        )

    if report.docling_markdown_path:
        lines.extend(
            [
                "## Docling",
                "",
                f"Markdown export: `{report.docling_markdown_path}`",
                "",
            ]
        )

    if report.notes:
        lines.extend(["## Notes", ""])
        lines.extend(f"- {note}" for note in report.notes)
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
