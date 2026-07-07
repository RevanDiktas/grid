# GridScout

**The intelligence layer on top of the Netherlands' (and later the EU's) grid-capacity data.**

For anyone trying to plug a large electricity load or battery into a congested grid, GridScout answers the single most expensive question in energy infrastructure today: *where can I connect, how much power, how fast, and how do I unlock more?*

## Why this exists

The Dutch grid is full — 14,000+ businesses are on connection waiting lists and parts of Amsterdam won't free up until ~2036. Today, developers answer "can I connect here?" with expensive consultants and months of back-and-forth, ending up with an *indicative* map they're told not to rely on. GridScout turns the newly-opened public grid data into a fast, trustworthy, decision-grade answer.

## Status

Pre-MVP, solo-built. Beachhead: NL, selling to battery (BESS) and large-load developers, starting with an on-demand **site feasibility report**.

## Architecture (short version)

Public grid data → `ingestion/` (one ETL job per source) → PostGIS (`db/`) → `assess(location)` scoring (`api/`) → map + report (`web/`, `reports/`).

## Getting started

```bash
make setup     # venv, deps, Postgres+PostGIS, migrations
make ingest SOURCE=capaciteitskaart
make serve     # api + web
make report LOCATION="1101 Amsterdam"
```

## Working with Claude Code

This repo is configured for Claude Code. `CLAUDE.md` is the project constitution (loaded every session); deep playbooks live in `.claude/skills/`. See `docs/build-plan.md` for the 0→10 build sequence and `docs/founding-thesis.md` for product/market context.

## Data & trust

Every data point carries a source and an as-of date. Capacity figures are indicative and are always presented with a confidence score — never as a guarantee. See `docs/data-sources.md`.
