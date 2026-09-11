"""Simple migration runner for SQL files in `backend/migrations/`.
Run: python scripts/run_migrations.py
It uses the `database_url` from `app.core.config.settings`.
"""
from pathlib import Path
from sqlalchemy import text, create_engine
from app.core.config import settings


def run():
    migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        for sql in sql_files:
            print(f"Applying {sql.name}")
            with open(sql, "r", encoding="utf-8") as fh:
                sql_text = fh.read()
            conn.execute(text(sql_text))
        conn.commit()


if __name__ == "__main__":
    run()
