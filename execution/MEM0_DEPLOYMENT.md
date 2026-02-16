# Mem0 API Deployment Guide

> Lightweight memory layer for Claude Code, Clawdbot, and Ralph running on EC2 at localhost:5020

## Overview

**What is Mem0?**
Mem0 is an AI memory library that provides persistent storage and retrieval of contextual information across agents. It uses vector embeddings for semantic search, enabling agents to remember and recall past interactions, preferences, and learnings.

**Architecture:**
- **FastAPI** REST server on localhost:5020
- **ChromaDB** for vector storage (persistent local files)
- **SQLite** for history database (~/.mem0/history.db)
- **OpenAI embeddings** (gpt-4.1-nano-2025-04-14 default)
- **Memory limit**: 300-400MB RAM (safe for EC2 with 1.8GB total)

**Why Not Docker?**
EC2 has limited resources (1.8GB RAM, 10GB disk). Running Mem0 directly with Python avoids Docker overhead (~100-200MB).

---

## Research Findings

### Can Mem0 Run Without Docker?
✓ **YES** - Mem0 can be installed via `pip install mem0ai` and run standalone ([source](https://docs.mem0.ai/openmemory/quickstart)).

### Minimal Configuration
Mem0 defaults to:
- **Local Qdrant** storage at `/tmp/qdrant` (or ChromaDB in-memory)
- **SQLite history** at `~/.mem0/history.db`
- **ChromaDB** supports both in-memory and persistent modes ([source](https://docs.mem0.ai/components/vectordbs/dbs/chroma))

For persistence, configure ChromaDB with a local path:
```python
config = {
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "agent_memory",
            "path": "~/.mem0/chroma_db",
        }
    }
}
```

### RAM Requirements
- **Base Mem0**: ~50-100MB
- **ChromaDB**: ~50-100MB (in-memory), ~20-50MB (persistent)
- **FastAPI/Uvicorn**: ~30-50MB
- **Total estimate**: **150-300MB** under normal load
- **Our limit**: 300-400MB (systemd MemoryMax)

This fits comfortably in EC2's available RAM (<500MB).

### FastAPI REST API
Mem0 provides an official REST API layer ([source](https://docs.mem0.ai/open-source/features/rest-api)):
- Built with FastAPI
- Supports add, search, update, delete operations
- Interactive docs at `/docs`
- Can run with `uvicorn main:app`

---

## Installation on EC2

### Prerequisites
1. **SSH access**: `ssh ec2` (configured in `~/.ssh/config`)
2. **Python 3**: `/usr/bin/python3` (already installed)
3. **OpenAI API key**: Set in `/home/ubuntu/dev-sandbox/.env`

### Step 1: Add API Key to .env

SSH into EC2 and add your OpenAI API key:

```bash
ssh ec2
cd /home/ubuntu/dev-sandbox
echo "OPENAI_API_KEY=sk-xxx..." >> .env
```

### Step 2: Upload Files to EC2

From your local machine:

```bash
# Upload the API script, service file, and installer
scp execution/mem0_api.py ec2:/home/ubuntu/dev-sandbox/execution/
scp execution/mem0-api.service ec2:/home/ubuntu/dev-sandbox/execution/
scp execution/install_mem0_ec2.sh ec2:/home/ubuntu/

# Make installer executable
ssh ec2 'chmod +x /home/ubuntu/install_mem0_ec2.sh'
```

### Step 3: Run Installer

```bash
ssh ec2 'bash /home/ubuntu/install_mem0_ec2.sh'
```

The installer will:
1. Install Python dependencies (`fastapi`, `uvicorn`, `mem0ai`, `python-dotenv`)
2. Create database directory (`~/.mem0/chroma_db`)
3. Test the API starts correctly
4. Install and start systemd service
5. Verify service is running

### Step 4: Verify Installation

```bash
ssh ec2

# Check service status
sudo systemctl status mem0-api

# View logs
sudo journalctl -u mem0-api -f

# Test health endpoint
curl http://localhost:5020/health
```

Expected output:
```json
{
  "status": "healthy",
  "service": "mem0-api",
  "timestamp": "2026-02-15T12:00:00",
  "collection": "agent_memory",
  "db_path": "/home/ubuntu/.mem0/chroma_db"
}
```

---

## API Reference

### Base URL
```
http://localhost:5020
```

### Endpoints

#### Health Check
```bash
GET /health

curl http://localhost:5020/health
```

#### Add Memory
```bash
POST /memory
Content-Type: application/json

{
  "agent_id": "claude-code",
  "content": "User prefers concise responses without emojis",
  "metadata": {
    "category": "preference",
    "priority": "high"
  }
}

# Example
curl -X POST http://localhost:5020/memory \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_id": "claude-code",
    "content": "User prefers concise responses",
    "metadata": {"category": "preference"}
  }'
```

#### Search Memories
```bash
GET /memory/search?q=<query>&agent_id=<agent>&limit=<N>

# Example
curl 'http://localhost:5020/memory/search?q=preferences&agent_id=claude-code&limit=10'
```

#### List All Memories
```bash
GET /memory/all?agent_id=<agent>&limit=<N>

# Example
curl 'http://localhost:5020/memory/all?agent_id=claude-code&limit=100'
```

#### Update Memory
```bash
PUT /memory/{memory_id}
Content-Type: application/json

{
  "content": "Updated content",
  "metadata": {"category": "preference"}
}

# Example
curl -X PUT http://localhost:5020/memory/abc123 \
  -H 'Content-Type: application/json' \
  -d '{"content": "Updated preference", "metadata": {}}'
```

#### Delete Memory
```bash
DELETE /memory/{memory_id}

# Example
curl -X DELETE http://localhost:5020/memory/abc123
```

### Agent IDs
- `claude-code` - Claude Code (Mac terminal)
- `clawdbot` - Clawdbot (Telegram, EC2 24/7)
- `ralph` - Ralph (EC2, PRD-driven builds)

---

## Testing

### Automated Test Suite

Run the full test suite:

```bash
# On EC2
ssh ec2 'cd dev-sandbox && python3 -m execution.test_mem0_api'

# Locally (if running API locally)
python -m execution.test_mem0_api
```

### Manual Testing

```bash
# 1. Health check
curl http://localhost:5020/health

# 2. Add a test memory
curl -X POST http://localhost:5020/memory \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_id": "test-agent",
    "content": "This is a test memory",
    "metadata": {"source": "manual_test"}
  }'

# 3. Search for it
curl 'http://localhost:5020/memory/search?q=test&agent_id=test-agent'

# 4. List all memories
curl 'http://localhost:5020/memory/all?agent_id=test-agent'
```

### Interactive Documentation

Open in browser (requires port forwarding):
```
http://localhost:5020/docs
```

Or use SSH tunnel from local machine:
```bash
ssh -L 5020:localhost:5020 ec2
# Then open http://localhost:5020/docs in browser
```

---

## Service Management

### Systemd Commands

```bash
# Start service
sudo systemctl start mem0-api

# Stop service
sudo systemctl stop mem0-api

# Restart service
sudo systemctl restart mem0-api

# Check status
sudo systemctl status mem0-api

# Enable on boot
sudo systemctl enable mem0-api

# Disable on boot
sudo systemctl disable mem0-api

# View logs (follow)
sudo journalctl -u mem0-api -f

# View recent logs
sudo journalctl -u mem0-api -n 100
```

### Resource Monitoring

```bash
# Check memory usage
systemctl status mem0-api | grep Memory

# Detailed resource usage
systemd-cgtop | grep mem0-api

# Process info
ps aux | grep mem0_api
```

### Service Limits

Configured in `/etc/systemd/system/mem0-api.service`:
- **MemoryMax**: 400MB (hard limit)
- **MemoryHigh**: 300MB (soft limit, triggers cleanup)
- **CPUQuota**: 50% (prevent CPU hogging)

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u mem0-api -n 50

# Common issues:
# 1. Missing OPENAI_API_KEY
grep OPENAI_API_KEY /home/ubuntu/dev-sandbox/.env

# 2. Port already in use
sudo lsof -i :5020

# 3. Python dependencies missing
/usr/bin/python3 -m pip list | grep -E 'mem0|fastapi|uvicorn'

# 4. Permissions on database directory
ls -la ~/.mem0/
```

### Out of Memory

If service hits memory limits:

```bash
# Check current memory usage
systemctl status mem0-api | grep Memory

# Restart service to clear memory
sudo systemctl restart mem0-api

# Reduce memory limits if needed (edit service file)
sudo nano /etc/systemd/system/mem0-api.service
sudo systemctl daemon-reload
sudo systemctl restart mem0-api
```

### ChromaDB Errors

```bash
# Check database directory
ls -la ~/.mem0/chroma_db/

# Reset database (CAUTION: deletes all memories)
sudo systemctl stop mem0-api
rm -rf ~/.mem0/chroma_db
mkdir -p ~/.mem0/chroma_db
sudo systemctl start mem0-api
```

### API Not Responding

```bash
# Check if process is running
ps aux | grep mem0_api

# Check if port is listening
sudo lsof -i :5020

# Test locally
curl http://localhost:5020/health

# Check firewall (should be localhost only)
sudo iptables -L | grep 5020
```

---

## Integration Examples

### From n8n Workflow

Use HTTP Request node:

```json
{
  "method": "POST",
  "url": "http://localhost:5020/memory",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "agent_id": "{{ $json.agent_id }}",
    "content": "{{ $json.content }}",
    "metadata": {
      "workflow_id": "{{ $workflow.id }}",
      "execution_id": "{{ $execution.id }}"
    }
  }
}
```

### From Python (Agent Bridge API)

```python
import requests

def add_memory(agent_id: str, content: str, metadata: dict = None):
    """Add a memory to the Mem0 API."""
    response = requests.post(
        "http://localhost:5020/memory",
        json={
            "agent_id": agent_id,
            "content": content,
            "metadata": metadata or {}
        }
    )
    return response.json()

def search_memory(query: str, agent_id: str, limit: int = 10):
    """Search memories."""
    response = requests.get(
        "http://localhost:5020/memory/search",
        params={
            "q": query,
            "agent_id": agent_id,
            "limit": limit
        }
    )
    return response.json()
```

### From Claude Code (Local)

Via SSH tunnel or direct API calls from local Python scripts.

### From Clawdbot/Ralph (EC2)

Direct localhost calls since they run on same EC2 instance.

---

## Backup & Restore

### Backup

```bash
# Stop service
sudo systemctl stop mem0-api

# Backup database
tar -czf mem0-backup-$(date +%Y%m%d).tar.gz ~/.mem0/

# Restart service
sudo systemctl start mem0-api

# Download backup to local machine
scp ec2:/home/ubuntu/mem0-backup-*.tar.gz ~/backups/
```

### Restore

```bash
# Stop service
sudo systemctl stop mem0-api

# Restore database
tar -xzf mem0-backup-20260215.tar.gz -C ~/

# Restart service
sudo systemctl start mem0-api
```

---

## Performance Tuning

### For Very Low Memory (<300MB available)

Edit `/etc/systemd/system/mem0-api.service`:

```ini
# Reduce limits
MemoryMax=250M
MemoryHigh=200M
```

### For Better Performance (>500MB available)

```ini
# Increase limits
MemoryMax=600M
MemoryHigh=500M
CPUQuota=75%
```

After changes:
```bash
sudo systemctl daemon-reload
sudo systemctl restart mem0-api
```

---

## Monitoring & Logs

### View Real-Time Logs

```bash
sudo journalctl -u mem0-api -f
```

### Search Logs for Errors

```bash
sudo journalctl -u mem0-api | grep -i error
```

### Log Rotation

Logs are managed by systemd journal. Configure retention:

```bash
# Edit journal config
sudo nano /etc/systemd/journald.conf

# Set max size
SystemMaxUse=100M
SystemKeepFree=1G

# Reload
sudo systemctl restart systemd-journald
```

---

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop mem0-api
sudo systemctl disable mem0-api

# Remove service file
sudo rm /etc/systemd/system/mem0-api.service
sudo systemctl daemon-reload

# Remove database (optional, CAUTION: deletes all memories)
rm -rf ~/.mem0/

# Uninstall Python packages (optional)
/usr/bin/python3 -m pip uninstall -y mem0ai fastapi uvicorn
```

---

## Sources & References

- [Mem0 GitHub Repository](https://github.com/mem0ai/mem0)
- [Mem0 Quickstart Documentation](https://docs.mem0.ai/openmemory/quickstart)
- [Mem0 REST API Documentation](https://docs.mem0.ai/open-source/features/rest-api)
- [ChromaDB Configuration](https://docs.mem0.ai/components/vectordbs/dbs/chroma)
- [Mem0 Installation & Setup](https://deepwiki.com/mem0ai/mem0/1.2-installation-and-setup)
- [Mem0 PyPI Package](https://pypi.org/project/mem0ai/)

---

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u mem0-api -n 100`
2. Review this documentation
3. Check official Mem0 docs: https://docs.mem0.ai/
4. File issue in GitHub: https://github.com/mem0ai/mem0/issues

---

**Author**: William Marceau Jr.
**Created**: 2026-02-15
**Last Updated**: 2026-02-15
