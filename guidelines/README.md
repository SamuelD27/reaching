# RocketReach Contact Extractor - Enhanced Version

## Overview

This Python script automates bulk contact extraction from RocketReach API for internship/job hunting purposes. It extracts ALL email variations (not just one), classifies contacts by sector, prevents duplicate scraping, and can send automated personalized emails via Outlook.

## Key Features

### 1. **Complete Email Extraction**
- RocketReach's web interface only exports ONE email per contact
- This script extracts ALL email variations with confidence scores via the API
- Gets up to 5 emails and 3 phone numbers per contact

### 2. **Sector Classification** ✨ NEW
Automatically classifies contacts into finance sectors:
- Investment Banking (Goldman Sachs, Morgan Stanley, JP Morgan, etc.)
- Consulting (McKinsey, Bain, BCG, etc.)
- Hedge Funds (Bridgewater, Citadel, Millennium, etc.)
- Private Equity (Blackstone, KKR, Carlyle, etc.)
- Venture Capital (Sequoia, Andreessen Horowitz, etc.)
- Other (for non-finance professionals)

### 3. **Duplicate Prevention** ✨ NEW
- Maintains a local history file (`contact_history.json`)
- Automatically skips previously contacted people
- Tracks by both person ID and LinkedIn URL
- Prevents wasting API credits on duplicates

### 4. **Outlook Email Integration** ✨ NEW
- Send personalized emails via your u.nus.edu Outlook account
- Template-based emails with {name} personalization
- Bulk email sending with rate limiting
- Supports both plain text and HTML emails
- Cross-platform (uses SMTP, not Windows COM)

### 5. **Rate Limit Management**
- Automatic rate limiting (15 searches/min, 15 lookups/min)
- Based on RocketReach Pro plan limits
- Safe for long-running operations

### 6. **Graceful Interruption**
- Press Ctrl+C anytime to stop and save progress
- All extracted contacts are saved before exit
- Contact history preserved

### 7. **Smart Error Handling**
- Helpful suggestions for empty results
- Detailed error messages with API responses
- Continues on individual lookup failures

## Installation

```bash
# Clone or download the script
cd reaching_tool

# Install required packages
pip install requests pandas openpyxl
```

## Configuration

