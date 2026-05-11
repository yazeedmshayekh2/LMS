"""Stage 1 preprocessing for textbook PDFs (no OCR).

Profiles each page with PyMuPDF layout signals, classifies page type, and
compares text-layer backends (PyMuPDF, pypdf, pdfplumber) plus optional
Docling markdown export.

Run from repo root:
  uv run python src/pipeline/run_preprocess.py
  uv run python src/pipeline/run_preprocess.py --skip-docling
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
from pipeline.ingestion.preprocess.pipeline import run_preprocessing


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preprocess a textbook PDF.")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="Path to the source PDF (defaults to the sample science book).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for preprocessing artifacts.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Number of pages to profile (default: 10).",
    )
    parser.add_argument(
        "--all-pages",
        action="store_true",
        help="Process the full document instead of --max-pages.",
    )
    parser.add_argument(
        "--skip-docling",
        action="store_true",
        help="Skip Docling markdown export (faster local iteration).",
    )
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=None,
        help="Optional cap on extracted text length per backend (default: full page text).",
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
        include_docling=not args.skip_docling,
    )
    if args.pdf is not None:
        config.pdf_path = args.pdf
    if args.output_dir is not None:
        config.output_dir = args.output_dir
    if args.preview_chars is not None:
        config.preview_chars = args.preview_chars

    report = run_preprocessing(config)
    print(f"Wrote preprocessing report for {report.processed_pages} page(s):")
    print(f"  {config.output_dir / 'preprocess_report.json'}")
    print(f"  {config.output_dir / 'preprocess_summary.md'}")
    print(f"  {config.pages_dir}/page_###.json")
    print(f"  {config.backends_dir}/<backend>/page_###.txt")
    if report.docling_markdown_path:
        print(f"  {report.docling_markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
