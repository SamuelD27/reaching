"""
Rate Limiter with Exponential Backoff
Manages API rate limits across multiple time windows
"""

import time
import threading
from typing import Dict, List
from collections import deque


class RateLimiter:
    """
    Thread-safe rate limiter with multiple time windows and exponential backoff

    Features:
    - Conservative limits (10/min, 35/hour, 350/day)
    - Exponential backoff on 429 errors (2^attempt * 60 seconds, max 3 retries)
    - Thread-safe call tracking
    - Status reporting
    """

    def __init__(self, limits: Dict[str, Dict[str, int]] = None):
        """
        Initialize rate limiter

        Args:
            limits: Dict of {window_name: {'limit': X, 'window': Y}}
                   Defaults to conservative limits
        """
        self.limits = limits or {
            'minute': {'limit': 10, 'window': 60},
            'hour': {'limit': 35, 'window': 3600},
            'day': {'limit': 350, 'window': 86400},
        }

        # Thread-safe call tracking using deque for efficient operations
        self.call_times = deque(maxlen=1000)  # Keep last 1000 calls
        self.lock = threading.RLock()

        # Backoff tracking
        self.retry_count = 0
        self.max_retries = 3
        self.base_backoff = 60  # 60 seconds base

    def wait_if_needed(self) -> None:
        """
        Wait if any rate limit would be exceeded
        Thread-safe implementation
        """
        with self.lock:
            now = time.time()

            # Clean old calls (older than longest window)
            max_window = max(limit['window'] for limit in self.limits.values())
            cutoff = now - max_window

            while self.call_times and self.call_times[0] < cutoff:
                self.call_times.popleft()

            # Check each time window
            for window_name, limit_config in self.limits.items():
                window_size = limit_config['window']
                limit = limit_config['limit']

                # Count calls within this window
                window_start = now - window_size
                calls_in_window = sum(1 for t in self.call_times if t > window_start)

                # If at limit, calculate wait time
                if calls_in_window >= limit:
                    # Find oldest call in this window
                    oldest_in_window = next(t for t in self.call_times if t > window_start)

                    # Wait until that call expires + safety buffer
                    sleep_time = window_size - (now - oldest_in_window) + 2

                    if sleep_time > 0:
                        print(f"⏳ Rate limit ({window_name}): {calls_in_window}/{limit} calls")
                        print(f"   Waiting {sleep_time:.0f}s before next call...")
                        time.sleep(sleep_time)
                        now = time.time()  # Update time after sleep

    def record_call(self) -> None:
        """Record that an API call was made"""
        with self.lock:
            self.call_times.append(time.time())

    def handle_429_error(self) -> bool:
        """
        Handle 429 (Too Many Requests) error with exponential backoff

        Returns:
            bool: True if should retry, False if max retries exceeded
        """
        with self.lock:
            if self.retry_count >= self.max_retries:
                print(f"❌ Max retries ({self.max_retries}) exceeded for 429 errors")
                self.retry_count = 0  # Reset for next batch
                return False

            # Exponential backoff: 2^attempt * base_backoff
            wait_time = (2 ** self.retry_count) * self.base_backoff
            self.retry_count += 1

            print(f"⚠️  429 Error: Too Many Requests")
            print(f"   Retry {self.retry_count}/{self.max_retries}")
            print(f"   Waiting {wait_time}s (exponential backoff)...")
            time.sleep(wait_time)

            return True

    def reset_backoff(self) -> None:
        """Reset backoff counter after successful call"""
        with self.lock:
            self.retry_count = 0

    def get_status(self) -> Dict[str, Dict]:
        """
        Get current rate limit status

        Returns:
            Dict with usage stats for each window
        """
        with self.lock:
            now = time.time()
            status = {}

            for window_name, limit_config in self.limits.items():
                window_size = limit_config['window']
                limit = limit_config['limit']
                window_start = now - window_size

                calls_in_window = sum(1 for t in self.call_times if t > window_start)

                status[window_name] = {
                    'used': calls_in_window,
                    'limit': limit,
                    'remaining': max(0, limit - calls_in_window),
                    'percentage': (calls_in_window / limit * 100) if limit > 0 else 0,
                    'resets_in': window_size if calls_in_window >= limit else None
                }

            return status

    def print_status(self) -> None:
        """Print current rate limit status in a readable format"""
        status = self.get_status()

        print("\n" + "=" * 60)
        print("RATE LIMIT STATUS")
        print("=" * 60)

        for window_name, stats in status.items():
            used = stats['used']
            limit = stats['limit']
            remaining = stats['remaining']
            pct = stats['percentage']

            # Visual bar
            bar_length = 30
            filled = int(bar_length * pct / 100)
            bar = "█" * filled + "░" * (bar_length - filled)

            print(f"\n{window_name.upper():8s} [{bar}] {pct:5.1f}%")
            print(f"         Used: {used}/{limit} (Remaining: {remaining})")

            if stats['resets_in']:
                print(f"         Resets in: {stats['resets_in']}s")

        print("=" * 60 + "\n")

    def __enter__(self):
        """Context manager support"""
        self.wait_if_needed()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Record call on context exit"""
        if exc_type is None:  # Only record if no exception
            self.record_call()
        return False  # Don't suppress exceptions


# Example usage
if __name__ == "__main__":
    # Create limiter with default conservative limits
    limiter = RateLimiter()

    print("Testing rate limiter...")
    print("Conservative limits: 10/min, 35/hour, 350/day")

    # Simulate API calls
    for i in range(15):
        print(f"\nCall {i+1}:")
        limiter.wait_if_needed()
        print(f"  Making API call...")
        limiter.record_call()
        time.sleep(0.5)  # Simulate API call time

    # Print final status
    limiter.print_status()

    # Test 429 handling
    print("\nTesting 429 error handling:")
    for attempt in range(5):
        should_retry = limiter.handle_429_error()
        if not should_retry:
            print("Max retries reached!")
            break
