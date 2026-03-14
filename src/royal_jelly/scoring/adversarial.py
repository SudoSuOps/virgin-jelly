"""Source-at-fault gate — detects unreliable source material.

This gate is NEW and does not exist in swarmrouter. It addresses the
adversarial case: what happens when the primary source is itself wrong?

An EDGAR filing with a restatement, a retracted PubMed paper, a corrected
news article, or a stale data point all reduce the confidence in the
intelligence derived from that source.

The gate does NOT reject data — it applies a confidence penalty (capped at
0.50) that degrades the JellyScore, potentially dropping a cell to a lower
tier. Data still flows through the pipeline but is flagged.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from royal_jelly.models.score import AdversarialResult
from royal_jelly.models.signal import SignalOrigin
from royal_jelly.protocol import ADVERSARIAL_PENALTY_CAP, STALENESS_THRESHOLD_DAYS

# ---------------------------------------------------------------------------
# Marker dictionaries
# ---------------------------------------------------------------------------

RETRACTION_MARKERS = [
    "restatement", "restated", "erroneously reported",
    "correction notice", "retracted", "withdrawn", "superseded",
    "errata", "corrigendum",
]

AMENDMENT_MARKERS = [
    "10-k/a", "10-q/a", "8-k/a", "amended filing",
    "amendment no.", "revised submission",
]

CONTRADICTION_MARKERS = [
    "contrary to", "contradicts", "inconsistent with",
    "disputes", "revised downward", "revised upward",
    "previously reported incorrectly",
]

# Penalties per fault type
_PENALTIES = {
    "retraction": 0.30,
    "amendment": 0.15,
    "contradiction": 0.25,
    "stale": 0.10,
}


class SourceFaultDetector:
    """Gate 7: Source-at-fault detection.

    Checks for signals that the source material itself is unreliable.
    Fundamentally different from the 6 quality gates (which check model
    output quality) — this gate checks input quality.
    """

    def detect(
        self,
        signal: SignalOrigin,
        content: str,
    ) -> AdversarialResult:
        """Analyse a signal and its derived content for source faults.

        Returns an ``AdversarialResult`` with the compound penalty (capped
        at 0.50) and evidence trail.
        """
        content_lower = content.lower()
        url_lower = signal.source_url.lower()
        combined = content_lower + " " + url_lower

        penalty = 0.0
        faults: list[str] = []
        evidence_parts: list[str] = []

        # --- Retraction check ---
        for marker in RETRACTION_MARKERS:
            if marker in combined:
                penalty += _PENALTIES["retraction"]
                faults.append("retraction")
                evidence_parts.append(f"retraction marker: '{marker}'")
                break

        # --- Amendment check ---
        for marker in AMENDMENT_MARKERS:
            if marker in combined:
                penalty += _PENALTIES["amendment"]
                faults.append("amendment")
                evidence_parts.append(f"amendment marker: '{marker}'")
                break

        # --- Contradiction check ---
        for marker in CONTRADICTION_MARKERS:
            if marker in content_lower:
                penalty += _PENALTIES["contradiction"]
                faults.append("contradiction")
                evidence_parts.append(f"contradiction marker: '{marker}'")
                break

        # --- Staleness check ---
        now = datetime.now(timezone.utc)
        collected = signal.collected_at
        if collected.tzinfo is None:
            collected = collected.replace(tzinfo=timezone.utc)
        age_days = (now - collected).days
        if age_days > STALENESS_THRESHOLD_DAYS:
            penalty += _PENALTIES["stale"]
            faults.append("stale")
            evidence_parts.append(f"signal age: {age_days} days (threshold: {STALENESS_THRESHOLD_DAYS})")

        # --- Cap compound penalty ---
        penalty = min(penalty, ADVERSARIAL_PENALTY_CAP)

        if not faults:
            return AdversarialResult()

        return AdversarialResult(
            source_fault_detected=True,
            fault_type="+".join(faults),
            confidence_penalty=round(penalty, 3),
            evidence="; ".join(evidence_parts),
        )
