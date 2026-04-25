#!/usr/bin/env bash
# deploy.sh — build images locally and (re)deploy the kindle stack on Docker Swarm.
#
# Usage on the VPS:
#   cd /opt/kindle-app
#   ./deploy.sh
#
# What it does:
#   1. Loads variables from .env into the current shell
#   2. Ensures bind-mount data directories exist
#   3. Builds api + web images with the right tags (web bakes VITE_API_URL at build time)
#   4. Runs `docker stack deploy` against docker-compose.stack.yml
#
# Prereqs:
#   - This host is a Docker Swarm manager (run `docker swarm init` if not)
#   - Traefik is already running on the external network referenced by .env (TRAEFIK_NETWORK)
#   - .env has been edited with real values (POSTGRES_PASSWORD, WEB_HOST, API_HOST, …)
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "❌ .env not found in $(pwd). Copy .env.example and edit it first." >&2
  exit 1
fi

# Export every key in .env so build-args and stack deploy can interpolate them.
set -a
# shellcheck disable=SC1091
source .env
set +a

: "${API_HOST:?API_HOST not set in .env}"
: "${WEB_HOST:?WEB_HOST not set in .env}"
: "${TRAEFIK_NETWORK:?TRAEFIK_NETWORK not set in .env}"
: "${TRAEFIK_CERTRESOLVER:?TRAEFIK_CERTRESOLVER not set in .env}"

# The stack file references KINDLE_APP_DIR for bind mounts; default to the current dir.
export KINDLE_APP_DIR="${KINDLE_APP_DIR:-$(pwd)}"

echo "==> Ensuring data directories exist"
mkdir -p "$KINDLE_APP_DIR/data/playwright" "$KINDLE_APP_DIR/data/vapid"

if ! docker network ls --format '{{.Name}}' | grep -qx "$TRAEFIK_NETWORK"; then
  echo "❌ External network '$TRAEFIK_NETWORK' not found. Is Traefik running?" >&2
  exit 1
fi

echo "==> Building API image (Playwright + chromium — first build takes a few minutes)"
docker build -t kindle-api:latest ./api

echo "==> Building Web image (Vite build with VITE_API_URL=https://${API_HOST})"
docker build \
  -t kindle-web:latest \
  --build-arg VITE_API_URL="https://${API_HOST}" \
  ./web

echo "==> Deploying stack 'kindle'"
docker stack deploy -c docker-compose.stack.yml kindle

echo
echo "==> Done. Watch service status with:"
echo "    docker service ls | grep kindle"
echo "    docker service logs -f kindle_api"
echo
echo "If TLS certs don't appear within ~2 min, check Traefik logs:"
echo "    docker service logs traefik_traefik 2>&1 | tail -50"
