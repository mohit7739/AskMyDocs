"""JSONL-based tracer for observability."""

import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

logger = logging.getLogger(__name__)

class JSONLTracer:
    """Appends trace telemetry to a JSON Lines file."""

    def __init__(self, log_path: str = "eval/reports/traces.jsonl"):
        self.log_path = Path(log_path)
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create trace directory: {e}")

    def log_trace(
        self,
        endpoint: str,
        question: str,
        answer: str,
        latency: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0,
        is_error: bool = False,
        error_msg: str = "",
        extra: dict[str, Any] = None,
    ):
        """Log a single request trace to the JSONL file."""
        from datetime import timezone
        trace = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": endpoint,
            "question": question,
            "answer": answer,
            "latency": latency,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost": cost,
            "is_error": is_error,
            "error_msg": error_msg,
        }
        if extra:
            trace.update(extra)

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write trace: {e}")

# Global instance for app-wide use.
# In production on Vercel, use /tmp to allow writes
import os
_trace_path = "/tmp/traces.jsonl" if os.environ.get("VERCEL") else "eval/reports/traces.jsonl"
global_tracer = JSONLTracer(log_path=_trace_path)
