"""Workbook parser: splits each chapter into three sections (Learning
Objectives, Practice Questions, Practice Projects), and further splits
the questions/projects sections into individual exercises.

The workbook's outline is very regular: each chapter contains two
icon-marked children (the question-mark icon and the pencil icon) whose
titles appear in the outline as plain text. Children underneath those
markers are individual exercise titles.
"""
from __future__ import annotations

from pathlib import Path

from .db import WorkbookChapter, WorkbookExercise, WorkbookSection
from .extract import extract_page_range, open_pdf, PDFContext
from .outline import (
    ChapterSpec,
    OutlineEntry,
    find_workbook_chapters,
    load_outline,
    resolve_end_pages,
)


_KIND_BY_KEYWORD = [
    ("LEARNING OBJECTIVES", "objectives"),
    ("Practice Questions", "questions"),
    ("Practice Projects", "projects"),
]


def _classify_section(title: str) -> str | None:
    """Map a workbook outline child title to our `kind` vocabulary."""
    for keyword, kind in _KIND_BY_KEYWORD:
        if keyword.lower() in title.lower():
            return kind
    return None


def parse_workbook(
    pdf_path: Path,
    *,
    chapter_filter: set[int] | None = None,
) -> list[tuple[WorkbookChapter, list[WorkbookSection], list[WorkbookExercise]]]:
    outline = load_outline(pdf_path)
    chapters = find_workbook_chapters(outline)
    results = []

    with open_pdf(pdf_path) as ctx:
        resolve_end_pages(chapters, ctx.total_pages)
        for ch in chapters:
            if chapter_filter is not None and ch.number not in chapter_filter:
                continue
            wb_ch = WorkbookChapter(
                number=ch.number,
                title=ch.title,
                start_page=ch.start_page,
                end_page=ch.end_page,
                source_ref=f"pdf:workbook.pdf#p={ch.start_page}",
            )
            sections, exercises = _build_chapter(ctx, ch)
            results.append((wb_ch, sections, exercises))
    return results


def _build_chapter(
    ctx: PDFContext, ch: ChapterSpec
) -> tuple[list[WorkbookSection], list[WorkbookExercise]]:
    # The chapter outline children are the icon-marked labels. Each has
    # sub-children that are the individual exercise titles.
    section_children: list[OutlineEntry] = list(ch.entry.children)
    # Resolve section end pages using the order of section_children.
    for i, s in enumerate(section_children):
        if i + 1 < len(section_children):
            s._end = section_children[i + 1].page - 1  # type: ignore[attr-defined]
        else:
            s._end = ch.end_page  # type: ignore[attr-defined]
        if s._end < s.page:  # type: ignore[attr-defined]
            s._end = s.page  # type: ignore[attr-defined]

    sections: list[WorkbookSection] = []
    exercises: list[WorkbookExercise] = []
    ex_counter = 0

    for order, sect in enumerate(section_children):
        kind = _classify_section(sect.title)
        if kind is None:
            continue
        text = extract_page_range(ctx, sect.page, sect._end)  # type: ignore[attr-defined]
        sections.append(
            WorkbookSection(
                order_index=order,
                kind=kind,
                title=sect.title.strip(),
                start_page=sect.page,
                end_page=sect._end,  # type: ignore[attr-defined]
                text=text,
                source_ref=f"pdf:workbook.pdf#p={sect.page}",
            )
        )
        # Only questions and projects generate individual exercise rows.
        if kind in {"questions", "projects"} and sect.children:
            exercise_children = sect.children
            for j, ex_entry in enumerate(exercise_children):
                start = ex_entry.page
                if j + 1 < len(exercise_children):
                    end = exercise_children[j + 1].page - 1
                else:
                    end = sect._end  # type: ignore[attr-defined]
                if end < start:
                    end = start
                ex_text = extract_page_range(ctx, start, end)
                ex_kind = "question" if kind == "questions" else "project"
                exercises.append(
                    WorkbookExercise(
                        order_index=ex_counter,
                        kind=ex_kind,
                        title=ex_entry.title.strip(),
                        text=ex_text,
                        source_ref=f"pdf:workbook.pdf#p={start}",
                    )
                )
                ex_counter += 1

    return sections, exercises
