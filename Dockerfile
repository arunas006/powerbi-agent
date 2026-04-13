# ---------- Builder Stage ----------

FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies (for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# copy Python dependencies
COPY requirements.txt .

# Install dependencies into custom location
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt

# ---------- Development Stage ----------
FROM python:3.11-slim AS dev
WORKDIR /app

# Copy installed dependencies
COPY --from=builder /install /usr/local

# Copy full project (for dev)
COPY . .

# Run with reload for development
CMD ["uvicorn", "src.agent.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

# ---------- Runtime / Inference Stage ----------

FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy only installed dependencies
COPY --from=builder /install /usr/local

COPY src/ ./src/

# Create non-root user (security best practice)
RUN useradd -m appuser
USER appuser

# Run production server
CMD ["sh", "-c", "uvicorn src.agent.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
