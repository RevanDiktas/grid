"""Ingestion job for the Netbeheer Nederland Capaciteitskaart PC6 source.

Reference implementation of the build-ingestion-job pattern: fetch → snapshot → parse &
normalise → validate → upsert (idempotent) → stamp provenance → log.

Reality notes (see docs/data-sources.md for the full write-up):
- The PC6 file encodes availability as a **category** (traffic-light / ordinal 0–3), NOT MW.
  So we populate ``offtake_status`` / ``feedin_status`` and leave the MW columns NULL.
- Exact headers, encoding, and the numeric<->label mapping were NOT sampled live (the backend
  was returning HTTP 500), so the parser **adapts to the real header at runtime and fails loudly**
  on anything it does not recognise, rather than guessing a structure.
- ``as_of`` comes from the file's HTTP ``Last-Modified``; if absent we refuse to invent one.
"""

from __future__ import annotations

import csv
import io
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx
import psycopg

from db.connection import connect

SOURCE = "capaciteitskaart"
CSV_URL = "https://data.partnersinenergie.nl/capaciteitskaart/api/download/congestie_pc6.csv"
FORWARD_YEAR_HORIZON = 0  # the live map is the present-day picture
# Low, deliberately: the source is explicitly "indicatief" and our numeric<->class mapping
# is provisional until brondata_documentatie.txt is sampled.
CONFIDENCE = 0.4

_REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = _REPO_ROOT / "data" / "snapshots" / SOURCE

# Canonical availability classes (must match the Postgres `availability_class` enum).
AVAILABLE = "available"
LIMITED = "limited"
STUDY = "study"
CONGESTED = "congested"
UNKNOWN = "unknown"
VALID_CLASSES = frozenset({AVAILABLE, LIMITED, STUDY, CONGESTED, UNKNOWN})

# Exact-token mapping (colour names + ordinal 0–3, provisional per research).
_CLASS_BY_TOKEN = {
    "groen": AVAILABLE, "green": AVAILABLE,
    "oranje": LIMITED, "orange": LIMITED, "geel": LIMITED, "yellow": LIMITED,
    "grijs": STUDY, "grey": STUDY, "gray": STUDY,
    "rood": CONGESTED, "red": CONGESTED,
    "0": AVAILABLE, "1": LIMITED, "2": STUDY, "3": CONGESTED,
    "": UNKNOWN, "nvt": UNKNOWN, "n.v.t.": UNKNOWN, "onbekend": UNKNOWN,
}

# Header-detection patterns (case-insensitive substring match against the real header).
_PC6_PATTERNS = ("postcode", "pc6", "pc_6", "pc-6")
_OFFTAKE_PATTERNS = ("afname", "withdrawal", "offtake")
_FEEDIN_PATTERNS = ("invoeding", "teruglever", "injection", "feedin", "feed_in", "feed-in")


@dataclass
class Observation:
    pc6: str
    offtake_status: str
    feedin_status: str
    as_of: date
    raw: dict[str, str] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Pure parse/normalise functions (unit-testable without network or DB)
# --------------------------------------------------------------------------- #

def normalize_pc6(value: str) -> str:
    """Normalise a Dutch postcode-6 to canonical form, e.g. ' 1012 ab ' -> '1012AB'."""
    pc6 = value.strip().upper().replace(" ", "")
    if len(pc6) != 6 or not pc6[:4].isdigit() or not pc6[4:].isalpha():
        raise ValueError(f"not a valid PC6 postcode: {value!r}")
    return pc6


def classify(value: str) -> str:
    """Map a raw capacity/congestion cell to an availability_class. Fails loudly if unknown."""
    token = value.strip().lower()
    if token in _CLASS_BY_TOKEN:
        return _CLASS_BY_TOKEN[token]
    # Substring heuristics for the long Dutch legend phrases.
    if "later" in token or "geen kleur" in token:
        return UNKNOWN
    if "tekort" in token:
        return CONGESTED
    if "onderzoek" in token:
        return STUDY
    if "beperkt" in token:
        return LIMITED
    if "beschikbaar" in token:  # (after 'beperkt' check) -> plain availability
        return AVAILABLE
    raise ValueError(f"unrecognised capacity value {value!r} — update the mapping, do not guess")


def _find_column(header: list[str], patterns: tuple[str, ...], role: str) -> str:
    for col in header:
        low = col.strip().lower()
        if any(p in low for p in patterns):
            return col
    raise ValueError(
        f"could not find the {role} column in header {header!r} "
        f"(looked for {patterns}); inspect the real file before ingesting"
    )


