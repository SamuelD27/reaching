# Rate Limits Update

## Your RocketReach Limits

Based on your account, your actual limits are:

| Time Window | Limit |
|-------------|-------|
| **Minute**  | 15    |
| **Hourly**  | 50    |
| **Daily**   | 500   |
| **Monthly** | 10,000|

## What Changed

### Before
- Only tracked per-minute limits
- Used hardcoded limit of 14 per minute
- Didn't track hourly, daily, or monthly usage

### After ✅
- Tracks **all four time windows** (minute, hour, day, month)
- Uses **conservative limits** (90% of actual) to stay safe:
  - Minute: 13 of 15 (87%)
  - Hourly: 45 of 50 (90%)
  - Daily: 450 of 500 (90%)
  - Monthly: 9,000 of 10,000 (90%)
- Automatically waits when any limit is reached
- Shows which limit triggered the wait

## How It Works

The script now:

1. **Tracks every API call** (searches + lookups together)
2. **Before each call**, checks all time windows:
   - How many calls in last 60 seconds?
   - How many calls in last hour?
   - How many calls in last day?
   - How many calls in last month?
3. **If any limit reached**, waits until oldest call expires
4. **Makes the call** and records the timestamp

## Example Output

When rate limits are hit, you'll see:

```
⏳ Rate limit (minute): 13/13 - waiting 25s...
```

or

```
⏳ Rate limit (hour): 45/45 - waiting 245s...
```

This tells you:
- Which time window triggered the wait
- Current usage vs limit
- How long to wait

## Rate Limit Status

You can check your current usage programmatically:

```python
status = extractor.get_rate_limit_status()
print(status)

# Output:
# {
#   'minute': {'used': 5, 'limit': 13, 'remaining': 8, 'percentage': 38.5},
#   'hour': {'used': 20, 'limit': 45, 'remaining': 25, 'percentage': 44.4},
#   'day': {'used': 100, 'limit': 450, 'remaining': 350, 'percentage': 22.2},
#   'month': {'used': 500, 'limit': 9000, 'remaining': 8500, 'percentage': 5.6}
# }
```

## Why Conservative Limits?

We use 90% of your actual limits (87% for minute) because:

1. **Safety margin** - Prevents accidental overages
2. **API delays** - Network delays might cause calls to cluster
3. **Other tools** - If you use RocketReach elsewhere, you have room
4. **Peace of mind** - Better to be slightly slower than hit hard limits

## Adjusting Limits

If you want to be more aggressive (use full limits), edit line ~34-38 in `smart_finance_extractor.py`:

```python
self.rate_limits = {
    'minute': {'limit': 15, 'window': 60},        # Full limit
    'hour': {'limit': 50, 'window': 3600},        # Full limit
    'day': {'limit': 500, 'window': 86400},       # Full limit
    'month': {'limit': 10000, 'window': 2592000}  # Full limit
}
```

## Estimation: Full Run

If you extract from **all 80 companies**:

### API Calls Needed
- **1 search per location per company** = 8 locations × 80 companies = 640 searches
- **~17 lookups per company** (if all locations have people) = 80 × 17 = 1,360 lookups
- **Total**: ~2,000 API calls

### Time Required

**Minute limit** (most restrictive for bulk operations):
- 13 calls per minute
- 2,000 calls ÷ 13 = ~154 minutes = **2.5 hours**

**Hourly limit**:
- 45 calls per hour
- 2,000 calls ÷ 45 = ~45 hours (but minute limit prevents this)

**In practice**:
- The script will throttle to stay within all limits
- Expect **2-3 hours** for a full run of all 80 companies
- You can split into smaller batches to run over multiple days

### Recommended Approach

**Day 1**: Investment Banking (27 companies)
- ~680 API calls
- ~52 minutes

**Day 2**: Hedge Funds (15 companies)
- ~380 API calls
- ~29 minutes

**Day 3**: Private Equity (15 companies)
- ~380 API calls
- ~29 minutes

**Day 4**: Consulting (9 companies)
- ~230 API calls
- ~18 minutes

**Day 5**: Venture Capital (14 companies)
- ~350 API calls
- ~27 minutes

## Benefits

✅ **Never hit API limits** - Automatic throttling
✅ **Track all time windows** - Minute, hour, day, month
✅ **Transparent** - See which limit is active
✅ **Safe** - Conservative 90% usage
✅ **Efficient** - Makes calls as fast as limits allow

## Testing

The rate limiting is working if you see:
- Smooth execution with occasional pauses
- Clear messages when waiting
- No 429 (Too Many Requests) errors from API

If you want to test, run:
```bash
python3 smart_finance_extractor.py
```

Watch for rate limit messages in the output.
