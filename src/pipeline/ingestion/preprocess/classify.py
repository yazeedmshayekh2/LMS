from __future__ import annotations

import re

from pipeline.ingestion.models import PageType
from pipeline.ingestion.text_utils import normalize_arabic_keywords

TOC_RE = re.compile(r"قائمة\s*المحتويات")
PREFACE_RE = re.compile(r"المقد\s*مة|مقد\s*مة")
LESSON_RE = re.compile(r"الدرس|نتاجات\s*التعلم|الفكرة\s*الرئيسة")
UNIT_RE = re.compile(r"الوحدة")
ENRICHMENT_RE = re.compile(r"الإثراء|التوسع")
INQUIRY_RE = re.compile(r"استقصاء|أستكشف|استكشاف")
REVIEW_RE = re.compile(r"مراجعة\s*الوحدة")
GLOSSARY_RE = re.compile(r"المصطلحات|مسرد")
LEGAL_RE = re.compile(
    r"HarperCollins|ISBN|All rights reserved|British Library|الإيداع",
    re.IGNORECASE,
)
COVER_RE = re.compile(r"العلوم|كتاب الطالب|فريق التأليف")


def classify_page(
    page_number: int,
    text: str,
    *,
    table_count: int,
    image_block_count: int,
) -> tuple[PageType, float, list[str]]:
    sample = text or ""
    compact = normalize_arabic_keywords(sample)
    reasons: list[str] = []
    scores: dict[PageType, float] = {page_type: 0.0 for page_type in PageType}

    if page_number == 1:
        scores[PageType.COVER] += 0.8
        reasons.append("first page")
    elif page_number > 1:
        scores[PageType.COVER] *= 0.35
    if COVER_RE.search(sample):
        scores[PageType.COVER] += 0.35
        reasons.append("cover keywords")
    if LEGAL_RE.search(sample):
        scores[PageType.LEGAL] += 0.75
        reasons.append("legal/copyright markers")
    if TOC_RE.search(sample) or (
        "المحتويات" in compact and "قائمة" in compact
    ):
        scores[PageType.TOC] += 0.85
        reasons.append("table of contents heading")
    if table_count > 0 and TOC_RE.search(sample):
        scores[PageType.TOC] += 0.2
        reasons.append("table detected on TOC page")
    if (
        PREFACE_RE.search(sample)
        or "مقدمة" in compact
        or "المقد" in compact
        or "مقد" in compact
        or ("بسم" in compact and ("الرحمن" in compact or "الرح" in compact))
    ):
        scores[PageType.PREFACE] += 0.8
        reasons.append("preface heading")
    if LESSON_RE.search(sample):
        scores[PageType.LESSON] += 0.7
        reasons.append("lesson markers")
    if UNIT_RE.search(sample):
        scores[PageType.UNIT_OPENER] += 0.45
        reasons.append("unit heading")
    if ENRICHMENT_RE.search(sample):
        scores[PageType.ENRICHMENT] += 0.7
        reasons.append("enrichment markers")
    if INQUIRY_RE.search(sample):
        scores[PageType.INQUIRY] += 0.7
        reasons.append("inquiry markers")
    if REVIEW_RE.search(sample):
        scores[PageType.UNIT_REVIEW] += 0.75
        reasons.append("unit review markers")
    if GLOSSARY_RE.search(sample):
        scores[PageType.GLOSSARY] += 0.7
        reasons.append("glossary markers")

    if page_number in {2, 3, 4} and scores[PageType.LEGAL] > 0:
        scores[PageType.LEGAL] += 0.15
    if page_number in {3, 4} and scores[PageType.TOC] > 0:
        scores[PageType.TOC] += 0.15
    if page_number == 5:
        scores[PageType.PREFACE] += 0.2
        reasons.append("known preface page index")
    if image_block_count >= 3 and scores[PageType.LESSON] > 0:
        scores[PageType.LESSON] += 0.1
        reasons.append("image-heavy lesson layout")

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_type, best_score = ranked[0]
    if best_score < 0.35:
        return PageType.UNKNOWN, round(best_score, 4), reasons or ["low-confidence fallback"]

    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = min(0.99, round(best_score - (second_score * 0.35), 4))
    return best_type, confidence, reasons
