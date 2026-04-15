"""Rebuild Learn-track micro-doses for every chapter in the DB.

Run after a fresh scrape:

    cd C:\\MicroMaster
    .venv/Scripts/python.exe -m backend.build_doses
"""
from __future__ import annotations

from scraper.db import make_engine, make_session_factory

from .app import models  # noqa: F401 - registers new tables
from .app.config import DEFAULT_DB_PATH
from .app.services.micro_dose_builder import rebuild_all
from scraper.db import Base


def main() -> int:
    engine = make_engine(DEFAULT_DB_PATH)
    Base.metadata.create_all(engine)
    Session = make_session_factory(engine)
    with Session() as session:
        counts = rebuild_all(session)
        session.commit()
    total = sum(counts.values())
    for num in sorted(counts):
        print(f"  ch{num:02d}: {counts[num]} doses")
    print(f"Total: {total} Learn-track micro-doses across {len(counts)} chapters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
