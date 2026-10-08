"""High-level object-oriented orchestration for EduCodeInsight."""
from pathlib import Path
from typing import Optional
from .config import MAX_WORKERS, BATCH_SIZE, DEFAULT_MODEL, estimate_processing_time, estimate_run_cost
from .processing import process_all_files_fast
from .feedback_parser import FeedbackParser
from .feedback_validator import FeedbackValidator
from .assignment_context import AssignmentContext
from .llm_classifier import LLMClassifier
from .analysis_engine import AnalysisEngine
from .result_manager import ResultManager

class EduCodeInsightPipeline:
    """Coordinate parsing, validation, context, classification and analysis services.

    The orchestrator depends on abstractions supplied through its constructor, making
    services replaceable in tests and avoiding a monolithic God class.
    """
    def __init__(self, parser: Optional[FeedbackParser] = None,
                 validator: Optional[FeedbackValidator] = None,
                 context: Optional[AssignmentContext] = None,
                 classifier: Optional[LLMClassifier] = None,
                 analyzer: Optional[AnalysisEngine] = None,
                 result_manager: Optional[ResultManager] = None):
        self.parser = parser or FeedbackParser(); self.validator = validator or FeedbackValidator()
        self.context = context or AssignmentContext(); self.classifier = classifier
        self.analyzer = analyzer or AnalysisEngine(); self.result_manager = result_manager or ResultManager()

    def process_assignment(self, feedback_folder: Path, memo_path: Path, spec_path: Optional[Path] = None,
                           *, output_folder: Path = Path("EduCodeInsight_Output"), max_workers: int = MAX_WORKERS,
                           batch_size: int = BATCH_SIZE, model: str = DEFAULT_MODEL,
                           classification_prompt: Optional[str] = None) -> dict:
        if self.classifier is None or self.classifier.model != model or self.classifier.batch_size != batch_size:
            self.classifier = LLMClassifier(model=model, batch_size=batch_size)
        return process_all_files_fast(feedback_folder=feedback_folder, memo_path=memo_path, spec_path=spec_path,
                                      output_folder=output_folder, max_workers=max_workers, batch_size=batch_size,
                                      model=model, classification_prompt=classification_prompt, reuse_saved=False)

    def validate_uploaded_feedback(self, uploaded_files) -> tuple[list[tuple[str, str]], list[dict]]:
        """Validate Streamlit-like uploaded text files without requiring local paths."""
        valid, failures = [], []
        for uploaded in uploaded_files or []:
            name = getattr(uploaded, "name", "uploaded.txt")
            try:
                data = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
                raw = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else str(data)
                ok, reasons = self.validator.validate(raw, name)
                if ok: valid.append((name, raw))
                else: failures.append({"file": name, "stage": "validation", "reason": "; ".join(reasons)})
            except Exception as exc:
                failures.append({"file": name, "stage": "reading", "reason": f"{type(exc).__name__}: {exc}"})
        return valid, failures

    def analyse_assignment(self, run_result: dict) -> dict: return self.analyzer.assignment_analysis(run_result)
    def analyse_overall(self, assignment_runs: dict) -> dict: return self.analyzer.overall_analysis(assignment_runs)
    def estimate_time(self, number_of_files: int) -> dict: return estimate_processing_time(number_of_files)
    def estimate_cost(self, estimated_input_tokens: int, estimated_output_tokens: int, model: str = DEFAULT_MODEL) -> dict:
        return estimate_run_cost(model, estimated_input_tokens, estimated_output_tokens)

__all__ = ["EduCodeInsightPipeline"]
