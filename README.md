# MicroMaster

A local web app for learning _Automate the Boring Stuff with Python, 3rd Edition_ by Al Sweigart, paired with its companion Workbook. MicroMaster breaks each chapter into two parallel tracks (Learn and Practice), delivers the material as short micro-doses with built-in code sandboxes, and tracks progress with light gamification and ADHD-friendly session tools.

## Attribution and licensing

MicroMaster is a personal study aid. It scrapes content from two freely available sources, stores a local copy in a SQLite database on your own machine, and always displays the source URL alongside the original text.

- Main book: _Automate the Boring Stuff with Python, 3rd Edition_ by Al Sweigart. Source: <https://automatetheboringstuff.com/3e/>
- Workbook: _The Automate the Boring Stuff with Python Workbook_ by Al Sweigart. Source: <https://inventwithpython.com/automate3workbook/>

Both titles are published by the author under Creative Commons licenses for non-commercial reading. MicroMaster does not redistribute, republish, or share the scraped content. Do not deploy this app to the public internet or make the scraped database available to others.

## Status

Under construction. Built phase by phase:

- [x] Phase 1: Project scaffold
- [x] Phase 2: Dual-source PDF scraper into SQLite
- [x] Phase 3: Flask backend API with micro-dose builder and XP scoring
- [x] Phase 4: React frontend scaffold + chapter grid + micro-dose viewer with copy-to-run sandbox
- [ ] Phase 5: Roadmap UI (24-chapter visual map)
- [ ] Phase 6: Pyodide sandbox upgrade
- [ ] Phase 7: Quiz + teach-back UI
- [ ] Phase 7b: Vocab and syntax challenges (third node type)
- [ ] Phase 8: Gamification UI (XP bar, levels, streaks, achievements)
- [ ] Phase 9: ADHD features (session timer, focus mode, just-one-more, daily goals)
- [ ] Phase 10: Claude API integration for teach-back evaluation

## Architecture

```
MicroMaster/
  scraper/      Python scrapers for book and workbook, writes to data/micromaster.db
  backend/      Flask API (Python), SQLite via SQLAlchemy
  frontend/     React + Vite, Pyodide for in-browser Python execution
  data/         SQLite database and raw HTML cache (gitignored)
  docs/         Design notes, schema, roadmap
```

## Prerequisites

- Python 3.11+ (tested with 3.14)
- Node.js 18+ (tested with 25)
- Git

## Quick start

From `C:\MicroMaster`, in two separate terminals:

```
# Terminal 1 - Flask backend on :5057
.venv\Scripts\python.exe -m backend.run

# Terminal 2 - Vite dev server on :5173
cd frontend
npm run dev
```

Then open <http://localhost:5173>. The Vite dev server proxies `/api/*`
to the Flask backend, so both dev and production builds share the same
relative URLs.

First-time setup (one-time):

```
# Python env (handled by uv; installs a private CPython 3.12)
uv venv --python 3.12
uv pip install -r backend/requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..

# Put your own copies of the PDFs in data/sources/
#   data\sources\book.pdf
#   data\sources\workbook.pdf

# Scrape + build micro-doses
.venv\Scripts\python.exe -m scraper --book --workbook
.venv\Scripts\python.exe -m backend.build_doses
```

## Development principles

- Each phase ends with a runnable state and a git commit.
- The scraper caches raw HTML locally so the source sites are hit at most once per page.
- All scraped rows store their source URL so attribution travels with the content.
