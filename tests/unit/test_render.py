from datetime import datetime, timezone

import pytest

from ai_release_notes.release_identity import build_release_identity
from ai_release_notes.render import (
    GeneratedSummary,
    PullRequest,
    ValidationError,
    render_summary,
    validate_no_duplicate_placement,
)


def make_pr(number, title="Some change"):
    return PullRequest(
        number=number,
        title=title,
        author="octocat",
        labels=[],
        body="",
        merged_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )


def make_summary():
    header = build_release_identity(
        release_name="Version 1.3.0",
        version="v1.3.0",
        commit_sha="abc123",
        rc_branch="release/1.3",
    )
    return GeneratedSummary(
        header=header,
        customer_sections={
            "Features": [make_pr(101, "Add dark mode")],
            "Fixes": [make_pr(102, "Fix crash on startup")],
        },
        internal_section=[make_pr(103, "Bump dependency version")],
        generated_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
    )


def test_render_shows_all_four_release_identity_header_fields():
    output = render_summary(make_summary())

    assert "Version 1.3.0" in output
    assert "v1.3.0" in output
    assert "release/1.3" in output
    assert "abc123" in output


def test_render_includes_each_pr_exactly_once():
    output = render_summary(make_summary())

    for number in (101, 102, 103):
        assert output.count(f"#{number}") == 1


def test_render_puts_internal_prs_in_their_own_deemphasized_section():
    output = render_summary(make_summary())

    assert "Other/Internal Changes" in output
    internal_section_index = output.index("Other/Internal Changes")
    internal_pr_index = output.index("#103")
    assert internal_pr_index > internal_section_index


def test_validate_passes_for_disjoint_sections():
    validate_no_duplicate_placement(make_summary())  # should not raise


def test_validate_raises_when_a_pr_appears_in_two_sections():
    summary = make_summary()
    summary.internal_section.append(make_pr(101, "Duplicate placement"))

    with pytest.raises(ValidationError):
        validate_no_duplicate_placement(summary)
