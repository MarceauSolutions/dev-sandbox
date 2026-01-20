# Human Actions Required

Tasks that require human intervention (database setup, permissions, etc.)

---

## Priority 1: Database Setup (10-15 minutes)

### 1.1 Install PostgreSQL

```bash
brew install postgresql@14
brew services start postgresql@14
```

### 1.2 Create Database

```bash
createdb mcp_aggregator
```

### 1.3 Run Schema

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent3-platform-core/workspace
psql mcp_aggregator < schema.sql
```

### 1.4 Load Seed Data

```bash
psql mcp_aggregator < seed_data.sql
```

### 1.5 Test Connection

```bash
pip install psycopg2-binary
python test_connection.py
```

**Expected Output:** "CONNECTION TEST PASSED"

---

## Priority 2: Run Tests (5 minutes)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent3-platform-core/workspace

# Install pytest if needed
pip install pytest

# Run tests
pytest test_platform.py -v
```

**Expected:** All tests should pass (uses SQLite, no PostgreSQL required)

---

## Priority 3: Environment Setup (Optional)

If using custom PostgreSQL settings:

```bash
# Add to ~/.zshrc or ~/.bashrc
export DATABASE_URL="postgresql://user:password@localhost:5432/mcp_aggregator"

# Reload shell
source ~/.zshrc
```

---

## Verification Checklist

After completing setup, verify:

- [ ] PostgreSQL is running (`brew services list`)
- [ ] Database exists (`psql -l | grep mcp_aggregator`)
- [ ] Tables created (`psql mcp_aggregator -c "\dt"`)
- [ ] Seed data loaded (`psql mcp_aggregator -c "SELECT COUNT(*) FROM mcps"`)
- [ ] Connection test passes (`python test_connection.py`)
- [ ] All tests pass (`pytest test_platform.py -v`)

---

## Troubleshooting

### PostgreSQL won't start

```bash
brew services restart postgresql@14
tail -f /opt/homebrew/var/log/postgresql@14.log
```

### psycopg2 not found

```bash
pip install psycopg2-binary
```

### Permission denied

```bash
# Create user and grant permissions
psql postgres -c "CREATE USER your_user WITH PASSWORD 'your_password';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE mcp_aggregator TO your_user;"
```

---

## Time Estimates

| Task | Time |
|------|------|
| Install PostgreSQL | 2 min |
| Create database | 1 min |
| Run schema | 1 min |
| Load seed data | 1 min |
| Test connection | 2 min |
| Run tests | 3 min |
| **Total** | **~10 min** |

---

## Next Steps After Setup

1. Run platform tests to verify everything works
2. Review architecture documentation (`ARCHITECTURE.md`)
3. Start building API layer
4. Integrate with existing rideshare MCP code
