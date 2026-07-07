# GridScout data-source registry

**Single source of truth for where data comes from.** Nothing gets ingested unless it's registered here. Every ingested row references a `source` name from this table and carries an `as_of` date. Verify each source when you wire it up — endpoints, cadences, and licences change.

| Source (name) | Provides | Access | Format | Geo key | Cadence | Licence | Caveats |
|---|---|---|---|---|---|---|---|
| `capaciteitskaart` | Availability **category** (offtake + feed-in) per PC6 | `data.partnersinenergie.nl/capaciteitskaart/api/download/congestie_pc6.csv` (old netbeheernederland URL 301s here) | **CSV** | postcode-6 | irregular / on-demand | **Ambiguous — see below** | **Reference implementation.** Traffic-light class, *not* MW; no geometry; as_of is per-DSO; HTTP 500 observed |
| `vivet` | Substation-level capacity, **3/5/10-yr forward** | Kadaster via **PDOK** (pdok.nl) | Geo (WFS/WMS) | substation | quarterly | Open gov | Powers timeline estimates |
| `liander` | Topology, stations, forecasts, capacity-per-region | liander.nl/over-ons/open-data; data.overheid.nl; PDOK/ArcGIS | Geo/CSV | station/region | varies | CC BY 4.0 (many sets) | Attribution required |
| `enexis` | Transportschaarste, waiting lists per station | enexis.nl open data; data.overheid.nl/.../enexis | CSV/map | station/region | monthly-ish | Open (verify) | Province waiting-list maps |
| `stedin` | Topology, capacity | data.overheid.nl/.../stedin | Geo/CSV | station/region | varies | Open (verify) | |
| `tennet` | 110/150 kV HV headroom | TenneT capaciteitskaart | viewer/data | HV node | varies | Open (verify) | HV layer |
| `entsoe` | EU transmission / load / congestion | web-api.tp.entsoe.eu/api (free token by email; `entsoe-py`) | XML | bidding zone | on demand | ENTSO-E terms | Max 1 yr/request; rate limits; needs `ENTSOE_API_TOKEN` |
| `gopacs` | Congestion & redispatch signals | gopacs.eu | web/data | area | frequent | verify | Feeds congestion-risk score |
| `capacitypedia` | Pan-EU capacity index (roadmap) | ENTSO-E / DSO Entity portal | links/index | country | periodic | Open | Directory of links — for EU expansion later |
| `partners-in-energie` | Request channel for non-open DSO data | partnersinenergie.nl | request | — | — | per request | Start requests early; doubles as DSO relationship |

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
