"""CLI entry point for the MicroMaster scraper.

Typical usage:

    python -m scraper --book --workbook --chapters 1-3
    python -m scraper --book --workbook                 # all 24 chapters
    python -m scraper --workbook-only --chapters 1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import delete

from .book_parser import parse_book
from .db import (
    BookChapter,
    BookSection,
    WorkbookChapter,
    WorkbookExercise,
    WorkbookSection,
    make_engine,
    make_session_factory,
)
from .workbook_parser import parse_workbook

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOOK = PROJECT_ROOT / "data" / "sources" / "book.pdf"
DEFAULT_WORKBOOK = PROJECT_ROOT / "data" / "sources" / "workbook.pdf"
DEFAULT_DB = PROJECT_ROOT / "data" / "micromaster.db"


def parse_chapter_filter(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out or None


def build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Scrape Automate the Boring Stuff PDFs into SQLite.")
    p.add_argument("--book", action="store_true", help="Scrape the main book.")
    p.add_argument("--workbook", action="store_true", help="Scrape the workbook.")
    p.add_argument(
        "--chapters",
        type=str,
        default=None,
        help="Chapter filter e.g. '1-3' or '1,4,7'. Defaults to all 24.",
    )
    p.add_argument("--book-pdf", type=Path, default=DEFAULT_BOOK)
    p.add_argument("--workbook-pdf", type=Path, default=DEFAULT_WORKBOOK)
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_cli().parse_args(argv)
    if not args.book and not args.workbook:
        print("Specify --book, --workbook, or both.", file=sys.stderr)
        return 2

    chapter_filter = parse_chapter_filter(args.chapters)

    engine = make_engine(args.db)
    Session = make_session_factory(engine)

    if args.book:
        if not args.book_pdf.exists():
            print(f"Missing main book PDF: {args.book_pdf}", file=sys.stderr)
            return 1
        print(f"Scraping main book from {args.book_pdf.name}...")
        if chapter_filter:
            print(f"  chapters: {sorted(chapter_filter)}")
        book_rows = parse_book(args.book_pdf, chapter_filter=chapter_filter)
        with Session() as session:
            # Idempotent: delete sections first, then chapters. Explicit
            # sections-first delete avoids relying on SQLite cascade
            # semantics across connections.
            if chapter_filter:
                ids = [
                    row[0]
                    for row in session.execute(
                        BookChapter.__table__.select().with_only_columns(BookChapter.id).where(
                            BookChapter.number.in_(chapter_filter)
                        )
                    ).all()
                ]
                if ids:
                    session.execute(delete(BookSection).where(BookSection.chapter_id.in_(ids)))
                session.execute(delete(BookChapter).where(BookChapter.number.in_(chapter_filter)))
            else:
                session.execute(delete(BookSection))
                session.execute(delete(BookChapter))
            session.flush()
            for ch, sections in book_rows:
                session.add(ch)
                session.flush()
                for s in sections:
                    s.chapter_id = ch.id
                    session.add(s)
                print(
                    f"  ch{ch.number:02d} {ch.title!r}: {len(sections)} sections, "
                    f"p{ch.start_page}-{ch.end_page}"
                )
            session.commit()

    if args.workbook:
        if not args.workbook_pdf.exists():
            print(f"Missing workbook PDF: {args.workbook_pdf}", file=sys.stderr)
            return 1
        print(f"Scraping workbook from {args.workbook_pdf.name}...")
        if chapter_filter:
            print(f"  chapters: {sorted(chapter_filter)}")
        wb_rows = parse_workbook(args.workbook_pdf, chapter_filter=chapter_filter)
        with Session() as session:
            if chapter_filter:
                ids = [
                    row[0]
                    for row in session.execute(
                        WorkbookChapter.__table__.select().with_only_columns(WorkbookChapter.id).where(
                            WorkbookChapter.number.in_(chapter_filter)
                        )
                    ).all()
                ]
                if ids:
                    session.execute(delete(WorkbookExercise).where(WorkbookExercise.chapter_id.in_(ids)))
                    session.execute(delete(WorkbookSection).where(WorkbookSection.chapter_id.in_(ids)))
                session.execute(delete(WorkbookChapter).where(WorkbookChapter.number.in_(chapter_filter)))
            else:
                session.execute(delete(WorkbookExercise))
                session.execute(delete(WorkbookSection))
                session.execute(delete(WorkbookChapter))
            session.flush()
            for ch, sections, exercises in wb_rows:
                session.add(ch)
                session.flush()
                for s in sections:
                    s.chapter_id = ch.id
                    session.add(s)
                for ex in exercises:
                    ex.chapter_id = ch.id
                    session.add(ex)
                print(
                    f"  ch{ch.number:02d} {ch.title!r}: {len(sections)} sections, "
                    f"{len(exercises)} exercises, p{ch.start_page}-{ch.end_page}"
                )
            session.commit()

    print(f"Done. Database: {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
