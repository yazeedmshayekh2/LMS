"""Stage 2 hybrid extraction to raw Markdown (no full-book OCR).

Uses stage-1 preprocess profiles when available, then emits per-page raw
Markdown with layout regions, table blocks, bilingual term pairs, and vision
OCR placeholders for image-heavy regions.

Run from repo root:
  uv run python src/pipeline/run_preprocess.py --skip-docling --max-pages 10
  uv run python src/pipeline/run_extract.py --max-pages 10
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
from pipeline.ingestion.extract.pipeline import run_extraction


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract raw Markdown from a textbook PDF.",
    )
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument(
        "--preprocess-dir",
        type=Path,
        default=None,
        help="Stage-1 preprocess output directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Stage-2 raw Markdown output directory.",
    )
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--all-pages", action="store_true")
    parser.add_argument(
        "--with-docling",
        action="store_true",
        help="Append a Docling layout appendix to document.md.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
        force=True,
    )

    pipeline_dir = Path(__file__).resolve().parent
    config = IngestionConfig.for_sample_book(
        pipeline_dir,
        max_pages=None if args.all_pages else args.max_pages,
        include_docling=False,
    )
    if args.pdf is not None:
        config.pdf_path = args.pdf
    if args.preprocess_dir is not None:
        config.output_dir = args.preprocess_dir
    if args.output_dir is not None:
        config.raw_markdown_output_dir = args.output_dir
    if args.with_docling:
        config.extract_include_docling = True

    report = run_extraction(config)
    print(f"Wrote raw Markdown for {report.processed_pages} page(s):")
    print(f"  {report.document_markdown_path}")
    print(f"  {config.raw_markdown_pages_dir}/page_###.md")
    print(f"  {config.raw_markdown_dir / 'extract_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
