"""Ingestion job for CBS Postcode6 PC6 polygon geometry (via PDOK WFS).

This is the **geometry backbone**: it fills the ``areas`` layer with a MultiPolygon per
6-char Dutch postcode (PC6), so PC6-keyed capacity data (e.g. capaciteitskaart) can be joined
to geometry and rendered on a map. It carries *geometry*, not capacity — no MW, no status.

Follows the build-ingestion-job pattern: fetch → snapshot → parse & normalise → validate →
idempotent upsert → provenance (source + as_of) → log.

Reality notes (verified live 2026-07-07, see docs/data-sources.md):
- Source: PDOK WFS 2.0 ``postcode6:postcode6`` (CBS Postcode6 2024). Keyless, CC BY 4.0.
- **The service returns GeoJSON in EPSG:28992 (RD New) by default** — coordinates are
  easting,northing metres, NOT lon,lat. We deliberately fetch native RD (unambiguous axis
  order) and let PostGIS ``ST_Transform`` reproject to 4326, dodging the WFS-2.0 EPSG:4326
  lat,lon axis-flip trap entirely (that trap silently returns HTTP 200 + wrong/empty data).
- ~464,964 features nationally; server page cap = 1000 → page with ``startIndex`` + ``count``.
- **No Last-Modified header** on the response, so ``as_of`` cannot come from HTTP. We use the
  dataset vintage in the URL path (2024) → 2024-01-01 (the reference date of an annual CBS
  product), logged explicitly — a documented convention, not an invented figure.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx
import psycopg

from db.connection import connect
from ingestion.capaciteitskaart import normalize_pc6  # reuse the PC6 normaliser

SOURCE = "cbs_postcode6"
VINTAGE_YEAR = 2024
WFS_BASE = f"https://service.pdok.nl/cbs/postcode6/{VINTAGE_YEAR}/wfs/v1_0"
TYPE_NAME = "postcode6:postcode6"
PC6_FIELD = "postcode6"
SOURCE_SRID = 28992  # RD New — the service's native GeoJSON CRS
PAGE_SIZE = 1000  # server maxRecordCount

# Annual-product reference date. No Last-Modified is served; this is the documented vintage
# date, NOT an invented one (see module docstring / data rules: no fabrication).
AS_OF = date(VINTAGE_YEAR, 1, 1)

# Netherlands RD/28992 envelope (generous). Used to catch a CRS/axis mistake: if the service
# ever returned lon,lat degrees (~[4.9, 52.4]) instead of RD metres, it falls far outside this.
_RD_X = (0.0, 300_000.0)
_RD_Y = (280_000.0, 640_000.0)

_REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = _REPO_ROOT / "data" / "snapshots" / SOURCE


@dataclass
class Area:
    pc6: str
    geom_geojson: str  # a GeoJSON geometry (MultiPolygon) as text, coordinates in RD/28992
    as_of: date


# --------------------------------------------------------------------------- #
# Pure parse/validate functions (unit-testable without network or DB)
# --------------------------------------------------------------------------- #

def parse_features(geojson: dict, as_of: date = AS_OF) -> list[Area]:
    """Turn a WFS GeoJSON FeatureCollection into Areas.

    Skips (with a logged reason) any feature missing a postcode or a geometry, rather than
    guessing. Raises on a malformed postcode (we would rather fail loudly than store garbage).
    """
    out: list[Area] = []
    for feature in geojson.get("features", []):
        props = feature.get("properties") or {}
        raw_pc6 = props.get(PC6_FIELD)
        geom = feature.get("geometry")
        if not raw_pc6:
            print(f"  skip: feature {feature.get('id')!r} has no {PC6_FIELD}")
            continue
        if not geom or not geom.get("coordinates"):
            print(f"  skip: postcode {raw_pc6!r} has no geometry")
            continue
        out.append(
            Area(
                pc6=normalize_pc6(raw_pc6),
                geom_geojson=json.dumps(geom, ensure_ascii=False),
                as_of=as_of,
            )
        )
    return out


def _first_coord(geometry: dict) -> tuple[float, float]:
    """Drill to the first (x, y) coordinate pair of any (Multi)Polygon geometry."""
    node = geometry["coordinates"]
    while isinstance(node, list) and node and isinstance(node[0], list):
        node = node[0]
    return float(node[0]), float(node[1])


def assert_rd_envelope(features: list[dict]) -> None:
    """Guard: representative coordinates must be inside the NL RD/28992 envelope.

    Catches a silent CRS/axis mistake (e.g. lon,lat degrees) that would otherwise land valid
    JSON but nonsensical geometry in the database.
    """
    checked = 0
    for feature in features:
        geom = feature.get("geometry")
        if not geom or not geom.get("coordinates"):
            continue
        x, y = _first_coord(geom)
        if not (_RD_X[0] <= x <= _RD_X[1] and _RD_Y[0] <= y <= _RD_Y[1]):
            raise ValueError(
                f"coordinate ({x}, {y}) is outside the NL RD/28992 envelope — the service CRS "
                f"is not EPSG:{SOURCE_SRID} as assumed; refusing to ingest wrong geometry"
            )
        checked += 1
    if checked == 0:
        raise ValueError("no geometries to validate — refusing to proceed (nothing fetched)")


# --------------------------------------------------------------------------- #
# Edges: network + DB (isolated so the pure functions above stay testable)
# --------------------------------------------------------------------------- #

def _keyset_filter(after_pc6: str) -> str:
    """OGC FES 2.0 filter ``postcode6 > after_pc6`` — the keyset cursor. postcode6 is
    ``\\d{4}[A-Z]{2}`` so it needs no XML escaping."""
    return (
        '<fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0">'
        "<fes:PropertyIsGreaterThan>"
        f"<fes:ValueReference>{PC6_FIELD}</fes:ValueReference>"
        f"<fes:Literal>{after_pc6}</fes:Literal>"
        "</fes:PropertyIsGreaterThan></fes:Filter>"
    )


def fetch_page(
    *,
    client: httpx.Client,
    count: int = PAGE_SIZE,
    bbox: str | None = None,
    start_index: int = 0,
    after_pc6: str | None = None,
    retries: int = 5,
) -> dict:
    """Fetch one WFS GeoJSON page.

    Two paging modes (the server caps numeric ``startIndex`` at ~50k, so the national load
    cannot use offset paging — it uses a keyset cursor instead):
    - **bbox mode** (``bbox`` set): offset paging within a small spatial tile (smoke-load).
    - **keyset mode** (default): ``sortBy=postcode6`` + FES ``postcode6 > after_pc6``; no cap.
    """
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": TYPE_NAME,
        "outputFormat": "application/json",
        "count": str(count),
    }
    if bbox is not None:
        params["bbox"] = f"{bbox},urn:ogc:def:crs:EPSG::{SOURCE_SRID}"
        params["startIndex"] = str(start_index)
    else:
        params["sortBy"] = PC6_FIELD  # stable order for the keyset cursor
        if after_pc6 is not None:
            params["filter"] = _keyset_filter(after_pc6)
    where = f"bbox startIndex={start_index}" if bbox is not None else f"after={after_pc6}"
    for attempt in range(retries):
        try:
            resp = client.get(WFS_BASE, params=params)
        except httpx.TransportError as exc:
            # Transient transport-layer failure (read/connect timeout, reset). Over ~465
            # requests a blip is near-certain; retry rather than abort the whole load.
            wait = 2.0 * (attempt + 1)
            print(f"  fetch: transport error {type(exc).__name__} (attempt {attempt + 1}/"
                  f"{retries}); retrying in {wait:.0f}s")
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            wait = 2.0 * (attempt + 1)
            print(f"  fetch: HTTP {resp.status_code} (attempt {attempt + 1}/{retries}); "
                  f"retrying in {wait:.0f}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"PDOK WFS unavailable after {retries} attempts ({where})")


def iter_pages(
    *, bbox: str | None = None, max_pages: int | None = None, pause_s: float = 0.2
) -> Iterator[tuple[int, list[dict]]]:
    """Yield ``(page, features)`` one WFS page at a time (streaming).

    Streaming (vs. accumulating all ~465k features) keeps memory flat and lets the caller
    upsert per page so progress is durable and resumable. National pulls use a keyset cursor
    on ``postcode6`` (no offset cap); bbox pulls use offset paging within the small tile.
    """
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        page = 0
        start_index = 0
        after_pc6: str | None = None
        while True:
            batch = fetch_page(
                client=client, bbox=bbox, start_index=start_index, after_pc6=after_pc6
            )
            got = batch.get("features", [])
            page += 1
            yield page, got
            if len(got) < PAGE_SIZE:
                break  # short page = last page
            if max_pages is not None and page >= max_pages:
                print(f"  stopping at max_pages={max_pages}")
                break
            if bbox is not None:
                start_index += PAGE_SIZE
            else:
                # keyset cursor = the last (max) postcode6 of this sorted page
                after_pc6 = got[-1]["properties"][PC6_FIELD]
            time.sleep(pause_s)  # be gentle


def snapshot_page(features: list[dict], *, tag: str, seq: int) -> Path:
    """Persist one raw page before parsing, so history is reprocessable. Per-page (not one giant
    file) so a partial national load still leaves the fetched pages on disk."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / f"{VINTAGE_YEAR}_{tag}_{seq:04d}.geojson"
    payload = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(payload, ensure_ascii=False))
    return path


