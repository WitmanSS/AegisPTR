#!/bin/sh
set -eu

if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
  python scripts/run_migrations.py

  if [ -n "${ADMIN_USER:-}" ] && [ -n "${ADMIN_PASS:-}" ]; then
    python scripts/seed_roles_and_admin.py --admin-user "$ADMIN_USER" --admin-pass "$ADMIN_PASS"
  else
    python scripts/seed_roles_and_admin.py
  fi
fi

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec uvicorn app.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}"
