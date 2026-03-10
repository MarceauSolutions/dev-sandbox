# Fitness Influencer AI — Scaling Plan (Phase 2)

> **Status**: Deferred — Activate when trigger conditions are met
> **Current Deployment**: EC2 (t4g.small) at `https://fitai.marceausolutions.com`
> **Created**: 2026-02-09

## Trigger Conditions

| Trigger | Action |
|---------|--------|
| Want to sell to 1-5 users | Stay on EC2, add auth + PostgreSQL (steps 1-4 below) |
| Want to sell to 10+ users | Migrate to Railway/Render (steps 1-7 below) |
| EC2 memory gets tight (n8n + fitai + bridge on 2GB) | Upgrade to t4g.medium ($30/mo) first |

## Existing Scalability Foundation

The codebase already has multi-tenancy scaffolding:
- All gamification/task routes accept `tenant_id` parameter
- `User` model with `tier` field (free/pro/enterprise)
- SQLAlchemy ORM supports PostgreSQL (currently using SQLite/JSON files)
- CORS already permissive (`allow_origins=["*"]`)
- `Procfile` exists: `web: uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}`

## Steps to Scale

### 1. Add Authentication (JWT or OAuth)
- Currently no login system — all requests use hardcoded `tenant_id=wmarceau`
- Options:
  - **JWT**: FastAPI + python-jose + passlib (simplest, self-contained)
  - **OAuth**: Google/Apple sign-in via authlib (better UX, less password management)
- Add `/api/auth/register`, `/api/auth/login`, `/api/auth/me` endpoints
- Middleware to extract `tenant_id` from JWT token instead of query param

### 2. Migrate Database: SQLite/JSON → PostgreSQL
- SQLAlchemy already supports PostgreSQL — change connection string in `.env`:
  ```
  DATABASE_URL=postgresql://user:pass@host:5432/fitai
  ```
- Migrate JSON file storage (player data, gamification state) to database tables
- Use Alembic for schema migrations: `pip install alembic && alembic init`
- Key tables: `users`, `player_stats`, `quests`, `achievements`, `rewards`, `tasks`

### 3. Frontend: Dynamic Tenant Resolution
- Change `tenant_id` from hardcoded `'wmarceau'` to login-based
- Store JWT token in localStorage after login
- Add `Authorization: Bearer <token>` header to all API calls in `api.js`
- Add login/register page to the SPA router

### 4. Migrate File Uploads: Local Disk → S3/R2
- Currently saves to local filesystem (`data/`, `uploads/`)
- Move to S3 (or Cloudflare R2 for cheaper egress):
  ```
  AWS_S3_BUCKET=fitai-uploads
  AWS_S3_REGION=us-east-1
  ```
- Use `boto3` for uploads, presigned URLs for downloads
- This is required for Railway/Render (ephemeral filesystem)

### 5. Create Railway Config
- `railway.json`:
  ```json
  {
    "$schema": "https://railway.com/railway.schema.json",
    "build": { "builder": "NIXPACKS" },
    "deploy": {
      "startCommand": "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}",
      "healthcheckPath": "/",
      "restartPolicyType": "ON_FAILURE"
    }
  }
  ```
- Procfile already exists (Railway reads it automatically)
- Add Railway PostgreSQL addon ($7/mo for hobby)

### 6. Optional: Add Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
- Not required for Railway (uses Nixpacks by default)
- Useful for Docker Compose, Fly.io, or custom hosting

### 7. Migrate to Railway/Render
- Connect GitHub repo → auto-deploy on push
- Set environment variables in Railway dashboard
- Point `fitai.marceausolutions.com` DNS to Railway's provided domain
- Railway pricing: ~$5/mo base + $0.000231/GB-hr compute

## Cost Comparison

| Setup | Monthly Cost | Scales To |
|-------|-------------|-----------|
| Current (EC2 t4g.small) | ~$15 | 1-5 users |
| EC2 t4g.medium | ~$30 | 5-20 users |
| Railway Hobby | ~$5-20 | 1-50 users (auto-scale) |
| Railway Pro | ~$20-100 | 50-500+ users |

## Architecture After Phase 2

```
Users → fitai.marceausolutions.com
         ↓
    Railway/Render
    ├── FastAPI (auto-scaled)
    ├── PostgreSQL (managed)
    └── S3/R2 (file storage)
```

vs Current:
```
You → fitai.marceausolutions.com
       ↓
    EC2 t4g.small
    ├── Caddy (HTTPS)
    ├── FastAPI (:8000)
    ├── n8n (:5678)
    ├── Agent Bridge (:5010)
    └── SQLite + JSON files
```
