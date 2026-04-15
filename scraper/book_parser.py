"""Main-book parser: reads the outline, resolves section page ranges, and
extracts section text using pdfplumber.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .cleaners import clean_extracted
from .db import BookChapter, BookSection
from .extract import PDFContext, open_pdf
from .outline import (
    ChapterSpec,
    OutlineEntry,
    find_book_chapters,
    flatten,
    load_outline,
    resolve_end_pages,
)


@dataclass
class SectionSpec:
    order_index: int
    title: str
    depth: int
    start_page: int
    end_page: int


def collect_section_specs(ch: ChapterSpec) -> list[SectionSpec]:
    """Flatten a chapter's outline subtree into ordered SectionSpec rows."""
    entries: list[OutlineEntry] = flatten(ch.entry.children)
    specs: list[SectionSpec] = []
    for i, e in enumerate(entries):
        # depth is relative to the chapter root (0 = direct child)
        specs.append(
            SectionSpec(
                order_index=i,
                title=e.title,
                depth=e.depth - (ch.entry.depth + 1),
                start_page=e.page,
                end_page=0,
            )
        )
    for i, s in enumerate(specs):
        if i + 1 < len(specs):
            s.end_page = specs[i + 1].start_page - 1
        else:
            s.end_page = ch.end_page
        if s.end_page < s.start_page:
            s.end_page = s.start_page
    return specs


def parse_book(
    pdf_path: Path,
    *,
    chapter_filter: set[int] | None = None,
) -> list[tuple[BookChapter, list[BookSection]]]:
    """Return fully populated (but unsaved) BookChapter / BookSection rows.

    Pass `chapter_filter={1, 2, 3}` to limit to specific chapters (used in
    phase 2 smoke-test runs to keep iteration fast).
    """
    outline = load_outline(pdf_path)
    chapters = find_book_chapters(outline)
    results: list[tuple[BookChapter, list[BookSection]]] = []

    with open_pdf(pdf_path) as ctx:
        resolve_end_pages(chapters, ctx.total_pages)
        for ch in chapters:
            if chapter_filter is not None and ch.number not in chapter_filter:
                continue
            book_ch = BookChapter(
                number=ch.number,
                title=ch.title,
                start_page=ch.start_page,
                end_page=ch.end_page,
                source_ref=f"pdf:book.pdf#p={ch.start_page}",
            )
            sections: list[BookSection] = []
            for spec in collect_section_specs(ch):
                text = _extract(ctx, spec.start_page, spec.end_page)
                sections.append(
                    BookSection(
                        order_index=spec.order_index,
                        title=spec.title,
                        depth=spec.depth,
                        start_page=spec.start_page,
                        end_page=spec.end_page,
                        text=text,
                        source_ref=f"pdf:book.pdf#p={spec.start_page}",
                    )
                )
            results.append((book_ch, sections))
    return results


def _extract(ctx: PDFContext, start: int, end: int) -> str:
    from .extract import extract_page_range

    return extract_page_range(ctx, start, end)
