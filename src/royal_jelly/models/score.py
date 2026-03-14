"""JellyScore result models — the output of the scoring engine."""

from __future__ import annotations

from pydantic import BaseModel, Field

from royal_jelly.models.tier import HoneyTier


class GateResults(BaseModel):
    """Results from the 6 deterministic quality gates.

    Maps to ``run_all_gates()`` in swarmrouter/data/factory/gates.py.
    """

    json_valid: bool = True
    output_length: bool = True
    numeric_verify: bool = True
    concept_present: bool = True
    dedup: bool = True
    degenerate: bool = True

    @property
    def gates_passed(self) -> int:
        return sum([
            self.json_valid, self.output_length, self.numeric_verify,
            self.concept_present, self.dedup, self.degenerate,
        ])

    @property
    def gate_pass_rate(self) -> float:
        return self.gates_passed / 6


class ScoreComponents(BaseModel):
    """The 5 sub-scores that compose the JellyScore.

    Each maps to a concrete computation in the swarmrouter codebase:

    - source_confidence  → signal/scorer.py EntityScorer
    - gate_integrity     → data/factory/gates.py pass rate
    - reasoning_depth    → data/difficulty_scorer.py DifficultyProfile
    - entropy_health     → data/factory/entropy.py batch health
    - fingerprint_uniqueness → data/factory/merkle.py uniqueness check
    """

    source_confidence: float = Field(
        ge=0.0, le=1.0,
        description="source_weight*0.4 + entity_richness*0.25 + freshness*0.2 + cross_source*0.15",
    )
    gate_integrity: float = Field(
        ge=0.0, le=1.0,
        description="Pass rate across 6 deterministic gates (6/6 = 1.0)",
    )
    reasoning_depth: float = Field(
        ge=0.0, le=1.0,
        description="Trajectory steps + causal chains + conditionals + quantitative ops (0-10 normalised to 0-1)",
    )
    entropy_health: float = Field(
        ge=0.0, le=1.0,
        description="Batch-level vocab/structure/bigram entropy (0-100 normalised to 0-1)",
    )
    fingerprint_uniqueness: float = Field(
        ge=0.0, le=1.0,
        description="1.0 if unique SHA-256 fingerprint, 0.0 if duplicate",
    )


class AdversarialResult(BaseModel):
    """Source-at-fault gate result.

    The adversarial gate checks whether the *source material itself* is
    unreliable — retractions, amendments, contradictions, staleness.
    Unlike the 6 quality gates (which check model output), this gate checks
    input quality.

    The gate does NOT reject data — it applies a confidence penalty (up to
    0.50) that degrades the JellyScore, potentially dropping the cell to a
    lower tier.
    """

    source_fault_detected: bool = False
    fault_type: str = Field(
        default="",
        description="retraction | amendment | contradiction | stale | empty if no fault",
    )
    confidence_penalty: float = Field(
        ge=0.0, le=0.5, default=0.0,
        description="Additive penalties capped at 0.50",
    )
    evidence: str = Field(
        default="",
        description="Brief explanation of what triggered the fault",
    )


class JellyScoreResult(BaseModel):
    """Complete JellyScore output for a single intelligence cell."""

    score: float = Field(ge=0.0, le=100.0, description="Composite JellyScore")
    tier: HoneyTier
    components: ScoreComponents
    gates: GateResults
    adversarial: AdversarialResult | None = None
    cell_id: str = ""
    fingerprint: str = ""