### 1. RocketReach API Key
Get your API key from [RocketReach Account Settings](https://rocketreach.co/account)

```python
API_KEY = "your_api_key_here"
```

### 2. Email Configuration (Optional)
For sending emails via Outlook:

```python
SENDER_EMAIL = "your_email@u.nus.edu"
SENDER_PASSWORD = "your_password"
```

**Important:** If you have 2-factor authentication enabled on your Microsoft account, you'll need to:
1. Go to [Microsoft Account Security](https://account.microsoft.com/security)
2. Generate an app-specific password
3. Use that password instead of your regular password

## Usage

### Basic Usage - Extract Contacts Only

```python
from base_script import RocketReachExtractor

# Initialize
extractor = RocketReachExtractor("your_api_key")

# Define search criteria
search_criteria = {
    "query": {
        "current_employer": ["Goldman Sachs", "Morgan Stanley"],
        "location": ["New York", "Singapore"],
        "school": ["National University of Singapore"]
    }
}

# Extract contacts (max 50)
contacts_df = extractor.extract_all_contacts(search_criteria, max_results=50)

# Export to Excel
extractor.export_to_excel(contacts_df, "my_contacts.xlsx")
```

### Advanced Usage - With Email Campaign

```python
# Extract contacts
contacts_df = extractor.extract_all_contacts(search_criteria, max_results=20)

# Filter by sector if desired
pe_contacts = contacts_df[contacts_df['sector'] == 'Private Equity']

# Email template
email_template = """
Dear {name},

I hope this email finds you well. My name is Samuel Dukmedjian, and I am currently
a final year student at the National University of Singapore studying Business Analytics.

I came across your profile and was impressed by your experience at {company}.
I am very interested in learning more about your career path in {sector}.

Would you be available for a brief 15-minute informational chat in the coming weeks?
I would love to learn from your insights and experiences.

Thank you for considering my request.

Best regards,
Samuel Dukmedjian
"""

# Send emails
results = extractor.send_bulk_emails(
    contacts_df=pe_contacts,
    email_template=email_template,
    subject_template="NUS Student Seeking Career Advice",
    sender_email="your_email@u.nus.edu",
    sender_password="your_password",
    email_column="email_1"
)

print(f"Sent: {results['sent']}, Failed: {results['failed']}")
```

## Search Parameters

Available search filters:

```python
search_criteria = {
    "query": {
        # Job titles
        "current_title": ["Analyst", "Associate", "Vice President"],

        # Company names
        "current_employer": ["Google", "Meta", "McKinsey"],

        # Or company domains
        "employer_domain": ["google.com", "mckinsey.com"],

        # Locations
        "location": ["New York", "San Francisco", "Singapore"],

        # Management levels
        "management_level": ["Manager", "Director", "VP", "C-Level"],

        # Schools/Universities
        "school": ["Stanford University", "Harvard University", "NUS"]
    }
}
```

**Note:** At least ONE search parameter is required. Empty arrays will be ignored.

## Output Format

### Excel Export
The script exports an Excel file with these columns:

| Column | Description |
|--------|-------------|
| first_name | First name |
| last_name | Last name |
| full_name | Full name |
| current_title | Job title |
| current_employer | Company name |
| **sector** | Finance sector classification ✨ NEW |
| location | Location |
| linkedin_url | LinkedIn profile URL |
| email_1 to email_5 | Up to 5 email addresses |
| email_X_status | Email verification status |
| email_X_type | Email type (work/personal) |
| phone_1 to phone_3 | Up to 3 phone numbers |
| phone_X_type | Phone type |

### Contact History
`contact_history.json` tracks all contacted person IDs and LinkedIn URLs:

```json
{
  "contacted_ids": [
    "12345678",
    "https://www.linkedin.com/in/john-doe",
    "87654321"
  ]
}
```

## Best Practices

### 1. RocketReach Credits Management
- Start with small batches (max_results=10-20) to test
- Monitor your credit usage on RocketReach dashboard
- Search API calls are cheaper than lookup calls
- The script skips duplicates to save credits

### 2. Email Campaigns
- Always personalize your emails
- Keep emails concise and respectful
- Don't send to more than 20-30 people per day (avoid spam filters)
- Test with yourself first before bulk sending
- Use professional email templates

### 3. Sector Targeting
After extracting contacts, filter by sector:

```python
# Get only Investment Banking contacts
ib_contacts = contacts_df[contacts_df['sector'] == 'Investment Banking']

# Get finance professionals only (exclude "Other")
finance_contacts = contacts_df[contacts_df['sector'] != 'Other']

# Multiple sectors
target_sectors = ['Private Equity', 'Venture Capital']
target_contacts = contacts_df[contacts_df['sector'].isin(target_sectors)]
```

### 4. Running Multiple Searches
The script handles duplicates across runs:

```bash
# Day 1: Search Goldman Sachs
python3 base_script.py  # Extracts 20 GS contacts

# Day 2: Search Morgan Stanley
python3 base_script.py  # Extracts 20 MS contacts, skips any GS overlap

# Day 3: Expand GS search
python3 base_script.py  # Skips 20 previously contacted GS contacts
```

## Troubleshooting

### "Insufficient Credits" Error
```
Lookup error: 403 Client Error: Forbidden
Response: {"detail":"Insufficient Credits"}
```
**Solution:** You've exhausted your RocketReach lookup credits. Wait for reset or upgrade plan.

### Email Authentication Failed
```
Failed to send email: (535, b'5.7.3 Authentication unsuccessful')
```
**Solutions:**
1. Check email/password are correct
2. Enable "Less secure app access" (if applicable)
3. Generate and use an app-specific password
4. Check if u.nus.edu uses different SMTP settings

### Empty Results
```
ERROR: No results found for your search criteria
```
**Solutions:**
1. Broaden your search (remove some filters)
2. Check spelling of company names
3. Try different search parameters
4. Some companies might have different names in RocketReach

### Duplicate Not Detected
If the script doesn't skip a duplicate:
1. Check `contact_history.json` exists
2. Verify the person ID or LinkedIn URL is in the history
3. The script tracks by both ID and LinkedIn URL

## File Structure

```
reaching_tool/
├── base_script.py              # Main script
├── contact_history.json        # Duplicate tracking (auto-generated)
├── internship_contacts.xlsx    # Output file (auto-generated)
└── README.md                   # This file
```

## Security Notes

⚠️ **Important Security Reminders:**

1. **Never commit API keys or passwords to Git**
   - Use environment variables instead
   - Add `base_script.py` to `.gitignore` if it contains credentials

2. **Email Password Security**
   - Use app-specific passwords, not your main password
   - Consider using environment variables:
   ```python
   import os
   SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
   ```

3. **Contact History Privacy**
   - `contact_history.json` contains LinkedIn URLs
   - Don't share this file publicly
   - Add to `.gitignore` if using version control

## Limitations

1. **RocketReach Plan Limits**
   - Free tier: Very limited lookups per month
   - Pro tier: ~15 searches/min, ~15 lookups/min
   - Enterprise: Higher limits

2. **Email Deliverability**
   - Bulk emails may trigger spam filters
   - Keep daily volume under 50 emails
   - Personalize each email
   - Use professional email templates

3. **Sector Classification**
   - Based on keyword matching
   - May misclassify edge cases
   - "Other" category for non-finance roles
   - Can be customized by editing `sector_keywords` dict

## Customization

### Add New Sectors
Edit the `sector_keywords` dictionary in `__init__`:

```python
self.sector_keywords = {
    "Tech": ["software engineer", "google", "meta", "apple"],
    "Healthcare": ["hospital", "medical", "pharma"],
    # ... add more
}
```

### Change Email Settings
For non-Outlook email providers, modify in `send_email_outlook`:

```python
# Example: Gmail
smtp_server = "smtp.gmail.com"
smtp_port = 587
```

### Adjust Rate Limits
```python
self.search_limit_per_minute = 20  # Increase if you have higher plan
self.lookup_limit_per_minute = 20
```

## Tech Stack

- **Python 3.7+**
- **requests** - API calls
- **pandas** - Data manipulation
- **openpyxl** - Excel export
- **smtplib** - Email sending
- **json** - Contact history storage

## License

This tool is for personal use only. Respect RocketReach's Terms of Service and rate limits.

## Support

For issues with:
- **RocketReach API**: support@rocketreach.co
- **This Script**: Check error messages and troubleshooting section above
- **Email Integration**: Verify u.nus.edu email settings with NUS IT

---

**Happy Networking! 🚀**
