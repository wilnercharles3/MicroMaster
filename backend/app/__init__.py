"""Flask app factory for MicroMaster.

Creates a Flask instance, wires CORS for the Vite dev server, attaches
the shared SQLAlchemy engine, and registers the API blueprints.

Run with:

    cd C:\\MicroMaster
    .venv/Scripts/python.exe -m backend.run
"""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from scraper.db import make_engine, make_session_factory

from .config import DEFAULT_DB_PATH, FRONTEND_ORIGINS


def create_app(*, db_path: Path | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or DEFAULT_DB_PATH
    app.config["JSON_SORT_KEYS"] = False

    engine = make_engine(app.config["DB_PATH"])
    app.extensions["engine"] = engine
    app.extensions["session_factory"] = make_session_factory(engine)

    CORS(app, resources={r"/api/*": {"origins": FRONTEND_ORIGINS}})

    # Register blueprints.
    from .api.health import bp as health_bp
    from .api.chapters import bp as chapters_bp
    from .api.micro_doses import bp as micro_doses_bp
    from .api.practice import bp as practice_bp
    from .api.progress import bp as progress_bp
    from .api.xp import bp as xp_bp

    for bp in (health_bp, chapters_bp, micro_doses_bp, practice_bp, progress_bp, xp_bp):
        app.register_blueprint(bp, url_prefix="/api")

    # Ensure new tables exist. The scraper's make_engine calls
    # Base.metadata.create_all, but the backend's additional models only
    # get registered after we import models below, so we re-run it.
    from . import models  # noqa: F401  (ensures new tables are registered)
    from scraper.db import Base

    Base.metadata.create_all(engine)

    # Ensure a default user row exists.
    from .services.users import ensure_default_user
    with app.extensions["session_factory"]() as session:
        ensure_default_user(session)
        session.commit()

    return app
