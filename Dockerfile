# Stage 1: Build stage
FROM python:3.10-slim AS builder

WORKDIR /build

# Install compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into a separate directory
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Final runtime stage
FROM python:3.10-slim

WORKDIR /workspace

# Install runtime dependencies (e.g. libpq for postgres connection)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ /workspace/app/
COPY scripts/ /workspace/scripts/

# Ensure PYTHONPATH includes the current directory so imports work
ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1

# Expose port 8000 for the FastAPI service
EXPOSE 8000

# Create a non-root user and assign permissions
RUN useradd -u 10001 -m appuser && \
    chown -R appuser:appuser /workspace

USER appuser

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
