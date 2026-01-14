# Python official image
FROM python:3.11-slim

# =========================
# Environment settings
# =========================
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=UTC

# =========================
# Set workdir
# =========================
WORKDIR /app

# =========================
# System dependencies
# =========================
# build-essential  -> asyncpg / wheels
# libpq-dev        -> PostgreSQL client libs
# ca-certificates  -> HTTPS (OpenAI, Telegram)
# tzdata           -> time correctness (scheduler)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ca-certificates \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# =========================
# Python dependencies
# =========================
# Copy requirements first (better Docker cache)
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# =========================
# Copy project source
# =========================
COPY . .

# =========================
# Run bot
# =========================
CMD ["python", "-m", "bot.main"]
