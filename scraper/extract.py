"""Page-range text extraction from a PDF, using pdfplumber.

Keeps the pdfplumber handle open so repeated per-chapter extractions
don't re-parse the 1450-page book from scratch every time. Call
`open_pdf(path)` as a context manager and pass the PDFContext into the
extraction helpers.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pdfplumber

from .cleaners import clean_extracted


@dataclass
class PDFContext:
    path: Path
    pdf: pdfplumber.PDF

    @property
    def total_pages(self) -> int:
        return len(self.pdf.pages)


@contextmanager
def open_pdf(path: Path) -> Iterator[PDFContext]:
    with pdfplumber.open(str(path)) as pdf:
        yield PDFContext(path=path, pdf=pdf)


def extract_page_range(
    ctx: PDFContext,
    start_page: int,
    end_page: int,
    *,
    strip_running_text: bool = True,
) -> str:
    """Extract cleaned text from 1-based inclusive page range."""
    texts: list[str] = []
    start_idx = max(0, start_page - 1)
    end_idx = min(ctx.total_pages - 1, end_page - 1)
    for idx in range(start_idx, end_idx + 1):
        try:
            page = ctx.pdf.pages[idx]
            raw = page.extract_text() or ""
        except Exception:
            raw = ""
        if strip_running_text:
            # Drop the first line if it's a short header (page number or
            # running title); these are typically 1-6 words.
            lines = raw.split("\n", 1)
            if len(lines) == 2 and len(lines[0]) < 80 and not lines[0].rstrip().endswith((".", ":")):
                raw = lines[1]
        texts.append(raw)
    return clean_extracted("\n\n".join(texts))
