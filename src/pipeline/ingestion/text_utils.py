from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from pipeline.ingestion.models import TextSignals

ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
LATIN_RE = re.compile(r"[A-Za-z]")
DIGIT_RE = re.compile(r"\d")
REPLACEMENT_RE = re.compile(r"[\ufffd\uFFFD]")
WHITESPACE_RE = re.compile(r"\s")


def normalize_for_compare(text: str) -> str:
    collapsed = WHITESPACE_RE.sub(" ", text or "").strip()
    return unicodedata.normalize("NFKC", collapsed)


def normalize_arabic_keywords(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = normalized.replace("\u0640", "")
    return WHITESPACE_RE.sub("", normalized)


def analyze_text(text: str) -> TextSignals:
    sample = text or ""
    char_count = len(sample)
    if char_count == 0:
        return TextSignals(
            char_count=0,
            arabic_ratio=0.0,
            latin_ratio=0.0,
            digit_ratio=0.0,
            replacement_char_count=0,
            whitespace_ratio=0.0,
        )

    arabic = len(ARABIC_RE.findall(sample))
    latin = len(LATIN_RE.findall(sample))
    digits = len(DIGIT_RE.findall(sample))
    replacements = len(REPLACEMENT_RE.findall(sample))
    whitespace = len(WHITESPACE_RE.findall(sample))
    return TextSignals(
        char_count=char_count,
        arabic_ratio=round(arabic / char_count, 4),
        latin_ratio=round(latin / char_count, 4),
        digit_ratio=round(digits / char_count, 4),
        replacement_char_count=replacements,
        whitespace_ratio=round(whitespace / char_count, 4),
    )


def similarity(a: str, b: str) -> float:
    left = normalize_for_compare(a)
    right = normalize_for_compare(b)
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def quality_score(
    text: str,
    *,
    reference: str | None = None,
    rtl_penalty: float = 0.0,
) -> float:
    signals = analyze_text(text)
    if signals.char_count == 0:
        return 0.0

    score = 0.35
    score += min(signals.arabic_ratio, 0.45)
    score += min(signals.latin_ratio, 0.15)
    score -= min(signals.replacement_char_count / max(signals.char_count, 1), 1.0) * 0.35
    score -= min(signals.whitespace_ratio, 0.5) * 0.1
    score -= rtl_penalty

    if reference is not None:
        score = (score * 0.55) + (similarity(text, reference) * 0.45)

    return round(max(0.0, min(score, 1.0)), 4)


def format_extracted_text(
    text: str,
    limit: int | None = None,
    *,
    normalize: bool = False,
) -> str:
    output = normalize_for_compare(text) if normalize else (text or "").strip()
    if limit is None or len(output) <= limit:
        return output
    return output[:limit]
