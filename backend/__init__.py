"""MicroMaster backend package.

Flask app lives under `backend.app`. The scraper's SQLAlchemy models are
imported from the `scraper.db` module so both processes share one source
of truth for the content tables. New user-facing tables (progress, XP,
micro-doses) are defined in `backend.app.models` against the same Base.
"""
