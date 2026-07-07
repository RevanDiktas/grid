-- 0002_seed_reference_locations.sql — verification anchors, NOT capacity facts.
-- Two real, well-known Dutch locations used to eyeball spatial correctness and to
-- spot-check ingested capacity against the public capaciteitskaart. Coordinates are
-- public geography; we deliberately assert NO capacity numbers here (that must come
-- from a registered source and be verified). Forward-only, idempotent.

CREATE TABLE IF NOT EXISTS reference_locations (
    key         text PRIMARY KEY,
    name        text NOT NULL,
    pc6         text,
    city        text,
    dso         text,
    expectation text,                       -- qualitative, to VERIFY against the live source
    geom        geometry(Point, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS reference_locations_geom_gix ON reference_locations USING gist (geom);

INSERT INTO reference_locations (key, name, pc6, city, dso, expectation, geom) VALUES
    ('amsterdam-congested', 'Amsterdam centrum (Dam)', '1012NP', 'Amsterdam', 'liander',
     'Amsterdam is a known congestion zone; expect offtake to read limited/congested. VERIFY against capaciteitskaart.',
     ST_SetSRID(ST_MakePoint(4.8926, 52.3731), 4326)),
    ('groningen-open', 'Groningen centrum (Grote Markt)', '9711LV', 'Groningen', 'enexis',
     'Groningen area expected to have more headroom; VERIFY offtake/feed-in against capaciteitskaart.',
     ST_SetSRID(ST_MakePoint(6.5665, 53.2194), 4326))
ON CONFLICT (key) DO NOTHING;
