"""Export readable Markdown with LLM postprocessing.

Reads stage-3 section files and writes reader-friendly copies under:
  assets/normalized/readable/sections/
  assets/normalized/readable/document.md

Run from repo root:
  uv run python src/pipeline/run_export_readable.py
  uv run python src/pipeline/run_export_readable.py --provider gemini --model gemini-2.5-flash
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
from pipeline.ingestion.normalize.readable_pipeline import run_readable_export


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export readable Markdown with LLM postprocessing.",
    )
    parser.add_argument(
        "--normalized-dir",
        type=Path,
        default=None,
        help="Stage-3 normalized output directory.",
    )
    parser.add_argument("--provider", default="gemini")
    parser.add_argument("--model", default=None)
    parser.add_argument("--dry-run", action="store_true")
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
    config = IngestionConfig.for_sample_book(pipeline_dir, max_pages=None)
    if args.normalized_dir is not None:
        config.normalized_output_dir = args.normalized_dir

    report = run_readable_export(
        config,
        provider_name=args.provider,
        model=args.model,
        dry_run=args.dry_run,
    )

    print("Wrote readable Markdown:")
    print(f"  {report.document_path}")
    for path in report.section_paths:
        print(f"  {path}")
    if report.dry_run:
        print("Readable export ran in dry-run mode (no LLM postprocess).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
