# Multi-stage build for DocBot

# Stage 1: Frontend Builder - build React app
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package.json frontend/package-lock.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 2: Backend Builder - install Python dependencies
FROM python:3.12-slim AS backend-builder

# Install build dependencies for native packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files and source code (needed for uv sync to build the package)
COPY pyproject.toml uv.lock README.md ./
COPY src/ /app/src/

# Install dependencies (production only)
RUN uv sync --frozen --no-dev

# Stage 3: Runtime - minimal image with application
FROM python:3.12-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy virtual environment from backend builder
COPY --from=backend-builder /app/.venv /app/.venv

# Copy application source
COPY src/ /app/src/
COPY db/ /app/db/

# Copy built frontend from frontend builder
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

# Add .venv/bin to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "docbot.main:app", "--host", "0.0.0.0", "--port", "8000"]
