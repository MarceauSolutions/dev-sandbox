# Mem0 Deployment Checklist

> Step-by-step deployment guide with verification at each stage

---

## Pre-Deployment Checklist

- [ ] EC2 SSH access working: `ssh ec2`
- [ ] Python 3 installed on EC2: `ssh ec2 'python3 --version'`
- [ ] dev-sandbox directory exists: `ssh ec2 'ls /home/ubuntu/dev-sandbox'`
- [ ] OPENAI_API_KEY in .env: `ssh ec2 'grep OPENAI_API_KEY /home/ubuntu/dev-sandbox/.env'`
- [ ] Port 5020 not in use: `ssh ec2 'sudo lsof -i :5020'` (should be empty)
- [ ] Disk space available: `ssh ec2 'df -h /home/ubuntu'` (need >1GB free)

---

## Deployment Steps

### Step 1: Upload Files to EC2

```bash
cd /Users/williammarceaujr./dev-sandbox

# Upload all Mem0 files
scp execution/mem0_api.py ec2:/home/ubuntu/dev-sandbox/execution/
scp execution/mem0-api.service ec2:/home/ubuntu/dev-sandbox/execution/
scp execution/install_mem0_ec2.sh ec2:/home/ubuntu/dev-sandbox/execution/
scp execution/test_mem0_api.py ec2:/home/ubuntu/dev-sandbox/execution/
scp execution/mem0_client.py ec2:/home/ubuntu/dev-sandbox/execution/
```

**Verification:**
```bash
ssh ec2 'ls -lh /home/ubuntu/dev-sandbox/execution/mem0*'
```

Expected: 5 files (mem0_api.py, mem0-api.service, mem0_client.py, install script, test script)

- [ ] Files uploaded successfully

---

### Step 2: Make Scripts Executable

```bash
ssh ec2 'chmod +x /home/ubuntu/dev-sandbox/execution/install_mem0_ec2.sh'
ssh ec2 'chmod +x /home/ubuntu/dev-sandbox/execution/test_mem0_api.py'
ssh ec2 'chmod +x /home/ubuntu/dev-sandbox/execution/mem0_client.py'
```

**Verification:**
```bash
ssh ec2 'ls -l /home/ubuntu/dev-sandbox/execution/*.sh | grep rwx'
```

- [ ] Scripts are executable

---

### Step 3: Run Installer

```bash
ssh ec2 'bash /home/ubuntu/dev-sandbox/execution/install_mem0_ec2.sh'
```

**Expected Output:**
```
==========================================
Installing Mem0 API on EC2
==========================================

[1/6] Installing Python dependencies...
[2/6] Creating Mem0 database directory...
[3/6] Testing Mem0 API locally...
[4/6] Installing systemd service...
[5/6] Enabling and starting service...
[6/6] Checking service status...
...
Installation Complete!
```

**Watch for:**
- ✓ All dependencies installed
- ✓ Database directory created
- ✓ Test startup successful
- ✓ Service started

- [ ] Installation completed without errors

---

### Step 4: Verify Service Status

```bash
ssh ec2 'sudo systemctl status mem0-api'
```

**Expected:**
```
● mem0-api.service - Mem0 Agent Memory API
   Loaded: loaded (/etc/systemd/system/mem0-api.service; enabled)
   Active: active (running) since ...
   ...
```

Look for:
- ✓ `Active: active (running)`
- ✓ No error messages
- ✓ Process ID shown

- [ ] Service is running

---

### Step 5: Test Health Endpoint

```bash
ssh ec2 'curl http://localhost:5020/health'
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "mem0-api",
  "timestamp": "2026-02-15T...",
  "collection": "agent_memory",
  "db_path": "/home/ubuntu/.mem0/chroma_db"
}
```

- [ ] Health check returns "healthy"

---

### Step 6: Run Automated Test Suite

```bash
ssh ec2 'cd /home/ubuntu/dev-sandbox && python3 -m execution.test_mem0_api'
```

**Expected:**
```
============================================================
# Mem0 API Test Suite
# Target: http://localhost:5020
============================================================

============================================================
TEST: Health Check
============================================================
✓ PASS: Health check passed

============================================================
TEST: Add Memory
============================================================
✓ PASS: Memory added successfully

============================================================
TEST: Search Memory
============================================================
✓ PASS: Search returned N results

============================================================
TEST: List All Memories
============================================================
✓ PASS: Found N total memories

============================================================
TEST SUMMARY
============================================================
✓ PASS: Health Check
✓ PASS: Add Memory
✓ PASS: Search Memory
✓ PASS: List All Memories

Total: 4/4 tests passed
```

