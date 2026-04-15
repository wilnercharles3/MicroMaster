"""/api/progress endpoint: overall roadmap progress, XP, level, streak."""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint
from sqlalchemy import func, select

from scraper.db import BookChapter, WorkbookChapter, WorkbookExercise

from ..config import DEFAULT_USER_ID, TRACK_WEIGHTS
from ..models import MicroDose, UserProgress
from ..services.scoring import compute_level, compute_streak, compute_total_xp, streak_multiplier
from ._util import db_route, ok

bp = Blueprint("progress", __name__)


@bp.get("/progress")
@db_route
def get_progress(session):
    total_xp = compute_total_xp(session)
    level = compute_level(total_xp)
    streak = compute_streak(session)

    # Per-chapter rollup.
    chapters = session.scalars(select(BookChapter).order_by(BookChapter.number)).all()
    rows = []
    chapter_score_sum = 0.0
    for ch in chapters:
        n_doses = session.scalar(
            select(func.count(MicroDose.id)).where(MicroDose.chapter_id == ch.id)
        ) or 0
        done_doses = session.scalar(
            select(func.count(UserProgress.id)).where(
                UserProgress.user_id == DEFAULT_USER_ID,
                UserProgress.node_kind == "learn_dose",
                UserProgress.status == "completed",
                UserProgress.node_id.in_(
                    select(MicroDose.id).where(MicroDose.chapter_id == ch.id)
                ),
            )
        ) or 0
        wb = session.scalar(select(WorkbookChapter).where(WorkbookChapter.number == ch.number))
        n_ex = 0
        done_ex = 0
        if wb:
            n_ex = session.scalar(
                select(func.count(WorkbookExercise.id)).where(WorkbookExercise.chapter_id == wb.id)
            ) or 0
            done_ex = session.scalar(
                select(func.count(UserProgress.id)).where(
                    UserProgress.user_id == DEFAULT_USER_ID,
                    UserProgress.node_kind == "practice_exercise",
                    UserProgress.status == "completed",
                    UserProgress.node_id.in_(
                        select(WorkbookExercise.id).where(WorkbookExercise.chapter_id == wb.id)
                    ),
                )
            ) or 0

        mini_done = session.scalar(
            select(func.count(UserProgress.id)).where(
                UserProgress.user_id == DEFAULT_USER_ID,
                UserProgress.node_kind == "miniproject",
                UserProgress.status == "completed",
                UserProgress.node_id == ch.number,
            )
        ) or 0

        learn_ratio = (done_doses / n_doses) if n_doses else 0.0
        prac_ratio = (done_ex / n_ex) if n_ex else 0.0
        mini_ratio = 1.0 if mini_done else 0.0
        chapter_score = (
            learn_ratio * TRACK_WEIGHTS["learn"]
            + prac_ratio * TRACK_WEIGHTS["practice"]
            + mini_ratio * TRACK_WEIGHTS["miniproject"]
        )
        chapter_score_sum += chapter_score

        rows.append(
            {
                "number": ch.number,
                "title": ch.title,
                "learn": {"total": n_doses, "completed": done_doses, "ratio": learn_ratio},
                "practice": {"total": n_ex, "completed": done_ex, "ratio": prac_ratio},
                "miniproject": {"completed": bool(mini_done), "ratio": mini_ratio},
                "chapter_score": round(chapter_score, 4),
            }
        )

    overall_score = chapter_score_sum / len(chapters) if chapters else 0.0

    return ok(
        {
            "user_id": DEFAULT_USER_ID,
            "total_xp": total_xp,
            "level": {
                "name": level.name,
                "min_xp": level.min_xp,
                "next_name": level.next_name,
                "next_min_xp": level.next_min_xp,
                "xp_into_level": level.xp_into_level,
                "xp_to_next": level.xp_to_next,
            },
            "streak": {
                "days": streak,
                "multiplier": streak_multiplier(streak),
            },
            "overall_score": round(overall_score, 4),
            "chapters": rows,
            "as_of": datetime.now(timezone.utc).isoformat(),
        }
    )
