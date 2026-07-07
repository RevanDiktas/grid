"""Ingestion job for the **Liander Investeringsplan 2026** — the forward-looking timeline
("when does power arrive here"). Facts-only, licence-constrained.

LICENCE (see decisions D-licence / provenance.sources): the IP is a proprietary netbeheerder
publication with **no open licence**. We extract FACTS into our own schema and **never store,
serve, mirror, or reproduce the PDF or its tables/figures/text**. Concretely:
- the PDF is fetched to a temp file, parsed, and **deleted** — never written to the repo or to
  ``data/snapshots/``;
- the snapshot persisted is only our small structured **extracted facts**, not the source.

Source of the facts: appendix **§10.6 "Majeure capaciteitsknelpunten en uitbreidingsinvesteringen
elektriciteit"** (pages ~123+). One row per station-knelpunt-direction, carrying: the knelpunt id,
onset year and capacity shortfall (MW) per ACM scenario (KM/EV/GB) at first-year and 2035, the
fixing investment id(s), and the IBN (in-service) year(s). We normalise this into
``capacity_timeline`` — facts, not their layout.

Modelling choices (documented, indicative, low confidence — every value traces to a real cell or a
stated aggregation of real cells; nothing is invented):
- ``added_mw`` = the **max across the three scenarios of the 2035 capaciteitstekort (MW)** — an
  indicative upper bound of the capacity the reinforcement must resolve at the horizon.
- ``expected_year`` = the **latest concrete IBN year** across the fixing investments (ranges use
  their end year) — the conservative "capacity reliably relieved by" year. NULL (with a logged
  reason) when every IBN is undetermined (``n.t.b.``/``n.v.t.``) — never guessed.
- geography stays NULL for now (no station→coordinate source yet); ``location_name`` keeps the
  station name for later geocoding.
"""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import httpx
import psycopg
import pypdf

from db.connection import connect

JOB_NAME = "investeringsplannen_liander"  # `make ingest SOURCE=investeringsplannen_liander`
SOURCE = "investeringsplannen_2026"  # registry / provenance key (report-safe: facts only)
OPERATOR = "liander"

PDF_URL = (
    "https://www.liander.nl/-/media/files/financiele-communicatie/investeringsplannen/"
    "investeringsplannen-2026/investeringsplan-liander-elektriciteit-en-gas-2026.pdf"
)
APPENDIX_TITLE = "10.6 Majeure capaciteitsknelpunten"
FALLBACK_AS_OF = date(2026, 1, 1)  # IP2026 vintage, if the PDF carries no CreationDate

_REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = _REPO_ROOT / "data" / "snapshots" / JOB_NAME  # FACTS only, never the PDF

# Liander's service-area provinces (appendix is organised per province; a bare province line
# switches the running context). Used to tag facts for verification (not a DB column).
_PROVINCES = frozenset(
    {
        "Friesland",
        "Groningen",
        "Drenthe",
        "Noord-Holland",
        "Flevoland",
        "Gelderland",
        "Zuid-Holland",
        "Utrecht",
        "Noord-Brabant",
    }
)

_NULL_TOKENS = frozenset({"n.v.t.", "n.t.b.", "nvt", "ntb", ""})
# A knelpunt id like '10-1i', optionally combined ('10-1i + 10-2i'), at the end of the label.
_KNELPUNT_RE = re.compile(r"\s*((?:\d{1,3}-\d+\w?)(?:\s*\+\s*\d{1,3}-\d+\w?)*)\s*$")
_YEAR_RE = re.compile(r"\b(20\d{2})\b")


@dataclass
class TimelineFact:
    project_ref: str
    location_name: str
    bottleneck: str | None
    direction: str | None  # 'offtake' | 'feedin'
    expected_year: int | None
    added_mw: float | None
    confidence: float
    province: str | None = None  # verification context, not persisted as a column
    raw_extract: dict[str, str] = field(
        default_factory=dict
    )  # OUR extracted fields, for the snapshot


# --------------------------------------------------------------------------- #
# Pure parse/normalise functions (unit-testable without network or DB)
# --------------------------------------------------------------------------- #


