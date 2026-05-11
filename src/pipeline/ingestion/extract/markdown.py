from __future__ import annotations

from pathlib import Path

from pipeline.ingestion.extract.models import (
    ExtractedTable,
    LayoutBlock,
    RawPageMarkdown,
    VisionPlaceholder,
)


def _format_bbox(bbox: tuple[float, float, float, float]) -> str:
    return ",".join(f"{value:.2f}" for value in bbox)


def _render_table(table: ExtractedTable) -> list[str]:
    lines = [
        f"<!-- table: {table.index} source={table.source} -->",
    ]
    if not table.rows:
        lines.append("(empty table)")
        return lines

    header = table.rows[0]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in table.rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def render_raw_page_markdown(page: RawPageMarkdown, source_pdf: Path) -> str:
    lines = [
        "---",
        f"page: {page.page_number}",
        f"page_type: {page.page_type}",
        f"source_pdf: {source_pdf.name}",
        "stage: raw_markdown",
        f"recommended_backends: {', '.join(page.recommended_backends) or 'none'}",
        "---",
        "",
        f"<!-- page: {page.page_number} -->",
        f"<!-- page_type: {page.page_type} -->",
    ]
    if page.flags:
        lines.append(f"<!-- flags: {', '.join(page.flags)} -->")
    lines.append("")

    for block in page.blocks:
        lines.append(
            f"<!-- block: {block.index} region={block.region} "
            f"bbox={_format_bbox(block.bbox)} -->"
        )
        if block.bilingual_pairs:
            lines.append("<!-- bilingual_terms -->")
            for arabic, english in block.bilingual_pairs:
                lines.append(f"- {arabic} | {english}")
            lines.append("")
        lines.extend(block.lines)
        lines.append("")

    for table in page.tables:
        lines.extend(_render_table(table))
        lines.append("")

    for placeholder in page.vision_placeholders:
        lines.append(
            f"<!-- vision_ocr_pending: image={placeholder.index} "
            f"bbox={_format_bbox(placeholder.bbox)} reason={placeholder.reason} -->"
        )
    lines.append("")

    if page.notes:
        lines.append("<!-- extraction_notes -->")
        lines.extend(f"- {note}" for note in page.notes)
        lines.append("")

    return "\n".join(lines).strip() + "\n"
