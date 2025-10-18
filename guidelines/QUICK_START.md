# Quick Start Guide - Smart Finance Extractor

## ✨ NEW FEATURES!

✅ **Max total contacts limit** - Set exactly how many contacts to extract
✅ **Fully automated** - Runs in background, handles rate limits automatically
✅ **No user input needed** - Set it and forget it!

**See [NEW_FEATURES_SUMMARY.md](NEW_FEATURES_SUMMARY.md) for details!**

---

## What You Asked For ✅

✅ **Finance companies only** (Investment Banks, PE, Hedge Funds, Consulting, VC)
✅ **8 specific locations** (Singapore, Hong Kong, Paris, London, Luxembourg, Geneva, Shanghai, Zurich)
✅ **Senior positions only** (MD, VP, Director, Portfolio Manager, Head, C-Suite, Partner)
✅ **Geographic priority** (3:2:1 ratio - Singapore/HK/Paris prioritized)
✅ **Even distribution per company** (processes one company at a time)
✅ **Auto-deduplication** (skips all 1,009 people from Compiled_names.xlsx and HF.xlsx)
✅ **Max contacts limit** - Control exactly how many to extract
✅ **Background operation** - Run while you do other work

## What You Got

### New File: `smart_finance_extractor.py`

This script does **exactly** what you specified:

1. **Searches each company systematically**
2. **Gets 3 people from**: Singapore, Hong Kong, Paris (Tier 1)
3. **Gets 2 people from**: London, Luxembourg, Geneva (Tier 2)
4. **Gets 1 person from**: Shanghai, Zurich (Tier 3)
5. **Only senior positions**: Managing Director, VP, Director, etc.
6. **Skips anyone** already in Compiled_names.xlsx or HF.xlsx

### Distribution Example

If you extract from **10 companies**, you get approximately:

| Location | Contacts | Tier |
|----------|----------|------|
| Singapore | 30 | 1 |
| Hong Kong | 30 | 1 |
| Paris | 30 | 1 |
| London | 20 | 2 |
| Luxembourg | 20 | 2 |
| Geneva | 20 | 2 |
| Shanghai | 10 | 3 |
| Zurich | 10 | 3 |
| **TOTAL** | **170** | - |

## How to Run

### 1. Set API Key

```bash
export ROCKETREACH_API_KEY="your_api_key_here"
```

### 2. Choose Companies

Edit line ~580 in `smart_finance_extractor.py`:

```python
# Option A: Specific companies (recommended for testing)
target_companies = [
    "Goldman Sachs",
    "Morgan Stanley",
    "Blackstone",
    "Citadel",
    "BlackRock"
]

# Option B: ALL 100+ finance companies
# target_companies = extractor.all_companies
```

### 3. Run It

```bash
python3 smart_finance_extractor.py
```

### 4. Check Results

Opens: `smart_finance_contacts.xlsx`

## Companies Included (100+)

### Investment Banking (26)
Goldman Sachs, Morgan Stanley, JP Morgan, Bank of America, Citi, Barclays, UBS, Credit Suisse, Deutsche Bank, HSBC, BNP Paribas, Lazard, Jefferies, Evercore, Rothschild, Moelis, etc.

### Private Equity (20)
Blackstone, KKR, Carlyle, Apollo, TPG, Warburg Pincus, Bain Capital, Vista Equity, Silver Lake, Thoma Bravo, Advent, Permira, CVC, Brookfield, etc.

### Hedge Funds (21)
Citadel, Bridgewater, Millennium, Point72, Two Sigma, D.E. Shaw, Renaissance Tech, Elliott, Tiger Global, Coatue, Viking, Baupost, Third Point, etc.

### Asset Management (16)
BlackRock, Vanguard, Fidelity, State Street, PIMCO, Amundi, Invesco, Franklin Templeton, T. Rowe Price, Schroders, etc.

### Venture Capital (16)
Sequoia, Andreessen Horowitz, Accel, Benchmark, Greylock, Kleiner Perkins, Lightspeed, Insight Partners, Founders Fund, Temasek, etc.

