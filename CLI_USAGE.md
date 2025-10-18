# CLI Usage Guide

The CLI is now fully functional! Here's how to use it.

## Setup

### 1. Activate Virtual Environment

```bash
source venv/bin/activate
```

Or use the venv Python directly:

```bash
./venv/bin/python cli.py [command]
```

### 2. Set API Key

```bash
export ROCKETREACH_API_KEY="your_api_key_here"
```

## Commands

### Extract Contacts

Extract contacts from finance companies with geographic distribution.

**Basic usage:**

```bash
python cli.py extract --companies "Goldman Sachs" --max 50
```

**All options:**

```bash
python cli.py extract \
  --companies "Goldman Sachs,Morgan Stanley,JPMorgan" \
  --max 100 \
  --format xlsx \
  --resume
```

**Parameters:**
- `--companies`: Comma-separated list of companies (optional, defaults to all finance companies)
- `--max`: Maximum total contacts to extract (optional, defaults to 100)
- `--format`: Output format - xlsx, csv, or json (default: xlsx)
- `--resume`: Resume from checkpoint (not yet implemented)
- `--config`: Custom config file path (optional)

**Features:**
- Geographic distribution (3:2:1 ratio across 8 locations)
- Senior position filtering (MD, VP, Director, Portfolio Manager, etc.)
- Auto-deduplication against existing files
- Automatic rate limit handling
- Saves to `output/extracted_contacts_[timestamp].[format]`

**Example:**

```bash
# Extract 50 contacts from Goldman Sachs
python cli.py extract --companies "Goldman Sachs" --max 50

# Extract from multiple companies in CSV format
python cli.py extract --companies "Morgan Stanley,JPMorgan,Blackstone" --max 100 --format csv

# Extract from all finance companies (80+ companies)
python cli.py extract --max 200
```

### Verify Emails

Verify email addresses in an existing file with confidence scores.

**Basic usage:**

```bash
python cli.py verify --input contacts.xlsx --output verified.xlsx
```

**All options:**

```bash
python cli.py verify \
  --input extracted_contacts.xlsx \
  --output verified_contacts.xlsx
```

**Parameters:**
- `--input`: Input file path (required) - supports .xlsx or .csv
- `--output`: Output file path (optional, defaults to [input]_verified.[ext])

**Features:**
- SMTP verification with DNS fallback
- Confidence scoring (0-100)
- Adds three new columns:
  - `verification_status`: valid, invalid, unknown, or error
  - `verification_confidence`: 0-100 score
  - `verification_method`: smtp, dns, or syntax
- Progress indicators every 10 emails
- Summary statistics

**Input file requirements:**
- Must be .xlsx or .csv format
- Must have an `email` column

**Example:**

```bash
# Verify emails in an Excel file
python cli.py verify --input output/extracted_contacts_20251018_153000.xlsx

# Verify with custom output path
python cli.py verify --input contacts.csv --output results/verified_contacts.xlsx
```

### Check API Status

Check your RocketReach API status and rate limits.

**Usage:**

```bash
python cli.py status
```

**Shows:**
- Account information
- Current rate limit usage
- Available quota

## Complete Workflow Example

Here's a complete workflow from extraction to verification:

```bash
# 1. Set API key
export ROCKETREACH_API_KEY="your_key_here"

# 2. Activate venv (if not already active)
source venv/bin/activate

# 3. Check API status
python cli.py status

# 4. Extract contacts from specific companies
python cli.py extract --companies "Goldman Sachs,Morgan Stanley" --max 50 --format xlsx

# 5. Verify the extracted emails
python cli.py verify --input output/extracted_contacts_20251018_153000.xlsx

# 6. Review the verified contacts
# Open output/extracted_contacts_20251018_153000_verified.xlsx
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'yaml'"

Install dependencies in your venv:

```bash
./venv/bin/pip install -r requirements.txt
```

### "ROCKETREACH_API_KEY not set"

Set your API key:

```bash
export ROCKETREACH_API_KEY="your_api_key_here"
```

### Virtual environment not activating properly

Use the venv Python directly:

```bash
./venv/bin/python cli.py [command]
```

### "No matching companies found"

The company name matching is case-insensitive and partial. Try:

```bash
# Instead of "Goldman Sachs Group"
python cli.py extract --companies "Goldman Sachs"

# Instead of "JP Morgan"
python cli.py extract --companies "JPMorgan"
```

## Notes

- The CLI uses the same `SmartFinanceExtractor` as the standalone script
- All rate limiting and geographic distribution logic is preserved
- Output files are automatically timestamped to prevent overwrites
- The verify command can handle large files but may take time due to SMTP verification
- Verification results include confidence scores to help identify false positives

## Alternative: Use Standalone Scripts

If you prefer the original scripts:

```bash
# Extraction
python smart_finance_extractor.py

# Email verification
python email_verifier.py
```

Both approaches work identically - the CLI just provides a cleaner interface.
