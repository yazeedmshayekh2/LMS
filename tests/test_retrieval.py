from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.ingestion.retrieval import (
    HybridRetriever,
    create_embeddings,
    load_chunks_from_sections,
)


def test_load_chunks_from_real_sections():
    sections_dir = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "pipeline"
        / "assets"
        / "normalized"
        / "sections"
    )
    if not sections_dir.is_dir():
        pytest.skip("normalized sections not generated yet")

    chunks = load_chunks_from_sections(sections_dir)
    assert len(chunks) >= 1
    assert all(chunk.chunk_id for chunk in chunks)
    assert all(chunk.text.strip() for chunk in chunks)


def test_hybrid_retriever_ranks_genetics_chunk_first(sample_chunks):
    embeddings = create_embeddings("fake")
    retriever = HybridRetriever(sample_chunks, embeddings)
    retriever.index()

    hits = retriever.search("المادة الوراثية في الخلايا", k=3)

    assert hits
    assert hits[0].chunk.chunk_id == "genetics-overview"
    assert hits[0].bm25_rank is not None
    assert hits[0].dense_rank is not None
    assert hits[0].bm25_score is not None
    assert hits[0].cosine_score is not None
    assert hits[0].rrf_score == hits[0].score


def test_hybrid_retriever_ranks_reproduction_for_reproduction_query(sample_chunks):
    embeddings = create_embeddings("fake")
    retriever = HybridRetriever(sample_chunks, embeddings)
    retriever.index()

    hits = retriever.search("كيف تتكاثر الكائنات الحية", k=2)

    assert hits[0].chunk.chunk_id == "reproduction-lesson"
