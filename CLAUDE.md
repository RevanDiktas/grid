# CLAUDE.md — GridScout

Project constitution. Claude Code loads this every session. Kept lean on purpose — depth lives in `.claude/skills/`. If you're about to add a multi-step procedure here, make it a skill instead.

## North star (read first)

GridScout is the **intelligence layer on top of Netherlands (later EU) grid-capacity data**. For someone siting a large electricity load or battery, we answer: *where can I connect, how much power, how fast, and how to unlock more.* Solo founder — you are the whole team, so act like a senior engineer who owns the outcome, not a code-typist.

**Scope discipline (non-negotiable):** ship the narrow NL wedge first — a capacity map + an on-demand **feasibility report** for **BESS / large-load developers**. Everything broader (more countries, the physics/"hidden capacity" layer, DSO contracts) comes later.

**Decision test for any change:** *does this get a Dutch BESS/large-load developer to a trustworthy connect / where / how-much / when answer faster than they can get today?* If no → defer it and say so.

Full context lives in `docs/`: `docs/founding-thesis.md` (product + market + competition) and `docs/build-plan.md` (the 0→10 build sequence). Read them before large decisions. The data-source registry `docs/data-sources.md` is the **single source of truth** for where data comes from — never invent a source or field that isn't in it.

## Tech stack

- **Python 3.12** — ingestion/ETL + scoring logic. Package/deps via **uv**.
- **PostgreSQL + PostGIS** — geospatial database. Everything is "what's true at/near this point."
- **FastAPI** — the `assess(location)` API.
- **Next.js + React + MapLibre GL** — web app + map. JS deps via **pnpm**.
- **WeasyPrint** (HTML→PDF) — feasibility reports.

## Repo layout

- `ingestion/` — one idempotent ETL job per data source
- `db/` — schema + `db/migrations/` + seed data
- `api/` — FastAPI service exposing `assess()`
- `web/` — Next.js app (search, map, report button, auth)
- `reports/` — feasibility report templates + generator
- `docs/` — thesis, build plan, `data-sources.md` registry
- `.claude/` — skills, rules, hooks, agents (your leverage)

## Commands

- `make setup` — venv (uv), install deps, bring up Postgres+PostGIS, run migrations
- `make ingest SOURCE=<name>` — run one ingestion job
- `make migrate` — apply DB migrations
- `make serve` — run api + web locally
- `make report LOCATION="<address|postcode>"` — generate a feasibility report
- `make test` — run tests
- `make check` — lint + typecheck. **Run before every commit.**

## Always

- Run `make check` and relevant tests before committing; fix failures before moving on.
- Every data row carries a `source` and an `as_of` date. **Provenance is the moat — no exceptions.**
- Keep **raw ingested facts** separate from **derived intelligence** (`assess()` output). Never overwrite raw data.
- Use **plan mode** for anything non-trivial; show the plan and wait for approval before editing.
- Small, reviewable commits. Conventional-commit messages (`feat:`, `fix:`, `data:`, `chore:`).
- Prefer editing existing files over adding new ones; keep the tree tidy.

## Ask the human before

- Any schema-breaking migration or destructive data operation.
- Adding a paid dependency or a new external data source not in `docs/data-sources.md`.
- Anything touching secrets, auth, or (future) billing.
- Spending a long autonomous loop (>~15 tool calls) — checkpoint with a plan first.

## Never

- Never commit secrets/tokens/`.env` (a PreToolUse hook backstops this — don't rely on it alone).
- Never present indicative capacity as a guarantee. Always attach **confidence + as_of + source**.
- Never scrape a source whose terms forbid it — check the license column in `docs/data-sources.md` first.
- Never invent data-source URLs, API fields, or capacity numbers. If unsure, use the `data-source-researcher` subagent or ask.

## Skills (auto-load on demand — `.claude/skills/`)

- **onboard-data-source** — add a new grid data source end to end (research → register → ingest → verify)
- **build-ingestion-job** — the standard idempotent ETL job pattern
- **assess-scoring** — turn raw capacity data into the decision-grade verdict
- **feasibility-report** — generate the sellable report
- **verify-against-reality** — accuracy checks + the prediction→outcome flywheel
- **postgis-geospatial** — geospatial modelling conventions

## Subagent (`.claude/agents/`)

- **data-source-researcher** — investigate an unknown grid data source in an isolated context and return a clean spec (keeps research noise out of the main session).

## Dependencies & setup

- Python: `entsoe-py` (ENTSO-E Transparency API client), `pandas`, `geopandas`, `shapely`, `sqlalchemy`, `psycopg[binary]`, `httpx`, `pydantic`, `weasyprint`.
- Secret: `ENTSOE_API_TOKEN` in `.env` (free token — email ENTSO-E; see `docs/data-sources.md`). Never commit `.env`.
- First run: `make setup`. Confirm Postgres+PostGIS is up and `make migrate` succeeds before ingesting.

## Working style for this project

Research → plan → execute → verify → commit. When a task would flood context (reading many files, exploring a new data source), spawn the subagent and get a summary back instead of doing it inline. When you learn something durable (a source's quirk, a build gotcha), tell me so we can add it here or to a skill. You are building a company's foundation solo — bias toward correctness, provenance, and things that compound.
