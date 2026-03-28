#!/bin/bash
# Sync pipeline.db AND PA handler files from Mac to EC2
# Runs automatically via cross_tower_sync (every 5 min) and after every save.sh push
#
# Strategy: Mac is primary, EC2 gets copies.

EC2_HOST="ec2-user@34.193.98.97"
EC2_KEY="$HOME/.ssh/marceau-ec2-key.pem"
MAC_DB="$HOME/dev-sandbox/projects/lead-generation/sales-pipeline/data/pipeline.db"
EC2_DB="/home/clawdbot/data/pipeline.db"
PA_SRC="$HOME/dev-sandbox/projects/personal-assistant/src"
EC2_PA="/home/clawdbot/pa-handlers"

LAST_SYNC="$HOME/dev-sandbox/projects/personal-assistant/logs/.last_pipeline_sync"
LAST_CODE_SYNC="$HOME/dev-sandbox/projects/personal-assistant/logs/.last_code_sync"

synced=""

# 1. Sync pipeline.db (only if changed)
if [ -f "$MAC_DB" ]; then
    if [ -f "$LAST_SYNC" ]; then
        mac_mod=$(stat -f %m "$MAC_DB" 2>/dev/null || stat -c %Y "$MAC_DB" 2>/dev/null)
        last_sync=$(cat "$LAST_SYNC")
        if [ "$mac_mod" != "$last_sync" ]; then
            scp -i "$EC2_KEY" -o ConnectTimeout=5 -q "$MAC_DB" "$EC2_HOST:/tmp/pipeline_sync.db" 2>/dev/null
            if [ $? -eq 0 ]; then
                ssh -i "$EC2_KEY" -o ConnectTimeout=5 "$EC2_HOST" "sudo cp /tmp/pipeline_sync.db $EC2_DB && sudo chown clawdbot:clawdbot $EC2_DB" 2>/dev/null
                if [ $? -eq 0 ]; then
                    echo "$mac_mod" > "$LAST_SYNC"
                    synced="${synced}pipeline.db "
                fi
            fi
        fi
    else
        # First sync
        scp -i "$EC2_KEY" -o ConnectTimeout=5 -q "$MAC_DB" "$EC2_HOST:/tmp/pipeline_sync.db" 2>/dev/null
        if [ $? -eq 0 ]; then
            ssh -i "$EC2_KEY" -o ConnectTimeout=5 "$EC2_HOST" "sudo cp /tmp/pipeline_sync.db $EC2_DB && sudo chown clawdbot:clawdbot $EC2_DB" 2>/dev/null
            stat -f %m "$MAC_DB" > "$LAST_SYNC" 2>/dev/null || stat -c %Y "$MAC_DB" > "$LAST_SYNC" 2>/dev/null
            synced="${synced}pipeline.db "
        fi
    fi
fi

# 2. Sync PA handler code (only if .py files changed since last code sync)
newest_py=$(find "$PA_SRC" -name "*.py" -newer "$LAST_CODE_SYNC" 2>/dev/null | head -1)
if [ -n "$newest_py" ] || [ ! -f "$LAST_CODE_SYNC" ]; then
    # Copy the key handler files
    scp -i "$EC2_KEY" -o ConnectTimeout=5 -q \
        "$PA_SRC/clawdbot_handlers.py" \
        "$PA_SRC/goal_manager.py" \
        "$PA_SRC/goal_progress.py" \
        "$EC2_HOST:/tmp/" 2>/dev/null
    if [ $? -eq 0 ]; then
        ssh -i "$EC2_KEY" -o ConnectTimeout=5 "$EC2_HOST" \
            "sudo cp /tmp/clawdbot_handlers.py /tmp/goal_manager.py /tmp/goal_progress.py $EC2_PA/ && sudo chown clawdbot:clawdbot $EC2_PA/*.py" 2>/dev/null
        if [ $? -eq 0 ]; then
            touch "$LAST_CODE_SYNC"
            synced="${synced}handlers "
            # Restart the PA service to pick up new code (separate SSH calls for reliability)
            ssh -i "$EC2_KEY" -o ConnectTimeout=5 "$EC2_HOST" "sudo pkill -f 'uvicorn.*8786'" 2>/dev/null
            sleep 2
            ssh -i "$EC2_KEY" -o ConnectTimeout=5 "$EC2_HOST" "sudo -u clawdbot bash -c 'cd $EC2_PA && nohup python3 -m uvicorn service:app --host 127.0.0.1 --port 8786 > service.log 2>&1 &'" 2>/dev/null
            synced="${synced}(restarted) "
        fi
    fi
fi

# 3. Sync goals.json
if [ -f "$HOME/dev-sandbox/projects/personal-assistant/data/goals.json" ]; then
    scp -i "$EC2_KEY" -o ConnectTimeout=5 -q \
        "$HOME/dev-sandbox/projects/personal-assistant/data/goals.json" \
        "$EC2_HOST:/tmp/goals_sync.json" 2>/dev/null
    if [ $? -eq 0 ]; then
        ssh -i "$EC2_KEY" -o ConnectTimeout=5 "$EC2_HOST" \
            "sudo cp /tmp/goals_sync.json $EC2_PA/data/goals.json && sudo chown clawdbot:clawdbot $EC2_PA/data/goals.json" 2>/dev/null
    fi
fi

if [ -n "$synced" ]; then
    echo "$(date): Synced to EC2: $synced"
fi