## Sample Output

```
================================================================================
SMART FINANCE CONTACT EXTRACTION
================================================================================

📍 Location Priority System:
   Tier 1 (3 per location): Singapore, Hong Kong, Paris
   Tier 2 (2 per location): London, Luxembourg, Geneva
   Tier 3 (1 per location): Shanghai, Zurich

🎯 Target Positions: Managing Director, Vice President, Director...

🏢 Companies to search: 5
🚫 Already contacted: 1,009 people
================================================================================

[1/5] Processing: Goldman Sachs
  📍 Tier 1 Locations (quota: 3 each):
    🌍 Singapore...
       Found 12 senior profiles
       🔍 Fetching: John Smith - Managing Director
       ✅ Added (1/3)
       ...
       📊 Final: 3/3

    🌍 Hong Kong...
       📊 Final: 3/3

    🌍 Paris...
       📊 Final: 3/3

  💼 Total from Goldman Sachs: 17 contacts

[2/5] Processing: Morgan Stanley
  ...

EXTRACTION SUMMARY
Total contacts extracted: 85
By Location:
  Singapore       15
  Hong Kong       15
  Paris           15
  London          10
  ...
```

## Important Notes

### About Email Verification

As you discovered with `lydia_koh@mckinsey.com`:
- SMTP verification can give **false positives**
- Many companies (McKinsey, Goldman, etc.) accept emails during SMTP handshake
- But reject at delivery time (anti-harvesting security measure)
- **Recommendation**: Verify person exists on LinkedIn before emailing

### About Deduplication

The script automatically loads:
- ✅ `Compiled_names.xlsx` - 959 contacts
- ✅ `HF.xlsx` - 50 contacts
- ✅ `contact_history.json` - previous extractions

**Total**: 1,009+ people automatically skipped!

### About Rate Limits

The script respects RocketReach limits:
- Searches: 15/min, 50/hour, 500/day
- Lookups: 15/min, 100/hour, 500/day

It will automatically pause when needed.

## Customization

### Change Location Quotas

In `smart_finance_extractor.py` line ~27:

```python
'tier1': {
    'locations': ['Singapore', 'Hong Kong', 'Paris'],
    'quota_per_company': 5,  # Change from 3 to 5
}
```

### Add More Locations

```python
'tier1': {
    'locations': ['Singapore', 'Hong Kong', 'Paris', 'Tokyo'],  # Add Tokyo
    'quota_per_company': 3,
}
```

### Add More Companies

Line ~61:

```python
"Investment Banking": [
    "Goldman Sachs",
    "Your Custom Bank",  # Add here
]
```

## Testing

**Recommended first run**:

```python
target_companies = ["Goldman Sachs", "Blackstone"]  # Just 2 companies
max_per_company = 10  # Limit results
```

This will:
- Extract ~20 contacts total
- Test all locations
- Verify deduplication works
- Use minimal API credits

## Files Created

1. **`smart_finance_extractor.py`** - Main script (new!)
2. **`SMART_EXTRACTOR_GUIDE.md`** - Detailed documentation
3. **`QUICK_START.md`** - This file
4. **`smart_finance_contacts.xlsx`** - Output (created when you run)

## Next Steps

1. ✅ Review this guide
2. ✅ Set your API key
3. ✅ Choose 2-3 companies for testing
4. ✅ Run: `python3 smart_finance_extractor.py`
5. ✅ Check results in `smart_finance_contacts.xlsx`
6. ✅ If happy, run with more companies!

## Questions?

- **How it works**: See `SMART_EXTRACTOR_GUIDE.md`
- **Email verification**: See `EMAIL_VERIFICATION_GUIDE.md`
- **Original functionality**: See `base_script.py`

---

## TL;DR

```bash
# Set API key
export ROCKETREACH_API_KEY="your_key"

# Edit companies (line ~580)
nano smart_finance_extractor.py

# Run
python3 smart_finance_extractor.py

# Check results
open smart_finance_contacts.xlsx
```

Done! 🎉
