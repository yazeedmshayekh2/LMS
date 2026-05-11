"""Export readable Markdown without per-chunk YAML frontmatter.

Reads stage-3 section files and writes body-only copies under:
  assets/normalized/readable/sections/
  assets/normalized/readable/document.md

Run from repo root:
  uv run python src/pipeline/run_export_readable.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from pipeline.ingestion.config import IngestionConfig
from pipeline.ingestion.normalize.reader_export import (
    export_readable_document,
    export_readable_sections,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export readable Markdown without chunk frontmatter.",
    )
    parser.add_argument(
        "--normalized-dir",
        type=Path,
        default=None,
        help="Stage-3 normalized output directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    pipeline_dir = Path(__file__).resolve().parent
    config = IngestionConfig.for_sample_book(pipeline_dir, max_pages=None)
    if args.normalized_dir is not None:
        config.normalized_output_dir = args.normalized_dir

    sections_dir = config.normalized_sections_dir
    if not sections_dir.is_dir():
        print(f"Normalized sections not found: {sections_dir}", file=sys.stderr)
        return 1

    readable_sections_dir = config.normalized_markdown_dir / "readable" / "sections"
    written = export_readable_sections(sections_dir, output_dir=readable_sections_dir)
    document_path = export_readable_document(
        sections_dir,
        output_path=config.normalized_markdown_dir / "readable" / "document.md",
    )

    print("Wrote readable Markdown without chunk frontmatter:")
    print(f"  {document_path}")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
