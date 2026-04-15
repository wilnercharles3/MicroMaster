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
- [ ] Phase 2: Dual-source scraper (book + workbook) into SQLite
- [ ] Phase 3: Flask backend API
- [ ] Phase 4: Micro-dose lesson viewer with code sandbox
- [ ] Phase 5: React frontend scaffold
- [ ] Phase 6: Roadmap UI (24-chapter visual map)
- [ ] Phase 7: Pyodide sandbox + quiz + teach-back UI
- [ ] Phase 8: Gamification (XP, levels, streaks, achievements)
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

Nothing runs yet. Setup instructions will be added phase by phase.

## Development principles

- Each phase ends with a runnable state and a git commit.
- The scraper caches raw HTML locally so the source sites are hit at most once per page.
- All scraped rows store their source URL so attribution travels with the content.
