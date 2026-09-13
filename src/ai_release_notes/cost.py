"""Usage Record: converts Anthropic token usage into an estimated cost and
appends it to logs/cost/runs/usage_log.jsonl (FR-007, Cost Transparency).

Per spec Assumptions, the pricing table below is maintained manually by the
developer -- no automated staleness detection in v1.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from datetime import datetime

DEFAULT_USAGE_LOG_PATH = Path("logs/cost/runs/usage_log.jsonl")

# USD per token, derived from Anthropic's published per-million-token pricing.
PRICING_TABLE = {
    "claude-sonnet-5": {
        "input_per_token": 3.0 / 1_000_000,
        "output_per_token": 15.0 / 1_000_000,
    },
}


class CostError(Exception):
    """Raised when a model has no pricing table entry."""


@dataclass
class UsageRecord:
    timestamp: datetime
    repo: str
    since: str
    until: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING_TABLE.get(model)
    if pricing is None:
        raise CostError(f"No pricing entry for model '{model}'")
    cost = input_tokens * pricing["input_per_token"] + output_tokens * pricing["output_per_token"]
    return round(cost, 6)


def format_cost_for_display(cost: float) -> str:
    return f"${cost:.4f}"


def record_usage(record: UsageRecord, path: Path = DEFAULT_USAGE_LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": record.timestamp.isoformat(),
        "repo": record.repo,
        "since": record.since,
        "until": record.until,
        "model": record.model,
        "input_tokens": record.input_tokens,
        "output_tokens": record.output_tokens,
        "estimated_cost_usd": record.estimated_cost_usd,
    }
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
