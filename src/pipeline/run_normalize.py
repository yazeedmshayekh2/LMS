"""Stage 3 schema-first LLM normalization for textbook Markdown.

Consumes stage-2 raw Markdown, batches pages with TOC context, and writes
normalized sections plus QC metrics.

Run from repo root:
  uv run python src/pipeline/run_preprocess.py --skip-docling --max-pages 10
  uv run python src/pipeline/run_extract.py --max-pages 10
  uv run python src/pipeline/run_normalize.py --provider gemini --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from pipeline.ingestion.config import IngestionConfig
from pipeline.ingestion.normalize.pipeline import run_normalization


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize raw textbook Markdown.")
    parser.add_argument("--provider", default="gemini")
    parser.add_argument("--model", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--preprocess-dir", type=Path, default=None)
    parser.add_argument("--raw-markdown-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
        force=True,
    )

    pipeline_dir = Path(__file__).resolve().parent
    config = IngestionConfig.for_sample_book(pipeline_dir, max_pages=args.max_pages)
    if args.preprocess_dir is not None:
        config.output_dir = args.preprocess_dir
    if args.raw_markdown_dir is not None:
        config.raw_markdown_output_dir = args.raw_markdown_dir
    if args.output_dir is not None:
        config.normalized_output_dir = args.output_dir
    config.normalize_batch_size = args.batch_size
    config.normalize_dry_run = args.dry_run

    report = run_normalization(
        config,
        provider_name=args.provider,
        model=args.model,
        dry_run=args.dry_run,
    )
    print(f"Wrote normalized Markdown for {report.processed_pages} page(s):")
    print(f"  {report.document_markdown_path}")
    print(f"  {config.normalized_sections_dir}/p###_###.md")
    print(f"  {config.normalized_markdown_dir / 'readable/document.md'}")
    print(f"  {config.normalized_markdown_dir / 'readable/sections'}/p###_###.md")
    print(f"  {report.qc_report_path}")
    print(f"  {config.normalized_markdown_dir / 'normalize_report.json'}")
    if report.dry_run:
        print("Dry-run mode: prompts and placeholder sections were written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
