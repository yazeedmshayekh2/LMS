from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class PageType(StrEnum):
    COVER = "cover"
    LEGAL = "legal"
    TOC = "toc"
    PREFACE = "preface"
    UNIT_OPENER = "unit_opener"
    LESSON = "lesson"
    ENRICHMENT = "enrichment"
    INQUIRY = "inquiry"
    UNIT_REVIEW = "unit_review"
    GLOSSARY = "glossary"
    BODY = "body"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class PageGeometry:
    width_pt: float
    height_pt: float
    rotation: int
    mediabox: tuple[float, float, float, float]


@dataclass(slots=True)
class LayoutSignals:
    text_block_count: int
    non_text_block_count: int
    image_block_count: int
    table_count: int
    line_count: int
    span_count: int
    unique_fonts: list[str] = field(default_factory=list)
    median_font_size_pt: float | None = None


@dataclass(slots=True)
class TextSignals:
    char_count: int
    arabic_ratio: float
    latin_ratio: float
    digit_ratio: float
    replacement_char_count: int
    whitespace_ratio: float


@dataclass(slots=True)
class BackendExtraction:
    backend: str
    ok: bool
    char_count: int
    text_signals: TextSignals | None
    text: str
    quality_score: float
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PageProfile:
    page_number: int
    page_type: PageType
    classification_confidence: float
    classification_reasons: list[str]
    geometry: PageGeometry
    layout: LayoutSignals
    primary_text_signals: TextSignals
    backends: list[BackendExtraction]
    recommended_backends: list[str]
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PreprocessReport:
    source_pdf: str
    written_at: str
    page_count: int
    processed_pages: int
    document_metadata: dict[str, Any]
    backend_summary: dict[str, Any]
    pages: list[PageProfile]
    docling_markdown_path: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["pages"] = [page.to_dict() for page in self.pages]
        return payload
