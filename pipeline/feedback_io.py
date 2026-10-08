"""Low-level parsing and validation helpers for student feedback text files."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

from .models import RubricItem, QuestionBlock, StudentFeedback

_QUESTION_HEADER_RE = re.compile(
    r"^\s*QUESTION\s+(\d+)\s*(?::|\-|–|—)?\s*(.*?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_GRADE_RE = re.compile(r"Grade:\s*([\d.]+)\s*/\s*([\d.]+)", re.IGNORECASE)
_CHECKBOX_SPLIT_RE = re.compile(r"(?=[☑☐◪])")
_STATUS_MARKERS = {"☑": "met", "☐": "failed", "◪": "partial"}

_QUOTE_NORMALISE_MAP = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
}


def _normalise_text(text: str) -> str:
    for old, new in _QUOTE_NORMALISE_MAP.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def _extract_student_id(text: str, filename: str) -> str:
    # Prefer StudentNNN from the filename.
    stem = Path(filename).stem.strip()
    match = re.search(r"Student\d+", stem, re.IGNORECASE)
    if match:
        return match.group(0)

    match = re.search(r"\bStudent\d+\b", text, re.IGNORECASE)
    if match:
        return match.group(0)

    # Avoid treating the rubric placeholder YourDetails as a real student ID.
    match = re.search(r"\bCSIS\d+_web_(?!YourDetails\b)[A-Za-z0-9_-]+", text, re.IGNORECASE)
    if match:
        return match.group(0)

    return stem or "UnknownStudent"


def _parse_question_block(raw_block: str, q_num: int, q_title: str) -> QuestionBlock:
    question = QuestionBlock(
        number=q_num,
        title=q_title.strip() or f"Question {q_num}"
    )

    grade_match = _GRADE_RE.search(raw_block)
    if grade_match:
        question.grade_earned = float(grade_match.group(1))
        question.grade_total = float(grade_match.group(2))

    rubric_match = re.search(r"Rubric Justification:\s*", raw_block, re.IGNORECASE)
    items_text = raw_block[rubric_match.end():] if rubric_match else raw_block

    grade_in_items = _GRADE_RE.search(items_text)
    if grade_in_items:
        items_text = items_text[:grade_in_items.start()]

    pieces = [p.strip() for p in _CHECKBOX_SPLIT_RE.split(items_text) if p.strip()]

    for piece in pieces:
        marker = piece[0] if piece else ""
        status = _STATUS_MARKERS.get(marker)
        if not status:
            continue

        body = piece[1:].strip()
        reason_match = re.search(r"Reason:\s*(.+)", body, re.IGNORECASE | re.DOTALL)

        if reason_match:
            reason = _normalise_text(reason_match.group(1))
            item_text = _normalise_text(body[:reason_match.start()])
        else:
            reason = None
            item_text = _normalise_text(body)

        if item_text:
            question.items.append(
                RubricItem(
                    question_number=q_num,
                    question_title=question.title,
                    text=item_text,
                    status=status,
                    reason=reason,
                )
            )

    return question


def parse_feedback_text(raw_text: str, source_file: str = "") -> StudentFeedback:
    feedback = StudentFeedback(
        student_id=_extract_student_id(raw_text, source_file),
        source_file=source_file,
    )

    headers = list(_QUESTION_HEADER_RE.finditer(raw_text))

    for index, header in enumerate(headers):
        q_num = int(header.group(1))
        q_title = header.group(2).strip()

        block_start = header.end()
        block_end = headers[index + 1].start() if index + 1 < len(headers) else len(raw_text)

        feedback.questions.append(
            _parse_question_block(
                raw_text[block_start:block_end],
                q_num,
                q_title,
            )
        )

    return feedback


def validate_feedback_text(raw_text: str, filename: str) -> Tuple[bool, List[str]]:
    errors = []

    if not filename.lower().endswith(".txt"):
        errors.append("File is not a .txt file")

    if not _QUESTION_HEADER_RE.search(raw_text):
        errors.append("No QUESTION section header found")

    if not re.search(r"[☑☐◪]", raw_text):
        errors.append("No rubric checkbox marker (☑, ☐ or ◪) found")

    if not _GRADE_RE.search(raw_text):
        errors.append("No Grade: x/y line found")

    parsed = parse_feedback_text(raw_text, filename)

    if not parsed.questions:
        errors.append("No question blocks could be parsed")
    elif not parsed.all_items:
        errors.append("No rubric items could be parsed")

    return len(errors) == 0, errors


def load_feedback_folder(folder: Path):
    valid_files = []
    invalid_files = []

    for path in sorted(folder.glob("*.txt")):
        raw_text = path.read_text(encoding="utf-8", errors="replace")
        valid, errors = validate_feedback_text(raw_text, path.name)

        if valid:
            valid_files.append((path.name, raw_text))
        else:
            invalid_files.append({
                "file": path.name,
                "errors": errors,
            })

    return valid_files, invalid_files
