"""Hybrid retrieval smoke test over normalized textbook chunks.

Combines BM25 sparse search with dense embedding similarity (RRF fusion).

Run from repo root:
  uv run python src/pipeline/run_test_retrieval.py --embedding-provider fake
  uv run python src/pipeline/run_test_retrieval.py --embedding-provider gemini --query "المادة الوراثية"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from pipeline.ingestion.config import IngestionConfig
from pipeline.ingestion.retrieval import (
    HybridRetriever,
    create_embeddings,
    load_chunks_from_sections,
)

logger = logging.getLogger(__name__)

DEFAULT_QUERIES = [
    "ما هي المادة الوراثية؟",
    "كيف تتكاثر الكائنات الحية؟",
    "الوراثة والتكاثر",
]


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Test hybrid retrieval (BM25 + embeddings) on normalized chunks.",
    )
    parser.add_argument(
        "--sections-dir",
        type=Path,
        default=None,
        help="Normalized sections directory (default: pipeline assets).",
    )
    parser.add_argument(
        "--embedding-provider",
        default="gemini",
        choices=["gemini", "google", "openai", "gpt", "ollama", "fake"],
        help="Embedding model provider.",
    )
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--query", action="append", default=[], help="Query text (repeatable).")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def _print_hits(query: str, hits: list, *, as_json: bool) -> None:
    if as_json:
        payload = {
            "query": query,
            "hits": [hit.to_dict() for hit in hits],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"\nQuery: {query}")
    print("-" * 72)
    if not hits:
        print("(no results)")
        return
    for rank, hit in enumerate(hits, start=1):
        chunk = hit.chunk
        preview = chunk.text.replace("\n", " ")[:160]
        bm25 = f"{hit.bm25_score:.4f}" if hit.bm25_score is not None else "-"
        cosine = f"{hit.cosine_score:.4f}" if hit.cosine_score is not None else "-"
        print(
            f"{rank}. rrf={hit.rrf_score:.4f}  cosine={cosine}  bm25={bm25}  "
            f"chunk_id={chunk.chunk_id}  page={chunk.page_start}  "
            f"bm25=#{hit.bm25_rank or '-'}  dense=#{hit.dense_rank or '-'}"
        )
        if chunk.unit_title:
            print(f"   unit: {chunk.unit_title}")
        print(f"   {preview}...")


def main() -> int:
    _load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = _build_parser().parse_args()

    config = IngestionConfig.for_sample_book()
    sections_dir = args.sections_dir or config.normalized_sections_dir
    queries = args.query or DEFAULT_QUERIES

    logger.info("Loading chunks from %s", sections_dir)
    chunks = load_chunks_from_sections(sections_dir)
    logger.info("Loaded %d chunks", len(chunks))

    logger.info(
        "Indexing with %s embeddings (%s)",
        args.embedding_provider,
        args.embedding_model or "default",
    )
    embeddings = create_embeddings(
        args.embedding_provider,
        model=args.embedding_model,
    )
    retriever = HybridRetriever(chunks, embeddings)
    retriever.index()

    for query in queries:
        hits = retriever.search(query, k=args.top_k)
        _print_hits(query, hits, as_json=args.json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
