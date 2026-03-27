# MCP Aggregator API - Production Dockerfile
#
# Build:
#   docker build -t mcp-aggregator-api .
#
# Run:
#   docker run -p 8000:8000 --env-file .env mcp-aggregator-api

# === Stage 1: Build ===
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# === Stage 2: Runtime ===
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy application code
COPY server.py .
COPY models.py .
COPY config.py .
COPY auth.py .

# Copy rideshare MCP (in production, this would be a package install)
# For local development, we'll mount this as a volume
RUN mkdir -p /app/mcps/rideshare
COPY --chown=appuser:appgroup . /app/

# Create directory for rideshare MCP (will be mounted)
RUN mkdir -p /app/src/mcps/rideshare && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Default environment variables
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV MCP_DEBUG=false
ENV MCP_WORKERS=4
ENV MCP_LOG_LEVEL=INFO

# Run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
