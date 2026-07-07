"""Integration test for the CBS Postcode6 upsert against real PostGIS.

Proves the geometry upsert is idempotent (re-running does not duplicate) and that the RD/28992
GeoJSON is reprojected to a valid 4326 MultiPolygon. Uses SYNTHETIC geometry inside a
transaction that is ALWAYS ROLLED BACK — nothing is persisted. Skips if the DB is unreachable.
"""

from __future__ import annotations

from datetime import date

import pytest

from ingestion.cbs_postcode6 import Area, upsert

try:
    from db.connection import connect

    _conn = connect()
    _conn.close()
except Exception:  # pragma: no cover - environment without a DB
    pytest.skip("database not reachable; skipping integration test", allow_module_level=True)

# Synthetic RD/28992 MultiPolygon near Amsterdam.
_GEOM = (
    '{"type":"MultiPolygon","coordinates":'
    "[[[[122300.0,490900.0],[122400.0,490900.0],[122400.0,491000.0],"
    "[122300.0,491000.0],[122300.0,490900.0]]]]}"
)


def test_upsert_reprojects_and_is_idempotent() -> None:
    areas = [Area("1011AB", _GEOM, date(2024, 1, 1))]
    conn = connect()
    try:
        upsert(areas, conn=conn)
        upsert(areas, conn=conn)  # second run must NOT duplicate (pc6 is PK)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT count(*), bool_and(ST_IsValid(geom)),
                       bool_and(ST_SRID(geom) = 4326),
                       bool_and(GeometryType(geom) = 'MULTIPOLYGON'),
                       bool_and(source = 'cbs_postcode6')
                FROM areas WHERE pc6 = '1011AB'
                """
            )
            count, valid, srid_ok, is_multipoly, src_ok = cur.fetchone()
            assert count == 1  # one row, not two -> idempotent
            assert valid and srid_ok and is_multipoly and src_ok

            # Reprojected centroid must land in the Netherlands (lon ~4-5, lat ~52).
            cur.execute(
                "SELECT ST_X(ST_Centroid(geom)), ST_Y(ST_Centroid(geom)) "
                "FROM areas WHERE pc6 = '1011AB'"
            )
            lon, lat = cur.fetchone()
            assert 3.0 < lon < 7.5 and 50.5 < lat < 53.8
    finally:
        conn.rollback()  # persist nothing
        conn.close()
