# Schema Mismatch Fix Summary

**Date**: 2026-01-20
**Issue**: ScheduledPost dataclass missing required fields, blocking 175 posts from processing

## Problem

The `business_scheduler.py` was creating posts with fields that didn't exist in the `ScheduledPost` dataclass:
- `business_id`
- `template_type`
- `generate_image`

Additionally, `business_scheduler.py` posts were missing required fields from the original `ScheduledPost`:
- `id` (required positional argument)
- `priority`, `status`, `created_at`, etc.

This created two incompatible post formats in the queue file, causing the error:
```
WARNING: Error loading queue: ScheduledPost.__init__() got an unexpected keyword argument 'business_id'
```

## Solution

### 1. Updated ScheduledPost Dataclass

**File**: `/Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/social-media-automation/src/x_scheduler.py`

Added three missing fields to the dataclass (lines 81-83):
```python
business_id: Optional[str] = None
template_type: Optional[str] = None
generate_image: bool = False
```

### 2. Implemented Queue Migration Logic

Enhanced `_load_queue()` method to handle both old and new post formats:

**For posts missing `id` field** (from business_scheduler):
- Generate deterministic ID using MD5 hash of text + scheduled_time

**For posts missing new fields** (from old x_scheduler):
- Add default values: `business_id=None`, `template_type=None`, `generate_image=False`

**For posts missing old fields** (from business_scheduler):
- Add defaults for all required ScheduledPost fields

### 3. Fixed Cron Job Paths

**Old path** (incorrect):
```
/Users/williammarceaujr./dev-sandbox/projects/social-media-automation
```

**New path** (correct):
```
/Users/williammarceaujr./dev-sandbox/projects/shared-multi-tenant/social-media-automation
```

**Script**: `update_cron_jobs.sh` - Updates all 9 cron jobs to use correct path

## Verification

### Before Fix
```bash
python -m src.business_scheduler process --max 5
# WARNING: Error loading queue: ScheduledPost.__init__() got an unexpected keyword argument 'business_id'
# INFO: No posts ready to process
```

### After Fix
```bash
python -m src.business_scheduler process --max 5
# Processed 1 posts (rate limited after first post)
# INFO: Tweet posted successfully: 2013695347218915677
```

### Queue Statistics
```
Total posts: 180
  - Posted: 6
  - Pending: 174

By Campaign:
  - ai-automation-agency: 175
  - squarefoot-shipping-general-awareness: 2
  - swflorida-hvac-general-awareness: 2
  - fitness-launch: 1
```

## Impact

✅ **Schema mismatch resolved** - All 180 posts now load successfully
✅ **175 pending posts unblocked** - Can now be processed by automated system
✅ **Automated posting resumed** - Cron jobs will process queue at scheduled times
✅ **No data loss** - All existing posts preserved with proper migration
✅ **Forward compatibility** - Future posts from both systems will work

## Next Steps

1. Monitor automated posting via cron jobs (every 2 hours from 8am-10pm)
2. Check posting.log for any issues: `tail -f output/posting.log`
3. Rate limit allows ~25 posts/day, so 174 pending posts will clear in ~7 days
4. Queue will auto-replenish via `daily-run` at 6am each day

## Files Modified

1. `src/x_scheduler.py` - Added 3 fields to ScheduledPost dataclass + migration logic
2. `update_cron_jobs.sh` - Script to fix cron job paths (one-time use)
3. Crontab - Updated 9 cron jobs with correct paths

## Cron Schedule (Now Active)

```
0  6 * * * daily-run (generate 3 days ahead + process queue)
0  8 * * * process (post ready items)
0 10 * * * process
0 12 * * * process
0 14 * * * process
0 16 * * * process
0 18 * * * process
0 20 * * * process
0 22 * * * process
```

Expected posting rate: ~25 posts/day (X API rate limit)
