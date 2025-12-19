"""Thread-safe request throttler for rate limiting concurrent API requests."""

from __future__ import annotations

import threading
import time
from collections.abc import Generator
from contextlib import contextmanager


class RequestThrottler:
    """Thread-safe throttler to limit concurrent requests and request rate.

    This class prevents overwhelming the API server by:
    1. Limiting the number of concurrent requests (semaphore-based)
    2. Limiting the request rate (token bucket algorithm)

    Example:
        >>> throttler = RequestThrottler(max_concurrent=10, requests_per_second=5.0)
        >>> with throttler.acquire():
        ...     # Make API request here
        ...     response = session.get(url)
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        requests_per_second: float | None = None,
    ) -> None:
        """Initialize the request throttler.

        Args:
            max_concurrent: Maximum number of concurrent requests allowed.
                Defaults to 10. Set to 0 or negative to disable.
            requests_per_second: Maximum requests per second (rate limit).
                Defaults to None (no rate limit). When set, requests are
                spaced to maintain this rate across all threads.
        """
        self._max_concurrent = max_concurrent
        self._requests_per_second = requests_per_second

        # Semaphore for limiting concurrent requests
        if max_concurrent > 0:
            self._semaphore: threading.Semaphore | None = threading.Semaphore(max_concurrent)
        else:
            self._semaphore = None

        # Token bucket for rate limiting
        self._rate_lock = threading.Lock()
        self._tokens = float(max_concurrent) if max_concurrent > 0 else 1.0
        self._max_tokens = self._tokens
        self._last_refill = time.monotonic()

        # Statistics
        self._stats_lock = threading.Lock()
        self._total_requests = 0
        self._queued_requests = 0
        self._current_concurrent = 0

    @property
    def max_concurrent(self) -> int:
        """Maximum number of concurrent requests allowed."""
        return self._max_concurrent

    @property
    def requests_per_second(self) -> float | None:
        """Maximum requests per second, or None if unlimited."""
        return self._requests_per_second

    @property
    def stats(self) -> dict[str, int]:
        """Get current throttler statistics.

        Returns:
            Dictionary with total_requests, queued_requests, and current_concurrent.
        """
        with self._stats_lock:
            return {
                "total_requests": self._total_requests,
                "queued_requests": self._queued_requests,
                "current_concurrent": self._current_concurrent,
            }

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time (token bucket algorithm)."""
        if self._requests_per_second is None:
            return

        now = time.monotonic()
        elapsed = now - self._last_refill
        self._last_refill = now

        # Add tokens based on elapsed time
        new_tokens = elapsed * self._requests_per_second
        self._tokens = min(self._max_tokens, self._tokens + new_tokens)

    def _wait_for_token(self) -> None:
        """Wait until a token is available for rate limiting."""
        if self._requests_per_second is None:
            return

        with self._rate_lock:
            self._refill_tokens()

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return

            # Calculate wait time for next token
            tokens_needed = 1.0 - self._tokens
            wait_time = tokens_needed / self._requests_per_second

        # Wait outside the lock
        if wait_time > 0:
            time.sleep(wait_time)

        # Consume the token after waiting
        with self._rate_lock:
            self._refill_tokens()
            self._tokens = max(0, self._tokens - 1.0)

    @contextmanager
    def acquire(self, timeout: float | None = None) -> Generator[None, None, None]:
        """Acquire permission to make a request.

        This context manager blocks until the request is allowed based on
        both concurrency limits and rate limits.

        Args:
            timeout: Maximum seconds to wait for permission. None means wait forever.
                     Only applies to the concurrency semaphore, not rate limiting.

        Yields:
            None when permission is granted.

        Raises:
            TimeoutError: If timeout is specified and permission is not granted in time.

        Example:
            >>> with throttler.acquire():
            ...     response = session.get(url)
        """
        # Track queued request
        with self._stats_lock:
            self._queued_requests += 1

        acquired = False
        try:
            # Wait for concurrent slot
            if self._semaphore is not None:
                acquired = self._semaphore.acquire(blocking=True, timeout=timeout)
                if not acquired:
                    raise TimeoutError(f"Timed out waiting for request slot after {timeout}s")
            else:
                acquired = True

            # Update stats
            with self._stats_lock:
                self._queued_requests -= 1
                self._current_concurrent += 1
                self._total_requests += 1

            # Wait for rate limit token
            self._wait_for_token()

            yield

        finally:
            if acquired:
                with self._stats_lock:
                    self._current_concurrent -= 1

                if self._semaphore is not None:
                    self._semaphore.release()
            else:
                # Wasn't acquired (timeout), just decrement queued
                with self._stats_lock:
                    self._queued_requests -= 1

    def acquire_nowait(self) -> bool:
        """Try to acquire permission without blocking.

        Returns:
            True if permission was granted, False if it would block.

        Note:
            This only checks the concurrency semaphore, not rate limiting.
            If rate limiting is enabled, the caller may still need to wait.
        """
        if self._semaphore is None:
            return True
        return self._semaphore.acquire(blocking=False)

    def release(self) -> None:
        """Release a previously acquired permission.

        Only call this if you used acquire_nowait() and got True.
        Do not call this if you used the acquire() context manager.
        """
        if self._semaphore is not None:
            self._semaphore.release()
        with self._stats_lock:
            self._current_concurrent = max(0, self._current_concurrent - 1)
