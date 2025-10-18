#!/usr/bin/env python3
"""
Email Pattern Generator
Learns email patterns from examples and generates probable emails for new contacts
"""

import re
import json
from typing import List, Dict, Tuple, Set
from collections import defaultdict, Counter


class EmailPatternGenerator:
    """
    Learns email patterns from known examples and generates probable emails

    Supports patterns like:
    - first.last@company.com
    - firstlast@company.com
    - f.last@company.com
    - first.l@company.com
    - first_last@company.com
    - flast@company.com
    - lastf@company.com
    And many more...
    """

    def __init__(self, examples_file: str = "email_examples.json"):
        """
        Initialize with known email examples

        Args:
            examples_file: JSON file with company email examples
        """
        self.examples_file = examples_file
        self.company_patterns = self._load_examples()
        self.pattern_library = self._build_pattern_library()

    def _load_examples(self) -> Dict[str, List[Dict]]:
        """Load email examples from JSON file"""
        try:
            with open(self.examples_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  {self.examples_file} not found. Creating empty file.")
            return {}

    def _extract_domain(self, email: str) -> str:
        """Extract domain from email"""
        return email.split('@')[1].lower() if '@' in email else ""

    def _extract_local_part(self, email: str) -> str:
        """Extract local part (before @) from email"""
        return email.split('@')[0].lower() if '@' in email else email.lower()

    def _detect_pattern(self, email: str, first_name: str, last_name: str) -> str:
        """
        Detect the pattern used in an email

        Returns pattern code like:
        - "first.last" (john.doe@company.com)
        - "firstlast" (johndoe@company.com)
        - "f.last" (j.doe@company.com)
        - "first.l" (john.d@company.com)
        - "flast" (jdoe@company.com)
        - etc.
        """
        local = self._extract_local_part(email)
        first = first_name.lower().strip()
        last = last_name.lower().strip()

        if not first or not last:
            return "unknown"

        # Remove common special characters for comparison
        local_clean = re.sub(r'[._\-]', '', local)

        # Pattern detection
        patterns = [
            # Full names
            (f"{first}.{last}", "first.last"),
            (f"{first}{last}", "firstlast"),
            (f"{first}_{last}", "first_last"),
            (f"{first}-{last}", "first-last"),
            (f"{last}.{first}", "last.first"),
            (f"{last}{first}", "lastfirst"),
            (f"{last}_{first}", "last_first"),
            (f"{last}-{first}", "last-first"),

            # First initial + last name
            (f"{first[0]}.{last}", "f.last"),
            (f"{first[0]}{last}", "flast"),
            (f"{first[0]}_{last}", "f_last"),
            (f"{first[0]}-{last}", "f-last"),

            # First name + last initial
            (f"{first}.{last[0]}", "first.l"),
            (f"{first}{last[0]}", "firstl"),
            (f"{first}_{last[0]}", "first_l"),
            (f"{first}-{last[0]}", "first-l"),

            # Last name + first initial
            (f"{last}.{first[0]}", "last.f"),
            (f"{last}{first[0]}", "lastf"),
            (f"{last}_{first[0]}", "last_f"),
            (f"{last}-{first[0]}", "last-f"),

            # Last initial + first name
            (f"{last[0]}.{first}", "l.first"),
            (f"{last[0]}{first}", "lfirst"),

            # Just first name
            (f"{first}", "first"),

            # Just last name
            (f"{last}", "last"),

            # First initial + last initial
            (f"{first[0]}.{last[0]}", "f.l"),
            (f"{first[0]}{last[0]}", "fl"),
        ]

        for pattern_email, pattern_code in patterns:
            pattern_clean = re.sub(r'[._\-]', '', pattern_email)
            if local_clean == pattern_clean or local == pattern_email:
                return pattern_code

        return "unknown"

    def _build_pattern_library(self) -> Dict[str, Dict[str, int]]:
        """
        Build a library of patterns per company domain

        Returns: {domain: {pattern: count}}
        """
        library = defaultdict(lambda: defaultdict(int))

        for company, examples in self.company_patterns.items():
            for example in examples:
                email = example['email']
                first = example['first_name']
                last = example['last_name']
                domain = self._extract_domain(email)

                pattern = self._detect_pattern(email, first, last)
                library[domain][pattern] += 1

        return dict(library)

    def add_example(self, company: str, email: str, first_name: str, last_name: str):
        """Add a new example to the database"""
        if company not in self.company_patterns:
            self.company_patterns[company] = []

        self.company_patterns[company].append({
            "email": email,
            "first_name": first_name,
            "last_name": last_name
        })

        # Rebuild pattern library
        self.pattern_library = self._build_pattern_library()

    def save_examples(self):
        """Save examples to JSON file"""
        with open(self.examples_file, 'w') as f:
            json.dump(self.company_patterns, f, indent=2)

    def _apply_pattern(self, first_name: str, last_name: str, pattern: str, domain: str) -> str:
        """Apply a pattern to generate an email"""
        first = first_name.lower().strip()
        last = last_name.lower().strip()

        if not first or not last:
            return ""

        # Pattern application
        patterns_map = {
            "first.last": f"{first}.{last}",
            "firstlast": f"{first}{last}",
            "first_last": f"{first}_{last}",
            "first-last": f"{first}-{last}",
            "last.first": f"{last}.{first}",
            "lastfirst": f"{last}{first}",
            "last_first": f"{last}_{first}",
            "last-first": f"{last}-{first}",
            "f.last": f"{first[0]}.{last}",
            "flast": f"{first[0]}{last}",
            "f_last": f"{first[0]}_{last}",
            "f-last": f"{first[0]}-{last}",
            "first.l": f"{first}.{last[0]}",
            "firstl": f"{first}{last[0]}",
            "first_l": f"{first}_{last[0]}",
            "first-l": f"{first}-{last[0]}",
            "last.f": f"{last}.{first[0]}",
            "lastf": f"{last}{first[0]}",
            "last_f": f"{last}_{first[0]}",
            "last-f": f"{last}-{first[0]}",
            "l.first": f"{last[0]}.{first}",
            "lfirst": f"{last[0]}{first}",
            "first": f"{first}",
            "last": f"{last}",
            "f.l": f"{first[0]}.{last[0]}",
            "fl": f"{first[0]}{last[0]}",
        }

        local = patterns_map.get(pattern, "")
        if local:
            return f"{local}@{domain}"
        return ""

    def generate_emails(self, first_name: str, last_name: str, company: str,
                       company_domain: str = None) -> List[Dict[str, any]]:
        """
        Generate probable emails for a person at a company

        Args:
            first_name: Person's first name
            last_name: Person's last name
            company: Company name (e.g., "Goldman Sachs")
            company_domain: Company domain (e.g., "gs.com"), optional

        Returns:
            List of dicts with 'email' and 'confidence' (high/medium/low)
        """
        results = []

        # Normalize names
        first = first_name.lower().strip()
        last = last_name.lower().strip()

        if not first or not last:
            return []

        # Find matching domain
        domain = company_domain

        if not domain:
            # Try to find domain from examples
            company_lower = company.lower()
            for comp, examples in self.company_patterns.items():
                if company_lower in comp.lower() or comp.lower() in company_lower:
                    if examples:
                        domain = self._extract_domain(examples[0]['email'])
                        break

        if not domain:
            # Guess common domains
            company_clean = re.sub(r'[^a-z0-9]', '', company.lower())
            possible_domains = [
                f"{company_clean}.com",
                f"{company.lower().replace(' ', '')}.com",
            ]
        else:
            possible_domains = [domain]

        # Generate emails for each possible domain
        for dom in possible_domains:
            # Check if we have patterns for this domain
            if dom in self.pattern_library:
                patterns = self.pattern_library[dom]
                # Sort by frequency (most common first)
                sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)

                for pattern, count in sorted_patterns:
                    email = self._apply_pattern(first, last, pattern, dom)
                    if email:
                        # Confidence based on frequency
                        total_examples = sum(patterns.values())
                        frequency_ratio = count / total_examples

                        if frequency_ratio >= 0.7:
                            confidence = "high"
                        elif frequency_ratio >= 0.3:
                            confidence = "medium"
                        else:
                            confidence = "low"

                        results.append({
                            "email": email,
                            "confidence": confidence,
                            "pattern": pattern,
                            "examples_count": count,
                            "source": "learned"
                        })
            else:
                # No examples for this domain, use common patterns
                common_patterns = [
                    "first.last", "firstlast", "f.last", "flast",
                    "first_last", "first", "last.first"
                ]

                for pattern in common_patterns:
                    email = self._apply_pattern(first, last, pattern, dom)
                    if email:
                        results.append({
                            "email": email,
                            "confidence": "low",
                            "pattern": pattern,
                            "examples_count": 0,
                            "source": "guessed"
                        })

        # Remove duplicates while preserving order
        seen = set()
        unique_results = []
        for r in results:
            if r['email'] not in seen:
                seen.add(r['email'])
                unique_results.append(r)

        return unique_results

    def get_company_stats(self) -> Dict[str, Dict]:
        """Get statistics about learned patterns"""
        stats = {}

        for company, examples in self.company_patterns.items():
            domain = self._extract_domain(examples[0]['email']) if examples else "unknown"
            patterns = self.pattern_library.get(domain, {})

            stats[company] = {
                "examples_count": len(examples),
                "domain": domain,
                "patterns": dict(patterns),
                "most_common_pattern": max(patterns.items(), key=lambda x: x[1])[0] if patterns else None
            }

        return stats


