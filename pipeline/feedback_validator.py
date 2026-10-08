"""Feedback validation service."""
from pathlib import Path
from typing import List, Tuple
from .feedback_io import validate_feedback_text, load_feedback_folder

class FeedbackValidator:
    """Validate uploaded feedback before expensive LLM processing."""
    def validate(self, raw_text: str, filename: str) -> Tuple[bool, List[str]]:
        return validate_feedback_text(raw_text, filename)

    def validate_folder(self, folder: Path):
        return load_feedback_folder(folder)

__all__ = ["FeedbackValidator"]
