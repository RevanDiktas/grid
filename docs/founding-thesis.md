# GridScout — Founding Thesis, Market & Competitor Analysis, and Build Plan

> **Working name:** "GridScout" is a placeholder — check trademark/domain availability before committing. Other candidates: Voltground, Capacita, PowerLine, GridSight.
>
> **Category:** European grid-capacity intelligence (the "where can I actually get power, and how fast?" layer)
>
> **One-line positioning:** *GridCARE for Europe* — the decision layer on top of Europe's newly-opened grid data.
>
> **Prepared:** July 2026. Figures are sourced at the end; energy markets move fast, so re-verify before fundraising.

---

## 1. The pitches

### Short pitch (50 words)

> GridScout is the intelligence layer for Europe's congested power grid. We turn fragmented, public grid data into one clear answer for anyone trying to connect a large electricity load or battery: where spare capacity exists, how fast you can get connected, and how to unlock more. Powered land, decided in minutes.

### Longer pitch — what it does, the problem, and why it's the next big thing

**The problem.** Europe's electricity grid has run out of room. In the Netherlands alone, over 14,000 businesses sit on waiting lists for a grid connection, and the national transmission operator's queue tops 38 GW. New connections in major hubs like Amsterdam now take up to a decade — capacity around the capital won't free up until roughly 2036. This is no longer a niche utility problem: it is the rate-limiting step for data centers, battery storage, factories, EV depots, and the entire electrification of the economy. The single most valuable question in energy infrastructure today is **"where can I actually get power, and how fast?"** — and today that question is answered by expensive consultants, months of back-and-forth with grid operators, and guesswork.

**What GridScout does.** GridScout ingests the messy, fragmented grid data that is now — thanks to new EU transparency rules — increasingly public: distribution-operator capacity maps, transmission data, congestion and redispatch feeds, queue and permit records. Our AI turns it into a single, queryable intelligence product. For any location or region, GridScout tells a developer the realistically available capacity, the likely connection timeline, the congestion outlook, and the smart options (flexible connections, energy hubs, storage) to unlock more. We start as a **data and feasibility-report product** anyone can use, then climb into **physics-based capacity modelling** that reveals hidden headroom the standard planning process misses — the deepest and most defensible layer.

**Why it's the next big thing.** Three forces are converging right now. (1) **Demand:** the EU intends to roughly triple data-center capacity by 2032, electricity demand is set to rise ~60% by 2030, and every one of those projects is now gated by grid access, not chips or capital. (2) **A proven model, an empty continent:** in the US, this exact category just produced GridCARE, which raised a $64M Series A in May 2026 on the strength of unlocking "hidden" grid capacity — but it is US-focused, and **Europe has essentially no equivalent**, despite worse congestion. (3) **Regulation is handing us the raw material:** the EU now *mandates* that grid operators publish hosting-capacity data, so the data moat is cheap to start building and compounds with every customer. Own the most accurate capacity map on the continent, become the neutral referee grid operators validate, and you own the decision layer for €584 billion of European grid build-out. That is a category-defining, potentially monopoly-grade position — and it can be started by one technical founder.

---

## 2. The problem in depth

### 2.1 The Netherlands: the epicentre

The Netherlands is the worst grid-congestion market in Europe and therefore the ideal beachhead:

- **Queues:** ~14,044 offtake requests (≈9 GW) sit on regional grid-operator waiting lists; the national operator TenneT's offtake queue holds 212 requests totalling ~38 GW. A further ~8,600 parties are queued to *feed in*.
- **Economic cost:** a government-cited study puts the social cost of congestion at **€10–40 billion**. Upgrading the national grid is estimated at **~€192 billion**, and physical grid build takes **8–12 years**.
- **It's getting worse, not better:** from 1 July 2026, the capacity that was reserved for small consumers (including housing) disappears in congested areas — everyone joins the same queue. Grid operators warn shortages in Amsterdam persist until at least 2030.
- **Policy is pushing toward software solutions:** the new Energy Law (*Energiewet*, in force 1 January 2026) enables collective/flexible connection arrangements; the government aims to procure an extra **€500 million/year** of flexibility in 2026–27; and grid operators run market mechanisms (GOPACS) and are piloting energy hubs. Flexibility is becoming mandatory practice — and flexibility needs intelligence.
- **~3,800 business parks**, nearly all in congestion zones.

