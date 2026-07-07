"""GridScout provenance & licence enforcement.

Single import point for source licence metadata and the report-path licence gate.
"""

from __future__ import annotations

from provenance.report_gate import (
    INDICATIVE_DISCLAIMER,
    NOT_ADVICE,
    FactProvenance,
    ProvenanceFooter,
    ReportLicenceError,
    assert_report_safe,
    provenance_footer,
    required_attributions,
)
from provenance.sources import SOURCES, Source, get_source

__all__ = [
    "INDICATIVE_DISCLAIMER",
    "NOT_ADVICE",
    "SOURCES",
    "FactProvenance",
    "ProvenanceFooter",
    "ReportLicenceError",
    "Source",
    "assert_report_safe",
    "get_source",
    "provenance_footer",
    "required_attributions",
]
