from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class BlockRegion(StrEnum):
    MAIN = "main"
    SIDEBAR = "sidebar"
    HEADER = "header"
    FOOTER = "footer"
    CAPTION = "caption"
    FRONT_MATTER = "front_matter"
    TERMS = "terms"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class LayoutBlock:
    index: int
    region: BlockRegion
    bbox: tuple[float, float, float, float]
    lines: list[str]
    bilingual_pairs: list[tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExtractedTable:
    index: int
    source: str
    rows: list[list[str]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VisionPlaceholder:
    index: int
    bbox: tuple[float, float, float, float]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RawPageMarkdown:
    page_number: int
    page_type: str
    recommended_backends: list[str]
    flags: list[str]
    blocks: list[LayoutBlock]
    tables: list[ExtractedTable]
    vision_placeholders: list[VisionPlaceholder]
    markdown: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blocks"] = [block.to_dict() for block in self.blocks]
        payload["tables"] = [table.to_dict() for table in self.tables]
        payload["vision_placeholders"] = [
            placeholder.to_dict() for placeholder in self.vision_placeholders
        ]
        return payload


@dataclass(slots=True)
class ExtractReport:
    source_pdf: str
    preprocess_report: str | None
    written_at: str
    page_count: int
    processed_pages: int
    pages: list[RawPageMarkdown]
    document_markdown_path: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_pdf": self.source_pdf,
            "preprocess_report": self.preprocess_report,
            "written_at": self.written_at,
            "page_count": self.page_count,
            "processed_pages": self.processed_pages,
            "document_markdown_path": self.document_markdown_path,
            "notes": self.notes,
            "pages": [page.to_dict() for page in self.pages],
        }
