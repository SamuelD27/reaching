#!/usr/bin/env python3
"""
Email Verification Example
Demonstrates enhanced email verification with confidence scores
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.email_verifier import EmailVerifier


def main():
    """Verify sample emails with confidence scores"""
    print("=" * 80)
    print("EMAIL VERIFICATION EXAMPLE")
    print("=" * 80)

    # Create verifier
    verifier = EmailVerifier(timeout=15)

    # Test emails
    test_emails = [
        "info@goldmansachs.com",
        "contact@morganstanley.com",
        "invalid@nonexistentdomain12345.com",
        "not-an-email",
    ]

    print("\nVerifying emails with confidence scores...\n")

    results = []
    for email in test_emails:
        print(f"Checking: {email}")
        result = verifier.verify_with_fallback(email)

        results.append(result)

        # Display result with confidence
        status = result['status']
        confidence = result['confidence']
        method = result['method']

        # Color-code based on confidence
        if confidence >= 80:
            indicator = "✅" if status == 'valid' else "❌"
        elif confidence >= 50:
            indicator = "⚠️ "
        else:
            indicator = "❓"

        print(f"   {indicator} Status: {status.upper()}")
        print(f"   Confidence: {confidence}%")
        print(f"   Method: {method}")

        if 'reason' in result.get('details', {}):
            print(f"   Reason: {result['details']['reason']}")

        print()

    # Summary statistics
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    stats = verifier.get_statistics(results)

    print(f"Total checked: {stats['total']}")
    print(f"Valid: {stats['valid']}")
    print(f"Invalid: {stats['invalid']}")
    print(f"Unknown: {stats['unknown']}")
    print(f"Average confidence: {stats['avg_confidence']:.1f}%")
    print(f"High confidence results: {stats['high_confidence']}")

    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
