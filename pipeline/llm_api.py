"""Together AI request/response handling for rubric classification."""
from __future__ import annotations

import json
import os
import re
import time
from typing import List, Optional, Tuple

import requests
from pydantic import ValidationError

from .config import BATCH_SIZE, DEFAULT_MODEL, MAX_RETRIES, REQUEST_TIMEOUT
from .models import ClassificationResult, RubricItem
from .prompts import (
    DEFAULT_CLASSIFICATION_PROMPT,
    _build_batch_prompt,
    classification_prompt_hash,
    normalise_classification_prompt,
)
from .usage import add_usage_to_summary, empty_usage_summary

# ============================================================
# EXTRACT JSON ARRAY FROM LLM RESPONSE
# ============================================================

def _extract_json_array(
    text: str,
):
    """
    Extract and parse a JSON array returned by the LLM.
    """

    if (
        not text
        or
        not text.strip()
    ):

        raise ValueError(
            "LLM returned an empty response."
        )

    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )

    try:

        data = json.loads(
            cleaned
        )

    except json.JSONDecodeError:

        start = (
            cleaned.find(
                "["
            )
        )

        end = (
            cleaned.rfind(
                "]"
            )
        )

        if (
            start < 0
            or
            end <= start
        ):

            raise ValueError(
                "Could not find a valid JSON array "
                "in the LLM response. "
                f"Response preview: {cleaned[:500]}"
            )

        data = json.loads(
            cleaned[
                start:end + 1
            ]
        )

    if not isinstance(
        data,
        list,
    ):

        raise ValueError(
            "LLM response was valid JSON "
            "but was not a JSON array."
        )

    return data



# ============================================================
# CLASSIFY RUBRIC ITEMS USING TOGETHER AI
# ============================================================

