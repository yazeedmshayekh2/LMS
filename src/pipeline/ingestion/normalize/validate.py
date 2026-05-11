from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path

from pipeline.ingestion.normalize.models import NormalizedSection, ValidationResult
from pipeline.ingestion.normalize.schema import CONTENT_KINDS, REQUIRED_FRONTMATTER_FIELDS

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL | re.MULTILINE)
_FIELD_RE = re.compile(r"^([A-Za-z_]+):\s*(.+?)\s*$", re.MULTILINE)
_HEADING_RE = re.compile(r"^(#{1,6})\s+.+$", re.MULTILINE)
_FOOTNOTE_REF_RE = re.compile(r"\[\^\d+\]")
_FOOTNOTE_DEF_RE = re.compile(r"^\[\^\d+\]:", re.MULTILINE)
_VISION_PENDING_RE = re.compile(r"vision_ocr_pending")
_FIGURE_BLOCK_RE = re.compile(r"^::: figure$", re.MULTILINE)
_PAGE_BREAK_RE = re.compile(r"<!--\s*page_break:\s*\d+\s*-->")


def _parse_frontmatter_blocks(markdown: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    for match in _FRONTMATTER_RE.finditer(markdown):
        fields: dict[str, str] = {}
        for field_match in _FIELD_RE.finditer(match.group(1)):
            fields[field_match.group(1)] = field_match.group(2).strip()
        blocks.append(fields)
    return blocks


def validate_normalized_markdown(
    markdown: str,
    *,
    reference_text: str | None = None,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, float | int] = {}

    frontmatter_blocks = _parse_frontmatter_blocks(markdown)
    metrics["frontmatter_block_count"] = len(frontmatter_blocks)
    if not frontmatter_blocks:
        errors.append("No YAML frontmatter blocks found.")
        if markdown.lstrip().startswith(("yaml", "YAML")):
            warnings.append(
                "Frontmatter is missing --- delimiters; expected fenced YAML blocks."
            )

    for index, fields in enumerate(frontmatter_blocks, start=1):
        missing = [name for name in REQUIRED_FRONTMATTER_FIELDS if name not in fields]
        if missing:
            errors.append(f"Chunk {index} missing frontmatter fields: {', '.join(missing)}")
        content_kind = fields.get("content_kind")
        if content_kind and content_kind not in CONTENT_KINDS:
            errors.append(f"Chunk {index} has invalid content_kind: {content_kind}")

    heading_levels = {len(match.group(1)) for match in _HEADING_RE.finditer(markdown)}
    if heading_levels - {1, 2, 3}:
        warnings.append("Headings found outside # / ## / ### levels.")

    if _VISION_PENDING_RE.search(markdown):
        warnings.append("vision_ocr_pending markers remain in normalized output.")

    if _FOOTNOTE_REF_RE.search(markdown) and not _FOOTNOTE_DEF_RE.search(markdown):
        warnings.append("Footnote references exist without footnote definitions.")

    metrics["figure_block_count"] = len(_FIGURE_BLOCK_RE.findall(markdown))
    metrics["page_break_comment_count"] = len(_PAGE_BREAK_RE.findall(markdown))

    if reference_text:
        ratio = SequenceMatcher(None, reference_text, markdown).ratio()
        metrics["reference_similarity"] = round(ratio, 4)
        metrics["approx_cer"] = round(1.0 - ratio, 4)

    return ValidationResult(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        metrics=metrics,
    )


def load_reference_text(preprocess_dir: Path, page_number: int) -> str | None:
    path = preprocess_dir / "backends" / "pymupdf" / f"page_{page_number:03d}.txt"
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    body = [line for line in lines if line and not line.startswith(("backend:", "page:", "ok:", "quality_score:", "char_count:", "note:", "error:"))]
    return "\n".join(body).strip()
