#!/usr/bin/env python3
"""
CLI Interface for RocketReach Contact Extractor

Usage:
    python cli.py extract --companies "Goldman Sachs,Morgan Stanley" --max 50
    python cli.py extract --config custom_config.yaml --resume
    python cli.py verify --input contacts.xlsx --output verified.xlsx
    python cli.py status
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.clients.base_client import BaseAPIClient
from smart_finance_extractor import SmartFinanceExtractor
import pandas as pd
from src.utils.email_verifier import EmailVerifier


def cmd_extract(args):
    """Handle extract command"""
    print("=" * 80)
    print("CONTACT EXTRACTION")
    print("=" * 80)

    # Load config
    config_file = args.config if args.config else "config.yaml"
    config = Config(config_file)

    # Get API key
    api_key = config.get('rocketreach.api_key') or os.getenv('ROCKETREACH_API_KEY')
    if not api_key:
        print("❌ ERROR: ROCKETREACH_API_KEY not set!")
        print("   Set it with: export ROCKETREACH_API_KEY='your_key'")
        return 1

    # Parse companies
    if args.companies:
        companies = [c.strip() for c in args.companies.split(',')]
    else:
        companies = None

    max_contacts = args.max if args.max else config.get('extraction.max_total_contacts', 100)

    print(f"\n📋 Configuration:")
    print(f"   Companies: {companies if companies else 'All finance companies'}")
    print(f"   Max contacts: {max_contacts}")
    print(f"   Resume: {args.resume}")
    print(f"   Output format: {args.format}")

    try:
        # Create extractor
        print("\n🚀 Initializing extractor...")
        extractor = SmartFinanceExtractor(api_key)

        # Filter companies if specified
        if companies:
            print(f"   Filtering for: {', '.join(companies)}")
            # Filter the finance_companies dict to only include specified companies
            filtered_companies = {}
            for sector, company_list in extractor.finance_companies.items():
                filtered = [c for c in company_list if any(target.lower() in c.lower() for target in companies)]
                if filtered:
                    filtered_companies[sector] = filtered

            if not filtered_companies:
                print(f"❌ ERROR: No matching companies found for: {companies}")
                return 1

            extractor.finance_companies = filtered_companies

        # Run extraction
        print("\n⏳ Starting extraction...")
        print("   (This may take a while due to rate limiting)")

        # Build list of companies to search
        companies_list = None
        if companies:
            companies_list = []
            for sector, company_list in extractor.finance_companies.items():
                companies_list.extend(company_list)

        # Extract contacts (returns a DataFrame)
        df = extractor.extract_with_distribution(
            companies_to_search=companies_list,
            max_total_contacts=max_contacts
        )

        if df.empty:
            print("\n⚠️  No contacts extracted")
            return 0

        # Save results
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"extracted_contacts_{timestamp}"

        print(f"\n💾 Saving {len(df)} contacts...")

        if args.format == 'xlsx':
            output_file = output_dir / f"{base_name}.xlsx"
            df.to_excel(output_file, index=False)
        elif args.format == 'csv':
            output_file = output_dir / f"{base_name}.csv"
            df.to_csv(output_file, index=False)
        elif args.format == 'json':
            output_file = output_dir / f"{base_name}.json"
            df.to_json(output_file, orient='records', indent=2)

        print(f"   ✅ Saved to: {output_file}")
        print(f"\n✨ Extraction complete!")
        print(f"   Total contacts: {len(df)}")

        return 0

    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_verify(args):
    """Handle verify command"""
    print("=" * 80)
    print("EMAIL VERIFICATION")
    print("=" * 80)

    if not args.input:
        print("❌ ERROR: --input required")
        return 1

    input_file = Path(args.input)
    if not input_file.exists():
        print(f"❌ ERROR: Input file not found: {input_file}")
        return 1

    output_file = Path(args.output) if args.output else input_file.with_stem(f"{input_file.stem}_verified")

    print(f"\n📋 Configuration:")
    print(f"   Input: {input_file}")
    print(f"   Output: {output_file}")

    try:
        # Load input file
        print("\n📂 Loading contacts...")
        if input_file.suffix == '.xlsx':
            df = pd.read_excel(input_file)
        elif input_file.suffix == '.csv':
            df = pd.read_csv(input_file)
        else:
            print(f"❌ ERROR: Unsupported file format: {input_file.suffix}")
            print("   Supported formats: .xlsx, .csv")
            return 1

        if 'email' not in df.columns:
            print("❌ ERROR: Input file must have an 'email' column")
            return 1

        print(f"   Found {len(df)} contacts")

        # Verify emails
        print("\n🔍 Verifying emails...")
        verifier = EmailVerifier()

        verified_results = []
        for idx, row in df.iterrows():
            email = row['email']
            if pd.isna(email) or not email:
                continue

            result = verifier.verify_with_fallback(email)
            verified_results.append({
                **row.to_dict(),
                'verification_status': result['status'],
                'verification_confidence': result['confidence'],
                'verification_method': result['method']
            })

            # Progress indicator
            if (idx + 1) % 10 == 0:
                print(f"   Verified {idx + 1}/{len(df)} emails...")

        print(f"   ✅ Verified {len(verified_results)} emails")

        # Save results
        print(f"\n💾 Saving results to {output_file}...")
        result_df = pd.DataFrame(verified_results)

        if output_file.suffix == '.xlsx':
            result_df.to_excel(output_file, index=False)
        elif output_file.suffix == '.csv':
            result_df.to_csv(output_file, index=False)
        else:
            # Default to xlsx if no extension
            output_file = output_file.with_suffix('.xlsx')
            result_df.to_excel(output_file, index=False)

        print(f"   ✅ Saved to: {output_file}")

        # Print summary
        print("\n📊 Verification Summary:")
        print(f"   Total verified: {len(verified_results)}")
        valid_count = sum(1 for r in verified_results if r['verification_status'] == 'valid')
        invalid_count = sum(1 for r in verified_results if r['verification_status'] == 'invalid')
        unknown_count = sum(1 for r in verified_results if r['verification_status'] == 'unknown')
        print(f"   Valid: {valid_count}")
        print(f"   Invalid: {invalid_count}")
        print(f"   Unknown: {unknown_count}")

        return 0

    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_status(args):
    """Handle status command - show rate limits and API status"""
    print("=" * 80)
    print("API STATUS & RATE LIMITS")
    print("=" * 80)

    # Load config
    config = Config()

    # Get API key
    api_key = config.get('rocketreach.api_key') or os.getenv('ROCKETREACH_API_KEY')
    if not api_key:
        print("❌ ERROR: ROCKETREACH_API_KEY not set!")
        return 1

    try:
        # Create client
        client = BaseAPIClient(api_key)

        # Get account info
        print("\n📊 Account Information:")
        account = client._get("account")
        if account:
            for key, value in account.items():
                print(f"   {key}: {value}")
        else:
            print("   ❌ Could not fetch account info")

        # Show rate limit status
        print("\n⏱️  Current Rate Limits:")
        client.print_rate_limit_status()

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="RocketReach Contact Extractor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from specific companies
  python cli.py extract --companies "Goldman Sachs,Morgan Stanley" --max 50

  # Extract with custom config and resume
  python cli.py extract --config my_config.yaml --resume

  # Verify emails in a file
  python cli.py verify --input contacts.xlsx --output verified.xlsx

  # Check API status and rate limits
  python cli.py status
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract contacts')
    extract_parser.add_argument('--companies', type=str, help='Comma-separated list of companies')
    extract_parser.add_argument('--max', type=int, help='Maximum total contacts to extract')
    extract_parser.add_argument('--config', type=str, help='Config file path')
    extract_parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    extract_parser.add_argument('--format', type=str, choices=['xlsx', 'csv', 'json'],
                               default='xlsx', help='Output format')

    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify email addresses')
    verify_parser.add_argument('--input', type=str, required=True, help='Input file with emails')
    verify_parser.add_argument('--output', type=str, help='Output file for verified emails')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show API status and rate limits')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command handler
    if args.command == 'extract':
        return cmd_extract(args)
    elif args.command == 'verify':
        return cmd_verify(args)
    elif args.command == 'status':
        return cmd_status(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
