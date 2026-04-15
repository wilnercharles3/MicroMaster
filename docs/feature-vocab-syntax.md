# Vocab and syntax challenges (deferred feature)

Added to the roadmap after initial spec, during the Phase 2 scraper work.

## What it is

A third node type that sits between Learn and Practice on each chapter's
path, focused on **language-level fluency** rather than concept
understanding or project-building. Intended to build the kind of
instant-recall skill you get from Anki-style spaced repetition, but
inside the flow of a lesson instead of as a separate app.

Two sub-modes:

1. **Vocab** - quick identify-this-term drills pulled from chapter
   keywords: "What does `f-string` mean?", "What is a _list comprehension_?",
   "What keyword starts a function?". Answer by typing a short response
   or picking from distractors.
2. **Syntax** - fill-in-the-blank code snippets from the chapter:
   user types the missing token and the sandbox runs the completed
   snippet against a hidden test to verify. Example: show
   `for i in ___(10):` with the task "complete so this prints 0-9".

## Where it fits

- On the roadmap: a small orange Vocab node between each Learn node and
  its next Practice node.
- In XP weighting (subject to tuning): Vocab 10%, shrinking Learn/Practice
  weights to 45/30 and keeping Miniproject at 15%.
- Not required to unlock the Practice node - it's a parallel quick-hit
  path, suited to the "random challenge" ADHD feature.

## Data source

The scraper extracts chapter vocabulary from two signals:

- Boldface / italicized technical terms in the main book body text (the
  PDF's font runs make these identifiable).
- Subsection titles in the outline (they're already chunked by concept).

Syntax snippets are pulled from code blocks in the chapter, with one
token blanked out. The blanked token must be:

- A keyword (`for`, `while`, `def`, `return`, `in`, `is`, `not`, ...).
- Or a builtin name (`range`, `len`, `print`, `input`, ...).
- Or a literal operator (`==`, `!=`, `<=`, `>=`, `and`, `or`).

## Phase placement

Implemented in a dedicated phase after the main Learn/Practice system
works end-to-end, most likely between Phase 7 (Pyodide sandbox) and
Phase 8 (gamification). Tracked as Phase 7b in docs/phase-plan.md.
