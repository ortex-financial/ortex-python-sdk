"""Core HTTP client for ORTEX API with rate limiting and retry logic."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .response import OrtexResponse
from urllib.parse import urljoin

import pandas as pd
import requests
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import (
    APIError,
    AuthenticationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .throttler import RequestThrottler

logger = logging.getLogger("ortex")


class OrtexClient:
    """HTTP client for ORTEX API with built-in retry and rate limit handling.

    This client handles all HTTP communication with the ORTEX API, including:
    - Authentication via API key
    - Automatic retry with exponential backoff on rate limits and timeouts
    - Request timeout handling
    - Response parsing and error handling
    - Local request throttling to prevent overwhelming the API

    Example:
        >>> client = OrtexClient(api_key="your-api-key")
        >>> data = client.get("NYSE/F/short_interest")

        >>> # With throttling for concurrent usage
        >>> client = OrtexClient(
        ...     api_key="your-api-key",
        ...     max_concurrent_requests=10,
        ...     requests_per_second=5.0,
        ... )
    """

    BASE_URL = "https://api.ortex.com/api/v1/"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 5
    MIN_RETRY_WAIT = 1
    MAX_RETRY_WAIT = 60
    DEFAULT_MAX_CONCURRENT = 2
    DEFAULT_REQUESTS_PER_SECOND: float | None = 3.0

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        max_concurrent_requests: int | None = None,
        requests_per_second: float | None = None,
    ) -> None:
        """Initialize the ORTEX API client.

        Args:
            api_key: Your ORTEX API key. If not provided, will look for
                ORTEX_API_KEY environment variable.
            timeout: Request timeout in seconds. Defaults to 30.
            max_retries: Maximum number of retry attempts for rate-limited
                or timed-out requests. Defaults to 5.
            max_concurrent_requests: Maximum number of concurrent requests
                allowed. Defaults to 10. Set to 0 to disable throttling.
                This is useful when using the client from multiple threads.
            requests_per_second: Maximum requests per second (rate limit).
                Defaults to None (no rate limit). When set, requests are
                spaced to maintain this rate across all threads.

        Raises:
            AuthenticationError: If no API key is provided or found in environment.

        Example:
            >>> # Using explicit API key
            >>> client = OrtexClient(api_key="your-api-key")
            >>>
            >>> # Using environment variable
            >>> import os
            >>> os.environ["ORTEX_API_KEY"] = "your-api-key"
            >>> client = OrtexClient()
            >>>
            >>> # With throttling for multi-threaded usage
            >>> client = OrtexClient(
            ...     api_key="your-api-key",
            ...     max_concurrent_requests=10,  # Max 10 concurrent requests
            ...     requests_per_second=5.0,     # Max 5 requests per second
            ... )
        """
        self.api_key = api_key or os.environ.get("ORTEX_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Pass api_key parameter or set ORTEX_API_KEY "
                "environment variable. "
                "Get your API key at https://app.ortex.com/apis"
            )

        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize throttler for concurrent request limiting
        effective_max_concurrent = (
            max_concurrent_requests
            if max_concurrent_requests is not None
            else self.DEFAULT_MAX_CONCURRENT
        )
        effective_requests_per_second = (
            requests_per_second
            if requests_per_second is not None
            else self.DEFAULT_REQUESTS_PER_SECOND
        )
        self._throttler = RequestThrottler(
            max_concurrent=effective_max_concurrent,
            requests_per_second=effective_requests_per_second,
        )

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Ortex-Api-Key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ortex-python-sdk/1.0.4",
            }
        )

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint.

        Args:
            endpoint: API endpoint path.

        Returns:
            Full URL for the API request.
        """
        # Remove leading slash if present for proper joining
        endpoint = endpoint.lstrip("/")
        return urljoin(self.BASE_URL, endpoint)

    def _handle_response(self, response: requests.Response) -> Any:
        """Handle API response and raise appropriate exceptions.

        Args:
            response: Response from the API.

        Returns:
            Parsed JSON response data.

        Raises:
            AuthenticationError: If authentication fails (401).
            RateLimitError: If rate limit exceeded (429).
            NotFoundError: If resource not found (404).
            ValidationError: If request validation fails (400).
            ServerError: If server error occurs (5xx).
            OrtexError: For other HTTP errors.
        """
        if response.status_code == 200:
            return response.json()

        # Extract error message from response if available
        try:
            error_data = response.json()
            message = error_data.get("message", error_data.get("error", response.text))
        except (ValueError, KeyError):
            message = response.text or f"HTTP {response.status_code}"

        status = response.status_code
        if status == 401:
            raise AuthenticationError(message)
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif status == 404:
            raise NotFoundError(message)
        elif status == 400:
            raise ValidationError(message)
        elif 500 <= status < 600:
            raise ServerError(message)
        else:
            raise APIError(message, status_code=response.status_code)

    @property
    def throttler(self) -> RequestThrottler:
        """Get the request throttler for this client.

        Returns:
            The RequestThrottler instance used by this client.

        Example:
            >>> client = OrtexClient(api_key="your-key")
            >>> stats = client.throttler.stats
            >>> print(f"Total requests: {stats['total_requests']}")
        """
        return self._throttler

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make a GET request to the ORTEX API with automatic retry.

        This method includes automatic retry with exponential backoff for
        rate-limited requests (429), transient server errors (5xx), and
        timeouts. Requests are also throttled to prevent overwhelming the API.

        Args:
            endpoint: API endpoint path (e.g., "NYSE/F/short_interest").
            params: Optional query parameters.

        Returns:
            Parsed JSON response data.

        Raises:
            AuthenticationError: If authentication fails.
            RateLimitError: If rate limit exceeded after all retries.
            NotFoundError: If resource not found.
            ValidationError: If request validation fails.
            ServerError: If server error after all retries.
            NetworkError: If network connection fails.
            TimeoutError: If request times out after all retries.

        Example:
            >>> client = OrtexClient(api_key="your-key")
            >>> data = client.get("NYSE/F/short_interest")
        """

        @retry(
            retry=retry_if_exception_type((RateLimitError, ServerError, TimeoutError)),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=1,
                min=self.MIN_RETRY_WAIT,
                max=self.MAX_RETRY_WAIT,
            ),
            reraise=True,
        )
        def _request() -> Any:
            # Use throttler to limit concurrent requests
            with self._throttler.acquire():
                try:
                    response = self._session.get(
                        self._build_url(endpoint),
                        params=params,
                        timeout=self.timeout,
                    )
                    return self._handle_response(response)
                except requests.exceptions.Timeout as e:
                    raise TimeoutError(f"Request to {endpoint} timed out") from e
                except requests.exceptions.ConnectionError as e:
                    raise NetworkError(f"Failed to connect to ORTEX API: {e}") from e
                except requests.exceptions.RequestException as e:
                    raise NetworkError(f"Request failed: {e}") from e

        try:
            return _request()
        except RetryError as e:
            # Re-raise the last exception from retries
            exc = e.last_attempt.exception()
            if exc is not None:
                raise exc from e
            raise APIError("Request failed after retries") from e

    def fetch(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> OrtexResponse:
        """Make a GET request and return an OrtexResponse with pagination support.

        This method is similar to get() but returns an OrtexResponse wrapper
        that provides access to pagination, credits info, and data as DataFrame.

        Args:
            endpoint: API endpoint path (e.g., "NYSE/F/short_interest").
            params: Optional query parameters including page and page_size.

        Returns:
            OrtexResponse with data, pagination links, and credit info.

        Example:
            >>> client = OrtexClient(api_key="your-key")
            >>> response = client.fetch("NYSE/F/short_interest", {"page_size": 100})
            >>> print(f"Credits used: {response.credits_used}")
            >>> df = response.df
        """
        from .response import OrtexResponse

        raw = self.get(endpoint, params)
        return OrtexResponse(
            raw_response=raw,
            client=self,
            endpoint=endpoint,
            params=params,
        )

    def close(self) -> None:
        """Close the HTTP session.

        Call this method when you're done using the client to release resources.
        Alternatively, use the client as a context manager.
        """
        self._session.close()

    def __enter__(self) -> OrtexClient:
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and close session."""
        self.close()


