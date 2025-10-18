#!/usr/bin/env python3
"""
Test what data we actually get from search vs lookup
"""

import requests
import json

API_KEY = os.getenv("ROCKETREACH_API_KEY")
    if not API_KEY:
        print("ERROR: ROCKETREACH_API_KEY environment variable not set!")
        print("Please set it with: export ROCKETREACH_API_KEY='your_key_here'")
        exit(1)
base_url = "https://api.rocketreach.co/v2/api"
headers = {
    "Api-Key": API_KEY,
    "Content-Type": "application/json"
}

print("=" * 80)
print("TESTING: What data do we get from SEARCH vs LOOKUP?")
print("=" * 80)

# 1. Test SEARCH - see what contact info it returns
print("\n1. Testing PERSON SEARCH...")
search_params = {
    "query": {
        "current_employer": ["Google"]
    },
    "page_size": 1,
    "start": 1
}

try:
    response = requests.post(f"{base_url}/person/search", headers=headers, json=search_params)
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        profiles = data.get("profiles", [])

        if profiles:
            profile = profiles[0]
            print(f"\n   Profile from SEARCH:")
            print(json.dumps(profile, indent=4))

            # Check if emails are included
            has_emails = "emails" in profile or "email" in profile
            has_phones = "phones" in profile or "phone" in profile

            print(f"\n   Does SEARCH include emails? {has_emails}")
            print(f"   Does SEARCH include phones? {has_phones}")

            person_id = profile.get("id")

            # 2. Now test LOOKUP with the same person
            if person_id:
                print(f"\n2. Testing PERSON LOOKUP for same person (ID: {person_id})...")

                try:
                    lookup_response = requests.get(
                        f"{base_url}/person/lookup",
                        headers=headers,
                        params={"id": person_id}
                    )
                    print(f"   Status: {lookup_response.status_code}")

                    if lookup_response.status_code == 200:
                        lookup_data = lookup_response.json()
                        print(f"\n   Profile from LOOKUP:")
                        print(json.dumps(lookup_data, indent=4))

                        # Compare data
                        print("\n" + "=" * 80)
                        print("COMPARISON:")
                        print("=" * 80)
                        print(f"SEARCH returned: {len(json.dumps(profile))} characters")
                        print(f"LOOKUP returned: {len(json.dumps(lookup_data))} characters")

                        # Check for contact info
                        search_has_emails = "emails" in profile or "email" in profile
                        lookup_has_emails = "emails" in lookup_data or "email" in lookup_data

                        print(f"\nSEARCH includes contact info: {search_has_emails}")
                        print(f"LOOKUP includes contact info: {lookup_has_emails}")

                    elif lookup_response.status_code == 403:
                        print(f"   Error: {lookup_response.text}")
                        print("\n   ⚠️  LOOKUP blocked by insufficient credits")
                        print("   BUT we already have basic data from SEARCH!")

                except Exception as e:
                    print(f"   Exception: {e}")

    else:
        print(f"   Error: {response.text}")

except Exception as e:
    print(f"   Exception: {e}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("If SEARCH returns contact info, we don't need LOOKUP at all!")
print("If SEARCH only returns basic info, then we're blocked without export credits.")
print("=" * 80)
