#!/usr/bin/env python3
"""
Email Verification System
Checks if email addresses exist WITHOUT sending emails

Methods:
1. SMTP verification (checks with mail server)
2. Syntax validation
3. DNS/MX record verification
4. Disposable email detection
"""

import re
import smtplib
import dns.resolver
import socket
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class EmailVerifier:
    """
    Verify email addresses without sending emails

    Uses SMTP protocol to check if mailbox exists:
    1. Connect to mail server
    2. Ask "does this email exist?"
    3. Server responds yes/no
    4. Disconnect (no email sent!)
    """

    def __init__(self, timeout: int = 10, max_workers: int = 5):
        """
        Initialize verifier

        Args:
            timeout: Seconds to wait for server response
            max_workers: Number of parallel verification threads
        """
        self.timeout = timeout
        self.max_workers = max_workers

        # Cache results to avoid re-checking
        self.cache = {}

        # Rate limiting per domain
        self.last_check = {}
        self.min_delay = 2  # seconds between checks to same domain

    def _is_valid_syntax(self, email: str) -> bool:
        """Check if email has valid syntax"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _get_mx_record(self, domain: str) -> List[str]:
        """Get MX (mail exchange) records for domain"""
        try:
            records = dns.resolver.resolve(domain, 'MX')
            return [str(r.exchange).rstrip('.') for r in records]
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout):
            return []

    def _check_smtp(self, email: str, mx_host: str) -> Dict[str, any]:
        """
        Check if email exists via SMTP

        This is the core verification method:
        - Connects to mail server
        - Uses SMTP VRFY or RCPT TO command
        - Server tells us if mailbox exists
        - No email is sent!
        """
        try:
            # Connect to mail server
            server = smtplib.SMTP(timeout=self.timeout)
            server.set_debuglevel(0)
            server.connect(mx_host)
            server.helo(server.local_hostname)  # Introduce ourselves
            server.mail('verify@example.com')   # Say we're sending from here

            # The magic: ask if recipient exists
            code, message = server.rcpt(email)
            server.quit()

            # Response codes:
            # 250 = mailbox exists
            # 550 = mailbox doesn't exist
            # 451/452 = temporary error
            # 553 = invalid mailbox name

            if code == 250:
                return {
                    'status': 'valid',
                    'exists': True,
                    'code': code,
                    'message': message.decode() if isinstance(message, bytes) else str(message)
                }
            elif code in [550, 551, 553]:
                return {
                    'status': 'invalid',
                    'exists': False,
                    'code': code,
                    'message': message.decode() if isinstance(message, bytes) else str(message)
                }
            else:
                return {
                    'status': 'unknown',
                    'exists': None,
                    'code': code,
                    'message': message.decode() if isinstance(message, bytes) else str(message)
                }

        except smtplib.SMTPServerDisconnected:
            return {'status': 'error', 'exists': None, 'message': 'Server disconnected'}
        except smtplib.SMTPResponseException as e:
            if e.smtp_code == 550:
                return {'status': 'invalid', 'exists': False, 'message': str(e)}
            return {'status': 'error', 'exists': None, 'message': str(e)}
        except (socket.timeout, socket.error):
            return {'status': 'timeout', 'exists': None, 'message': 'Connection timeout'}
        except Exception as e:
            return {'status': 'error', 'exists': None, 'message': str(e)}

    def _rate_limit_check(self, domain: str):
        """Enforce rate limiting per domain"""
        now = time.time()
        if domain in self.last_check:
            elapsed = now - self.last_check[domain]
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)
        self.last_check[domain] = time.time()

    def verify_email(self, email: str, use_cache: bool = True) -> Dict[str, any]:
        """
        Verify if an email address exists

        Args:
            email: Email address to verify
            use_cache: Use cached results if available

        Returns:
            Dict with:
            - email: The email checked
            - valid: True/False/None (None = couldn't verify)
            - status: 'valid', 'invalid', 'unknown', 'error'
            - method: How it was verified
            - details: Additional info
        """
        email = email.lower().strip()

        # Check cache
        if use_cache and email in self.cache:
            return self.cache[email]

        result = {
            'email': email,
            'valid': None,
            'status': 'unknown',
            'method': None,
            'details': {}
        }

        # Step 1: Syntax validation
        if not self._is_valid_syntax(email):
            result['valid'] = False
            result['status'] = 'invalid'
            result['method'] = 'syntax'
            result['details'] = {'reason': 'Invalid email syntax'}
            self.cache[email] = result
            return result

        # Step 2: Extract domain
        domain = email.split('@')[1]

        # Step 3: Check MX records
        mx_hosts = self._get_mx_record(domain)
        if not mx_hosts:
            result['valid'] = False
            result['status'] = 'invalid'
            result['method'] = 'dns'
            result['details'] = {'reason': 'No MX records found for domain'}
            self.cache[email] = result
            return result

        result['details']['mx_hosts'] = mx_hosts

        # Step 4: SMTP verification (rate limited)
        self._rate_limit_check(domain)

        # Try each MX host
        for mx_host in mx_hosts[:3]:  # Try first 3 MX servers
            smtp_result = self._check_smtp(email, mx_host)

            if smtp_result['status'] in ['valid', 'invalid']:
                result['valid'] = smtp_result['exists']
                result['status'] = smtp_result['status']
                result['method'] = 'smtp'
                result['details'].update(smtp_result)
                result['details']['mx_host_used'] = mx_host
                break
        else:
            # Couldn't verify with any MX host
            result['status'] = 'unknown'
            result['method'] = 'smtp'
            result['details']['reason'] = 'Could not verify with mail servers'

        # Cache result
        self.cache[email] = result
        return result

    def verify_batch(self, emails: List[str]) -> List[Dict[str, any]]:
        """
        Verify multiple emails in parallel

        Args:
            emails: List of email addresses

        Returns:
            List of verification results
        """
        results = []

        print(f"Verifying {len(emails)} emails...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all verification tasks
            future_to_email = {
                executor.submit(self.verify_email, email): email
                for email in emails
            }

            # Collect results as they complete
            for future in as_completed(future_to_email):
                email = future_to_email[future]
                try:
                    result = future.result()
                    results.append(result)

                    # Print progress
                    status_emoji = {
                        'valid': '✅',
                        'invalid': '❌',
                        'unknown': '❓',
                        'error': '⚠️'
                    }
                    emoji = status_emoji.get(result['status'], '❓')
                    print(f"  {emoji} {email}: {result['status']}")

                except Exception as e:
                    print(f"  ⚠️  {email}: Error - {e}")
                    results.append({
                        'email': email,
                        'valid': None,
                        'status': 'error',
                        'details': {'error': str(e)}
                    })

        return results

    def get_statistics(self, results: List[Dict]) -> Dict[str, int]:
        """Get statistics from verification results"""
        stats = {
            'total': len(results),
            'valid': sum(1 for r in results if r['status'] == 'valid'),
            'invalid': sum(1 for r in results if r['status'] == 'invalid'),
            'unknown': sum(1 for r in results if r['status'] == 'unknown'),
            'error': sum(1 for r in results if r['status'] == 'error')
        }
        stats['verified_rate'] = (stats['valid'] / stats['total'] * 100) if stats['total'] > 0 else 0
        return stats


# Demo/Test
if __name__ == "__main__":
    print("=" * 80)
    print("EMAIL VERIFICATION SYSTEM - DEMO")
    print("=" * 80)
    print("\nThis system checks if emails exist WITHOUT sending any emails!")
    print("It uses SMTP protocol to query mail servers directly.\n")

    # Initialize verifier
    verifier = EmailVerifier(timeout=10)

    # Test emails (mix of valid/invalid)
    test_emails = [
        "john.doe@gmail.com",         # Likely exists
        "thisemailsurelydoesnotexist12345@gmail.com",  # Doesn't exist
        "info@goldmansachs.com",      # Corporate email
        "invalid-email",              # Invalid syntax
        "test@invaliddomain12345.com" # Invalid domain
    ]

    print("Testing email verification:\n")

    for email in test_emails:
        print(f"Checking: {email}")
        result = verifier.verify_email(email)

        status_emoji = {
            'valid': '✅',
            'invalid': '❌',
            'unknown': '❓',
            'error': '⚠️'
        }
        emoji = status_emoji.get(result['status'], '❓')

        print(f"  {emoji} Status: {result['status']}")
        print(f"  Method: {result['method']}")
        if 'reason' in result['details']:
            print(f"  Reason: {result['details']['reason']}")
        print()

    print("=" * 80)
    print("IMPORTANT NOTES:")
    print("=" * 80)
    print("1. Some mail servers block verification (Gmail, Outlook often do)")
    print("2. Corporate servers (Goldman, etc.) may always return 'unknown'")
    print("3. This is a 'best effort' - not 100% accurate")
    print("4. Rate limiting is important to avoid being blocked")
    print("5. Use responsibly - don't spam mail servers!")
    print("=" * 80)
