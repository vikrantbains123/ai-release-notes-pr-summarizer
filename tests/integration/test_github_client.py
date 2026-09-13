from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from ai_release_notes.github_client import (
    GitHubClientError,
    InvalidRefError,
    PullRequestCapExceededError,
    fetch_merged_prs,
    get_default_branch_head_sha,
    resolve_ref,
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


def test_get_default_branch_head_sha_resolves_via_repo_and_branch_lookup(mock_requests):
    mock_requests.get.side_effect = [
        _response({"default_branch": "main"}),
        _response({"sha": "deadbeef"}),
    ]

    sha = get_default_branch_head_sha("owner/repo", token="ghp_faketoken")

    assert sha == "deadbeef"


def test_resolve_ref_returns_sha_and_commit_date(mock_requests):
    mock_requests.get.return_value = _response(
        {
            "sha": "abc123",
            "commit": {"committer": {"date": "2026-08-01T00:00:00Z"}},
        }
    )

    sha, committed_at = resolve_ref("owner/repo", "v1.2.0", token="ghp_faketoken")

    assert sha == "abc123"
    assert committed_at == datetime(2026, 8, 1, tzinfo=timezone.utc)


def test_resolve_ref_raises_invalid_ref_error_for_nonexistent_ref(mock_requests):
    mock_requests.get.return_value = _response({"message": "Not Found"}, status_code=404)

    with pytest.raises(InvalidRefError) as exc_info:
        resolve_ref("owner/repo", "does-not-exist", token="ghp_faketoken")

    assert "does-not-exist" in str(exc_info.value)


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
