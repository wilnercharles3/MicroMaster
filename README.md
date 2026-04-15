# MicroMaster

A local study app for _Automate the Boring Stuff with Python, 3rd Edition_ by Al Sweigart, paired with its companion Workbook. MicroMaster breaks each chapter into two parallel tracks (Learn and Practice), delivers the material as short micro-doses with built-in code sandboxes, and tracks progress with light gamification and ADHD-friendly session tools.

## Attribution and licensing

MicroMaster is a personal study aid. It extracts content from your own PDF copies of the book and workbook, stores the parsed text in a SQLite database on your own machine, and always displays the source page number alongside the original text.

- Main book: _Automate the Boring Stuff with Python, 3rd Edition_ by Al Sweigart. Online: <https://automatetheboringstuff.com/3e/>
- Workbook: _The Automate the Boring Stuff with Python Workbook_ by Al Sweigart. Online: <https://inventwithpython.com/automate3workbook/>

Both titles are published by the author under Creative Commons licenses for non-commercial reading. MicroMaster does not redistribute, republish, or share the scraped content. Do not deploy this app to the public internet or share the scraped database.

## Status

Under construction. Built phase by phase:

- [x] Phase 1: Project scaffold
- [x] Phase 2: Dual-source PDF scraper into SQLite
- [x] Phase 3: Flask backend API with micro-dose builder and XP scoring
- [x] Phase 4: React frontend scaffold + chapter grid + micro-dose viewer with copy-to-run sandbox
- [ ] Phase 5: Roadmap UI (24-chapter visual map)
- [ ] Phase 6: Pyodide sandbox upgrade (run Python directly in the browser)
- [ ] Phase 7: Quiz + teach-back UI
- [ ] Phase 7b: Vocab and syntax challenges (third node type)
- [ ] Phase 8: Gamification UI (XP animations, level-ups, achievement toasts)
- [ ] Phase 9: ADHD features (session timer, focus mode, just-one-more, daily goals)
- [ ] Phase 10: Claude API integration for teach-back evaluation and paraphrasing

## You do NOT need to install Mu

Chapter 1 of the book recommends installing Mu as a beginner-friendly editor. **You are not required to install Mu to use MicroMaster or to follow the book.** Any of these work fine:

- **IDLE** comes bundled with every Python install. Open it from the Windows Start menu (type "IDLE").
- **VS Code** with the Python extension, if you already use it.
- **PyCharm Community**, if you prefer a full IDE.
- **The `python` command itself** in a terminal gives you the same `>>>` interactive shell the book demonstrates.
- **MicroMaster's built-in sandbox** (once Phase 6 lands) will run Python directly in the browser via Pyodide, so you won't need a local editor at all to try the code snippets on a chapter page.

If you've already installed Mu, it works too. Pick whatever sticks.

## Prerequisites

- Python 3.11 or 3.12 (recommended). Python 3.13 and 3.14 on Windows have shipped with broken installs in our testing; stick with 3.12 to avoid pain.
- Node.js 18+ (tested with 25).
- Git.
- [uv](https://docs.astral.sh/uv/) — handles Python installation and venvs. Install with one of:
  ```cmd
  rem PowerShell installer (recommended on Windows)
  powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  or `winget install astral-sh.uv`.

## One-time setup

Open a terminal at `C:\MicroMaster`. Copy each block in order.

### 1. Install a known-good Python and create the venv

```cmd
uv python install 3.12
uv venv --python 3.12
```

### 2. Install backend Python dependencies

```cmd
uv pip install -r backend\requirements.txt
```

### 3. Install frontend dependencies

```cmd
cd frontend
npm install
cd ..
```

### 4. Provide your own PDF copies

Place your own personal copies of the two PDFs here, named exactly:

```
C:\MicroMaster\data\sources\book.pdf
C:\MicroMaster\data\sources\workbook.pdf
```

### 5. Scrape and build micro-doses

```cmd
.venv\Scripts\python.exe -m scraper --book --workbook
.venv\Scripts\python.exe -m backend.build_doses
```

The scrape takes ~1-2 minutes. You should see 24 chapters reported from each source and a final line like `Total: 815 Learn-track micro-doses across 24 chapters.`

## Running the app

The app currently runs as two processes: a Flask API server and a Vite dev server for the React UI. Keep both windows open while you study; close them when you're done.

### Terminal 1 — backend API

Windows `cmd.exe`:
```cmd
cd C:\MicroMaster
.venv\Scripts\python.exe -m backend.run
```

Git Bash or MINGW64:
```bash
cd /c/MicroMaster
source .venv/Scripts/activate
python -m backend.run
```

You should see `Running on http://127.0.0.1:5057`.

### Terminal 2 — frontend (React dev server)

Windows `cmd.exe`:
```cmd
cd C:\MicroMaster\frontend
npm run dev
```

Git Bash:
```bash
cd /c/MicroMaster/frontend
npm run dev
```

Vite prints a line like `Local: http://localhost:5173/`. If port 5173 is taken (for example a stale Vite from an earlier session), it will slide to 5174, 5175, and so on. That is fine — the backend proxy is port-independent.

### Open the app

Open the Vite URL in your browser. The React UI fetches `/api/*` which Vite forwards to Flask on 5057, so both servers must be up.

### Stopping the app

Press `Ctrl+C` in each terminal window. If a previous Vite run left a zombie holding port 5173, close its window or kill it from Task Manager.

## Architecture

```
MicroMaster/
  scraper/      PDF parsers for book and workbook -> writes data/micromaster.db
  backend/      Flask API (Python), SQLAlchemy on SQLite
  frontend/     React + Vite; Pyodide sandbox ships in Phase 6
  data/
    sources/    Your own copies of the PDFs (gitignored)
    cache/      Scraper intermediates (gitignored)
    *.db        Local SQLite database (gitignored)
  docs/         Design notes, phase plan
```

## Troubleshooting

- **`No Python at ...\cpython-3.12.13-...\python.exe`** — the uv-managed Python disappeared (Windows cleanup or antivirus). Re-run `uv python install 3.12 --reinstall`, delete `.venv`, then recreate it with `uv venv --python 3.12`.
- **`502 Bad Gateway` on `/api/*` in the browser** — Flask isn't running. Start it in Terminal 1.
- **Page loads but everything looks unstyled** — hard refresh (`Ctrl+Shift+R`) to bypass the CSS cache. If that doesn't help, stop Vite, `rm -rf frontend/node_modules/.vite`, then `npm run dev` again.
- **`'#' is not recognized as an internal or external command`** — you pasted a comment into `cmd.exe`. In cmd use `rem` for comments, or just skip comment lines when copying.
- **`.venvScriptspython.exe: command not found` in bash** — backslashes are escape characters in bash. Use forward slashes (`.venv/Scripts/python.exe`), or activate the venv first with `source .venv/Scripts/activate` then just type `python`.

## Development principles

- Each phase ends with a runnable state and a git commit.
- All extracted rows store a `source_ref` pointing back to the origin PDF and page number so attribution travels with the content.
- No scraped content is ever pushed to git; only the Python and TypeScript code.
