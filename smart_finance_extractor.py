#!/usr/bin/env python3
"""
Smart Finance Contact Extractor with Geographic Distribution
Prioritizes contacts from finance companies with intelligent location-based distribution
"""

import requests
import pandas as pd
import time
from datetime import datetime
import json
import os
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from pathlib import Path

class SmartFinanceExtractor:
    def __init__(self, api_key: str, history_file: str = "contact_history.json"):
        """Initialize with smart distribution logic"""
        self.api_key = api_key
        self.base_url = "https://api.rocketreach.co/v2/api"
        self.headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }

        # Rate limiting tracking
        # Your actual RocketReach limits:
        # - Searches: 15/min, 50/hour, 500/day, 10,000/month
        # - Lookups: Same as searches (unified limit)
        self.api_calls = []  # Track all API calls together

        # Conservative limits (to avoid 429 errors)
        self.rate_limits = {
            'minute': {'limit': 12, 'window': 60},        # 12 of 15 (80%)
            'hour': {'limit': 40, 'window': 3600},        # 40 of 50 (80%)
            'day': {'limit': 400, 'window': 86400},       # 400 of 500 (80%)
            'month': {'limit': 8000, 'window': 2592000}   # 8000 of 10,000 (80%)
        }

        # Location tiers with priorities (3:2:1 ratio)
        self.location_tiers = {
            'tier1': {
                'locations': ['Singapore', 'Hong Kong', 'Paris'],
                'quota_per_company': 3,  # 3 people per location for tier 1
                'priority': 1
            },
            'tier2': {
                'locations': ['London', 'Luxembourg', 'Geneva'],
                'quota_per_company': 2,  # 2 people per location for tier 2
                'priority': 2
            },
            'tier3': {
                'locations': ['Shanghai', 'Zurich'],
                'quota_per_company': 1,  # 1 person per location for tier 3
                'priority': 3
            }
        }

        # Top-level positions to target
        self.target_positions = [
            "Managing Director",
            "Vice President", "VP",
            "Director",
            "Portfolio Manager",
            "Head of",
            "Chief", "CEO", "CFO", "CIO", "COO", "CTO",  # C-Suite
            "Partner",
            "Senior Vice President", "SVP",
            "Executive Director",
            "General Partner", "GP",
            "Managing Partner"
        ]

        # Finance companies to target (customized list)
        self.finance_companies = {
            "Investment Banking": [
                # Bulge Bracket
                "Goldman Sachs",
                "J.P. Morgan",
                "JPMorgan Chase",
                "Morgan Stanley",
                "Bank of America Merrill Lynch",
                "Bank of America",
                "Merrill Lynch",
                "Citigroup",
                "Citi",
                "Barclays",
                "UBS",
                "Credit Suisse",
                "Deutsche Bank",
                "BNP Paribas",
                "Société Générale",
                "Societe Generale",
                # Elite Boutiques
                "Evercore",
                "Lazard",
                "Moelis & Company",
                "Moelis",
                "PJT Partners",
                "Houlihan Lokey",
                "Rothschild & Co",
                "Rothschild",
                "Jefferies",
                "Perella Weinberg Partners",
                "Greenhill"
            ],
            "Hedge Fund": [
                "Bridgewater Associates",
                "Citadel",
                "Point72 Asset Management",
                "Point72",
                "Millennium Management",
                "D.E. Shaw",
                "Elliott Management",
                "Baupost Group",
                "Tiger Global Management",
                "Tiger Global",
                "Viking Global Investors",
                "Viking Global",
                "Third Point",
                "Pershing Square Capital",
                "Lone Pine Capital",
                "Coatue Management",
                "Coatue"
            ],
            "Private Equity": [
                "Blackstone",
                "KKR",
                "Apollo Global Management",
                "Apollo Global",
                "Carlyle Group",
                "TPG Capital",
                "Vista Equity Partners",
                "EQT Partners",
                "Hellman & Friedman",
                "Silver Lake Partners",
                "Silver Lake",
                "General Atlantic",
                "Warburg Pincus",
                "Advent International",
                "CVC Capital Partners"
            ],
            "Consulting": [
                "McKinsey & Company",
                "McKinsey",
                "Boston Consulting Group",
                "BCG",
                "Bain & Company",
                "Bain",
                "Oliver Wyman",
                "Roland Berger",
                "Strategy&",
                "EY-Parthenon",
                "LEK Consulting",
                "L.E.K. Consulting",
                "Alvarez & Marsal"
            ],
            "Venture Capital": [
                "Sequoia Capital",
                "Andreessen Horowitz",
                "a16z",
                "Accel",
                "Insight Partners",
                "B Capital",
                "General Catalyst",
                "Index Ventures",
                "Lightspeed Venture Partners",
                "Peak XV Partners",
                "Wavemaker Partners",
                "Tiger Global",  # Hybrid HF/VC
                "SoftBank Vision Fund",
                "Coatue"  # Hybrid HF/VC
            ]
        }

        # Flatten company list for easy access
        self.all_companies = []
        for sector, companies in self.finance_companies.items():
            self.all_companies.extend(companies)

        # Load contacted history
        self.history_file = history_file
        self.contacted_people = self._load_contacted_history()

        # Track distribution per company
        self.company_distribution = defaultdict(lambda: defaultdict(int))

    def _load_contacted_history(self) -> Set[str]:
        """Load all previously contacted people from multiple sources"""
        contacted = set()

        # Load from history file
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    contacted.update(data.get("contacted_ids", []))
            except Exception as e:
                print(f"Warning: Could not load contact history: {e}")

        # Load from Compiled_names.xlsx
        if os.path.exists("Compiled_names.xlsx"):
            try:
                df = pd.read_excel("Compiled_names.xlsx")
                if 'Name' in df.columns:
                    names = df['Name'].dropna().str.lower().str.strip()
                    contacted.update(names)
                if 'Email contact' in df.columns:
                    emails = df['Email contact'].dropna().str.lower().str.strip()
                    contacted.update(emails)
                print(f"✓ Loaded {len(df)} contacts from Compiled_names.xlsx")
            except Exception as e:
                print(f"Warning: Could not load Compiled_names.xlsx: {e}")

        # Load from HF.xlsx
        if os.path.exists("HF.xlsx"):
            try:
                df = pd.read_excel("HF.xlsx")
                # Skip header row and get names from Column1
                if 'Column1' in df.columns:
                    names = df['Column1'].iloc[1:].dropna().str.lower().str.strip()
                    contacted.update(names)
                print(f"✓ Loaded {len(df)-1} contacts from HF.xlsx")
            except Exception as e:
                print(f"Warning: Could not load HF.xlsx: {e}")

        print(f"\n📊 Total previously contacted people: {len(contacted)}")
        return contacted

    def _is_already_contacted(self, name: str, email: str = None, linkedin: str = None) -> bool:
        """Check if person was already contacted"""
        identifiers = [
            name.lower().strip() if name else None,
            email.lower().strip() if email else None,
            linkedin.lower().strip() if linkedin else None
        ]

        for identifier in identifiers:
            if identifier and identifier in self.contacted_people:
                return True
        return False

    def _matches_target_position(self, title: str) -> bool:
        """Check if title matches target senior positions"""
        if not title:
            return False

        title_lower = title.lower()

        for position in self.target_positions:
            if position.lower() in title_lower:
                return True

        return False

    def _get_location_tier(self, location: str) -> Tuple[str, int]:
        """Determine which tier a location belongs to"""
        if not location:
            return None, 0

        location_lower = location.lower()

        for tier_name, tier_data in self.location_tiers.items():
            for target_loc in tier_data['locations']:
                if target_loc.lower() in location_lower:
                    return tier_name, tier_data['quota_per_company']

        return None, 0

    def _should_fetch_from_location(self, company: str, location: str) -> bool:
        """Check if we should fetch more people from this company/location combination"""
        tier, quota = self._get_location_tier(location)

        if tier is None:
            return False

        current_count = self.company_distribution[company][location]
        return current_count < quota

    def _wait_for_rate_limit(self):
        """
        Smart rate limiting - checks all time windows
        Your limits: 15/min, 50/hour, 500/day, 10,000/month
        """
        now = time.time()

        # Clean up old calls (older than 1 month)
        month_ago = now - 2592000
        self.api_calls[:] = [t for t in self.api_calls if t > month_ago]

        # Check each time window - wait if we're at ANY limit
        for window_name, limits in self.rate_limits.items():
            window_size = limits['window']
            limit = limits['limit']

            # Count calls within this window
            window_start = now - window_size
            calls_in_window = [t for t in self.api_calls if t > window_start]

            # If we're at the limit, wait
            if len(calls_in_window) >= limit:
                oldest_call = calls_in_window[0]
                sleep_time = window_size - (now - oldest_call) + 2  # +2 for safety buffer

                if sleep_time > 0:
                    print(f"⏳ Rate limit ({window_name}): {len(calls_in_window)}/{limit} - waiting {sleep_time:.0f}s...")
                    time.sleep(sleep_time)
                    now = time.time()  # Update time after sleep

                    # Re-clean the call list after sleep
                    self.api_calls[:] = [t for t in self.api_calls if now - t < window_size]

    def _record_api_call(self):
        """Record that an API call was made"""
        self.api_calls.append(time.time())

    def get_rate_limit_status(self) -> Dict[str, Dict]:
        """Get current rate limit usage"""
        now = time.time()
        status = {}

        for window_name, limits in self.rate_limits.items():
            window_size = limits['window']
            limit = limits['limit']
            window_start = now - window_size
            calls_in_window = [t for t in self.api_calls if t > window_start]

            status[window_name] = {
                'used': len(calls_in_window),
                'limit': limit,
                'remaining': limit - len(calls_in_window),
                'percentage': (len(calls_in_window) / limit * 100) if limit > 0 else 0
            }

        return status

    def search_company_location(self, company: str, location: str,
                               page_size: int = 10) -> List[Dict]:
        """Search for contacts at a specific company and location"""

        self._wait_for_rate_limit()

        # Build search query
        query = {
            "current_employer": [company],
            "location": [location]
        }

        # Add position filter
        # Note: RocketReach might not support all these filters,
        # so we'll filter results after fetching

        params = {
            "query": query,
            "page_size": page_size,
            "start": 1
        }

        try:
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json=params,
                timeout=30
            )

            # Record the API call was made
            self._record_api_call()

            # Accept both 200 (OK) and 201 (Created) as success
            if response.status_code in [200, 201]:
                data = response.json()
                profiles = data.get('profiles', [])

                # Filter for senior positions only
                senior_profiles = [
                    p for p in profiles
                    if self._matches_target_position(p.get('current_title', ''))
                ]

                return senior_profiles
            else:
                print(f"⚠️  Search error for {company} in {location}: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"       Error details: {error_data}")
                except:
                    print(f"       Response text: {response.text[:200]}")
                return []

        except Exception as e:
            print(f"❌ Error searching {company} in {location}: {e}")
            return []

    def lookup_person(self, profile_id: str) -> Dict:
        """Get detailed info for a person"""

        self._wait_for_rate_limit()

        try:
            response = requests.get(
                f"{self.base_url}/lookupProfile",
                headers=self.headers,
                params={"id": profile_id},
                timeout=30
            )

            # Record the API call was made
            self._record_api_call()

            # Accept both 200 (OK) and 201 (Created) as success
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"⚠️  Lookup error: {response.status_code}")
                return {}

        except Exception as e:
            print(f"❌ Lookup error: {e}")
            return {}

    def extract_with_distribution(self, companies_to_search: List[str] = None,
                                  max_per_company: int = 20,
                                  max_total_contacts: int = None) -> pd.DataFrame:
        """
        Extract contacts with smart geographic distribution

        Args:
            companies_to_search: List of companies to search
            max_per_company: Maximum contacts per company (default 20)
            max_total_contacts: Maximum total contacts to extract (default None = unlimited)

        For each company:
        - Fetch 3 people from each Tier 1 location (Singapore, Hong Kong, Paris)
        - Fetch 2 people from each Tier 2 location (London, Luxembourg, Geneva)
        - Fetch 1 person from each Tier 3 location (Shanghai, Zurich)
        """

        if companies_to_search is None:
            companies_to_search = self.all_companies

        all_contacts = []
        total_extracted = 0

        print("=" * 80)
        print("SMART FINANCE CONTACT EXTRACTION")
        print("=" * 80)
        print(f"\n📍 Location Priority System:")
        print(f"   Tier 1 (3 per location): {', '.join(self.location_tiers['tier1']['locations'])}")
        print(f"   Tier 2 (2 per location): {', '.join(self.location_tiers['tier2']['locations'])}")
        print(f"   Tier 3 (1 per location): {', '.join(self.location_tiers['tier3']['locations'])}")
        print(f"\n🎯 Target Positions: {', '.join(self.target_positions[:5])}...")
        print(f"\n🏢 Companies to search: {len(companies_to_search)}")
        print(f"🚫 Already contacted: {len(self.contacted_people)} people")
        if max_total_contacts:
            print(f"🎯 Max total contacts: {max_total_contacts}")
        print(f"📊 Max per company: {max_per_company}")
        print("=" * 80)

        # Process each company
        for company_idx, company in enumerate(companies_to_search, 1):
            # Check if we've reached max total contacts
            if max_total_contacts and total_extracted >= max_total_contacts:
                print(f"\n\n🎯 Reached max total contacts limit ({max_total_contacts})")
                print(f"✅ Stopping extraction")
                break

            print(f"\n\n{'='*80}")
            print(f"[{company_idx}/{len(companies_to_search)}] Processing: {company}")
            print(f"Total extracted so far: {total_extracted}" + (f"/{max_total_contacts}" if max_total_contacts else ""))
            print(f"{'='*80}")

            company_contacts = []

            # Process locations by tier (priority order)
            for tier_name in ['tier1', 'tier2', 'tier3']:
                tier_data = self.location_tiers[tier_name]
                locations = tier_data['locations']
                quota = tier_data['quota_per_company']

                print(f"\n  📍 Tier {tier_data['priority']} Locations (quota: {quota} each):")

                for location in locations:
                    print(f"\n    🌍 {location}...")

                    # Check if we need more from this location
                    current_count = self.company_distribution[company][location]
                    needed = quota - current_count

                    if needed <= 0:
                        print(f"       ✓ Quota met ({current_count}/{quota})")
                        continue

                    # Search for people
                    profiles = self.search_company_location(
                        company,
                        location,
                        page_size=needed * 3  # Get more to account for filtering
                    )

                    if not profiles:
                        print(f"       ⚠️  No profiles found")
                        continue

                    print(f"       Found {len(profiles)} senior profiles")

                    # Process each profile
                    fetched_count = 0
                    for profile in profiles:
                        # Check max total limit
                        if max_total_contacts and total_extracted >= max_total_contacts:
                            print(f"       🎯 Max total contacts reached ({max_total_contacts})")
                            break

                        if fetched_count >= needed:
                            break

                        name = profile.get('name', '')
                        title = profile.get('current_title', '')
                        profile_id = profile.get('id', '')

                        # Skip if already contacted
                        if self._is_already_contacted(name):
                            print(f"       ⏭️  Skipping {name} (already contacted)")
                            continue

                        # Get detailed info
                        print(f"       🔍 Fetching: {name} - {title}")
                        detailed = self.lookup_person(profile_id)

                        if detailed:
                            # Extract contact info
                            contact = self._extract_contact_data(detailed, company, location)

                            if contact:
                                company_contacts.append(contact)
                                fetched_count += 1
                                total_extracted += 1
                                self.company_distribution[company][location] += 1

                                print(f"       ✅ Added ({fetched_count}/{needed}) [Total: {total_extracted}]")

                                # Check if we hit max total
                                if max_total_contacts and total_extracted >= max_total_contacts:
                                    print(f"       🎯 Reached max total contacts ({max_total_contacts})")
                                    break

                    print(f"       📊 Final: {self.company_distribution[company][location]}/{quota}")

            # Add company contacts to results
            all_contacts.extend(company_contacts)

            print(f"\n  💼 Total from {company}: {len(company_contacts)} contacts")

            # Stop if we've reached max per company
            if len(company_contacts) >= max_per_company:
                print(f"  🎯 Reached max per company ({max_per_company})")

        # Create DataFrame
        if all_contacts:
            df = pd.DataFrame(all_contacts)

            # Summary statistics
            print("\n\n" + "=" * 80)
            print("EXTRACTION SUMMARY")
            print("=" * 80)
            print(f"Total contacts extracted: {len(df)}")
            print(f"\nBy Location:")
            print(df['location'].value_counts())
            print(f"\nBy Company:")
            print(df['current_employer'].value_counts())
            print("=" * 80)

            return df
        else:
            print("\n⚠️  No contacts extracted")
            return pd.DataFrame()

    def _extract_contact_data(self, profile_data: Dict, company: str, location: str) -> Dict:
        """Extract relevant data from profile"""
        try:
            name = profile_data.get('name', '')
            name_parts = name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            # Get emails
            emails = profile_data.get('emails', [])
            primary_email = emails[0] if emails else ""

            # Mark as contacted
            if name:
                self.contacted_people.add(name.lower().strip())
            if primary_email:
                self.contacted_people.add(primary_email.lower().strip())

            return {
                "first_name": first_name,
                "last_name": last_name,
                "full_name": name,
                "current_title": profile_data.get('current_title', ''),
                "current_employer": company,
                "location": location,
                "primary_email": primary_email,
                "all_emails": ", ".join(emails),
                "linkedin_url": profile_data.get('linkedin_url', ''),
                "phone": ", ".join(profile_data.get('phones', [])),
                "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"       ⚠️  Error extracting data: {e}")
            return None

    def save_results(self, df: pd.DataFrame, filename: str = "smart_finance_contacts.xlsx"):
        """Save results to Excel with formatting"""
        if df.empty:
            print("No data to save")
            return

        try:
            # Save to Excel
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"\n✅ Results saved to: {filename}")

            # Also save updated contact history
            self._save_contact_history()

        except Exception as e:
            print(f"❌ Error saving: {e}")

    def _save_contact_history(self):
        """Save contacted people to history file"""
        try:
            data = {
                "contacted_ids": list(self.contacted_people),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save contact history: {e}")


# Main execution
if __name__ == "__main__":
    # Get API key from environment or prompt
    api_key = os.getenv("ROCKETREACH_API_KEY")

    if not api_key:
        print("Please set ROCKETREACH_API_KEY environment variable")
        print("Or edit this script to add your API key directly")
        exit(1)

    # Initialize extractor
    extractor = SmartFinanceExtractor(api_key)

    # Option 1: Search specific companies (recommended for testing)
    target_companies = [
        # Investment Banks
        "Goldman Sachs",
        "Morgan Stanley",
        "J.P. Morgan",

        # Private Equity
        "Blackstone",
        "KKR",

        # Hedge Funds
        "Citadel",
        "Bridgewater Associates",

        # Consulting
        "McKinsey & Company",
        "Boston Consulting Group",

        # Venture Capital
        "Sequoia Capital",
        "Andreessen Horowitz"
    ]

    # Option 2: Search ALL finance companies (80+ companies)
    # target_companies = extractor.all_companies

    # Option 3: Search by sector
    # target_companies = extractor.finance_companies["Investment Banking"]
    # target_companies = extractor.finance_companies["Hedge Fund"]
    # target_companies = extractor.finance_companies["Private Equity"]
    # target_companies = extractor.finance_companies["Consulting"]
    # target_companies = extractor.finance_companies["Venture Capital"]

    # CONFIGURATION: Set your extraction limits here
    MAX_TOTAL_CONTACTS = 500      # Stop after extracting this many contacts (None = unlimited)
    MAX_PER_COMPANY = 20          # Maximum contacts per company

    print("\n🤖 AUTOMATED EXTRACTION MODE")
    print("=" * 80)
    print("This script will run fully automatically in the background.")
    print("It will handle rate limits by waiting and resuming automatically.")
    print(f"Max total contacts: {MAX_TOTAL_CONTACTS if MAX_TOTAL_CONTACTS else 'Unlimited'}")
    print(f"Max per company: {MAX_PER_COMPANY}")
    print("=" * 80)
    print("\nYou can minimize this window and do other work.")
    print("The script will save results when done.\n")

    # Extract with smart distribution
    try:
        results_df = extractor.extract_with_distribution(
            companies_to_search=target_companies,
            max_per_company=MAX_PER_COMPANY,
            max_total_contacts=MAX_TOTAL_CONTACTS
        )

        # Save results
        if not results_df.empty:
            extractor.save_results(results_df, "smart_finance_contacts.xlsx")
            print("\n🎉 Extraction complete!")
            print(f"📊 Total contacts extracted: {len(results_df)}")
            print(f"💾 Results saved to: smart_finance_contacts.xlsx")
        else:
            print("\n⚠️  No contacts extracted")

    except KeyboardInterrupt:
        print("\n\n⚠️  Extraction interrupted by user")
        if all_contacts:
            print("💾 Saving partial results...")
            df = pd.DataFrame(all_contacts)
            extractor.save_results(df, "smart_finance_contacts_partial.xlsx")
            print(f"✅ Partial results saved ({len(df)} contacts)")

    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        print("Check your API key and internet connection")
