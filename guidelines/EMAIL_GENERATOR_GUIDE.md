# Email Pattern Generator - User Guide

## Overview

This system learns email patterns from your known examples and generates probable emails for new contacts **without needing export credits**.

## How It Works

### 1. **Learning Phase**
You provide examples of real emails you've collected:
```json
{
  "Goldman Sachs": [
    {"email": "john.doe@gs.com", "first_name": "John", "last_name": "Doe"},
    {"email": "jane.smith@gs.com", "first_name": "Jane", "last_name": "Smith"}
  ]
}
```

The system analyzes these and learns:
- ✅ Goldman Sachs uses: `first.last@gs.com`
- ✅ Domain: `gs.com`
- ✅ Pattern confidence: HIGH (based on # of examples)

### 2. **Generation Phase**
When you extract a new contact:
- Name: **Samuel Dukmedjian**
- Company: **Goldman Sachs**

The system generates:
- 🟢 `samuel.dukmedjian@gs.com` (HIGH confidence, learned pattern)

## Supported Email Patterns

The system detects and generates 25+ common patterns:

| Pattern | Example | Description |
|---------|---------|-------------|
| `first.last` | john.doe@company.com | Most common |
| `firstlast` | johndoe@company.com | No separator |
| `f.last` | j.doe@company.com | Initial + last |
| `flast` | jdoe@company.com | Initial + last, no dot |
| `first.l` | john.d@company.com | First + initial |
| `first_last` | john_doe@company.com | Underscore |
| `first-last` | john-doe@company.com | Hyphen |
| `last.first` | doe.john@company.com | Reversed |
| `last.f` | doe.j@company.com | Last + initial |
| `lastf` | doej@company.com | Last + initial, no dot |
| `first` | john@company.com | First name only |
| `last` | doe@company.com | Last name only |
| And 13 more... | | |

## Adding Your Email Examples

### Step 1: Open `email_examples.json`

```json
{
  "Company Name": [
    {
      "email": "actual.email@domain.com",
      "first_name": "Actual",
      "last_name": "Name"
    }
  ]
}
```

### Step 2: Add Your Real Examples

**IMPORTANT:** Add emails you've actually sent to or collected from your outreach!

```json
{
  "Goldman Sachs": [
    {"email": "john.smith@gs.com", "first_name": "John", "last_name": "Smith"},
    {"email": "sarah.johnson@gs.com", "first_name": "Sarah", "last_name": "Johnson"},
    {"email": "michael.wong@gs.com", "first_name": "Michael", "last_name": "Wong"}
  ],
  "JPMorgan": [
    {"email": "alice.chen@jpmorgan.com", "first_name": "Alice", "last_name": "Chen"},
    {"email": "bob.martinez@jpmorgan.com", "first_name": "Bob", "last_name": "Martinez"}
  ],
  "McKinsey": [
    {"email": "emily_taylor@mckinsey.com", "first_name": "Emily", "last_name": "Taylor"},
    {"email": "david_lee@mckinsey.com", "first_name": "David", "last_name": "Lee"}
  ],
  "Bain": [
    {"email": "james.anderson@bain.com", "first_name": "James", "last_name": "Anderson"}
  ],
  "Blackstone": [
    {"email": "sophia.kim@blackstone.com", "first_name": "Sophia", "last_name": "Kim"},
    {"email": "lucas.garcia@blackstone.com", "first_name": "Lucas", "last_name": "Garcia"}
  ]
}
```

### Step 3: The More Examples, The Better!

**Minimum:** 1 example = Generates 1 email pattern
**Recommended:** 3+ examples = Better pattern detection
**Ideal:** 5+ examples = Can detect multiple patterns & confidence levels

#### Why More Is Better:

**1 example:**
```json
{"email": "john.doe@company.com", "first_name": "John", "last_name": "Doe"}
→ Learns: first.last@company.com (no confidence data)
```

**3 examples with same pattern:**
```json
All use first.last@company.com
→ 🟢 HIGH confidence: This is THE pattern
```

**5 examples with mixed patterns:**
```json
3 use first.last@company.com
2 use flast@company.com
→ 🟢 first.last@company.com (60% - high confidence)
→ 🟡 flast@company.com (40% - medium confidence)
```

## Confidence Levels

| Symbol | Confidence | Meaning | Recommendation |
|--------|------------|---------|----------------|
| 🟢 | HIGH | 70%+ of examples use this pattern | Send directly |
| 🟡 | MEDIUM | 30-70% of examples use this pattern | Test with verifier |
| 🔴 | LOW | <30% or guessed (no examples) | Use as backup |

## Usage

### Quick Start

```bash
# 1. Add your examples to email_examples.json
# 2. Run the smart extractor
python3 smart_extractor.py
```

### Output

You'll get an Excel file with:
- Basic contact info (name, title, company, LinkedIn)
- Generated emails with confidence scores
- Pattern used for each email
- Source (learned vs guessed)

**Example row:**
```
Name: Samuel Dukmedjian
Company: Goldman Sachs
generated_email_1: samuel.dukmedjian@gs.com
email_1_confidence: high
email_1_pattern: first.last
email_1_source: learned
linkedin_url: https://linkedin.com/in/samuel-dukmedjian
```

## Best Practices

### 1. Quality Over Quantity
- ✅ Add emails you've successfully sent to
- ✅ Add emails from confirmed contacts
- ❌ Don't guess or make up emails

### 2. Verify Patterns
If you notice a company uses multiple patterns:
```
john.doe@gs.com
jane.smith@gs.com
bob.jones@gs.com
```
Add all of them! The system will learn both patterns.

### 3. Update Regularly
- After successful email campaigns, add working emails
- If bounces occur, check the pattern
- The more data, the smarter the system

### 4. Domain Variations
Some companies have multiple domains:
```json
"Goldman Sachs": [
  {"email": "john.doe@gs.com", ...},
  {"email": "jane.smith@goldmansachs.com", ...}
]
```
The system will learn both!

### 5. Use Both Strategies
**Best approach:**
1. LinkedIn outreach (always works, higher response rate)
2. Email outreach (high confidence emails)
3. Combine both for maximum coverage

## Testing Your Patterns

### View Learned Patterns
```python
from email_pattern_generator import EmailPatternGenerator

generator = EmailPatternGenerator()
stats = generator.get_company_stats()

for company, info in stats.items():
    print(f"{company}: {info['most_common_pattern']} @ {info['domain']}")
```

**Output:**
```
Goldman Sachs: first.last @ gs.com (3 examples)
Morgan Stanley: first.last @ morganstanley.com (2 examples)
McKinsey: first_last @ mckinsey.com (5 examples)
```

### Test Email Generation
```python
emails = generator.generate_emails("Samuel", "Dukmedjian", "Goldman Sachs")

for email in emails:
    print(f"{email['email']} - {email['confidence']}")
```

**Output:**
```
samuel.dukmedjian@gs.com - high
samueldukmedjian@gs.com - medium
s.dukmedjian@gs.com - medium
```

## Integration with Main Workflow

### Complete Workflow:

```bash
# 1. Extract contacts from RocketReach (no export credits needed)
python3 smart_extractor.py

# 2. Get Excel with:
#    - LinkedIn URLs
#    - Generated emails (🟢 high confidence)
#    - Sector classification

# 3. Outreach strategy:
#    a) Send to 🟢 high-confidence emails
#    b) Connect on LinkedIn
#    c) Test 🟡 medium-confidence emails
#    d) Use LinkedIn InMail for 🔴 low-confidence

# 4. Track results:
#    - Add working emails to email_examples.json
#    - Note bounce patterns
#    - Update and improve
```

## Example: Real-World Scenario

**You have:**
- 50 examples from previous outreach campaigns
- Targeting Investment Banking sector

**Process:**

1. **Add examples to `email_examples.json`:**
```json
{
  "Goldman Sachs": [15 examples],
  "Morgan Stanley": [12 examples],
  "JPMorgan": [18 examples],
  "Citi": [5 examples]
}
```

2. **Run smart extractor:**
```bash
python3 smart_extractor.py
# Extracts 100 contacts from these companies
```

3. **Results:**
```
📧 Email Generation:
   🟢 High confidence:   95 contacts (95%)
   🟡 Medium confidence:  5 contacts (5%)
   🔴 Low confidence:     0 contacts (0%)

🎓 Email Source:
   Learned from examples: 100 contacts (100%)
   Guessed (no examples): 0 contacts (0%)
```

4. **Outreach:**
- Send emails to 95 high-confidence addresses
- Connect on LinkedIn with all 100
- Verify 5 medium-confidence before sending

5. **Results tracking:**
- Track bounce rate (~5% expected)
- Track response rate (~15-20% for personalized)
- Add new working emails to examples

## Troubleshooting

### Issue: All emails show "low confidence"
**Cause:** No examples in `email_examples.json`
**Fix:** Add at least 1-2 examples per company

### Issue: Wrong domain generated
**Cause:** Company name mismatch
**Fix:** Ensure company name in examples matches RocketReach exactly

### Issue: Multiple patterns, all show "medium"
**Cause:** Company uses multiple patterns equally
**Solution:** This is normal! Send to all generated emails or test first

### Issue: Names with special characters
**Cause:** Names like "O'Brien" or "José"
**Solution:** System handles this automatically:
- O'Brien → obrien
- José García → jose.garcia

## Advanced: Adding Examples Programmatically

```python
from email_pattern_generator import EmailPatternGenerator

generator = EmailPatternGenerator()

# Add new example
generator.add_example(
    company="Goldman Sachs",
    email="new.person@gs.com",
    first_name="New",
    last_name="Person"
)

# Save to file
generator.save_examples()
```

## Summary

**The email pattern generator solves your export credit problem by:**

✅ Learning from your existing email examples
✅ Generating probable emails for new contacts
✅ Providing confidence scores
✅ No API credits needed
✅ Works with search-only mode

**Your emails + their names/companies = Complete contact database**

---

**Next Step:** Add your hundreds of real email examples to `email_examples.json` and watch the magic happen!
