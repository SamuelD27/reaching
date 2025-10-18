# Background Execution Guide

## New Features Added ✅

### 1. Max Total Contacts Limit
You can now set a maximum number of total contacts to extract:

```python
MAX_TOTAL_CONTACTS = 500  # Stop after 500 contacts
```

Set to `None` for unlimited extraction.

### 2. Fully Automated Operation
The script now:
- ✅ Runs completely automatically
- ✅ Handles rate limits by waiting and resuming
- ✅ No user input required
- ✅ Can run in background while you do other work
- ✅ Saves results automatically when done
- ✅ Saves partial results if interrupted

## How to Configure

Edit lines ~693-694 in `smart_finance_extractor.py`:

```python
# CONFIGURATION: Set your extraction limits here
MAX_TOTAL_CONTACTS = 500      # Stop after extracting this many contacts (None = unlimited)
MAX_PER_COMPANY = 20          # Maximum contacts per company
```

### Examples

**Extract exactly 100 contacts:**
```python
MAX_TOTAL_CONTACTS = 100
MAX_PER_COMPANY = 10
```

**Extract up to 1000 contacts:**
```python
MAX_TOTAL_CONTACTS = 1000
MAX_PER_COMPANY = 20
```

**Unlimited extraction:**
```python
MAX_TOTAL_CONTACTS = None
MAX_PER_COMPANY = 20
```

## Running in Background

### Method 1: Simple Background (Recommended for Mac/Linux)

```bash
# Run in background
python3 smart_finance_extractor.py > extraction.log 2>&1 &

# Save the process ID
echo $! > extraction.pid

# Check progress anytime
tail -f extraction.log

# Stop if needed
kill $(cat extraction.pid)
```

### Method 2: Using `nohup` (Survives terminal close)

```bash
# Run with nohup
nohup python3 smart_finance_extractor.py > extraction.log 2>&1 &

# Check progress
tail -f extraction.log

# Find process if you forgot PID
ps aux | grep smart_finance_extractor

# Stop if needed
killall -9 python3  # BE CAREFUL: kills all Python processes
```

### Method 3: Using `screen` (Detachable terminal)

```bash
# Start a screen session
screen -S extraction

# Run the script
python3 smart_finance_extractor.py

# Detach: Press Ctrl+A then D

# Reattach anytime to check progress
screen -r extraction

# Kill the session when done
screen -X -S extraction quit
```

### Method 4: Using `tmux` (Alternative to screen)

```bash
# Start tmux session
tmux new -s extraction

# Run the script
python3 smart_finance_extractor.py

# Detach: Press Ctrl+B then D

# Reattach anytime
tmux attach -t extraction

# Kill when done
tmux kill-session -t extraction
```

## What Happens When Running

### Startup
```
🤖 AUTOMATED EXTRACTION MODE
================================================================================
This script will run fully automatically in the background.
It will handle rate limits by waiting and resuming automatically.
Max total contacts: 500
Max per company: 20
================================================================================

You can minimize this window and do other work.
The script will save results when done.
```

### During Extraction

The script shows progress:
```
[1/10] Processing: Goldman Sachs
Total extracted so far: 0/500

  📍 Tier 1 Locations (quota: 3 each):
    🌍 Singapore...
       Found 12 senior profiles
       🔍 Fetching: John Smith - Managing Director
       ✅ Added (1/3) [Total: 1]
       ...
```

### Rate Limiting

When it hits a limit, it automatically waits:
```
⏳ Rate limit (minute): 12/12 - waiting 45s...
```

You don't need to do anything - it will resume automatically!

### Completion

```
🎉 Extraction complete!
📊 Total contacts extracted: 500
💾 Results saved to: smart_finance_contacts.xlsx
```

## Monitoring Progress

### Check How Many Extracted So Far

```bash
# Count lines in output file (if it exists)
wc -l smart_finance_contacts.xlsx

# Or check the log
grep "Total extracted so far" extraction.log | tail -1
```

### Check Rate Limit Status

```bash
# See recent rate limit messages
grep "Rate limit" extraction.log | tail -5
```

### Check Which Company Being Processed

```bash
# See current company
grep "Processing:" extraction.log | tail -1
```

## Interrupting the Script

### Graceful Stop (Saves Partial Results)

```bash
# Press Ctrl+C in the terminal
# Or send interrupt signal
kill -INT $(cat extraction.pid)
```

