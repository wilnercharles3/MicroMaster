"""Dev server entry point.

    cd C:\\MicroMaster
    .venv/Scripts/python.exe -m backend.run
"""
from __future__ import annotations

import os

from .app import create_app


def main() -> None:
    app = create_app()
    host = os.environ.get("MICROMASTER_HOST", "127.0.0.1")
    port = int(os.environ.get("MICROMASTER_PORT", "5057"))
    app.run(host=host, port=port, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
