"""Compatibility facade for EduCodeInsight pipeline helpers.

New code should import from the responsibility-specific modules directly.
This module intentionally contains no processing implementation; it re-exports
legacy names so older notebooks and imports continue to work.
"""
from .models import CATEGORIES, RubricItem, QuestionBlock, StudentFeedback, MemoSection, ClassificationResult
from .config import (
    MODEL_CONFIGS, DEFAULT_MODEL_LABEL, DEFAULT_MODEL, MAX_WORKERS, BATCH_SIZE,
    MAX_RETRIES, REQUEST_TIMEOUT, get_model_config, calculate_model_cost,
    estimate_processing_time, estimate_run_cost, get_enabled_models,
)
from .feedback_io import (
    _extract_student_id, parse_feedback_text, validate_feedback_text, load_feedback_folder,
)
from .assignment_io import (
    extract_pdf_text, parse_memo_sections_from_text, match_section_for_question, relevant_spec_excerpt,
)
from .prompts import (
    DEFAULT_CLASSIFICATION_PROMPT, SYSTEM_PROMPT_BATCH, normalise_classification_prompt,
    classification_prompt_hash,
)
from .usage import parse_token_usage, empty_usage_summary, add_usage_to_summary
from .llm_api import classify_items_batched
from .processing import process_one_feedback, _safe_result_filename, process_all_files_fast
from .analytics import build_overall_analysis, results_to_dataframe, category_counts, rubric_criterion_counts

# Service-class re-exports for older imports.
from .feedback_parser import FeedbackParser
from .feedback_validator import FeedbackValidator
from .assignment_context import AssignmentContext
from .llm_classifier import LLMClassifier
from .analysis_engine import AnalysisEngine
from .chart_generator import ChartGenerator
from .result_manager import ResultManager
from .report_generator import ReportGenerator
from .pipeline import EduCodeInsightPipeline

__all__ = [
    "CATEGORIES", "RubricItem", "QuestionBlock", "StudentFeedback", "MemoSection", "ClassificationResult",
    "MODEL_CONFIGS", "DEFAULT_MODEL_LABEL", "DEFAULT_MODEL", "MAX_WORKERS", "BATCH_SIZE",
    "MAX_RETRIES", "REQUEST_TIMEOUT", "get_model_config", "calculate_model_cost",
    "estimate_processing_time", "estimate_run_cost", "get_enabled_models",
    "parse_feedback_text", "validate_feedback_text", "load_feedback_folder", "extract_pdf_text",
    "parse_memo_sections_from_text", "match_section_for_question", "relevant_spec_excerpt",
    "DEFAULT_CLASSIFICATION_PROMPT", "SYSTEM_PROMPT_BATCH", "normalise_classification_prompt",
    "classification_prompt_hash", "parse_token_usage", "empty_usage_summary", "add_usage_to_summary",
    "classify_items_batched", "process_one_feedback", "process_all_files_fast",
    "build_overall_analysis", "results_to_dataframe", "category_counts", "rubric_criterion_counts",
    "FeedbackParser", "FeedbackValidator", "AssignmentContext", "LLMClassifier",
    "AnalysisEngine", "ChartGenerator", "ResultManager", "ReportGenerator", "EduCodeInsightPipeline",
]
