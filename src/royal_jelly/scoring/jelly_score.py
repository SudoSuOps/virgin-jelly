"""JellyScore — the composite scoring engine for the Royal Jelly Protocol.

The formula maps every weight to a concrete computation in swarmrouter:

    JellyScore = (
        source_confidence    * 0.25  +
        gate_integrity       * 0.30  +
        reasoning_depth      * 0.20  +
        entropy_health       * 0.10  +
        fingerprint_unique   * 0.15
    ) * 100

    If adversarial.source_fault_detected:
        JellyScore *= (1.0 - adversarial.confidence_penalty)
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from royal_jelly.models.score import (
    AdversarialResult,
    GateResults,
    JellyScoreResult,
    ScoreComponents,
)
from royal_jelly.models.signal import SignalOrigin
from royal_jelly.models.tier import HoneyTier, tier_from_score
from royal_jelly.protocol import DOMAIN_CONCEPTS, JELLY_WEIGHTS, SOURCE_WEIGHTS
from royal_jelly.scoring.adversarial import SourceFaultDetector
from royal_jelly.scoring.gates import run_all_gates


# ---------------------------------------------------------------------------
# Source confidence sub-formula
# ---------------------------------------------------------------------------
# EntityScorer from swarmrouter/signal/scorer.py:113-141
#
#   source_confidence =
#       source_weight          * 0.40
#     + entity_richness        * 0.25
#     + freshness              * 0.20
#     + cross_source           * 0.15
# ---------------------------------------------------------------------------

def _compute_source_confidence(
    source_weight: float,
    entity_count: int,
    signal_age_hours: float = 0.0,
    cross_source_count: int = 0,
) -> float:
    """Compute source confidence using the EntityScorer formula."""
    # Entity richness: more entities = higher confidence (cap at 10)
    entity_richness = min(entity_count / 10, 1.0)

    # Freshness: newer signals are more valuable (decay over 168 hours / 1 week)
    freshness = max(0.0, 1.0 - (signal_age_hours / 168.0))

    # Cross-source confirmation: more independent sources = higher confidence
    cross_source = min(cross_source_count / 3, 1.0)

    return (
        source_weight * 0.40
        + entity_richness * 0.25
        + freshness * 0.20
        + cross_source * 0.15
    )


# ---------------------------------------------------------------------------
# Reasoning depth sub-formula
# ---------------------------------------------------------------------------
# DifficultyProfile from swarmrouter/data/difficulty_scorer.py:132-191
#
#   reasoning_depth (0-10) =
#       trajectory_steps (0-5)     — IDENTIFY/CALCULATE/ANALYZE/EVALUATE/RECOMMEND
#     + causal_chains   (0-3 cap)  — because/therefore/implies
#     + conditionals    (0-2 cap)  — if/then/unless/when
#     + quant_ops       (0-2 cap)  — $/% or calculation patterns
# ---------------------------------------------------------------------------

_TRAJECTORY_KEYWORDS = ["identify", "calculate", "analyze", "evaluate", "recommend"]
_CAUSAL_KEYWORDS = ["because", "therefore", "implies", "consequently", "thus", "hence"]
_CONDITIONAL_KEYWORDS = ["if", "then", "unless", "when", "assuming", "given that"]


def _compute_reasoning_depth(answer: str) -> float:
    """Compute reasoning depth (0-10 scale, normalised to 0-1)."""
    answer_lower = answer.lower()

    trajectory = sum(1 for kw in _TRAJECTORY_KEYWORDS if kw in answer_lower)
    trajectory = min(trajectory, 5)

    causal = sum(1 for kw in _CAUSAL_KEYWORDS if kw in answer_lower)
    causal = min(causal, 3)

    conditionals = sum(1 for kw in _CONDITIONAL_KEYWORDS if kw in answer_lower)
    conditionals = min(conditionals, 2)

    # Quantitative operations: presence of $ or % or calculation patterns
    quant = 0
    if "$" in answer or "%" in answer:
        quant += 1
    if re.search(r"\d+\s*[x×*/+-]\s*\d+", answer):
        quant += 1
    quant = min(quant, 2)

    raw = trajectory + causal + conditionals + quant  # 0-12, capped below
    depth = min(raw, 10) / 10.0
    return depth


# ---------------------------------------------------------------------------
# Fingerprint
# ---------------------------------------------------------------------------

def _fingerprint(question: str, answer: str) -> str:
    """SHA-256 of normalised Q+A content — matches merkle.py pair_fingerprint."""
    text = " ".join((question + " " + answer).lower().split())
    return hashlib.sha256(text.encode()).hexdigest()


# ---------------------------------------------------------------------------
# JellyScorer
# ---------------------------------------------------------------------------

class JellyScorer:
    """Composite scoring engine for the Royal Jelly Protocol.

    Usage::

        scorer = JellyScorer(domain="cre", source_weight=0.9)
        result = scorer.score(record)
        print(result.tier)  # HoneyTier.royal_jelly
    """

    def __init__(
        self,
        domain: str = "cre",
        source_weight: float | None = None,
        entropy_health: float = 0.80,
    ):
        self.domain = domain
        self.source_weight = source_weight or SOURCE_WEIGHTS.get(domain, 0.5)
        self.entropy_health = entropy_health  # batch-level, set once per batch
        self._seen_hashes: set[str] = set()
        self._fault_detector = SourceFaultDetector()

    def score(
        self,
        record: dict,
        signal: SignalOrigin | None = None,
        cross_source_count: int = 0,
    ) -> JellyScoreResult:
        """Score a single record and return a full JellyScoreResult.

        Args:
            record: A pair in messages format (``{"messages": [...]}``).
            signal: Optional signal origin for source confidence and
                    adversarial analysis.
            cross_source_count: Number of independent sources confirming
                                the same intelligence.
        """
        # -- Extract content --
        question = ""
        answer = ""
        for msg in record.get("messages", []):
            if msg.get("role") == "user":
                question = msg.get("content", "")
            elif msg.get("role") == "assistant":
                answer = msg.get("content", "")

        fp = _fingerprint(question, answer)

        # -- 1. Run 6 deterministic gates --
        all_passed, gate_results = run_all_gates(
            record, domain=self.domain, seen_hashes=self._seen_hashes
        )
        gates = GateResults(
            json_valid=gate_results[0].passed,
            output_length=gate_results[1].passed,
            numeric_verify=gate_results[2].passed,
            concept_present=gate_results[3].passed,
            dedup=gate_results[4].passed,
            degenerate=gate_results[5].passed,
        )

        # -- 2. Source confidence --
        # When SignalOrigin is absent, assume reasonable baselines.
        # Absence of metadata does NOT mean the signal is bad — it means
        # we don't have the metadata yet. Default to optimistic middle
        # ground that content quality (gates + reasoning) can push to
        # royal_jelly without signal metadata being a gatekeeper.
        if signal:
            entity_count = len(signal.entities)
            now = datetime.now(timezone.utc)
            collected = signal.collected_at
            if collected.tzinfo is None:
                collected = collected.replace(tzinfo=timezone.utc)
            signal_age_hours = (now - collected).total_seconds() / 3600.0
            sw = signal.source_weight
        else:
            # Metadata-absent baseline: assume 5 entities (moderate richness),
            # fresh signal (0 hours), 1 cross-source confirmation.
            entity_count = 5
            signal_age_hours = 0.0
            cross_source_count = max(cross_source_count, 1)
            sw = self.source_weight

        source_confidence = _compute_source_confidence(
            source_weight=sw,
            entity_count=entity_count,
            signal_age_hours=signal_age_hours,
            cross_source_count=cross_source_count,
        )

        # -- 3. Reasoning depth --
        reasoning = _compute_reasoning_depth(answer)

        # -- 4. Fingerprint uniqueness --
        fp_unique = 1.0 if gates.dedup else 0.0

        # -- 5. Compose score --
        w = JELLY_WEIGHTS
        raw = (
            source_confidence * w["source_confidence"]
            + gates.gate_pass_rate * w["gate_integrity"]
            + reasoning * w["reasoning_depth"]
            + self.entropy_health * w["entropy_health"]
            + fp_unique * w["fingerprint_uniqueness"]
        ) * 100

        # -- 6. Adversarial gate --
        adversarial: AdversarialResult | None = None
        if signal:
            adversarial = self._fault_detector.detect(signal, answer)
            if adversarial.source_fault_detected:
                raw *= (1.0 - adversarial.confidence_penalty)

        score = round(min(max(raw, 0.0), 100.0), 2)
        tier = tier_from_score(score)

        components = ScoreComponents(
            source_confidence=round(source_confidence, 4),
            gate_integrity=round(gates.gate_pass_rate, 4),
            reasoning_depth=round(reasoning, 4),
            entropy_health=round(self.entropy_health, 4),
            fingerprint_uniqueness=fp_unique,
        )

        cell_id = f"HIVE-{self.domain[:3].upper()}-{fp[:12]}"

        return JellyScoreResult(
            score=score,
            tier=tier,
            components=components,
            gates=gates,
            adversarial=adversarial,
            cell_id=cell_id,
            fingerprint=fp,
        )
