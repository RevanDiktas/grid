-- 0003_capacity_timeline.sql — DERIVED forward-looking timeline ("when does power arrive here").
-- Facts extracted from operator Investeringsplannen into OUR schema. We NEVER store the source
-- PDF or its table/figure/text layout — only normalised fields (see decisions D-licence).
-- Additive, forward-only, idempotent. Separate from raw capacity facts (capacity_observations).

CREATE TABLE IF NOT EXISTS capacity_timeline (
    id             bigserial PRIMARY KEY,
    -- Idempotency key: the operator's own project/knelpunt id when present, else a deterministic
    -- slug of location+bottleneck+date built in the ingestion job (never a guess).
    project_ref    text NOT NULL,
    operator       text NOT NULL,                         -- liander | tennet | enexis | stedin | ...
    -- Geography (best-effort; unresolved stays NULL with a logged reason — never guessed):
    location_name  text,                                  -- operator's station/area name (a fact)
    pc6            text REFERENCES areas (pc6),            -- when resolvable to a PC6
    substation_id  bigint REFERENCES substations (id),    -- when resolvable to a station
    geom           geometry(Point, 4326),                 -- when geocodable
    -- The forward-looking facts:
    bottleneck     text,                                  -- the knelpunt, normalised into our words
    direction      text,                                  -- 'offtake' | 'feedin' | 'both' when stated
    expected_date  date,                                  -- expected in-service date (IBN) when given
    expected_year  smallint,                              -- when only a year/horizon is published
    added_mw       double precision,                      -- expected added capacity, when stated
    confidence     double precision CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    source         text NOT NULL,                         -- '<operator> IP 2026'
    as_of          date NOT NULL,                         -- the plan's own date, not ingest time
    ingested_at    timestamptz NOT NULL DEFAULT now()
);

-- Idempotency: re-running an ingest upserts on (source, project_ref) rather than duplicating.
CREATE UNIQUE INDEX IF NOT EXISTS capacity_timeline_uix
    ON capacity_timeline (source, project_ref);
CREATE INDEX IF NOT EXISTS capacity_timeline_geom_gix
    ON capacity_timeline USING gist (geom);
