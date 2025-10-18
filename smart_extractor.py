#!/usr/bin/env python3
"""
Smart Contact Extractor with Email Generation
Combines RocketReach search + intelligent email pattern generation
"""

import sys
sys.path.append('.')

from search_only_mode import RocketReachSearchOnly
from email_pattern_generator import EmailPatternGenerator
import pandas as pd
from datetime import datetime


class SmartContactExtractor(RocketReachSearchOnly):
    """
    Enhanced extractor that combines:
    1. RocketReach search (names, titles, companies, LinkedIn)
    2. Intelligent email generation from learned patterns
    """

    def __init__(self, api_key: str, history_file: str = "contact_history.json",
                 examples_file: str = "email_examples.json"):
        """Initialize with both RocketReach and email generator"""
        super().__init__(api_key, history_file)
        self.email_generator = EmailPatternGenerator(examples_file)

    def extract_with_emails(self, search_params: dict, max_results: int = 500) -> pd.DataFrame:
        """
        Extract contacts and generate probable emails

        Returns DataFrame with:
        - Basic info from RocketReach
        - 3-5 generated emails with confidence scores
        """
        print("\n" + "=" * 80)
        print("SMART CONTACT EXTRACTOR")
        print("=" * 80)
        print("Step 1: Extracting from RocketReach (search-only mode)")
        print("Step 2: Generating probable emails from learned patterns")
        print("=" * 80 + "\n")

        # Step 1: Get contacts from RocketReach
        contacts_df = self.extract_contacts_search_only(search_params, max_results)

        if contacts_df.empty:
            return contacts_df

        print(f"\n{'=' * 80}")
        print("GENERATING EMAILS FOR {len(contacts_df)} CONTACTS")
        print("=" * 80)

        # Step 2: Generate emails for each contact
        all_generated_emails = []

        for idx, row in contacts_df.iterrows():
            first_name = row['first_name']
            last_name = row['last_name']
            company = row['current_employer']

            print(f"\n{idx + 1}. {first_name} {last_name} @ {company}")

            # Generate emails
            generated = self.email_generator.generate_emails(
                first_name, last_name, company
            )

            # Add top 5 emails to the row
            for i, email_info in enumerate(generated[:5], 1):
                row[f'generated_email_{i}'] = email_info['email']
                row[f'email_{i}_confidence'] = email_info['confidence']
                row[f'email_{i}_pattern'] = email_info['pattern']
                row[f'email_{i}_source'] = email_info['source']

                # Show in console
                confidence_emoji = {
                    "high": "🟢",
                    "medium": "🟡",
                    "low": "🔴"
                }[email_info['confidence']]

                print(f"   {confidence_emoji} {email_info['email']} "
                      f"({email_info['confidence']}, {email_info['pattern']})")

            all_generated_emails.append(row)

        # Create new DataFrame with generated emails
        result_df = pd.DataFrame(all_generated_emails)

        return result_df

    def export_with_emails(self, df: pd.DataFrame, filename: str = None) -> None:
        """Export contacts with generated emails"""
        if filename is None:
            filename = f"contacts_with_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        # Reorder columns for better readability
        base_cols = ['first_name', 'last_name', 'full_name', 'current_title',
                     'current_employer', 'sector', 'location', 'linkedin_url']

        email_cols = [col for col in df.columns if 'generated_email' in col or 'email_' in col]
        other_cols = [col for col in df.columns if col not in base_cols + email_cols]

        ordered_cols = base_cols + email_cols + other_cols
        ordered_cols = [col for col in ordered_cols if col in df.columns]

        df_ordered = df[ordered_cols]
        df_ordered.to_excel(filename, index=False, engine='openpyxl')

        print(f"\n{'=' * 80}")
        print(f"✓ Exported to: {filename}")
        print("=" * 80)

    def show_statistics(self, df: pd.DataFrame):
        """Show statistics about extraction and email generation"""
        print(f"\n{'=' * 80}")
        print("STATISTICS")
        print("=" * 80)

        print(f"\n📊 Contacts by Sector:")
        print(df['sector'].value_counts().to_string())

        # Count high-confidence emails
        high_conf = df['email_1_confidence'].value_counts().get('high', 0)
        medium_conf = df['email_1_confidence'].value_counts().get('medium', 0)
        low_conf = df['email_1_confidence'].value_counts().get('low', 0)

        print(f"\n📧 Email Generation Confidence:")
        print(f"   🟢 High confidence:   {high_conf} contacts")
        print(f"   🟡 Medium confidence: {medium_conf} contacts")
        print(f"   🔴 Low confidence:    {low_conf} contacts")

        # Show learned vs guessed
        learned = (df['email_1_source'] == 'learned').sum()
        guessed = (df['email_1_source'] == 'guessed').sum()

        print(f"\n🎓 Email Source:")
        print(f"   Learned from examples: {learned} contacts")
        print(f"   Guessed (no examples): {guessed} contacts")

        print(f"\n💡 Recommendation:")
        if guessed > 0:
            print(f"   Add more examples to email_examples.json for better accuracy!")
        else:
            print(f"   All emails generated from learned patterns - high accuracy!")


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("SMART CONTACT EXTRACTOR - Email Generation Demo")
    print("=" * 80)

    API_KEY = "1ac349bkd05e6c94a51cd27e7070e825a9e3392e"

    # Initialize smart extractor
    extractor = SmartContactExtractor(API_KEY)

    # Show learned patterns
    print("\n📚 Learned Email Patterns:")
    print("-" * 80)
    stats = extractor.email_generator.get_company_stats()
    for company, info in stats.items():
        print(f"  {company}: {info['most_common_pattern']} @ {info['domain']}")

    # Search criteria
    search_criteria = {
        "query": {
            "current_employer": ["Goldman Sachs", "Morgan Stanley", "McKinsey"],
            # "location": ["New York", "Singapore"],
        }
    }

    # Extract with email generation
    contacts_df = extractor.extract_with_emails(search_criteria, max_results=10)

    if not contacts_df.empty:
        # Show statistics
        extractor.show_statistics(contacts_df)

        # Export
        extractor.export_with_emails(contacts_df, "contacts_with_emails.xlsx")

        print("\n" + "=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print("1. Open contacts_with_emails.xlsx")
        print("2. Review generated emails (🟢 = high confidence)")
        print("3. Test emails by sending (or use email verification tool)")
        print("4. Add confirmed emails to email_examples.json for better accuracy")
        print("5. Reach out via:")
        print("   - Email (high confidence ones first)")
        print("   - LinkedIn (all contacts have URLs)")
        print("   - Both for maximum response rate!")
        print("=" * 80)
