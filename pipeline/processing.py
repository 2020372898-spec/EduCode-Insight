"""Per-student and whole-assignment processing orchestration."""
from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

import requests

from .assignment_io import (
    extract_pdf_text,
    match_section_for_question,
    parse_memo_sections_from_text,
    relevant_spec_excerpt,
)
from .config import (
    BATCH_SIZE, DEFAULT_MODEL, MAX_WORKERS,
    calculate_model_cost, estimate_processing_time, get_model_config,
)
from .feedback_io import _extract_student_id, load_feedback_folder, parse_feedback_text
from .llm_api import classify_items_batched
from .models import MemoSection
from .prompts import (
    DEFAULT_CLASSIFICATION_PROMPT, classification_prompt_hash, normalise_classification_prompt,
)

# ============================================================
# PROCESS ONE STUDENT FEEDBACK FILE
# ============================================================

def process_one_feedback(
    filename: str,
    raw_text: str,
    memo_sections: List[MemoSection],
    specification_text: str,
    *,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    classification_prompt: Optional[str] = None,
    batch_size: int = BATCH_SIZE,
) -> dict:
    """
    Process one student's feedback file.

    The function:
    - parses the student's feedback;
    - identifies failed / partially met rubric items;
    - matches relevant memorandum and specification context;
    - classifies errors using the selected AI model;
    - uses the lecturer-approved prompt;
    - aggregates token usage and estimated model cost;
    - records the processing time for the student.
    """

    started = time.perf_counter()

    # --------------------------------------------------------
    # PREPARE PROMPT
    # --------------------------------------------------------

    selected_prompt = (
        normalise_classification_prompt(
            classification_prompt
        )
    )

    prompt_hash = (
        classification_prompt_hash(
            selected_prompt
        )
    )

    prompt_modified = (
        selected_prompt
        !=
        DEFAULT_CLASSIFICATION_PROMPT.strip()
    )


    # --------------------------------------------------------
    # MODEL INFORMATION
    # --------------------------------------------------------

    model_config = (
        get_model_config(
            model
        )
    )


    # --------------------------------------------------------
    # PARSE FEEDBACK
    # --------------------------------------------------------

    feedback = (
        parse_feedback_text(
            raw_text,
            filename,
        )
    )

    questions_out = []


    # --------------------------------------------------------
    # STUDENT-LEVEL USAGE TOTALS
    # --------------------------------------------------------

    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    total_api_requests = 0

    total_failed_items = 0


    # --------------------------------------------------------
    # CREATE ONE SESSION PER STUDENT
    # --------------------------------------------------------

    with requests.Session() as session:

        for question in feedback.questions:

            # ------------------------------------------------
            # MATCH MEMO SECTION
            # ------------------------------------------------

            memo_match = (
                match_section_for_question(
                    memo_sections,
                    question.grade_total,
                    question.title,
                )
            )

            memo_context = (
                memo_match.body
                if memo_match
                else None
            )


            # ------------------------------------------------
            # FAILED / PARTIALLY MET ITEMS
            # ------------------------------------------------

            failed_items = [
                item
                for item in question.items
                if not item.met
            ]

            total_failed_items += (
                len(
                    failed_items
                )
            )


            # ------------------------------------------------
            # FIND RELEVANT SPECIFICATION CONTEXT
            # ------------------------------------------------

            spec_excerpt = (
                relevant_spec_excerpt(
                    specification_text,
                    question.title,
                    failed_items,
                )
            )


            # ------------------------------------------------
            # CLASSIFY
            # ------------------------------------------------

            classifications, usage_summary = (
                classify_items_batched(
                    failed_items,
                    memo_context=
                        memo_context,
                    specification_context=
                        spec_excerpt,
                    api_key=
                        api_key,
                    model=
                        model,
                    classification_prompt=
                        selected_prompt,
                    batch_size=
                        batch_size,
                    session=
                        session,
                )
            )


            # ------------------------------------------------
            # ADD QUESTION USAGE TO STUDENT TOTAL
            # ------------------------------------------------

            total_input_tokens += int(
                usage_summary.get(
                    "input_tokens",
                    0,
                )
            )

            total_output_tokens += int(
                usage_summary.get(
                    "output_tokens",
                    0,
                )
            )

            total_tokens += int(
                usage_summary.get(
                    "total_tokens",
                    0,
                )
            )

            total_api_requests += int(
                usage_summary.get(
                    "api_requests",
                    0,
                )
            )


            # ------------------------------------------------
            # BUILD FAILED ITEM OUTPUT
            # ------------------------------------------------

            failed_out = []

            for item, result in zip(
                failed_items,
                classifications,
            ):

                failed_out.append(
                    {
                        "criterion":
                            item.text,

                        "status":
                            item.status,

                        "reason":
                            item.reason,

                        "category":
                            result.category,

                        "justification":
                            result.justification,

                        "classification_source":
                            result.source,

                        "rule_violated":
                            (
                                item.text
                                if (
                                    result.category
                                    ==
                                    "Rule-Based Error"
                                )
                                else None
                            ),
                    }
                )


            # ------------------------------------------------
            # QUESTION OUTPUT
            # ------------------------------------------------

            questions_out.append(
                {
                    "question_number":
                        question.number,

                    "question_title":
                        question.title,

                    "grade_earned":
                        question.grade_earned,

                    "grade_total":
                        question.grade_total,

                    "failed_items":
                        failed_out,
                }
            )


    # --------------------------------------------------------
    # CALCULATE STUDENT COST
    # --------------------------------------------------------

    estimated_cost_usd = (
        calculate_model_cost(
            model,
            total_input_tokens,
            total_output_tokens,
        )
    )


    # --------------------------------------------------------
    # PROCESSING TIME
    # --------------------------------------------------------

    elapsed_seconds = (
        time.perf_counter()
        -
        started
    )


    # --------------------------------------------------------
    # FINAL STUDENT RESULT
    # --------------------------------------------------------

    return {

        "student_id":
            feedback.student_id,

        "source_file":
            filename,

        "questions":
            questions_out,


        # ====================================================
        # ANALYSIS METADATA
        # ====================================================

        "analysis_metadata": {

            "model_label":
                model_config[
                    "label"
                ],

            "model_id":
                model,

            "prompt_used":
                selected_prompt,

            "prompt_hash":
                prompt_hash,

            "prompt_modified":
                prompt_modified,

            "batch_size":
                batch_size,

            "failed_partial_items":
                total_failed_items,

            "input_tokens":
                total_input_tokens,

            "output_tokens":
                total_output_tokens,

            "total_tokens":
                total_tokens,

            "api_requests":
                total_api_requests,

            "estimated_cost_usd":
                round(
                    estimated_cost_usd,
                    8,
                ),

            "processing_seconds":
                round(
                    elapsed_seconds,
                    3,
                ),
        },
    }