def upsert(areas: list[Area], conn: psycopg.Connection | None = None) -> int:
    """Idempotently upsert PC6 polygons into ``areas``. Returns rows written.

    Geometry arrives as RD/28992 GeoJSON and is reprojected to 4326 (schema SRID) in-database.
    CBS is the authoritative geometry-provenance owner of the ``areas`` row, so on conflict we
    set geom/source/as_of (capaciteitskaart only ever creates keyed stubs via DO NOTHING).
    Pass an existing ``conn`` to run inside a caller-managed transaction (used by tests).
    """
    if not areas:
        return 0
    if conn is None:
        conn = connect()
        own = True
    else:
        own = False
    try:
        with conn.cursor() as cur:
            for area in areas:
                cur.execute(
                    """
                    INSERT INTO areas (pc6, geom, source, as_of)
                    VALUES (
                        %s,
                        -- reproject RD->4326, then repair source self-intersections
                        -- (~17 of 464964 CBS polygons); CollectionExtract(...,3) keeps
                        -- polygons only and guarantees a MultiPolygon for the typed column.
                        ST_Multi(ST_CollectionExtract(
                            ST_MakeValid(
                                ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s), %s), 4326)
                            ), 3)),
                        %s, %s
                    )
                    ON CONFLICT (pc6) DO UPDATE SET
                        geom        = EXCLUDED.geom,
                        source      = EXCLUDED.source,
                        as_of       = EXCLUDED.as_of,
                        ingested_at = now()
                    """,
                    (area.pc6, area.geom_geojson, SOURCE_SRID, SOURCE, area.as_of),
                )
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()
    return len(areas)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def run(*, bboxes: list[str] | None = None, max_pages: int | None = None) -> int:
    """Stream pages → per-page (validate → snapshot → parse → upsert → commit). ``bboxes``
    (RD/28992) restricts the pull (used for the smoke-load); None pulls the whole country.

    Per-page commit means a national load is durable and resumable: a mid-run failure leaves the
    already-fetched pages upserted (idempotent on the pc6 PK), so a re-run finishes the rest.
    """
    targets = bboxes if bboxes is not None else [None]
    tag = "smoke" if bboxes is not None else "national"

    written = 0
    seq = 0
    conn = connect()
    try:
        for bbox in targets:
            where = f"bbox={bbox}" if bbox else "national"
            print(f"ingest[{SOURCE}]: fetching {where}")
            for page, got in iter_pages(bbox=bbox, max_pages=max_pages):
                seq += 1
                print(f"  page {page}: -> {len(got)} features (committed so far {written})")
                if not got:
                    continue
                assert_rd_envelope(got)  # per-page CRS guard, before any DB write
                snapshot_page(got, tag=tag, seq=seq)
                areas = parse_features({"features": got})
                upsert(areas, conn=conn)
                conn.commit()  # durable per page
                written += len(areas)
    finally:
        conn.close()

    if written == 0:
        raise RuntimeError("upserted 0 features — aborting rather than claiming an empty result")

    print(f"ingest[{SOURCE}]: upserted {written} PC6 polygon(s), as_of={AS_OF} "
          f"(vintage {VINTAGE_YEAR}; no Last-Modified served), source={SOURCE}")
    return written


def main() -> None:
    import os

    bbox_env = os.environ.get("CBS_PC6_BBOX")  # 'x1,y1,x2,y2' RD/28992, optional smoke bbox
    max_pages_env = os.environ.get("CBS_PC6_MAX_PAGES")
    run(
        bboxes=[bbox_env] if bbox_env else None,
        max_pages=int(max_pages_env) if max_pages_env else None,
    )


if __name__ == "__main__":
    main()
