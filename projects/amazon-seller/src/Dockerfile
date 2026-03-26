FROM python:3.11-slim

LABEL maintainer="William Marceau Jr. <william@marceausolutions.com>"
LABEL description="Amazon seller tools: FBA fees, inventory optimization, restock recommendations"
LABEL version="1.0.0"

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
# Required environment variables:
#   AMAZON_REFRESH_TOKEN
#   AMAZON_LWA_APP_ID
#   AMAZON_LWA_CLIENT_SECRET
#   AMAZON_AWS_ACCESS_KEY
#   AMAZON_AWS_SECRET_KEY
ENTRYPOINT ["amazon-seller-mcp"]
