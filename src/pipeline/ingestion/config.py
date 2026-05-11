from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class IngestionConfig:
    """Runtime settings for preprocessing and later ingestion stages."""

    pdf_path: Path
    output_dir: Path
    max_pages: int | None = 10
    preview_chars: int | None = None
    include_docling: bool = True
    include_pypdf: bool = True
    include_pymupdf: bool = True
    include_pdfplumber: bool = True
    include_structure: bool = True
    extract_include_docling: bool = False
    raw_markdown_output_dir: Path | None = None
    normalized_output_dir: Path | None = None
    normalize_batch_size: int = 2
    normalize_dry_run: bool = False

    @classmethod
    def for_sample_book(
        cls,
        pipeline_dir: Path | None = None,
        *,
        max_pages: int | None = 10,
        include_docling: bool = True,
    ) -> IngestionConfig:
        root = pipeline_dir or Path(__file__).resolve().parents[1]
        return cls(
            pdf_path=root / "علوم ثامن طالب ف1 S .pdf",
            output_dir=root / "assets" / "preprocess",
            max_pages=max_pages,
            include_docling=include_docling,
        )

    @property
    def pages_dir(self) -> Path:
        return self.output_dir / "pages"

    @property
    def backends_dir(self) -> Path:
        return self.output_dir / "backends"

    @property
    def preprocess_report_path(self) -> Path:
        return self.output_dir / "preprocess_report.json"

    @property
    def raw_markdown_dir(self) -> Path:
        if self.raw_markdown_output_dir is not None:
            return self.raw_markdown_output_dir
        return self.output_dir.parent / "raw_markdown"

    @property
    def raw_markdown_pages_dir(self) -> Path:
        return self.raw_markdown_dir / "pages"

    @property
    def extract_report_path(self) -> Path:
        return self.raw_markdown_dir / "extract_report.json"

    @property
    def normalized_markdown_dir(self) -> Path:
        if self.normalized_output_dir is not None:
            return self.normalized_output_dir
        return self.raw_markdown_dir.parent / "normalized"

    @property
    def normalized_sections_dir(self) -> Path:
        return self.normalized_markdown_dir / "sections"

    @property
    def normalized_pages_dir(self) -> Path:
        return self.normalized_markdown_dir / "pages"

    def ensure_output_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.backends_dir.mkdir(parents=True, exist_ok=True)

    def ensure_raw_markdown_dirs(self) -> None:
        self.raw_markdown_dir.mkdir(parents=True, exist_ok=True)
        self.raw_markdown_pages_dir.mkdir(parents=True, exist_ok=True)

    def ensure_normalized_dirs(self) -> None:
        self.normalized_markdown_dir.mkdir(parents=True, exist_ok=True)
        self.normalized_sections_dir.mkdir(parents=True, exist_ok=True)
        self.normalized_pages_dir.mkdir(parents=True, exist_ok=True)
