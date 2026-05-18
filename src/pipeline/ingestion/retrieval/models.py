from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RetrievalChunk:
    """One searchable unit from normalized section Markdown."""

    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source_path: str | None = None

    @property
    def page_start(self) -> int | None:
        value = self.metadata.get("page_start")
        return int(value) if value is not None else None

    @property
    def unit_title(self) -> str | None:
        value = self.metadata.get("unit_title")
        return str(value) if value is not None else None


@dataclass(slots=True)
class SearchHit:
    chunk: RetrievalChunk
    rrf_score: float
    bm25_score: float | None = None
    cosine_score: float | None = None
    bm25_rank: int | None = None
    dense_rank: int | None = None

    @property
    def score(self) -> float:
        """Alias for ``rrf_score`` (backward compatible)."""
        return self.rrf_score

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "rrf_score": round(self.rrf_score, 6),
            "bm25_score": round(self.bm25_score, 6) if self.bm25_score is not None else None,
            "cosine_score": round(self.cosine_score, 6) if self.cosine_score is not None else None,
            "bm25_rank": self.bm25_rank,
            "dense_rank": self.dense_rank,
            "page_start": self.chunk.page_start,
            "unit_title": self.chunk.unit_title,
            "content_kind": self.chunk.metadata.get("content_kind"),
            "text_preview": self.chunk.text[:240],
        }
