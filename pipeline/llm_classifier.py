"""Together AI classifier service."""
import os
from typing import List, Optional
from .models import RubricItem
from .config import DEFAULT_MODEL, BATCH_SIZE, get_model_config, calculate_model_cost
from .llm_api import classify_items_batched

class LLMClassifier:
    """Own Together AI classification configuration and execution."""
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL, batch_size: int = BATCH_SIZE):
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY")
        self.model = model
        self.batch_size = batch_size

    @property
    def model_config(self) -> dict:
        return get_model_config(self.model)

    def classify(self, items: List[RubricItem], memo_context: Optional[str], specification_context: str,
                 prompt: Optional[str] = None, session=None):
        if not self.api_key:
            raise RuntimeError("TOGETHER_API_KEY is not configured.")
        return classify_items_batched(
            items,
            memo_context=memo_context,
            specification_context=specification_context,
            api_key=self.api_key,
            model=self.model,
            classification_prompt=prompt,
            batch_size=self.batch_size,
            session=session,
        )

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return calculate_model_cost(self.model, input_tokens, output_tokens)

__all__ = ["LLMClassifier"]