# ============================================================
# FAST ASSIGNMENT PROCESSING
# ============================================================

def _safe_result_filename(
    filename: str,
    raw_text: str,
) -> str:
    """
    Create a safe JSON filename using the student ID.
    """

    student = (
        _extract_student_id(
            raw_text,
            filename,
        )
    )

    safe = re.sub(
        r"[^A-Za-z0-9_.-]+",
        "_",
        student,
    )

    return f"{safe}.json"


# ============================================================
# PROCESS ALL STUDENT FEEDBACK FILES
# ============================================================

def process_all_files_fast(
    feedback_folder: Path,
    memo_path: Path,
    spec_path: Optional[Path] = None,
    *,
    output_folder: Path = Path("EduCodeInsight_Output"),
    max_workers: int = MAX_WORKERS,
    batch_size: int = BATCH_SIZE,
    model: str = DEFAULT_MODEL,
    classification_prompt: Optional[str] = None,
    reuse_saved: bool = True,
):
    """
    Process all valid student feedback files for one assignment.

    The function:
    - validates feedback files;
    - loads the memorandum;
    - loads the assignment specification;
    - uses the lecturer-selected AI model;
    - uses the lecturer-approved classification prompt;
    - processes multiple students concurrently;
    - reuses compatible cached results;
    - records token usage;
    - calculates AI cost;
    - records wall-clock processing time;
    - calculates throughput;
    - returns assignment-wide metadata.
    """

    # ========================================================
    # START TIMER
    # ========================================================

    start_time = time.perf_counter()


    # ========================================================
    # PREPARE OUTPUT FOLDER
    # ========================================================

    output_folder = Path(
        output_folder
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True,
    )


    # ========================================================
    # PREPARE CLASSIFICATION PROMPT
    # ========================================================

    selected_prompt = (
        normalise_classification_prompt(
            classification_prompt
        )
    )

    selected_prompt_hash = (
        classification_prompt_hash(
            selected_prompt
        )
    )

    prompt_modified = (
        selected_prompt
        !=
        DEFAULT_CLASSIFICATION_PROMPT.strip()
    )


    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    model_config = (
        get_model_config(
            model
        )
    )


    # ========================================================
    # LOAD AND VALIDATE FEEDBACK FILES
    # ========================================================

    valid_files, invalid_files = (
        load_feedback_folder(
            feedback_folder
        )
    )


    # ========================================================
    # LOAD MEMORANDUM
    # ========================================================

    memo_text = (
        extract_pdf_text(
            memo_path
        )
    )

    memo_sections = (
        parse_memo_sections_from_text(
            memo_text
        )
    )


    # ========================================================
    # LOAD ASSIGNMENT SPECIFICATION
    # ========================================================

    specification_text = ""

    if (
        spec_path
        and
        Path(spec_path).exists()
    ):

        specification_text = (
            extract_pdf_text(
                spec_path
            )
        )


    # ========================================================
    # TOGETHER API KEY
    # ========================================================

    api_key = (
        os.environ.get(
            "TOGETHER_API_KEY"
        )
    )

    if not api_key:

        raise RuntimeError(
            "TOGETHER_API_KEY is not available."
        )


    # ========================================================
    # RESULT CONTAINERS
    # ========================================================

    results = []

    fresh_results = []

    failures = []

    cached = 0

    work = []


    # ========================================================
    # CHECK SAVED RESULTS
    # ========================================================

    for filename, raw_text in valid_files:

        result_path = (
            output_folder
            /
            _safe_result_filename(
                filename,
                raw_text,
            )
        )

        if (
            reuse_saved
            and
            result_path.exists()
        ):

            try:

                cached_result = (
                    json.loads(
                        result_path.read_text(
                            encoding="utf-8"
                        )
                    )
                )

                metadata = (
                    cached_result.get(
                        "analysis_metadata",
                        {},
                    )
                )

                cached_model = (
                    metadata.get(
                        "model_id"
                    )
                )

                cached_prompt_hash = (
                    metadata.get(
                        "prompt_hash"
                    )
                )

                cached_batch_size = int(
                    metadata.get(
                        "batch_size",
                        -1,
                    )
                )

                cache_matches = (
                    cached_model == model
                    and
                    cached_prompt_hash
                    == selected_prompt_hash
                    and
                    cached_batch_size
                    == batch_size
                )

                if cache_matches:

                    results.append(
                        cached_result
                    )

                    cached += 1

                    continue

            except Exception:

                pass

        work.append(
            (
                filename,
                raw_text,
                result_path,
            )
        )


    # ========================================================
    # COUNTS
    # ========================================================

    total = len(
        valid_files
    )

    fresh_total = len(
        work
    )


    # ========================================================
    # PRE-RUN TIME ESTIMATE
    # ========================================================

    time_estimate = (
        estimate_processing_time(
            fresh_total
        )
    )


    # ========================================================
    # DISPLAY PRE-RUN SUMMARY
    # ========================================================

    print()

    print(
        "EduCodeInsight Run Estimate"
    )

    print(
        "---------------------------"
    )

    print(
        f"Valid files            : {total}"
    )

    print(
        f"Invalid files          : {len(invalid_files)}"
    )

    print(
        f"Cached results reused  : {cached}"
    )

    print(
        f"Fresh files to process : {fresh_total}"
    )

    print(
        (
            f"Selected model         : "
            f"{model_config['label']}"
        )
    )

    print(
        (
            f"Workers / batch        : "
            f"{max_workers} / {batch_size}"
        )
    )

    print(
        (
            f"Prompt modified        : "
            f"{prompt_modified}"
        )
    )

    if fresh_total > 0:

        print(
            (
                "Estimated time         : "
                f"{time_estimate['lower_minutes']}"
                " - "
                f"{time_estimate['upper_minutes']}"
                " minutes"
            )
        )

    else:

        print(
            "Estimated time         : No fresh processing required"
        )


    # ========================================================
    # PROCESS FRESH FILES
    # ========================================================

    if work:

        with ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:

            future_map = {

                executor.submit(
                    process_one_feedback,
                    filename,
                    raw_text,
                    memo_sections,
                    specification_text,
                    api_key=api_key,
                    model=model,
                    classification_prompt=
                        selected_prompt,
                    batch_size=batch_size,
                ):
                (
                    filename,
                    result_path,
                )

                for (
                    filename,
                    raw_text,
                    result_path,
                ) in work
            }


            completed = 0


            for future in (
                as_completed(
                    future_map
                )
            ):

                (
                    filename,
                    result_path,
                ) = (
                    future_map[
                        future
                    ]
                )

                completed += 1

                try:

                    result = (
                        future.result()
                    )

                    result_path.write_text(
                        json.dumps(
                            result,
                            indent=2,
                            ensure_ascii=False,
                        ),
                        encoding="utf-8",
                    )

                    results.append(
                        result
                    )

                    fresh_results.append(
                        result
                    )

                    state = "OK"

                except Exception as exc:

                    failures.append(
                        (
                            f"{filename}: "
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        )
                    )

                    state = "FAILED"

                print(
                    (
                        f"[{completed:>3}/"
                        f"{fresh_total}] "
                        f"{state:<6} "
                        f"{filename}"
                    )
                )


    # ========================================================
    # AGGREGATE COMPLETE RESULT METADATA
    # ========================================================

    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    total_api_requests = 0
    total_failed_partial_items = 0

    for result in results:

        metadata = (
            result.get(
                "analysis_metadata",
                {},
            )
        )

        total_input_tokens += int(
            metadata.get(
                "input_tokens",
                0,
            )
        )

        total_output_tokens += int(
            metadata.get(
                "output_tokens",
                0,
            )
        )

        total_tokens += int(
            metadata.get(
                "total_tokens",
                0,
            )
        )

        total_api_requests += int(
            metadata.get(
                "api_requests",
                0,
            )
        )

        total_failed_partial_items += int(
            metadata.get(
                "failed_partial_items",
                0,
            )
        )


    # ========================================================
    # CURRENT RUN USAGE
    # ========================================================

    run_input_tokens = 0
    run_output_tokens = 0
    run_total_tokens = 0
    run_api_requests = 0

    for result in fresh_results:

        metadata = (
            result.get(
                "analysis_metadata",
                {},
            )
        )

        run_input_tokens += int(
            metadata.get(
                "input_tokens",
                0,
            )
        )

        run_output_tokens += int(
            metadata.get(
                "output_tokens",
                0,
            )
        )

        run_total_tokens += int(
            metadata.get(
                "total_tokens",
                0,
            )
        )

        run_api_requests += int(
            metadata.get(
                "api_requests",
                0,
            )
        )


    # ========================================================
    # COSTS
    # ========================================================

    actual_run_cost_usd = (
        calculate_model_cost(
            model,
            run_input_tokens,
            run_output_tokens,
        )
    )

    dataset_cost_usd = (
        calculate_model_cost(
            model,
            total_input_tokens,
            total_output_tokens,
        )
    )


    # ========================================================
    # WALL-CLOCK TIME
    # ========================================================

    elapsed = (
        time.perf_counter()
        -
        start_time
    )

    processed = len(
        results
    )

    freshly_processed = len(
        fresh_results
    )


    # ========================================================
    # THROUGHPUT
    # ========================================================

    throughput = (

        freshly_processed
        /
        elapsed
        *
        60

        if (
            elapsed > 0
            and
            freshly_processed > 0
        )

        else
        0.0
    )


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()

    print(
        "Processing Complete"
    )

    print(
        "-------------------"
    )

    print(
        f"Uploaded/valid files : {total}"
    )

    print(
        f"Processed results    : {processed}"
    )

    print(
        f"Freshly processed    : {freshly_processed}"
    )

    print(
        f"Cached reused        : {cached}"
    )

    print(
        f"File-level failures  : {len(failures)}"
    )

    print(
        (
            f"Failed/partial items : "
            f"{total_failed_partial_items}"
        )
    )


    print()

    print(
        "Current Run AI Usage"
    )

    print(
        "--------------------"
    )

    print(
        (
            f"Input tokens         : "
            f"{run_input_tokens:,}"
        )
    )

    print(
        (
            f"Output tokens        : "
            f"{run_output_tokens:,}"
        )
    )

    print(
        (
            f"Total tokens         : "
            f"{run_total_tokens:,}"
        )
    )

    print(
        (
            f"API requests         : "
            f"{run_api_requests:,}"
        )
    )

    print(
        (
            f"Actual run cost      : "
            f"${actual_run_cost_usd:.6f}"
        )
    )


    print()

    print(
        "Performance"
    )

    print(
        "-----------"
    )

    print(
        (
            f"Elapsed time         : "
            f"{elapsed:.1f} seconds"
        )
    )

    print(
        (
            f"Elapsed time         : "
            f"{elapsed / 60:.1f} minutes"
        )
    )

    print(
        (
            f"Throughput           : "
            f"{throughput:.1f} files/min"
        )
    )


    # ========================================================
    # RETURN COMPLETE ASSIGNMENT RESULT
    # ========================================================

    return {

        "results":
            results,

        "invalid_files":
            invalid_files,

        "failures":
            failures,


        # ----------------------------------------------------
        # COUNTS
        # ----------------------------------------------------

        "valid_count":
            total,

        "processed_count":
            processed,

        "fresh_count":
            freshly_processed,

        "cached_count":
            cached,

        "failed_partial_items":
            total_failed_partial_items,


        # ----------------------------------------------------
        # MODEL
        # ----------------------------------------------------

        "model_label":
            model_config[
                "label"
            ],

        "model_id":
            model,


        # ----------------------------------------------------
        # PROMPT
        # ----------------------------------------------------

        "prompt_used":
            selected_prompt,

        "prompt_hash":
            selected_prompt_hash,

        "prompt_modified":
            prompt_modified,


        # ----------------------------------------------------
        # CURRENT RUN TOKEN USAGE
        # ----------------------------------------------------

        "run_input_tokens":
            run_input_tokens,

        "run_output_tokens":
            run_output_tokens,

        "run_total_tokens":
            run_total_tokens,

        "run_api_requests":
            run_api_requests,

        "actual_run_cost_usd":
            round(
                actual_run_cost_usd,
                8,
            ),


        # ----------------------------------------------------
        # COMPLETE DATASET USAGE
        # ----------------------------------------------------

        "dataset_input_tokens":
            total_input_tokens,

        "dataset_output_tokens":
            total_output_tokens,

        "dataset_total_tokens":
            total_tokens,

        "dataset_api_requests":
            total_api_requests,

        "dataset_cost_usd":
            round(
                dataset_cost_usd,
                8,
            ),


        # ----------------------------------------------------
        # TIME
        # ----------------------------------------------------

        "elapsed_seconds":
            elapsed,

        "elapsed_minutes":
            (
                elapsed
                /
                60
            ),

        "throughput_files_per_minute":
            throughput,

        "estimated_time":
            time_estimate,


        # ----------------------------------------------------
        # PROCESSING SETTINGS
        # ----------------------------------------------------

        "workers":
            max_workers,

        "batch_size":
            batch_size,
    }

