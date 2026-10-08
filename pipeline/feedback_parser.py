"""Feedback parsing service."""
from pathlib import Path
from .models import StudentFeedback
from .feedback_io import parse_feedback_text, _extract_student_id, load_feedback_folder

class FeedbackParser:
    """Parse raw student feedback into domain objects.

    This class owns the parsing responsibility exposed to the application. Low-level
    regex helpers remain private implementation utilities in ``core`` for backwards
    compatibility with the original research prototype.
    """
    def parse(self, raw_text: str, source_file: str = "") -> StudentFeedback:
        return parse_feedback_text(raw_text, source_file)

    def extract_student_id(self, raw_text: str, source_file: str) -> str:
        return _extract_student_id(raw_text, source_file)

    def load_folder(self, folder: Path):
        return load_feedback_folder(folder)

__all__ = ["FeedbackParser"]
