"""Assignment memorandum/specification context service."""
from pathlib import Path
from typing import List, Optional
from .models import MemoSection, RubricItem
from .assignment_io import (extract_pdf_text, parse_memo_sections_from_text,
                   match_section_for_question, relevant_spec_excerpt)

class AssignmentContext:
    """Extract and match assignment context used by the classifier."""
    def extract_pdf_text(self, pdf_source) -> str:
        return extract_pdf_text(pdf_source)

    def parse_memo(self, text: str) -> List[MemoSection]:
        return parse_memo_sections_from_text(text)

    def load_memo(self, memo_path: Path) -> List[MemoSection]:
        return self.parse_memo(self.extract_pdf_text(memo_path))

    def load_specification(self, spec_path: Optional[Path]) -> str:
        if spec_path and Path(spec_path).exists():
            return self.extract_pdf_text(spec_path)
        return ""

    def match_memo(self, sections: List[MemoSection], grade_total: Optional[float], question_title: Optional[str] = None):
        return match_section_for_question(sections, grade_total, question_title)

    def relevant_spec(self, specification_text: str, question_title: str, items: List[RubricItem], max_chars: int = 4000) -> str:
        return relevant_spec_excerpt(specification_text, question_title, items, max_chars)

__all__ = ["AssignmentContext"]
