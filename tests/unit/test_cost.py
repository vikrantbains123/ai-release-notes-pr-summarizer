import json
from datetime import datetime, timezone

import pytest

from ai_release_notes.cost import (
    CostError,
    UsageRecord,
    compute_cost,
    format_cost_for_display,
    record_usage,
)


def test_compute_cost_uses_pricing_table_and_rounds_to_six_decimals():
    cost = compute_cost(model="claude-sonnet-5", input_tokens=1000, output_tokens=500)

    assert isinstance(cost, float)
    assert round(cost, 6) == cost


def test_compute_cost_unknown_model_raises():
    with pytest.raises(CostError):
        compute_cost(model="not-a-real-model", input_tokens=1000, output_tokens=500)


def test_format_cost_for_display_rounds_to_four_decimals():
    assert format_cost_for_display(0.0033335) == "$0.0033"
    assert format_cost_for_display(1.5) == "$1.5000"


def test_record_usage_appends_well_formed_jsonl_line(tmp_path):
    path = tmp_path / "usage_log.jsonl"
    record = UsageRecord(
        timestamp=datetime(2026, 9, 12, tzinfo=timezone.utc),
        repo="owner/repo",
        since="2026-08-01",
        until="2026-08-31",
        model="claude-sonnet-5",
        input_tokens=1200,
        output_tokens=300,
        estimated_cost_usd=compute_cost(model="claude-sonnet-5", input_tokens=1200, output_tokens=300),
    )

    record_usage(record, path=path)

    lines = path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["repo"] == "owner/repo"
    assert entry["model"] == "claude-sonnet-5"
    assert entry["input_tokens"] == 1200
    assert entry["output_tokens"] == 300
    assert "estimated_cost_usd" in entry


def test_record_usage_appends_rather_than_overwriting(tmp_path):
    path = tmp_path / "usage_log.jsonl"
    record = UsageRecord(
        timestamp=datetime(2026, 9, 12, tzinfo=timezone.utc),
        repo="owner/repo",
        since="2026-08-01",
        until="2026-08-31",
        model="claude-sonnet-5",
        input_tokens=100,
        output_tokens=50,
        estimated_cost_usd=0.001,
    )

    record_usage(record, path=path)
    record_usage(record, path=path)

    assert len(path.read_text().strip().splitlines()) == 2


def test_usage_log_never_contains_a_credential_value(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-super-secret-value")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_super_secret_value")
    path = tmp_path / "usage_log.jsonl"
    record = UsageRecord(
        timestamp=datetime(2026, 9, 12, tzinfo=timezone.utc),
        repo="owner/repo",
        since="2026-08-01",
        until="2026-08-31",
        model="claude-sonnet-5",
        input_tokens=100,
        output_tokens=50,
        estimated_cost_usd=0.001,
    )

    record_usage(record, path=path)

    contents = path.read_text()
    assert "sk-ant-super-secret-value" not in contents
    assert "ghp_super_secret_value" not in contents
