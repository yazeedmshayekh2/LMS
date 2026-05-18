from __future__ import annotations

import re
from pathlib import Path

import yaml

from pipeline.ingestion.retrieval.models import RetrievalChunk

_SECTION_FILE_RE = re.compile(r"^p\d{3}_\d{3}\.md$", re.IGNORECASE)
_FRONTMATTER_SPLIT_RE = re.compile(r"(?m)^---\s*$")


def _parse_section_file(path: Path) -> list[RetrievalChunk]:
    segments = [part.strip() for part in _FRONTMATTER_SPLIT_RE.split(path.read_text(encoding="utf-8"))]
    segments = [part for part in segments if part]

    chunks: list[RetrievalChunk] = []
    index = 0
    while index + 1 < len(segments):
        meta_raw, body = segments[index], segments[index + 1]
        index += 2
        try:
            meta = yaml.safe_load(meta_raw) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(meta, dict):
            continue
        chunk_id = str(meta.get("chunk_id") or f"{path.stem}-{len(chunks)}")
        chunks.append(
            RetrievalChunk(
                chunk_id=chunk_id,
                text=body,
                metadata=meta,
                source_path=str(path),
            )
        )
    return chunks


def load_chunks_from_sections(sections_dir: Path) -> list[RetrievalChunk]:
    """Load retrieval chunks from normalized section Markdown files."""
    if not sections_dir.is_dir():
        msg = f"Sections directory not found: {sections_dir}"
        raise FileNotFoundError(msg)

    chunks: list[RetrievalChunk] = []
    for path in sorted(sections_dir.glob("p*_*.md")):
        if path.name.endswith(".prompt.md"):
            continue
        if not _SECTION_FILE_RE.match(path.name):
            continue
        chunks.extend(_parse_section_file(path))

    if not chunks:
        msg = f"No chunks found under {sections_dir}"
        raise ValueError(msg)
    return chunks