**The pain, in one example:** Equinix received a permit for an 80 MW Amsterdam data center — but because the grid is over-congested, it is **building its own connection to TenneT's high-voltage grid**, and full capacity only becomes available after new substations are completed **around 2036**. That is the exact pain GridScout addresses: knowing, before you commit capital, where power actually is and when it arrives.

### 2.2 The EU: a €584bn+ structural build-out

- The EU estimates **€584 billion** of grid investment is needed by 2030 (a ~60% increase over prior rates). The December 2025 EU Grids Package puts the longer figure at roughly **€1.2 trillion for 2024–2040**.
- Electricity consumption is projected to grow **~60% by 2030**; wind + solar capacity is targeted to rise from ~400 GW (2022) to **≥1,000 GW by 2030**; ~40% of Europe's distribution grids are already **>40 years old**.
- **Data centers are the sharp edge of demand.** EMEA operational data-center capacity passed **11.4 GW at end-2025 (+19% YoY)**, with a development pipeline near **15 GW** — but capacity actually *under construction* has plateaued at ~2.5 GW because power and permitting, not demand, are the bottleneck. The EU wants to roughly **triple** data-center capacity (≈8 GW → ≈22 GW) by 2032; hyperscale build-out runs ~**$10M per MW**.
- Connection waits of **4–7 years** in the core "FLAP-D" hubs (Frankfurt, London, Amsterdam, Paris, Dublin) are pushing development into Tier-II markets (Berlin, Milan, Madrid, Warsaw, the Nordics, Iberia, Poland). Every one of those relocation decisions is a **"where's the power?" decision** — GridScout's core query.

---

## 3. The product

### 3.1 What it is

A B2B SaaS + data product that answers, for any European location or region: **available grid capacity, connection timeline, congestion risk, and options to unlock more.** Delivered as (a) an interactive capacity map/dashboard, (b) on-demand site **feasibility reports**, and (c) an **API/data feed** for developers, advisors, and investors.

### 3.2 The two-layer strategy (this is the whole game)

**Layer 1 — Grid-capacity data layer (build this first, solo).**
Aggregate and normalise public data into one clean, queryable map + report product. This is buildable by one technical founder because the raw data is increasingly public and the value is in the *synthesis*, not proprietary physics. This is what US players like LandGate/Latapult/Acres sell — and what nobody sells for Europe.

**Layer 2 — Physics / flexibility layer (climb into this as you grow, with power-systems depth).**
Model the grid to reveal *latent* capacity that standard planning misses, and quantify flexible-connection options (curtailable "emergency-lane" connections, storage, energy hubs). This is GridCARE's game and the deepest moat. You reach it after accumulating data, capital, and (likely) a power-systems co-founder or hire.

### 3.3 Core features (MVP → v2)

| Feature | Layer | Notes |
|---|---|---|
| Interactive capacity map (NL first) | 1 | Substation/region-level available capacity, colour-coded, queryable |
| Site feasibility report (on-demand) | 1 | The first thing customers will *pay* for; de-risks 7–8 figure decisions |
| Connection-timeline estimator | 1 | Combines queue data + reinforcement schedules + historical outcomes |
| Congestion & redispatch outlook | 1 | From GOPACS/market data; matters for BESS revenue siting |
| Flexible-connection / hub optimiser | 2 | "You can connect 2 yrs sooner if you accept X hours of curtailment" |
| Latent-capacity modelling | 2 | Physics-based; the defensible core; validated with DSOs |
| API / data licensing | 1→2 | High-margin; feeds developer, advisor, and investor workflows |

---

## 4. Market analysis

### 4.1 Sizing (directional)

This is a *new* category in Europe, so treat sizing as directional, built bottom-up:

- **TAM (broad):** the decision-support and software layer riding on €584bn–€1.2T of EU grid build-out and the tripling of EU data-center capacity. Realistically a multi-billion-euro software/data opportunity over a decade if you become the standard layer.
- **SAM (near-term, serviceable):** capacity-intelligence spend by large-load developers (data centers, BESS, industrial), site-selection advisors, and grid operators across NL + DE + the Nordics + UK. Anchor points: hyperscale ~$10M/MW means even small time-to-power improvements are worth millions per project; US comparable GridCARE claims **>$10bn of economic value created** for developers.
- **SOM (beachhead):** NL BESS + data-center + industrial developers and their advisors — a few hundred organisations you can reach founder-led, each willing to pay for reports/subscriptions that de-risk major capital decisions.

