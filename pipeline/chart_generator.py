"""Reusable chart generation service."""
import pandas as pd
import matplotlib.pyplot as plt

class ChartGenerator:
    """Create matplotlib figures without coupling charts to Streamlit."""
    def category_distribution(self, counts: pd.Series):
        fig, ax = plt.subplots(figsize=(8, 5))
        nonzero = counts[counts > 0]
        if len(nonzero):
            ax.bar(nonzero.index, nonzero.values)
            ax.set_ylabel("Failed / partially met rubric items")
            ax.set_title("Error Category Distribution")
            ax.tick_params(axis="x", rotation=20)
        else:
            ax.text(0.5, 0.5, "No errors found", ha="center", va="center")
            ax.set_axis_off()
        fig.tight_layout(); return fig

    def top_recurring_errors(self, patterns: pd.DataFrame, top_n: int = 10):
        fig, ax = plt.subplots(figsize=(10, 6)); top = patterns.head(top_n).copy()
        if not top.empty:
            labels = [str(x)[:75] + ("..." if len(str(x)) > 75 else "") for x in top["rubric_text"]]
            ax.barh(labels[::-1], top["count"].values[::-1]); ax.set_xlabel("Number of students")
            ax.set_title("Most Frequently Failed / Partially Met Criteria")
        else:
            ax.text(0.5, 0.5, "No recurring patterns found", ha="center", va="center"); ax.set_axis_off()
        fig.tight_layout(); return fig

    def errors_by_question(self, df: pd.DataFrame):
        fig, ax = plt.subplots(figsize=(10, 5))
        if df.empty:
            ax.text(0.5, 0.5, "No errors found", ha="center", va="center"); ax.set_axis_off()
        else:
            counts = df.groupby("question_number").size().sort_index(); ax.bar(counts.index.astype(str), counts.values)
            ax.set_xlabel("Question"); ax.set_ylabel("Failed / partially met items"); ax.set_title("Failed / Partially Met Criteria by Question")
        fig.tight_layout(); return fig

__all__ = ["ChartGenerator"]
