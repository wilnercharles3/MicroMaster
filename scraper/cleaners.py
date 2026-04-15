"""Text cleanup helpers for PDF-extracted strings.

pdfplumber returns raw glyph-order text that includes a few systematic
issues when applied to the Sweigart PDFs:

- Smart quotes and en/em dashes come through as literal U+FFFD or stray
  control-style characters.
- Image alt-text from the workbook ("A simple drawing of a light bulb.")
  is embedded inline and should be stripped.
- Running headers and page numbers sometimes sneak into the extracted
  text between sections.

These helpers normalize whitespace, strip known alt-text prefixes, and
fix the most common encoding artifacts so downstream parsers can work
with clean strings.
"""
from __future__ import annotations

import re
import unicodedata

# Common alt-text blurbs that appear before the workbook's section icons.
# Matched case-insensitively, optional trailing period.
_ALT_TEXT_PATTERNS = [
    r"A simple drawing of a light bulb\.?",
    r"A simple drawing of a sharpened pencil\.?",
    r"A grey circle with a white question mark at the center\.?",
]
_ALT_TEXT_RE = re.compile("|".join(_ALT_TEXT_PATTERNS), re.IGNORECASE)

# Characters the PDF extractor emits for typographic punctuation that we
# want to normalize to ASCII-compatible equivalents.
_REPLACE_MAP = {
    "\u2013": "-",   # en dash
    "\u2014": "--",  # em dash
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u201C": '"',   # left double quote
    "\u201D": '"',   # right double quote
    "\u2026": "...", # ellipsis
    "\ufffd": "'",   # replacement char, most often a missing quote
    "\xa0": " ",     # non-breaking space
}


def normalize_text(text: str) -> str:
    """Normalize unicode and replace common typographic glyphs."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    for src, dst in _REPLACE_MAP.items():
        text = text.replace(src, dst)
    return text


def strip_alt_text(text: str) -> str:
    """Remove embedded alt-text phrases that describe workbook icons."""
    return _ALT_TEXT_RE.sub("", text)


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace while preserving paragraph breaks.

    Any run of 2+ newlines is kept as a single paragraph break. Other
    whitespace sequences collapse to a single space.
    """
    if not text:
        return ""
    # Unify paragraph breaks before collapsing spaces.
    text = re.sub(r"\r\n?", "\n", text)
    paragraphs = re.split(r"\n\s*\n+", text)
    cleaned = []
    for p in paragraphs:
        p = re.sub(r"[ \t]*\n[ \t]*", " ", p)
        p = re.sub(r"[ \t]+", " ", p).strip()
        if p:
            cleaned.append(p)
    return "\n\n".join(cleaned)


def clean_extracted(text: str) -> str:
    """Full cleaning pipeline for PDF-extracted text."""
    text = normalize_text(text)
    text = strip_alt_text(text)
    text = collapse_whitespace(text)
    return text
