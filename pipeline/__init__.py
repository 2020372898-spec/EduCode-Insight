"""EduCodeInsight OOP pipeline package."""
from .models import (
    CATEGORIES,
    RubricItem,
    QuestionBlock,
    StudentFeedback,
    MemoSection,
    ClassificationResult,
)
from .core import (
    MODEL_CONFIGS, DEFAULT_MODEL_LABEL, DEFAULT_MODEL,
    MAX_WORKERS, BATCH_SIZE, MAX_RETRIES, REQUEST_TIMEOUT,
    get_model_config, calculate_model_cost, estimate_processing_time, estimate_run_cost,
    parse_feedback_text, validate_feedback_text, load_feedback_folder, extract_pdf_text,
    parse_memo_sections_from_text, match_section_for_question, relevant_spec_excerpt,
    normalise_classification_prompt, classification_prompt_hash, parse_token_usage,
    empty_usage_summary, add_usage_to_summary, classify_items_batched, process_one_feedback,
    process_all_files_fast, build_overall_analysis, results_to_dataframe, category_counts,
    rubric_criterion_counts,
)
from .feedback_parser import FeedbackParser
from .feedback_validator import FeedbackValidator
from .assignment_context import AssignmentContext
from .llm_classifier import LLMClassifier
from .analysis_engine import AnalysisEngine
from .chart_generator import ChartGenerator
from .report_generator import ReportGenerator
from .result_manager import ResultManager
from .pipeline import EduCodeInsightPipeline