*Adjacent context:* the virtual-power-plant market alone is projected to grow from ~$6.1bn (2025) to ~$30.9bn (2033), ~22.6% CAGR — evidence of how fast capital is flowing into grid-flexibility software.

### 4.2 Customer segments (who pays, and why)

| Segment | Pain | Why they pay | Priority |
|---|---|---|---|
| **BESS / battery developers** | Must site where they can connect *and* earn congestion revenue | Fast-moving, software-native, booming NL pipeline | **Beachhead #1** |
| **Data-center / colo developers** | 4–7 yr waits; land-first model is dead | Each mis-sited project = millions lost | High (bigger deals, slower) |
| **Industrial / logistics firms** | Stuck on waiting lists; can't expand/electrify | Expansion is blocked without answers | Medium |
| **Site-selection advisors / brokers (JLL-type)** | Need power intelligence to advise clients | White-label your reports | Channel partner |
| **EV-charging / depot operators** | Need connection + flexibility siting | Growing, software-friendly | Medium |
| **DSOs / TSOs** | Lack visibility into their own congested areas; must publish capacity | The ultimate anchor + deepest moat | Later (slow, huge) |
| **Investors / lenders (infra funds)** | Need to de-risk connection assumptions in diligence | Data licensing / diligence reports | Later, high-margin |

**Why BESS developers first:** the Dutch battery pipeline is booming (TenneT is signing "congestion-mitigator" battery deals; the regulator created a queue-jumping framework for storage). They urgently need to know *where to site to connect and earn* — and they move in months, not years. They are the ideal first ten logos and the fastest route to a data flywheel.

---

## 5. Competitive landscape (deep)

The market splits into **three tiers**. The key insight: the developer-facing intelligence tier is well-populated in the US and **essentially empty in Europe**, while EU regulation is simultaneously forcing the underlying data open.

### Tier A — Developer-facing capacity intelligence (the category you're entering)

| Company | HQ / focus | What they do | Funding / status | Relevance |
|---|---|---|---|---|
| **GridCARE** | US (Stanford spinout) | Physics-based AI to unlock latent grid capacity; compresses interconnection from years to months; sells to hyperscalers & utilities | **$64M Series A (May 2026)**, $14M seed (2025); >2 GW pipeline; claims >$10bn value created | The model to emulate. **US-focused → Europe is open.** Your eventual Layer-2 competitor if they cross the Atlantic. |
| **LandGate** | US | Proprietary substation *offtake-capacity* data + powered-land due-diligence reports | Established data business | US substation modelling only; non-US is just a data-center *directory*, not capacity analysis. **No EU capacity product.** |
| **Latapult / Acres AI** | US | GIS/parcel "powered land" platforms; overlay transmission, substations, capacity for siting | Growth-stage | US-centric; GIS-overlay depth, not grid physics. |
| **Enverus** | US | Broad energy-data SaaS incl. data-center siting/grid analysis | Large incumbent | US-centric; could expand but hasn't owned EU capacity intelligence. |

**Takeaway:** the entire Tier-A category is US-shaped. In Europe — and acutely in NL — the developer-facing "where's the power" intelligence product does not meaningfully exist. That is the opening.

### Tier B — Grid-side / DSO software (adjacent; potential partners or data sources, not head-to-head)

| Company | Focus | Relevance |
|---|---|---|
| **envelio** (Germany) | Intelligent Grid Platform; grid-connection navigator & hosting-capacity tools sold **to DSOs** | Closest European name, but customer is the grid operator, not the developer. Different wedge; possible partner/competitor if they go developer-facing. |
| **DIgSILENT** (PowerFactory ICA) | Hosting-capacity calculation engine for planning engineers | Incumbent modelling software, DSO-side. Possible Layer-2 tech reference. |
| **Smarter Grid Solutions** (Strata Grid) | Grid capacity management / DERMS control for DSOs | DSO-side operational control, not developer decision support. |
| **Alliander (open-source)** | Dutch DSO building open capacity-management software in-house | Signals DSOs are digitising; source of open components + a relationship target. |

### Tier C — Public / regulatory aggregators (they *help* you: free raw data, shallow product)

