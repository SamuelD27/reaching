#!/usr/bin/env python3
"""
RocketReach Search-Only Mode
Uses ONLY the search API (no export credits needed)

What you get:
- Name, title, company, location
- LinkedIn profile URLs (most valuable!)
- Sector classification
- Duplicate tracking

What you DON'T get:
- Email addresses
- Phone numbers

Strategy: Export LinkedIn URLs, then:
1. Connect with them on LinkedIn directly
2. Use other tools (Hunter.io, LinkedIn Sales Nav) for emails
3. Contact via LinkedIn InMail
"""

import requests
import pandas as pd
import time
from datetime import datetime
import json
import os
from typing import List, Dict, Set

class RocketReachSearchOnly:
    def __init__(self, api_key: str, history_file: str = "contact_history.json"):
        """Initialize search-only mode (no export credits needed)"""
        self.api_key = api_key
        self.base_url = "https://api.rocketreach.co/v2/api"
        self.headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }

        # Rate limits for search only
        self.search_calls = []
        self.search_rate_limits = {
            'minute': {'limit': 15, 'window': 60},
            'hour': {'limit': 50, 'window': 3600},
            'day': {'limit': 500, 'window': 86400},
            'month': {'limit': 10000, 'window': 2592000}
        }

        # Duplicate tracking
        self.history_file = history_file
        self.contacted_ids = self._load_contact_history()

        # Sector classification
        self.sector_keywords = {
            "Investment Banking": [
                "investment bank", "goldman sachs", "morgan stanley", "jp morgan", "jpmorgan",
                "bank of america merrill", "merrill lynch", "citi", "citigroup", "barclays",
                "credit suisse", "ubs", "deutsche bank", "jefferies", "lazard", "evercore",
                "rothschild", "moelis", "centerview", "pjt partners", "greenhill", "houlihan lokey",
                "investment banking", "m&a", "mergers and acquisitions", "capital markets", "ibd"
            ],
            "Consulting": [
                "mckinsey", "bain", "boston consulting", "bcg", "deloitte consulting",
                "pwc consulting", "accenture", "kpmg consulting", "ey consulting", "parthenon",
                "oliver wyman", "strategy&", "roland berger", "a.t. kearney", "l.e.k",
                "consultant", "management consulting", "strategy consulting"
            ],
            "Hedge Fund": [
                "hedge fund", "bridgewater", "citadel", "millennium", "point72", "two sigma",
                "d.e. shaw", "renaissance technologies", "elliott management", "tiger global",
                "coatue", "viking global", "baupost", "appaloosa", "third point", "och-ziff",
                "paulson", "soros fund", "quantitative", "long short", "macro fund"
            ],
            "Private Equity": [
                "private equity", "blackstone", "kkr", "carlyle", "apollo", "tpg", "warburg pincus",
                "bain capital", "vista equity", "silver lake", "thoma bravo", "advent", "permira",
                "cvc", "apax", "general atlantic", "hellman & friedman", "providence equity",
                "buyout", "growth equity", "leveraged buyout", "lbo"
            ],
            "Venture Capital": [
                "venture capital", "sequoia", "andreessen horowitz", "a16z", "accel", "benchmark",
                "greylock", "kleiner perkins", "lightspeed", "insight partners", "nea", "khosla",
                "founders fund", "general catalyst", "bessemer", "index ventures", "ycombinator",
                "y combinator", "500 startups", "techstars", "seed", "series a", "series b"
            ]
        }

    def _load_contact_history(self) -> Set[str]:
        """Load previously contacted person IDs"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get("contacted_ids", []))
            except:
                return set()
        return set()

    def _save_contact_history(self) -> None:
        """Save contacted person IDs"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump({"contacted_ids": list(self.contacted_ids)}, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save history: {e}")

    def _classify_sector(self, title: str, company: str) -> str:
        """Classify sector based on keywords"""
        text = f"{title} {company}".lower()
        for sector, keywords in self.sector_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return sector
        return "Other"

    def _check_rate_limit(self) -> None:
        """Check and enforce search rate limits"""
        current_time = time.time()

        for window_name, config in self.search_rate_limits.items():
            limit = config['limit']
            window_seconds = config['window']

            recent_calls = [t for t in self.search_calls if current_time - t < window_seconds]

            if len(recent_calls) >= limit:
                oldest_call = min(recent_calls)
                wait_time = window_seconds - (current_time - oldest_call) + 1
                print(f"⏳ Rate limit: {limit} searches per {window_name}. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                self.search_calls[:] = [t for t in self.search_calls if time.time() - t < window_seconds]

        # Clean up old calls
        max_window = max(config['window'] for config in self.search_rate_limits.values())
        self.search_calls[:] = [t for t in self.search_calls if current_time - t < max_window]
        self.search_calls.append(current_time)

    def search_people(self, search_params: Dict) -> List[Dict]:
        """Search for people (no export credits needed!)"""
        self._check_rate_limit()

        url = f"{self.base_url}/person/search"

        # Clean empty params
        cleaned_params = {"query": {}}
        if "query" in search_params:
            for key, value in search_params["query"].items():
                if value and len(value) > 0:
                    cleaned_params["query"][key] = value

        if not cleaned_params["query"]:
            print("Error: At least one search parameter required")
            return []

        # Add pagination
        if "page_size" in search_params:
            cleaned_params["page_size"] = search_params["page_size"]
        if "start" in search_params:
            cleaned_params["start"] = search_params["start"]

        try:
            response = requests.post(url, headers=self.headers, json=cleaned_params)
            response.raise_for_status()
            data = response.json()
            return data.get("profiles", [])
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def extract_contacts_search_only(self, search_params: Dict, max_results: int = 500) -> pd.DataFrame:
        """
        Extract contacts using SEARCH ONLY (no export credits needed)

        Returns basic info + LinkedIn URLs for manual outreach
        """
        all_contacts = []
        page_size = 100
        current_start = 1
        total_fetched = 0

        print(f"\n{'=' * 80}")
        print(f"SEARCH-ONLY MODE (No export credits needed!)")
        print(f"{'=' * 80}")
        print(f"Extracting up to {max_results} contacts...")
        print(f"Press Ctrl+C anytime to stop and save progress\n")

        try:
            while total_fetched < max_results:
                search_params["page_size"] = min(page_size, max_results - total_fetched)
                search_params["start"] = current_start

                print(f"Searching page {current_start} (fetched {total_fetched} so far)...")
                profiles = self.search_people(search_params)

                if not profiles:
                    if total_fetched == 0:
                        print("\n⚠️  No results found. Try broadening your search.")
                        return pd.DataFrame()
                    else:
                        print("No more results.")
                        break

                # Process profiles
                for i, profile in enumerate(profiles):
                    person_id = str(profile.get("id", ""))
                    linkedin_url = profile.get("linkedin_url", "")

                    # Check duplicates
                    if person_id in self.contacted_ids or linkedin_url in self.contacted_ids:
                        print(f"  Skipping {profile.get('name', 'Unknown')} - Already contacted")
                        continue

                    # Extract data from SEARCH response (no lookup needed!)
                    name = profile.get("name", "")
                    name_parts = name.split()
                    first_name = name_parts[0] if name_parts else ""
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

                    current_title = profile.get("current_title", "")
                    current_employer = profile.get("current_employer", "")
                    sector = self._classify_sector(current_title, current_employer)

                    # Check if contact preview indicates email availability
                    teaser = profile.get("teaser", {})
                    preview = teaser.get("preview", [])
                    has_personal_email = "personal emails" in str(preview).lower()
                    has_professional_email = "professional emails" in str(preview).lower()

                    contact_entry = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "full_name": name,
                        "current_title": current_title,
                        "current_employer": current_employer,
                        "sector": sector,
                        "location": profile.get("location", ""),
                        "linkedin_url": linkedin_url,
                        "rocketreach_id": person_id,
                        "has_personal_email": has_personal_email,
                        "has_professional_email": has_professional_email,
                        "profile_status": profile.get("status", ""),
                    }

                    all_contacts.append(contact_entry)

                    # Mark as contacted
                    self.contacted_ids.add(person_id)
                    if linkedin_url:
                        self.contacted_ids.add(linkedin_url)

                    print(f"  ✓ {name} ({sector})")

                total_fetched += len(profiles)
                current_start += len(profiles)

                if len(profiles) < page_size:
                    break

                time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n\n⚠️  Interrupted. Saving {len(all_contacts)} contacts...")

        # Save history
        self._save_contact_history()

        if len(all_contacts) == 0:
            print("\n⚠️  No contacts extracted.")
            return pd.DataFrame()

        print(f"\n✓ Extracted {len(all_contacts)} contacts!")
        return pd.DataFrame(all_contacts)

    def export_to_excel(self, df: pd.DataFrame, filename: str = None) -> None:
        """Export to Excel"""
        if filename is None:
            filename = f"contacts_search_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✓ Exported to: {filename}")


