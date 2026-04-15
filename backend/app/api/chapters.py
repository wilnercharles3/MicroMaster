"""/api/chapters endpoints.

Returns the 24-chapter roadmap data: main book chapters paired with
their workbook counterparts by chapter number, plus high-level progress
summary so the roadmap UI can render Learn / Practice / Miniproject /
Boss Battle node states without further round-trips.
"""
from __future__ import annotations

from flask import Blueprint, abort
from sqlalchemy import func, select

from scraper.db import BookChapter, BookSection, WorkbookChapter, WorkbookExercise

from ..config import DEFAULT_USER_ID
from ..models import MicroDose, UserProgress
from ._util import db_route, ok

bp = Blueprint("chapters", __name__)


def _chapter_summary(session, book_ch: BookChapter) -> dict:
    n_sections = session.scalar(
        select(func.count(BookSection.id)).where(BookSection.chapter_id == book_ch.id)
    )
    n_doses = session.scalar(
        select(func.count(MicroDose.id)).where(MicroDose.chapter_id == book_ch.id)
    )
    wb_ch = session.scalar(
        select(WorkbookChapter).where(WorkbookChapter.number == book_ch.number)
    )
    n_exercises = 0
    if wb_ch:
        n_exercises = session.scalar(
            select(func.count(WorkbookExercise.id)).where(WorkbookExercise.chapter_id == wb_ch.id)
        )

    # Completed-count lookups per kind.
    def completed(kind: str, ids_subq) -> int:
        return session.scalar(
            select(func.count(UserProgress.id)).where(
                UserProgress.user_id == DEFAULT_USER_ID,
                UserProgress.node_kind == kind,
                UserProgress.status == "completed",
                UserProgress.node_id.in_(ids_subq),
            )
        ) or 0

    dose_ids = select(MicroDose.id).where(MicroDose.chapter_id == book_ch.id)
    ex_ids = (
        select(WorkbookExercise.id).where(WorkbookExercise.chapter_id == wb_ch.id)
        if wb_ch
        else select(WorkbookExercise.id).where(WorkbookExercise.id == 0)
    )

    return {
        "number": book_ch.number,
        "title": book_ch.title,
        "source_ref": book_ch.source_ref,
        "book_pages": [book_ch.start_page, book_ch.end_page],
        "workbook_number": wb_ch.number if wb_ch else None,
        "workbook_title": wb_ch.title if wb_ch else None,
        "workbook_pages": [wb_ch.start_page, wb_ch.end_page] if wb_ch else None,
        "totals": {
            "sections": int(n_sections or 0),
            "learn_doses": int(n_doses or 0),
            "practice_exercises": int(n_exercises or 0),
        },
        "completed": {
            "learn_doses": int(completed("learn_dose", dose_ids)),
            "practice_exercises": int(completed("practice_exercise", ex_ids)),
        },
    }


@bp.get("/chapters")
@db_route
def list_chapters(session):
    chapters = session.scalars(select(BookChapter).order_by(BookChapter.number)).all()
    return ok({"chapters": [_chapter_summary(session, c) for c in chapters]})


@bp.get("/chapters/<int:number>")
@db_route
def get_chapter(number: int, session):
    ch = session.scalar(select(BookChapter).where(BookChapter.number == number))
    if not ch:
        abort(404, description=f"Chapter {number} not found")
    sections = session.scalars(
        select(BookSection).where(BookSection.chapter_id == ch.id).order_by(BookSection.order_index)
    ).all()
    summary = _chapter_summary(session, ch)
    summary["sections"] = [
        {
            "id": s.id,
            "order_index": s.order_index,
            "title": s.title,
            "depth": s.depth,
            "pages": [s.start_page, s.end_page],
            "source_ref": s.source_ref,
            "char_count": len(s.text or ""),
        }
        for s in sections
    ]
    return ok(summary)
