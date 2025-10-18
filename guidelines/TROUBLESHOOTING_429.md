# Troubleshooting 429 Errors (Too Many Requests)

## What Happened

You received 429 errors from the RocketReach API, which means you hit their rate limits.

## Fixes Applied

### 1. More Conservative Limits
Changed from 90% to **80% of your actual limits**:
- Minute: 12 of 15 (was 13)
- Hourly: 40 of 50 (was 45)
- Daily: 400 of 500 (was 450)
- Monthly: 8,000 of 10,000 (was 9,000)

### 2. Fixed Timing Issue
- Now records API calls AFTER they're made (not before)
- Adds +2 second safety buffer when waiting
- Re-cleans call list after sleeping

### 3. Proper Call Recording
- `_record_api_call()` is now called after each successful request
- Prevents timing mismatches

## If You Still Get 429 Errors

### Option 1: Wait It Out
If you hit 429 errors, wait:
- **1 hour** if you hit the hourly limit
- **5 minutes** if you hit the minute limit

Then run the script again - it will skip already-contacted people.

### Option 2: Even More Conservative
Edit line ~34-38 in `smart_finance_extractor.py` to be even more conservative:

```python
self.rate_limits = {
    'minute': {'limit': 10, 'window': 60},        # 10 of 15 (66%)
    'hour': {'limit': 35, 'window': 3600},        # 35 of 50 (70%)
    'day': {'limit': 350, 'window': 86400},       # 350 of 500 (70%)
    'month': {'limit': 7000, 'window': 2592000}   # 7000 of 10,000 (70%)
}
```

### Option 3: Add Exponential Backoff
If you want to handle 429 errors gracefully, I can add automatic retry logic.

## Why This Happened

Possible reasons:
1. **Previous runs** - API calls from earlier runs still counting toward limits
2. **Network delays** - Requests bunching up despite rate limiting
3. **RocketReach's internal limits** - They may have additional undocumented limits

## Current Status

After the fixes:
- ✅ More conservative limits (80% vs 90%)
- ✅ Proper timing (records after call)
- ✅ Safety buffer (+2 seconds)
- ✅ Better call tracking

## How to Resume

The script tracks all contacted people, so you can safely resume:

```bash
# Wait 1 hour for limits to reset
sleep 3600

# Run again - it will skip already-contacted people
python3 smart_finance_extractor.py
```

## Checking Your Current Usage

If you want to know your actual RocketReach usage, log into your RocketReach dashboard:
- https://rocketreach.co/dashboard

Look for:
- API usage this hour
- API usage today
- API usage this month

Compare with your limits:
- Minute: 15
- Hour: 50
- Day: 500
- Month: 10,000

## Recommended Approach

Given the 429 errors, I recommend:

### Run in Small Batches

**Batch 1**: 3-5 companies
```python
target_companies = ["Goldman Sachs", "Morgan Stanley", "J.P. Morgan"]
```

**Wait 1 hour between batches**

**Batch 2**: Next 3-5 companies
```python
target_companies = ["Blackstone", "KKR", "Citadel"]
```

This way:
- You stay well within limits
- You get consistent results
- You can monitor progress
- Less risk of hitting limits

### Time Estimation Per Batch (3 companies)

- ~24 searches (3 companies × 8 locations)
- ~51 lookups (if all quotas filled: 3 × 17)
- **Total**: ~75 API calls
- **Time**: ~6 minutes at 12 calls/minute

You can comfortably run **8 batches per hour** with this approach!

## Prevention

To avoid 429 errors in future:

1. ✅ Use updated script (fixes applied)
2. ✅ Run in smaller batches
3. ✅ Check RocketReach dashboard before large runs
4. ✅ Wait between batches if doing multiple runs
5. ✅ Monitor console output for rate limit warnings

## Emergency: Hit Daily Limit?

If you hit the daily limit (500 calls):
- **Stop immediately**
- **Wait until midnight** (RocketReach timezone)
- **Resume the next day**

The script remembers all contacted people, so you won't lose progress!
