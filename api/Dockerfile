# Official Playwright image: ships with Chromium + all OS deps preinstalled,
# avoiding the Debian-trixie vs Ubuntu-20.04 package mismatches you hit when
# `playwright install --with-deps` runs on a vanilla python:slim base.
FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Sao_Paulo

RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    apt-get update && apt-get install -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Ensure entrypoint is executable even if the host filesystem stripped the bit.
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
