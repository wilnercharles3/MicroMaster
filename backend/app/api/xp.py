"""/api/xp endpoints."""
from __future__ import annotations

from flask import Blueprint, request
from sqlalchemy import select

from ..config import DEFAULT_USER_ID
from ..models import XpEvent
from ._util import db_route, ok

bp = Blueprint("xp", __name__)


@bp.get("/xp/events")
@db_route
def xp_events(session):
    limit = int(request.args.get("limit", "30"))
    limit = max(1, min(500, limit))
    rows = session.scalars(
        select(XpEvent)
        .where(XpEvent.user_id == DEFAULT_USER_ID)
        .order_by(XpEvent.occurred_at.desc())
        .limit(limit)
    ).all()
    return ok(
        {
            "events": [
                {
                    "id": r.id,
                    "event_type": r.event_type,
                    "amount": r.amount,
                    "multiplier": r.multiplier,
                    "reference_kind": r.reference_kind,
                    "reference_id": r.reference_id,
                    "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
                }
                for r in rows
            ]
        }
    )