- [ ] All tests passed

---

### Step 7: Manual API Test

```bash
# Add a test memory
ssh ec2 'curl -X POST http://localhost:5020/memory \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\": \"test-agent\", \"content\": \"Manual deployment test\", \"metadata\": {\"source\": \"deployment\"}}"'
```

**Expected:**
```json
{
  "status": "success",
  "result": { ... },
  "agent_id": "test-agent",
  "content": "Manual deployment test",
  ...
}
```

- [ ] Can add memories via API

```bash
# Search for it
ssh ec2 'curl "http://localhost:5020/memory/search?q=deployment&agent_id=test-agent"'
```

**Expected:**
```json
{
  "status": "success",
  "query": "deployment",
  "count": 1,
  "results": [ ... ]
}
```

- [ ] Can search memories via API

---

### Step 8: Check Resource Usage

```bash
ssh ec2 'systemctl status mem0-api | grep Memory'
```

**Expected:**
```
   Memory: 150.0M (max: 400.0M available: 250.0M)
```

Memory usage should be **under 300MB**.

- [ ] Memory usage is within limits

```bash
ssh ec2 'ps aux | grep mem0_api'
```

Check CPU usage (should be <10% at idle).

- [ ] CPU usage is reasonable

---

### Step 9: Check Logs

```bash
ssh ec2 'sudo journalctl -u mem0-api -n 50'
```

**Look for:**
- ✓ "Starting Mem0 API..."
- ✓ "Mem0 initialized successfully"
- ✓ No ERROR or CRITICAL messages

- [ ] Logs show normal operation

---

### Step 10: Test Client Library

```bash
ssh ec2 'cd /home/ubuntu/dev-sandbox && python3 -m execution.mem0_client'
```

**Expected:**
```
API Status: healthy

=== Mem0 Client Demo ===

1. Adding memory...
   Added: success

2. Searching for 'test'...
   Found N results

3. Listing all memories...
   Total memories: N

4. Counting memories...
   Count: N

=== Demo Complete ===
```

- [ ] Client library works

---

## Post-Deployment Verification

### Database Files

```bash
ssh ec2 'ls -lh ~/.mem0/'
```

**Expected:**
```
drwxrwxr-x chroma_db/
-rw-rw-r-- history.db
```

- [ ] ChromaDB directory exists
- [ ] SQLite history database exists

### Service Persistence

```bash
# Restart service
ssh ec2 'sudo systemctl restart mem0-api'

# Wait 3 seconds
sleep 3

# Check it came back up
ssh ec2 'curl http://localhost:5020/health'
```

- [ ] Service restarts successfully

### Auto-Start on Boot

```bash
ssh ec2 'sudo systemctl is-enabled mem0-api'
```

**Expected:** `enabled`

- [ ] Service is enabled for auto-start

---

## Integration Tests

### From n8n (Manual)

If n8n is running:

1. Create HTTP Request node
2. Method: POST
3. URL: `http://localhost:5020/memory`
4. Body:
   ```json
   {
     "agent_id": "n8n-test",
     "content": "Integration test from n8n",
     "metadata": {"source": "n8n"}
   }
   ```
5. Execute

- [ ] n8n can write to Mem0 API (if applicable)

### From Agent Bridge API (Optional)

```bash
ssh ec2 'curl http://localhost:5010/health'
```

If Agent Bridge is running, test integration:

```python
# Add to agent_bridge_api.py test
import requests
response = requests.post("http://localhost:5020/memory", json={
    "agent_id": "agent-bridge",
    "content": "Bridge test",
    "metadata": {}
})
print(response.json())
```

- [ ] Agent Bridge can access Mem0 API (if applicable)

---

## Troubleshooting Checklist

### If Service Won't Start

- [ ] Check OPENAI_API_KEY is set: `ssh ec2 'grep OPENAI_API_KEY /home/ubuntu/dev-sandbox/.env'`
- [ ] Check Python dependencies: `ssh ec2 'python3 -m pip list | grep -E "mem0|fastapi|uvicorn"'`
- [ ] Check logs: `ssh ec2 'sudo journalctl -u mem0-api -n 100'`
- [ ] Check port availability: `ssh ec2 'sudo lsof -i :5020'`

