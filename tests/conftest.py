"""Pytest configuration and fixtures for ORTEX SDK tests."""

from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture
def api_key() -> str:
    """Provide a test API key."""
    return "test-api-key-12345"


@pytest.fixture(autouse=True)
def reset_global_client() -> Generator[None, None, None]:
    """Reset global client state between tests."""
    import ortex.api

    original_client = ortex.api._client
    yield
    ortex.api._client = original_client


@pytest.fixture
def mock_env_api_key(api_key: str) -> Generator[None, None, None]:
    """Set API key in environment."""
    with patch.dict(os.environ, {"ORTEX_API_KEY": api_key}):
        yield