def create_example_file():
    """Create an example email_examples.json file"""
    examples = {
        "Goldman Sachs": [
            {"email": "john.doe@gs.com", "first_name": "John", "last_name": "Doe"},
            {"email": "jane.smith@gs.com", "first_name": "Jane", "last_name": "Smith"},
            {"email": "michael.johnson@gs.com", "first_name": "Michael", "last_name": "Johnson"}
        ],
        "Morgan Stanley": [
            {"email": "alice.wong@morganstanley.com", "first_name": "Alice", "last_name": "Wong"},
            {"email": "bob.chen@morganstanley.com", "first_name": "Bob", "last_name": "Chen"}
        ],
        "McKinsey": [
            {"email": "sarah_martinez@mckinsey.com", "first_name": "Sarah", "last_name": "Martinez"},
            {"email": "david_lee@mckinsey.com", "first_name": "David", "last_name": "Lee"}
        ],
        "Bain": [
            {"email": "emily.taylor@bain.com", "first_name": "Emily", "last_name": "Taylor"},
            {"email": "james.anderson@bain.com", "first_name": "James", "last_name": "Anderson"}
        ]
    }

    with open("email_examples.json", 'w') as f:
        json.dump(examples, f, indent=2)

    print("✓ Created email_examples.json with example patterns")