def normalize_exchange(exchange: str) -> str:
    """Normalize exchange code to uppercase.

    Args:
        exchange: Exchange code (e.g., "nyse", "NASDAQ").

    Returns:
        Uppercase exchange code.

    Example:
        >>> normalize_exchange("nyse")
        'NYSE'
    """
    return exchange.upper().strip()


def normalize_ticker(ticker: str) -> str:
    """Normalize ticker symbol to uppercase.

    Args:
        ticker: Stock ticker symbol (e.g., "aapl", "TSLA").

    Returns:
        Uppercase ticker symbol.

    Example:
        >>> normalize_ticker("aapl")
        'AAPL'
    """
    return ticker.upper().strip()


def normalize_date(d: str | date | datetime | None) -> str | None:
    """Normalize date to YYYY-MM-DD string format.

    Args:
        d: Date as string, date object, or datetime object. If None, returns None.

    Returns:
        Date string in YYYY-MM-DD format, or None if input is None.

    Raises:
        ValidationError: If date string is not in valid format.

    Example:
        >>> normalize_date("2024-01-15")
        '2024-01-15'
        >>> normalize_date(date(2024, 1, 15))
        '2024-01-15'
        >>> normalize_date(datetime(2024, 1, 15, 12, 30))
        '2024-01-15'
    """
    if d is None:
        return None

    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d")

    if isinstance(d, date):
        return d.strftime("%Y-%m-%d")

    if isinstance(d, str):
        # Validate format
        try:
            datetime.strptime(d.strip(), "%Y-%m-%d")
            return d.strip()
        except ValueError as e:
            raise ValidationError(f"Invalid date format: '{d}'. Expected YYYY-MM-DD format.") from e

    raise ValidationError(f"Invalid date type: {type(d)}. Expected str, date, or datetime.")


def to_dataframe(data: list[dict[str, Any]] | dict[str, Any]) -> pd.DataFrame:
    """Convert API response data to pandas DataFrame.

    Args:
        data: API response data, either a list of records or a single record.

    Returns:
        DataFrame containing the data.

    Example:
        >>> data = [{"date": "2024-01-15", "value": 100}]
        >>> df = to_dataframe(data)
    """
    if isinstance(data, dict):
        data = [data]

    if not data:
        return pd.DataFrame()

    return pd.DataFrame(data)
