"""DataFrame conversion and cross-assignment analytics helpers."""
from __future__ import annotations

from typing import List

import pandas as pd

from .config import DEFAULT_MODEL_LABEL
from .models import CATEGORIES

# ============================================================
# OVERALL ANALYSIS ACROSS MULTIPLE ASSIGNMENTS
# ============================================================

def build_overall_analysis(
    assignment_runs: dict,
) -> dict:
    """
    Combine multiple assignment-run dictionaries.

    Expected input:
        {
            "Practical 2": run_result_1,
            "Practical 3": run_result_2,
            ...
        }

    Each run_result should be the dictionary returned by
    process_all_files_fast().

    No LLM calls are made by this function.
    """

    combined_frames = []
    assignment_summary_rows = []

    total_assignments = 0
    total_student_submissions = 0
    total_failed_partial_items = 0

    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    total_api_requests = 0

    total_ai_cost_usd = 0.0
    total_processing_seconds = 0.0


    for assignment_name, run_data in assignment_runs.items():

        if not run_data:
            continue

        results = run_data.get(
            "results",
            [],
        )

        if not results:
            continue

        total_assignments += 1

        assignment_df = (
            results_to_dataframe(
                results
            )
        )

        if not assignment_df.empty:

            assignment_df = (
                assignment_df.copy()
            )

            assignment_df[
                "assignment"
            ] = assignment_name

            combined_frames.append(
                assignment_df
            )


        processed_count = int(
            run_data.get(
                "processed_count",
                len(results),
            )
        )

        failed_partial_items = int(
            run_data.get(
                "failed_partial_items",
                len(assignment_df),
            )
        )

        input_tokens = int(
            run_data.get(
                "dataset_input_tokens",
                0,
            )
        )

        output_tokens = int(
            run_data.get(
                "dataset_output_tokens",
                0,
            )
        )

        tokens = int(
            run_data.get(
                "dataset_total_tokens",
                input_tokens + output_tokens,
            )
        )

        api_requests = int(
            run_data.get(
                "dataset_api_requests",
                0,
            )
        )

        assignment_cost = float(
            run_data.get(
                "dataset_cost_usd",
                0.0,
            )
        )

        elapsed_seconds = float(
            run_data.get(
                "elapsed_seconds",
                0.0,
            )
        )

        model_label = (
            run_data.get(
                "model_label",
                DEFAULT_MODEL_LABEL,
            )
        )

        prompt_modified = bool(
            run_data.get(
                "prompt_modified",
                False,
            )
        )


        total_student_submissions += (
            processed_count
        )

        total_failed_partial_items += (
            failed_partial_items
        )

        total_input_tokens += (
            input_tokens
        )

        total_output_tokens += (
            output_tokens
        )

        total_tokens += (
            tokens
        )

        total_api_requests += (
            api_requests
        )

        total_ai_cost_usd += (
            assignment_cost
        )

        total_processing_seconds += (
            elapsed_seconds
        )


        assignment_summary_rows.append(
            {
                "assignment":
                    assignment_name,

                "students_processed":
                    processed_count,

                "failed_partial_items":
                    failed_partial_items,

                "model":
                    model_label,

                "prompt_modified":
                    prompt_modified,

                "input_tokens":
                    input_tokens,

                "output_tokens":
                    output_tokens,

                "total_tokens":
                    tokens,

                "api_requests":
                    api_requests,

                "ai_cost_usd":
                    round(
                        assignment_cost,
                        6,
                    ),

                "processing_minutes":
                    round(
                        elapsed_seconds / 60,
                        2,
                    ),
            }
        )


    if combined_frames:

        combined_df = pd.concat(
            combined_frames,
            ignore_index=True,
        )

    else:

        combined_df = pd.DataFrame()


    assignment_summary_df = pd.DataFrame(
        assignment_summary_rows
    )


    # --------------------------------------------------------
    # UNIQUE STUDENTS
    # --------------------------------------------------------

    unique_students = 0

    if (
        not combined_df.empty
        and
        "student_id" in combined_df.columns
    ):

        unique_students = (
            combined_df[
                "student_id"
            ]
            .dropna()
            .astype(str)
            .nunique()
        )


    # --------------------------------------------------------
    # CATEGORY DISTRIBUTION
    # --------------------------------------------------------

    if (
        not combined_df.empty
        and
        "category" in combined_df.columns
    ):

        category_distribution = (
            combined_df[
                "category"
            ]
            .value_counts()
            .rename_axis(
                "category"
            )
            .reset_index(
                name="count"
            )
        )

    else:

        category_distribution = pd.DataFrame(
            columns=[
                "category",
                "count",
            ]
        )


    # --------------------------------------------------------
    # RECURRING ERRORS
    # --------------------------------------------------------

    if (
        not combined_df.empty
        and
        "rubric_text" in combined_df.columns
    ):

        recurring_errors = (
            combined_df
            .groupby(
                "rubric_text",
                dropna=False,
            )
            .agg(
                occurrences=(
                    "rubric_text",
                    "size",
                ),
                students_affected=(
                    "student_id",
                    "nunique",
                ),
                assignments_affected=(
                    "assignment",
                    "nunique",
                ),
                dominant_category=(
                    "category",
                    lambda values:
                        values.value_counts().index[0]
                        if not values.dropna().empty
                        else "Unknown",
                ),
            )
            .reset_index()
            .sort_values(
                [
                    "students_affected",
                    "occurrences",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
            .reset_index(
                drop=True
            )
        )

    else:

        recurring_errors = pd.DataFrame(
            columns=[
                "rubric_text",
                "occurrences",
                "students_affected",
                "assignments_affected",
                "dominant_category",
            ]
        )


    # --------------------------------------------------------
    # ERRORS BY ASSIGNMENT
    # --------------------------------------------------------

    if not combined_df.empty:

        errors_by_assignment = (
            combined_df
            .groupby(
                "assignment"
            )
            .size()
            .reset_index(
                name="error_count"
            )
            .sort_values(
                "error_count",
                ascending=False,
            )
            .reset_index(
                drop=True
            )
        )

    else:

        errors_by_assignment = pd.DataFrame(
            columns=[
                "assignment",
                "error_count",
            ]
        )


    # --------------------------------------------------------
    # CATEGORY BY ASSIGNMENT
    # --------------------------------------------------------

    if (
        not combined_df.empty
        and
        "category" in combined_df.columns
    ):

        category_by_assignment = (
            combined_df
            .groupby(
                [
                    "assignment",
                    "category",
                ]
            )
            .size()
            .reset_index(
                name="count"
            )
        )

    else:

        category_by_assignment = pd.DataFrame(
            columns=[
                "assignment",
                "category",
                "count",
            ]
        )


    # --------------------------------------------------------
    # MODEL USAGE
    # --------------------------------------------------------

    if not assignment_summary_df.empty:

        model_usage = (
            assignment_summary_df
            .groupby(
                "model",
                dropna=False,
            )
            .agg(
                assignments=(
                    "assignment",
                    "count",
                ),
                students_processed=(
                    "students_processed",
                    "sum",
                ),
                total_tokens=(
                    "total_tokens",
                    "sum",
                ),
                total_cost_usd=(
                    "ai_cost_usd",
                    "sum",
                ),
            )
            .reset_index()
        )

    else:

        model_usage = pd.DataFrame(
            columns=[
                "model",
                "assignments",
                "students_processed",
                "total_tokens",
                "total_cost_usd",
            ]
        )


    # --------------------------------------------------------
    # STUDENT TRENDS
    # --------------------------------------------------------

    if (
        not combined_df.empty
        and
        "student_id" in combined_df.columns
    ):

        student_overall = (
            combined_df
            .groupby(
                "student_id"
            )
            .agg(
                total_failed_partial_items=(
                    "student_id",
                    "size",
                ),
                assignments_affected=(
                    "assignment",
                    "nunique",
                ),
            )
            .reset_index()
            .sort_values(
                "total_failed_partial_items",
                ascending=False,
            )
            .reset_index(
                drop=True
            )
        )

    else:

        student_overall = pd.DataFrame(
            columns=[
                "student_id",
                "total_failed_partial_items",
                "assignments_affected",
            ]
        )


    return {

        "summary": {

            "assignments_analysed":
                total_assignments,

            "student_submissions_processed":
                total_student_submissions,

            "unique_students":
                unique_students,

            "failed_partial_items":
                total_failed_partial_items,

            "input_tokens":
                total_input_tokens,

            "output_tokens":
                total_output_tokens,

            "total_tokens":
                total_tokens,

            "api_requests":
                total_api_requests,

            "total_ai_cost_usd":
                round(
                    total_ai_cost_usd,
                    6,
                ),

            "total_processing_minutes":
                round(
                    total_processing_seconds / 60,
                    2,
                ),
        },

        "combined_dataframe":
            combined_df,

        "assignment_summary":
            assignment_summary_df,

        "category_distribution":
            category_distribution,

        "recurring_errors":
            recurring_errors,

        "errors_by_assignment":
            errors_by_assignment,

        "category_by_assignment":
            category_by_assignment,

        "model_usage":
            model_usage,

        "student_overall":
            student_overall,
    }




def results_to_dataframe(results: List[dict]) -> pd.DataFrame:
    """
    Convert all successfully processed student results into
    one Pandas DataFrame.

    Each row represents one failed or partially met rubric item.
    """

    rows = []

    for student_result in results:

        student_id = student_result.get("student_id")
        source_file = student_result.get("source_file")

        for question in student_result.get("questions", []):

            question_number = question.get("question_number")
            question_title = question.get("question_title")
            grade_earned = question.get("grade_earned")
            grade_total = question.get("grade_total")

            for item in question.get("failed_items", []):

                rows.append({
                    "student_id": student_id,
                    "source_file": source_file,

                    "question_number": question_number,
                    "question_title": question_title,

                    "grade_earned": grade_earned,
                    "grade_total": grade_total,

                    "rubric_text": item.get("criterion"),
                    "status": item.get("status"),

                    "reason": item.get("reason"),

                    "category": item.get("category"),

                    "justification": item.get(
                        "justification"
                    ),

                    "classification_source": item.get(
                        "classification_source",
                        "unknown",
                    ),
                })

    # --------------------------------------------------------
    # Define columns explicitly so the DataFrame still has
    # the correct structure even when there are no errors.
    # --------------------------------------------------------

    columns = [
        "student_id",
        "source_file",

        "question_number",
        "question_title",

        "grade_earned",
        "grade_total",

        "rubric_text",
        "status",

        "reason",

        "category",
        "justification",

        "classification_source",
    ]

    return pd.DataFrame(
        rows,
        columns=columns,
    )


# ============================================================
# Count errors by category
# ============================================================

def category_counts(df: pd.DataFrame) -> pd.Series:
    """
    Count how many failed/partial rubric items belong to
    each of the four error categories.
    """

    if df.empty:
        return pd.Series(
            0,
            index=CATEGORIES,
            dtype=int,
        )

    return (
        df["category"]
        .value_counts()
        .reindex(
            CATEGORIES,
            fill_value=0,
        )
    )


# ============================================================
# Detect recurring rubric patterns
# ============================================================

def rubric_criterion_counts(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Identify rubric criteria that were failed or partially met
    by the largest number of students.

    For every criterion:
    - count the number of unique students affected;
    - determine the dominant LLM error category.
    """

    if df.empty:

        return pd.DataFrame(
            columns=[
                "rubric_text",
                "count",
                "dominant_category",
            ]
        )

    grouped = (
        df
        .groupby(
            "rubric_text",
            dropna=False,
        )
        .agg(

            # Number of different students who
            # experienced this rubric error
            count=(
                "student_id",
                "nunique",
            ),

            # Most common LLM classification
            # for this rubric criterion
            dominant_category=(
                "category",
                lambda values:
                    values.value_counts().index[0]
                    if not values.dropna().empty
                    else "Unknown",
            ),
        )
        .reset_index()
        .sort_values(
            [
                "count",
                "rubric_text",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(drop=True)
    )

    return grouped
