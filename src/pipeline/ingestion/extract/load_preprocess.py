from __future__ import annotations

import logging
from pathlib import Path

from pipeline.ingestion.backends.pymupdf import (
    extract_pymupdf_page,
    extract_pymupdf_structure,
    page_geometry,
)
from pipeline.ingestion.config import IngestionConfig
from pipeline.ingestion.models import (
    LayoutSignals,
    PageGeometry,
    PageProfile,
    TextSignals,
)
from pipeline.ingestion.preprocess.classify import classify_page
from pipeline.ingestion.preprocess.io import load_preprocess_report
from pipeline.ingestion.text_utils import analyze_text

logger = logging.getLogger(__name__)


def _derive_page_profile(pdf_path: Path, page_number: int) -> PageProfile:
    geometry_data = page_geometry(pdf_path, page_number)
    geometry = PageGeometry(
        width_pt=geometry_data["width_pt"],
        height_pt=geometry_data["height_pt"],
        rotation=geometry_data["rotation"],
        mediabox=geometry_data["mediabox"],
    )
    structure = extract_pymupdf_structure(pdf_path, page_number)
    layout = LayoutSignals(
        text_block_count=structure.text_block_count,
        non_text_block_count=structure.non_text_block_count,
        image_block_count=structure.image_block_count,
        table_count=structure.table_count,
        line_count=structure.line_count,
        span_count=structure.span_count,
        unique_fonts=structure.unique_fonts,
        median_font_size_pt=structure.median_font_size_pt,
    )
    text = extract_pymupdf_page(pdf_path, page_number)
    page_type, confidence, reasons = classify_page(
        page_number,
        text,
        table_count=layout.table_count,
        image_block_count=layout.image_block_count,
    )
    flags: list[str] = []
    if layout.table_count > 0:
        flags.append("has_tables")
    if layout.image_block_count > 0:
        flags.append("has_images")
    signals = analyze_text(text)
    if signals.replacement_char_count > 0:
        flags.append("replacement_chars_present")

    return PageProfile(
        page_number=page_number,
        page_type=page_type,
        classification_confidence=confidence,
        classification_reasons=reasons,
        geometry=geometry,
        layout=layout,
        primary_text_signals=signals,
        backends=[],
        recommended_backends=["pymupdf", "pymupdf_structure"],
        flags=flags,
    )


def resolve_page_profiles(
    config: IngestionConfig,
    *,
    last_page: int,
) -> dict[int, PageProfile]:
    if config.preprocess_report_path.is_file():
        report = load_preprocess_report(config.preprocess_report_path)
        profiles = {
            profile.page_number: profile
            for profile in report.pages
            if profile.page_number <= last_page
        }
        missing = [page for page in range(1, last_page + 1) if page not in profiles]
        if missing:
            logger.warning(
                "Preprocess report missing %s page profile(s); deriving inline.",
                len(missing),
            )
        for page_number in missing:
            profiles[page_number] = _derive_page_profile(config.pdf_path, page_number)
        return profiles

    logger.warning(
        "Preprocess report not found at %s; deriving page profiles inline.",
        config.preprocess_report_path,
    )
    return {
        page_number: _derive_page_profile(config.pdf_path, page_number)
        for page_number in range(1, last_page + 1)
    }
