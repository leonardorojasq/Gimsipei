# Base stage: system dependencies and Python
FROM python:3.13-slim AS base

ENV DIR=/app
WORKDIR $DIR

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev-compat \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Builder stage: install Python dependencies and copy the source code
FROM base AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency manifests first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Sync dependencies into a project-local venv (no dev deps, no project install)
RUN uv sync --frozen --no-dev --no-install-project

# Copy the source code
COPY . .

# Production stage: only the necessary for running the app
FROM python:3.13-slim AS production

ENV DIR=/app
WORKDIR $DIR

# Copy the venv from the builder
COPY --from=builder $DIR/.venv $DIR/.venv

# Copy the source code from the builder
COPY --from=builder $DIR $DIR

# Use the project venv
ENV PATH="$DIR/.venv/bin:$PATH"

# Environment variables for production
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Create a non-root user and use it
RUN adduser --disabled-password --no-create-home --gecos '' appuser
USER appuser

# Expose the port (adjust if you use another)
EXPOSE 5010

# Command to run the app (adjust if your entrypoint is different)
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-5010} main:app"]