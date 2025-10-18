# Smart Finance Contact Extractor - User Guide

## Overview

This script intelligently extracts finance industry contacts with **geographic distribution** and **automatic deduplication**.

## Key Features

### ✅ What's Implemented

1. **Geographic Priority System (3:2:1 Ratio)**
   - **Tier 1** (3 contacts per location): Singapore, Hong Kong, Paris
   - **Tier 2** (2 contacts per location): London, Luxembourg, Geneva
   - **Tier 3** (1 contact per location): Shanghai, Zurich

2. **Senior Positions Only**
   - Managing Director
   - Vice President / SVP
   - Director / Executive Director
   - Portfolio Manager
   - C-Suite (CEO, CFO, CIO, COO, CTO)
   - Partner / Managing Partner / General Partner
   - Head of [Department]

3. **Comprehensive Finance Companies**
   - **Investment Banking**: Goldman Sachs, Morgan Stanley, JP Morgan, Citi, Barclays, UBS, Credit Suisse, Deutsche Bank, Lazard, Jefferies, etc.
   - **Private Equity**: Blackstone, KKR, Carlyle, Apollo, TPG, Bain Capital, Vista Equity, Silver Lake, etc.
   - **Hedge Funds**: Citadel, Bridgewater, Millennium, Point72, Two Sigma, D.E. Shaw, Elliott, Tiger Global, etc.
   - **Asset Management**: BlackRock, Vanguard, Fidelity, PIMCO, State Street, etc.
   - **Venture Capital**: Sequoia, Andreessen Horowitz, Accel, Benchmark, Lightspeed, etc.

4. **Smart Deduplication**
   - Automatically loads and checks against:
     - `Compiled_names.xlsx` (959 contacts)
     - `HF.xlsx` (50 contacts)
     - `contact_history.json` (all previous extractions)
   - Skips anyone already contacted

5. **Even Distribution Per Company**
   - Processes one company at a time
   - Fetches from all locations before moving to next company
   - Respects quotas for balanced distribution

## How It Works

### Distribution Logic

For **each company**, the script:

1. Searches **Singapore** → finds 3 senior people → adds them
2. Searches **Hong Kong** → finds 3 senior people → adds them
3. Searches **Paris** → finds 3 senior people → adds them
4. Searches **London** → finds 2 senior people → adds them
5. Searches **Luxembourg** → finds 2 senior people → adds them
6. Searches **Geneva** → finds 2 senior people → adds them
7. Searches **Shanghai** → finds 1 senior person → adds them
8. Searches **Zurich** → finds 1 senior person → adds them

**Result**: Up to **17 contacts per company** with perfect geographic distribution!

### Example Distribution

If you extract from 10 companies:
- Singapore: ~30 contacts (3 per company)
- Hong Kong: ~30 contacts (3 per company)
- Paris: ~30 contacts (3 per company)
- London: ~20 contacts (2 per company)
- Luxembourg: ~20 contacts (2 per company)
- Geneva: ~20 contacts (2 per company)
- Shanghai: ~10 contacts (1 per company)
- Zurich: ~10 contacts (1 per company)

**Total**: ~170 perfectly distributed contacts

## Usage

### Quick Start

```python
python3 smart_finance_extractor.py
```

### Configuration

Edit the script at the bottom (line ~580) to customize:

```python
# Option 1: Target specific companies
target_companies = [
    "Goldman Sachs",
    "Morgan Stanley",
    "JP Morgan",
    "Blackstone",
    "KKR",
    "Citadel",
    "BlackRock"
]

# Option 2: Search ALL finance companies (100+)
# target_companies = extractor.all_companies

# Run extraction
results_df = extractor.extract_with_distribution(
    companies_to_search=target_companies,
    max_per_company=20  # Safety limit per company
)
```

### API Key Setup

Make sure your RocketReach API key is set:

```bash
export ROCKETREACH_API_KEY="your_key_here"
```

Or edit line ~572 in the script to add it directly.

## Output

### Excel File: `smart_finance_contacts.xlsx`

