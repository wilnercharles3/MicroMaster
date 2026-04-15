"""Quick sanity check on the scraped database.

Prints row counts, a sample section preview, and flags any empty rows.
Used at the end of Phase 2 to confirm the scraper produced usable data.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select

from .db import (
    BookChapter,
    BookSection,
    WorkbookChapter,
    WorkbookExercise,
    WorkbookSection,
    make_engine,
    make_session_factory,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB = PROJECT_ROOT / "data" / "micromaster.db"


def main() -> int:
    engine = make_engine(DB)
    Session = make_session_factory(engine)
    with Session() as s:
        bc = s.scalar(select(func.count(BookChapter.id)))
        bs = s.scalar(select(func.count(BookSection.id)))
        wc = s.scalar(select(func.count(WorkbookChapter.id)))
        ws = s.scalar(select(func.count(WorkbookSection.id)))
        we = s.scalar(select(func.count(WorkbookExercise.id)))
        print(f"book_chapters:     {bc}")
        print(f"book_sections:     {bs}")
        print(f"workbook_chapters: {wc}")
        print(f"workbook_sections: {ws}")
        print(f"workbook_exercises:{we}")

        empty_sections = s.scalars(
            select(BookSection).where(func.length(BookSection.text) < 50).limit(5)
        ).all()
        if empty_sections:
            print("\nBook sections with very short text (possible parse miss):")
            for sec in empty_sections:
                print(f"  ch{sec.chapter_id} #{sec.order_index} '{sec.title}' ({len(sec.text)} chars, p{sec.start_page}-{sec.end_page})")

        print("\nSample book section (ch1, section 1):")
        sec = s.scalar(
            select(BookSection).join(BookChapter).where(
                BookChapter.number == 1, BookSection.order_index == 1
            )
        )
        if sec:
            preview = sec.text[:300].replace("\n", " | ")
            print(f"  title: {sec.title}")
            print(f"  pages: {sec.start_page}-{sec.end_page}")
            print(f"  source_ref: {sec.source_ref}")
            print(f"  text length: {len(sec.text)} chars")
            print(f"  preview: {preview}...")

        print("\nSample workbook exercise (ch1, exercise 0):")
        ex = s.scalar(
            select(WorkbookExercise).join(WorkbookChapter).where(
                WorkbookChapter.number == 1, WorkbookExercise.order_index == 0
            )
        )
        if ex:
            preview = ex.text[:240].replace("\n", " | ")
            print(f"  kind: {ex.kind}")
            print(f"  title: {ex.title}")
            print(f"  source_ref: {ex.source_ref}")
            print(f"  text length: {len(ex.text)} chars")
            print(f"  preview: {preview}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
