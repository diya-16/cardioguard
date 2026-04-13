# ── Base image ────────────────────────────────────────────────
FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ───────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project files ────────────────────────────────────────
COPY . .

# ── Ensure data & outputs dirs exist ─────────────────────────
RUN mkdir -p data outputs models

# ── Streamlit config ──────────────────────────────────────────
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# ── Expose port ───────────────────────────────────────────────
EXPOSE 8501

# ── Health check ──────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# ── Run app ───────────────────────────────────────────────────
CMD ["streamlit", "run", "app.py"]