Columns:
- `first_name`: First name
- `last_name`: Last name
- `full_name`: Full name
- `current_title`: Job title (verified senior position)
- `current_employer`: Company name
- `location`: City/location
- `primary_email`: Main email address
- `all_emails`: All available emails
- `linkedin_url`: LinkedIn profile
- `phone`: Phone numbers
- `fetched_at`: Timestamp of extraction

### Console Output

The script provides detailed progress:

```
================================================================================
[1/10] Processing: Goldman Sachs
================================================================================

  📍 Tier 1 Locations (quota: 3 each):

    🌍 Singapore...
       Found 12 senior profiles
       🔍 Fetching: John Smith - Managing Director
       ✅ Added (1/3)
       🔍 Fetching: Jane Doe - Vice President
       ✅ Added (2/3)
       📊 Final: 3/3

    🌍 Hong Kong...
       Found 8 senior profiles
       📊 Final: 3/3
```

## Important Notes

### Rate Limits

The script automatically handles RocketReach rate limits:
- **Searches**: 15/min, 50/hour, 500/day
- **Lookups**: 15/min, 100/hour, 500/day

It will automatically pause and wait when needed.

### Deduplication

The script checks against:
1. Names from `Compiled_names.xlsx`
2. Names from `HF.xlsx`
3. Emails from both files
4. Previous extractions in `contact_history.json`

**Note**: If you manually add new people to `Compiled_names.xlsx` or `HF.xlsx`, the script will automatically detect them on the next run!

### False Positives with Email Verification

As you discovered, **SMTP verification can return false positives** for security-conscious companies (McKinsey, Goldman Sachs, etc.).

These companies intentionally accept email addresses during SMTP handshake but reject at delivery time to prevent email harvesting.

**Recommendation**:
- Use the extracted contacts as a starting point
- Cross-reference with LinkedIn to verify the person exists
- Consider using the person's LinkedIn messaging instead of email for initial outreach

## Customization

### Adjust Location Quotas

In `__init__` method (line ~27):

```python
self.location_tiers = {
    'tier1': {
        'locations': ['Singapore', 'Hong Kong', 'Paris'],
        'quota_per_company': 5,  # Changed from 3 to 5
        'priority': 1
    },
    # ...
}
```

### Add More Companies

In `__init__` method (line ~61):

```python
self.finance_companies = {
    "Investment Banking": [
        "Goldman Sachs",
        "Your Custom Bank",  # Add here
        # ...
    ],
}
```

### Modify Target Positions

In `__init__` method (line ~42):

```python
self.target_positions = [
    "Managing Director",
    "Your Custom Title",  # Add here
    # ...
]
```

## Troubleshooting

### "No profiles found"

This usually means:
- The company name doesn't match RocketReach's database exactly
- Try variations: "JP Morgan" vs "JPMorgan Chase" vs "J.P. Morgan"
- Check the company's official name on LinkedIn

### Rate limit warnings

The script automatically handles this. If you see frequent rate limit warnings, you're hitting API limits. Consider:
- Running extraction in smaller batches
- Increasing wait times between calls
- Upgrading your RocketReach plan

### Already contacted everyone

If the script says "already contacted" for everyone:
- Your `Compiled_names.xlsx` and `HF.xlsx` files are comprehensive
- Try adding more companies to search
- Try different locations

## Best Practices

1. **Start Small**: Test with 2-3 companies first
2. **Monitor Output**: Watch the console to ensure it's working correctly
3. **Check Results**: Review the Excel file before using contacts
4. **Respect Rate Limits**: Don't try to extract thousands of contacts at once
5. **Keep Records Updated**: Add new contacted people to `Compiled_names.xlsx`

## Example Workflow

1. **First Run**: Extract from 5 target companies
   ```python
   target_companies = ["Goldman Sachs", "Morgan Stanley", "Blackstone", "KKR", "Citadel"]
   ```

2. **Review Results**: Check `smart_finance_contacts.xlsx`

3. **Contact People**: Send your outreach emails

4. **Update Records**: Add newly contacted people to `Compiled_names.xlsx`

5. **Next Run**: The script automatically skips them!

## Need Help?

Check these files for more info:
- `EMAIL_VERIFICATION_GUIDE.md` - Email verification details
- `base_script.py` - Original extraction logic
- `email_verifier.py` - Email verification system
