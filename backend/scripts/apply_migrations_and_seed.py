"""Run SQL migrations then seed initial roles/admin.
Usage:
  python scripts/apply_migrations_and_seed.py --admin-user admin --admin-pass secret
Or set env vars ADMIN_USER/ADMIN_PASS and run without args.
"""
import os
import argparse
from backend.scripts.run_migrations import run as run_migrations
from backend.scripts.seed_roles_and_admin import seed as seed_roles


def main(admin_user: str | None, admin_pass: str | None):
  try:
    print("Running SQL migrations...")
    run_migrations()
    print("Migrations applied.")
  except Exception as exc:  # pragma: no cover - operational
    print("Error while applying migrations:", exc)
    raise

  try:
    print("Seeding roles/admin (if provided)...")
    seed_roles(admin_user, admin_pass)
    print("Seeding complete.")
  except Exception as exc:  # pragma: no cover - operational
    print("Error while seeding roles/admin:", exc)
    raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--admin-user", default=os.environ.get("ADMIN_USER"))
    p.add_argument("--admin-pass", default=os.environ.get("ADMIN_PASS"))
    args = p.parse_args()
    main(args.admin_user, args.admin_pass)
