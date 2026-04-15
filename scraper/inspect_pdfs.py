"""One-off script: inspect PDF structure to inform parser design.

Prints TOC (outline) entries, page counts, and samples of the first few
pages with font information so we can design a robust chapter detector.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOOK = PROJECT_ROOT / "data" / "sources" / "book.pdf"
WORKBOOK = PROJECT_ROOT / "data" / "sources" / "workbook.pdf"


def print_outline(pdf_path: Path, label: str) -> None:
    print(f"\n=== {label}: {pdf_path.name} ===")
    reader = PdfReader(str(pdf_path))
    print(f"Pages: {len(reader.pages)}")
    try:
        outlines = reader.outline
    except Exception as e:
        print(f"No outline accessible: {e}")
        return

    def walk(items, depth: int = 0) -> None:
        for it in items:
            if isinstance(it, list):
                walk(it, depth + 1)
            else:
                title = getattr(it, "title", str(it))
                try:
                    page_num = reader.get_destination_page_number(it) + 1
                except Exception:
                    page_num = "?"
                print(f"{'  ' * depth}[p{page_num}] {title}")

    if outlines:
        walk(outlines)
    else:
        print("(no outline / bookmarks)")


def font_sample(pdf_path: Path, label: str, page_indexes: list[int]) -> None:
    print(f"\n--- Font sample from {label} ---")
    with pdfplumber.open(str(pdf_path)) as pdf:
        for idx in page_indexes:
            if idx >= len(pdf.pages):
                continue
            page = pdf.pages[idx]
            chars = page.chars[:30]
            fonts = {(c.get("fontname"), round(c.get("size", 0), 1)) for c in page.chars}
            print(f"\nPage {idx + 1}: {len(page.chars)} chars, fonts: {sorted(fonts)[:8]}")
            text = page.extract_text() or ""
            preview = text[:400].replace("\n", " | ")
            print(f"Text preview: {preview}")


def main() -> int:
    if not BOOK.exists():
        print(f"Missing: {BOOK}", file=sys.stderr)
        return 1
    if not WORKBOOK.exists():
        print(f"Missing: {WORKBOOK}", file=sys.stderr)
        return 1

    print_outline(BOOK, "MAIN BOOK")
    font_sample(BOOK, "MAIN BOOK", [0, 5, 15, 30])

    print_outline(WORKBOOK, "WORKBOOK")
    font_sample(WORKBOOK, "WORKBOOK", [0, 1, 5, 10])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