| Source | What it is | Why it helps rather than threatens |
|---|---|---|
| **Capacitypedia** (ENTSO-E + EU DSO Entity, launched May 2026) | Pan-EU portal linking to national hosting-capacity pages | It's a **directory of links**, not analytics — it validates demand and centralises where to find raw data, but leaves the decision/intelligence layer wide open. |
| **National capacity maps** (NL *capaciteitskaart*; DSO maps) | Public colour-coded maps of where capacity exists | Free raw input to your data pipeline. Static, siloed, no timeline/decision logic. |
| **GOPACS** | Dutch grid operators' congestion/redispatch market & data | Free congestion-signal data for your BESS-siting features. |
| **EU regulatory mandate** | Electricity Market Regulation (arts. 50 & 57) + Grid Action Plan Action 6 now **require** hosting-capacity publication | The single biggest tailwind: it forces your raw material into the open, continent-wide. |

### Tier D — Energy-analytics incumbents (watch as future competitors/acquirers)

- **Aurora Energy Research** (EOS platform) — serious European energy-market analytics/software. Not in this exact niche today, but the most plausible incumbent to move in — or to acquire you.
- **Wood Mackenzie / BloombergNEF / others** — market intelligence, not location-level connection feasibility.
- **Tibo Energy** (NL, ~$7M seed 2025) — AI energy management for high-use facilities; **adjacent** (behind-the-meter optimisation), not capacity siting — but a Dutch team to watch.
- **VPP / flexibility players** (GridBeyond, Sympower, Entrix, Next Kraftwerke) — they *use* congestion data to trade flexibility; they are not selling capacity intelligence. Potential customers/partners, not direct rivals.

### 5.1 Positioning statement

> The US has powered-land intelligence (GridCARE, LandGate); Europe has free-but-shallow public maps (Capacitypedia) and DSO-side tools (envelio). **Nobody owns the developer-facing capacity-decision layer for Europe.** GridScout is that layer — starting in the Netherlands, where congestion is worst and public data is best.

---

## 6. Why now (timing)

1. **Demand shock:** AI/data-center + electrification demand has made grid access *the* bottleneck across Europe (2025–2026 inflection).
2. **Proven category, empty geography:** GridCARE's $64M Series A validated the model in the US in May 2026; Europe is uncontested.
3. **Regulation opens the data:** mandatory hosting-capacity transparency (Grid Action Plan Action 6, Electricity Market Regulation) + Capacitypedia (May 2026) cut your data-acquisition cost dramatically.
4. **NL policy tailwind:** Energiewet (Jan 2026), flexible/collective connections, energy hubs, €500M/yr flexibility procurement — all create demand for intelligence.
5. **Capital is hunting this thesis:** energy × AI is the hottest venture theme; €584bn–€1.2T of grid build-out is the backdrop.

---

## 7. Business model & pricing

- **Feasibility reports (transactional):** per-report fee for a site/region assessment. Fastest first revenue; low cost to produce once the pipeline exists; high perceived value against 7–8-figure decisions.
- **SaaS subscription:** seat-based access to the map, timeline estimator, and congestion outlook. Tiers for developers, advisors, DSOs.
- **API / data licensing:** high-margin feeds into developer, advisor, lender, and PropTech workflows. The most defensible recurring line at scale.
- **Enterprise / DSO contracts (later):** large annual deals with grid operators and infra funds; the anchor revenue + moat.

Gross margins are strong (data/software), with modest data-engineering and validation costs early. Note that unlike flexibility *aggregators* (who earn a trading margin), this is cleaner recurring software/data ARR.

---

## 8. The moat — path to a European monopoly

Monopoly here means **owning the most accurate capacity map + becoming the neutral referee** — a winner-take-most data business. Four compounding moats:

1. **Data flywheel:** every feasibility study, every DSO conversation, and — crucially — every *actual connection outcome you observe* makes your predictions more accurate than anyone else's. Accuracy compounds with usage; buyers standardise on the most accurate map.
2. **Utility validation & relationships:** GridCARE's key trust move is validating its model *with* utilities. Replicate this and you become the neutral standard — very hard to dislodge.
3. **Workflow lock-in:** once GridScout reports are the standard input to project financing and diligence, switching costs are high.
4. **Two-layer ascent:** start as the data layer (low moat individually, but a real product), then climb into physics/flexibility modelling (deep moat) using the data and relationships you accumulated.

---

## 9. Fundability