def parse_decimal(token: str) -> float | None:
    """NL decimal-comma number → float; null tokens (n.v.t./n.t.b.) → None."""
    tok = token.strip().lower()
    if tok in _NULL_TOKENS:
        return None
    try:
        return float(tok.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def parse_ibn_years(field_text: str) -> tuple[int | None, bool]:
    """Parse a semicolon-packed IBN-jaar cell into ``(latest_year, undetermined)``.

    Ranges ('2031 - 2033') use their END year (conservative in-service point). ``undetermined``
    is True if any packed value is n.t.b./n.v.t. Returns ``(None, True)`` when no concrete year.
    """
    parts = [p.strip() for p in field_text.split(";")]
    undetermined = False
    years: list[int] = []
    for part in parts:
        low = part.strip().lower()
        if low in _NULL_TOKENS:
            undetermined = True
            continue
        found = [int(y) for y in _YEAR_RE.findall(part)]
        if not found:
            undetermined = True
            continue
        years.append(max(found))  # a range → its end year
    return (max(years) if years else None), undetermined


def extract_knelpunt(label: str) -> tuple[str, str | None]:
    """Split a row label into ``(station_name, knelpunt_id)``; knelpunt_id None if not present."""
    m = _KNELPUNT_RE.search(label)
    if not m:
        return label.strip(), None
    knelpunt = re.sub(r"\s+", " ", m.group(1)).strip()
    station = label[: m.start()].strip()
    return (station or label.strip()), knelpunt


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_row(line: str, province: str | None = None) -> TimelineFact | None:
    """Parse one §10.6 data line into a TimelineFact, or return None (with a printed reason) if the
    line is not a well-formed data row. Never guesses — a malformed row is skipped, not invented."""
    m = re.search(r"\b(Afname|Opwek)\b", line)
    if not m:
        return None  # not a directional data row (province header / legend / wrapped fragment)
    label = line[: m.start()].strip()
    direction_nl = m.group(1)
    tokens = line[m.end() :].split()
    # Expected: kV, 9 scenario tokens (3 onset yr + 3 MW-1e + 3 MW-2035), ID investering, IBN...
    if len(tokens) < 12 or not tokens[0].isdigit():
        print(f"  skip malformed row (token layout): {label!r}")
        return None
    scenario = tokens[1:10]
    mw_2035 = [parse_decimal(t) for t in scenario[6:9]]
    ibn_field = " ".join(tokens[11:])

    added_mw = max((v for v in mw_2035 if v is not None), default=None)
    expected_year, undetermined = parse_ibn_years(ibn_field)
    station, knelpunt = extract_knelpunt(label)
    direction = "offtake" if direction_nl == "Afname" else "feedin"
    # Indicative source + scenario/aggregation modelling + undetermined IBN → low confidence.
    confidence = 0.35 if (undetermined or expected_year is None) else 0.5

    return TimelineFact(
        project_ref=_slug(f"{OPERATOR}:{label}:{direction}"),
        location_name=station,
        bottleneck=knelpunt,
        direction=direction,
        expected_year=expected_year,
        added_mw=added_mw,
        confidence=confidence,
        province=province,
        raw_extract={
            "station": station,
            "knelpunt": knelpunt or "",
            "direction": direction,
            "kV": tokens[0],
            "ibn_jaar": ibn_field,
            "capaciteitstekort_2035_mw_maxscenario": "" if added_mw is None else f"{added_mw}",
        },
    )


def parse_lines(lines: list[str]) -> list[TimelineFact]:
    """Parse appendix lines, tracking the running province from bare province-name lines."""
    province: str | None = None
    facts: list[TimelineFact] = []
    for raw in lines:
        line = raw.strip()
        if line in _PROVINCES:
            province = line
            continue
        fact = parse_row(line, province)
        if fact is not None:
            facts.append(fact)
    return facts


# --------------------------------------------------------------------------- #
# Edges: PDF fetch (temp, never persisted) + DB (isolated from the pure code)
# --------------------------------------------------------------------------- #


def _as_of_from_metadata(reader: pypdf.PdfReader) -> date:
    """Use the PDF's own CreationDate (e.g. 'D:20260104...') as as_of; else the IP2026 vintage."""
    meta: dict[str, object] = dict(reader.metadata or {})
    raw = meta.get("/CreationDate")
    if raw:
        m = re.search(r"D:(\d{4})(\d{2})(\d{2})", str(raw))
        if m:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    print(f"  no CreationDate in PDF metadata; falling back to IP2026 vintage {FALLBACK_AS_OF}")
    return FALLBACK_AS_OF


def fetch_and_extract() -> tuple[list[TimelineFact], date]:
    """Download the IP PDF to a TEMP file, extract §10.6 facts, and delete the PDF. The source
    document is never persisted (licence: facts only)."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            resp = client.get(PDF_URL)
            resp.raise_for_status()
            tmp.write(resp.content)
            tmp.flush()
        reader = pypdf.PdfReader(tmp.name)
        as_of = _as_of_from_metadata(reader)
        lines: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if APPENDIX_TITLE in text and ("Afname" in text or "Opwek" in text):
                lines.extend(text.splitlines())
    # tmp (the PDF) is deleted here on context exit.
    return parse_lines(lines), as_of


def snapshot(facts: list[TimelineFact], as_of: date) -> Path:
    """Persist ONLY our extracted facts (small structured file) — never the source PDF."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / f"{as_of.isoformat()}_{len(facts)}facts.json"
    payload = [
        {
            "project_ref": f.project_ref,
            "operator": OPERATOR,
            "location_name": f.location_name,
            "bottleneck": f.bottleneck,
            "direction": f.direction,
            "expected_year": f.expected_year,
            "added_mw": f.added_mw,
            "confidence": f.confidence,
            "province": f.province,
            **f.raw_extract,
        }
        for f in facts
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=0))
    return path


