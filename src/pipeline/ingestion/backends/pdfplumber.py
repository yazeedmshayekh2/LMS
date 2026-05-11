from __future__ import annotations

from pathlib import Path


def extract_pdfplumber_page(pdf_path: Path, page_number: int) -> tuple[str, list[list[list[str]]]]:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]
        text = (page.extract_text() or "").strip()
        tables = page.extract_tables() or []
        normalized_tables = [
            [
                [str(cell).strip() if cell is not None else "" for cell in (row or [])]
                for row in table
            ]
            for table in tables
        ]
        return text, normalized_tables
