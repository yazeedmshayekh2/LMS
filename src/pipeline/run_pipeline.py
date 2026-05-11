"""Run the textbook ingestion pipeline end to end.

Stages (in order):
  preprocess -> extract -> normalize -> readable

Add a new stage by registering it in pipeline.ingestion.runner.PIPELINE_STAGES.

Run from repo root:
  uv run python src/pipeline/run_pipeline.py --max-pages 10 --skip-docling
  uv run python src/pipeline/run_pipeline.py --only normalize --provider gemini
  uv run python src/pipeline/run_pipeline.py --list-stages
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
from pipeline.ingestion.runner import (
    PIPELINE_STAGES,
    PipelineContext,
    run_pipeline,
    stage_names,
)


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the textbook ingestion pipeline.")
    parser.add_argument("--list-stages", action="store_true", help="List registered stages.")
    parser.add_argument("--pdf", type=Path, default=None)
    parser.add_argument("--preprocess-dir", type=Path, default=None)
    parser.add_argument("--raw-markdown-dir", type=Path, default=None)
    parser.add_argument("--normalized-dir", type=Path, default=None)
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--all-pages", action="store_true")
    parser.add_argument("--skip-docling", action="store_true")
    parser.add_argument("--with-docling", action="store_true")
    parser.add_argument("--preview-chars", type=int, default=None)
    parser.add_argument("--from-stage", choices=stage_names(), default=None)
    parser.add_argument("--to-stage", choices=stage_names(), default=None)
    parser.add_argument("--only", nargs="+", choices=stage_names(), default=None)
    parser.add_argument("--provider", default="gemini")
    parser.add_argument("--model", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=1)
    return parser


def _build_context(args: argparse.Namespace, pipeline_dir: Path) -> PipelineContext:
    config = IngestionConfig.for_sample_book(
        pipeline_dir,
        max_pages=None if args.all_pages else args.max_pages,
        include_docling=not args.skip_docling,
    )
    if args.pdf is not None:
        config.pdf_path = args.pdf
    if args.preprocess_dir is not None:
        config.output_dir = args.preprocess_dir
    if args.raw_markdown_dir is not None:
        config.raw_markdown_output_dir = args.raw_markdown_dir
    if args.normalized_dir is not None:
        config.normalized_output_dir = args.normalized_dir
    if args.preview_chars is not None:
        config.preview_chars = args.preview_chars
    if args.with_docling:
        config.extract_include_docling = True

    config.normalize_batch_size = args.batch_size
    config.normalize_dry_run = args.dry_run

    return PipelineContext(
        config=config,
        provider=args.provider,
        model=args.model,
        dry_run=args.dry_run,
    )


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    args = _build_parser().parse_args(argv)

    if args.list_stages:
        for stage in PIPELINE_STAGES:
            print(f"{stage.name}: {stage.description}")
        return 0

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
        force=True,
    )

    pipeline_dir = Path(__file__).resolve().parent
    context = _build_context(args, pipeline_dir)
    results = run_pipeline(
        context,
        from_stage=args.from_stage,
        to_stage=args.to_stage,
        only=args.only,
    )

    print("Pipeline complete:")
    for result in results:
        print(f"- {result.stage}: {result.summary}")
        for artifact in result.artifacts:
            print(f"    {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