def upsert(facts: list[TimelineFact], as_of: date, conn: psycopg.Connection | None = None) -> int:
    """Idempotently upsert timeline facts into ``capacity_timeline`` on (source, project_ref).
    Geography stays NULL (unresolved) — never guessed. Pass ``conn`` for a caller-managed txn."""
    if not facts:
        return 0
    if conn is None:
        conn = connect()
        own = True
    else:
        own = False
    try:
        with conn.cursor() as cur:
            for f in facts:
                cur.execute(
                    """
                    INSERT INTO capacity_timeline
                        (project_ref, operator, location_name, bottleneck, direction,
                         expected_year, added_mw, confidence, source, as_of)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source, project_ref) DO UPDATE SET
                        operator      = EXCLUDED.operator,
                        location_name = EXCLUDED.location_name,
                        bottleneck    = EXCLUDED.bottleneck,
                        direction     = EXCLUDED.direction,
                        expected_year = EXCLUDED.expected_year,
                        added_mw      = EXCLUDED.added_mw,
                        confidence    = EXCLUDED.confidence,
                        as_of         = EXCLUDED.as_of,
                        ingested_at   = now()
                    """,
                    (
                        f.project_ref,
                        OPERATOR,
                        f.location_name,
                        f.bottleneck,
                        f.direction,
                        f.expected_year,
                        f.added_mw,
                        f.confidence,
                        SOURCE,
                        as_of,
                    ),
                )
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()
    return len(facts)


def main() -> None:
    print(f"ingest[{JOB_NAME}]: fetching Liander IP2026 PDF (temp; not persisted)")
    facts, as_of = fetch_and_extract()
    if not facts:
        raise RuntimeError(
            "extracted 0 facts from §10.6 — aborting rather than writing nothing useful"
        )
    snap = snapshot(facts, as_of)
    print(
        f"ingest[{JOB_NAME}]: snapshot (facts only) -> {snap} ({len(facts)} facts), as_of={as_of}"
    )
    resolved = sum(1 for f in facts if f.expected_year is not None)
    print(
        f"ingest[{JOB_NAME}]: {len(facts)} facts; {resolved} with a concrete IBN year. "
        "Geography unresolved for all (no station->coordinate source yet) — location_name kept."
    )
    written = upsert(facts, as_of)
    print(f"ingest[{JOB_NAME}]: upserted {written} timeline fact(s), source={SOURCE}")


if __name__ == "__main__":
    main()
