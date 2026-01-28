FROM python:3.11-slim

LABEL maintainer="William Marceau Jr. <william@marceausolutions.com>"
LABEL description="Apollo.io lead enrichment and prospecting MCP server"
LABEL version="1.1.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# The MCP server communicates via stdio
# API key should be passed via environment variable: APOLLO_API_KEY
ENTRYPOINT ["apollo-mcp"]
