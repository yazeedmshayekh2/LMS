from __future__ import annotations

from pipeline.ingestion.normalize.page_guides import guidance_for_page_types

READABLE_LAYOUT_GUIDE = """\
Readable export rules:
- Output valid Markdown only. Do not wrap the answer in a code fence.
- Do not emit YAML frontmatter or chunk metadata.
- Reorder the supplied text into the same order a student would read it in the printed book.
- Use clear heading hierarchy: # for unit or major page titles, ## for lessons or major sections, ### for subsections and sidebars.
- Place <!-- page_break: N --> at the start of each page block when the input spans multiple pages.
- Keep Arabic in natural reading order and fix obvious RTL or glyph artifacts without changing meaning.
- Remove exact duplicate lines and merge split fragments of the same sentence when they clearly belong together.
- Keep English science labels beside their Arabic counterparts when both appear in the source.
- Present table-of-contents entries as a readable list or Markdown table with topic and page columns when page numbers are present.
- Present learning outcomes under a ### heading such as نتاجات التعلم, using bullet lists.
- Present key terms under a ### heading such as المفاهيم والمصطلحات, using lines formatted as Arabic | English.
- Keep figure blocks in this form when figures are present:

::: figure
figure_id: ...
caption: ...
alt_text: ...
source_page: ...
:::

- Keep footnotes as [^N] with definitions at the end of the page section.
- Do not invent titles, explanations, page numbers, or examples that are not supported by the input.
- Do not summarize or shorten lesson body text.
"""


def build_readable_system_prompt() -> str:
    return (
        "You postprocess normalized Arabic textbook Markdown for human reading. "
        "Your job is layout and reading order only: make the page easy to follow "
        "while preserving the source wording."
    )


def build_readable_user_prompt(
    *,
    page_start: int,
    page_end: int,
    page_types: list[str],
    outline_context: str,
    markdown: str,
) -> str:
    page_guidance = guidance_for_page_types(page_types)
    return (
        f"{READABLE_LAYOUT_GUIDE}\n\n"
        f"{page_guidance}\n\n"
        "Book outline and page map:\n"
        f"{outline_context}\n\n"
        f"Postprocess pages {page_start}-{page_end} for readable export.\n"
        f"Observed page types: {', '.join(page_types)}\n\n"
        "Normalized Markdown without frontmatter:\n"
        f"{markdown}\n"
    )
