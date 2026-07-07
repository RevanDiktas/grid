"""Integration test for the capaciteitskaart DB write-path, against real PostGIS.

Proves the upsert is idempotent (re-running does not duplicate) using SYNTHETIC observations
inside a transaction that is ALWAYS ROLLED BACK — so nothing is persisted and no fabricated
capacity ever lands in the database. Skips cleanly if the database is unreachable.
"""

from __future__ import annotations

from datetime import date

import pytest

from ingestion.capaciteitskaart import Observation, upsert

try:
    from db.connection import connect

    _conn = connect()
except Exception:  # pragma: no cover - environment without a DB
    pytest.skip("database not reachable; skipping integration test", allow_module_level=True)


def test_upsert_is_idempotent_and_leaves_nothing() -> None:
    obs = [
        Observation("1012AB", "available", "congested", date(2026, 6, 1), {"synthetic": "1"}),
        Observation("9711LV", "limited", "available", date(2026, 6, 1), {"synthetic": "1"}),
    ]
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM capacity_observations")
            before = cur.fetchone()[0]

        upsert(obs, conn=conn)
        upsert(obs, conn=conn)  # second run must NOT duplicate

        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM capacity_observations WHERE pc6 = ANY(%s)",
                (["1012AB", "9711LV"],),
            )
            assert cur.fetchone()[0] == 2  # two rows, not four → idempotent
    finally:
        conn.rollback()  # persist nothing
        conn.close()

    # Confirm the rollback left the table exactly as it was.
    verify = connect()
    try:
        with verify.cursor() as cur:
            cur.execute("SELECT count(*) FROM capacity_observations")
            assert cur.fetchone()[0] == before
    finally:
        verify.close()