def classify_items_batched(
    items: List[RubricItem],
    memo_context: Optional[str] = None,
    specification_context: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    classification_prompt: Optional[str] = None,
    batch_size: int = BATCH_SIZE,
    max_retries: int = MAX_RETRIES,
    timeout: int = REQUEST_TIMEOUT,
    session: Optional[requests.Session] = None,
) -> Tuple[
    List[ClassificationResult],
    dict,
]:
    """
    Classify failed/partially met rubric items using Together AI.

    Returns:
        (
            classifications,
            usage_summary
        )

    usage_summary contains:
        - model label
        - model id
        - input tokens
        - output tokens
        - total tokens
        - estimated USD cost
        - successful API request count

    The lecturer may supply a custom classification prompt.
    If none is supplied, DEFAULT_CLASSIFICATION_PROMPT is used.

    No heuristic or mock fallback classifier is used.
    """

    selected_prompt = (
        normalise_classification_prompt(
            classification_prompt
        )
    )

    usage_summary = (
        empty_usage_summary(
            model
        )
    )

    usage_summary[
        "prompt_hash"
    ] = (
        classification_prompt_hash(
            selected_prompt
        )
    )

    usage_summary[
        "prompt_modified"
    ] = (
        selected_prompt
        !=
        DEFAULT_CLASSIFICATION_PROMPT.strip()
    )

    if not items:

        return (
            [],
            usage_summary,
        )

    # --------------------------------------------------------
    # API KEY
    # --------------------------------------------------------

    api_key = (
        api_key
        or
        os.environ.get(
            "TOGETHER_API_KEY"
        )
    )

    if not api_key:

        raise RuntimeError(
            "TOGETHER_API_KEY is not available. "
            "LLM classification cannot continue."
        )

    # --------------------------------------------------------
    # SESSION
    # --------------------------------------------------------

    own_session = (
        session is None
    )

    if session is None:

        session = (
            requests.Session()
        )

    all_results: List[
        ClassificationResult
    ] = []

    try:

        # ----------------------------------------------------
        # PROCESS ITEMS IN BATCHES
        # ----------------------------------------------------

        for start in range(
            0,
            len(items),
            batch_size,
        ):

            batch = items[
                start:
                start + batch_size
            ]

            headers = {
                "Authorization":
                    f"Bearer {api_key}",

                "Content-Type":
                    "application/json",
            }

            user_prompt = (
                _build_batch_prompt(
                    batch,
                    memo_context,
                    specification_context,
                )
            )

            payload = {

                "model":
                    model,

                "messages": [

                    {
                        "role":
                            "system",

                        "content":
                            selected_prompt,
                    },

                    {
                        "role":
                            "user",

                        "content":
                            user_prompt,
                    },

                ],

                "reasoning_effort":
                    "medium",

                "temperature":
                    1.0,

                "max_tokens":
                    12000,
            }

            last_error = None
            batch_results = None
            successful_usage = None

            # ------------------------------------------------
            # RETRIES
            # ------------------------------------------------

            for attempt in range(
                1,
                max_retries + 1,
            ):

                try:

                    response = (
                        session.post(
                            "https://api.together.xyz/v1/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=timeout,
                        )
                    )

                    if (
                        response.status_code
                        !=
                        200
                    ):

                        print()

                        print(
                            f"Together API attempt "
                            f"{attempt}/{max_retries} failed."
                        )

                        print(
                            "HTTP status:",
                            response.status_code,
                        )

                        print(
                            "API response:",
                            response.text[:1500],
                        )

                    response.raise_for_status()

                    response_json = (
                        response.json()
                    )

                    choices = (
                        response_json.get(
                            "choices",
                            [],
                        )
                    )

                    if not choices:

                        raise ValueError(
                            "Together API returned no choices."
                        )

                    choice = (
                        choices[0]
                    )

                    finish_reason = (
                        choice.get(
                            "finish_reason"
                        )
                    )

                    usage = (
                        response_json.get(
                            "usage",
                            {},
                        )
                    )

                    if finish_reason:

                        print(
                            "LLM finish reason:",
                            finish_reason,
                        )

                    if usage:

                        print(
                            "Token usage:",
                            usage,
                        )

                    message = (
                        choice.get(
                            "message",
                            {},
                        )
                    )

                    reply = (
                        message
                        .get(
                            "content",
                            "",
                        )
                        .strip()
                    )

                    if not reply:

                        reasoning = (
                            message.get(
                                "reasoning",
                                "",
                            )
                            or
                            ""
                        )

                        print(
                            "LLM returned empty content."
                        )

                        print(
                            "Finish reason:",
                            finish_reason,
                        )

                        print(
                            "Reasoning characters:",
                            len(
                                reasoning
                            ),
                        )

                        print(
                            "Usage:",
                            usage,
                        )

                        raise ValueError(
                            "LLM returned an empty message."
                        )

                    if (
                        finish_reason
                        ==
                        "length"
                    ):

                        raise ValueError(
                            "LLM response was cut off because "
                            "the output token limit was reached."
                        )

                    # ----------------------------------------
                    # PARSE RESULT
                    # ----------------------------------------

                    data = (
                        _extract_json_array(
                            reply
                        )
                    )

                    by_id = {}

                    for record in data:

                        if not isinstance(
                            record,
                            dict,
                        ):

                            raise ValueError(
                                "Every LLM classification "
                                "must be a JSON object."
                            )

                        for required_field in [
                            "id",
                            "category",
                            "justification",
                        ]:

                            if (
                                required_field
                                not in
                                record
                            ):

                                raise ValueError(
                                    "Classification result "
                                    f"is missing "
                                    f"'{required_field}'."
                                )

                        idx = int(
                            record[
                                "id"
                            ]
                        )

                        if (
                            idx < 0
                            or
                            idx >= len(
                                batch
                            )
                        ):

                            raise ValueError(
                                f"LLM returned invalid "
                                f"item id {idx}."
                            )

                        result = (
                            ClassificationResult(
                                category=
                                    record[
                                        "category"
                                    ],

                                justification=
                                    str(
                                        record[
                                            "justification"
                                        ]
                                    ).strip(),

                                source=
                                    "llm",
                            )
                        )

                        by_id[
                            idx
                        ] = result

                    if (
                        len(
                            by_id
                        )
                        !=
                        len(
                            batch
                        )
                    ):

                        raise ValueError(
                            f"Expected {len(batch)} "
                            f"classifications but received "
                            f"{len(by_id)}."
                        )

                    missing_ids = [

                        i

                        for i in range(
                            len(
                                batch
                            )
                        )

                        if i
                        not in
                        by_id

                    ]

                    if missing_ids:

                        raise ValueError(
                            "LLM response is missing "
                            f"IDs: {missing_ids}"
                        )

                    batch_results = [

                        by_id[
                            i
                        ]

                        for i in range(
                            len(
                                batch
                            )
                        )

                    ]

                    successful_usage = (
                        usage
                    )

                    break

                # --------------------------------------------
                # HTTP ERROR
                # --------------------------------------------

                except requests.HTTPError as exc:

                    status_code = (
                        exc.response.status_code
                        if exc.response
                        is not None
                        else
                        "unknown"
                    )

                    response_body = ""

                    if (
                        exc.response
                        is not None
                    ):

                        try:

                            response_body = (
                                exc.response.text[
                                    :1500
                                ]
                            )

                        except Exception:

                            pass

                    last_error = (
                        RuntimeError(
                            f"Together API HTTP "
                            f"{status_code}: "
                            f"{response_body}"
                        )
                    )

                    if (
                        attempt
                        <
                        max_retries
                    ):

                        if (
                            status_code
                            ==
                            429
                        ):

                            wait_seconds = (
                                5
                                *
                                attempt
                            )

                        else:

                            wait_seconds = min(
                                2 ** (
                                    attempt - 1
                                ),
                                4,
                            )

                        print(
                            f"Retrying in "
                            f"{wait_seconds} seconds..."
                        )

                        time.sleep(
                            wait_seconds
                        )

                # --------------------------------------------
                # NETWORK ERROR
                # --------------------------------------------

                except requests.RequestException as exc:

                    last_error = (
                        exc
                    )

                    print(
                        f"Network/API error on attempt "
                        f"{attempt}/{max_retries}: "
                        f"{type(exc).__name__}: {exc}"
                    )

                    if (
                        attempt
                        <
                        max_retries
                    ):

                        wait_seconds = min(
                            2 ** (
                                attempt - 1
                            ),
                            4,
                        )

                        print(
                            f"Retrying in "
                            f"{wait_seconds} seconds..."
                        )

                        time.sleep(
                            wait_seconds
                        )

                # --------------------------------------------
                # RESPONSE / VALIDATION ERROR
                # --------------------------------------------

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                    json.JSONDecodeError,
                    ValidationError,
                ) as exc:

                    last_error = (
                        exc
                    )

                    print(
                        f"LLM response error on attempt "
                        f"{attempt}/{max_retries}: "
                        f"{type(exc).__name__}: {exc}"
                    )

                    if (
                        attempt
                        <
                        max_retries
                    ):

                        wait_seconds = min(
                            2 ** (
                                attempt - 1
                            ),
                            4,
                        )

                        print(
                            f"Retrying in "
                            f"{wait_seconds} seconds..."
                        )

                        time.sleep(
                            wait_seconds
                        )

            # ------------------------------------------------
            # NO FALLBACK CLASSIFIER
            # ------------------------------------------------

            if (
                batch_results
                is None
            ):

                raise RuntimeError(
                    f"LLM classification failed "
                    f"after {max_retries} attempts. "
                    f"Last error: {last_error}"
                )

            all_results.extend(
                batch_results
            )

            # Only successful requests are billed into our
            # stored usage summary here.
            add_usage_to_summary(
                usage_summary,
                successful_usage,
                model,
            )

    finally:

        if own_session:

            session.close()

    usage_summary[
        "estimated_cost_usd"
    ] = round(
        usage_summary[
            "estimated_cost_usd"
        ],
        8,
    )

    return (
        all_results,
        usage_summary,
    )
