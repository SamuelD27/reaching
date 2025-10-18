#!/usr/bin/env python3
"""
RocketReach API Status Checker
Verifies your API key and checks available credits/limits
"""

import requests
import json

# Your API Key
API_KEY = "1ac349bkd05e6c94a51cd27e7070e825a9e3392e"

def check_api_status():
    """Check RocketReach API account status and limits"""

    print("=" * 80)
    print("ROCKETREACH API STATUS CHECKER")
    print("=" * 80)

    # API endpoints
    base_url = "https://api.rocketreach.co/v2/api"
    headers = {
        "Api-Key": API_KEY,
        "Content-Type": "application/json"
    }

    # 1. Check account info
    print("\n1. Checking account information...")
    try:
        response = requests.get(f"{base_url}/account", headers=headers)
        if response.status_code == 200:
            account = response.json()
            print("   ✓ API Key is valid")
            print(f"\n   Account Details:")
            for key, value in account.items():
                print(f"     {key}: {value}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")

    # 2. Check usage/credits
    print("\n2. Checking usage and credits...")
    try:
        response = requests.get(f"{base_url}/usage", headers=headers)
        if response.status_code == 200:
            usage = response.json()
            print("   ✓ Usage information retrieved")
            print(f"\n   Usage Details:")
            print(json.dumps(usage, indent=4))
        else:
            print(f"   ✗ Error: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")

    # 3. Try a simple lookup to test
    print("\n3. Testing lookup capability...")
    try:
        # Try to lookup a well-known person
        test_params = {
            "name": "Sundar Pichai",
            "current_employer": "Google"
        }
        response = requests.get(f"{base_url}/person/lookup", headers=headers, params=test_params)

        if response.status_code == 200:
            print("   ✓ Lookup test successful!")
            result = response.json()
            print(f"   Found: {result.get('name', 'Unknown')}")
        elif response.status_code == 403:
            print("   ✗ Lookup failed: Insufficient Credits")
            print(f"   Response: {response.text}")
        else:
            print(f"   ✗ Error: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")

    # 4. Check rate limits
    print("\n4. Checking rate limits...")
    try:
        response = requests.get(f"{base_url}/ratelimits", headers=headers)
        if response.status_code == 200:
            limits = response.json()
            print("   ✓ Rate limit information retrieved")
            print(f"\n   Rate Limits:")
            print(json.dumps(limits, indent=4))
        else:
            print(f"   ✗ Endpoint may not exist or error: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")

    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)
    print("\nIf you see 'Insufficient Credits', you need to:")
    print("  1. Check your RocketReach dashboard at https://rocketreach.co/account")
    print("  2. Verify your plan includes lookup credits")
    print("  3. Check if you've exhausted your monthly/daily quota")
    print("  4. Contact RocketReach support if the issue persists")
    print("=" * 80)

if __name__ == "__main__":
    check_api_status()
