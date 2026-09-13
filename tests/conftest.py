"""Shared test fixtures. No test in this suite may make a live network call
(constitution Principle I) -- github_client.py's requests calls and
summarizer.py's Anthropic calls are mocked here.
"""
from unittest.mock import MagicMock

import pytest


def make_response(status_code=200, json_data=None, headers=None):
    """Build a fake requests.Response-like object."""
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    response.json.return_value = json_data if json_data is not None else {}
    if status_code >= 400:
        response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    else:
        response.raise_for_status.side_effect = None
    return response


@pytest.fixture
def mock_requests(monkeypatch):
    """Patches requests.get/post so github_client.py never hits the network.

    Tests configure behavior via `mock_requests.get.return_value = ...` (or
    `.side_effect = ...`), using `make_response()` to build fake responses.
    """
    mock_get = MagicMock()
    mock_post = MagicMock()
    monkeypatch.setattr("requests.get", mock_get)
    monkeypatch.setattr("requests.post", mock_post)
    mock_get.return_value = make_response()
    mock_post.return_value = make_response()
    return MagicMock(get=mock_get, post=mock_post)


@pytest.fixture
def mock_anthropic_client(monkeypatch):
    """Patches anthropic.Anthropic so summarizer.py never hits the network.

    Tests configure the response via
    `mock_anthropic_client.messages.create.return_value = ...` (or
    `.side_effect = ...` for failure/retry scenarios).
    """
    client = MagicMock()
    monkeypatch.setattr("anthropic.Anthropic", lambda *args, **kwargs: client)
    return client
