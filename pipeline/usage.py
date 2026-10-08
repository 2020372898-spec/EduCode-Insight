"""Token-usage aggregation and model cost helpers."""
from __future__ import annotations

from typing import Optional

from .config import calculate_model_cost, get_model_config



def _usage_value(
    usage: Optional[dict],
    *names,
) -> int:
    """
    Safely obtain a token value from Together's usage object.

    Supports alternate field names so the pipeline remains robust
    if the API returns prompt/completion terminology or
    input/output terminology.
    """

    if not usage:
        return 0

    for name in names:

        value = usage.get(
            name
        )

        if value is not None:

            try:
                return int(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

    return 0


def parse_token_usage(
    usage: Optional[dict],
) -> dict:
    """
    Convert Together API usage information into a consistent format.
    """

    input_tokens = _usage_value(
        usage,
        "prompt_tokens",
        "input_tokens",
    )

    output_tokens = _usage_value(
        usage,
        "completion_tokens",
        "output_tokens",
    )

    total_tokens = _usage_value(
        usage,
        "total_tokens",
    )

    if total_tokens == 0:

        total_tokens = (
            input_tokens
            +
            output_tokens
        )

    return {
        "input_tokens":
            input_tokens,

        "output_tokens":
            output_tokens,

        "total_tokens":
            total_tokens,
    }


def empty_usage_summary(
    model: str,
) -> dict:
    """
    Create an empty usage summary for a classification run.
    """

    config = (
        get_model_config(
            model
        )
    )

    return {
        "model_label":
            config[
                "label"
            ],

        "model_id":
            model,

        "input_tokens":
            0,

        "output_tokens":
            0,

        "total_tokens":
            0,

        "estimated_cost_usd":
            0.0,

        "api_requests":
            0,
    }


def add_usage_to_summary(
    summary: dict,
    usage: Optional[dict],
    model: str,
) -> None:
    """
    Add one successful API request's usage to an aggregated summary.
    """

    parsed = (
        parse_token_usage(
            usage
        )
    )

    summary[
        "input_tokens"
    ] += (
        parsed[
            "input_tokens"
        ]
    )

    summary[
        "output_tokens"
    ] += (
        parsed[
            "output_tokens"
        ]
    )

    summary[
        "total_tokens"
    ] += (
        parsed[
            "total_tokens"
        ]
    )

    summary[
        "api_requests"
    ] += 1

    summary[
        "estimated_cost_usd"
    ] = (
        calculate_model_cost(
            model,
            summary[
                "input_tokens"
            ],
            summary[
                "output_tokens"
            ],
        )
    )


