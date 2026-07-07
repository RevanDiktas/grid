"""Forward-only migration runner.

Applies every ``db/migrations/*.sql`` file not yet recorded in ``schema_migrations``,
in filename order, each in its own transaction. Idempotent: re-running only applies
what is new. Never drops data (that discipline lives in the migration files themselves).
"""

from __future__ import annotations

from pathlib import Path

from db.connection import connect

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _applied(cur: object) -> set[str]:
    cur.execute(  # type: ignore[attr-defined]
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename   text PRIMARY KEY,
            applied_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute("SELECT filename FROM schema_migrations")  # type: ignore[attr-defined]
    return {row[0] for row in cur.fetchall()}  # type: ignore[attr-defined]


def main() -> None:
    # Skip macOS AppleDouble sidecars (._*.sql) that exFAT sprinkles next to real files.
    files = sorted(p for p in MIGRATIONS_DIR.glob("*.sql") if not p.name.startswith("._"))
    with connect() as conn:
        with conn.cursor() as cur:
            done = _applied(cur)
        conn.commit()

        pending = [f for f in files if f.name not in done]
        if not pending:
            print(f"migrate: up to date ({len(done)} already applied)")
            return

        for path in pending:
            print(f"migrate: applying {path.name}")
            sql = path.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,)
                )
            conn.commit()

        print(f"migrate: applied {len(pending)} migration(s)")


if __name__ == "__main__":
    main()
