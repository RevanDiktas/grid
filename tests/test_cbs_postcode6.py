"""Unit tests for the CBS Postcode6 geometry parser + CRS guard.

Fixtures are SYNTHETIC GeoJSON (tiny, clearly test-only) exercising parse/validate logic —
no real CBS data is loaded here. Coordinates use RD/28992 metres (the service's native CRS).
"""

from __future__ import annotations

from datetime import date

import pytest

from ingestion.cbs_postcode6 import (
    AS_OF,
    Area,
    assert_rd_envelope,
    parse_features,
)

# A minimal RD/28992 MultiPolygon around Amsterdam (~x122k, y490k).
_AMS_GEOM = {
    "type": "MultiPolygon",
    "coordinates": [[[[122300.0, 490900.0], [122400.0, 490900.0],
                      [122400.0, 491000.0], [122300.0, 491000.0], [122300.0, 490900.0]]]],
}


def _feature(pc6: str | None, geom: dict | None, fid: str = "postcode6.1") -> dict:
    return {"type": "Feature", "id": fid, "properties": {"postcode6": pc6}, "geometry": geom}


def test_parse_features_extracts_pc6_and_geometry() -> None:
    fc = {"features": [_feature("1011ab", _AMS_GEOM), _feature("9711LV", _AMS_GEOM)]}
    areas = parse_features(fc)
    assert [a.pc6 for a in areas] == ["1011AB", "9711LV"]  # normalised, uppercased
    assert all(isinstance(a, Area) and a.as_of == AS_OF for a in areas)
    assert '"MultiPolygon"' in areas[0].geom_geojson


def test_parse_features_skips_missing_pc6_or_geometry() -> None:
    fc = {
        "features": [
            _feature("1011AB", _AMS_GEOM),
            _feature(None, _AMS_GEOM),  # no postcode -> skipped
            _feature("1012NP", None),  # no geometry -> skipped
        ]
    }
    areas = parse_features(fc)
    assert [a.pc6 for a in areas] == ["1011AB"]


def test_parse_features_uses_given_as_of() -> None:
    fc = {"features": [_feature("1011AB", _AMS_GEOM)]}
    areas = parse_features(fc, as_of=date(2024, 1, 1))
    assert areas[0].as_of == date(2024, 1, 1)


def test_assert_rd_envelope_accepts_nl_rd_coords() -> None:
    assert_rd_envelope([_feature("1011AB", _AMS_GEOM)])  # in-envelope -> no raise


def test_assert_rd_envelope_rejects_lonlat_degrees() -> None:
    # If the service ever returned EPSG:4326 lon,lat, coords look like [4.9, 52.4] — far
    # outside the RD metre envelope. This is the axis/CRS trap the guard exists to catch.
    lonlat = {
        "type": "MultiPolygon",
        "coordinates": [[[[4.90, 52.37], [4.91, 52.37], [4.91, 52.38],
                          [4.90, 52.38], [4.90, 52.37]]]],
    }
    with pytest.raises(ValueError, match="outside the NL RD"):
        assert_rd_envelope([_feature("1011AB", lonlat)])


def test_assert_rd_envelope_rejects_empty() -> None:
    with pytest.raises(ValueError, match="nothing fetched"):
        assert_rd_envelope([_feature("1011AB", None)])
