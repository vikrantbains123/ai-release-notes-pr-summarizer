import json
from pathlib import Path

from ai_release_notes import cli


def _pr_json(number, merged_at, title="Some change", body="details"):
    return {
        "number": number,
        "title": title,
        "user": {"login": "octocat"},
        "labels": [],
        "body": body,
        "merged_at": merged_at,
    }


def _repo_response(json_data):
    from unittest.mock import MagicMock

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = json_data
    response.raise_for_status.side_effect = None
    return response


def _anthropic_response(categorization):
    response = type("Response", (), {})()
    response.content = [type("Block", (), {"text": json.dumps(categorization)})()]
    response.usage = type("Usage", (), {"input_tokens": 500, "output_tokens": 200})()
    return response


def _set_credentials(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_faketoken")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-faketoken")


def test_successful_run_writes_output_file_and_prints_cost_summary(
    tmp_path, monkeypatch, capsys, mock_requests, mock_anthropic_client
):
    monkeypatch.chdir(tmp_path)
    _set_credentials(monkeypatch)
    mock_requests.get.side_effect = [
        _repo_response([_pr_json(101, "2026-08-15T00:00:00Z")]),
        _repo_response({"default_branch": "main"}),
        _repo_response({"sha": "deadbeef"}),
    ]
    mock_anthropic_client.messages.create.return_value = _anthropic_response({"101": "Features"})

    exit_code = cli.main(
        ["--repo", "owner/repo", "--since", "2026-08-01", "--until", "2026-08-31"]
    )

    assert exit_code == 0
    output_path = tmp_path / "RELEASE_NOTES.md"
    assert output_path.exists()
    content = output_path.read_text()
    assert "Some change" in content
    assert "#101" in content
    assert "deadbeef" in content

    captured = capsys.readouterr()
    assert "$" in captured.out  # cost summary printed


def test_window_with_zero_prs_exits_zero_with_no_misleading_file(
    tmp_path, monkeypatch, capsys, mock_requests, mock_anthropic_client
):
    monkeypatch.chdir(tmp_path)
    _set_credentials(monkeypatch)
    mock_requests.get.return_value = _repo_response([])

    exit_code = cli.main(
        ["--repo", "owner/repo", "--since", "2026-08-01", "--until", "2026-08-31"]
    )

    assert exit_code == 0
    assert not (tmp_path / "RELEASE_NOTES.md").exists()
    captured = capsys.readouterr()
    assert "No pull requests found" in captured.out
    # No AI call should have been made when there's nothing to summarize.
    mock_anthropic_client.messages.create.assert_not_called()


def test_missing_credentials_exits_one_with_clear_stderr_message(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    exit_code = cli.main(
        ["--repo", "owner/repo", "--since", "2026-08-01", "--until", "2026-08-31"]
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "GITHUB_TOKEN" in captured.err
    assert "not set" in captured.err
