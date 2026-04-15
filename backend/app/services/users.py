"""Default-user bootstrap for the single-user local app."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..config import DEFAULT_USER_ID
from ..models import User


def ensure_default_user(session: Session) -> User:
    user = session.get(User, DEFAULT_USER_ID)
    if user is None:
        user = User(id=DEFAULT_USER_ID, display_name="Learner")
        session.add(user)
        session.flush()
    return user
