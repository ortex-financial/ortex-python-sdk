"""Custom exceptions for the ORTEX SDK."""

from __future__ import annotations


class APIError(Exception):
    """Base exception for all ORTEX SDK errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize APIError.

        Args:
            message: Error message describing what went wrong.
            status_code: HTTP status code if applicable.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


# Backwards compatibility alias
OrtexError = APIError


class AuthenticationError(APIError):
    """Raised when API key is missing or invalid."""

    def __init__(self, message: str = "Invalid or missing API key") -> None:
        """Initialize AuthenticationError.

        Args:
            message: Error message.
        """
        super().__init__(message, status_code=401)


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        """Initialize RateLimitError.

        Args:
            message: Error message.
            retry_after: Seconds to wait before retrying.
        """
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class NotFoundError(APIError):
    """Raised when requested resource is not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        """Initialize NotFoundError.

        Args:
            message: Error message.
        """
        super().__init__(message, status_code=404)


class ValidationError(APIError):
    """Raised when request parameters are invalid."""

    def __init__(self, message: str = "Invalid request parameters") -> None:
        """Initialize ValidationError.

        Args:
            message: Error message.
        """
        super().__init__(message, status_code=400)


class ServerError(APIError):
    """Raised when ORTEX server encounters an error."""

    def __init__(self, message: str = "Server error") -> None:
        """Initialize ServerError.

        Args:
            message: Error message.
        """
        super().__init__(message, status_code=500)


class TimeoutError(APIError):
    """Raised when request times out."""

    def __init__(self, message: str = "Request timed out") -> None:
        """Initialize TimeoutError.

        Args:
            message: Error message.
        """
        super().__init__(message)


class NetworkError(APIError):
    """Raised when network connection fails."""

    def __init__(self, message: str = "Network connection error") -> None:
        """Initialize NetworkError.

        Args:
            message: Error message.
        """
        super().__init__(message)
