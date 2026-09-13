import pytest

from ai_release_notes.config import (
    CredentialError,
    load_config,
    missing_credential_error,
    rejected_credential_error,
)


def test_load_config_succeeds_when_both_present(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_faketoken")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-faketoken")

    config = load_config()

    assert config.github_token == "ghp_faketoken"
    assert config.anthropic_api_key == "sk-ant-faketoken"


def test_load_config_raises_when_github_token_missing(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-faketoken")

    with pytest.raises(CredentialError) as exc_info:
        load_config()

    assert "GITHUB_TOKEN" in str(exc_info.value)
    assert "not set" in str(exc_info.value)


def test_load_config_raises_when_anthropic_key_missing(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_faketoken")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(CredentialError) as exc_info:
        load_config()

    assert "ANTHROPIC_API_KEY" in str(exc_info.value)
    assert "not set" in str(exc_info.value)


def test_load_config_never_includes_raw_value_in_error(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-super-secret-value")

    with pytest.raises(CredentialError) as exc_info:
        load_config()

    assert "sk-ant-super-secret-value" not in str(exc_info.value)


def test_missing_credential_error_wording():
    err = missing_credential_error("GITHUB_TOKEN")
    assert str(err) == "GITHUB_TOKEN is not set"


def test_rejected_credential_error_wording():
    err = rejected_credential_error("GITHUB_TOKEN", "GitHub")
    assert str(err) == "GITHUB_TOKEN was rejected by GitHub"
    # Distinct wording from the missing case -- "rejected", not "not set".
    assert "not set" not in str(err)
