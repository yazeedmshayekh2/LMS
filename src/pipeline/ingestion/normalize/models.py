from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class TocEntry:
    page_number: int
    title: str
    unit_no: int | None = None
    lesson_no: int | None = None
    entry_kind: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BookOutline:
    book_title: str
    grade: int | None
    semester: int | None
    entries: list[TocEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "book_title": self.book_title,
            "grade": self.grade,
            "semester": self.semester,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    def entry_for_page(self, page_number: int) -> TocEntry | None:
        candidates = [entry for entry in self.entries if entry.page_number <= page_number]
        if not candidates:
            return None
        return max(candidates, key=lambda entry: entry.page_number)


@dataclass(slots=True)
class NormalizeBatch:
    batch_id: str
    page_start: int
    page_end: int
    page_types: list[str]
    raw_markdown: str
    outline_context: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class NormalizedSection:
    batch_id: str
    page_start: int
    page_end: int
    markdown: str
    validation: ValidationResult
    prompt_path: str | None = None
    provider: str | None = None
    model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["validation"] = self.validation.to_dict()
        return payload


@dataclass(slots=True)
class NormalizeReport:
    source_extract_report: str
    written_at: str
    processed_pages: int
    provider: str
    model: str
    dry_run: bool
    outline: BookOutline
    sections: list[NormalizedSection]
    document_markdown_path: str
    qc_report_path: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_extract_report": self.source_extract_report,
            "written_at": self.written_at,
            "processed_pages": self.processed_pages,
            "provider": self.provider,
            "model": self.model,
            "dry_run": self.dry_run,
            "outline": self.outline.to_dict(),
            "document_markdown_path": self.document_markdown_path,
            "qc_report_path": self.qc_report_path,
            "notes": self.notes,
            "sections": [section.to_dict() for section in self.sections],
        }
