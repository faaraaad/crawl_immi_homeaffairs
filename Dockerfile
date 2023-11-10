FROM python:3.12-slim

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for Playwright and general builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging configuration and install dependencies
COPY pyproject.toml .
COPY README.md .
COPY src/ ./src/

# Install the package in editable/development mode or standard mode
RUN pip install --no-cache-dir .[dev]

# Install Playwright and its Chromium dependencies
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy remaining code files (migrations, Makefile, etc.)
COPY migrations/ ./migrations/
COPY alembic.ini .
COPY Makefile .

# Default command: show CLI help
CMD ["immi-crawler", "--help"]
