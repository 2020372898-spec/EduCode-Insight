"""Architecture checks for the responsibility-specific OOP service layer."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pipeline import (
    RubricItem, QuestionBlock, StudentFeedback, MemoSection, ClassificationResult,
    FeedbackParser, FeedbackValidator, AssignmentContext, LLMClassifier,
    AnalysisEngine, ChartGenerator, ResultManager, ReportGenerator,
    EduCodeInsightPipeline,
)


DOMAIN_MODELS = [RubricItem, QuestionBlock, StudentFeedback, MemoSection, ClassificationResult]
for model in DOMAIN_MODELS:
    assert model.__module__ == "pipeline.models", f"{model.__name__} still lives in {model.__module__}"

EXPECTED_MODULES = {
    FeedbackParser: "pipeline.feedback_parser",
    FeedbackValidator: "pipeline.feedback_validator",
    AssignmentContext: "pipeline.assignment_context",
    LLMClassifier: "pipeline.llm_classifier",
    AnalysisEngine: "pipeline.analysis_engine",
    ChartGenerator: "pipeline.chart_generator",
    ResultManager: "pipeline.result_manager",
    ReportGenerator: "pipeline.report_generator",
    EduCodeInsightPipeline: "pipeline.pipeline",
}

for cls, module_name in EXPECTED_MODULES.items():
    assert cls.__module__ == module_name, f"{cls.__name__} still lives in {cls.__module__}"

# Constructor injection/composition check.
parser = FeedbackParser()
validator = FeedbackValidator()
context = AssignmentContext()
analyzer = AnalysisEngine()
manager = ResultManager()
pipeline = EduCodeInsightPipeline(
    parser=parser,
    validator=validator,
    context=context,
    analyzer=analyzer,
    result_manager=manager,
)
assert pipeline.parser is parser
assert pipeline.validator is validator
assert pipeline.context is context
assert pipeline.analyzer is analyzer
assert pipeline.result_manager is manager



# core.py must remain a thin compatibility facade rather than a monolith.
core_path = ROOT / "pipeline" / "core.py"
core_lines = core_path.read_text(encoding="utf-8").splitlines()
assert len(core_lines) < 100, f"core.py is too large again: {len(core_lines)} lines"

# Responsibility-specific service modules should not depend on core.py.
service_files = [
    "feedback_parser.py", "feedback_validator.py", "assignment_context.py",
    "llm_classifier.py", "analysis_engine.py", "result_manager.py",
    "report_generator.py", "pipeline.py",
]
for filename in service_files:
    content = (ROOT / "pipeline" / filename).read_text(encoding="utf-8")
    assert "from .core import" not in content, f"{filename} still depends on core.py"

print("OOP architecture test passed.")
