"""Tests for ORTEX exception classes."""

from __future__ import annotations

import pytest

from ortex.exceptions import (
    AuthenticationError,
    NetworkError,
    NotFoundError,
    OrtexError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)


class TestOrtexError:
    """Tests for base OrtexError class."""

    def test_init_with_message(self) -> None:
        """Test OrtexError with message only."""
        error = OrtexError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.status_code is None

    def test_init_with_status_code(self) -> None:
        """Test OrtexError with message and status code."""
        error = OrtexError("Bad request", status_code=400)
        assert str(error) == "[400] Bad request"
        assert error.message == "Bad request"
        assert error.status_code == 400


class TestAuthenticationError:
    """Tests for AuthenticationError class."""

    def test_default_message(self) -> None:
        """Test AuthenticationError with default message."""
        error = AuthenticationError()
        assert "Invalid or missing API key" in str(error)
        assert error.status_code == 401

    def test_custom_message(self) -> None:
        """Test AuthenticationError with custom message."""
        error = AuthenticationError("API key expired")
        assert "API key expired" in str(error)
        assert error.status_code == 401


class TestRateLimitError:
    """Tests for RateLimitError class."""

    def test_default_values(self) -> None:
        """Test RateLimitError with default values."""
        error = RateLimitError()
        assert error.status_code == 429
        assert error.retry_after is None

    def test_with_retry_after(self) -> None:
        """Test RateLimitError with retry_after."""
        error = RateLimitError("Too many requests", retry_after=60)
        assert error.retry_after == 60
        assert error.status_code == 429


class TestNotFoundError:
    """Tests for NotFoundError class."""

    def test_default_message(self) -> None:
        """Test NotFoundError with default message."""
        error = NotFoundError()
        assert "not found" in str(error).lower()
        assert error.status_code == 404

    def test_custom_message(self) -> None:
        """Test NotFoundError with custom message."""
        error = NotFoundError("Ticker INVALID not found")
        assert "INVALID" in str(error)


class TestValidationError:
    """Tests for ValidationError class."""

    def test_default_message(self) -> None:
        """Test ValidationError with default message."""
        error = ValidationError()
        assert error.status_code == 400

    def test_custom_message(self) -> None:
        """Test ValidationError with custom message."""
        error = ValidationError("Invalid date format")
        assert "Invalid date format" in str(error)


class TestServerError:
    """Tests for ServerError class."""

    def test_default_message(self) -> None:
        """Test ServerError with default message."""
        error = ServerError()
        assert error.status_code == 500


class TestTimeoutError:
    """Tests for TimeoutError class."""

    def test_default_message(self) -> None:
        """Test TimeoutError with default message."""
        error = TimeoutError()
        assert "timed out" in str(error).lower()
        assert error.status_code is None


class TestNetworkError:
    """Tests for NetworkError class."""

    def test_default_message(self) -> None:
        """Test NetworkError with default message."""
        error = NetworkError()
        assert "connection" in str(error).lower()
        assert error.status_code is None


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_inherit_from_ortex_error(self) -> None:
        """Test all exceptions inherit from OrtexError."""
        exceptions = [
            AuthenticationError(),
            RateLimitError(),
            NotFoundError(),
            ValidationError(),
            ServerError(),
            TimeoutError(),
            NetworkError(),
        ]
        for exc in exceptions:
            assert isinstance(exc, OrtexError)

    def test_all_inherit_from_exception(self) -> None:
        """Test all exceptions inherit from Exception."""
        exceptions = [
            OrtexError("test"),
            AuthenticationError(),
            RateLimitError(),
            NotFoundError(),
            ValidationError(),
            ServerError(),
            TimeoutError(),
            NetworkError(),
        ]
        for exc in exceptions:
            assert isinstance(exc, Exception)

    def test_can_catch_as_ortex_error(self) -> None:
        """Test all exceptions can be caught as OrtexError."""
        with pytest.raises(OrtexError):
            raise AuthenticationError()

        with pytest.raises(OrtexError):
            raise RateLimitError()

        with pytest.raises(OrtexError):
            raise NotFoundError()
