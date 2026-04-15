"""User-facing SQLAlchemy models added on top of the scraper's schema.

Imports the shared Base so calling `Base.metadata.create_all(engine)`
creates these tables alongside the scraped content tables.

Tables introduced here:
  users            - single default row for this local-only app.
  micro_doses      - derived Learn-track units split out of book sections.
  user_progress    - per-user status/score for each trackable node.
  xp_events        - append-only log of XP awards.
  achievements     - unlockables (one row per user+code).
  daily_goals      - micro-dose goals keyed by (user, calendar date).
  focus_sessions   - ADHD 15-min session log.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scraper.db import Base, BookChapter, BookSection, WorkbookChapter, WorkbookExercise  # noqa: F401


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), default="Learner")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class MicroDose(Base):
    """A single Learn-track micro-lesson derived from a book section.

    A section that fits in one dose produces exactly one micro-dose.
    A long section splits into multiple doses in paragraph order.
    """

    __tablename__ = "micro_doses"
    __table_args__ = (
        UniqueConstraint("section_id", "order_index", name="ux_micro_doses_section_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("book_chapters.id", ondelete="CASCADE"), nullable=False)
    section_id: Mapped[int] = mapped_column(ForeignKey("book_sections.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    hook: Mapped[str] = mapped_column(Text, default="")
    reading: Mapped[str] = mapped_column(Text, nullable=False)
    starter_code: Mapped[str] = mapped_column(Text, default="")
    quiz_json: Mapped[str] = mapped_column(Text, default="")
    teach_back_prompt: Mapped[str] = mapped_column(Text, default="")
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class UserProgress(Base):
    """Per-user progress for a trackable node.

    `node_kind` is one of: 'learn_dose', 'practice_exercise',
    'miniproject', 'boss_battle', 'vocab', 'syntax'. `node_id` references
    the appropriate table's primary key (we do not enforce FK at DB
    level so the same row can reference different kinds).
    """

    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "node_kind", "node_id", name="ux_user_progress_node"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    node_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    node_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="available")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    last_code: Mapped[str] = mapped_column(Text, default="")
    last_teach_back: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class XpEvent(Base):
    __tablename__ = "xp_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    reference_kind: Mapped[str] = mapped_column(String(32), default="")
    reference_id: Mapped[int] = mapped_column(Integer, default=0)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)


class Achievement(Base):
    __tablename__ = "achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="ux_achievements_user_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class DailyGoal(Base):
    __tablename__ = "daily_goals"
    __table_args__ = (
        UniqueConstraint("user_id", "day", name="ux_daily_goals_user_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    goal_doses: Mapped[int] = mapped_column(Integer, default=3)
    completed_doses: Mapped[int] = mapped_column(Integer, default=0)


class FocusSession(Base):
    __tablename__ = "focus_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    planned_minutes: Mapped[int] = mapped_column(Integer, default=15)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    nodes_completed: Mapped[int] = mapped_column(Integer, default=0)
