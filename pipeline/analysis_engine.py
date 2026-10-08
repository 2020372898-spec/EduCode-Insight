"""Analysis service for per-assignment and overall results."""
from typing import List
import pandas as pd
from .analytics import results_to_dataframe, category_counts, rubric_criterion_counts, build_overall_analysis

class AnalysisEngine:
    """Transform classifier output into analytical structures."""
    def results_to_dataframe(self, results: List[dict]) -> pd.DataFrame:
        return results_to_dataframe(results)

    def category_counts(self, df: pd.DataFrame) -> pd.Series:
        return category_counts(df)

    def recurring_errors(self, df: pd.DataFrame) -> pd.DataFrame:
        return rubric_criterion_counts(df)

    def assignment_analysis(self, run_result: dict) -> dict:
        df = self.results_to_dataframe(run_result.get("results", []))
        return {"dataframe": df, "category_counts": self.category_counts(df),
                "recurring_errors": self.recurring_errors(df)}

    def overall_analysis(self, assignment_runs: dict) -> dict:
        return build_overall_analysis(assignment_runs)

__all__ = ["AnalysisEngine"]