- **Narrative:** *"GridCARE for Europe — attacking the AI-era power bottleneck on the continent that's furthest behind."* Currently one of the most fundable stories in venture.
- **Investors to target (verify current fit before pitching):** European climate/energy VCs (e.g., World Fund, Extantia, Contrarian Ventures, Future Energy Ventures, Klima/Alantra), deep-tech/AI generalists with energy interest, and strategic/CVC (utility, grid-equipment, data-center players). GridCARE's backers (Sutter Hill, a16z, Temasek/Xora, National Grid Ventures) show the archetype.
- **Non-dilutive money (solo-founder cheat code):** NL/EU grants — EIC Accelerator, Invest-NL, WBSO (R&D tax), InvestAI-adjacent and Climate-Fund-linked programmes. Funds the build without dilution *and* validates you.
- **What a raise looks like:** pre-seed/seed on (wedge product + design partner + early data). The single biggest lever is **one name-brand pilot** (a serious developer or, ideally, a DSO) — it converts "solo generalist with a thesis" into "founder with traction in a hot category."
- **Solo-founder honesty:** deep-energy solo raises are harder; investors will want to see either a power-systems co-founder/advisor lined up for Layer 2, or clear traction that de-risks it. Land the pilot first; raise second.

---

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| **Data access / quality** varies by country | Start in NL (best public data); convert DSO relationships into private/validated feeds; build country-by-country. |
| **DSOs slow / gatekeeping** | Their slowness is also your moat once you're embedded; approach them as validation partners, not just customers. |
| **GridCARE / Enverus enter Europe** | Head start + local regulatory/data depth they'd have to rebuild; lock in NL + a DSO relationship early. |
| **Capacitypedia / free public maps** "good enough" | They're link-directories/static maps; your value is synthesis, timelines, congestion outlook, and decision logic they don't provide. |
| **Regulatory change** | Mostly a tailwind — every new flexible-connection rule is complexity someone must model (i.e., more demand for you). |
| **Solo bandwidth** on Layer 2 physics | Sequence it: ship Layer 1 solo; add power-systems depth (co-founder/hire) after funding. |
| **Long enterprise sales (DSO/hyperscaler)** | Lead with fast-moving BESS/industrial developers + transactional reports for early revenue. |

---

## 11. Step-by-step build guide

A pragmatic sequence for **one technical founder**, optimised for your priorities (highest ceiling, solo-buildable, fundable).

### Phase 0 — Validate & focus (Weeks 0–4)

1. **Pick the beachhead:** NL, BESS + industrial developers as first customers.
2. **Customer discovery:** talk to 15–20 target users (BESS developers, DC site-selectors, advisors). Confirm the sharpest pain and what they'd pay for a report. Don't build yet.
3. **Map the data:** inventory available sources (see Phase 1) and their formats/gaps.
4. **Define the wedge deliverable:** a single, sellable **site feasibility report** template (capacity + timeline + congestion + options).

### Phase 1 — MVP data pipeline + capacity map (Weeks 2–8)

**Data sources (NL first):**
- DSO capacity maps: Liander, Enexis, Stedin (the *capaciteitskaart*), plus RVO's congestion portal.
- TenneT / ENTSO-E transparency data (transmission).
- GOPACS congestion & redispatch data (congestion signals).
- Queue/waiting-list data and municipal permit records where available.
- Capacitypedia as a cross-EU index for expansion later.

**Tech stack (suggested, lean):**
- Ingestion/ETL: Python (pandas, GeoPandas), scheduled jobs; store in PostgreSQL + **PostGIS** (geospatial is core).
- Geospatial/mapping: PostGIS + a vector tile layer (e.g., MapLibre/Mapbox) for the interactive map.
- AI/synthesis: LLM-based extraction/normalisation of messy PDFs/pages + a scoring/estimation model for timelines and available-capacity confidence. Keep a human-in-the-loop review early.
- App: a simple web app (Next.js/React) + an internal report generator (templated PDF/HTML).
- Infra: a single cloud project; cheap to run solo.

**Deliverable:** an internal tool that, for a given NL location/region, outputs available capacity, a connection-timeline estimate, and congestion context — and generates a clean feasibility report.

### Phase 2 — First paying customers (Weeks 6–14)

1. **Produce 3 real feasibility reports** for 3 real candidate sites (use them as demos).
2. **Founder-led sales:** take them to ~10 BESS/industrial developers for feedback + to sell.
3. **Convert 1 paid pilot or LOI.** Price on value (de-risking a large decision), not cost.
4. **Instrument feedback → product:** tighten the report to what buyers actually act on.

