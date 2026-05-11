from __future__ import annotations

from pipeline.ingestion.backends.pymupdf import PageImageBlock
from pipeline.ingestion.extract.models import VisionPlaceholder
from pipeline.ingestion.models import PageProfile, PageType


def build_vision_placeholders(
    profile: PageProfile,
    image_blocks: list[PageImageBlock],
) -> list[VisionPlaceholder]:
    if not image_blocks:
        return []

    placeholders: list[VisionPlaceholder] = []
    if profile.page_type in {
        PageType.COVER,
        PageType.LEGAL,
        PageType.TOC,
        PageType.PREFACE,
    }:
        return placeholders

    if profile.layout.image_block_count < 3:
        return placeholders

    reason = "layout_heavy_page"
    if profile.page_type in {PageType.LESSON, PageType.INQUIRY, PageType.ENRICHMENT}:
        reason = "diagram_or_sidebar_layout"
    if "replacement_chars_present" in profile.flags:
        reason = "text_layer_degraded"

    for image in image_blocks:
        placeholders.append(
            VisionPlaceholder(
                index=image.index,
                bbox=image.bbox,
                reason=reason,
            )
        )
    return placeholders
