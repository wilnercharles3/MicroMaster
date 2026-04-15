"""XP, level, and streak computation.

All scoring is derived from the immutable `xp_events` log plus the
per-day `daily_goals` table. No denormalized total is stored; the total
is computed by summing the log when the progress endpoint is called.
That keeps things simple at this scale (hundreds of events max).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import DEFAULT_USER_ID, LEVELS, STREAK_MULTIPLIERS
from ..models import XpEvent


@dataclass
class LevelInfo:
    name: str
    min_xp: int
    next_name: str | None
    next_min_xp: int | None
    xp_into_level: int
    xp_to_next: int | None


def compute_total_xp(session: Session, user_id: str = DEFAULT_USER_ID) -> int:
    total = session.scalar(
        select(func.coalesce(func.sum(XpEvent.amount), 0)).where(XpEvent.user_id == user_id)
    )
    return int(total or 0)


def compute_level(total_xp: int) -> LevelInfo:
    current = LEVELS[0]
    nxt: tuple[str, int] | None = None
    for i, (name, min_xp) in enumerate(LEVELS):
        if total_xp >= min_xp:
            current = (name, min_xp)
            nxt = LEVELS[i + 1] if i + 1 < len(LEVELS) else None
        else:
            break
    name, min_xp = current
    if nxt:
        next_name, next_min_xp = nxt
        xp_to_next = next_min_xp - total_xp
    else:
        next_name, next_min_xp = None, None
        xp_to_next = None
    return LevelInfo(
        name=name,
        min_xp=min_xp,
        next_name=next_name,
        next_min_xp=next_min_xp,
        xp_into_level=total_xp - min_xp,
        xp_to_next=xp_to_next,
    )


def compute_streak(session: Session, user_id: str = DEFAULT_USER_ID) -> int:
    """Count consecutive days (including today) with at least one XP event."""
    today = datetime.now(timezone.utc).date()
    active_days: set[date] = set()
    rows = session.execute(
        select(func.date(XpEvent.occurred_at)).where(XpEvent.user_id == user_id).distinct()
    ).all()
    for (day_str,) in rows:
        if isinstance(day_str, str):
            try:
                active_days.add(date.fromisoformat(day_str))
            except ValueError:
                continue
        elif isinstance(day_str, date):
            active_days.add(day_str)
    streak = 0
    cursor = today
    while cursor in active_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def streak_multiplier(streak: int) -> float:
    """Pick the highest multiplier whose threshold is <= streak."""
    best = 1.0
    for threshold, mult in sorted(STREAK_MULTIPLIERS.items()):
        if streak >= threshold:
            best = mult
    return best


def award_xp(
    session: Session,
    *,
    event_type: str,
    amount: int,
    reference_kind: str = "",
    reference_id: int = 0,
    user_id: str = DEFAULT_USER_ID,
) -> XpEvent:
    """Write an XP event and return it. Caller commits."""
    streak = compute_streak(session, user_id)
    mult = streak_multiplier(streak)
    boosted = int(round(amount * mult))
    ev = XpEvent(
        user_id=user_id,
        event_type=event_type,
        amount=boosted,
        multiplier=mult,
        reference_kind=reference_kind,
        reference_id=reference_id,
    )
    session.add(ev)
    session.flush()
    return ev
