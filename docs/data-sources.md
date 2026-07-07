# GridScout data-source registry

**Single source of truth for where data comes from.** Nothing gets ingested unless it's registered here. Every ingested row references a `source` name from this table and carries an `as_of` date. Verify each source when you wire it up — endpoints, cadences, and licences change.

| Source (name) | Provides | Access | Format | Geo key | Cadence | Licence | Caveats |
|---|---|---|---|---|---|---|---|
| `capaciteitskaart` | Availability **category** (offtake + feed-in) per PC6 | `data.partnersinenergie.nl/capaciteitskaart/api/download/congestie_pc6.csv` (old netbeheernederland URL 301s here) | **CSV** | postcode-6 | irregular / on-demand | **Ambiguous — see below** | **Reference implementation.** Traffic-light class, *not* MW; no geometry; as_of is per-DSO; HTTP 500 observed |
| `cbs_postcode6` | PC6 **polygon geometry** (the `areas` layer) — geometry only, no capacity | PDOK WFS 2.0 `service.pdok.nl/cbs/postcode6/2024/wfs/v1_0` (keyless) | **WFS → GeoJSON** | postcode-6 | yearly vintage | **CC BY 4.0** (`© CBS / PDOK`) | Geometry backbone for the map; native CRS is **RD/28992** (reproject to 4326); 464,964 features; see below |
| `vivet` | ~~Substation-level capacity, 3/5/10-yr forward~~ | ~~Kadaster via PDOK~~ | — | — | — | — | ⛔ **RETIRED — see below.** Do **not** build. Timeline is re-sourced from DSO waitlists + Investeringsplannen |
| `liander` | Topology, stations, forecasts, capacity-per-region | liander.nl/over-ons/open-data; data.overheid.nl; PDOK/ArcGIS | Geo/CSV | station/region | varies | CC BY 4.0 (many sets) | Attribution required |
| `enexis` | Transportschaarste, waiting lists per station | enexis.nl open data; data.overheid.nl/.../enexis | CSV/map | station/region | monthly-ish | Open (verify) | Province waiting-list maps |
| `stedin` | Topology, capacity | data.overheid.nl/.../stedin | Geo/CSV | station/region | varies | Open (verify) | |
| `tennet` | 110/150 kV HV headroom | TenneT capaciteitskaart | viewer/data | HV node | varies | Open (verify) | HV layer |
| `entsoe` | EU transmission / load / congestion | web-api.tp.entsoe.eu/api (free token by email; `entsoe-py`) | XML | bidding zone | on demand | ENTSO-E terms | Max 1 yr/request; rate limits; needs `ENTSOE_API_TOKEN` |
| `gopacs` | Congestion & redispatch signals | gopacs.eu | web/data | area | frequent | verify | Feeds congestion-risk score |
| `capacitypedia` | Pan-EU capacity index (roadmap) | ENTSO-E / DSO Entity portal | links/index | country | periodic | Open | Directory of links — for EU expansion later |
| `partners-in-energie` | Request channel for non-open DSO data | partnersinenergie.nl | request | — | — | per request | Start requests early; doubles as DSO relationship |
| `enexis_waitlist` 🟡 | **PLANNED** — per-station queue depth + planned-expansion date + expected added MW | Enexis open data / ArcGIS (unverified) | TBD | station/region | TBD | verify | **PLANNED / unverified.** Timeline-feature input (see below). Do not build until a research gate confirms queryable fields |
| `liander_waitlist` 🟡 | **PLANNED** — per-station queue depth + expansion schedule | Liander open data / PDOK/ArcGIS (unverified) | TBD | station/region | TBD | CC BY 4.0 (verify) | **PLANNED / unverified.** Timeline-feature input |
| `investeringsplannen_2026` 🟡 | **PLANNED** — project-level reinforcement schedules (regional 10-yr / TenneT 15-yr) | DSO/TenneT Investeringsplannen 2026 (unverified) | TBD | project/region | 2-yearly | verify | **PLANNED / unverified.** Quantitative horizon (regional first 3 yrs / TenneT first 5 yrs); feeds timeline + delay-risk |

