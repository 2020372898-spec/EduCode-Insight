"""Input bytes/text, as supplied by Streamlit, should work without paths."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import AssignmentContext, FeedbackParser, FeedbackValidator


def test_in_memory_feedback():
    text = "QUESTION 1: Example\nGrade: 0/1\nRubric Justification:\n☐ Compiles (0/1)\n"
    valid, errors = FeedbackValidator().validate(text, "Student1.txt")
    assert valid, errors
    feedback = FeedbackParser().parse(text, "Student1.txt")
    assert feedback.student_id == "Student1"
    assert len(feedback.questions) == 1


def test_pdf_service_accepts_bytes_interface():
    # No PDF content is needed to verify that the service exists and is callable.
    assert callable(AssignmentContext().extract_pdf_text)


if __name__ == "__main__":
    test_in_memory_feedback()
    test_pdf_service_accepts_bytes_interface()
    print("Upload-input smoke test passed.")
