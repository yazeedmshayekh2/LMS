from __future__ import annotations

import json
from pathlib import Path

from pipeline.ingestion.extract.models import (
    ExtractReport,
    ExtractedTable,
    LayoutBlock,
    RawPageMarkdown,
    VisionPlaceholder,
)
from pipeline.ingestion.extract.models import BlockRegion


def _layout_block(data: dict) -> LayoutBlock:
    return LayoutBlock(
        index=data["index"],
        region=BlockRegion(data["region"]),
        bbox=tuple(data["bbox"]),
        lines=data["lines"],
        bilingual_pairs=[tuple(pair) for pair in data.get("bilingual_pairs", [])],
    )


def _raw_page(data: dict) -> RawPageMarkdown:
    return RawPageMarkdown(
        page_number=data["page_number"],
        page_type=data["page_type"],
        recommended_backends=data["recommended_backends"],
        flags=data.get("flags", []),
        blocks=[_layout_block(item) for item in data["blocks"]],
        tables=[
            ExtractedTable(index=item["index"], source=item["source"], rows=item["rows"])
            for item in data["tables"]
        ],
        vision_placeholders=[
            VisionPlaceholder(
                index=item["index"],
                bbox=tuple(item["bbox"]),
                reason=item["reason"],
            )
            for item in data["vision_placeholders"]
        ],
        markdown=data["markdown"],
        notes=data.get("notes", []),
    )


def load_extract_report(path: Path) -> ExtractReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pages = [_raw_page(item) for item in payload["pages"]]
    return ExtractReport(
        source_pdf=payload["source_pdf"],
        preprocess_report=payload.get("preprocess_report"),
        written_at=payload["written_at"],
        page_count=payload["page_count"],
        processed_pages=payload["processed_pages"],
        pages=pages,
        document_markdown_path=payload["document_markdown_path"],
        notes=payload.get("notes", []),
    )
