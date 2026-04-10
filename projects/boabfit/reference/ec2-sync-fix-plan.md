# EC2 Sync Fix Plan

## Problem
Two separate dev-sandbox directories on EC2:
- `/home/ec2-user/dev-sandbox/` — no .git, loose files, where all BOABFIT work was built today
- `/home/clawdbot/dev-sandbox/` — has .git, synced with GitHub, where the sync hook pulls to

The post-push sync hook pulls to clawdbot's repo. All SSH work writes to ec2-user's directory.
They are completely disconnected. Changes made on one don't appear on the other.

## Root Cause
When services and scripts were created via SSH as ec2-user, they wrote to ec2-user's home directory.
The git-synced repo lives under clawdbot's home directory. No one caught the divergence.

## Solution
Consolidate to ONE directory. The git-synced `/home/clawdbot/dev-sandbox/` should be the single source of truth.

### Step 1: Inventory what's on ec2-user that isn't on clawdbot
- BOABFIT scripts (src/)
- BOABFIT data files (data/)
- Julia response monitor service
- Any other services pointing to ec2-user paths

### Step 2: Copy unique files from ec2-user to clawdbot repo
- Only files that don't exist in the clawdbot repo
- Don't overwrite clawdbot's git-tracked files

### Step 3: Update all systemd services to use clawdbot paths
- julia-response-monitor.service
- boabfit-relay.service
- Any other services referencing /home/ec2-user/dev-sandbox/

### Step 4: Update the sync hook
- Ensure it pulls as clawdbot user to /home/clawdbot/dev-sandbox/
- SSH commands from Mac should write to /home/clawdbot/dev-sandbox/ not ec2-user

### Step 5: Create symlink for backward compatibility
- `ln -s /home/clawdbot/dev-sandbox /home/ec2-user/dev-sandbox`
- This way any existing scripts that reference ec2-user paths still work

### Step 6: Verify
- Push from Mac → sync hook fires → clawdbot repo updates → services see new code
- SSH from Mac → writes to clawdbot repo (via symlink) → git tracks changes

## Risk
- Services will restart when paths change
- Existing cron jobs or n8n SSH nodes may reference ec2-user paths
- Need to grep all systemd units, cron tabs, and n8n workflows for /home/ec2-user/dev-sandbox/

## When to Do This
- Tomorrow — needs careful execution, not a late-night rush
- Back up both directories first
