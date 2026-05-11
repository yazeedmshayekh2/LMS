from __future__ import annotations

from pipeline.ingestion.extract.models import BlockRegion
from pipeline.ingestion.models import PageType


def classify_block_region(
    *,
    page_type: PageType,
    bbox: tuple[float, float, float, float],
    page_width: float,
    page_height: float,
    max_font_size: float,
    median_font_size: float | None,
    line_count: int,
) -> BlockRegion:
    x0, y0, x1, y1 = bbox
    x_center = (x0 + x1) / 2.0
    y_center = (y0 + y1) / 2.0

    if page_type in {PageType.COVER, PageType.LEGAL, PageType.TOC, PageType.PREFACE}:
        return BlockRegion.FRONT_MATTER

    if y_center <= page_height * 0.11:
        return BlockRegion.HEADER
    if y_center >= page_height * 0.9:
        return BlockRegion.FOOTER

    if page_type in {
        PageType.LESSON,
        PageType.INQUIRY,
        PageType.ENRICHMENT,
        PageType.UNIT_OPENER,
        PageType.UNIT_REVIEW,
        PageType.GLOSSARY,
    }:
        if x_center >= page_width * 0.54:
            return BlockRegion.SIDEBAR
        if (
            median_font_size is not None
            and max_font_size <= median_font_size * 0.92
            and line_count <= 2
            and y_center >= page_height * 0.55
        ):
            return BlockRegion.CAPTION

    return BlockRegion.MAIN
