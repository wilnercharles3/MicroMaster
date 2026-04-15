"""/api/chapters/<n>/micro-doses and /api/micro-doses/<id> endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, abort, request
from sqlalchemy import select

from sqlalchemy.orm import Session

from scraper.db import BookChapter

from ..config import DEFAULT_USER_ID, XP_LEARN_DOSE_COMPLETE
from ..models import MicroDose, UserProgress
from ..services.micro_dose_builder import rebuild_chapter
from ..services.scoring import award_xp
from ._util import db_route, ok

bp = Blueprint("micro_doses", __name__)


def _dose_payload(session: Session, dose: MicroDose) -> dict:
    prog = session.scalar(
        select(UserProgress).where(
            UserProgress.user_id == DEFAULT_USER_ID,
            UserProgress.node_kind == "learn_dose",
            UserProgress.node_id == dose.id,
        )
    )
    ch = session.get(BookChapter, dose.chapter_id)
    return {
        "id": dose.id,
        "chapter_id": dose.chapter_id,
        "chapter_number": ch.number if ch else None,
        "chapter_title": ch.title if ch else None,
        "section_id": dose.section_id,
        "order_index": dose.order_index,
        "title": dose.title,
        "hook": dose.hook,
        "reading": dose.reading,
        "starter_code": dose.starter_code,
        "teach_back_prompt": dose.teach_back_prompt,
        "quiz_json": dose.quiz_json,
        "char_count": dose.char_count,
        "source_ref": dose.source_ref,
        "progress": {
            "status": prog.status if prog else "available",
            "score": prog.score if prog else 0.0,
            "completed_at": prog.completed_at.isoformat() if prog and prog.completed_at else None,
            "last_code": prog.last_code if prog else "",
            "last_teach_back": prog.last_teach_back if prog else "",
        },
    }


@bp.get("/chapters/<int:number>/micro-doses")
@db_route
def list_doses_for_chapter(number: int, session):
    ch = session.scalar(select(BookChapter).where(BookChapter.number == number))
    if not ch:
        abort(404, description=f"Chapter {number} not found")
    doses = session.scalars(
        select(MicroDose)
        .where(MicroDose.chapter_id == ch.id)
        .order_by(MicroDose.order_index)
    ).all()
    return ok(
        {
            "chapter_number": ch.number,
            "chapter_title": ch.title,
            "count": len(doses),
            "doses": [
                {
                    "id": d.id,
                    "order_index": d.order_index,
                    "title": d.title,
                    "hook": d.hook,
                    "char_count": d.char_count,
                }
                for d in doses
            ],
        }
    )


@bp.get("/micro-doses/<int:dose_id>")
@db_route
def get_dose(dose_id: int, session):
    dose = session.get(MicroDose, dose_id)
    if not dose:
        abort(404, description="Micro-dose not found")
    return ok(_dose_payload(session, dose))


def _upsert_progress(session, node_kind: str, node_id: int) -> UserProgress:
    prog = session.scalar(
        select(UserProgress).where(
            UserProgress.user_id == DEFAULT_USER_ID,
            UserProgress.node_kind == node_kind,
            UserProgress.node_id == node_id,
        )
    )
    if prog is None:
        prog = UserProgress(
            user_id=DEFAULT_USER_ID,
            node_kind=node_kind,
            node_id=node_id,
            status="available",
        )
        session.add(prog)
        session.flush()
    return prog


@bp.post("/micro-doses/<int:dose_id>/save")
@db_route
def save_dose_work(dose_id: int, session):
    dose = session.get(MicroDose, dose_id)
    if not dose:
        abort(404)
    body = request.get_json(silent=True) or {}
    prog = _upsert_progress(session, "learn_dose", dose_id)
    if prog.started_at is None:
        prog.started_at = datetime.now(timezone.utc)
    if "last_code" in body:
        prog.last_code = body["last_code"] or ""
    if "last_teach_back" in body:
        prog.last_teach_back = body["last_teach_back"] or ""
    if prog.status == "available":
        prog.status = "in_progress"
    return ok(_dose_payload(session, dose))


@bp.post("/micro-doses/<int:dose_id>/complete")
@db_route
def complete_dose(dose_id: int, session):
    dose = session.get(MicroDose, dose_id)
    if not dose:
        abort(404)
    body = request.get_json(silent=True) or {}
    score = float(body.get("score", 1.0))
    score = max(0.0, min(1.0, score))
    prog = _upsert_progress(session, "learn_dose", dose_id)
    if prog.status != "completed":
        prog.status = "completed"
        prog.score = score
        prog.completed_at = datetime.now(timezone.utc)
        award_xp(
            session,
            event_type="learn_dose_complete",
            amount=XP_LEARN_DOSE_COMPLETE,
            reference_kind="micro_dose",
            reference_id=dose.id,
        )
    return ok(_dose_payload(session, dose))


@bp.post("/chapters/<int:number>/rebuild-doses")
@db_route
def rebuild_doses(number: int, session):
    """Admin-style endpoint: re-derive micro-doses from the chapter's
    scraped sections. Useful after a parser tweak or a fresh scrape."""
    ch = session.scalar(select(BookChapter).where(BookChapter.number == number))
    if not ch:
        abort(404, description=f"Chapter {number} not found")
    count = rebuild_chapter(session, ch)
    return ok({"chapter_number": ch.number, "micro_doses": count})