This will:
1. Stop extraction
2. Save partial results to `smart_finance_contacts_partial.xlsx`
3. Exit cleanly

### Force Stop (No Save)

```bash
kill -9 $(cat extraction.pid)
```

Use only if script is frozen.

## Estimating Time

With your rate limits (12 calls/minute after safety margin):

| Contacts | API Calls | Time Estimate |
|----------|-----------|---------------|
| 50 | ~100 | ~8 minutes |
| 100 | ~200 | ~17 minutes |
| 200 | ~400 | ~33 minutes |
| 500 | ~1000 | ~83 minutes (~1.4 hours) |
| 1000 | ~2000 | ~167 minutes (~2.8 hours) |

These are estimates. Actual time depends on:
- How many people are already contacted (skipped)
- How many senior positions are available
- Network speed
- RocketReach API response time

## Output Files

### Main Output
`smart_finance_contacts.xlsx` - Final results with all contacts

### Partial Output (if interrupted)
`smart_finance_contacts_partial.xlsx` - Results up to interruption point

### History File
`contact_history.json` - All contacted people (for deduplication)

### Log File (if using background method)
`extraction.log` - Full console output for monitoring

## Tips for Long Runs

### 1. Start Small
Test with a small limit first:
```python
MAX_TOTAL_CONTACTS = 50
```

### 2. Use Logging
Always log to a file when running in background:
```bash
python3 smart_finance_extractor.py > extraction.log 2>&1 &
```

### 3. Check Progress Periodically
```bash
tail -f extraction.log
```

### 4. Run During Off-Hours
For very large extractions (1000+ contacts), run overnight:
```bash
# Start at night
nohup python3 smart_finance_extractor.py > extraction.log 2>&1 &

# Check in morning
tail extraction.log
```

### 5. Split Into Batches
For maximum control, extract by sector across multiple runs:

**Day 1: Investment Banking**
```python
target_companies = extractor.finance_companies["Investment Banking"]
MAX_TOTAL_CONTACTS = 200
```

**Day 2: Hedge Funds**
```python
target_companies = extractor.finance_companies["Hedge Fund"]
MAX_TOTAL_CONTACTS = 150
```

And so on...

## Troubleshooting

### Script Not Starting
```bash
# Check API key is set
echo $ROCKETREACH_API_KEY

# If not set:
export ROCKETREACH_API_KEY="your_key_here"
```

### Script Stops Unexpectedly
Check `extraction.log` for errors:
```bash
tail -50 extraction.log
```

Common issues:
- Internet connection lost
- RocketReach API down
- Hit daily limit (500 calls)

### Can't Find Process
```bash
# List all Python processes
ps aux | grep python

# Or specifically this script
ps aux | grep smart_finance
```

### Results File Missing
The file is only created when extraction completes or is interrupted (Ctrl+C).

If script crashes, results may not be saved.

## Example: Overnight Run

```bash
# Evening: Start extraction for 500 contacts
cd ~/Desktop/reaching_tool
export ROCKETREACH_API_KEY="your_key"

# Configure for 500 contacts
# Edit smart_finance_extractor.py: MAX_TOTAL_CONTACTS = 500

# Run in background with logging
nohup python3 smart_finance_extractor.py > extraction.log 2>&1 &

# Note the process ID
echo $! > extraction.pid
echo "Started extraction at $(date)"

# Go to sleep!

# Morning: Check results
cd ~/Desktop/reaching_tool
tail -100 extraction.log

# Open results
open smart_finance_contacts.xlsx
```

## Safety Features

The script is safe for background operation because:

1. ✅ **Automatic rate limiting** - Never exceeds your limits
2. ✅ **Deduplication** - Never contacts same person twice
3. ✅ **Progress tracking** - Always knows where it left off
4. ✅ **Graceful interruption** - Saves partial results if stopped
5. ✅ **Error handling** - Logs errors and continues when possible
6. ✅ **No user input needed** - Runs completely automated

## Need Help?

If the script stops or you see errors:
1. Check `extraction.log` for error messages
2. Verify your API key is correct
3. Check RocketReach dashboard for usage limits
4. Wait 1 hour if you hit rate limits
5. Try again with smaller `MAX_TOTAL_CONTACTS`

The script remembers all contacted people, so you can always resume safely!
