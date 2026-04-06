import time
from typing import Dict, Any, List
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage) # Mock cost calculation
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        Calculates the cost of a request based on the model and token usage.
        Pricing is based on the model's token cost per 1,000 tokens.
        """
        # Define pricing per 1,000 tokens for different models
        pricing = {
            "gpt-4": 0.03,  # Example pricing for GPT-4
            "gpt-3.5": 0.002,  # Example pricing for GPT-3.5
            "default": 0.01  # Default pricing for unknown models
        }

        # Get the cost per 1,000 tokens for the given model, defaulting to "default" pricing
        cost_per_1000_tokens = pricing.get(model, pricing["default"])

        # Calculate the total cost based on token usage
        total_tokens = usage.get("total_tokens", 0)
        return (total_tokens / 1000) * cost_per_1000_tokens

# Global tracker instance
tracker = PerformanceTracker()
