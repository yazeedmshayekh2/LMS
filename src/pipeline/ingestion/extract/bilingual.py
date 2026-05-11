from __future__ import annotations

import re

from pipeline.ingestion.text_utils import ARABIC_RE, LATIN_RE

PAIR_SPLIT_RE = re.compile(r"\s*(?:\||/|:)\s*")
PAREN_LATIN_RE = re.compile(r"\(([^)]+)\)")
PAREN_ARABIC_RE = re.compile(r"([\u0600-\u06FF][^()]{1,80})\s*\(([^)]+)\)")


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_bilingual_pairs(lines: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for line in lines:
        sample = _clean(line)
        if not sample:
            continue

        for match in PAREN_ARABIC_RE.finditer(sample):
            arabic = _clean(match.group(1))
            latin = _clean(match.group(2))
            if arabic and latin and LATIN_RE.search(latin):
                key = (arabic, latin)
                if key not in seen:
                    seen.add(key)
                    pairs.append(key)

        if ARABIC_RE.search(sample) and LATIN_RE.search(sample):
            if PAIR_SPLIT_RE.search(sample):
                parts = PAIR_SPLIT_RE.split(sample, maxsplit=1)
                if len(parts) == 2:
                    left, right = _clean(parts[0]), _clean(parts[1])
                    if ARABIC_RE.search(left) and LATIN_RE.search(right):
                        key = (left, right)
                    elif ARABIC_RE.search(right) and LATIN_RE.search(left):
                        key = (right, left)
                    else:
                        continue
                    if key not in seen:
                        seen.add(key)
                        pairs.append(key)
    return pairs
