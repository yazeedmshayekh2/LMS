from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PageLayoutBlock:
    index: int
    bbox: tuple[float, float, float, float]
    lines: list[str]
    max_font_size: float


@dataclass(slots=True)
class PageImageBlock:
    index: int
    bbox: tuple[float, float, float, float]


@dataclass(slots=True)
class PyMuPDFStructure:
    text_block_count: int
    non_text_block_count: int
    image_block_count: int
    table_count: int
    line_count: int
    span_count: int
    unique_fonts: list[str]
    median_font_size_pt: float | None
    tables: list[list[list[str]]]


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _line_text(line: dict) -> str:
    return "".join(span.get("text", "") for span in line.get("spans", []))


def _block_sort_key(block: dict) -> tuple[float, float]:
    bbox = block.get("bbox", (0.0, 0.0, 0.0, 0.0))
    return (round(float(bbox[1]), 1), -round(float(bbox[2]), 1))


def _text_blocks(page) -> list[dict]:
    blocks = page.get_text("dict", sort=True).get("blocks", [])
    text_blocks = [block for block in blocks if block.get("type") == 0]
    text_blocks.sort(key=_block_sort_key)
    return text_blocks


def extract_page_layout_blocks(pdf_path: Path, page_number: int) -> list[PageLayoutBlock]:
    import fitz

    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number - 1)
        layout_blocks: list[PageLayoutBlock] = []
        for index, block in enumerate(_text_blocks(page)):
            lines = [_line_text(line) for line in block.get("lines", [])]
            lines = [line for line in lines if line.strip()]
            if not lines:
                continue
            sizes = [
                float(span.get("size", 0))
                for line in block.get("lines", [])
                for span in line.get("spans", [])
                if isinstance(span.get("size"), (int, float))
            ]
            bbox = tuple(float(value) for value in block.get("bbox", (0.0, 0.0, 0.0, 0.0)))
            layout_blocks.append(
                PageLayoutBlock(
                    index=index,
                    bbox=(bbox[0], bbox[1], bbox[2], bbox[3]),
                    lines=lines,
                    max_font_size=max(sizes) if sizes else 0.0,
                )
            )
        return layout_blocks


def extract_page_image_blocks(pdf_path: Path, page_number: int) -> list[PageImageBlock]:
    import fitz

    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number - 1)
        blocks = page.get_text("dict", sort=True).get("blocks", [])
        image_blocks: list[PageImageBlock] = []
        for index, block in enumerate(blocks):
            if block.get("type") != 1:
                continue
            bbox = tuple(float(value) for value in block.get("bbox", (0.0, 0.0, 0.0, 0.0)))
            image_blocks.append(
                PageImageBlock(
                    index=index,
                    bbox=(bbox[0], bbox[1], bbox[2], bbox[3]),
                )
            )
        return image_blocks


def extract_pymupdf_page(pdf_path: Path, page_number: int) -> str:
    import fitz

    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number - 1)
        parts: list[str] = []
        for block in _text_blocks(page):
            lines = [_line_text(line) for line in block.get("lines", [])]
            lines = [line for line in lines if line.strip()]
            if lines:
                parts.append("\n".join(lines))
        return "\n\n".join(parts).strip()


def render_pymupdf_structure_text(pdf_path: Path, page_number: int) -> str:
    import fitz

    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number - 1)
        lines: list[str] = []
        for index, block in enumerate(_text_blocks(page)):
            bbox = block.get("bbox")
            lines.append(f"Block {index} bbox={bbox!r}")
            for line_index, line in enumerate(block.get("lines", [])):
                spans = line.get("spans", [])
                span_parts = [
                    f"{span.get('text', '')!r} [{span.get('font', '')} {span.get('size', 0):g}pt]"
                    for span in spans
                ]
                lines.append(f"  Line {line_index} bbox={line.get('bbox')!r}")
                lines.append(f"    {' '.join(span_parts) if span_parts else '(empty line)'}")
            lines.append("")

        lines.append("-- Tables (find_tables) --")
        try:
            tables = page.find_tables().tables
        except AttributeError:
            tables = []
            lines.append("(page.find_tables not available in this PyMuPDF build)")
        if tables:
            for table_index, table in enumerate(tables, start=1):
                grid = table.extract()
                lines.append(f"Table {table_index} ({len(grid)} rows)")
                for row in grid:
                    cells = [str(cell).strip() if cell is not None else "" for cell in row]
                    lines.append("  | " + " | ".join(cells))
                lines.append("")
        else:
            lines.append("(no tables detected on this page)")
        return "\n".join(lines).strip()


def extract_pymupdf_structure(pdf_path: Path, page_number: int) -> PyMuPDFStructure:
    import fitz

    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number - 1)
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])

        text_blocks = [block for block in blocks if block.get("type") == 0]
        non_text_blocks = [block for block in blocks if block.get("type") != 0]
        image_blocks = [
            block
            for block in non_text_blocks
            if block.get("type") == 1 or "image" in block
        ]

        fonts: set[str] = set()
        sizes: list[float] = []
        line_count = 0
        span_count = 0
        for block in text_blocks:
            for line in block.get("lines", []):
                line_count += 1
                for span in line.get("spans", []):
                    span_count += 1
                    font = span.get("font")
                    if font:
                        fonts.add(str(font))
                    size = span.get("size")
                    if isinstance(size, (int, float)):
                        sizes.append(float(size))

        tables: list[list[list[str]]] = []
        try:
            for table in page.find_tables().tables:
                grid = table.extract()
                if grid:
                    tables.append(
                        [
                            [str(cell).strip() if cell is not None else "" for cell in row]
                            for row in grid
                        ]
                    )
        except AttributeError:
            pass

        return PyMuPDFStructure(
            text_block_count=len(text_blocks),
            non_text_block_count=len(non_text_blocks),
            image_block_count=len(image_blocks),
            table_count=len(tables),
            line_count=line_count,
            span_count=span_count,
            unique_fonts=sorted(fonts),
            median_font_size_pt=_median(sizes),
            tables=tables,
        )


def page_geometry(pdf_path: Path, page_number: int) -> dict[str, Any]:
    import fitz

    with fitz.open(pdf_path) as doc:
        page = doc.load_page(page_number - 1)
        rect = page.rect
        mediabox = page.mediabox
        return {
            "width_pt": float(rect.width),
            "height_pt": float(rect.height),
            "rotation": int(page.rotation),
            "mediabox": (
                float(mediabox.x0),
                float(mediabox.y0),
                float(mediabox.x1),
                float(mediabox.y1),
            ),
        }
