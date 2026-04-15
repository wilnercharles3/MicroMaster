"""SQLAlchemy models for the MicroMaster local database.

Phase 2 only defines the scraper's content tables. Progress, XP, and
gamification tables are added in Phase 3.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BookChapter(Base):
    __tablename__ = "book_chapters"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    end_page: Mapped[int] = mapped_column(Integer, nullable=False)
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    sections: Mapped[list["BookSection"]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan", order_by="BookSection.order_index"
    )


class BookSection(Base):
    __tablename__ = "book_sections"
    __table_args__ = (UniqueConstraint("chapter_id", "order_index", name="ux_book_sections_chapter_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("book_chapters.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    end_page: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)

    chapter: Mapped[BookChapter] = relationship(back_populates="sections")


class WorkbookChapter(Base):
    __tablename__ = "workbook_chapters"
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    end_page: Mapped[int] = mapped_column(Integer, nullable=False)
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    sections: Mapped[list["WorkbookSection"]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="WorkbookSection.order_index",
    )
    exercises: Mapped[list["WorkbookExercise"]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="WorkbookExercise.order_index",
    )


class WorkbookSection(Base):
    """A subsection inside a workbook chapter, e.g. Practice Questions or
    Practice Projects, or the Learning Objectives block."""

    __tablename__ = "workbook_sections"
    __table_args__ = (UniqueConstraint("chapter_id", "order_index", name="ux_workbook_sections_chapter_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("workbook_chapters.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)  # objectives | questions | projects
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    end_page: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)

    chapter: Mapped[WorkbookChapter] = relationship(back_populates="sections")


class WorkbookExercise(Base):
    """A single practice question or practice project, split out of a
    workbook section. Later phases use these as Practice-track nodes."""

    __tablename__ = "workbook_exercises"
    __table_args__ = (UniqueConstraint("chapter_id", "order_index", name="ux_workbook_exercises_chapter_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("workbook_chapters.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)  # question | project
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)

    chapter: Mapped[WorkbookChapter] = relationship(back_populates="exercises")


@event.listens_for(Engine, "connect")
def _sqlite_fk_on(dbapi_conn, _):  # pragma: no cover - infra hook
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        # Non-SQLite engines won't support this; ignore.
        pass


def make_engine(db_path: Path, *, echo: bool = False):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", echo=echo, future=True)
    Base.metadata.create_all(engine)
    return engine


def make_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
