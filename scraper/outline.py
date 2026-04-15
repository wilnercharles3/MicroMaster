"""Parse a PDF outline (bookmarks) into a flat list of entries with page
numbers. Handles both book and workbook conventions.

Chapter detection:
- Main book:   entries starting with r"^\\d+\\.\\s+" at outline depth 2
               (under Part I / Part II parents).
- Workbook:    entries starting with r"^\\d+[A-Z ]" at outline depth 0
               (e.g. "1PYTHON BASICS", "10READING AND WRITING FILES").

Callers get back typed dataclasses (`OutlineEntry`) so the rest of the
scraper doesn't touch pypdf internals.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


@dataclass
class OutlineEntry:
    title: str
    page: int  # 1-based
    depth: int
    children: list["OutlineEntry"] = field(default_factory=list)


def load_outline(pdf_path: Path) -> list[OutlineEntry]:
    """Return the PDF's outline as a nested list of OutlineEntry."""
    reader = PdfReader(str(pdf_path))
    raw = reader.outline or []

    def walk(items: Iterable, depth: int) -> list[OutlineEntry]:
        result: list[OutlineEntry] = []
        pending: OutlineEntry | None = None
        for it in items:
            if isinstance(it, list):
                if pending is None:
                    continue
                pending.children = walk(it, depth + 1)
            else:
                title = (getattr(it, "title", "") or "").strip()
                try:
                    page = reader.get_destination_page_number(it) + 1
                except Exception:
                    page = 0
                pending = OutlineEntry(title=title, page=page, depth=depth)
                result.append(pending)
        return result

    return walk(raw, 0)


def flatten(entries: list[OutlineEntry]) -> list[OutlineEntry]:
    """Flatten a nested outline in document order."""
    out: list[OutlineEntry] = []

    def rec(items: list[OutlineEntry]) -> None:
        for e in items:
            out.append(e)
            if e.children:
                rec(e.children)

    rec(entries)
    return out


# --- Chapter detection -------------------------------------------------------

_BOOK_CHAPTER_RE = re.compile(r"^(\d{1,2})\.\s+(.+)$")
# Workbook labels: "1PYTHON BASICS", "10READING AND WRITING FILES",
# and occasionally "2 IF-ELSE AND FLOW CONTROL" with a space after the
# number. Allow optional whitespace between digit and first letter.
_WORKBOOK_CHAPTER_RE = re.compile(r"^(\d{1,2})\s*([A-Z].*)$")


@dataclass
class ChapterSpec:
    number: int
    title: str
    start_page: int
    end_page: int  # inclusive; set by caller via page-span resolution
    entry: OutlineEntry


def find_book_chapters(entries: list[OutlineEntry]) -> list[ChapterSpec]:
    """Find the 24 numbered chapters in the main book outline."""
    chapters: list[ChapterSpec] = []
    for e in flatten(entries):
        m = _BOOK_CHAPTER_RE.match(e.title)
        if not m:
            continue
        num = int(m.group(1))
        if not 1 <= num <= 24:
            continue
        # Guard: avoid duplicate matches from index/TOC entries that
        # happen to parse. Real chapters always have sub-entries.
        if not e.children:
            continue
        chapters.append(
            ChapterSpec(
                number=num,
                title=m.group(2).strip(),
                start_page=e.page,
                end_page=0,  # resolved later
                entry=e,
            )
        )
    # De-duplicate by number keeping the first, in case.
    seen: dict[int, ChapterSpec] = {}
    for c in chapters:
        seen.setdefault(c.number, c)
    return sorted(seen.values(), key=lambda c: c.number)


def find_workbook_chapters(entries: list[OutlineEntry]) -> list[ChapterSpec]:
    """Find the 24 chapters in the workbook outline."""
    chapters: list[ChapterSpec] = []
    for e in flatten(entries):
        m = _WORKBOOK_CHAPTER_RE.match(e.title)
        if not m:
            continue
        num = int(m.group(1))
        if not 1 <= num <= 24:
            continue
        title_raw = m.group(2).strip()
        # Convert "PYTHON BASICS" to "Python Basics" for display parity.
        title = " ".join(w.capitalize() for w in title_raw.split())
        chapters.append(
            ChapterSpec(
                number=num,
                title=title,
                start_page=e.page,
                end_page=0,
                entry=e,
            )
        )
    seen: dict[int, ChapterSpec] = {}
    for c in chapters:
        seen.setdefault(c.number, c)
    return sorted(seen.values(), key=lambda c: c.number)


def resolve_end_pages(chapters: list[ChapterSpec], total_pages: int) -> None:
    """Fill in each chapter's end_page using the next chapter's start_page.

    The final chapter is treated as running to the last page of the PDF.
    """
    for i, ch in enumerate(chapters):
        if i + 1 < len(chapters):
            ch.end_page = chapters[i + 1].start_page - 1
        else:
            ch.end_page = total_pages
        # Guard against inverted ranges.
        if ch.end_page < ch.start_page:
            ch.end_page = ch.start_page
