from datetime import datetime, timezone

from ai_release_notes.history import contains, load, record


def test_load_missing_file_returns_empty_history(tmp_path):
    path = tmp_path / "history.json"

    history = load("owner/repo", path=path)

    assert history.repo == "owner/repo"
    assert history.reported_pr_numbers == set()
    assert contains(history, 42) is False


def test_record_then_contains_excludes_already_reported_prs(tmp_path):
    path = tmp_path / "history.json"
    history = load("owner/repo", path=path)

    record(history, [101, 102], path=path, now=datetime(2026, 9, 1, tzinfo=timezone.utc))

    assert contains(history, 101) is True
    assert contains(history, 102) is True
    assert contains(history, 103) is False


def test_record_persists_across_a_fresh_load(tmp_path):
    path = tmp_path / "history.json"
    history = load("owner/repo", path=path)
    record(history, [101], path=path, now=datetime(2026, 9, 1, tzinfo=timezone.utc))

    reloaded = load("owner/repo", path=path)

    assert contains(reloaded, 101) is True


def test_history_is_scoped_per_repository(tmp_path):
    path = tmp_path / "history.json"
    history_a = load("owner/repo-a", path=path)
    record(history_a, [1], path=path, now=datetime(2026, 9, 1, tzinfo=timezone.utc))

    history_b = load("owner/repo-b", path=path)

    assert contains(history_b, 1) is False


def test_record_adds_to_existing_numbers_rather_than_overwriting(tmp_path):
    path = tmp_path / "history.json"
    history = load("owner/repo", path=path)
    record(history, [1], path=path, now=datetime(2026, 9, 1, tzinfo=timezone.utc))

    reloaded = load("owner/repo", path=path)
    record(reloaded, [2], path=path, now=datetime(2026, 9, 2, tzinfo=timezone.utc))

    final = load("owner/repo", path=path)
    assert contains(final, 1) is True
    assert contains(final, 2) is True
