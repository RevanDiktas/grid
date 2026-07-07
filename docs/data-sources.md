# GridScout data-source registry

**Single source of truth for where data comes from.** Nothing gets ingested unless it's registered here. Every ingested row references a `source` name from this table and carries an `as_of` date. Verify each source when you wire it up — endpoints, cadences, and licences change.

| Source (name) | Provides | Access | Format | Geo key | Cadence | Licence | Caveats |
|---|---|---|---|---|---|---|---|
| `capaciteitskaart` | Available capacity (offtake + feed-in) | capaciteitskaart.netbeheernederland.nl + downloadable **Excel at postcode-6** | Excel/viewer | postcode-6 | ~1st Friday monthly | Open (verify) | Indicative only; **reference implementation — start here** |
| `vivet` | Substation-level capacity, **3/5/10-yr forward** | Kadaster via **PDOK** (pdok.nl) | Geo (WFS/WMS) | substation | quarterly | Open gov | Powers timeline estimates |
| `liander` | Topology, stations, forecasts, capacity-per-region | liander.nl/over-ons/open-data; data.overheid.nl; PDOK/ArcGIS | Geo/CSV | station/region | varies | CC BY 4.0 (many sets) | Attribution required |
| `enexis` | Transportschaarste, waiting lists per station | enexis.nl open data; data.overheid.nl/.../enexis | CSV/map | station/region | monthly-ish | Open (verify) | Province waiting-list maps |
| `stedin` | Topology, capacity | data.overheid.nl/.../stedin | Geo/CSV | station/region | varies | Open (verify) | |
| `tennet` | 110/150 kV HV headroom | TenneT capaciteitskaart | viewer/data | HV node | varies | Open (verify) | HV layer |
| `entsoe` | EU transmission / load / congestion | web-api.tp.entsoe.eu/api (free token by email; `entsoe-py`) | XML | bidding zone | on demand | ENTSO-E terms | Max 1 yr/request; rate limits; needs `ENTSOE_API_TOKEN` |
| `gopacs` | Congestion & redispatch signals | gopacs.eu | web/data | area | frequent | verify | Feeds congestion-risk score |
| `capacitypedia` | Pan-EU capacity index (roadmap) | ENTSO-E / DSO Entity portal | links/index | country | periodic | Open | Directory of links — for EU expansion later |
| `partners-in-energie` | Request channel for non-open DSO data | partnersinenergie.nl | request | — | — | per request | Start requests early; doubles as DSO relationship |

## Getting the ENTSO-E token

Register at the ENTSO-E Transparency Platform, then email them with "RESTful API access" in the subject and your registered address in the body; a token is issued and goes in `.env` as `ENTSOE_API_TOKEN` (never committed). The `entsoe-py` Python client wraps the API.

## Adding a source

Use the `onboard-data-source` skill. Research unfamiliar sources with the `data-source-researcher` subagent first. Register the row here **before** writing any ingestion job.
