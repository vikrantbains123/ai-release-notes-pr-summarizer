import json
from datetime import datetime, timezone

import pytest

from ai_release_notes.release_identity import build_release_identity
from ai_release_notes.render import PullRequest
from ai_release_notes.summarizer import SummarizerError, summarize


def _pr(number, title="Some change", body="details", labels=None):
    return PullRequest(
        number=number,
        title=title,
        author="octocat",
        labels=labels or [],
        body=body,
        merged_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )


def _anthropic_response(categorization: dict, input_tokens=100, output_tokens=50):
    response = type("Response", (), {})()
    response.content = [type("Block", (), {"text": json.dumps(categorization)})()]
    response.usage = type("Usage", (), {"input_tokens": input_tokens, "output_tokens": output_tokens})()
    return response


def _header():
    return build_release_identity(release_name="v1.0.0", version="v1.0.0", commit_sha="abc123")


def test_successful_call_returns_categorized_summary_consumable_by_render(mock_anthropic_client):
    prs = [_pr(101, "Add dark mode"), _pr(102, "Bump dependency")]
    mock_anthropic_client.messages.create.return_value = _anthropic_response(
        {"101": "Features", "102": "Internal"}
    )

    summary, input_tokens, output_tokens = summarize(
        pull_requests=prs,
        header=_header(),
        generated_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
        client=mock_anthropic_client,
        sleep_func=lambda seconds: None,
    )

    assert summary.customer_sections["Features"][0].number == 101
    assert summary.internal_section[0].number == 102
    assert input_tokens == 100
    assert output_tokens == 50


def test_pr_not_mentioned_by_model_defaults_to_internal(mock_anthropic_client):
    prs = [_pr(101), _pr(999)]
    mock_anthropic_client.messages.create.return_value = _anthropic_response({"101": "Fixes"})

    summary, _, _ = summarize(
        pull_requests=prs,
        header=_header(),
        generated_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
        client=mock_anthropic_client,
        sleep_func=lambda seconds: None,
    )

    internal_numbers = [pr.number for pr in summary.internal_section]
    assert 999 in internal_numbers


def test_retries_up_to_three_attempts_with_exponential_backoff_then_succeeds(mock_anthropic_client):
    prs = [_pr(101)]
    sleeps = []
    mock_anthropic_client.messages.create.side_effect = [
        Exception("timeout"),
        Exception("timeout"),
        _anthropic_response({"101": "Features"}),
    ]

    summary, input_tokens, output_tokens = summarize(
        pull_requests=prs,
        header=_header(),
        generated_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
        client=mock_anthropic_client,
        sleep_func=lambda seconds: sleeps.append(seconds),
    )

    assert mock_anthropic_client.messages.create.call_count == 3
    assert sleeps == [2, 4]
    assert summary.customer_sections["Features"][0].number == 101


def test_fails_after_three_attempts_with_no_partial_result(mock_anthropic_client):
    prs = [_pr(101)]
    sleeps = []
    mock_anthropic_client.messages.create.side_effect = Exception("still failing")

    with pytest.raises(SummarizerError):
        summarize(
            pull_requests=prs,
            header=_header(),
            generated_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
            client=mock_anthropic_client,
            sleep_func=lambda seconds: sleeps.append(seconds),
        )

    assert mock_anthropic_client.messages.create.call_count == 3
    assert sleeps == [2, 4]
