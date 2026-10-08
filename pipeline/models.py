"""Domain data models used throughout EduCodeInsight.

This module contains the application's shared data structures.  Keeping domain
models separate from service classes makes the architecture easier to reason
about: ``models.py`` represents data, while the other pipeline modules represent
behaviour and orchestration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pydantic import BaseModel, field_validator


CATEGORIES = [
    "Syntax Error",
    "Semantic Error",
    "Best Practice Violation",
    "Rule-Based Error",
]


@dataclass(slots=True)
class RubricItem:
    """A single rubric criterion extracted from lecturer feedback."""

    question_number: int
    question_title: str
    text: str
    status: str  # met | partial | failed
    reason: Optional[str] = None

    @property
    def met(self) -> bool:
        """Return ``True`` when the criterion was fully met."""
        return self.status == "met"


@dataclass(slots=True)
class QuestionBlock:
    """Feedback and rubric items belonging to one assignment question."""

    number: int
    title: str
    grade_earned: Optional[float] = None
    grade_total: Optional[float] = None
    items: List[RubricItem] = field(default_factory=list)


@dataclass(slots=True)
class StudentFeedback:
    """Parsed feedback for one student submission."""

    student_id: str
    source_file: str
    questions: List[QuestionBlock] = field(default_factory=list)

    @property
    def failed_items(self) -> List[RubricItem]:
        """Return failed and partially-met items that require classification."""
        return [
            item
            for question in self.questions
            for item in question.items
            if not item.met
        ]

    @property
    def all_items(self) -> List[RubricItem]:
        """Return every rubric item across all questions."""
        return [item for question in self.questions for item in question.items]


@dataclass(slots=True)
class MemoSection:
    """A parsed section of the assignment marking memorandum."""

    title: str
    marks: float
    body: str


class ClassificationResult(BaseModel):
    """Validated LLM classification for one failed rubric criterion."""

    category: str
    justification: str
    source: str = "llm"

    @field_validator("category")
    @classmethod
    def category_must_be_valid(cls, value: str) -> str:
        if value not in CATEGORIES:
            raise ValueError(f"{value!r} is not one of {CATEGORIES}")
        return value


__all__ = [
    "CATEGORIES",
    "RubricItem",
    "QuestionBlock",
    "StudentFeedback",
    "MemoSection",
    "ClassificationResult",
]
