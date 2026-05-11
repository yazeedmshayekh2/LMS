from __future__ import annotations

from pipeline.ingestion.extract.models import RawPageMarkdown
from pipeline.ingestion.normalize.models import BookOutline, NormalizeBatch
from pipeline.ingestion.normalize.toc import render_outline_context


def _batch_key(page: RawPageMarkdown) -> tuple[str, int | None, int | None]:
    if page.page_type in {"cover", "legal", "preface", "toc", "unknown"}:
        return (page.page_type, None, None)
    return (page.page_type, page.page_number, page.page_number)


def build_batches(
    pages: list[RawPageMarkdown],
    outline: BookOutline,
    *,
    batch_size: int,
) -> list[NormalizeBatch]:
    ordered = sorted(pages, key=lambda page: page.page_number)
    outline_context = render_outline_context(outline)
    batches: list[NormalizeBatch] = []
    current: list[RawPageMarkdown] = []

    def flush() -> None:
        nonlocal current
        if not current:
            return
        page_start = current[0].page_number
        page_end = current[-1].page_number
        batch_id = f"p{page_start:03d}_{page_end:03d}"
        batches.append(
            NormalizeBatch(
                batch_id=batch_id,
                page_start=page_start,
                page_end=page_end,
                page_types=[page.page_type for page in current],
                raw_markdown="\n\n".join(page.markdown for page in current),
                outline_context=outline_context,
            )
        )
        current = []

    for page in ordered:
        if page.page_type in {"cover", "legal", "preface", "toc"}:
            flush()
            current = [page]
            flush()
            continue

        if not current:
            current = [page]
            continue

        same_key = _batch_key(page) == _batch_key(current[-1])
        if same_key and len(current) < batch_size:
            current.append(page)
        else:
            flush()
            current = [page]
    flush()
    return batches
