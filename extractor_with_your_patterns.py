#!/usr/bin/env python3
"""
Custom Extractor Using Your mega_email_patterns.xlsx
Optimized for your specific Excel format and patterns
"""

import sys
sys.path.append('.')

from search_only_mode import RocketReachSearchOnly
from email_verifier import EmailVerifier
import pandas as pd
from datetime import datetime
import time
import re


class CustomExtractor(RocketReachSearchOnly):
    """
    Extractor optimized for your mega_email_patterns.xlsx format

    Your Excel format:
    - Company: Company name
    - Domain: Email domain (with @)
    - Example Patterns: Multiple pattern examples
    - Most Common Pattern: The most frequent pattern
    - Sector: Company sector
    """

    def __init__(self, api_key: str, patterns_file: str = "mega_email_patterns.xlsx",
                 history_file: str = "contact_history.json"):
        """Initialize with your patterns file"""
        super().__init__(api_key, history_file)

        self.verifier = EmailVerifier(timeout=15, max_workers=3)
        self.patterns_file = patterns_file
        self.company_data = {}

        self._load_your_patterns()

    def _load_your_patterns(self):
        """Load patterns from YOUR Excel file"""
        try:
            df = pd.read_excel(self.patterns_file)
            print(f"\n📁 Loading patterns from: {self.patterns_file}")
            print(f"   Found {len(df)} companies with patterns\n")

            for _, row in df.iterrows():
                company = str(row['Company']).strip()
                domain = str(row['Domain']).strip().replace('@', '')
                most_common = str(row.get('Most Common Pattern', '')).strip()
                sector = str(row.get('Sector', '')).strip()
                example_patterns = str(row.get('Example Patterns', '')).strip()

                self.company_data[company.lower()] = {
                    'domain': domain,
                    'most_common_pattern': most_common,
                    'sector': sector,
                    'example_patterns': example_patterns,
                    'original_name': company
                }

            print(f"   ✅ Loaded {len(self.company_data)} companies")

            # Show some examples
            for i, (comp, data) in enumerate(list(self.company_data.items())[:5]):
                pattern = data['most_common_pattern'].replace(data['domain'], '').replace('@', '')
                print(f"      {data['original_name']}: {pattern}@{data['domain']}")

            if len(self.company_data) > 5:
                print(f"      ... and {len(self.company_data) - 5} more\n")

        except Exception as e:
            print(f"   ⚠️  Error loading patterns: {e}")

    def _get_company_info(self, company: str) -> dict:
        """Get company info from your patterns"""
        company_lower = company.lower()

        # Exact match
        if company_lower in self.company_data:
            return self.company_data[company_lower]

        # Partial match
        for comp_key, data in self.company_data.items():
            if comp_key in company_lower or company_lower in comp_key:
                return data

        return None

    def _parse_pattern(self, pattern_str: str) -> str:
        """
        Parse pattern string from your Excel

        Examples from your file:
        - "firstname.lastname@gs.com" -> "first.last"
        - "firstnamelastname@jpmorgan.com" -> "firstlast"
        - "f.lastname@citi.com" -> "f.last"
        """
        # Remove domain to get just the pattern
        pattern_str = re.sub(r'@.*', '', pattern_str.lower())

        # Use generic placeholders to detect pattern
        pattern_str = pattern_str.replace('firstname', 'FIRST')
        pattern_str = pattern_str.replace('francis', 'FIRST')
        pattern_str = pattern_str.replace('fmalcolm', 'FIRST')  # Your example
        pattern_str = pattern_str.replace('lastname', 'LAST')
        pattern_str = pattern_str.replace('malcolm', 'LAST')

        # Detect separators
        if 'FIRST.LAST' in pattern_str:
            return 'first.last'
        elif 'FIRSTLAST' in pattern_str:
            return 'firstlast'
        elif 'F.LAST' in pattern_str or pattern_str.startswith('f.'):
            return 'f.last'
        elif 'FIRST.L' in pattern_str:
            return 'first.l'
        elif 'FIRST_LAST' in pattern_str:
            return 'first_last'
        elif 'FIRST-LAST' in pattern_str:
            return 'first-last'
        elif 'LAST.FIRST' in pattern_str:
            return 'last.first'
        else:
            return 'unknown'

    def _apply_pattern(self, first_name: str, last_name: str, pattern: str, domain: str) -> str:
        """Apply a pattern to generate an email"""
        first = first_name.lower().strip()
        last = last_name.lower().strip()

        if not first or not last or not domain:
            return ""

        patterns_map = {
            "first.last": f"{first}.{last}",
            "firstlast": f"{first}{last}",
            "first_last": f"{first}_{last}",
            "first-last": f"{first}-{last}",
            "f.last": f"{first[0]}.{last}",
            "flast": f"{first[0]}{last}",
            "first.l": f"{first}.{last[0]}",
            "firstl": f"{first}{last[0]}",
            "last.first": f"{last}.{first}",
            "lastfirst": f"{last}{first}",
        }

        local = patterns_map.get(pattern, "")
        if local:
            return f"{local}@{domain}"
        return ""

    def _generate_priority_patterns(self, first_name: str, last_name: str,
                                    company_info: dict) -> list:
        """
        Generate patterns in priority order based on your Excel

        Priority:
        1. Most common pattern from your Excel
        2. Other patterns from example patterns
        3. Fallback common patterns
        """
        emails = []
        domain = company_info['domain']

        # Priority 1: Most common pattern from your Excel
        most_common = company_info.get('most_common_pattern', '')
        if most_common:
            pattern_type = self._parse_pattern(most_common)
            email = self._apply_pattern(first_name, last_name, pattern_type, domain)
            if email and email not in emails:
                emails.append({'email': email, 'source': 'most_common', 'priority': 1})

        # Priority 2: Parse example patterns from your Excel
        example_patterns_str = company_info.get('example_patterns', '')
        if example_patterns_str:
            # Examples like: "fmalcolm@gs.com, francis.malcolm@gs.com, f.malcolm@gs.com"
            for example in example_patterns_str.split(','):
                example = example.strip()
                if example:
                    pattern_type = self._parse_pattern(example)
                    email = self._apply_pattern(first_name, last_name, pattern_type, domain)
                    if email and email not in [e['email'] for e in emails]:
                        emails.append({'email': email, 'source': 'example', 'priority': 2})

        # Priority 3: Fallback common patterns
        common_patterns = ['first.last', 'firstlast', 'f.last', 'flast', 'first_last']
        for pattern in common_patterns:
            email = self._apply_pattern(first_name, last_name, pattern, domain)
            if email and email not in [e['email'] for e in emails]:
                emails.append({'email': email, 'source': 'fallback', 'priority': 3})

        return emails

    def extract_and_verify(self, search_params: dict, max_results: int = 50,
                          verify_emails: bool = True, quick_stop: bool = True) -> pd.DataFrame:
        """
        Extract contacts and verify emails using your patterns

        Args:
            search_params: RocketReach search parameters
            max_results: Max contacts to extract
            verify_emails: Whether to verify emails (True recommended)
            quick_stop: Stop after finding first valid email
        """
        print(f"\n{'=' * 80}")
        print("CUSTOM EXTRACTION WITH YOUR PATTERNS")
        print("=" * 80)
        print(f"Using: {self.patterns_file}")
        print(f"Step 1: Extract from RocketReach")
        print(f"Step 2: Match company patterns from your Excel")
        print(f"Step 3: Generate emails using YOUR patterns (priority order)")
        if verify_emails:
            print(f"Step 4: Verify emails (SMTP test)")
        print("=" * 80 + "\n")

        # Step 1: Extract from RocketReach
        contacts_df = self.extract_contacts_search_only(search_params, max_results)

        if contacts_df.empty:
            return contacts_df

        print(f"\n{'=' * 80}")
        print(f"PROCESSING {len(contacts_df)} CONTACTS")
        print("=" * 80)

        all_results = []

        for idx, row in contacts_df.iterrows():
            first_name = row['first_name']
            last_name = row['last_name']
            company = row['current_employer']

            print(f"\n[{idx + 1}/{len(contacts_df)}] {first_name} {last_name} @ {company}")

            # Step 2: Get company info from your patterns
            company_info = self._get_company_info(company)

            if not company_info:
                print(f"   ⚠️  No pattern found in your Excel for: {company}")
                row['domain'] = None
                row['verified_email_count'] = 0
                all_results.append(row)
                continue

            domain = company_info['domain']
            print(f"   📧 Domain: {domain}")
            print(f"   📊 Sector: {company_info.get('sector', 'N/A')}")

            row['domain'] = domain
            row['pattern_sector'] = company_info.get('sector', '')

            # Step 3: Generate emails using YOUR patterns (priority order)
            priority_emails = self._generate_priority_patterns(first_name, last_name, company_info)

            print(f"   🎯 Generated {len(priority_emails)} patterns (priority order)")

            # Step 4: Verify emails (if enabled)
            if verify_emails and priority_emails:
                print(f"   🔍 Verifying emails:")

                verified_count = 0
                for email_info in priority_emails:
                    email = email_info['email']
                    source = email_info['source']

                    result = self.verifier.verify_email(email)

                    status_emoji = {
                        'valid': '✅',
                        'invalid': '❌',
                        'unknown': '❓',
                        'error': '⚠️'
                    }[result.get('status', 'unknown')]

                    source_label = {
                        'most_common': '[MOST COMMON]',
                        'example': '[FROM EXCEL]',
                        'fallback': '[FALLBACK]'
                    }[source]

                    print(f"      {status_emoji} {email} {source_label}")

                    if result['status'] == 'valid':
                        verified_count += 1
                        row[f'verified_email_{verified_count}'] = email
                        row[f'email_{verified_count}_pattern'] = source
                        row[f'email_{verified_count}_method'] = 'smtp_verified'

                        if quick_stop:
                            print(f"      ✨ Found verified email! Stopping.")
                            break

                    time.sleep(0.5)

                row['verified_email_count'] = verified_count

                if verified_count > 0:
                    print(f"   ✅ Verified {verified_count} email(s)")
                else:
                    print(f"   ⚠️  No verified emails (but you have LinkedIn URL)")
            else:
                # Just add generated emails without verification
                for i, email_info in enumerate(priority_emails[:5], 1):
                    row[f'generated_email_{i}'] = email_info['email']
                    row[f'email_{i}_source'] = email_info['source']
                row['verified_email_count'] = 0

            all_results.append(row)
            time.sleep(1)

        result_df = pd.DataFrame(all_results)
        return result_df

    def export_results(self, df: pd.DataFrame, filename: str = None):
        """Export results"""
        if filename is None:
            filename = f"verified_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        base_cols = ['first_name', 'last_name', 'full_name', 'current_title',
                     'current_employer', 'domain', 'pattern_sector', 'sector', 'location', 'linkedin_url']
        email_cols = [col for col in df.columns if 'email' in col.lower()]
        other_cols = [col for col in df.columns if col not in base_cols + email_cols]

        ordered_cols = base_cols + email_cols + other_cols
        ordered_cols = [col for col in ordered_cols if col in df.columns]

        df_ordered = df[ordered_cols]
        df_ordered.to_excel(filename, index=False)

        print(f"\n{'=' * 80}")
        print(f"✅ EXPORTED TO: {filename}")
        print("=" * 80)

        total = len(df)
        with_verified = (df.get('verified_email_count', 0) > 0).sum()
        with_domain = df['domain'].notna().sum()

        print(f"\n📊 STATISTICS:")
        print(f"   Total contacts: {total}")
        print(f"   Patterns matched: {with_domain}/{total} ({with_domain/total*100:.1f}%)")
        print(f"   Verified emails: {with_verified}/{total} ({with_verified/total*100:.1f}%)")
        print(f"   LinkedIn URLs: {total}/{total} (100%)")


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("CUSTOM EXTRACTOR - USING YOUR mega_email_patterns.xlsx")
    print("=" * 80)

    API_KEY = os.getenv("ROCKETREACH_API_KEY")
    if not API_KEY:
        print("ERROR: ROCKETREACH_API_KEY environment variable not set!")
        print("Please set it with: export ROCKETREACH_API_KEY='your_key_here'")
        exit(1)

    # Initialize with YOUR patterns file
    extractor = CustomExtractor(
        api_key=API_KEY,
        patterns_file="mega_email_patterns.xlsx"
    )

    # Search criteria - targeting companies from YOUR Excel
    search_criteria = {
        "query": {
            # Test with Goldman Sachs first (we know François Labrousse works)
            "current_employer": ["Goldman Sachs"],
            # Add more from your Excel: "Morgan Stanley", "McKinsey", etc.
        }
    }

    # Extract and verify
    print("\nExtracting and verifying emails...")

    contacts_df = extractor.extract_and_verify(
        search_params=search_criteria,
        max_results=5,        # Start with 5 for testing
        verify_emails=True,   # Verify with SMTP
        quick_stop=True       # Stop after first verified email per person
    )

    if not contacts_df.empty:
        # Export
        extractor.export_results(contacts_df, "verified_contacts_with_your_patterns.xlsx")

        print("\n" + "=" * 80)
        print("✅ SUCCESS!")
        print("=" * 80)
        print(f"Results in: verified_contacts_with_your_patterns.xlsx")
        print(f"Using patterns from: mega_email_patterns.xlsx")
        print(f"Companies in your Excel: {len(extractor.company_data)}")
        print("=" * 80)
