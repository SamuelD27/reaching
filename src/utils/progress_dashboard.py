"""
Progress Dashboard for Real-time Extraction Monitoring
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict


class ProgressDashboard:
    """
    Real-time progress dashboard for extraction

    Features:
    - Session stats (current run)
    - Success rate by company
    - Rate limit status
    - Estimated time remaining
    - Visual progress bars
    """

    def __init__(self):
        """Initialize dashboard"""
        self.start_time = time.time()
        self.total_extracted = 0
        self.total_target = 0

        # Track by company
        self.company_stats = defaultdict(lambda: {'attempted': 0, 'success': 0, 'failed': 0})

        # Rate limit tracking
        self.api_calls_made = 0

        # Time estimation
        self.last_contact_time = time.time()
        self.contacts_times = []  # Track time per contact for estimation

    def update(self, company: str = None, success: bool = True):
        """
        Update dashboard with new contact

        Args:
            company: Company name (optional)
            success: Whether extraction succeeded
        """
        self.total_extracted += 1

        if company:
            self.company_stats[company]['attempted'] += 1
            if success:
                self.company_stats[company]['success'] += 1
            else:
                self.company_stats[company]['failed'] += 1

        # Track timing
        now = time.time()
        time_diff = now - self.last_contact_time
        self.contacts_times.append(time_diff)
        if len(self.contacts_times) > 10:  # Keep last 10
            self.contacts_times.pop(0)
        self.last_contact_time = now

    def set_target(self, target: int):
        """Set total extraction target"""
        self.total_target = target

    def record_api_call(self):
        """Record an API call was made"""
        self.api_calls_made += 1

    def get_estimated_time_remaining(self) -> Optional[timedelta]:
        """Calculate estimated time remaining"""
        if not self.contacts_times or self.total_target == 0:
            return None

        remaining = self.total_target - self.total_extracted
        if remaining <= 0:
            return timedelta(0)

        # Average time per contact from recent samples
        avg_time_per_contact = sum(self.contacts_times) / len(self.contacts_times)
        seconds_remaining = remaining * avg_time_per_contact

        return timedelta(seconds=int(seconds_remaining))

    def get_success_rate(self, company: str = None) -> float:
        """
        Get success rate

        Args:
            company: Specific company or None for overall

        Returns:
            Success rate as percentage (0-100)
        """
        if company:
            stats = self.company_stats[company]
            total = stats['attempted']
            if total == 0:
                return 0.0
            return (stats['success'] / total) * 100

        # Overall success rate
        total_attempted = sum(s['attempted'] for s in self.company_stats.values())
        if total_attempted == 0:
            return 0.0

        total_success = sum(s['success'] for s in self.company_stats.values())
        return (total_success / total_attempted) * 100

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def print(self, rate_limit_status: Dict = None):
        """
        Print dashboard to console

        Args:
            rate_limit_status: Rate limit status from RateLimiter.get_status()
        """
        self.clear_screen()

        # Calculate runtime
        runtime = timedelta(seconds=int(time.time() - self.start_time))

        # Header
        print("=" * 80)
        print("EXTRACTION DASHBOARD".center(80))
        print("=" * 80)
        print(f"Runtime: {runtime}  |  Updated: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)

        # Progress
        if self.total_target > 0:
            percentage = (self.total_extracted / self.total_target) * 100
            bar_length = 40
            filled = int(bar_length * percentage / 100)
            bar = "█" * filled + "░" * (bar_length - filled)

            print(f"\nPROGRESS:")
            print(f"  [{bar}] {percentage:.1f}%")
            print(f"  {self.total_extracted:,} / {self.total_target:,} contacts")

            # Time estimation
            eta = self.get_estimated_time_remaining()
            if eta:
                print(f"  ETA: {eta}")
        else:
            print(f"\nEXTRACTED: {self.total_extracted:,} contacts")

        # Success rate
        overall_rate = self.get_success_rate()
        print(f"\nSUCCESS RATE: {overall_rate:.1f}%")

        # Company breakdown
        if self.company_stats:
            print(f"\nBY COMPANY:")
            for company, stats in sorted(self.company_stats.items()):
                attempted = stats['attempted']
                success = stats['success']
                rate = (success / attempted * 100) if attempted > 0 else 0

                # Mini progress bar per company
                bar_len = 20
                filled = int(bar_len * rate / 100)
                mini_bar = "█" * filled + "░" * (bar_len - filled)

                print(f"  {company[:30]:<30} [{mini_bar}] {rate:5.1f}% ({success}/{attempted})")

        # Rate limits
        if rate_limit_status:
            print(f"\nRATE LIMITS:")
            for window, stats in rate_limit_status.items():
                used = stats['used']
                limit = stats['limit']
                remaining = stats['remaining']
                pct = stats['percentage']

                bar_len = 30
                filled = int(bar_len * pct / 100)
                bar = "█" * filled + "░" * (bar_len - filled)

                print(f"  {window.capitalize():<8} [{bar}] {used}/{limit} (Remaining: {remaining})")

        # API calls
        print(f"\nAPI CALLS MADE: {self.api_calls_made:,}")

        print("=" * 80)

    def print_summary(self):
        """Print final summary"""
        runtime = timedelta(seconds=int(time.time() - self.start_time))

        print("\n" + "=" * 80)
        print("EXTRACTION SUMMARY".center(80))
        print("=" * 80)
        print(f"Total Runtime: {runtime}")
        print(f"Total Extracted: {self.total_extracted:,} contacts")
        print(f"API Calls Made: {self.api_calls_made:,}")
        print(f"Overall Success Rate: {self.get_success_rate():.1f}%")

        if self.company_stats:
            print(f"\nCompany Breakdown:")
            for company, stats in sorted(self.company_stats.items()):
                print(f"  {company}: {stats['success']} contacts "
                      f"({self.get_success_rate(company):.1f}% success)")

        print("=" * 80)


# Example usage
if __name__ == "__main__":
    import random

    dashboard = ProgressDashboard()
    dashboard.set_target(100)

    companies = ['Goldman Sachs', 'Morgan Stanley', 'Blackstone', 'Citadel']

    print("Simulating extraction with dashboard updates...")
    print("(Updates every second for demo)")

    for i in range(20):
        # Simulate extraction
        company = random.choice(companies)
        success = random.random() > 0.1  # 90% success rate

        dashboard.update(company, success)
        dashboard.record_api_call()

        # Mock rate limit status
        rate_status = {
            'minute': {'used': i % 10, 'limit': 10, 'remaining': 10 - (i % 10), 'percentage': (i % 10) * 10},
            'hour': {'used': i % 35, 'limit': 35, 'remaining': 35 - (i % 35), 'percentage': (i % 35) / 35 * 100}
        }

        # Print dashboard
        dashboard.print(rate_status)

        time.sleep(1)

    # Print final summary
    dashboard.print_summary()