## Licence & report-safety (enforced in code)

**Authoritative copy lives in `provenance/sources.py`** (imported by ingestion + the report path);
this table mirrors it for humans. Operating rule: **use FACTS + our own words + a citation; never
reproduce a source's expression (tables/figures/maps/text/the document); attribution ≠ permission.**
`customer_report_safe=FALSE` data is blocked from the report path in code (`provenance.assert_report_safe`).

| Source | Licence | `customer_report_safe` | `reproduction_allowed` | Attribution (must render) | Usage note |
|---|---|---|---|---|---|
| `cbs_postcode6` | CC-BY-4.0 | ✅ yes | ✅ yes | `© CBS, © Esri Nederland` | Attribution mandatory on any map/report showing the polygons (licence condition). |
| `capaciteitskaart` | ambiguous-netbeheerder | ✅ yes | ❌ no | `Bron: Netbeheer Nederland, Capaciteitskaart elektriciteitsnet` | Indicative; always show confidence + as_of. Facts only, not the raw file. |
| `investeringsplannen_2026` | proprietary-netbeheerder (no open licence) | ✅ **facts only** | ❌ no | `Bron: <operator> Investeringsplan 2026` | Extract facts only. NEVER store/serve/mirror/reproduce the PDF or its tables/figures/maps/text. |
| `enexis_waitlist` | esri-platform-tou | ⛔ **no** | ❌ no | `Bron: Netbeheer Nederland / Esri Nederland` | LICENCE-BLOCKED for redistribution until cleared owner-direct via Partners in Energie. Prototype/read only. |
| _all other registered sources_ | unverified | ⛔ no (default) | ❌ no | — | Report-unsafe by default until each licence is individually assessed. |

## `cbs_postcode6` — verified details (2026-07-07)

Verified live against the service this session (GetFeature sampled). The PC6 **geometry backbone**
for the `areas` layer — carries geometry, **not** capacity.

- **Service:** PDOK WFS 2.0, base `https://service.pdok.nl/cbs/postcode6/2024/wfs/v1_0`. Keyless.
  FeatureType `postcode6:postcode6`; PC6 id field `postcode6` (e.g. `1011AB`); geometry field `geom`
  (MultiPolygon). ~100 extra CBS statistics columns are ignored — we keep only postcode + geometry.
- **CRS gotcha (important):** the default GeoJSON (`outputFormat=application/json`) is returned in
  **EPSG:28992 (RD New)** — coordinates are easting,northing **metres, not lon,lat**. We fetch native
  RD (unambiguous axis order) and reproject to 4326 in-DB via `ST_Transform`, dodging the WFS-2.0
  EPSG:4326 lat,lon axis-flip trap (which silently returns HTTP 200 + wrong/empty data). See pitfalls.
- **Volume & paging:** `numberMatched=464964` nationally; server page cap = 1000 → page with
  `startIndex` + `count=1000` (~465 requests). bbox filter uses `x1,y1,x2,y2,EPSG::28992`.
- **as_of:** the response carries **no Last-Modified** header, so as_of cannot come from HTTP. We use
  the dataset vintage in the URL path (2024) → `2024-01-01`, the reference date of an annual CBS
  product — a documented convention, logged explicitly, **not** an invented figure.
- **Licence:** **CC BY 4.0** (`<ows:Fees>none</ows:Fees>`, AccessConstraints = CC BY 4.0). Attribution
  string: `© CBS / PDOK, CC BY 4.0`.

## `vivet` — RETIRED (verified 2026-07-07)

