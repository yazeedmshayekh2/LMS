from __future__ import annotations

import re
from pathlib import Path

_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*(?:\n|$)", re.DOTALL | re.MULTILINE)


def strip_chunk_frontmatter(markdown: str) -> str:
    body = _FRONTMATTER_RE.sub("", markdown)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def export_readable_sections(
    sections_dir: Path,
    *,
    output_dir: Path,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for source in sorted(sections_dir.glob("p*.md")):
        if source.name.endswith(".prompt.md"):
            continue
        readable = strip_chunk_frontmatter(source.read_text(encoding="utf-8"))
        target = output_dir / source.name
        target.write_text(readable, encoding="utf-8")
        written.append(target)
    return written


def export_readable_document(
    sections_dir: Path,
    *,
    output_path: Path,
) -> Path:
    parts: list[str] = []
    for source in sorted(sections_dir.glob("p*.md")):
        if source.name.endswith(".prompt.md"):
            continue
        parts.append(strip_chunk_frontmatter(source.read_text(encoding="utf-8")))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(parts).strip() + "\n", encoding="utf-8")
    return output_path
