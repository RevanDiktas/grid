"""Tests for the licence gate + auto-attribution + provenance footer.

These are the structural guarantee that report-unsafe data (e.g. the Enexis waitlist) can never
reach a paid customer report, and that mandatory attribution + disclaimers always render.
"""

from __future__ import annotations

from datetime import date

import pytest

from provenance import (
    INDICATIVE_DISCLAIMER,
    NOT_ADVICE,
    FactProvenance,
    ReportLicenceError,
    assert_report_safe,
    get_source,
    provenance_footer,
    required_attributions,
)


def test_get_source_fails_loud_on_unregistered() -> None:
    with pytest.raises(KeyError, match="not registered"):
        get_source("totally_made_up_source")


def test_flags_match_spec() -> None:
    cbs = get_source("cbs_postcode6")
    assert cbs.customer_report_safe and cbs.reproduction_allowed
    assert cbs.attribution == "© CBS, © Esri Nederland"

    cap = get_source("capaciteitskaart")
    assert cap.customer_report_safe and not cap.reproduction_allowed  # facts safe, raw not

    ip = get_source("investeringsplannen_2026")
    assert ip.customer_report_safe and not ip.reproduction_allowed

    enx = get_source("enexis_waitlist")
    assert not enx.customer_report_safe and not enx.reproduction_allowed  # blocked


def test_gate_passes_safe_sources() -> None:
    # No raise for the safe set.
    assert_report_safe(["cbs_postcode6", "capaciteitskaart", "investeringsplannen_2026"])


def test_gate_blocks_enexis_from_a_paid_report() -> None:
    with pytest.raises(ReportLicenceError, match="enexis_waitlist"):
        assert_report_safe(["cbs_postcode6", "enexis_waitlist"])


def test_gate_blocks_unassessed_source_by_default() -> None:
    # Registered-but-unverified sources are report-unsafe by default.
    with pytest.raises(ReportLicenceError, match="tennet"):
        assert_report_safe(["cbs_postcode6", "tennet"])


def test_required_attributions_collects_and_dedupes() -> None:
    attrs = required_attributions(
        ["cbs_postcode6", "cbs_postcode6", "investeringsplannen_2026"]
    )
    assert attrs == [
        "© CBS, © Esri Nederland",
        "Bron: <operator> Investeringsplan 2026",
    ]


def test_provenance_footer_renders_disclaimers_and_sources() -> None:
    footer = provenance_footer(
        [
            FactProvenance("cbs_postcode6", date(2024, 1, 1)),
            FactProvenance("investeringsplannen_2026", date(2026, 1, 1), confidence=0.6),
        ]
    )
    assert INDICATIVE_DISCLAIMER in footer.disclaimers
    assert NOT_ADVICE in footer.disclaimers
    assert "© CBS, © Esri Nederland" in footer.attributions
    text = footer.render_text()
    assert "cbs_postcode6 (as of 2024-01-01)" in text
    assert "confidence 0.60" in text


def test_provenance_footer_refuses_unsafe_data() -> None:
    # Cannot even build a footer that includes report-unsafe data.
    with pytest.raises(ReportLicenceError):
        provenance_footer([FactProvenance("enexis_waitlist", date(2026, 7, 6))])
