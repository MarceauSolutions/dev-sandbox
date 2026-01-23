FROM python:3.11-slim

LABEL maintainer="William Marceau Jr. <william@marceausolutions.com>"
LABEL description="Convert markdown to professional PDFs with clickable table of contents"
LABEL version="1.0.1"

# Set working directory
WORKDIR /app

# Install system dependencies for WeasyPrint
# WeasyPrint requires Pango, Cairo, and related libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# The MCP server communicates via stdio
# No API keys required for this MCP
ENTRYPOINT ["md-to-pdf-mcp"]
