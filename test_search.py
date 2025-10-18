#!/usr/bin/env python3
"""
Quick test script to verify the search is working
"""

import os
from smart_finance_extractor import SmartFinanceExtractor

# Get API key
api_key = os.getenv("ROCKETREACH_API_KEY")

if not api_key:
    print("ERROR: Please set ROCKETREACH_API_KEY environment variable")
    exit(1)

print("Initializing extractor...")
extractor = SmartFinanceExtractor(api_key)

print("\nTesting search for Goldman Sachs in Singapore...")
profiles = extractor.search_company_location("Goldman Sachs", "Singapore", page_size=5)

print(f"\nResults: Found {len(profiles)} senior profiles")

if profiles:
    print("\nSample profiles:")
    for i, profile in enumerate(profiles[:3], 1):
        print(f"\n{i}. {profile.get('name', 'N/A')}")
        print(f"   Title: {profile.get('current_title', 'N/A')}")
        print(f"   Location: {profile.get('location', 'N/A')}")
else:
    print("\n⚠️  No profiles found - this could mean:")
    print("   1. No senior positions available in this location")
    print("   2. RocketReach doesn't have data for this combination")
    print("   3. API key issue")
    print("\nTry a different company or location")

print("\n" + "="*80)
print("Test complete!")
