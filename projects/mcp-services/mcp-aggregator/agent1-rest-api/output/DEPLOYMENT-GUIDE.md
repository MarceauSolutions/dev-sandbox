# MCP Aggregator API - Deployment Guide

**Estimated Time:** 30-45 minutes
**Prerequisites:** Docker, Python 3.11+, Git

---

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment (AWS)](#production-deployment-aws)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Troubleshooting](#troubleshooting)

---

## Local Development

### Quick Start (5 minutes)

```bash
# Navigate to workspace
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent1-rest-api/workspace

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python server.py
```

Server will be available at:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **OpenAPI:** http://localhost:8000/openapi.json

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Compare prices (with test API key)
curl -X POST "http://localhost:8000/v1/compare" \
  -H "X-API-Key: test_free_key_12345" \
  -H "Content-Type: application/json" \
  -d '{"pickup": {"latitude": 37.7879, "longitude": -122.4074}, "dropoff": {"latitude": 37.6213, "longitude": -122.3790}}'
```

### Run Tests

```bash
# Run all tests
pytest test_api.py -v

# Run with coverage
pytest test_api.py -v --cov=. --cov-report=html

# Run specific test class
pytest test_api.py::TestComparisonEndpoint -v
```

---

## Docker Deployment

### Option A: Docker Compose (Recommended for Development)

```bash
# Navigate to workspace
cd /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/agent1-rest-api/workspace

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option B: Standalone Docker

```bash
# Build image
docker build -t mcp-aggregator-api .

# Run container
docker run -d \
  --name mcp-api \
  -p 8000:8000 \
  -v /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/src/mcps/rideshare:/app/src/mcps/rideshare:ro \
  -e MCP_DEBUG=false \
  -e MCP_WORKERS=4 \
  mcp-aggregator-api

# Check logs
docker logs -f mcp-api

# Stop
docker stop mcp-api && docker rm mcp-api
```

### Verify Docker Deployment

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status": "healthy", "version": "1.0.0", ...}
```

---

## Production Deployment (AWS)

### Prerequisites

- AWS CLI configured
- ECR repository created
- ECS cluster or EC2 instance
- (Optional) ALB for load balancing

### Step 1: Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com

# Tag image
docker tag mcp-aggregator-api:latest YOUR_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/mcp-aggregator-api:latest

# Push
docker push YOUR_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/mcp-aggregator-api:latest
```

### Step 2: Deploy to ECS (Recommended)

Create `ecs-task-definition.json`:

```json
{
  "family": "mcp-aggregator-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/mcp-aggregator-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "MCP_HOST", "value": "0.0.0.0"},
        {"name": "MCP_PORT", "value": "8000"},
        {"name": "MCP_WORKERS", "value": "4"},
        {"name": "MCP_LOG_LEVEL", "value": "INFO"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mcp-aggregator-api",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3
      }
    }
  ]
}
```

Deploy:

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster mcp-cluster \
  --service-name mcp-aggregator-api \
  --task-definition mcp-aggregator-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Step 3: Configure Load Balancer

1. Create ALB in AWS Console
2. Create target group pointing to ECS service
3. Add HTTPS listener with SSL certificate
4. Update Route53 with ALB DNS

### Step 4: Set Up Domain

```bash
# Add DNS record
aws route53 change-resource-record-sets \
  --hosted-zone-id ZXXXXX \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.mcp-aggregator.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "ALB_HOSTED_ZONE_ID",
          "DNSName": "YOUR-ALB.us-west-2.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

---

## Post-Deployment Verification

### Health Check

```bash
# Production
curl https://api.mcp-aggregator.com/health

# Expected:
# {"status": "healthy", "version": "1.0.0", ...}
```

### API Functionality Test

```bash
# Compare prices
curl -X POST "https://api.mcp-aggregator.com/v1/compare" \
  -H "X-API-Key: YOUR_PRODUCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{"pickup": {"latitude": 37.7879, "longitude": -122.4074}, "dropoff": {"latitude": 37.6213, "longitude": -122.3790}}'

# Get cities
curl "https://api.mcp-aggregator.com/v1/cities" \
  -H "X-API-Key: YOUR_PRODUCTION_KEY"
```

### Load Test (Optional)

```bash
# Install hey (load testing tool)
brew install hey

# Run load test
hey -n 1000 -c 50 -H "X-API-Key: YOUR_KEY" \
  "https://api.mcp-aggregator.com/health"
```

---

## Troubleshooting

### Issue: Server won't start

**Symptom:** `ModuleNotFoundError: No module named 'comparison'`

**Solution:**
```bash
# Ensure rideshare MCP path is correct
ls /Users/williammarceaujr./dev-sandbox/projects/mcp-aggregator/src/mcps/rideshare/

# Should show: comparison.py, rate_cards.py, deep_links.py, __init__.py
```

### Issue: Docker build fails

**Symptom:** Permission denied or file not found

**Solution:**
```bash
# Ensure all files are present
ls -la workspace/

# Rebuild without cache
docker build --no-cache -t mcp-aggregator-api .
```

### Issue: Rate limiting too aggressive

**Symptom:** Getting 429 errors too quickly

**Solution:**
```bash
# Disable rate limiting temporarily
MCP_ENABLE_RATE_LIMITING=false python server.py

# Or increase limits in config.py
```

### Issue: CORS errors in browser

**Symptom:** Browser shows CORS error

**Solution:**
```bash
# Set specific origins
MCP_CORS_ORIGINS=https://your-app.com,https://localhost:3000 python server.py
```

### Issue: Health check failing

**Symptom:** Container unhealthy or health endpoint returning error

**Solution:**
```bash
# Check container logs
docker logs mcp-api

# Check if rate cards loaded
curl http://localhost:8000/health

# Should show: "rate_cards": "healthy"
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_HOST` | 0.0.0.0 | Server host |
| `MCP_PORT` | 8000 | Server port |
| `MCP_DEBUG` | false | Enable debug mode |
| `MCP_WORKERS` | 4 | Uvicorn workers |
| `MCP_LOG_LEVEL` | INFO | Logging level |
| `MCP_CORS_ORIGINS` | * | Allowed CORS origins |
| `MCP_ENABLE_RATE_LIMITING` | true | Enable rate limiting |
| `MCP_ENABLE_METRICS` | true | Enable metrics |
| `MCP_ENABLE_CACHING` | true | Enable response caching |
| `MCP_CACHE_TTL` | 300 | Cache TTL in seconds |

---

## Next Steps After Deployment

1. **Set up monitoring**: CloudWatch, Datadog, or Prometheus
2. **Configure alerts**: Set up alerts for 5xx errors, high latency
3. **Set up CI/CD**: GitHub Actions or AWS CodePipeline
4. **Add Redis**: For distributed rate limiting
5. **SSL Certificate**: Ensure HTTPS with valid cert

---

**Created by:** Agent 1 (REST API)
**Date:** 2026-01-12
