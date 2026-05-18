from __future__ import annotations

import re
from typing import Sequence

import numpy as np
from langchain_core.embeddings import Embeddings
from rank_bm25 import BM25Okapi

from pipeline.ingestion.retrieval.models import RetrievalChunk, SearchHit

_TOKEN_RE = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text or "")]


def _cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query_norm = np.linalg.norm(query)
    if query_norm == 0:
        return np.zeros(matrix.shape[0], dtype=np.float64)
    row_norms = np.linalg.norm(matrix, axis=1)
    row_norms[row_norms == 0] = 1.0
    return matrix @ query / (row_norms * query_norm)


def _reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[int]],
    *,
    k: int = 60,
) -> dict[int, float]:
    scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, doc_index in enumerate(ranked, start=1):
            scores[doc_index] = scores.get(doc_index, 0.0) + 1.0 / (k + rank)
    return scores


class HybridRetriever:
    """Combine BM25 (sparse) and embedding similarity (dense) with RRF."""

    def __init__(
        self,
        chunks: Sequence[RetrievalChunk],
        embeddings: Embeddings,
        *,
        rrf_k: int = 60,
    ) -> None:
        self._chunks = list(chunks)
        self._embeddings = embeddings
        self._rrf_k = rrf_k
        self._bm25: BM25Okapi | None = None
        self._dense_matrix: np.ndarray | None = None

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def index(self) -> None:
        """Build sparse and dense indexes over all chunks."""
        tokenized = [_tokenize(chunk.text) for chunk in self._chunks]
        self._bm25 = BM25Okapi(tokenized)

        texts = [chunk.text for chunk in self._chunks]
        vectors = self._embeddings.embed_documents(texts)
        self._dense_matrix = np.asarray(vectors, dtype=np.float64)

    def search(self, query: str, *, k: int = 5) -> list[SearchHit]:
        if self._bm25 is None or self._dense_matrix is None:
            msg = "Call index() before search()"
            raise RuntimeError(msg)
        if not self._chunks:
            return []

        k = min(k, len(self._chunks))
        query_tokens = _tokenize(query)
        bm25_scores = self._bm25.get_scores(query_tokens)
        bm25_ranked = np.argsort(bm25_scores)[::-1][:k].tolist()

        query_vector = np.asarray(
            self._embeddings.embed_query(query),
            dtype=np.float64,
        )
        dense_scores = _cosine_similarity(query_vector, self._dense_matrix)
        dense_ranked = np.argsort(dense_scores)[::-1][:k].tolist()

        fused = _reciprocal_rank_fusion(
            [bm25_ranked, dense_ranked],
            k=self._rrf_k,
        )
        top_indices = sorted(
            fused,
            key=lambda index: fused[index],
            reverse=True,
        )[:k]

        bm25_rank_map = {doc_id: rank for rank, doc_id in enumerate(bm25_ranked, start=1)}
        dense_rank_map = {doc_id: rank for rank, doc_id in enumerate(dense_ranked, start=1)}

        hits: list[SearchHit] = []
        for doc_index in top_indices:
            hits.append(
                SearchHit(
                    chunk=self._chunks[doc_index],
                    rrf_score=fused[doc_index],
                    bm25_score=float(bm25_scores[doc_index]),
                    cosine_score=float(dense_scores[doc_index]),
                    bm25_rank=bm25_rank_map.get(doc_index),
                    dense_rank=dense_rank_map.get(doc_index),
                )
            )
        return hits