### Phase 3 — Data flywheel + first DSO relationship (Months 3–6)

1. **Track outcomes:** log actual connection results vs. your predictions — this is the flywheel seed.
2. **Open one DSO conversation** (e.g., Alliander/Liander given their open-source posture) as a validation partner — the moat seed.
3. **Launch the subscription tier + API** so early customers become recurring.
4. **Start a grant application** (EIC/Invest-NL/WBSO) in parallel.

### Phase 4 — Raise, expand geography, begin Layer 2 (Months 6–12+)

1. **Pre-seed/seed raise** on the package: working product + paying customer(s) + DSO relationship + grant in flight.
2. **Add power-systems depth** (co-founder or senior hire) to start **Layer 2** (latent-capacity/physics + flexible-connection modelling).
3. **Expand data coverage** to a second market (Germany or the Nordics), using Capacitypedia + national feeds.
4. **Deepen the referee moat:** formalise DSO validation; make GridScout reports a standard diligence input for lenders/infra funds.

### 90-day scorecard (what "on track" looks like)

- ✅ Working NL capacity-map + feasibility-report tool
- ✅ 1 paying customer or signed LOI
- ✅ 1 DSO relationship started
- ✅ 1 grant application in flight
- ➡️ = a pre-seed round that's easy to raise

---

## 12. First 10 customers to call (profile, not names)

1–4. **NL BESS / battery-storage developers** actively siting projects (they need connect-and-earn intelligence, fast).
5–6. **Data-center / colocation developers** expanding into NL/German Tier-II markets.
7. **A site-selection advisory / commercial-real-estate firm** (white-label channel).
8. **An industrial or logistics group** stuck on a waiting list wanting to expand/electrify.
9. **An EV-charging depot operator** planning multi-site rollouts.
10. **One DSO** (validation partner + future anchor customer).

---

## 13. Key figures & sources

**Netherlands**
- 14,044 regional offtake requests (~9 GW); TenneT 212 requests (~38 GW); ~8,600 feed-in queue — Stibbe; KVK; Switchgear Magazine (2026).
- Congestion social cost €10–40bn; grid upgrade ~€192bn; build time 8–12 yrs — Stibbe; DutchBrief (2026).
- Reserved small-user capacity ends 1 July 2026; Energiewet in force 1 Jan 2026; +€500M/yr flexibility procurement — Stibbe; Law & More (2026).
- Amsterdam ~852 MW operational DC capacity; 182 MW under construction + 250 MW planned — Cushman & Wakefield (Apr 2026).
- Equinix 80 MW site building own TenneT connection; capacity ~2036; Liander shortages to 2030 — NL Times; DutchBrief (2026).
- ~3,800 business parks in congestion zones — withthegrid / TNO.

**EU**
- €584bn grid investment need by 2030; EU Grids Package ~€1.2T (2024–2040) — Eurelectric; European Parliament; GLOBSEC (2025).
- Electricity demand +60% by 2030; wind+solar 400→1,000 GW; 40% of distribution grids >40 yrs — Synertics; EU Action Plan for Grids.
- EMEA DC capacity >11.4 GW end-2025 (+19% YoY); pipeline ~15 GW; under construction ~2.5 GW — Cushman & Wakefield (Apr 2026).
- EU tripling DC capacity to ~22 GW by 2032; ~$10M/MW hyperscale; InvestAI up to €200bn — Rabobank; JLL (2026).
- Mandatory hosting-capacity transparency (Electricity Market Regulation arts 50/57; Grid Action Plan Action 6); Capacitypedia launched May 2026 — ENTSO-E; Ember.

**Competitors**
- GridCARE: $64M Series A (May 2026), $14M seed (2025), Stanford team, >2 GW pipeline, >$10bn value claimed — BusinessWire; Latitude Media; DCD.
- LandGate, Latapult, Acres AI, Enverus — company sites (US powered-land / capacity data).
- envelio, DIgSILENT, Smarter Grid Solutions, Alliander open-source — company/DSO sources (grid-side).
- Aurora Energy Research (EOS); Tibo Energy ($7M seed 2025, NL) — company/Global Venturing.
- VPP market $6.1bn (2025) → $30.9bn (2033), 22.6% CAGR — NatureTech Memos (2026).

> ⚠️ These figures were gathered in mid-2026 from secondary sources and market-research summaries; verify primary sources (and re-check competitor funding/status) before using in a fundraise or board deck.

---

*End of document.*
