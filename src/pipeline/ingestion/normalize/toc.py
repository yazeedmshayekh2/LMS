from __future__ import annotations

import re

from pipeline.ingestion.extract.models import RawPageMarkdown
from pipeline.ingestion.normalize.models import BookOutline, TocEntry

PAGE_ONLY_RE = re.compile(r"^\d{1,3}$")
UNIT_RE = re.compile(r"الوحدة")
LESSON_RE = re.compile(r"الدرس")
ENRICHMENT_RE = re.compile(r"الإثراء|التوسع")
INQUIRY_RE = re.compile(r"استقصاء|استكشاف")
REVIEW_RE = re.compile(r"مراجعة")
PREFACE_RE = re.compile(r"المقدمة")


def _infer_title(lines: list[str]) -> str:
    cleaned = [line.strip() for line in lines if line.strip()]
    return " ".join(cleaned)


def _infer_entry_kind(title: str) -> str:
    if UNIT_RE.search(title):
        return "unit"
    if LESSON_RE.search(title):
        return "lesson"
    if ENRICHMENT_RE.search(title):
        return "enrichment"
    if INQUIRY_RE.search(title):
        return "inquiry"
    if REVIEW_RE.search(title):
        return "review"
    if PREFACE_RE.search(title):
        return "preface"
    return "unknown"


def _parse_toc_page(page: RawPageMarkdown) -> list[TocEntry]:
    entries: list[TocEntry] = []
    pending_page: int | None = None
    pending_lines: list[str] = []

    def flush() -> None:
        nonlocal pending_page, pending_lines
        if pending_page is None:
            return
        title = _infer_title(pending_lines)
        if not title:
            pending_page = None
            pending_lines = []
            return
        entries.append(
            TocEntry(
                page_number=pending_page,
                title=title,
                entry_kind=_infer_entry_kind(title),
            )
        )
        pending_page = None
        pending_lines = []

    for block in page.blocks:
        for line in block.lines:
            stripped = line.strip()
            if PAGE_ONLY_RE.fullmatch(stripped):
                flush()
                pending_page = int(stripped)
                continue
            if pending_page is not None:
                pending_lines.append(stripped)
    flush()
    return entries


def _book_title_from_cover(page: RawPageMarkdown | None) -> str:
    if page is None:
        return "علوم"
    for block in page.blocks:
        for line in block.lines:
            if "العلوم" in line:
                return "العلوم"
    return "علوم"


def build_outline(pages: list[RawPageMarkdown]) -> BookOutline:
    by_page = {page.page_number: page for page in pages}
    cover = by_page.get(1)
    book_title = _book_title_from_cover(cover)

    entries: list[TocEntry] = []
    for page in pages:
        if page.page_type != "toc":
            continue
        entries.extend(_parse_toc_page(page))

    unit_no = 0
    lesson_no = 0
    for entry in entries:
        if entry.entry_kind == "unit":
            unit_no += 1
            lesson_no = 0
            entry.unit_no = unit_no
        elif entry.entry_kind == "lesson":
            lesson_no += 1
            entry.unit_no = unit_no or None
            entry.lesson_no = lesson_no

    return BookOutline(
        book_title=book_title,
        grade=8,
        semester=1,
        entries=entries,
    )


def render_outline_context(outline: BookOutline) -> str:
    lines = [
        f"book_title: {outline.book_title}",
        f"grade: {outline.grade}",
        f"semester: {outline.semester}",
        "",
        "TOC outline:",
    ]
    for entry in outline.entries:
        lines.append(
            f"- page {entry.page_number}: "
            f"unit={entry.unit_no} lesson={entry.lesson_no} "
            f"kind={entry.entry_kind} title={entry.title}"
        )
    return "\n".join(lines)
