"""Static configuration for the MicroMaster backend.

Single-user local app. `DEFAULT_USER_ID` is a string constant that
identifies the one and only user in this install. Level thresholds and
XP award amounts live here so the UI and backend agree on scoring.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "micromaster.db"

# Vite dev server defaults. Overridable via env var for custom ports.
FRONTEND_ORIGINS = os.environ.get(
    "MICROMASTER_FRONTEND_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

DEFAULT_USER_ID = "local"

# Track weights (as fractions of a chapter's total score).
TRACK_WEIGHTS = {
    "learn": 0.50,
    "practice": 0.35,
    "miniproject": 0.15,
}

# XP awards per event. Keep these as the single source of truth and
# compute per-dose amounts from them.
XP_LEARN_DOSE_COMPLETE = 10
XP_LEARN_QUIZ_CORRECT = 5
XP_LEARN_TEACH_BACK_GOOD = 15
XP_PRACTICE_EXERCISE_COMPLETE = 20
XP_MINIPROJECT_COMPLETE = 100
XP_BOSS_BATTLE_COMPLETE = 250

# Level thresholds: name, minimum XP.
LEVELS = [
    ("Novice", 0),
    ("Learner", 100),
    ("Coder", 300),
    ("Scripter", 700),
    ("Automator", 1500),
    ("Power User", 3000),
    ("Pythonista", 5000),
    ("Boring Stuff Destroyer", 10000),
]

# Daily streak multipliers (applied to XP earned that day).
STREAK_MULTIPLIERS = {
    0: 1.0,
    1: 1.0,
    2: 1.1,
    3: 1.2,
    5: 1.3,
    7: 1.5,
    14: 1.75,
    30: 2.0,
}

# Micro-dose sizing (in characters). The builder targets doses in this
# range when splitting long book sections.
MICRO_DOSE_TARGET_CHARS = 1800
MICRO_DOSE_MAX_CHARS = 3000
MICRO_DOSE_MIN_CHARS = 400  # don't split a section this small
