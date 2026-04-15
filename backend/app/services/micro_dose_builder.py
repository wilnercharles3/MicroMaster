"""Split scraped book sections into bite-sized Learn-track micro-doses.

Heuristics, in order of preference:

1. If the section text is shorter than MICRO_DOSE_MAX_CHARS, produce a
   single dose covering the whole section.
2. Otherwise, walk the paragraphs (already split by cleaners as "\\n\\n"
   groups) and pack them into doses targeted at MICRO_DOSE_TARGET_CHARS,
   never exceeding MICRO_DOSE_MAX_CHARS.
3. A single oversized paragraph becomes its own dose even if it exceeds
   the max; splitting mid-paragraph risks cutting a code example or a
   numbered list in half.

Each dose also gets:
- `hook`: a one-line teaser derived from the first sentence of the
  dose, trimmed to ~140 chars.
- `starter_code`: best-effort extracted first code snippet from the
  reading (indented blocks or lines with common Python tokens).
- `teach_back_prompt`: a templated prompt referencing the section title.
- `quiz_json`: left empty at Phase 3; filled in Phase 4 (or by the
  Claude API).

The builder is idempotent: running it twice for the same chapter
replaces the existing doses for that chapter.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from scraper.db import BookChapter, BookSection

from ..config import MICRO_DOSE_MAX_CHARS, MICRO_DOSE_MIN_CHARS, MICRO_DOSE_TARGET_CHARS
from ..models import MicroDose


@dataclass
class DoseDraft:
    order_index: int
    title: str
    hook: str
    reading: str
    starter_code: str
    teach_back_prompt: str
    source_ref: str


def _split_paragraphs(text: str) -> list[str]:
    return [p for p in text.split("\n\n") if p.strip()]


def _first_sentence(text: str, max_chars: int = 140) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    match = re.search(r"(?<=[.!?])\s+", stripped)
    end = match.start() if match else len(stripped)
    sentence = stripped[:end].strip()
    if len(sentence) > max_chars:
        sentence = sentence[: max_chars - 1].rstrip() + "..."
    return sentence


_CODE_HINT_RE = re.compile(
    r"(^>>> |^\.\.\. |\bdef \w+\(|\bimport \w|\bfor \w+ in\b|\bwhile .+:|\bprint\(|\bif .+:|\breturn\b)",
    re.MULTILINE,
)


def _extract_starter_code(text: str, max_lines: int = 12) -> str:
    """Best-effort starter-code extractor from reading text.

    Looks for a contiguous run of lines that look like Python: interactive
    shell prompts, def/for/while/if headers, imports, or print calls.
    """
    lines = text.split("\n")
    best: list[str] = []
    current: list[str] = []
    for line in lines:
        if _CODE_HINT_RE.search(line):
            current.append(line.strip())
            if len(current) > len(best):
                best = list(current)
        else:
            # Allow one blank between code lines to handle paragraph-cleaned text.
            if current and not line.strip():
                current.append("")
            else:
                current = []
    if not best:
        return ""
    # Strip interactive-shell prompts so the sandbox can run the code directly.
    cleaned = []
    for line in best[:max_lines]:
        stripped = line.lstrip()
        if stripped.startswith(">>> "):
            cleaned.append(stripped[4:])
        elif stripped.startswith("... "):
            cleaned.append(stripped[4:])
        else:
            cleaned.append(line)
    return "\n".join(cleaned).strip()


def _pack_paragraphs_into_doses(paragraphs: list[str]) -> list[str]:
    """Group paragraphs into dose-sized chunks."""
    doses: list[str] = []
    buf: list[str] = []
    buf_len = 0
    for p in paragraphs:
        # A pathologically long paragraph is its own dose.
        if len(p) > MICRO_DOSE_MAX_CHARS:
            if buf:
                doses.append("\n\n".join(buf))
                buf, buf_len = [], 0
            doses.append(p)
            continue
        projected = buf_len + (2 if buf else 0) + len(p)
        if buf and projected > MICRO_DOSE_TARGET_CHARS:
            doses.append("\n\n".join(buf))
            buf, buf_len = [p], len(p)
        else:
            buf.append(p)
            buf_len = projected
    if buf:
        doses.append("\n\n".join(buf))
    return doses


def drafts_for_section(section: BookSection) -> list[DoseDraft]:
    text = section.text or ""
    if len(text) <= max(MICRO_DOSE_MAX_CHARS, MICRO_DOSE_MIN_CHARS):
        # One dose covers the whole section.
        chunks = [text]
    else:
        chunks = _pack_paragraphs_into_doses(_split_paragraphs(text))
    drafts: list[DoseDraft] = []
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        title = section.title if total == 1 else f"{section.title} ({i + 1}/{total})"
        drafts.append(
            DoseDraft(
                order_index=i,
                title=title,
                hook=_first_sentence(chunk),
                reading=chunk,
                starter_code=_extract_starter_code(chunk),
                teach_back_prompt=(
                    f"In your own words, explain the key idea from \"{section.title}\". "
                    "Aim for 2-4 sentences and reference at least one concrete example."
                ),
                source_ref=section.source_ref,
            )
        )
    return drafts


def rebuild_chapter(session: Session, chapter: BookChapter) -> int:
    """Rebuild all micro-doses for a chapter. Returns the count created."""
    # Delete existing doses for this chapter.
    session.execute(delete(MicroDose).where(MicroDose.chapter_id == chapter.id))
    session.flush()

    dose_counter = 0
    sections = session.scalars(
        select(BookSection)
        .where(BookSection.chapter_id == chapter.id)
        .order_by(BookSection.order_index)
    ).all()
    for section in sections:
        if not section.text.strip():
            continue
        for draft in drafts_for_section(section):
            session.add(
                MicroDose(
                    chapter_id=chapter.id,
                    section_id=section.id,
                    order_index=dose_counter,
                    title=draft.title,
                    hook=draft.hook,
                    reading=draft.reading,
                    starter_code=draft.starter_code,
                    teach_back_prompt=draft.teach_back_prompt,
                    quiz_json="",
                    source_ref=draft.source_ref,
                    char_count=len(draft.reading),
                )
            )
            dose_counter += 1
    return dose_counter


def rebuild_all(session: Session) -> dict[int, int]:
    """Rebuild doses for every scraped chapter. Returns {chapter_number: n_doses}."""
    counts: dict[int, int] = {}
    chapters = session.scalars(select(BookChapter).order_by(BookChapter.number)).all()
    for ch in chapters:
        counts[ch.number] = rebuild_chapter(session, ch)
    return counts
