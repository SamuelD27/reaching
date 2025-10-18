#!/usr/bin/env python3
"""
Email Pattern Tester
Tests ALL possible email patterns for a person at a company
Finds which ones actually exist using email verification
"""

import sys
sys.path.append('.')

from email_verifier import EmailVerifier
from email_pattern_generator import EmailPatternGenerator
import pandas as pd
from typing import List, Dict
from datetime import datetime
import time


class PatternTester:
    """
    Tests all possible email patterns and finds the real ones

    Process:
    1. Generate all possible email patterns for person + company
    2. Verify each pattern (does it exist?)
    3. Return only the verified ones
    4. Update pattern database with confirmed pattern
    """

    def __init__(self, verifier: EmailVerifier = None, generator: EmailPatternGenerator = None):
        """Initialize with verifier and generator"""
        self.verifier = verifier or EmailVerifier(timeout=10, max_workers=3)
        self.generator = generator or EmailPatternGenerator()

        # All possible patterns to test
        self.all_patterns = [
            "first.last", "firstlast", "f.last", "flast",
            "first.l", "firstl", "first_last", "first-last",
            "last.first", "lastfirst", "last.f", "lastf",
            "l.first", "lfirst", "last_first", "last-first",
            "f_last", "f-last", "first_l", "first-l",
            "last_f", "last-f", "first", "last",
            "f.l", "fl"
        ]

    def generate_all_patterns(self, first_name: str, last_name: str, domain: str) -> List[str]:
        """
        Generate ALL possible email patterns for a person

        Args:
            first_name: First name
            last_name: Last name
            domain: Email domain (e.g., "gs.com")

        Returns:
            List of all possible email addresses
        """
        emails = []
        first = first_name.lower().strip()
        last = last_name.lower().strip()

        if not first or not last or not domain:
            return []

        # Generate using all known patterns
        for pattern in self.all_patterns:
            email = self.generator._apply_pattern(first_name, last_name, pattern, domain)
            if email and email not in emails:
                emails.append(email)

        return emails

    def test_person(self, first_name: str, last_name: str, company: str, domain: str,
                   quick_stop: bool = True) -> Dict[str, any]:
        """
        Test all email patterns for a person and find the real one(s)

        Args:
            first_name: Person's first name
            last_name: Person's last name
            company: Company name
            domain: Email domain (e.g., "gs.com")
            quick_stop: Stop after finding first valid email (faster)

        Returns:
            Dict with results
        """
        print(f"\nTesting: {first_name} {last_name} @ {company}")
        print(f"Domain: {domain}")

        # Generate all possible patterns
        all_emails = self.generate_all_patterns(first_name, last_name, domain)
        print(f"Generated {len(all_emails)} possible patterns")

        # Test each email
        verified_emails = []
        failed_emails = []
        unknown_emails = []

        for i, email in enumerate(all_emails, 1):
            print(f"  [{i}/{len(all_emails)}] Testing: {email}...", end=" ")

            result = self.verifier.verify_email(email)

            if result['status'] == 'valid':
                print("✅ EXISTS!")
                verified_emails.append({
                    'email': email,
                    'pattern': self._detect_pattern(email, first_name, last_name),
                    'verification': result
                })

                if quick_stop:
                    print(f"  Found valid email! Stopping early.")
                    break

            elif result['status'] == 'invalid':
                print("❌ Doesn't exist")
                failed_emails.append(email)

            else:
                print("❓ Unknown (server didn't confirm)")
                unknown_emails.append(email)

            # Rate limiting
            time.sleep(1)

        # Summary
        result_summary = {
            'person': f"{first_name} {last_name}",
            'company': company,
            'domain': domain,
            'patterns_tested': len(all_emails),
            'verified_emails': verified_emails,
            'failed_count': len(failed_emails),
            'unknown_count': len(unknown_emails),
            'success': len(verified_emails) > 0
        }

        print(f"\n📊 Results:")
        print(f"   ✅ Verified: {len(verified_emails)}")
        print(f"   ❌ Invalid: {len(failed_emails)}")
        print(f"   ❓ Unknown: {len(unknown_emails)}")

        return result_summary

    def _detect_pattern(self, email: str, first_name: str, last_name: str) -> str:
        """Detect which pattern was used"""
        return self.generator._detect_pattern(email, first_name, last_name)

    def test_batch(self, contacts_df: pd.DataFrame, domain_column: str = 'domain',
                  quick_stop: bool = True) -> pd.DataFrame:
        """
        Test email patterns for a batch of contacts

        Args:
            contacts_df: DataFrame with first_name, last_name, company, domain
            domain_column: Column name containing email domain
            quick_stop: Stop after finding first valid email per person

        Returns:
            DataFrame with verified emails added
        """
        results = []

        print(f"\n{'=' * 80}")
        print(f"BATCH PATTERN TESTING")
        print(f"{'=' * 80}")
        print(f"Testing {len(contacts_df)} contacts...")
        print(f"Quick stop: {quick_stop}")
        print(f"{'=' * 80}\n")

        for idx, row in contacts_df.iterrows():
            first_name = row.get('first_name', '')
            last_name = row.get('last_name', '')
            company = row.get('current_employer', '') or row.get('company', '')
            domain = row.get(domain_column, '')

            if not all([first_name, last_name, domain]):
                print(f"\n⚠️  Skipping {first_name} {last_name} - Missing data")
                continue

            # Test this person
            test_result = self.test_person(
                first_name, last_name, company, domain, quick_stop
            )

            # Add verified emails to row
            if test_result['verified_emails']:
                for i, verified in enumerate(test_result['verified_emails'][:5], 1):
                    row[f'verified_email_{i}'] = verified['email']
                    row[f'verified_email_{i}_pattern'] = verified['pattern']
                    row[f'verified_email_{i}_method'] = 'smtp_tested'

                # Mark the pattern as confirmed for learning
                best_email = test_result['verified_emails'][0]
                self.generator.add_example(
                    company=company,
                    email=best_email['email'],
                    first_name=first_name,
                    last_name=last_name
                )

            row['patterns_tested'] = test_result['patterns_tested']
            row['verified_count'] = len(test_result['verified_emails'])

            results.append(row)

            # Rate limiting between people
            time.sleep(2)

        # Save learned patterns
        self.generator.save_examples()
        print(f"\n✅ Saved verified patterns to email_examples.json")

        return pd.DataFrame(results)

    def test_from_excel(self, excel_file: str, output_file: str = None) -> pd.DataFrame:
        """
        Test patterns from an Excel file with contacts and domains

        Expected columns:
        - first_name
        - last_name
        - company or current_employer
        - domain

        Args:
            excel_file: Input Excel file
            output_file: Output file (default: verified_emails.xlsx)

        Returns:
            DataFrame with verified emails
        """
        print(f"Loading: {excel_file}")
        df = pd.read_excel(excel_file)

        print(f"Found {len(df)} contacts")
        print(f"Columns: {list(df.columns)}")

        # Test all contacts
        results_df = self.test_batch(df, quick_stop=True)

        # Export results
        if output_file is None:
            output_file = f"verified_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        results_df.to_excel(output_file, index=False)
        print(f"\n{'=' * 80}")
        print(f"✅ Results saved to: {output_file}")
        print(f"{'=' * 80}")

        # Show statistics
        total = len(results_df)
        verified = (results_df['verified_count'] > 0).sum()
        print(f"\n📊 Statistics:")
        print(f"   Total contacts: {total}")
        print(f"   Verified emails found: {verified} ({verified/total*100:.1f}%)")
        print(f"   No email found: {total - verified} ({(total-verified)/total*100:.1f}%)")

        return results_df


# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("EMAIL PATTERN TESTER - DEMO")
    print("=" * 80)
    print("This tests ALL possible email patterns and finds real ones!")
    print("=" * 80)

    # Create sample contact
    tester = PatternTester()

    # Test a single person (example - won't actually work without real data)
    print("\nExample: Testing patterns for a Goldman Sachs employee")
    print("(This is a demo - replace with real data)")

    test_person = {
        'first_name': 'John',
        'last_name': 'Doe',
        'company': 'Goldman Sachs',
        'domain': 'gs.com'
    }

    # Show what patterns would be generated
    emails = tester.generate_all_patterns(
        test_person['first_name'],
        test_person['last_name'],
        test_person['domain']
    )

    print(f"\nWould test these {len(emails)} patterns:")
    for i, email in enumerate(emails[:10], 1):
        print(f"  {i}. {email}")
    if len(emails) > 10:
        print(f"  ... and {len(emails) - 10} more")

    print("\n" + "=" * 80)
    print("USAGE:")
    print("=" * 80)
    print("1. Prepare Excel with: first_name, last_name, company, domain")
    print("2. Run: tester.test_from_excel('your_file.xlsx')")
    print("3. Get verified emails in output file")
    print("4. Patterns are automatically learned and saved")
    print("=" * 80)
