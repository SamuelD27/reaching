# Complete Company List - Smart Finance Extractor

## Overview

The script now includes **exactly** the companies you specified, organized by sector.

**Total Companies**: 80+ (including name variations)

---

## 📊 Investment Banking (IB) - 27 companies

### Bulge Bracket
1. Goldman Sachs
2. J.P. Morgan / JPMorgan Chase
3. Morgan Stanley
4. Bank of America Merrill Lynch / Bank of America / Merrill Lynch
5. Citigroup / Citi
6. Barclays
7. UBS
8. Credit Suisse
9. Deutsche Bank
10. BNP Paribas
11. Société Générale / Societe Generale

### Elite Boutiques
12. Evercore
13. Lazard
14. Moelis & Company / Moelis
15. PJT Partners
16. Houlihan Lokey
17. Rothschild & Co / Rothschild
18. Jefferies
19. Perella Weinberg Partners
20. Greenhill

---

## 🦈 Hedge Funds (HF) - 15 companies

1. Bridgewater Associates
2. Citadel
3. Point72 Asset Management / Point72
4. Millennium Management
5. D.E. Shaw
6. Elliott Management
7. Baupost Group
8. Tiger Global Management / Tiger Global
9. Viking Global Investors / Viking Global
10. Third Point
11. Pershing Square Capital
12. Lone Pine Capital
13. Coatue Management / Coatue

---

## 💰 Private Equity (PE) - 15 companies

1. Blackstone
2. KKR
3. Apollo Global Management / Apollo Global
4. Carlyle Group
5. TPG Capital
6. Vista Equity Partners
7. EQT Partners
8. Hellman & Friedman
9. Silver Lake Partners / Silver Lake
10. General Atlantic
11. Warburg Pincus
12. Advent International
13. CVC Capital Partners

---

## 📑 Consulting - 9 companies

1. McKinsey & Company / McKinsey
2. Boston Consulting Group / BCG
3. Bain & Company / Bain
4. Oliver Wyman
5. Roland Berger
6. Strategy&
7. EY-Parthenon
8. LEK Consulting / L.E.K. Consulting
9. Alvarez & Marsal

---

## 🚀 Venture Capital (VC) / Growth Equity - 14 companies

1. Sequoia Capital
2. Andreessen Horowitz / a16z
3. Accel
4. Insight Partners
5. B Capital
6. General Catalyst
7. Index Ventures
8. Lightspeed Venture Partners
9. Peak XV Partners (ex-Sequoia India)
10. Wavemaker Partners
11. Tiger Global (hybrid HF/VC)
12. SoftBank Vision Fund
13. Coatue (hybrid HF/VC)

---

## Name Variations Included

The script includes multiple name variations to improve matching with RocketReach:

### Examples:
- **J.P. Morgan** → Also searches "JPMorgan Chase"
- **McKinsey & Company** → Also searches "McKinsey"
- **BCG** → Also searches "Boston Consulting Group"
- **a16z** → Also searches "Andreessen Horowitz"
- **Point72** → Also searches "Point72 Asset Management"
- **Tiger Global** → Appears in both Hedge Fund and VC (hybrid)
- **Coatue** → Appears in both Hedge Fund and VC (hybrid)

---

## How to Use

### Option 1: Test with specific companies

Edit line ~570 in `smart_finance_extractor.py`:

```python
target_companies = [
    "Goldman Sachs",
    "Morgan Stanley",
    "Blackstone",
    "McKinsey & Company"
]
```

### Option 2: Search ALL companies

```python
target_companies = extractor.all_companies  # All 80+ companies
```

### Option 3: Search by sector

```python
# Investment Banking only (27 companies)
target_companies = extractor.finance_companies["Investment Banking"]

# Hedge Funds only (15 companies)
target_companies = extractor.finance_companies["Hedge Fund"]

# Private Equity only (15 companies)
target_companies = extractor.finance_companies["Private Equity"]

# Consulting only (9 companies)
target_companies = extractor.finance_companies["Consulting"]

# Venture Capital only (14 companies)
target_companies = extractor.finance_companies["Venture Capital"]
```

---

## Expected Results

### Per Company Distribution

For **each company**, the script fetches:
- 3 contacts from Singapore
- 3 contacts from Hong Kong
- 3 contacts from Paris
- 2 contacts from London
- 2 contacts from Luxembourg
- 2 contacts from Geneva
- 1 contact from Shanghai
- 1 contact from Zurich

**Total per company**: Up to 17 contacts

### Full Run Estimates

If you extract from **all 80 companies**:
- **Singapore**: ~240 contacts (3 per company)
- **Hong Kong**: ~240 contacts (3 per company)
- **Paris**: ~240 contacts (3 per company)
- **London**: ~160 contacts (2 per company)
- **Luxembourg**: ~160 contacts (2 per company)
- **Geneva**: ~160 contacts (2 per company)
- **Shanghai**: ~80 contacts (1 per company)
- **Zurich**: ~80 contacts (1 per company)

**Total**: ~1,360 contacts (if all positions available)

### Realistic Estimates

Not all companies have senior positions in all locations, so expect:
- **~50-70% success rate** per location
- **~600-900 total contacts** from a full run
- Higher success in major hubs (Singapore, Hong Kong, London, Paris)
- Lower success in smaller locations (Luxembourg, Geneva, Shanghai, Zurich)

---

## Sectors Summary

| Sector | Companies | % of Total |
|--------|-----------|------------|
| Investment Banking | 27 | 34% |
| Hedge Funds | 15 | 19% |
| Private Equity | 15 | 19% |
| Consulting | 9 | 11% |
| Venture Capital | 14 | 17% |
| **TOTAL** | **80** | **100%** |

---

## Deduplication

The script automatically skips:
- ✅ All 959 contacts from `Compiled_names.xlsx`
- ✅ All 50 contacts from `HF.xlsx`
- ✅ All previous extractions in `contact_history.json`

**Total skipped**: 1,009+ people

---

## Next Steps

1. **Test first**: Run with 3-5 companies
2. **Review results**: Check `smart_finance_contacts.xlsx`
3. **Scale up**: Run with full sector or all companies
4. **Contact people**: Use extracted contacts for outreach
5. **Update records**: Add to `Compiled_names.xlsx` for future deduplication

---

## Quick Start

```bash
# Set API key
export ROCKETREACH_API_KEY="your_key"

# Run the script
python3 smart_finance_extractor.py

# Check results
open smart_finance_contacts.xlsx
```

That's it! 🎉