def parse_rows(csv_text: str, as_of: date) -> list[Observation]:
    """Parse the PC6 congestion CSV text into Observations. Detects delimiter and columns."""
    sample = csv_text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = csv.excel  # default: comma
    reader = csv.DictReader(io.StringIO(csv_text), dialect=dialect)
    if reader.fieldnames is None:
        raise ValueError("CSV has no header row")
    header = list(reader.fieldnames)

    pc6_col = _find_column(header, _PC6_PATTERNS, "PC6")
    offtake_col = _find_column(header, _OFFTAKE_PATTERNS, "offtake/afname")
    feedin_col = _find_column(header, _FEEDIN_PATTERNS, "feed-in/invoeding")

    out: list[Observation] = []
    for row in reader:
        pc6 = normalize_pc6(row[pc6_col])
        out.append(
            Observation(
                pc6=pc6,
                offtake_status=classify(row[offtake_col]),
                feedin_status=classify(row[feedin_col]),
                as_of=as_of,
                raw={k: (v or "") for k, v in row.items()},
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Edges: network + DB (isolated so the pure functions above stay testable)
# --------------------------------------------------------------------------- #

def _as_of_from_headers(headers: httpx.Headers) -> date:
    last_modified = headers.get("last-modified")
    if not last_modified:
        raise RuntimeError(
            "no Last-Modified header on the CSV; cannot determine the data's as_of date "
            "without inventing one. Refusing to ingest (see data rules: no fabrication)."
        )
    return parsedate_to_datetime(last_modified).date()


def fetch(url: str = CSV_URL, *, retries: int = 5) -> tuple[bytes, date]:
    """Fetch the CSV, retrying on 5xx (the backend has been intermittently 500-ing)."""
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        last_status = None
        for attempt in range(retries):
            resp = client.get(url)
            last_status = resp.status_code
            if resp.status_code >= 500:
                wait = 2.0 * (attempt + 1)
                print(
                    f"  fetch: HTTP {resp.status_code} "
                    f"(attempt {attempt + 1}/{retries}); retrying in {wait:.0f}s"
                )
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.content, _as_of_from_headers(resp.headers)
    raise RuntimeError(
        f"capaciteitskaart backend unavailable (last HTTP {last_status}) after {retries} attempts; "
        "no rows written. Re-run `make ingest SOURCE=capaciteitskaart` when it recovers."
    )


def _decode(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("could not decode CSV with any expected encoding")


def snapshot(content: bytes) -> Path:
    """Persist the raw fetch before parsing, so history is reprocessable."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    path = SNAPSHOT_DIR / f"{stamp}.csv"
    path.write_bytes(content)
    return path


def upsert(observations: list[Observation], conn: psycopg.Connection | None = None) -> int:
    """Idempotently upsert areas + capacity_observations. Returns rows written.

    Pass an existing ``conn`` to run inside a caller-managed transaction (used by the
    integration test to write-and-rollback); otherwise a connection is opened and committed.
    """
    if not observations:
        return 0
    if conn is None:
        conn = connect()
        own = True
    else:
        own = False
    try:
        with conn.cursor() as cur:
            for obs in observations:
                cur.execute(
                    "INSERT INTO areas (pc6, source, as_of) VALUES (%s, %s, %s) "
                    "ON CONFLICT (pc6) DO NOTHING",
                    (obs.pc6, SOURCE, obs.as_of),
                )
                cur.execute(
                    """
                    INSERT INTO capacity_observations
                        (pc6, as_of, forward_year_horizon, offtake_status, feedin_status,
                         confidence, source, raw)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (pc6, source, as_of, forward_year_horizon)
                        WHERE pc6 IS NOT NULL
                    DO UPDATE SET
                        offtake_status = EXCLUDED.offtake_status,
                        feedin_status  = EXCLUDED.feedin_status,
                        confidence     = EXCLUDED.confidence,
                        raw            = EXCLUDED.raw,
                        ingested_at    = now()
                    """,
                    (
                        obs.pc6, obs.as_of, FORWARD_YEAR_HORIZON,
                        obs.offtake_status, obs.feedin_status, CONFIDENCE, SOURCE,
                        _json(obs.raw),
                    ),
                )
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()
    return len(observations)


def _json(data: dict[str, str]) -> str:
    import json

    return json.dumps(data, ensure_ascii=False)


def main() -> None:
    print(f"ingest[{SOURCE}]: fetching {CSV_URL}")
    content, as_of = fetch()
    snap = snapshot(content)
    print(f"ingest[{SOURCE}]: snapshot -> {snap} ({len(content)} bytes), as_of={as_of}")

    observations = parse_rows(_decode(content), as_of)
    if not observations:
        raise RuntimeError("parsed 0 rows — aborting rather than writing an empty result")

    written = upsert(observations)
    print(
        f"ingest[{SOURCE}]: upserted {written} PC6 observation(s), "
        f"as_of={as_of}, source={SOURCE}"
    )


if __name__ == "__main__":
    main()
