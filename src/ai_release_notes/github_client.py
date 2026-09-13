"""GitHub REST API client: fetch merged pull requests (FR-002, FR-017).

Ref resolution (US2) and release check/create (US3) are added to this
module later; only the PR-fetch path is Foundational.
"""
from datetime import datetime
from typing import List

import requests

from ai_release_notes.render import PullRequest
from ai_release_notes.window import TimeWindow

GITHUB_API_BASE = "https://api.github.com"
MAX_PULL_REQUESTS = 300


class GitHubClientError(Exception):
    """Raised for a GitHub API failure, with any credential value scrubbed
    from the message (FR-009)."""


class PullRequestCapExceededError(GitHubClientError):
    """Raised when a window resolves to more pull requests than
    MAX_PULL_REQUESTS (FR-017)."""


def _auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }


def _scrub_token(message: str, token: str) -> str:
    if token and token in message:
        return message.replace(token, "***")
    return message


def _parse_merged_at(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def fetch_merged_prs(repo: str, window: TimeWindow, token: str) -> List[PullRequest]:
    url = f"{GITHUB_API_BASE}/repos/{repo}/pulls"
    params = {"state": "closed", "sort": "updated", "direction": "desc", "per_page": 100}

    try:
        response = requests.get(url, headers=_auth_headers(token), params=params)
        response.raise_for_status()
    except Exception as exc:
        raise GitHubClientError(_scrub_token(str(exc), token)) from exc

    matched: List[PullRequest] = []
    for raw in response.json():
        merged_at_raw = raw.get("merged_at")
        if not merged_at_raw:
            continue  # not a merged PR
        merged_at = _parse_merged_at(merged_at_raw)
        if not (window.resolved_start <= merged_at <= window.resolved_end):
            continue
        matched.append(
            PullRequest(
                number=raw["number"],
                title=raw["title"],
                author=raw["user"]["login"],
                labels=[label["name"] for label in raw.get("labels", [])],
                body=raw.get("body") or "",
                merged_at=merged_at,
                linked_issues=[],
            )
        )

    if len(matched) > MAX_PULL_REQUESTS:
        raise PullRequestCapExceededError(
            f"Found {len(matched)} pull requests, which exceeds the "
            f"{MAX_PULL_REQUESTS} supported per window"
        )

    return matched
