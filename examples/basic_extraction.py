#!/usr/bin/env python3
"""
Basic Contact Extraction Example
Demonstrates simple extraction from one company
"""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.base_client import BaseAPIClient
from src.config import Config


def main():
    """Extract 10 contacts from Goldman Sachs"""
    print("=" * 80)
    print("BASIC EXTRACTION EXAMPLE")
    print("=" * 80)

    # Load configuration
    config = Config()

    # Get API key
    api_key = config.get('rocketreach.api_key') or os.getenv('ROCKETREACH_API_KEY')
    if not api_key:
        print("\n❌ ERROR: ROCKETREACH_API_KEY not set!")
        print("Set it with: export ROCKETREACH_API_KEY='your_key'")
        return 1

    # Create API client
    print("\n📡 Connecting to RocketReach API...")
    client = BaseAPIClient(api_key)

    # Simple search
    print("🔍 Searching for contacts at Goldman Sachs in Singapore...")

    search_params = {
        "query": {
            "current_employer": ["Goldman Sachs"],
            "location": ["Singapore"]
        },
        "page_size": 10,
        "start": 1
    }

    try:
        # Make API call (rate limiting is automatic!)
        result = client._post("search", data=search_params)

        if result and 'profiles' in result:
            profiles = result['profiles']
            print(f"\n✅ Found {len(profiles)} contacts!\n")

            # Display results
            for i, profile in enumerate(profiles, 1):
                name = profile.get('name', 'N/A')
                title = profile.get('current_title', 'N/A')
                location = profile.get('location', 'N/A')

                print(f"{i}. {name}")
                print(f"   Title: {title}")
                print(f"   Location: {location}")
                print()

            # Show rate limit status
            print("\n" + "=" * 80)
            print("Rate Limit Status:")
            client.print_rate_limit_status()

        else:
            print("❌ No results found")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

    print("=" * 80)
    print("✅ Example complete!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
