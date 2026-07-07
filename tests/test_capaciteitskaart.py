"""Unit tests for the capaciteitskaart parser.

The CSV fixtures here are SYNTHETIC (clearly-labelled test data exercising the parser's
logic) — not real capacity data, and never loaded into the database as such. They cover
both encodings we might meet: the long Dutch legend phrases and the ordinal 0–3 codes.
"""

from __future__ import annotations

from datetime import date

import pytest

from ingestion.capaciteitskaart import (
    AVAILABLE,
    CONGESTED,
    LIMITED,
    STUDY,
    UNKNOWN,
    classify,
    normalize_pc6,
    parse_rows,
)

AS_OF = date(2026, 6, 1)


@pytest.mark.parametrize(
    "raw,expected",
    [
        (" 1012 ab ", "1012AB"),
        ("1012AB", "1012AB"),
        ("9711lv", "9711LV"),
    ],
)
def test_normalize_pc6(raw: str, expected: str) -> None:
    assert normalize_pc6(raw) == expected


@pytest.mark.parametrize("bad", ["1012A", "10123AB", "ABCDEF", "", "1012 A"])
def test_normalize_pc6_rejects_bad(bad: str) -> None:
    with pytest.raises(ValueError):
        normalize_pc6(bad)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("groen", AVAILABLE),
        ("Oranje", LIMITED),
        ("ROOD", CONGESTED),
        ("grijs", STUDY),
        ("0", AVAILABLE),
        ("3", CONGESTED),
        ("", UNKNOWN),
        ("Tekort aan transportcapaciteit met wachtrij", CONGESTED),
        ("Transportcapaciteit beperkt beschikbaar zonder wachtrij", LIMITED),
        ("Transportcapaciteit beschikbaar zonder wachtrij", AVAILABLE),
        ("Gebied is in onderzoek met wachtrij", STUDY),
        ("Kleur wordt later toegevoegd", UNKNOWN),
    ],
)
def test_classify(raw: str, expected: str) -> None:
    assert classify(raw) == expected


def test_classify_rejects_unknown_rather_than_guessing() -> None:
    with pytest.raises(ValueError):
        classify("banana")


def test_parse_rows_semicolon_phrases() -> None:
    avail = "Transportcapaciteit beschikbaar zonder wachtrij"
    beperkt = "Transportcapaciteit beperkt beschikbaar zonder wachtrij"
    tekort = "Tekort aan transportcapaciteit met wachtrij"
    csv_text = (
        "postcode;afname;invoeding\n"
        f"1012AB;{avail};{tekort}\n"
        f"9711LV;{beperkt};{avail}\n"
    )
    rows = parse_rows(csv_text, AS_OF)
    assert len(rows) == 2
    assert rows[0].pc6 == "1012AB"
    assert rows[0].offtake_status == AVAILABLE
    assert rows[0].feedin_status == CONGESTED
    assert rows[1].offtake_status == LIMITED
    assert rows[0].as_of == AS_OF
    assert rows[0].raw["postcode"] == "1012AB"


def test_parse_rows_comma_ordinal() -> None:
    csv_text = "pc6,afname,invoeding\n1012AB,0,3\n9711LV,1,2\n"
    rows = parse_rows(csv_text, AS_OF)
    assert rows[0].offtake_status == AVAILABLE
    assert rows[0].feedin_status == CONGESTED
    assert rows[1].offtake_status == LIMITED
    assert rows[1].feedin_status == STUDY


def test_parse_rows_missing_column_fails_loudly() -> None:
    csv_text = "postcode;afname\n1012AB;groen\n"  # no invoeding column
    with pytest.raises(ValueError, match="feed-in/invoeding"):
        parse_rows(csv_text, AS_OF)
