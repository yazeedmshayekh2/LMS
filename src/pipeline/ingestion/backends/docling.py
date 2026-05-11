from __future__ import annotations

from pathlib import Path


def extract_docling_markdown(pdf_path: Path, *, first_page: int, last_page: int) -> str:
    from docling.document_converter import DocumentConverter  # type: ignore[import-untyped]

    converter = DocumentConverter()
    result = converter.convert(
        pdf_path,
        page_range=(first_page, last_page),
    )
    return (result.document.export_to_markdown() or "").strip()
