"""
Enhanced Email Verification System with Confidence Scores
Checks if email addresses exist WITHOUT sending emails
"""

import re
import smtplib
import dns.resolver
import socket
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


logger = logging.getLogger(__name__)


class EmailVerifier:
    """
    Verify email addresses with confidence scoring

    Features:
    - SMTP verification (primary method)
    - DNS/MX record validation (fallback)
    - Syntax validation
    - Confidence scores (0-100)
    - Caching to avoid re-checks
    - Rate limiting per domain
    """

    def __init__(self, timeout: int = 15, max_workers: int = 3):
        """
        Initialize verifier

        Args:
            timeout: Seconds to wait for server response
            max_workers: Number of parallel verification threads
        """
        self.timeout = timeout
        self.max_workers = max_workers

        # Cache results
        self.cache = {}

        # Rate limiting per domain
        self.last_check = {}
        self.min_delay = 2  # seconds between checks to same domain

        # Known patterns that indicate blocking
        self.blocking_indicators = [
            'spamhaus', 'blocked', 'blacklist', 'policy',
            'greylisted', 'temp', 'try again'
        ]

    def _is_valid_syntax(self, email: str) -> tuple[bool, int]:
        """
        Check if email has valid syntax

        Returns:
            (is_valid, confidence_score)
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, email):
            return False, 0

        # Additional checks for confidence
        confidence = 50  # Base confidence for valid syntax

        # Penalize if too many dots or special chars
        if email.count('.') > 3:
            confidence -= 10
        if email.count('+') > 0:  # Plus addressing
            confidence += 5  # Actually more likely to be valid

        # Boost for common TLDs
        common_tlds = ['.com', '.org', '.net', '.edu', '.gov']
        if any(email.endswith(tld) for tld in common_tlds):
            confidence += 10

        return True, min(confidence, 100)

    def _get_mx_record(self, domain: str) -> tuple[List[str], int]:
        """
        Get MX (mail exchange) records for domain

        Returns:
            (mx_records, confidence_score)
        """
        try:
            records = dns.resolver.resolve(domain, 'MX')
            mx_list = [str(r.exchange).rstrip('.') for r in records]

            # More MX records = more confidence
            confidence = min(30 + len(mx_list) * 10, 50)

            return mx_list, confidence

        except dns.resolver.NXDOMAIN:
            logger.debug(f"Domain does not exist: {domain}")
            return [], 0
        except dns.resolver.NoAnswer:
            logger.debug(f"No MX records for domain: {domain}")
            return [], 0
        except dns.exception.Timeout:
            logger.warning(f"DNS timeout for domain: {domain}")
            return [], 0
        except Exception as e:
            logger.error(f"DNS error for {domain}: {e}")
            return [], 0

    def _check_smtp(self, email: str, mx_host: str) -> Dict[str, any]:
        """
        Check if email exists via SMTP

        Returns:
            Dict with status, confidence, code, message
        """
        try:
            # Connect to mail server
            server = smtplib.SMTP(timeout=self.timeout)
            server.set_debuglevel(0)
            server.connect(mx_host)
            server.helo(server.local_hostname)
            server.mail('verify@example.com')

            # Ask if recipient exists
            code, message = server.rcpt(email)
            server.quit()

            message_str = message.decode() if isinstance(message, bytes) else str(message)
            message_lower = message_str.lower()

            # Check for blocking indicators
            is_blocked = any(indicator in message_lower
                           for indicator in self.blocking_indicators)

            if code == 250:
                # Success code, but might be false positive
                if is_blocked:
                    confidence = 40  # Server accepts all, low confidence
                else:
                    confidence = 90  # Real verification

                return {
                    'status': 'valid',
                    'confidence': confidence,
                    'code': code,
                    'message': message_str,
                    'method': 'smtp'
                }

            elif code in [550, 551, 553]:
                return {
                    'status': 'invalid',
                    'confidence': 85,  # High confidence it doesn't exist
                    'code': code,
                    'message': message_str,
                    'method': 'smtp'
                }

            else:
                # Uncertain codes
                return {
                    'status': 'unknown',
                    'confidence': 30,
                    'code': code,
                    'message': message_str,
                    'method': 'smtp'
                }

        except smtplib.SMTPServerDisconnected:
            return {'status': 'error', 'confidence': 0, 'message': 'Server disconnected', 'method': 'smtp'}
        except smtplib.SMTPResponseException as e:
            if e.smtp_code == 550:
                return {'status': 'invalid', 'confidence': 85, 'message': str(e), 'method': 'smtp'}
            return {'status': 'error', 'confidence': 0, 'message': str(e), 'method': 'smtp'}
        except (socket.timeout, socket.error):
            return {'status': 'timeout', 'confidence': 0, 'message': 'Connection timeout', 'method': 'smtp'}
        except Exception as e:
            logger.error(f"SMTP error for {email}: {e}")
            return {'status': 'error', 'confidence': 0, 'message': str(e), 'method': 'smtp'}

    def _rate_limit_check(self, domain: str):
        """Enforce rate limiting per domain"""
        now = time.time()
        if domain in self.last_check:
            elapsed = now - self.last_check[domain]
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)
        self.last_check[domain] = time.time()

    def verify_with_fallback(self, email: str, use_cache: bool = True) -> Dict[str, any]:
        """
        Verify email with fallback methods and confidence scoring

        Priority:
        1. Try SMTP verification
        2. If blocked/failed, fallback to DNS validation
        3. Always include syntax validation

        Returns:
            Dict with:
            - email: The email checked
            - valid: True/False/None
            - confidence: 0-100 score
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
            'confidence': 0,
            'status': 'unknown',
            'method': None,
            'details': {}
        }

        # Step 1: Syntax validation
        syntax_valid, syntax_confidence = self._is_valid_syntax(email)
        if not syntax_valid:
            result['valid'] = False
            result['status'] = 'invalid'
            result['confidence'] = 95  # High confidence it's invalid
            result['method'] = 'syntax'
            result['details'] = {'reason': 'Invalid email syntax'}
            self.cache[email] = result
            return result

        result['confidence'] = syntax_confidence

        # Step 2: Extract domain and check MX records
        domain = email.split('@')[1]
        mx_hosts, mx_confidence = self._get_mx_record(domain)

        if not mx_hosts:
            result['valid'] = False
            result['status'] = 'invalid'
            result['confidence'] = 90  # High confidence - no MX records
            result['method'] = 'dns'
            result['details'] = {'reason': 'No MX records found for domain'}
            self.cache[email] = result
            return result

        result['details']['mx_hosts'] = mx_hosts
        result['confidence'] = max(result['confidence'], mx_confidence)

        # Step 3: SMTP verification (rate limited)
        self._rate_limit_check(domain)

        smtp_result = None
        for mx_host in mx_hosts[:3]:  # Try first 3 MX servers
            smtp_result = self._check_smtp(email, mx_host)

            if smtp_result['status'] in ['valid', 'invalid']:
                result['valid'] = smtp_result['status'] == 'valid'
                result['status'] = smtp_result['status']
                result['confidence'] = smtp_result['confidence']
                result['method'] = 'smtp'
                result['details'].update(smtp_result)
                result['details']['mx_host_used'] = mx_host
                break

        # If SMTP didn't give clear answer, use DNS confidence
        if result['status'] == 'unknown':
            result['confidence'] = mx_confidence
            result['method'] = 'dns_fallback'
            result['details']['reason'] = 'SMTP verification inconclusive, using DNS confidence'

        # Cache result
        self.cache[email] = result
        return result

    # Backward compatibility alias
    def verify_email(self, email: str, use_cache: bool = True) -> Dict[str, any]:
        """Alias for verify_with_fallback for backward compatibility"""
        return self.verify_with_fallback(email, use_cache)

    def verify_batch(self, emails: List[str]) -> List[Dict[str, any]]:
        """
        Verify multiple emails in parallel

        Args:
            emails: List of email addresses

        Returns:
            List of verification results with confidence scores
        """
        results = []

        logger.info(f"Verifying {len(emails)} emails...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_email = {
                executor.submit(self.verify_with_fallback, email): email
                for email in emails
            }

            for future in as_completed(future_to_email):
                email = future_to_email[future]
                try:
                    result = future.result()
                    results.append(result)

                    # Log with confidence
                    confidence = result['confidence']
                    status = result['status']

                    if status == 'valid' and confidence >= 80:
                        logger.info(f"✅ {email}: VALID ({confidence}% confidence)")
                    elif status == 'invalid' and confidence >= 80:
                        logger.info(f"❌ {email}: INVALID ({confidence}% confidence)")
                    else:
                        logger.info(f"❓ {email}: {status.upper()} ({confidence}% confidence)")

                except Exception as e:
                    logger.error(f"⚠️  {email}: Error - {e}")
                    results.append({
                        'email': email,
                        'valid': None,
                        'confidence': 0,
                        'status': 'error',
                        'details': {'error': str(e)}
                    })

        return results

    def get_statistics(self, results: List[Dict]) -> Dict[str, any]:
        """Get statistics from verification results including confidence"""
        stats = {
            'total': len(results),
            'valid': sum(1 for r in results if r['status'] == 'valid'),
            'invalid': sum(1 for r in results if r['status'] == 'invalid'),
            'unknown': sum(1 for r in results if r['status'] == 'unknown'),
            'error': sum(1 for r in results if r['status'] == 'error'),
        }

        stats['verified_rate'] = (stats['valid'] / stats['total'] * 100) if stats['total'] > 0 else 0

        # Average confidence
        confidences = [r['confidence'] for r in results if r['confidence'] > 0]
        stats['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0

        # High confidence results
        stats['high_confidence'] = sum(1 for r in results if r['confidence'] >= 80)

        return stats


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("ENHANCED EMAIL VERIFICATION WITH CONFIDENCE SCORES")
    print("=" * 80)

    verifier = EmailVerifier(timeout=15)

    # Test emails
    test_emails = [
        "info@goldmansachs.com",
        "contact@jpmorgan.com",
        "invalid-email",
        "test@invaliddomain12345.com"
    ]

    print("\nTesting verification with confidence scores:\n")

    for email in test_emails:
        print(f"Checking: {email}")
        result = verifier.verify_with_fallback(email)

        print(f"  Status: {result['status']}")
        print(f"  Confidence: {result['confidence']}%")
        print(f"  Method: {result['method']}")
        if 'reason' in result['details']:
            print(f"  Reason: {result['details']['reason']}")
        print()

    print("=" * 80)