# Example usage
if __name__ == "__main__":
    API_KEY = "1ac349bkd05e6c94a51cd27e7070e825a9e3392e"

    extractor = RocketReachSearchOnly(API_KEY)

    # Search criteria
    search_criteria = {
        "query": {
            # "current_title": ["Analyst", "Associate", "Vice President"],
            "current_employer": ["Goldman Sachs", "Morgan Stanley", "McKinsey", "Bain"],
            # "location": ["New York", "Singapore"],
            # "school": ["National University of Singapore"],
        }
    }

    # Extract (NO export credits needed!)
    contacts_df = extractor.extract_contacts_search_only(search_criteria, max_results=100)

    if not contacts_df.empty:
        # Show sector breakdown
        print("\n📊 Sector Breakdown:")
        print(contacts_df['sector'].value_counts())

        # Export
        extractor.export_to_excel(contacts_df, "contacts_search_only.xlsx")

        print("\n" + "=" * 80)
        print("WHAT TO DO NEXT:")
        print("=" * 80)
        print("1. Open contacts_search_only.xlsx")
        print("2. You have LinkedIn URLs for everyone!")
        print("3. Connect with them on LinkedIn")
        print("4. Send InMail or connection requests")
        print("5. Use Hunter.io to find emails based on name + company")
        print("6. Once you get export credits, use the main script")
        print("=" * 80)
