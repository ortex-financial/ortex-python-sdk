"""Tests for ORTEX client."""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import patch

import pytest
import responses
from responses import matchers

from ortex import OrtexClient
from ortex.client import normalize_date, normalize_exchange, normalize_ticker, to_dataframe
from ortex.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


class TestOrtexClientInit:
    """Tests for OrtexClient initialization."""

    def test_init_with_api_key(self, api_key: str) -> None:
        """Test client initialization with explicit API key."""
        client = OrtexClient(api_key=api_key)
        assert client.api_key == api_key

    def test_init_with_env_var(self, api_key: str) -> None:
        """Test client initialization with environment variable."""
        with patch.dict("os.environ", {"ORTEX_API_KEY": api_key}):
            client = OrtexClient()
            assert client.api_key == api_key

    def test_init_without_api_key_raises(self) -> None:
        """Test that initialization without API key raises AuthenticationError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AuthenticationError):
                OrtexClient()

    def test_init_sets_headers(self, api_key: str) -> None:
        """Test that initialization sets correct headers."""
        client = OrtexClient(api_key=api_key)
        assert client._session.headers["Ortex-Api-Key"] == api_key
        assert client._session.headers["Content-Type"] == "application/json"
        assert client._session.headers["Accept"] == "application/json"

    def test_init_custom_timeout(self, api_key: str) -> None:
        """Test client initialization with custom timeout."""
        client = OrtexClient(api_key=api_key, timeout=60)
        assert client.timeout == 60

    def test_init_custom_max_retries(self, api_key: str) -> None:
        """Test client initialization with custom max retries."""
        client = OrtexClient(api_key=api_key, max_retries=10)
        assert client.max_retries == 10


class TestOrtexClientGet:
    """Tests for OrtexClient.get method."""

    @responses.activate
    def test_get_success(self, api_key: str) -> None:
        """Test successful GET request."""
        data = {"value": 123}
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            json=data,
            status=200,
        )

        client = OrtexClient(api_key=api_key)
        result = client.get("test/endpoint")

        assert result == data

    @responses.activate
    def test_get_with_params(self, api_key: str) -> None:
        """Test GET request with query parameters."""
        data = {"value": 123}
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            json=data,
            status=200,
            match=[matchers.query_param_matcher({"from_date": "2024-01-01"})],
        )

        client = OrtexClient(api_key=api_key)
        result = client.get("test/endpoint", params={"from_date": "2024-01-01"})

        assert result == data

    @responses.activate
    def test_get_401_raises_authentication_error(self, api_key: str) -> None:
        """Test that 401 response raises AuthenticationError."""
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            json={"error": "Invalid API key"},
            status=401,
        )

        client = OrtexClient(api_key=api_key)
        with pytest.raises(AuthenticationError):
            client.get("test/endpoint")

    @responses.activate
    def test_get_404_raises_not_found_error(self, api_key: str) -> None:
        """Test that 404 response raises NotFoundError."""
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            json={"error": "Not found"},
            status=404,
        )

        client = OrtexClient(api_key=api_key)
        with pytest.raises(NotFoundError):
            client.get("test/endpoint")

    @responses.activate
    def test_get_400_raises_validation_error(self, api_key: str) -> None:
        """Test that 400 response raises ValidationError."""
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            json={"error": "Invalid parameters"},
            status=400,
        )

        client = OrtexClient(api_key=api_key)
        with pytest.raises(ValidationError):
            client.get("test/endpoint")

    @responses.activate
    def test_get_429_raises_rate_limit_error(self, api_key: str) -> None:
        """Test that 429 response raises RateLimitError."""
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            json={"error": "Rate limit exceeded"},
            status=429,
            headers={"Retry-After": "60"},
        )

        client = OrtexClient(api_key=api_key, max_retries=1)
        with pytest.raises(RateLimitError) as exc_info:
            client.get("test/endpoint")
        assert exc_info.value.retry_after == 60

    @responses.activate
    def test_get_500_raises_server_error(self, api_key: str) -> None:
        """Test that 500 response raises ServerError."""
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            json={"error": "Internal server error"},
            status=500,
        )

        client = OrtexClient(api_key=api_key, max_retries=1)
        with pytest.raises(ServerError):
            client.get("test/endpoint")


class TestOrtexClientContextManager:
    """Tests for OrtexClient context manager."""

    def test_context_manager(self, api_key: str) -> None:
        """Test using client as context manager."""
        with OrtexClient(api_key=api_key) as client:
            assert client.api_key == api_key


class TestNormalizeFunctions:
    """Tests for normalization helper functions."""

    def test_normalize_exchange_uppercase(self) -> None:
        """Test exchange normalization to uppercase."""
        assert normalize_exchange("nyse") == "NYSE"
        assert normalize_exchange("NASDAQ") == "NASDAQ"
        assert normalize_exchange("  xetr  ") == "XETR"

    def test_normalize_ticker_uppercase(self) -> None:
        """Test ticker normalization to uppercase."""
        assert normalize_ticker("aapl") == "AAPL"
        assert normalize_ticker("TSLA") == "TSLA"
        assert normalize_ticker("  amc  ") == "AMC"

    def test_normalize_date_string(self) -> None:
        """Test date normalization from string."""
        assert normalize_date("2024-01-15") == "2024-01-15"
        assert normalize_date("  2024-01-15  ") == "2024-01-15"

    def test_normalize_date_date_object(self) -> None:
        """Test date normalization from date object."""
        assert normalize_date(date(2024, 1, 15)) == "2024-01-15"

    def test_normalize_date_datetime_object(self) -> None:
        """Test date normalization from datetime object."""
        assert normalize_date(datetime(2024, 1, 15, 12, 30)) == "2024-01-15"

    def test_normalize_date_none(self) -> None:
        """Test date normalization returns None for None input."""
        assert normalize_date(None) is None

    def test_normalize_date_invalid_format_raises(self) -> None:
        """Test that invalid date format raises ValidationError."""
        with pytest.raises(ValidationError):
            normalize_date("01-15-2024")

        with pytest.raises(ValidationError):
            normalize_date("2024/01/15")


class TestToDataframe:
    """Tests for to_dataframe function."""

    def test_to_dataframe_list(self) -> None:
        """Test converting list of dicts to DataFrame."""
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        df = to_dataframe(data)
        assert len(df) == 2
        assert list(df.columns) == ["a", "b"]

    def test_to_dataframe_dict(self) -> None:
        """Test converting single dict to DataFrame."""
        data = {"a": 1, "b": 2}
        df = to_dataframe(data)
        assert len(df) == 1
        assert df.iloc[0]["a"] == 1

    def test_to_dataframe_empty_list(self) -> None:
        """Test empty list returns empty DataFrame."""
        df = to_dataframe([])
        assert len(df) == 0
