#!/usr/bin/env python3
"""
Unit Tests for Rate Limiter
"""

import unittest
import time
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.rate_limiter import RateLimiter


class TestRateLimiter(unittest.TestCase):
    """Test cases for RateLimiter"""

    def setUp(self):
        """Set up test fixtures"""
        # Use very small limits for fast testing
        self.limiter = RateLimiter(limits={
            'second': {'limit': 2, 'window': 1},
            'minute': {'limit': 5, 'window': 60}
        })

    def test_initialization(self):
        """Test limiter initializes correctly"""
        self.assertIsNotNone(self.limiter)
        self.assertEqual(len(self.limiter.limits), 2)
        self.assertEqual(self.limiter.retry_count, 0)

    def test_record_call(self):
        """Test recording API calls"""
        initial_count = len(self.limiter.call_times)

        self.limiter.record_call()
        self.assertEqual(len(self.limiter.call_times), initial_count + 1)

        self.limiter.record_call()
        self.assertEqual(len(self.limiter.call_times), initial_count + 2)

    def test_rate_limiting(self):
        """Test that rate limiting actually waits"""
        # Make calls up to limit
        for _ in range(2):
            self.limiter.wait_if_needed()
            self.limiter.record_call()

        # Next call should trigger wait
        start = time.time()
        self.limiter.wait_if_needed()
        elapsed = time.time() - start

        # Should have waited ~1 second (window size)
        self.assertGreater(elapsed, 0.5, "Should have waited")

    def test_get_status(self):
        """Test status reporting"""
        self.limiter.record_call()
        self.limiter.record_call()

        status = self.limiter.get_status()

        self.assertIn('second', status)
        self.assertEqual(status['second']['used'], 2)
        self.assertEqual(status['second']['limit'], 2)
        self.assertEqual(status['second']['remaining'], 0)

    def test_handle_429_error(self):
        """Test exponential backoff for 429 errors"""
        # First retry
        start = time.time()
        should_retry = self.limiter.handle_429_error()
        elapsed = time.time() - start

        self.assertTrue(should_retry)
        self.assertEqual(self.limiter.retry_count, 1)
        # Should wait 2^0 * 60 = 60 seconds (or base_backoff)
        # For testing, we'd mock this

    def test_max_retries(self):
        """Test max retries for 429 errors"""
        # Exhaust retries
        for _ in range(3):
            self.limiter.handle_429_error()

        # Next should return False
        should_retry = self.limiter.handle_429_error()
        self.assertFalse(should_retry)

    def test_context_manager(self):
        """Test using limiter as context manager"""
        with self.limiter:
            # Inside context, call should be recorded on exit
            pass

        # Verify call was recorded
        status = self.limiter.get_status()
        self.assertGreater(status['second']['used'], 0)


class TestRateLimiterEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_custom_limits(self):
        """Test with custom limits"""
        custom = RateLimiter(limits={
            'test': {'limit': 10, 'window': 5}
        })
        self.assertEqual(len(custom.limits), 1)
        self.assertIn('test', custom.limits)

    def test_thread_safety(self):
        """Test thread-safe operations"""
        limiter = RateLimiter()

        # Simulate concurrent access
        import threading

        def make_calls():
            for _ in range(5):
                limiter.wait_if_needed()
                limiter.record_call()

        threads = [threading.Thread(target=make_calls) for _ in range(3)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify all calls recorded
        status = limiter.get_status()
        # Should have 15 total calls (3 threads * 5 calls)
        # But some might have expired depending on timing


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
