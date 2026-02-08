# PostgreSQL Database Setup Guide

Complete setup guide for the MCP Aggregator Platform database.

**Time Required:** 10-15 minutes

---

## Prerequisites

- macOS (these instructions are for macOS; adjust for other systems)
- Homebrew installed
- Terminal access

---

## Step 1: Install PostgreSQL

```bash
# Install PostgreSQL via Homebrew
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Verify it's running
brew services list | grep postgresql
# Should show: postgresql@14 started
```

**Troubleshooting:**
- If PostgreSQL won't start: `brew services restart postgresql@14`
- Check logs: `tail -f /opt/homebrew/var/log/postgresql@14.log`

---

## Step 2: Create Database

```bash
# Create the database
createdb mcp_aggregator

# Verify it exists
psql -l | grep mcp_aggregator
# Should show: mcp_aggregator

# Test connection
psql mcp_aggregator -c "SELECT 1"
# Should show: ?column? = 1
```

---

## Step 3: Run Schema

```bash
# Navigate to workspace
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent3-platform-core/workspace

# Run schema script
psql mcp_aggregator < schema.sql

# Verify tables created
psql mcp_aggregator -c "\dt"
# Should show 11+ tables
```

**Expected tables:**
- `developers` - MCP developers/companies
- `ai_platforms` - AI clients (Claude, ChatGPT)
- `mcps` - Registered MCP servers
- `mcp_capabilities` - What each MCP can do
- `circuit_breaker_state` - Fault tolerance state
- `transactions` - Billable API calls
- `rate_cards` - Rideshare pricing data
- `health_checks` - MCP health history
- `daily_stats` - Aggregated metrics
- `payouts` - Developer payments
- `invoices` - Platform invoices

---

## Step 4: Load Seed Data

```bash
# Run seed data script
psql mcp_aggregator < seed_data.sql

# Verify data loaded
psql mcp_aggregator -c "SELECT COUNT(*) FROM developers"
# Should show: count = 2

psql mcp_aggregator -c "SELECT COUNT(*) FROM rate_cards"
# Should show: count = 22 (rate cards for 10 cities)

psql mcp_aggregator -c "SELECT name, category, status FROM mcps"
# Should show the rideshare comparison MCP
```

---

## Step 5: Test Connection

```bash
# Install Python dependencies
pip install psycopg2-binary

# Run connection test
python test_connection.py
```

**Expected output:**
```
============================================================
MCP Aggregator Platform - PostgreSQL Connection Test
============================================================

Connection: localhost:5432/mcp_aggregator

Testing connection...
  Connected successfully!

Health check...
  Status: healthy
  Latency: 1.23ms

Verifying tables...
  developers: OK
  ai_platforms: OK
  mcps: OK
  [...]

============================================================
CONNECTION TEST PASSED
============================================================
```

---

## Step 6: Set Environment Variable (Optional)

For production or custom configurations:

```bash
# Add to ~/.zshrc or ~/.bashrc
export DATABASE_URL="postgresql://postgres@localhost:5432/mcp_aggregator"

# Or with password:
export DATABASE_URL="postgresql://user:password@localhost:5432/mcp_aggregator"

# Reload shell
source ~/.zshrc
```

---

## Running Tests

After database setup, run the test suite:

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent3-platform-core/workspace

# Run all tests (uses SQLite by default)
pytest test_platform.py -v

# Run specific test class
pytest test_platform.py::TestDatabase -v
pytest test_platform.py::TestMCPRegistry -v
pytest test_platform.py::TestBillingSystem -v
```

---

## Common Issues

### 1. "connection refused"

PostgreSQL isn't running:
```bash
brew services start postgresql@14
```

### 2. "database does not exist"

Create the database:
```bash
createdb mcp_aggregator
```

### 3. "relation does not exist"

Schema not loaded:
```bash
psql mcp_aggregator < schema.sql
```

### 4. "psycopg2 not found"

Install Python driver:
```bash
pip install psycopg2-binary
```

### 5. "permission denied"

Check PostgreSQL user permissions:
```bash
psql postgres -c "CREATE USER your_user WITH PASSWORD 'your_password';"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE mcp_aggregator TO your_user;"
```

---

## Database Management

### Backup

```bash
# Full backup
pg_dump mcp_aggregator > backup_$(date +%Y%m%d).sql

# Schema only
pg_dump --schema-only mcp_aggregator > schema_backup.sql

# Data only
pg_dump --data-only mcp_aggregator > data_backup.sql
```

### Restore

```bash
# Drop and recreate
dropdb mcp_aggregator
createdb mcp_aggregator
psql mcp_aggregator < backup_20260112.sql
```

### Reset (Development)

```bash
# Quick reset - drops and recreates everything
dropdb mcp_aggregator
createdb mcp_aggregator
psql mcp_aggregator < schema.sql
psql mcp_aggregator < seed_data.sql
```

---

## Useful Commands

```bash
# Connect to database
psql mcp_aggregator

# Inside psql:
\dt                     # List tables
\d mcps                 # Describe table structure
\di                     # List indexes
\dv                     # List views
\q                      # Quit

# Query examples
psql mcp_aggregator -c "SELECT name, status FROM mcps"
psql mcp_aggregator -c "SELECT * FROM mcp_directory"  # Uses view
```

---

## Next Steps

After database setup:

1. **Run platform tests:** `pytest test_platform.py -v`
2. **Start API server:** (implementation in progress)
3. **Integrate with rideshare MCP:** Connect existing comparison code

---

**Questions?** Check `ARCHITECTURE.md` for system design or `INTEGRATION-GUIDE.md` for API usage.
