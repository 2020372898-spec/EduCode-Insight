"""Offline smoke tests for EduCodeInsight package imports and construction."""
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline import (
    DEFAULT_MODEL, FeedbackParser, FeedbackValidator, AssignmentContext,
    LLMClassifier, AnalysisEngine, ChartGenerator, ReportGenerator,
    ResultManager, EduCodeInsightPipeline,
)

def test_oop_services_construct():
    assert DEFAULT_MODEL == "openai/gpt-oss-120b"
    assert isinstance(FeedbackParser(), FeedbackParser)
    assert isinstance(FeedbackValidator(), FeedbackValidator)
    assert isinstance(AssignmentContext(), AssignmentContext)
    assert isinstance(LLMClassifier(api_key="test-key"), LLMClassifier)
    assert isinstance(AnalysisEngine(), AnalysisEngine)
    assert isinstance(ChartGenerator(), ChartGenerator)
    assert isinstance(ResultManager(), ResultManager)
    assert isinstance(EduCodeInsightPipeline(), EduCodeInsightPipeline)

if __name__ == "__main__":
    test_oop_services_construct()
    print("EduCodeInsight pipeline smoke test passed.")
