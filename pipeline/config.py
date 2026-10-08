"""Application and Together AI configuration helpers."""
from __future__ import annotations

# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_CONFIGS = {

    "GPT-OSS 120B": {
        "id": "openai/gpt-oss-120b",
        "enabled": True,
        "input_price_per_million": 0.15,
        "output_price_per_million": 0.60,
    },

}


DEFAULT_MODEL_LABEL = "GPT-OSS 120B"

DEFAULT_MODEL = (
    MODEL_CONFIGS[
        DEFAULT_MODEL_LABEL
    ]["id"]
)


# ============================================================
# PROCESSING SETTINGS
# ============================================================

MAX_WORKERS = 3

BATCH_SIZE = 12

MAX_RETRIES = 3

REQUEST_TIMEOUT = 120


# ============================================================
# MODEL HELPERS
# ============================================================

def get_model_config(
    model_id: str,
) -> dict:
    """
    Return the configuration for a supported Together AI model.
    """

    for label, config in MODEL_CONFIGS.items():

        if config["id"] == model_id:

            return {
                "label": label,
                **config,
            }

    raise ValueError(
        f"Unsupported model: {model_id}"
    )


def calculate_model_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Calculate the estimated Together AI cost from token usage.
    """

    config = (
        get_model_config(
            model_id
        )
    )

    input_cost = (
        input_tokens
        / 1_000_000
        *
        config[
            "input_price_per_million"
        ]
    )

    output_cost = (
        output_tokens
        / 1_000_000
        *
        config[
            "output_price_per_million"
        ]
    )

    return (
        input_cost
        +
        output_cost
    )


# ============================================================
# RUN ESTIMATION HELPERS
# ============================================================

def estimate_processing_time(
    number_of_files: int,
    files_per_minute: float = 3.3,
) -> dict:
    """
    Estimate assignment processing time.

    The default 3.3 files/minute is a historical baseline.
    It is only an estimate because actual runtime depends on
    failed-item count, API latency, retries, and rate limits.
    """

    if number_of_files <= 0:

        return {
            "estimated_minutes": 0.0,
            "lower_minutes": 0.0,
            "upper_minutes": 0.0,
        }

    estimated_minutes = (
        number_of_files
        /
        files_per_minute
    )

    return {
        "estimated_minutes":
            round(
                estimated_minutes,
                1,
            ),

        "lower_minutes":
            round(
                estimated_minutes * 0.85,
                1,
            ),

        "upper_minutes":
            round(
                estimated_minutes * 1.20,
                1,
            ),
    }


def estimate_run_cost(
    model_id: str,
    estimated_input_tokens: int,
    estimated_output_tokens: int,
) -> dict:
    """
    Estimate a future run cost from estimated token counts.
    """

    estimated_cost = (
        calculate_model_cost(
            model_id,
            estimated_input_tokens,
            estimated_output_tokens,
        )
    )

    return {
        "estimated_input_tokens":
            estimated_input_tokens,

        "estimated_output_tokens":
            estimated_output_tokens,

        "estimated_total_tokens":
            (
                estimated_input_tokens
                +
                estimated_output_tokens
            ),

        "estimated_cost_usd":
            round(
                estimated_cost,
                6,
            ),
    }


# ============================================================
# AVAILABLE MODEL HELPER
# ============================================================

def get_enabled_models() -> dict:
    """
    Return models currently enabled for use.

    The Streamlit interface no longer needs to present a model
    selector because GPT-OSS 120B is the single validated model.
    """

    return {
        label: config
        for label, config
        in MODEL_CONFIGS.items()
        if config.get(
            "enabled",
            False,
        )
    }


