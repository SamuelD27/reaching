#!/usr/bin/env python3
"""
Create a template Excel file for domain patterns
"""

import pandas as pd

# Template with example companies and domains
template_data = {
    "Company": [
        "Goldman Sachs",
        "Morgan Stanley",
        "JP Morgan",
        "Citigroup",
        "Bank of America",
        "McKinsey & Company",
        "Bain & Company",
        "Boston Consulting Group",
        "Deloitte",
        "PwC",
        "Blackstone",
        "KKR",
        "Carlyle Group",
        "Apollo Global Management",
        "TPG Capital",
        "Sequoia Capital",
        "Andreessen Horowitz",
        "Accel Partners",
        "Benchmark Capital",
        "Greylock Partners",
    ],
    "Domain": [
        "gs.com",
        "morganstanley.com",
        "jpmorgan.com",
        "citi.com",
        "bofa.com",
        "mckinsey.com",
        "bain.com",
        "bcg.com",
        "deloitte.com",
        "pwc.com",
        "blackstone.com",
        "kkr.com",
        "carlyle.com",
        "apollo.com",
        "tpg.com",
        "sequoiacap.com",
        "a16z.com",
        "accel.com",
        "benchmark.com",
        "greylock.com",
    ],
    "Notes": [
        "Investment Banking",
        "Investment Banking",
        "Investment Banking",
        "Investment Banking",
        "Investment Banking",
        "Consulting",
        "Consulting",
        "Consulting",
        "Consulting",
        "Consulting",
        "Private Equity",
        "Private Equity",
        "Private Equity",
        "Private Equity",
        "Private Equity",
        "Venture Capital",
        "Venture Capital",
        "Venture Capital",
        "Venture Capital",
        "Venture Capital",
    ]
}

df = pd.DataFrame(template_data)

# Save to Excel
df.to_excel("domain_patterns.xlsx", index=False)

print("=" * 80)
print("✅ Created domain_patterns.xlsx")
print("=" * 80)
print(f"\nTemplate includes {len(df)} example companies")
print("\nColumns:")
print("  - Company: Company name")
print("  - Domain: Email domain (e.g., gs.com)")
print("  - Notes: Optional notes (sector, etc.)")
print("\n" + "=" * 80)
print("CUSTOMIZE THIS FILE:")
print("=" * 80)
print("1. Add all your target companies")
print("2. Add their email domains")
print("3. Save the file")
print("4. Run: complete_extractor_with_verification.py")
print("=" * 80)
