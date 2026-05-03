"""Extract text from the first 10 pages of the sample PDF using several Python tools.

Writes one UTF-8 file per tool next to this script:
  pdf_mining_first10_pypdf.txt
  pdf_mining_first10_pymupdf.txt
  pdf_mining_first10_structure_pymupdf.txt  — layout: blocks/lines/spans + tables
  pdf_mining_first10_pdfplumber.txt         — extract_text + extract_tables
  pdf_mining_first10_docling.txt            — DocumentConverter → Markdown
  pdf_mining_first10_ocr.txt

Other options (not wired here): Unstructured (partition_pdf).

Docling may download models on first run and is slower than plain text extractors.

Run from repo root:
  uv run python src/pipeline/test_pdf_mining_first10.py
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_PAGES = 10

PDF_FILENAME = "علوم ثامن طالب ف1 S .pdf"

OUTPUT_PYPDF = "assets/pdf_mining_first10_pypdf.txt"
OUTPUT_PYMUPDF = "assets/pdf_mining_first10_pymupdf.txt"
OUTPUT_STRUCTURE_PYMUPDF = "assets/pdf_mining_first10_structure_pymupdf.txt"
OUTPUT_PDFPLUMBER = "assets/pdf_mining_first10_pdfplumber.txt"
OUTPUT_DOCLING = "assets/pdf_mining_first10_docling.txt"
OUTPUT_OCR = "assets/pdf_mining_first10_ocr.txt"


def _append(blocks: list[str], title: str) -> None:
    blocks.append("=" * 72)
    blocks.append(title)
    blocks.append("=" * 72)


def _report_header(pdf_path: Path) -> list[str]:
    return [
        f"PDF mining — first {MAX_PAGES} pages",
        f"Source: {pdf_path}",
        f"Written: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]


def run_pypdf(pdf_path: Path) -> list[str]:
    blocks = _report_header(pdf_path)
    logging.info("Starting pypdf (text layer extraction)")
    _append(blocks, "TOOL: pypdf — PdfReader.pages[i].extract_text()")
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        total = len(reader.pages)
        n = min(MAX_PAGES, total)
        blocks.append(f"(document pages: {total}, extracting: {n})\n")
        for i in range(n):
            logging.info("  pypdf page %s/%s", i + 1, n)
            blocks.append(f"\n--- Page {i + 1} ---\n")
            raw = reader.pages[i].extract_text()
            text = (raw or "").strip()
            blocks.append(text if text else "(no text layer or empty extract)")
        logging.info("Finished pypdf")
    except Exception as exc:  # noqa: BLE001 — benchmark script
        logging.warning("pypdf failed: %s", exc)
        blocks.append(f"FAILED: {exc!r}\n")
    return blocks


def run_pymupdf(pdf_path: Path) -> list[str]:
    blocks = _report_header(pdf_path)
    logging.info("Starting pymupdf (text layer extraction)")
    _append(blocks, "TOOL: pymupdf — page.get_text()")
    try:
        import fitz

        doc = fitz.open(pdf_path)
        try:
            total = doc.page_count
            n = min(MAX_PAGES, total)
            blocks.append(f"(document pages: {total}, extracting: {n})\n")
            for i in range(n):
                logging.info("  pymupdf page %s/%s", i + 1, n)
                blocks.append(f"\n--- Page {i + 1} ---\n")
                raw = doc.load_page(i).get_text()
                text = (raw or "").strip()
                blocks.append(text if text else "(no text or empty extract)")
        finally:
            doc.close()
        logging.info("Finished pymupdf")
    except Exception as exc:  # noqa: BLE001
        logging.warning("pymupdf failed: %s", exc)
        blocks.append(f"FAILED: {exc!r}\n")
    return blocks


def _format_text_block_dict(block: dict, block_index: int) -> list[str]:
    """Turn one PyMuPDF text block from get_text('dict') into readable lines."""
    out: list[str] = []
    btype = block.get("type", 0)
    bbox = block.get("bbox")
    out.append(f"Block {block_index} type={btype} bbox={bbox!r}")
    if btype != 0:
        out.append("  (non-text block, e.g. image — no spans)")
        return out
    for li, line in enumerate(block.get("lines", [])):
        lb = line.get("bbox")
        span_parts: list[str] = []
        for span in line.get("spans", []):
            text = span.get("text", "")
            font = span.get("font", "")
            size = span.get("size", 0)
            span_parts.append(f"{text!r} [{font} {size:g}pt]")
        joined = " ".join(span_parts) if span_parts else "(empty line)"
        out.append(f"  Line {li} bbox={lb!r}")
        out.append(f"    {joined}")
    return out


def run_pymupdf_structure(pdf_path: Path) -> list[str]:
    """Layout-aware extract: block/line/span geometry + optional table grids."""
    blocks = _report_header(pdf_path)
    logging.info("Starting pymupdf structure (dict layout + find_tables)")
    _append(
        blocks,
        "TOOL: pymupdf — get_text('dict') blocks/lines/spans + find_tables()",
    )
    try:
        import fitz

        doc = fitz.open(pdf_path)
        try:
            total = doc.page_count
            n = min(MAX_PAGES, total)
            blocks.append(f"(document pages: {total}, extracting: {n})\n")
            for i in range(n):
                logging.info("  pymupdf structure page %s/%s", i + 1, n)
                page = doc.load_page(i)
                blocks.append(f"\n--- Page {i + 1} ---\n")

                td = page.get_text("dict")
                text_blocks = [b for b in td.get("blocks", []) if b.get("type") == 0]
                blocks.append(
                    f"Text blocks: {len(text_blocks)} "
                    f"(total blocks in dict: {len(td.get('blocks', []))})\n"
                )
                for bi, bdict in enumerate(text_blocks):
                    blocks.extend(_format_text_block_dict(bdict, bi))
                    blocks.append("")

                blocks.append("-- Tables (find_tables) --\n")
                try:
                    finder = page.find_tables()
                    tables = finder.tables
                except AttributeError:
                    tables = []
                    blocks.append(
                        "(page.find_tables not available in this PyMuPDF build)\n"
                    )
                if tables:
                    for ti, tab in enumerate(tables):
                        try:
                            grid = tab.extract()
                        except Exception as ex:  # noqa: BLE001
                            blocks.append(f"Table {ti + 1}: extract failed: {ex!r}\n")
                            continue
                        blocks.append(f"Table {ti + 1} ({len(grid)} rows)\n")
                        for row in grid:
                            cells = [
                                str(c).strip() if c is not None else "" for c in row
                            ]
                            blocks.append("  | " + " | ".join(cells))
                        blocks.append("")
                else:
                    blocks.append("(no tables detected on this page)\n")
        finally:
            doc.close()
        logging.info("Finished pymupdf structure")
    except Exception as exc:  # noqa: BLE001
        logging.warning("pymupdf structure failed: %s", exc)
        blocks.append(f"FAILED: {exc!r}\n")
    return blocks


def run_pdfplumber(pdf_path: Path) -> list[str]:
    blocks = _report_header(pdf_path)
    logging.info("Starting pdfplumber (extract_text + extract_tables)")
    _append(blocks, "TOOL: pdfplumber — page.extract_text() + extract_tables()")
    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            n = min(MAX_PAGES, total)
            blocks.append(f"(document pages: {total}, extracting: {n})\n")
            for i in range(n):
                logging.info("  pdfplumber page %s/%s", i + 1, n)
                page = pdf.pages[i]
                blocks.append(f"\n--- Page {i + 1} ---\n")
                raw = page.extract_text()
                text = (raw or "").strip()
                blocks.append(text if text else "(no text or empty extract)")

                blocks.append("\n-- extract_tables() --\n")
                table_rows = page.extract_tables()
                if table_rows:
                    for ti, table in enumerate(table_rows):
                        blocks.append(f"Table {ti + 1}\n")
                        for row in table or []:
                            cells = [
                                str(c).strip() if c is not None else ""
                                for c in (row or [])
                            ]
                            blocks.append("  | " + " | ".join(cells))
                        blocks.append("")
                else:
                    blocks.append("(no tables on this page)\n")
        logging.info("Finished pdfplumber")
    except Exception as exc:  # noqa: BLE001
        logging.warning("pdfplumber failed: %s", exc)
        blocks.append(f"FAILED: {exc!r}\n")
    return blocks


def run_docling(pdf_path: Path) -> list[str]:
    blocks = _report_header(pdf_path)
    logging.info("Starting Docling DocumentConverter (first run may download models)")
    _append(
        blocks,
        "TOOL: docling — DocumentConverter.convert(page_range=(1, N)) → "
        "export_to_markdown()",
    )
    blocks.append(
        "Note: convert(max_num_pages=N) means “reject PDFs with more than N pages”, "
        "not “convert N pages”. Use page_range for the latter.\n",
    )
    try:
        from docling.document_converter import DocumentConverter  # type: ignore[import-untyped]

        converter = DocumentConverter()
        # page_range is inclusive, 1-based; omit max_num_pages so large books stay valid.
        result = converter.convert(
            pdf_path,
            page_range=(1, MAX_PAGES),
        )
        blocks.append(f"status: {result.status}\n")
        if getattr(result, "errors", None):
            blocks.append(f"errors: {result.errors}\n")
        if getattr(result, "timings", None) is not None:
            blocks.append(f"timings: {result.timings}\n")
        blocks.append("")
        md = result.document.export_to_markdown()
        text = (md or "").strip()
        blocks.append(text if text else "(empty markdown export)")
        logging.info("Finished Docling")
    except Exception as exc:  # noqa: BLE001
        logging.warning("Docling failed: %s", exc)
        blocks.append(f"FAILED: {exc!r}\n")
    return blocks


def run_ocr(pdf_path: Path) -> list[str]:
    blocks = _report_header(pdf_path)
    logging.info(
        "Starting OCR (pdf2image → pytesseract); this step is slow for many pages"
    )
    _append(
        blocks,
        "TOOL: pdf2image + pytesseract — image_to_string (lang=ara+eng)",
    )
    try:
        from pdf2image import convert_from_path
        import pytesseract

        logging.info("  Rasterizing PDF pages (poppler)…")
        images = convert_from_path(
            str(pdf_path),
            first_page=1,
            last_page=MAX_PAGES,
            dpi=200,
        )
        blocks.append(f"(rendered {len(images)} page image(s) at 200 DPI)\n")
        for idx, pil_img in enumerate(images, start=1):
            logging.info("  OCR page %s/%s (tesseract)", idx, len(images))
            blocks.append(f"\n--- Page {idx} ---\n")
            text = pytesseract.image_to_string(pil_img, lang="ara+eng")
            text = (text or "").strip()
            blocks.append(text if text else "(OCR returned empty string)")
        logging.info("Finished OCR")
    except Exception as exc:  # noqa: BLE001
        logging.warning("OCR failed: %s", exc)
        blocks.append(
            f"FAILED: {exc!r}\n"
            "(often: missing poppler-utils for pdf2image, "
            "or missing tesseract Arabic pack: tesseract-ocr-ara)\n"
        )
    return blocks


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
        force=True,
    )

    here = Path(__file__).resolve().parent
    pdf_path = here / PDF_FILENAME

    if not pdf_path.is_file():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    logging.info(
        "PDF mining: first %s pages → separate files per tool",
        MAX_PAGES,
    )

    outputs: list[tuple[str, Path, list[str]]] = [
        ("pypdf", here / OUTPUT_PYPDF, run_pypdf(pdf_path)),
        ("pymupdf", here / OUTPUT_PYMUPDF, run_pymupdf(pdf_path)),
        (
            "pymupdf-structure",
            here / OUTPUT_STRUCTURE_PYMUPDF,
            run_pymupdf_structure(pdf_path),
        ),
        ("pdfplumber", here / OUTPUT_PDFPLUMBER, run_pdfplumber(pdf_path)),
        ("docling", here / OUTPUT_DOCLING, run_docling(pdf_path)),
        ("ocr", here / OUTPUT_OCR, run_ocr(pdf_path)),
    ]

    for name, path, lines in outputs:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logging.info("Wrote %s (%s bytes) [%s]", path.name, path.stat().st_size, name)

    print("Wrote:")
    for _, path, _ in outputs:
        print(f"  {path} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
