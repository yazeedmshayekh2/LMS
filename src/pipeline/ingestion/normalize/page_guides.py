from __future__ import annotations

FIDELITY_RULES = """\
Fidelity rules (apply to every page type):
- Use only text that appears in the raw stage-2 input for this batch. Do not add, infer, summarize, translate, or paraphrase.
- You may fix obvious OCR or RTL glyph issues, remove exact duplicate lines, and reorder text into a clearer reading order that still follows the book.
- Do not invent section titles, explanations, contact labels, or metadata that are not supported by the source text.
- If a field is missing in the source, leave it absent or set frontmatter values to null. Do not guess.
- Keep a polite, clean textbook tone by formatting only; do not add new prose.
"""

COVER_GUIDE = """\
Cover page (page_type=cover):
- Split the page into a small number of useful chunks, each with its own YAML frontmatter block and content_kind=front_matter.
- Suggested chunk order: title panel, authoring team, publisher and feedback contacts.
- Use headings only when the source already contains that label or role, such as the title, subtitle, semester line, فريق التأليف, and الناشر.
- Present author names as a readable list when the source lists people on separate lines.
- Keep contact lines, phone numbers, email, and web addresses exactly as written in the source.
- Remove duplicate title lines only when they are exact duplicates.
"""

LEGAL_GUIDE = """\
Legal and imprint pages (page_type=legal):
- Split the page into separate chunks by legal function, each with content_kind=front_matter.
- Keep Arabic official text, English copyright text, ISBN, deposit number, cataloging lines, and edition notes in distinct chunks.
- Preserve the original language of each block. Do not translate Arabic into English or the reverse.
- Use short headings only when they match a visible source label or an obvious legal section already present in the text.
- Keep long legal paragraphs intact; do not compress them into summaries.
"""

PREFACE_GUIDE = """\
Preface pages (page_type=preface):
- Use one or more front_matter chunks with natural paragraph breaks from the source.
- Keep the introduction in reading order. Do not add framing sentences or conclusions.
"""

TOC_GUIDE = """\
Table of contents pages (page_type=toc):
- Keep the current successful TOC strategy.
- Preserve one chunk per TOC entry when the source supports that structure.
- Keep page numbers, unit numbers, lesson numbers, and titles aligned with the source.
- Use content_kind=toc for TOC entries and keep enrichment, inquiry, and review entries distinct when the source distinguishes them.
"""

GENERAL_GUIDE = """\
Other general pages:
- Organize content in the same order a student would encounter it in the book.
- Prefer multiple focused chunks over one unstructured blob when the source has clear blocks or sidebars.
- Keep lesson, inquiry, enrichment, and review handling unchanged from the main schema.
"""


def guidance_for_page_types(page_types: list[str]) -> str:
    unique = list(dict.fromkeys(page_types))
    parts = [FIDELITY_RULES]
    for page_type in unique:
        if page_type == "cover":
            parts.append(COVER_GUIDE)
        elif page_type == "legal":
            parts.append(LEGAL_GUIDE)
        elif page_type == "preface":
            parts.append(PREFACE_GUIDE)
        elif page_type == "toc":
            parts.append(TOC_GUIDE)
        else:
            parts.append(GENERAL_GUIDE)
    return "\n".join(parts)
