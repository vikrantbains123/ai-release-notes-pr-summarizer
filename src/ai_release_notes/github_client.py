"""GitHub REST API client: fetch merged pull requests (FR-002, FR-017),
resolve a ref to its commit (US2), and release check/create (US3, added
later).
"""
from datetime import datetime
from typing import List, Tuple

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


class InvalidRefError(GitHubClientError):
    """Raised when a --from-ref/--to-ref doesn't exist in the repository
    (spec User Story 2, Acceptance Scenario 2)."""


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


def resolve_ref(repo: str, ref: str, token: str) -> Tuple[str, datetime]:
    """Resolves a ref (branch, tag, or SHA) to its commit SHA and commit
    date, feeding window.py's `refs` kind and the Release Identity header's
    commit SHA when the window is ref-based.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/commits/{ref}"
    try:
        response = requests.get(url, headers=_auth_headers(token))
    except Exception as exc:
        raise GitHubClientError(_scrub_token(str(exc), token)) from exc

    if response.status_code == 404:
        raise InvalidRefError(f"Reference '{ref}' was not found in {repo}")

    try:
        response.raise_for_status()
    except Exception as exc:
        raise GitHubClientError(_scrub_token(str(exc), token)) from exc

    data = response.json()
    sha = data["sha"]
    committed_at = datetime.fromisoformat(
        data["commit"]["committer"]["date"].replace("Z", "+00:00")
    )
    return sha, committed_at


def get_default_branch_head_sha(repo: str, token: str) -> str:
    """Resolves the commit SHA the notes are generated from, when the
    window isn't ref-based (FR-011, FR-019) -- the current HEAD of the
    repository's default branch.
    """
    headers = _auth_headers(token)
    try:
        repo_response = requests.get(f"{GITHUB_API_BASE}/repos/{repo}", headers=headers)
        repo_response.raise_for_status()
        default_branch = repo_response.json()["default_branch"]

        branch_response = requests.get(
            f"{GITHUB_API_BASE}/repos/{repo}/commits/{default_branch}", headers=headers
        )
        branch_response.raise_for_status()
        return branch_response.json()["sha"]
    except Exception as exc:
        raise GitHubClientError(_scrub_token(str(exc), token)) from exc
