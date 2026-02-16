# Mem0 API Quick Reference

> One-page cheat sheet for Mem0 deployment and usage

## Installation (One Command)

```bash
# From local machine
scp execution/{mem0_api.py,mem0-api.service,install_mem0_ec2.sh} ec2:/home/ubuntu/dev-sandbox/execution/
ssh ec2 'bash /home/ubuntu/dev-sandbox/execution/install_mem0_ec2.sh'
```

## Essential Commands

```bash
# Service management
sudo systemctl start mem0-api        # Start
sudo systemctl stop mem0-api         # Stop
sudo systemctl restart mem0-api      # Restart
sudo systemctl status mem0-api       # Status
sudo journalctl -u mem0-api -f       # Logs

# Health check
curl http://localhost:5020/health

# Test suite
ssh ec2 'cd dev-sandbox && python3 -m execution.test_mem0_api'
```

## API Endpoints

```bash
# Add memory
curl -X POST http://localhost:5020/memory \
  -H 'Content-Type: application/json' \
  -d '{"agent_id": "claude-code", "content": "Test", "metadata": {}}'

# Search
curl 'http://localhost:5020/memory/search?q=test&agent_id=claude-code'

# List all
curl 'http://localhost:5020/memory/all?agent_id=claude-code'

# Update
curl -X PUT http://localhost:5020/memory/{id} \
  -H 'Content-Type: application/json' \
  -d '{"content": "Updated", "metadata": {}}'

# Delete
curl -X DELETE http://localhost:5020/memory/{id}
```

## Agent IDs

- `claude-code` - Claude Code (Mac terminal)
- `clawdbot` - Clawdbot (Telegram)
- `ralph` - Ralph (PRD-driven)

## Python Integration

```python
import requests

# Add memory
requests.post("http://localhost:5020/memory", json={
    "agent_id": "claude-code",
    "content": "User prefers concise responses",
    "metadata": {"category": "preference"}
})

# Search
requests.get("http://localhost:5020/memory/search", params={
    "q": "preferences",
    "agent_id": "claude-code",
    "limit": 10
})
```

## n8n Integration

HTTP Request node → `POST http://localhost:5020/memory`

```json
{
  "agent_id": "{{ $json.agent }}",
  "content": "{{ $json.memory }}",
  "metadata": {
    "workflow_id": "{{ $workflow.id }}"
  }
}
```

## Troubleshooting

```bash
# Won't start?
sudo journalctl -u mem0-api -n 50     # Check logs
grep OPENAI_API_KEY /home/ubuntu/dev-sandbox/.env  # Check key
/usr/bin/python3 -m pip list | grep mem0  # Check install

# Out of memory?
sudo systemctl restart mem0-api       # Restart
systemctl status mem0-api | grep Memory  # Check usage

# Reset database (CAUTION: deletes all)
sudo systemctl stop mem0-api
rm -rf ~/.mem0/chroma_db && mkdir -p ~/.mem0/chroma_db
sudo systemctl start mem0-api
```

## Backup

```bash
sudo systemctl stop mem0-api
tar -czf mem0-backup-$(date +%Y%m%d).tar.gz ~/.mem0/
sudo systemctl start mem0-api
scp ec2:/home/ubuntu/mem0-backup-*.tar.gz ~/backups/
```

## Resources

- **Port**: 5020 (localhost only)
- **Limits**: 300-400MB RAM, 50% CPU
- **Docs**: http://localhost:5020/docs (via SSH tunnel)
- **Full Guide**: `execution/MEM0_DEPLOYMENT.md`

## Resource Requirements

✓ **RAM**: 150-300MB (fits in <500MB available on EC2)
✓ **Disk**: ~50-100MB for ChromaDB + SQLite
✓ **CPU**: <50% (systemd limited)
✓ **No Docker required**

## Files

- `execution/mem0_api.py` - FastAPI server
- `execution/mem0-api.service` - systemd service
- `execution/install_mem0_ec2.sh` - Installer
- `execution/test_mem0_api.py` - Test suite
- `execution/MEM0_DEPLOYMENT.md` - Full guide
