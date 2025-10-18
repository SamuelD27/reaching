#!/usr/bin/env python3
"""
Complete Contact Extractor with Email Verification
Combines everything:
1. RocketReach search (names, companies, LinkedIn)
2. Domain patterns from your Excel
3. Generate ALL possible emails
4. Verify which ones actually exist
5. Export only verified emails
"""

import sys
sys.path.append('.')

from search_only_mode import RocketReachSearchOnly
from email_verifier import EmailVerifier
from email_pattern_generator import EmailPatternGenerator
import pandas as pd
from datetime import datetime
from typing import List, Dict
import time


class CompleteExtractor(RocketReachSearchOnly):
    """
    Complete extraction with verification

    Process:
    1. Search RocketReach for contacts
    2. Load domain patterns from your Excel
    3. Generate all possible email patterns
    4. Verify each email (does it exist?)
    5. Export only verified emails + LinkedIn URLs
    """

    def __init__(self, api_key: str, domain_patterns_file: str = None,
                 history_file: str = "contact_history.json"):
        """
        Initialize complete extractor

        Args:
            api_key: RocketReach API key
            domain_patterns_file: Excel with company domains
            history_file: Contact history for duplicates
        """
        super().__init__(api_key, history_file)

        self.verifier = EmailVerifier(timeout=10, max_workers=3)
        self.generator = EmailPatternGenerator()

        # Load domain patterns from Excel
        self.domain_patterns = {}
        if domain_patterns_file:
            self._load_domain_patterns(domain_patterns_file)

        # All possible patterns to test
        self.all_patterns = [
            "first.last", "firstlast", "f.last", "flast",
            "first.l", "firstl", "first_last", "first-last",
            "last.first", "lastfirst", "last.f", "lastf",
            "l.first", "lfirst", "last_first", "last-first",
            "f_last", "f-last", "first_l", "first-l",
            "last_f", "last-f", "first", "last", "f.l", "fl"
        ]

    def _load_domain_patterns(self, filename: str):
        """
        Load company domains from Excel

        Expected columns:
        - company (or Company Name)
        - domain (or Domain)
        """
        try:
            df = pd.read_excel(filename)
            print(f"\n📁 Loading domain patterns from: {filename}")
            print(f"   Found {len(df)} companies")

            # Find company and domain columns (flexible naming)
            company_col = None
            domain_col = None

            for col in df.columns:
                col_lower = col.lower()
                if 'company' in col_lower or 'firm' in col_lower or 'name' in col_lower:
                    company_col = col
                if 'domain' in col_lower or 'email' in col_lower:
                    domain_col = col

            if not company_col or not domain_col:
                print(f"   ⚠️  Could not find company/domain columns")
                print(f"   Columns found: {list(df.columns)}")
                return

            # Build mapping
            for _, row in df.iterrows():
                company = str(row[company_col]).strip()
                domain = str(row[domain_col]).strip().lower()

                # Clean domain (remove @ or https:// if present)
                domain = domain.replace('@', '').replace('https://', '').replace('http://', '').replace('www.', '')

                if company and domain and domain != 'nan':
                    self.domain_patterns[company.lower()] = domain

            print(f"   ✅ Loaded {len(self.domain_patterns)} domain patterns")

            # Show some examples
            for i, (comp, dom) in enumerate(list(self.domain_patterns.items())[:5]):
                print(f"      {comp}: {dom}")
            if len(self.domain_patterns) > 5:
                print(f"      ... and {len(self.domain_patterns) - 5} more")

        except Exception as e:
            print(f"   ⚠️  Error loading domain patterns: {e}")

    def _get_domain_for_company(self, company: str) -> str:
        """Get email domain for a company"""
        company_lower = company.lower()

        # Exact match
        if company_lower in self.domain_patterns:
            return self.domain_patterns[company_lower]

        # Partial match
        for comp, domain in self.domain_patterns.items():
            if comp in company_lower or company_lower in comp:
                return domain

        return None

    def _generate_all_emails(self, first_name: str, last_name: str, domain: str) -> List[str]:
        """Generate all possible email patterns"""
        emails = []
        first = first_name.lower().strip()
        last = last_name.lower().strip()

        if not first or not last or not domain:
            return []

        for pattern in self.all_patterns:
            email = self.generator._apply_pattern(first_name, last_name, pattern, domain)
            if email and email not in emails:
                emails.append(email)

        return emails

    def _verify_emails(self, emails: List[str], quick_stop: bool = True) -> List[Dict]:
        """
        Verify a list of emails, return only valid ones

        Args:
            emails: List of emails to verify
            quick_stop: Stop after finding first valid email

        Returns:
            List of verified emails with details
        """
        verified = []

        for email in emails:
            result = self.verifier.verify_email(email)

            status_emoji = {
                'valid': '✅',
                'invalid': '❌',
                'unknown': '❓',
                'error': '⚠️'
            }[result.get('status', 'unknown')]

            print(f"      {status_emoji} {email}")

            if result['status'] == 'valid':
                verified.append({
                    'email': email,
                    'pattern': self.generator._detect_pattern(email, "", ""),
                    'verified': True,
                    'method': 'smtp'
                })

                if quick_stop:
                    print(f"      Found valid email! Stopping pattern test.")
                    break

            # Rate limiting
            time.sleep(0.5)

        return verified

    def extract_with_verification(self, search_params: Dict, max_results: int = 500,
                                  verify_emails: bool = True, quick_stop: bool = True) -> pd.DataFrame:
        """
        Extract contacts and verify emails

        Args:
            search_params: RocketReach search parameters
            max_results: Max contacts to extract
            verify_emails: Whether to verify emails (slower but accurate)
            quick_stop: Stop after finding first valid email per person

        Returns:
            DataFrame with verified emails
        """
        print(f"\n{'=' * 80}")
        print("COMPLETE CONTACT EXTRACTION WITH EMAIL VERIFICATION")
        print("=" * 80)
        print(f"Step 1: Extract from RocketReach")
        print(f"Step 2: Match company domains")
        print(f"Step 3: Generate all possible emails")
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

            # Step 2: Get domain
            domain = self._get_domain_for_company(company)

            if not domain:
                print(f"   ⚠️  No domain pattern found for {company}")
                row['domain'] = None
                row['verified_email_count'] = 0
                all_results.append(row)
                continue

            print(f"   Domain: {domain}")
            row['domain'] = domain

            # Step 3: Generate all possible emails
            all_emails = self._generate_all_emails(first_name, last_name, domain)
            print(f"   Generated {len(all_emails)} patterns")

            row['patterns_generated'] = len(all_emails)

            # Step 4: Verify emails (if enabled)
            if verify_emails and all_emails:
                print(f"   Verifying emails:")
                verified = self._verify_emails(all_emails, quick_stop=quick_stop)

                if verified:
                    for i, email_info in enumerate(verified[:5], 1):
                        row[f'verified_email_{i}'] = email_info['email']
                        row[f'email_{i}_pattern'] = email_info['pattern']
                        row[f'email_{i}_method'] = 'smtp_verified'

                    # Learn this pattern
                    self.generator.add_example(
                        company=company,
                        email=verified[0]['email'],
                        first_name=first_name,
                        last_name=last_name
                    )

                row['verified_email_count'] = len(verified)
            else:
                # Just add generated emails without verification
                for i, email in enumerate(all_emails[:5], 1):
                    row[f'generated_email_{i}'] = email
                row['verified_email_count'] = 0

            all_results.append(row)

            # Rate limiting between people
            time.sleep(1)

        # Save learned patterns
        self.generator.save_examples()
        print(f"\n✅ Saved learned patterns to email_examples.json")

        result_df = pd.DataFrame(all_results)
        return result_df

    def export_results(self, df: pd.DataFrame, filename: str = None):
        """Export results with verified emails"""
        if filename is None:
            filename = f"verified_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # Reorder columns
        base_cols = ['first_name', 'last_name', 'full_name', 'current_title',
                     'current_employer', 'domain', 'sector', 'location', 'linkedin_url']
        email_cols = [col for col in df.columns if 'email' in col.lower()]
        other_cols = [col for col in df.columns if col not in base_cols + email_cols]

        ordered_cols = base_cols + email_cols + other_cols
        ordered_cols = [col for col in ordered_cols if col in df.columns]

        df_ordered = df[ordered_cols]
        df_ordered.to_excel(filename, index=False)

        print(f"\n{'=' * 80}")
        print(f"✅ EXPORTED TO: {filename}")
        print("=" * 80)

        # Statistics
        total = len(df)
        with_verified = (df.get('verified_email_count', 0) > 0).sum()
        with_domain = df['domain'].notna().sum()

        print(f"\n📊 STATISTICS:")
        print(f"   Total contacts: {total}")
        print(f"   Domains matched: {with_domain} ({with_domain/total*100:.1f}%)")
        print(f"   Verified emails: {with_verified} ({with_verified/total*100:.1f}%)")
        print(f"   No email found: {total - with_verified} ({(total-with_verified)/total*100:.1f}%)")


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("COMPLETE CONTACT EXTRACTOR WITH EMAIL VERIFICATION")
    print("=" * 80)

    API_KEY = os.getenv("ROCKETREACH_API_KEY")
    if not API_KEY:
        print("\nERROR: ROCKETREACH_API_KEY environment variable not set!")
        print("Please set it with: export ROCKETREACH_API_KEY='your_key_here'")
        exit(1)

    # Initialize extractor with domain patterns
    extractor = CompleteExtractor(
        api_key=API_KEY,
        domain_patterns_file="domain_patterns.xlsx"  # Your Excel with domains
    )

    # Search criteria
    search_criteria = {
        "query": {
            "current_employer": ["Goldman Sachs", "Morgan Stanley"],
            # "location": ["New York"],
        }
    }

    # Extract and verify
    print("\nExtracting and verifying emails...")
    print("(This will take longer due to email verification)")

    contacts_df = extractor.extract_with_verification(
        search_params=search_criteria,
        max_results=5,  # Start small for testing
        verify_emails=True,  # Set to False for faster extraction without verification
        quick_stop=True  # Stop after finding first valid email per person
    )

    if not contacts_df.empty:
        # Export
        extractor.export_results(contacts_df, "verified_contacts.xlsx")

        print("\n" + "=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print("1. Review verified_contacts.xlsx")
        print("2. Contacts with verified emails are ready to email!")
        print("3. All contacts have LinkedIn URLs for backup outreach")
        print("4. Verified patterns are saved for future use")
        print("=" * 80)
