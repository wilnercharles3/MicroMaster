"""/api/practice endpoints: workbook exercises for a chapter, and submission."""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, abort, request
from sqlalchemy import select

from scraper.db import WorkbookChapter, WorkbookExercise, WorkbookSection

from ..config import DEFAULT_USER_ID, XP_PRACTICE_EXERCISE_COMPLETE
from ..models import UserProgress
from ..services.scoring import award_xp
from ._util import db_route, ok

bp = Blueprint("practice", __name__)


@bp.get("/chapters/<int:number>/practice")
@db_route
def list_practice(number: int, session):
    wb = session.scalar(select(WorkbookChapter).where(WorkbookChapter.number == number))
    if not wb:
        abort(404, description=f"Workbook chapter {number} not found")
    sections = session.scalars(
        select(WorkbookSection).where(WorkbookSection.chapter_id == wb.id).order_by(WorkbookSection.order_index)
    ).all()
    exercises = session.scalars(
        select(WorkbookExercise).where(WorkbookExercise.chapter_id == wb.id).order_by(WorkbookExercise.order_index)
    ).all()
    # Completed status per exercise.
    completed_ids = set(
        session.scalars(
            select(UserProgress.node_id).where(
                UserProgress.user_id == DEFAULT_USER_ID,
                UserProgress.node_kind == "practice_exercise",
                UserProgress.status == "completed",
            )
        ).all()
    )
    return ok(
        {
            "chapter_number": wb.number,
            "chapter_title": wb.title,
            "sections": [
                {"id": s.id, "kind": s.kind, "title": s.title, "text_preview": (s.text or "")[:280]}
                for s in sections
            ],
            "exercises": [
                {
                    "id": e.id,
                    "kind": e.kind,
                    "title": e.title,
                    "order_index": e.order_index,
                    "source_ref": e.source_ref,
                    "completed": e.id in completed_ids,
                }
                for e in exercises
            ],
        }
    )


@bp.get("/practice/<int:exercise_id>")
@db_route
def get_exercise(exercise_id: int, session):
    ex = session.get(WorkbookExercise, exercise_id)
    if not ex:
        abort(404)
    prog = session.scalar(
        select(UserProgress).where(
            UserProgress.user_id == DEFAULT_USER_ID,
            UserProgress.node_kind == "practice_exercise",
            UserProgress.node_id == exercise_id,
        )
    )
    return ok(
        {
            "id": ex.id,
            "chapter_id": ex.chapter_id,
            "kind": ex.kind,
            "title": ex.title,
            "text": ex.text,
            "source_ref": ex.source_ref,
            "progress": {
                "status": prog.status if prog else "available",
                "score": prog.score if prog else 0.0,
                "last_code": prog.last_code if prog else "",
                "completed_at": prog.completed_at.isoformat() if prog and prog.completed_at else None,
            },
        }
    )


@bp.post("/practice/<int:exercise_id>/submit")
@db_route
def submit_exercise(exercise_id: int, session):
    ex = session.get(WorkbookExercise, exercise_id)
    if not ex:
        abort(404)
    body = request.get_json(silent=True) or {}
    passed = bool(body.get("passed", False))
    code = body.get("code") or ""

    prog = session.scalar(
        select(UserProgress).where(
            UserProgress.user_id == DEFAULT_USER_ID,
            UserProgress.node_kind == "practice_exercise",
            UserProgress.node_id == exercise_id,
        )
    )
    if prog is None:
        prog = UserProgress(
            user_id=DEFAULT_USER_ID,
            node_kind="practice_exercise",
            node_id=exercise_id,
            status="in_progress",
        )
        session.add(prog)
        session.flush()

    prog.last_code = code
    if prog.started_at is None:
        prog.started_at = datetime.now(timezone.utc)

    awarded = False
    if passed and prog.status != "completed":
        prog.status = "completed"
        prog.score = 1.0
        prog.completed_at = datetime.now(timezone.utc)
        award_xp(
            session,
            event_type="practice_exercise_complete",
            amount=XP_PRACTICE_EXERCISE_COMPLETE,
            reference_kind="workbook_exercise",
            reference_id=ex.id,
        )
        awarded = True
    elif not passed:
        prog.status = "in_progress"

    return ok(
        {
            "id": ex.id,
            "passed": passed,
            "awarded_xp": awarded,
            "status": prog.status,
        }
    )