- **The PDOK VIVET service ("Beschikbare capaciteit elektriciteitsnet", Kadaster) was taken out of
  production on 11 Jun 2025.** All its endpoints (`service.pdok.nl/kadaster/netcapaciteit/{wfs,wms,atom}`,
  the OAF `/collections`) return **HTTP 404**, verified live; PDOK itself is healthy. Confirmed by PDOK's
  own retirement notice (`pdok.nl/-/dataset-beschikbare-capaciteit-elektriciteitsnet-van-kadaster-uit-productie`).
- **A live successor exists off-PDOK** — Netbeheer Nederland's Capaciteitskaart as a public ArcGIS
  Feature Service (`services.arcgis.com/nSZVuSZjHpEZZbRo/.../Capaciteitskaart_elektriciteitsnet_v2_afname/FeatureServer/0`).
  But it is **voedingsgebied-polygon, categorical status codes (`afname`/`opwek`), NOT MW**, **has no
  3/5/10-yr forward horizons**, and its **licence is unconfirmed**. It is therefore **demoted to an
  optional geometry/status convenience — NOT the timeline source** (see `harness/decisions.md` D7).
- **The forward-looking timeline is re-sourced** from DSO waitlist maps (`enexis_waitlist`,
  `liander_waitlist`) + `investeringsplannen_2026`, plus a delay-risk adjustment in `assess()`.

## `capaciteitskaart` — verified details (2026-07-07)

Investigated with the data-source-researcher pattern. Key facts that differ from the original registry assumption:

- **URL moved & format changed.** `capaciteitskaart.netbeheernederland.nl` now 301-redirects to
  `https://data.partnersinenergie.nl/capaciteitskaart/`. The PC6 export is a **CSV** (`congestie_pc6.csv`
  under `.../api/download/`), not an Excel. Sibling exports: `voedingsgebieden.csv` (the only file with
  numeric MW-ish capacity, at supply-area level), `tennetgebieden.csv`, `tennetcongestie.csv`,
  `projecten.csv`, and `brondata_documentatie.txt` (the column dictionary).
- **Capacity is categorical, not MW.** PC6 rows carry a 4-level traffic-light per direction
  (afname/offtake, invoeding/feed-in): available (green) / limited (orange) / study (grey) /
  congested (red), plus "not yet coloured" (unknown); older docs describe an ordinal **0–3** code
  (increasing scarcity). We map these to the `availability_class` enum and **leave MW NULL**.
- **No geometry** in the file — PC6 polygons must be joined from an external set (PDOK/CBS) later.
- **as_of is per-DSO**, published at `.../capaciteitskaart/info/laatst-vernieuwd` (e.g. Stedin 2026-06-25,
  Enexis 2026-06-01, Liander 2026-05-01, TenneT 2026-07-01). There is no single file-level date; the job
  falls back to the CSV's HTTP `Last-Modified` and refuses to invent an `as_of`.
- **Licence is AMBIGUOUS.** No explicit open/CC statement found; only an "indicatief, u kunt hier geen
  rechten aan ontlenen, gebruik op eigen verantwoordelijkheid" disclaimer. Exports are published for reuse
  ("voor gebruik in uw GIS-systeem"), but **commercial redistribution rights are not spelled out** →
  confirm with `capaciteitskaart@netbeheernederland.nl` before redistributing. Internal ingestion/analysis
  is within the stated intent. Stored with **low confidence**.
- **Quirks:** delimiter likely `;` and decimal comma (NL) — the parser detects rather than assumes;
  exact headers/encoding UNVERIFIED because `/api/download/*.csv` returned **HTTP 500** during
  investigation *and* at first ingest attempt (2026-07-07). The job retries 5xx and, if still down,
  writes nothing rather than fabricating rows.

## Getting the ENTSO-E token

Register at the ENTSO-E Transparency Platform, then email them with "RESTful API access" in the subject and your registered address in the body; a token is issued and goes in `.env` as `ENTSOE_API_TOKEN` (never committed). The `entsoe-py` Python client wraps the API.

## Adding a source

Use the `onboard-data-source` skill. Research unfamiliar sources with the `data-source-researcher` subagent first. Register the row here **before** writing any ingestion job.
