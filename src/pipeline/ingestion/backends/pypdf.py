from __future__ import annotations

from pathlib import Path


def extract_pypdf_page(pdf_path: Path, page_number: int) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    page = reader.pages[page_number - 1]
    return (page.extract_text() or "").strip()
