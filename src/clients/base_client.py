"""
Base API Client with Shared Logic
All extractors inherit from this class
"""

import requests
import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from requests.exceptions import HTTPError, Timeout, ConnectionError

from ..utils.rate_limiter import RateLimiter


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction.log'),
        logging.StreamHandler()
    ]
)


def safe_api_call(func: Callable) -> Callable:
    """
    Decorator for safe API calls with error handling

    Handles:
    - HTTPError: 429 with exponential backoff, other errors logged
    - Timeout: Retry with longer timeout
    - ConnectionError: Log and continue
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        max_attempts = 3
        base_timeout = self.timeout

        for attempt in range(max_attempts):
            try:
                return func(self, *args, **kwargs)

            except HTTPError as e:
                if e.response.status_code == 429:
                    # Handle with rate limiter's exponential backoff
                    should_retry = self.rate_limiter.handle_429_error()
                    if not should_retry:
                        self.logger.error(f"Max retries for 429 error: {func.__name__}")
                        return None
                    continue  # Retry
                else:
                    self.logger.error(f"HTTP Error in {func.__name__}: {e}")
                    return None

            except Timeout:
                # Retry with longer timeout
                self.timeout = base_timeout * (attempt + 2)
                self.logger.warning(f"Timeout in {func.__name__}, "
                                  f"retrying with {self.timeout}s timeout (attempt {attempt+1}/{max_attempts})")
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    self.logger.error(f"Max timeout retries in {func.__name__}")
                    self.timeout = base_timeout  # Reset
                    return None

            except ConnectionError as e:
                self.logger.error(f"Connection error in {func.__name__}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(5)
                    continue
                return None

            except Exception as e:
                self.logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                return None

        return None

    return wrapper


class BaseAPIClient:
    """
    Base class for API clients with shared functionality

    Features:
    - API authentication
    - Request handling with retry logic
    - Error handling decorator
    - Rate limiting integration
    - Logging
    """

    def __init__(self, api_key: str, base_url: str = None, timeout: int = 30):
        """
        Initialize base API client

        Args:
            api_key: API key for authentication
            base_url: Base URL for API (optional)
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url or "https://api.rocketreach.co/v2/api"
        self.timeout = timeout

        # Setup headers
        self.headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

        # Initialize rate limiter with conservative limits
        self.rate_limiter = RateLimiter()

        # Setup logger
        self.logger = logging.getLogger(self.__class__.__name__)

    @safe_api_call
    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Make GET request with rate limiting

        Args:
            endpoint: API endpoint (will be appended to base_url)
            params: Query parameters

        Returns:
            Response data as dict, or None on error
        """
        # Wait for rate limit if needed
        self.rate_limiter.wait_if_needed()

        url = f"{self.base_url}/{endpoint}"

        self.logger.debug(f"GET {url} with params: {params}")

        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=self.timeout
        )

        # Record API call
        self.rate_limiter.record_call()

        # Raise for HTTP errors
        response.raise_for_status()

        # Reset backoff on success
        self.rate_limiter.reset_backoff()

        return response.json()

    @safe_api_call
    def _post(self, endpoint: str, data: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Make POST request with rate limiting

        Args:
            endpoint: API endpoint (will be appended to base_url)
            data: Request body data

        Returns:
            Response data as dict, or None on error
        """
        # Wait for rate limit if needed
        self.rate_limiter.wait_if_needed()

        url = f"{self.base_url}/{endpoint}"

        self.logger.debug(f"POST {url} with data: {data}")

        response = requests.post(
            url,
            headers=self.headers,
            json=data,
            timeout=self.timeout
        )

        # Record API call
        self.rate_limiter.record_call()

        # Raise for HTTP errors
        response.raise_for_status()

        # Reset backoff on success
        self.rate_limiter.reset_backoff()

        return response.json()

    def get_rate_limit_status(self) -> Dict[str, Dict]:
        """Get current rate limit status"""
        return self.rate_limiter.get_status()

    def print_rate_limit_status(self) -> None:
        """Print rate limit status"""
        self.rate_limiter.print_status()

    def set_log_level(self, level: str) -> None:
        """
        Set logging level

        Args:
            level: One of 'DEBUG', 'INFO', 'WARNING', 'ERROR'
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)


# Example usage
if __name__ == "__main__":
    import os

    # Load API key from environment
    api_key = os.getenv("ROCKETREACH_API_KEY")
    if not api_key:
        print("Set ROCKETREACH_API_KEY environment variable")
        exit(1)

    # Create client
    client = BaseAPIClient(api_key)

    # Test GET request
    print("Testing API connection...")
    result = client._get("account")

    if result:
        print(f"✅ API connection successful!")
        print(f"Account info: {result}")
    else:
        print("❌ API connection failed")

    # Print rate limit status
    client.print_rate_limit_status()
