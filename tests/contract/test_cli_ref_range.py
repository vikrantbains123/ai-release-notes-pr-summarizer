import json
from unittest.mock import MagicMock

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


def _response(json_data, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.raise_for_status.side_effect = None if status_code < 400 else Exception(f"HTTP {status_code}")
    return response


def _anthropic_response(categorization):
    response = type("Response", (), {})()
    response.content = [type("Block", (), {"text": json.dumps(categorization)})()]
    response.usage = type("Usage", (), {"input_tokens": 500, "output_tokens": 200})()
    return response


def _set_credentials(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_faketoken")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-faketoken")


def _ref_commit_response(sha, date):
    return _response({"sha": sha, "commit": {"committer": {"date": date}}})


def test_ref_pair_produces_same_output_shape_as_date_range(
    tmp_path, monkeypatch, mock_requests, mock_anthropic_client
):
    monkeypatch.chdir(tmp_path)
    _set_credentials(monkeypatch)
    mock_requests.get.side_effect = [
        _ref_commit_response("fromsha", "2026-07-01T00:00:00Z"),
        _ref_commit_response("tosha", "2026-08-01T00:00:00Z"),
        _response([_pr_json(101, "2026-07-15T00:00:00Z")]),
    ]
    mock_anthropic_client.messages.create.return_value = _anthropic_response({"101": "Features"})

    exit_code = cli.main(["--repo", "owner/repo", "--from-ref", "v1.2.0", "--to-ref", "v1.3.0"])

    assert exit_code == 0
    content = (tmp_path / "RELEASE_NOTES.md").read_text()
    assert "#101" in content
    assert "tosha" in content  # header commit SHA is the --to-ref's own commit


def test_both_date_and_ref_options_together_is_usage_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _set_credentials(monkeypatch)

    exit_code = cli.main(
        [
            "--repo", "owner/repo",
            "--since", "2026-08-01", "--until", "2026-08-31",
            "--from-ref", "v1.2.0", "--to-ref", "v1.3.0",
        ]
    )

    assert exit_code == 2
    assert "Cannot combine" in capsys.readouterr().err


def test_only_from_ref_without_to_ref_is_usage_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _set_credentials(monkeypatch)

    exit_code = cli.main(["--repo", "owner/repo", "--from-ref", "v1.2.0"])

    assert exit_code == 2


def test_invalid_ref_produces_clear_error(tmp_path, monkeypatch, capsys, mock_requests):
    monkeypatch.chdir(tmp_path)
    _set_credentials(monkeypatch)
    mock_requests.get.return_value = _response({"message": "Not Found"}, status_code=404)

    exit_code = cli.main(["--repo", "owner/repo", "--from-ref", "no-such-ref", "--to-ref", "v1.3.0"])

    assert exit_code == 1
    assert "no-such-ref" in capsys.readouterr().err
