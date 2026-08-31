FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and buffer outputs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create directory for SQLite DB and logs
RUN mkdir -p /app/logs

# Healthcheck
HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
  CMD python -c "import os; exit(0 if os.path.exists('bithumb_quant.db') else 1)"

CMD ["python", "main.py"]
