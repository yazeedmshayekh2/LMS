from __future__ import annotations

from pathlib import Path

from pipeline.ingestion.backends.pdfplumber import extract_pdfplumber_page
from pipeline.ingestion.backends.pymupdf import extract_pymupdf_structure
from pipeline.ingestion.extract.models import ExtractedTable
from pipeline.ingestion.models import PageType


def extract_page_tables(
    pdf_path: Path,
    page_number: int,
    *,
    page_type: PageType,
) -> list[ExtractedTable]:
    structure = extract_pymupdf_structure(pdf_path, page_number)
    tables: list[ExtractedTable] = []
    for index, rows in enumerate(structure.tables, start=1):
        tables.append(ExtractedTable(index=index, source="pymupdf", rows=rows))

    if tables:
        return tables

    _, pdfplumber_tables = extract_pdfplumber_page(pdf_path, page_number)
    for index, rows in enumerate(pdfplumber_tables, start=1):
        tables.append(ExtractedTable(index=index, source="pdfplumber", rows=rows))

    if tables:
        return tables

    if page_type == PageType.TOC:
        return tables
    return tables
