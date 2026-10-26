"""Tests for ORTEX client."""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import patch

import pytest
import responses
from responses import matchers

from ortex import OrtexClient, __version__
from ortex.client import normalize_date, normalize_exchange, normalize_ticker, to_dataframe
from ortex.exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
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

    def test_user_agent_matches_package_version(self, api_key: str) -> None:
        """The User-Agent must track __version__ rather than a hardcoded string."""
        client = OrtexClient(api_key=api_key)
        assert client._session.headers["User-Agent"] == f"ortex-python-sdk/{__version__}"

    def test_init_custom_timeout(self, api_key: str) -> None:
        """Test client initialization with custom timeout."""
        client = OrtexClient(api_key=api_key, timeout=60)
        assert client.timeout == 60

    def test_init_custom_max_retries(self, api_key: str) -> None:
        """Test client initialization with custom max retries."""
        client = OrtexClient(api_key=api_key, max_retries=10)
        assert client.max_retries == 10

    def test_rate_limit_defaults_to_three_per_second(self, api_key: str) -> None:
        """Omitting requests_per_second keeps the 3.0 default."""
        client = OrtexClient(api_key=api_key)
        assert client.throttler.requests_per_second == 3.0

    def test_rate_limit_none_disables_it(self, api_key: str) -> None:
        """Passing requests_per_second=None must disable rate limiting, not restore 3.0."""
        client = OrtexClient(api_key=api_key, requests_per_second=None)
        assert client.throttler.requests_per_second is None


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


class TestOrtexClientErrorBodies:
    """Tests for error-body shapes the message extraction must handle."""

    @responses.activate
    def test_nested_error_object_gives_string_message(self, api_key: str) -> None:
        """A {"error": {"code", "message"}} body yields a readable string, not a dict."""
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            json={
                "error": {
                    "status": 402,
                    "code": "creditsExhausted",
                    "message": "Out of credits",
                }
            },
            status=402,
        )

        client = OrtexClient(api_key=api_key, max_retries=1)
        with pytest.raises(APIError) as exc_info:
            client.get("test/endpoint")
        assert isinstance(exc_info.value.message, str)
        assert exc_info.value.message == "creditsExhausted: Out of credits"
        assert exc_info.value.status_code == 402

    @responses.activate
    def test_list_error_body_does_not_crash(self, api_key: str) -> None:
        """A JSON list body must map to the status exception, not AttributeError."""
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            json=[{"field": "from_date", "problem": "required"}],
            status=400,
        )

        client = OrtexClient(api_key=api_key, max_retries=1)
        with pytest.raises(ValidationError) as exc_info:
            client.get("test/endpoint")
        assert isinstance(exc_info.value.message, str)
        assert "from_date" in exc_info.value.message

    @responses.activate
    def test_non_json_error_body_uses_text(self, api_key: str) -> None:
        """A non-JSON error body falls back to its text."""
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            body="<html><body>Bad Gateway</body></html>",
            status=502,
            content_type="text/html",
        )

        client = OrtexClient(api_key=api_key, max_retries=1)
        with pytest.raises(ServerError) as exc_info:
            client.get("test/endpoint")
        assert "Bad Gateway" in exc_info.value.message

    @responses.activate
    def test_empty_error_body_reports_status(self, api_key: str) -> None:
        """An empty error body still produces a message."""
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            body="",
            status=404,
        )

        client = OrtexClient(api_key=api_key, max_retries=1)
        with pytest.raises(NotFoundError) as exc_info:
            client.get("test/endpoint")
        assert exc_info.value.message == "HTTP 404"

    @responses.activate
    def test_non_json_200_raises_api_error_not_network_error(self, api_key: str) -> None:
        """A 200 with a non-JSON body is an API error, not a connectivity failure."""
        responses.add(
            responses.GET,
            "https://api.ortex.com/api/v1/test/endpoint",
            body="<html>proxy page</html>",
            status=200,
            content_type="text/html",
        )

        client = OrtexClient(api_key=api_key, max_retries=1)
        with pytest.raises(APIError) as exc_info:
            client.get("test/endpoint")
        assert not isinstance(exc_info.value, NetworkError)
        assert exc_info.value.status_code == 200
        assert "text/html" in exc_info.value.message
        assert "proxy page" in exc_info.value.message


class TestOrtexClientPost:
    """Tests for OrtexClient.post method."""

    @responses.activate
    def test_post_success(self, api_key: str) -> None:
        """Test successful POST request."""
        data = {"quality": 69.5, "total": 78.0}
        responses.add(
            responses.POST,
            "https://api.ortex.com/api/v1/test/endpoint",
            json=data,
            status=200,
        )

        client = OrtexClient(api_key=api_key)
        result = client.post("test/endpoint", json={"weights": {"quality": 50}})

        assert result == data

    @responses.activate
    def test_post_with_params(self, api_key: str) -> None:
        """Test POST request with query parameters."""
        data = {"quality": 69.5}
        responses.add(
            responses.POST,
            "https://api.ortex.com/api/v1/test/endpoint",
            json=data,
            status=200,
            match=[matchers.query_param_matcher({"from_date": "2024-01-01"})],
        )

        client = OrtexClient(api_key=api_key)
        result = client.post(
            "test/endpoint",
            params={"from_date": "2024-01-01"},
            json={"weights": {}},
        )

        assert result == data

    @responses.activate
    def test_post_401_raises_authentication_error(self, api_key: str) -> None:
        """Test that 401 response on POST raises AuthenticationError."""
        responses.add(
            responses.POST,
            "https://api.ortex.com/api/v1/test/endpoint",
            json={"error": "Invalid API key"},
            status=401,
        )

        client = OrtexClient(api_key=api_key)
        with pytest.raises(AuthenticationError):
            client.post("test/endpoint", json={})

    @responses.activate
    def test_fetch_post(self, api_key: str) -> None:
        """Test fetch_post returns OrtexResponse."""
        data = {
            "paginationLinks": {"next": None, "previous": None},
            "length": 1,
            "rows": [{"quality": 69.5, "total": 78.0}],
            "creditsUsed": 1.0,
            "creditsLeft": 999.0,
        }
        responses.add(
            responses.POST,
            "https://api.ortex.com/api/v1/test/endpoint",
            json=data,
            status=200,
        )

        client = OrtexClient(api_key=api_key)
        from ortex import OrtexResponse

        response = client.fetch_post("test/endpoint", json={"weights": {}})
        assert isinstance(response, OrtexResponse)


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
