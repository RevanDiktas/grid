"""Unit tests for the Liander IP2026 §10.6 parser.

Fixtures are SYNTHETIC rows that replicate the appendix's column *structure* with invented station
names — not copied source text — so we test the parser without reproducing the document.
"""

from __future__ import annotations

import pytest

from ingestion.investeringsplannen_liander import (
    extract_knelpunt,
    parse_decimal,
    parse_ibn_years,
    parse_lines,
    parse_row,
)


@pytest.mark.parametrize(
    "raw,expected",
    [("0,9", 0.9), ("17,5", 17.5), ("0", 0.0), ("n.v.t.", None), ("n.t.b.", None), ("", None)],
)
def test_parse_decimal(raw: str, expected: float | None) -> None:
    assert parse_decimal(raw) == expected


def test_parse_ibn_years_takes_latest_end_year() -> None:
    # ranges use their END year; latest across packed values wins.
    assert parse_ibn_years("2024;2032 - 2034;2029 - 2031") == (2034, False)
    assert parse_ibn_years("2031 - 2033;n.t.b.") == (2033, True)  # undetermined flagged
    assert parse_ibn_years("n.v.t.") == (None, True)  # nothing concrete


@pytest.mark.parametrize(
    "label,station,knelpunt",
    [
        ("OS TESTVILLE 10-1i", "OS TESTVILLE", "10-1i"),
        ("OS TESTVILLE 10-1i + 10-2i", "OS TESTVILLE", "10-1i + 10-2i"),
        ("OS TESTVILLE 20KV 20-1i", "OS TESTVILLE 20KV", "20-1i"),
        ("Aansluitknelpunt OS Testville", "Aansluitknelpunt OS Testville", None),
    ],
)
def test_extract_knelpunt(label: str, station: str, knelpunt: str | None) -> None:
    assert extract_knelpunt(label) == (station, knelpunt)


def test_parse_row_offtake_clean() -> None:
    # kV, 3 onset yrs, 3 MW-1e-jaar, 3 MW-2035, ID investering, IBN jaar
    row = "OS TESTVILLE 20-1i Afname 20 2026 2026 2026 17,5 17,8 17,5 48,2 51,4 44,1 105827;106092 2031 - 2033;n.t.b."  # noqa: E501
    fact = parse_row(row, province="Noord-Holland")
    assert fact is not None
    assert fact.location_name == "OS TESTVILLE"
    assert fact.bottleneck == "20-1i"
    assert fact.direction == "offtake"
    assert fact.added_mw == 51.4  # max of the 2035 scenario triplet (48,2 / 51,4 / 44,1)
    assert fact.expected_year == 2033  # latest IBN end-year
    assert fact.province == "Noord-Holland"
    assert fact.confidence == 0.35  # undetermined IBN present → low


def test_parse_row_feedin_and_confidence() -> None:
    row = "OS TESTVILLE 10-1i Opwek 10 2025 2025 2025 1 6,5 1 54,6 113,7 55 102244 2026"
    fact = parse_row(row)
    assert fact is not None
    assert fact.direction == "feedin"
    assert fact.added_mw == 113.7
    assert fact.expected_year == 2026
    assert fact.confidence == 0.5  # fully determined IBN


def test_parse_row_all_null_yields_no_year() -> None:
    row = "OS TESTVILLE SUB 10-1i Afname 10 2036 2034 2039 0,4 0,1 0,2 0 0,8 0 n.t.b. n.v.t."
    fact = parse_row(row)
    assert fact is not None
    assert fact.expected_year is None
    assert fact.confidence == 0.35


def test_parse_row_skips_non_data_lines() -> None:
    assert parse_row("Noord-Holland") is None
    assert parse_row("ID knelpunt") is None
    assert parse_row("2034") is None  # wrapped fragment
    assert (
        parse_row("OS TESTVILLE 10-1i Afname 10 2038") is None
    )  # too few columns → skip, not guess


def test_parse_lines_tracks_province_and_collects() -> None:
    lines = [
        "Noord-Holland",
        "OS TESTVILLE 10-1i Afname 10 2025 2025 2025 1 2 1 10 20 12 105001 2027",
        "ID knelpunt",  # legend noise, ignored
        "OS OTHERTOWN 20-1i Opwek 20 2026 2026 2026 3 4 3 30 40 33 105002 2028",
    ]
    facts = parse_lines(lines)
    assert [f.location_name for f in facts] == ["OS TESTVILLE", "OS OTHERTOWN"]
    assert all(f.province == "Noord-Holland" for f in facts)
    # idempotency keys are distinct
    assert len({f.project_ref for f in facts}) == 2
