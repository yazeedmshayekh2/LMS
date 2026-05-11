from __future__ import annotations

REQUIRED_FRONTMATTER_FIELDS = (
    "book_title",
    "grade",
    "semester",
    "subject",
    "unit_no",
    "unit_title",
    "lesson_no",
    "lesson_title",
    "content_kind",
    "page_start",
    "page_end",
    "heading_path",
    "chunk_id",
)

CONTENT_KINDS = (
    "lesson_body",
    "learning_outcomes",
    "key_terms",
    "figure",
    "enrichment",
    "inquiry",
    "review",
    "front_matter",
    "toc",
)

MARKDOWN_SCHEMA_GUIDE = """\
Output valid Markdown only. Do not wrap the answer in a code fence.

Each logical chunk must begin with a YAML frontmatter block delimited by --- on its own lines.
Use exactly these keys inside every frontmatter block:
- book_title
- grade
- semester
- subject
- unit_no
- unit_title
- lesson_no
- lesson_title
- content_kind
- page_start
- page_end
- heading_path
- chunk_id

Allowed content_kind values:
lesson_body, learning_outcomes, key_terms, figure, enrichment, inquiry, review, front_matter, toc

Use null for unknown numeric or title fields when the source does not support them.

After frontmatter:
- Use # for unit-level titles, ## for lesson-level titles, ### for subsection titles only when the source clearly supports that hierarchy.
- On cover, legal, and preface pages, prefer multiple focused chunks with clear source-based headings instead of one unstructured blob.
- Keep Arabic prose in natural reading order and fix RTL or glyph artifacts from extraction without adding new wording.
- Put sidebar learning outcomes in their own chunk with content_kind=learning_outcomes.
- Put bilingual terminology in content_kind=key_terms using lines formatted as: Arabic | English
- Convert each figure placeholder into a structured block:

::: figure
figure_id: ...
caption: ...
alt_text: ...
source_page: ...
:::

- Preserve page citations with HTML comments: <!-- page_break: N -->
- Preserve footnotes as [^N] with definitions at the section end.
- Do not leave raw <!-- vision_ocr_pending --> markers in the final output; convert them into figure blocks with cautious alt_text when possible.
- Keep English science terms explicit and aligned with their Arabic labels.
- Emit stable chunk_id values such as u1-l1-body-p10.
"""
