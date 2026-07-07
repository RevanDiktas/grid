"""Report-path enforcement: the licence gate, auto-attribution, and the provenance footer.

Built now so the (not-yet-existing) report generator inherits it by construction rather than
bolting it on later. Any code that emits a customer-facing artifact (report or map) MUST route
its contributing sources through here:

- ``assert_report_safe`` — hard gate: refuse if any contributing source is
  ``customer_report_safe=False`` (so e.g. Enexis waitlist data can never reach a *paid* report).
- ``required_attributions`` — collect the exact credit strings that MUST render.
- ``provenance_footer`` — the standing footer every report/map carries (attribution block, each
  fact's source + as_of + confidence, and the indicative + not-advice disclaimers). It enforces
  the gate first, so a footer can't even be built for report-unsafe data.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from provenance.sources import get_source

# Standing disclaimers — every customer-facing artifact renders both (see feasibility-report skill).
INDICATIVE_DISCLAIMER = (
    "Capacity and timelines are indicative; confirmed only by the operator's technical study."
)
NOT_ADVICE = "This report is informational and is not legal or financial advice."


class ReportLicenceError(Exception):
    """Raised when a source that is not ``customer_report_safe`` would reach a customer report."""


@dataclass(frozen=True)
class FactProvenance:
    """Provenance of one fact contributing to an output."""

    source: str
    as_of: date
    confidence: float | None = None


@dataclass(frozen=True)
class ProvenanceFooter:
    """Structured footer the report/map template renders. Kept structured (not pre-rendered
    HTML) so the future WeasyPrint template can lay it out."""

    attributions: list[str]
    entries: list[FactProvenance]
    disclaimers: list[str]

    def render_text(self) -> str:
        """Plain-text rendering (usable before the HTML template exists)."""
        lines = ["Bronnen / Sources:"]
        for e in sorted(self.entries, key=lambda x: x.source):
            conf = f", confidence {e.confidence:.2f}" if e.confidence is not None else ""
            lines.append(f"  - {e.source} (as of {e.as_of.isoformat()}{conf})")
        if self.attributions:
            lines.append("Attribution: " + " · ".join(self.attributions))
        lines.extend(self.disclaimers)
        return "\n".join(lines)


def assert_report_safe(source_names: Iterable[str]) -> None:
    """Raise ``ReportLicenceError`` if any named source may not appear in a paid customer report.

    ``get_source`` also fails loud on an unregistered name, so an unknown source is blocked too.
    """
    blocked = [n for n in dict.fromkeys(source_names) if not get_source(n).customer_report_safe]
    if blocked:
        raise ReportLicenceError(
            "these sources are not customer_report_safe and must not reach a paid report: "
            + ", ".join(sorted(blocked))
        )


def required_attributions(source_names: Iterable[str]) -> list[str]:
    """De-duplicated, first-seen-ordered list of the credit strings that MUST render."""
    out: list[str] = []
    for name in dict.fromkeys(source_names):  # preserve first-seen order, dedupe names
        attribution = get_source(name).attribution
        if attribution and attribution not in out:
            out.append(attribution)
    return out


def provenance_footer(facts: Iterable[FactProvenance]) -> ProvenanceFooter:
    """Build the standing provenance footer for the given contributing facts.

    Enforces the licence gate first: a footer cannot be built for report-unsafe data.
    """
    entries = list(facts)
    source_names = [e.source for e in entries]
    assert_report_safe(source_names)  # gate before we render anything
    return ProvenanceFooter(
        attributions=required_attributions(source_names),
        entries=entries,
        disclaimers=[INDICATIVE_DISCLAIMER, NOT_ADVICE],
    )
