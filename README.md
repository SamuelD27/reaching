# Smart Finance Contact Extractor

Automated contact extraction tool for finance industry professionals using RocketReach API.

## Features

✅ **Automated Extraction** - Runs fully automatically in background
✅ **Smart Geographic Distribution** - 3:2:1 ratio across 8 key financial hubs
✅ **Senior Positions Only** - MD, VP, Director, Portfolio Manager, Head, C-Suite, Partner
✅ **80+ Finance Companies** - Investment Banking, Private Equity, Hedge Funds, Consulting, VC
✅ **Auto-Deduplication** - Tracks and skips already contacted people
✅ **Rate Limit Handling** - Automatically waits and resumes
✅ **Max Contacts Limit** - Control exactly how many to extract
✅ **Email Verification** - SMTP-based verification without sending emails

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Key

```bash
export ROCKETREACH_API_KEY="your_api_key_here"
```

### 3. Configure

Edit `smart_finance_extractor.py` (lines 693-694):

```python
MAX_TOTAL_CONTACTS = 500  # Stop after 500 contacts
MAX_PER_COMPANY = 20      # Max per company
```

### 4. Run

```bash
python3 smart_finance_extractor.py
```

Or in background:

```bash
python3 smart_finance_extractor.py > extraction.log 2>&1 &
```

## Geographic Distribution

The script prioritizes contacts across 8 locations with a 3:2:1 ratio:

| Tier | Locations | Contacts per Company |
|------|-----------|---------------------|
| 1 | Singapore, Hong Kong, Paris | 3 each |
| 2 | London, Luxembourg, Geneva | 2 each |
| 3 | Shanghai, Zurich | 1 each |

## Companies Covered

### Investment Banking (27)
Goldman Sachs, Morgan Stanley, J.P. Morgan, Bank of America, Citi, Barclays, UBS, Credit Suisse, Deutsche Bank, BNP Paribas, Société Générale, Evercore, Lazard, Moelis, PJT Partners, Houlihan Lokey, Rothschild, Jefferies, Perella Weinberg, Greenhill

### Private Equity (15)
Blackstone, KKR, Apollo, Carlyle, TPG, Vista Equity, EQT, Hellman & Friedman, Silver Lake, General Atlantic, Warburg Pincus, Advent, CVC

### Hedge Funds (15)
Citadel, Bridgewater, Millennium, Point72, D.E. Shaw, Elliott, Baupost, Tiger Global, Viking Global, Third Point, Pershing Square, Lone Pine, Coatue

### Consulting (9)
McKinsey, BCG, Bain, Oliver Wyman, Roland Berger, Strategy&, EY-Parthenon, L.E.K., Alvarez & Marsal

### Venture Capital (14)
Sequoia, Andreessen Horowitz, Accel, Insight Partners, B Capital, General Catalyst, Index Ventures, Lightspeed, Peak XV, Wavemaker, SoftBank Vision Fund

## Documentation

- **[QUICK_START.md](guidelines/QUICK_START.md)** - Quick reference guide
- **[NEW_FEATURES_SUMMARY.md](guidelines/NEW_FEATURES_SUMMARY.md)** - Latest features
- **[BACKGROUND_EXECUTION_GUIDE.md](guidelines/BACKGROUND_EXECUTION_GUIDE.md)** - Running in background
- **[COMPANY_LIST.md](guidelines/COMPANY_LIST.md)** - Complete company list
- **[RATE_LIMITS_UPDATE.md](guidelines/RATE_LIMITS_UPDATE.md)** - Rate limiting details
- **[EMAIL_VERIFICATION_GUIDE.md](guidelines/EMAIL_VERIFICATION_GUIDE.md)** - Email verification

## Key Scripts

| Script | Purpose |
|--------|---------|
| `smart_finance_extractor.py` | Main automated extraction tool |
| `email_verifier.py` | Email verification system |
| `base_script.py` | Original foundation script |
| `test_search.py` | Quick test script |

## Example Output

```
🤖 AUTOMATED EXTRACTION MODE
================================================================================
Max total contacts: 500
Max per company: 20
================================================================================

[1/10] Processing: Goldman Sachs
Total extracted so far: 0/500

    🌍 Singapore...
       🔍 Fetching: John Smith - Managing Director
       ✅ Added (1/3) [Total: 1]

⏳ Rate limit (minute): 12/12 - waiting 45s...

🎉 Extraction complete!
📊 Total contacts extracted: 500
💾 Results saved to: smart_finance_contacts.xlsx
```

## Time Estimates

| Contacts | Time (Automated) |
|----------|-----------------|
| 50 | ~8 minutes |
| 100 | ~17 minutes |
| 200 | ~33 minutes |
| 500 | ~1.4 hours |
| 1000 | ~2.8 hours |

All rate limit waiting is handled automatically!

## Requirements

- Python 3.7+
- RocketReach API key
- Dependencies: requests, pandas, openpyxl, dnspython

## Security

The `.gitignore` is configured to exclude:
- API keys and sensitive data
- Contact history and output files
- Virtual environments
- Temporary files

Never commit your API key or contact data!

## License

MIT

## Credits

Built with [Claude Code](https://claude.com/claude-code)
