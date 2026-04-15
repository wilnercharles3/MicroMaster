from __future__ import annotations

from flask import Blueprint, current_app

from ._util import ok

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    return ok(
        {
            "status": "ok",
            "service": "micromaster",
            "db": str(current_app.config["DB_PATH"]),
        }
    )
