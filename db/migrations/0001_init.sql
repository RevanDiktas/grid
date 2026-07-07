-- 0001_init.sql — GridScout initial PostGIS schema.
-- Conventions (postgis-geospatial skill): SRID 4326 everywhere, GiST on all geometry,
-- provenance (source, as_of) mandatory on every fact table, raw tables immutable.
-- Forward-only. Never drops data.

CREATE EXTENSION IF NOT EXISTS postgis;

-- Canonical availability class. The capaciteitskaart PC6 source is a traffic-light, not MW:
-- these are the four legend classes plus 'unknown' ("kleur wordt later toegevoegd").
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'availability_class') THEN
        CREATE TYPE availability_class AS ENUM (
            'available',   -- green:  transportcapaciteit beschikbaar zonder wachtrij
            'limited',     -- orange: beperkt beschikbaar zonder wachtrij
            'study',       -- grey:   gebied in onderzoek met wachtrij
            'congested',   -- red:    tekort aan transportcapaciteit met wachtrij
            'unknown'      -- not yet coloured
        );
    END IF;
END$$;

-- ---------------------------------------------------------------------------
-- Geography reference tables
-- ---------------------------------------------------------------------------

-- Areas: postcode-6 zones and (later) DSO service regions. geom is nullable until we
-- join an external PC6 polygon set (the capaciteitskaart export has no geometry).
CREATE TABLE IF NOT EXISTS areas (
    pc6         text PRIMARY KEY,                      -- '1012AB' (6-char NL postcode), uppercased, no space
    geom        geometry(MultiPolygon, 4326),         -- nullable until sourced
    dso         text,                                  -- liander | enexis | stedin | ...
    source      text NOT NULL,                         -- registry name in docs/data-sources.md
    as_of       date NOT NULL,                         -- the data's own date, not ingest time
    ingested_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS areas_geom_gix ON areas USING gist (geom);

CREATE TABLE IF NOT EXISTS substations (
    id          bigserial PRIMARY KEY,
    code        text UNIQUE,                           -- operator's station id, when known
    name        text,
    operator    text,
    voltage_kv  numeric,
    geom        geometry(Point, 4326) NOT NULL,
    source      text NOT NULL,
    as_of       date NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS substations_geom_gix ON substations USING gist (geom);

-- ---------------------------------------------------------------------------
-- Raw fact tables (IMMUTABLE — assess() writes to separate derived tables later)
-- ---------------------------------------------------------------------------

-- One row = capacity at one geography, one as_of, one forward horizon.
-- offtake_mw/feedin_mw hold true MW where a source provides it; offtake_status/feedin_status
-- hold the categorical class where a source is a traffic-light (e.g. capaciteitskaart PC6).
-- `raw` keeps the original source record for reprocessing/audit.
CREATE TABLE IF NOT EXISTS capacity_observations (
    id                   bigserial PRIMARY KEY,
    pc6                  text REFERENCES areas (pc6),
    substation_id        bigint REFERENCES substations (id),
    as_of                date NOT NULL,
    forward_year_horizon smallint NOT NULL DEFAULT 0,  -- 0 = now; 3/5/10 = VIVET forward views
    offtake_mw           double precision,
    feedin_mw            double precision,
    offtake_status       availability_class,
    feedin_status        availability_class,
    confidence           double precision CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    source               text NOT NULL,
    raw                  jsonb,
    ingested_at          timestamptz NOT NULL DEFAULT now(),
    -- every observation must be anchored to some geography level
    CONSTRAINT capacity_obs_has_geography CHECK (pc6 IS NOT NULL OR substation_id IS NOT NULL)
);
-- Idempotency: re-running an ingest upserts on the natural key rather than duplicating.
CREATE UNIQUE INDEX IF NOT EXISTS capacity_obs_pc6_uix
    ON capacity_observations (pc6, source, as_of, forward_year_horizon)
    WHERE pc6 IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS capacity_obs_substation_uix
    ON capacity_observations (substation_id, source, as_of, forward_year_horizon)
    WHERE substation_id IS NOT NULL;

-- Waiting-list pressure per station (Enexis/Liander sources — stub for now).
CREATE TABLE IF NOT EXISTS waiting_lists (
    id            bigserial PRIMARY KEY,
    substation_id bigint REFERENCES substations (id),
    pc6           text REFERENCES areas (pc6),
    request_count integer,
    requested_mw  double precision,
    as_of         date NOT NULL,
    source        text NOT NULL,
    ingested_at   timestamptz NOT NULL DEFAULT now()
);

-- Congestion / redispatch signals (GOPACS source — stub for now).
CREATE TABLE IF NOT EXISTS congestion_events (
    id            bigserial PRIMARY KEY,
    geom          geometry(Geometry, 4326),
    substation_id bigint REFERENCES substations (id),
    event_ts      timestamptz,
    signal        text,
    as_of         date NOT NULL,
    source        text NOT NULL,
    ingested_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS congestion_events_geom_gix ON congestion_events USING gist (geom);
