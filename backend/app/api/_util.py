"""Helpers shared across API blueprints."""
from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import current_app, jsonify
from sqlalchemy.orm import Session


def db_route(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Route decorator that opens a session and passes it as `session=`."""
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        factory = current_app.extensions["session_factory"]
        with factory() as session:  # type: Session
            result = fn(*args, session=session, **kwargs)
            session.commit()
            return result

    return wrapper


def ok(payload: Any, status: int = 200):
    return jsonify(payload), status
