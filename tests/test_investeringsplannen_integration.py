"""Integration test for the Liander IP2026 upsert against real PostGIS.

Proves the timeline upsert is idempotent (re-running does not duplicate) using SYNTHETIC facts
inside a transaction that is ALWAYS ROLLED BACK — nothing is persisted. Skips if the DB is down.
"""

from __future__ import annotations

from datetime import date

import pytest

from ingestion.investeringsplannen_liander import SOURCE, TimelineFact, upsert

try:
    from db.connection import connect

    _c = connect()
    _c.close()
except Exception:  # pragma: no cover - environment without a DB
    pytest.skip("database not reachable; skipping integration test", allow_module_level=True)

AS_OF = date(2026, 1, 4)


def _facts() -> list[TimelineFact]:
    return [
        TimelineFact(
            "liander:os-testville-10-1i:offtake",
            "OS TESTVILLE",
            "10-1i",
            "offtake",
            2033,
            51.4,
            0.35,
        ),
        TimelineFact(
            "liander:os-othertown-20-1i:feedin", "OS OTHERTOWN", "20-1i", "feedin", 2026, 113.7, 0.5
        ),
    ]


def test_upsert_is_idempotent_and_geography_null() -> None:
    conn = connect()
    try:
        upsert(_facts(), AS_OF, conn=conn)
        upsert(_facts(), AS_OF, conn=conn)  # second run must NOT duplicate

        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*), "
                "bool_and(pc6 IS NULL AND substation_id IS NULL AND geom IS NULL), "
                "bool_and(source = %s) FROM capacity_timeline "
                "WHERE project_ref = ANY(%s)",
                (
                    SOURCE,
                    ["liander:os-testville-10-1i:offtake", "liander:os-othertown-20-1i:feedin"],
                ),
            )
            count, geo_null, src_ok = cur.fetchone()
            assert count == 2  # two rows, not four → idempotent
            assert geo_null  # geography left NULL (unresolved), never guessed
            assert src_ok
    finally:
        conn.rollback()  # persist nothing
        conn.close()
