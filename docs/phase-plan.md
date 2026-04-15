# Phase plan

Each phase lands as a single commit. After each phase, the app is in a testable state and we pause for review before the next phase begins.

## Phase 1: Scaffold
- Directory layout, README, .gitignore, phase plan, git init. No runtime code yet.

## Phase 2: Dual-source scraper
- Pull all 24 chapters of the main book from automatetheboringstuff.com/3e/ and all workbook exercises from inventwithpython.com/automate3workbook/.
- Cache raw HTML under `data/cache/` so each URL is fetched at most once.
- 1.5 s delay between requests. Polite User-Agent.
- Parse into a SQLite database at `data/micromaster.db`:
  - `book_chapters(id, chapter_number, title, source_url, scraped_at)`
  - `book_sections(id, chapter_id, order_index, heading, html, text, source_url)`
  - `workbook_chapters(id, chapter_number, title, source_url, scraped_at)`
  - `workbook_exercises(id, chapter_id, order_index, title, html, text, kind, source_url)`
- CLI: `python -m scraper --book --workbook` with flags to limit chapters for testing.
- Test: after the scraper runs, the DB contains 24 book chapters and every workbook exercise set, and each row has a source_url.

## Phase 3: Flask backend
- SQLAlchemy models mirroring the scraper schema plus: `micro_doses`, `user_progress`, `xp_events`, `achievements`, `sessions`.
- A "micro-dose builder" service splits each book section into 3-7 minute doses (hook, reading, sandbox starter, quiz stub, teach-back prompt).
- API endpoints: chapters list, chapter detail, micro-dose detail, progress, XP.
- Test: hit endpoints with curl and see JSON.

## Phase 4: Micro-dose viewer with sandbox (server-rendered first)
- A minimal server-rendered HTML view of a single micro-dose with a CodeMirror textarea and a "Run" button.
- Initial sandbox uses Pyodide if it loads cleanly; fallback is a "copy code" button plus a link to a scratch file.
- Test: open a micro-dose in a browser, run the starter code.

## Phase 5: React frontend scaffold
- Vite + React + TypeScript, dev proxy to Flask, shared API client, basic layout.

## Phase 6: Roadmap UI
- 24-chapter visual map. Each chapter shows blue Learn nodes and green Practice nodes that converge into a purple Miniproject node and a gold Boss Battle node.

## Phase 7: Pyodide sandbox + quiz + teach-back UI
- React sandbox component. Quiz component. Teach-back textarea.

## Phase 8: Gamification
- XP, levels (Novice -> Boring Stuff Destroyer), streaks with multipliers, achievements.
- Weighting: Learn 50%, Practice 35%, Miniproject 15%.

## Phase 9: ADHD features
- 15-min session timer, focus mode, "just one more" prompt, random challenge button, daily micro-goals.

## Phase 10: Claude API integration
- Teach-back evaluation (was the explanation correct and complete?).
- Optional paraphrasing for doses the user marks "too dense".
- Uses `ANTHROPIC_API_KEY` env var. Graceful fallback when the key is missing.