### If Health Check Fails

- [ ] Service is running: `ssh ec2 'sudo systemctl status mem0-api'`
- [ ] Port is listening: `ssh ec2 'sudo lsof -i :5020'`
- [ ] Firewall not blocking: `ssh ec2 'sudo iptables -L | grep 5020'`
- [ ] Test direct curl: `ssh ec2 'curl -v http://localhost:5020/health'`

### If Tests Fail

- [ ] API is accessible: `ssh ec2 'curl http://localhost:5020/health'`
- [ ] Dependencies installed: `ssh ec2 'python3 -m pip list | grep requests'`
- [ ] Run tests with verbose: `ssh ec2 'cd dev-sandbox && python3 -m execution.test_mem0_api -v'`

### If Memory Usage Too High

- [ ] Check current usage: `ssh ec2 'systemctl status mem0-api | grep Memory'`
- [ ] Restart service: `ssh ec2 'sudo systemctl restart mem0-api'`
- [ ] Reduce limits in service file if needed

---

## Rollback Plan

If deployment fails and you need to rollback:

```bash
# Stop and disable service
ssh ec2 'sudo systemctl stop mem0-api'
ssh ec2 'sudo systemctl disable mem0-api'

# Remove service file
ssh ec2 'sudo rm /etc/systemd/system/mem0-api.service'
ssh ec2 'sudo systemctl daemon-reload'

# Remove database (optional)
ssh ec2 'rm -rf ~/.mem0/'

# Uninstall packages (optional)
ssh ec2 'python3 -m pip uninstall -y mem0ai fastapi uvicorn'
```

- [ ] Rollback successful (if needed)

---

## Success Criteria

All items must be checked:

- [x] Files uploaded to EC2
- [ ] Installation completed successfully
- [ ] Service is running
- [ ] Health check returns "healthy"
- [ ] All automated tests pass
- [ ] Can add memories via API
- [ ] Can search memories via API
- [ ] Memory usage under 300MB
- [ ] CPU usage reasonable (<10% idle)
- [ ] Logs show no errors
- [ ] Client library works
- [ ] Database files exist
- [ ] Service restarts successfully
- [ ] Service enabled for auto-start

**If all checked:** ✅ **DEPLOYMENT SUCCESSFUL**

---

## Next Steps After Deployment

1. **Set up monitoring**
   ```bash
   # Add to cron for daily health checks
   ssh ec2 'crontab -e'
   # Add: 0 9 * * * curl http://localhost:5020/health || echo "Mem0 API down"
   ```

2. **Configure backups**
   ```bash
   # Weekly database backup
   ssh ec2 'crontab -e'
   # Add: 0 2 * * 0 cd ~ && tar -czf mem0-backup-$(date +\%Y\%m\%d).tar.gz .mem0/
   ```

3. **Integrate with agents**
   - Update Claude Code scripts to use `execution.mem0_client`
   - Add Mem0 calls to Clawdbot workflows
   - Integrate with Ralph PRD processing

4. **Documentation**
   - Add Mem0 API to MEMORY.md
   - Update execution/CLAUDE.md with Mem0 reference
   - Add examples to relevant project docs

---

## Maintenance Schedule

**Daily:**
- [ ] Check service status: `ssh ec2 'sudo systemctl status mem0-api'`

**Weekly:**
- [ ] Review logs: `ssh ec2 'sudo journalctl -u mem0-api --since "1 week ago"'`
- [ ] Check memory usage: `ssh ec2 'systemctl status mem0-api | grep Memory'`
- [ ] Run test suite: `ssh ec2 'cd dev-sandbox && python3 -m execution.test_mem0_api'`
- [ ] Backup database: `ssh ec2 'cd ~ && tar -czf mem0-backup-$(date +\%Y\%m\%d).tar.gz .mem0/'`

**Monthly:**
- [ ] Review and clean old memories (if needed)
- [ ] Check for Mem0 updates: `ssh ec2 'python3 -m pip list --outdated | grep mem0'`
- [ ] Download backups to local: `scp ec2:/home/ubuntu/mem0-backup-*.tar.gz ~/backups/`

---

**Deployment Date:** _________________
**Deployed By:** William Marceau Jr.
**EC2 Instance:** 34.193.98.97
**Service Port:** 5020
**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Completed | ⬜ Failed
