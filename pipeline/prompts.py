"""Prompt templates and prompt construction helpers."""
from __future__ import annotations

import hashlib
from typing import List, Optional

from .models import RubricItem

# ============================================================
# DEFAULT CLASSIFICATION PROMPT
# ============================================================

DEFAULT_CLASSIFICATION_PROMPT = """
You are an expert HTML/CSS error-analysis classifier for a
first-year web development module.

The student has already been graded by another assessment system.
You are NOT grading the student.

Your task is to determine WHY each FAILED or PARTIALLY MET rubric
criterion was incorrect.

Use your own expert understanding of these error categories:

- Syntax Error
- Semantic Error
- Best Practice Violation
- Rule-Based Error

For this project, "Rule-Based Error" specifically means that the
student violated an explicit requirement stated in the rubric,
marking memorandum, or assignment specification.

For every item, consider ALL of the following:

1. What the rubric criterion required.
2. The marker's explanation of what the student did wrong.
3. The relevant marking memorandum.
4. The relevant assignment specification.

Compare what was required against what the student actually did,
then select the SINGLE category that best describes the underlying
cause of the error.

Important instructions:

- Do NOT re-grade the student.
- Do NOT decide whether the marker was correct or incorrect.
- Use the marker's reason as evidence of what the student did wrong.
- Use the memo and specification to understand what was officially required.
- Do NOT classify based only on individual keywords.
- Consider the meaning of the full error.
- A Rule-Based Error concerns failure to follow an explicit
  assignment requirement.
- A Best Practice Violation concerns accepted HTML/CSS practice
  rather than a specific assignment instruction.

Return ONLY a valid JSON array.

Each object must contain exactly:

{
  "id": <integer>,
  "category": "<Syntax Error | Semantic Error | Best Practice Violation | Rule-Based Error>",
  "justification": "<brief explanation of why this category applies>"
}

Return exactly one object for every supplied ID.

Return the objects in the same order as the supplied IDs.

Do not include markdown.
Do not include ```json.
Do not include any text before or after the JSON array.
"""


# Backward-compatible name if other notebook cells still use it.
SYSTEM_PROMPT_BATCH = DEFAULT_CLASSIFICATION_PROMPT


# ============================================================
# PROMPT HELPERS
# ============================================================

def normalise_classification_prompt(
    prompt: Optional[str] = None,
) -> str:
    """
    Return the lecturer-selected prompt.

    If no custom prompt is supplied, the default EduCodeInsight
    classification prompt is used.
    """

    if prompt is None:
        return DEFAULT_CLASSIFICATION_PROMPT.strip()

    cleaned = str(
        prompt
    ).strip()

    if not cleaned:
        return DEFAULT_CLASSIFICATION_PROMPT.strip()

    return cleaned


def classification_prompt_hash(
    prompt: str,
) -> str:
    """
    Generate a SHA-256 hash for the exact classification prompt used.
    """

    return hashlib.sha256(
        prompt.encode(
            "utf-8"
        )
    ).hexdigest()



# ============================================================
# BUILD USER PROMPT FOR A BATCH
# ============================================================

def _build_batch_prompt(
    items: List[RubricItem],
    memo_context: Optional[str],
    specification_context: Optional[str],
) -> str:
    """
    Build the assignment-specific user message sent with the
    lecturer-approved classification prompt.
    """

    item_blocks = []

    for index, item in enumerate(
        items
    ):

        item_blocks.append(
            f"""
================ ITEM {index} ================

ID:
{index}

QUESTION:
{item.question_title}

RUBRIC STATUS:
{item.status}

WHAT THE RUBRIC REQUIRED:
{item.text}

WHY THE STUDENT LOST MARKS:
{item.reason or "No marker reason was provided."}

================================================
""".strip()
        )

    memo_text = (
        memo_context[:5000]
        if memo_context
        else
        "No relevant memorandum section was available."
    )

    specification_text = (
        specification_context[:4000]
        if specification_context
        else
        "No relevant assignment specification excerpt was available."
    )

    official_context = f"""

================ OFFICIAL ASSESSMENT CONTEXT ================

RELEVANT MARKING MEMORANDUM:

{memo_text}


RELEVANT ASSIGNMENT SPECIFICATION:

{specification_text}

===============================================================

CLASSIFICATION TASK:

For every rubric item above:

1. Read what the rubric required.
2. Read why the marker says the student lost marks.
3. Compare this with the memorandum.
4. Compare this with the assignment specification.
5. Determine the underlying type of error.
6. Return exactly one classification for every ID.

Remember:
You are classifying WHY the student made the error.
You are not grading the student again.
"""

    return (
        "\n\n".join(
            item_blocks
        )
        +
        official_context
    )

