from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from ai_release_notes.github_client import (
    GitHubClientError,
    PullRequestCapExceededError,
    fetch_merged_prs,
)
from ai_release_notes.window import resolve_window


def _fake_pr(number, merged_at, body="Some body", labels=None):
    return {
        "number": number,
        "title": f"PR {number}",
        "user": {"login": "octocat"},
        "labels": [{"name": label} for label in (labels or [])],
        "body": body,
        "merged_at": merged_at,
    }


def _response(json_data, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    if status_code >= 400:
        response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    else:
        response.raise_for_status.side_effect = None
    return response


def test_fetch_merged_prs_returns_pull_requests_within_the_window(mock_requests):
    window = resolve_window(
        since=datetime(2026, 8, 1, tzinfo=timezone.utc).date(),
        until=datetime(2026, 8, 31, tzinfo=timezone.utc).date(),
    )
    mock_requests.get.return_value = _response(
        [
            _fake_pr(101, "2026-08-15T00:00:00Z", labels=["feature"]),
            _fake_pr(102, "2026-07-01T00:00:00Z"),  # outside window
        ]
    )

    prs = fetch_merged_prs("owner/repo", window, token="ghp_faketoken")

    assert [pr.number for pr in prs] == [101]
    assert prs[0].author == "octocat"
    assert prs[0].labels == ["feature"]


def test_fetch_merged_prs_treats_empty_body_as_valid(mock_requests):
    window = resolve_window(
        since=datetime(2026, 8, 1, tzinfo=timezone.utc).date(),
        until=datetime(2026, 8, 31, tzinfo=timezone.utc).date(),
    )
    mock_requests.get.return_value = _response(
        [_fake_pr(101, "2026-08-15T00:00:00Z", body=None)]
    )

    prs = fetch_merged_prs("owner/repo", window, token="ghp_faketoken")

    assert prs[0].body == ""


def test_fetch_merged_prs_raises_when_cap_exceeded(mock_requests):
    window = resolve_window(
        since=datetime(2026, 8, 1, tzinfo=timezone.utc).date(),
        until=datetime(2026, 8, 31, tzinfo=timezone.utc).date(),
    )
    too_many = [_fake_pr(n, "2026-08-15T00:00:00Z") for n in range(301)]
    mock_requests.get.return_value = _response(too_many)

    with pytest.raises(PullRequestCapExceededError) as exc_info:
        fetch_merged_prs("owner/repo", window, token="ghp_faketoken")

    assert "301" in str(exc_info.value)
    assert "300" in str(exc_info.value)


def test_fetch_merged_prs_scrubs_token_from_error_message(mock_requests):
    window = resolve_window(
        since=datetime(2026, 8, 1, tzinfo=timezone.utc).date(),
        until=datetime(2026, 8, 31, tzinfo=timezone.utc).date(),
    )
    secret_token = "ghp_super_secret_value"
    mock_requests.get.side_effect = Exception(f"401 Unauthorized: Bearer {secret_token} rejected")

    with pytest.raises(GitHubClientError) as exc_info:
        fetch_merged_prs("owner/repo", window, token=secret_token)

    assert secret_token not in str(exc_info.value)
