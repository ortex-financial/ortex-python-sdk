"""Tests for request throttler."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ortex.throttler import RequestThrottler


class TestRequestThrottlerInit:
    """Tests for RequestThrottler initialization."""

    def test_init_default_values(self) -> None:
        """Test default initialization values."""
        throttler = RequestThrottler()
        assert throttler.max_concurrent == 10  # RequestThrottler default
        assert throttler.requests_per_second is None  # RequestThrottler default

    def test_init_custom_max_concurrent(self) -> None:
        """Test custom max_concurrent value."""
        throttler = RequestThrottler(max_concurrent=5)
        assert throttler.max_concurrent == 5

    def test_init_custom_requests_per_second(self) -> None:
        """Test custom requests_per_second value."""
        throttler = RequestThrottler(requests_per_second=2.0)
        assert throttler.requests_per_second == 2.0

    def test_init_disabled_throttling(self) -> None:
        """Test disabling throttling with max_concurrent=0."""
        throttler = RequestThrottler(max_concurrent=0)
        assert throttler.max_concurrent == 0


class TestRequestThrottlerAcquire:
    """Tests for RequestThrottler.acquire method."""

    def test_acquire_basic(self) -> None:
        """Test basic acquire and release."""
        throttler = RequestThrottler(max_concurrent=1)
        with throttler.acquire():
            # Should not block
            pass

    def test_acquire_tracks_stats(self) -> None:
        """Test that acquire updates statistics."""
        throttler = RequestThrottler(max_concurrent=10)

        with throttler.acquire():
            stats = throttler.stats
            assert stats["current_concurrent"] == 1
            assert stats["total_requests"] == 1

        stats = throttler.stats
        assert stats["current_concurrent"] == 0
        assert stats["total_requests"] == 1

    def test_acquire_multiple(self) -> None:
        """Test multiple sequential acquisitions."""
        throttler = RequestThrottler(max_concurrent=10)

        for _ in range(5):
            with throttler.acquire():
                pass

        stats = throttler.stats
        assert stats["total_requests"] == 5


class TestRequestThrottlerConcurrency:
    """Tests for concurrent request limiting."""

    def test_limits_concurrent_requests(self) -> None:
        """Test that concurrent requests are limited."""
        max_concurrent = 3
        throttler = RequestThrottler(max_concurrent=max_concurrent)
        concurrent_count = []
        lock = threading.Lock()

        def worker() -> None:
            with throttler.acquire():
                with lock:
                    concurrent_count.append(throttler.stats["current_concurrent"])
                time.sleep(0.05)  # Hold the slot briefly

        # Start more threads than max_concurrent
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No recorded count should exceed max_concurrent
        assert all(c <= max_concurrent for c in concurrent_count)

    def test_concurrent_requests_complete(self) -> None:
        """Test that all concurrent requests eventually complete."""
        throttler = RequestThrottler(max_concurrent=2)
        results = []
        lock = threading.Lock()

        def worker(n: int) -> int:
            with throttler.acquire():
                time.sleep(0.01)
                with lock:
                    results.append(n)
                return n

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            completed = [f.result() for f in as_completed(futures)]

        assert len(completed) == 10
        assert len(results) == 10


class TestRequestThrottlerRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limiting_enforced(self) -> None:
        """Test that rate limiting is enforced."""
        # 5 requests per second = 0.2s between requests
        # With max_concurrent=2, bucket starts with 2 tokens
        throttler = RequestThrottler(max_concurrent=2, requests_per_second=5.0)

        start = time.monotonic()

        # Make 5 requests:
        # - First 2 use initial tokens (instant)
        # - Next 3 need to wait for tokens at 5/sec rate = 0.6s minimum
        for _ in range(5):
            with throttler.acquire():
                pass

        elapsed = time.monotonic() - start

        # We need at least 0.6s for the 3 rate-limited requests
        # Allow some tolerance for execution overhead
        assert elapsed >= 0.5, f"Rate limiting not enforced, elapsed: {elapsed}"

    def test_no_rate_limiting_when_disabled(self) -> None:
        """Test that requests are fast when rate limiting is disabled."""
        throttler = RequestThrottler(max_concurrent=10, requests_per_second=None)

        start = time.monotonic()

        for _ in range(10):
            with throttler.acquire():
                pass

        elapsed = time.monotonic() - start

        # Without rate limiting, should complete very quickly
        assert elapsed < 0.5


class TestRequestThrottlerWithOrtexClient:
    """Tests for throttler integration with OrtexClient."""

    def test_client_has_throttler(self, api_key: str) -> None:
        """Test that OrtexClient has a throttler."""
        from ortex import OrtexClient

        client = OrtexClient(api_key=api_key)
        assert client.throttler is not None
        assert isinstance(client.throttler, RequestThrottler)

    def test_client_default_throttler_settings(self, api_key: str) -> None:
        """Test default throttler settings in OrtexClient."""
        from ortex import OrtexClient

        client = OrtexClient(api_key=api_key)
        assert client.throttler.max_concurrent == 2  # OrtexClient default
        assert client.throttler.requests_per_second == 3.0  # OrtexClient default

    def test_client_custom_throttler_settings(self, api_key: str) -> None:
        """Test custom throttler settings in OrtexClient."""
        from ortex import OrtexClient

        client = OrtexClient(
            api_key=api_key,
            max_concurrent_requests=5,
            requests_per_second=2.0,
        )
        assert client.throttler.max_concurrent == 5
        assert client.throttler.requests_per_second == 2.0

    def test_client_disabled_throttling(self, api_key: str) -> None:
        """Test disabling throttling in OrtexClient."""
        from ortex import OrtexClient

        client = OrtexClient(api_key=api_key, max_concurrent_requests=0)
        assert client.throttler.max_concurrent == 0


class TestRequestThrottlerTimeout:
    """Tests for acquire timeout functionality."""

    def test_acquire_timeout(self) -> None:
        """Test that acquire can timeout."""
        throttler = RequestThrottler(max_concurrent=1)

        # Acquire the only slot
        with throttler.acquire():
            # Try to acquire from another thread with short timeout
            result = {"timed_out": False}

            def try_acquire() -> None:
                try:
                    with throttler.acquire(timeout=0.1):
                        pass
                except TimeoutError:
                    result["timed_out"] = True

            thread = threading.Thread(target=try_acquire)
            thread.start()
            thread.join()

            assert result["timed_out"], "Expected timeout but didn't get one"


class TestRequestThrottlerStats:
    """Tests for throttler statistics."""

    def test_stats_initial(self) -> None:
        """Test initial statistics values."""
        throttler = RequestThrottler()
        stats = throttler.stats
        assert stats["total_requests"] == 0
        assert stats["queued_requests"] == 0
        assert stats["current_concurrent"] == 0

    def test_stats_thread_safe(self) -> None:
        """Test that statistics are thread-safe."""
        throttler = RequestThrottler(max_concurrent=5)

        def worker() -> None:
            with throttler.acquire():
                time.sleep(0.01)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = throttler.stats
        assert stats["total_requests"] == 20
        assert stats["current_concurrent"] == 0


class TestRequestThrottlerAcquireNowait:
    """Tests for non-blocking acquire."""

    def test_acquire_nowait_success(self) -> None:
        """Test successful non-blocking acquire."""
        throttler = RequestThrottler(max_concurrent=1)

        assert throttler.acquire_nowait() is True
        throttler.release()

    def test_acquire_nowait_failure(self) -> None:
        """Test failed non-blocking acquire when slots exhausted."""
        throttler = RequestThrottler(max_concurrent=1)

        # Take the only slot
        with throttler.acquire():
            # Try to acquire without blocking
            assert throttler.acquire_nowait() is False