# Test/Demo
if __name__ == "__main__":
    print("=" * 80)
    print("EMAIL PATTERN GENERATOR - DEMO")
    print("=" * 80)

    # Create example file if it doesn't exist
    import os
    if not os.path.exists("email_examples.json"):
        create_example_file()

    # Initialize generator
    generator = EmailPatternGenerator()

    # Show learned patterns
    print("\n1. Learned Patterns:")
    print("-" * 80)
    stats = generator.get_company_stats()
    for company, info in stats.items():
        print(f"\n{company}:")
        print(f"  Domain: {info['domain']}")
        print(f"  Examples: {info['examples_count']}")
        print(f"  Most common pattern: {info['most_common_pattern']}")
        if info['patterns']:
            print(f"  All patterns: {info['patterns']}")

    # Test generation
    print("\n\n2. Generating Emails:")
    print("-" * 80)

    test_cases = [
        ("Samuel", "Dukmedjian", "Goldman Sachs"),
        ("Maria", "Garcia", "Morgan Stanley"),
        ("Alex", "Kim", "McKinsey"),
        ("Sophie", "Anderson", "Unknown Company", "newcompany.com"),
    ]

    for first, last, company, *domain in test_cases:
        domain = domain[0] if domain else None
        print(f"\n{first} {last} @ {company}")

        emails = generator.generate_emails(first, last, company, domain)

        for i, result in enumerate(emails[:5], 1):  # Show top 5
            confidence_emoji = {
                "high": "🟢",
                "medium": "🟡",
                "low": "🔴"
            }[result['confidence']]

            print(f"  {i}. {confidence_emoji} {result['email']}")
            print(f"      Pattern: {result['pattern']}, "
                  f"Confidence: {result['confidence']}, "
                  f"Source: {result['source']}")

    print("\n" + "=" * 80)
    print("Add your own examples to email_examples.json!")
    print("=" * 80)
