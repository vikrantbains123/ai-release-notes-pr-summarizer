"""Summarization History: tracks which PR numbers have already been
reported for a repository, so a PR is never reported twice across
separate runs, even with overlapping windows (FR-016, SC-008).
"""
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Set

DEFAULT_HISTORY_PATH = Path(".ai-release-notes/history.json")


@dataclass
class SummarizationHistory:
    repo: str
    reported_pr_numbers: Set[int] = field(default_factory=set)
    updated_at: Optional[datetime] = None


def load(repo: str, path: Path = DEFAULT_HISTORY_PATH) -> SummarizationHistory:
    if not path.exists():
        return SummarizationHistory(repo=repo)

    data = json.loads(path.read_text())
    repo_entry = data.get(repo, {})
    updated_at_raw = repo_entry.get("updated_at")
    return SummarizationHistory(
        repo=repo,
        reported_pr_numbers=set(repo_entry.get("reported_pr_numbers", [])),
        updated_at=datetime.fromisoformat(updated_at_raw) if updated_at_raw else None,
    )


def contains(history: SummarizationHistory, pr_number: int) -> bool:
    return pr_number in history.reported_pr_numbers


def record(
    history: SummarizationHistory,
    pr_numbers: Iterable[int],
    path: Path = DEFAULT_HISTORY_PATH,
    now: Optional[datetime] = None,
) -> SummarizationHistory:
    history.reported_pr_numbers.update(pr_numbers)
    history.updated_at = now or datetime.now(timezone.utc)
    _save(history, path)
    return history


def _save(history: SummarizationHistory, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text()) if path.exists() else {}
    data[history.repo] = {
        "reported_pr_numbers": sorted(history.reported_pr_numbers),
        "updated_at": history.updated_at.isoformat() if history.updated_at else None,
    }
    path.write_text(json.dumps(data, indent=2))
