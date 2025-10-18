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

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.clients.base_client import BaseAPIClient


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

    print(f"\n📋 Configuration:")
    print(f"   Companies: {companies if companies else 'All'}")
    print(f"   Max contacts: {args.max if args.max else config.get('extraction.max_total_contacts')}")
    print(f"   Resume: {args.resume}")
    print(f"   Output format: {args.format}")

    # TODO: Implement actual extraction
    # This would use the refactored smart_finance_extractor
    print("\n⚠️  Extraction functionality coming in Phase 2 completion")
    print("   For now, use: python3 smart_finance_extractor.py")

    return 0


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

    # TODO: Implement verification
    print("\n⚠️  Verification functionality coming in Phase 2 completion")
    print("   For now, use: python3 email_verifier.py")

    return 0


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
