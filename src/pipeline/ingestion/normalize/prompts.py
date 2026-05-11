from __future__ import annotations

from pipeline.ingestion.normalize.models import NormalizeBatch
from pipeline.ingestion.normalize.page_guides import guidance_for_page_types
from pipeline.ingestion.normalize.schema import MARKDOWN_SCHEMA_GUIDE


def build_system_prompt() -> str:
    return (
        "You normalize Arabic textbook extraction into schema-compliant Markdown "
        "for an LMS ingestion pipeline. Follow the schema exactly. Structure and "
        "clean the source text, but never invent book content. Preserve TOC "
        "behavior when the page type is toc."
    )


def build_user_prompt(batch: NormalizeBatch) -> str:
    page_guidance = guidance_for_page_types(batch.page_types)
    return (
        f"{MARKDOWN_SCHEMA_GUIDE}\n\n"
        f"{page_guidance}\n\n"
        "Book outline and page map:\n"
        f"{batch.outline_context}\n\n"
        f"Normalize pages {batch.page_start}-{batch.page_end}.\n"
        f"Observed page types: {', '.join(batch.page_types)}\n\n"
        "Raw stage-2 Markdown:\n"
        f"{batch.raw_markdown}\n"
    )
