"""PDF extraction and assignment-context matching helpers."""
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import List, Optional

import pdfplumber

from .models import MemoSection, RubricItem


# Matches memorandum section headings such as:
# "Question 1 (10 marks)" or "Database Design (5.5 marks)".
_SECTION_HEADER_RE = re.compile(
    r"^\s*(.+?)\s*\((\d+(?:\.\d+)?)\s*marks?\)\s*$",
    re.IGNORECASE,
)

def extract_pdf_text(pdf_source) -> str:
    """Accept a Path, bytes, or file-like object."""
    if isinstance(pdf_source, (str, Path)):
        source = str(pdf_source)
    elif isinstance(pdf_source, bytes):
        source = io.BytesIO(pdf_source)
    else:
        source = pdf_source

    chunks = []
    with pdfplumber.open(source) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                chunks.append(text)

    return "\n".join(chunks)


def parse_memo_sections_from_text(text: str) -> List[MemoSection]:
    lines = text.splitlines()
    headers = []

    for i, line in enumerate(lines):
        match = _SECTION_HEADER_RE.match(line)
        if match:
            headers.append((i, match.group(1).strip(), float(match.group(2))))

    sections = []
    for index, (line_i, title, marks) in enumerate(headers):
        start = line_i + 1
        end = headers[index + 1][0] if index + 1 < len(headers) else len(lines)
        body = "\n".join(lines[start:end]).replace("\x0c", "").strip()
        sections.append(MemoSection(title=title, marks=marks, body=body))

    return sections


def match_section_for_question(
    sections: List[MemoSection],
    grade_total: Optional[float],
    question_title: Optional[str] = None,
) -> Optional[MemoSection]:
    if grade_total is None:
        return None

    candidates = [
        section for section in sections
        if abs(section.marks - grade_total) < 0.01
    ]

    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    if question_title:
        import difflib
        return max(
            candidates,
            key=lambda section: difflib.SequenceMatcher(
                None,
                section.title.lower(),
                question_title.lower(),
            ).ratio(),
        )

    return candidates[0]


def _tokens(text: str):
    return {
        token
        for token in re.findall(r"[A-Za-z0-9_-]{3,}", (text or "").lower())
        if token not in {
            "the", "and", "for", "with", "from", "this", "that",
            "your", "you", "use", "using", "must", "should"
        }
    }


def relevant_spec_excerpt(
    specification_text: str,
    question_title: str,
    items: List[RubricItem],
    max_chars: int = 4000,
) -> str:
    """Rank paragraphs by keyword overlap with the current question/items."""
    if not specification_text:
        return ""

    query = question_title + " " + " ".join(item.text for item in items)
    query_tokens = _tokens(query)

    paragraphs = [
        re.sub(r"\s+", " ", paragraph).strip()
        for paragraph in re.split(r"\n\s*\n|(?<=\.)\s{2,}", specification_text)
        if paragraph.strip()
    ]

    scored = []
    for paragraph in paragraphs:
        overlap = len(query_tokens & _tokens(paragraph))
        if overlap:
            scored.append((overlap, paragraph))

    if not scored:
        return specification_text[:max_chars]

    scored.sort(key=lambda x: x[0], reverse=True)

    selected = []
    current_len = 0
    for _, paragraph in scored:
        if current_len + len(paragraph) + 2 > max_chars:
            continue
        selected.append(paragraph)
        current_len += len(paragraph) + 2
        if current_len >= max_chars * 0.8:
            break

    return "\n\n".join(selected)[:max_chars]
