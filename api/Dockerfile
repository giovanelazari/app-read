FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=America/Sao_Paulo
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright chromium with OS deps (needed for headless scraping inside the container).
RUN playwright install --with-deps chromium

COPY . .

# Ensure entrypoint is executable even if the host filesystem stripped the bit.
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
