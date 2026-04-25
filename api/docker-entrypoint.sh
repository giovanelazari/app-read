#!/bin/sh
set -e

# Apply pending migrations on every boot. Idempotent — Alembic skips up-to-date heads.
# In Swarm mode this gives us auto-schema-management without a separate migrate task.
echo "[entrypoint] Running alembic upgrade head…"
alembic upgrade head

echo "[entrypoint] Starting: $*"
exec "$@"
