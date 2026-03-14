"""BaseBee — abstract protocol for all Bee agents in the Royal Jelly Protocol.

Every Bee follows the same lifecycle:

    fetch → cook → gate → score → stamp → emit

This mirrors ``BaseWorker`` in swarmrouter/signal/workers/base_worker.py but
extends it to include the cooking (signal → training pair) and scoring
(JellyScore) steps that currently live in separate swarmrouter modules.

Three Bee classes exist in the protocol:
    - Scout Bee:   wide search, many sources, lower depth
    - Worker Bee:  deep extraction, single source, maximum fidelity
    - Auditor Bee: cross-validates other bees' output
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from royal_jelly.models.cell import CellLineage, HiveCell
from royal_jelly.models.score import JellyScoreResult
from royal_jelly.models.signal import SignalOrigin
from royal_jelly.scoring.jelly_score import JellyScorer


class BaseBee(ABC):
    """Abstract base class for Bee agents.

    Subclasses must implement ``fetch()`` and ``cook()``.
    The ``process()`` method runs the full lifecycle.
    """

    WORKER_NAME: str = ""
    SOURCE_WEIGHT: float = 0.5
    DOMAIN: str = ""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.scorer = JellyScorer(
            domain=self.DOMAIN,
            source_weight=self.SOURCE_WEIGHT,
        )
        self._stats = {"fetched": 0, "cooked": 0, "gated": 0, "emitted": 0}

    # -- Abstract methods -- subclasses implement these --------------------

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Fetch raw data from the source. Returns list of raw records."""
        ...

    @abstractmethod
    def cook(self, raw: dict) -> dict | None:
        """Transform a raw record into a training pair (messages format).

        Returns a dict with ``messages`` key, or None to skip.
        """
        ...

    # -- Optional overrides ------------------------------------------------

    def make_signal(self, raw: dict) -> SignalOrigin:
        """Build a SignalOrigin from a raw record. Override for custom mapping."""
        return SignalOrigin(
            source_worker=self.WORKER_NAME,
            source_url=raw.get("url", ""),
            source_weight=self.SOURCE_WEIGHT,
            collected_at=datetime.now(timezone.utc),
            dedup_key=raw.get("dedup_key", ""),
            domain=self.DOMAIN,
            signal_type=raw.get("signal_type", ""),
            priority=raw.get("priority", 3),
            entities=raw.get("entities", []),
            metadata=raw.get("metadata", {}),
        )

    # -- Lifecycle ---------------------------------------------------------

    def process(self) -> list[HiveCell]:
        """Execute the full Bee lifecycle: fetch → cook → gate → score → stamp → emit."""
        raw_records = self.fetch()
        self._stats["fetched"] = len(raw_records)

        cells: list[HiveCell] = []

        for raw in raw_records:
            # Cook: raw → training pair
            pair = self.cook(raw)
            if pair is None:
                continue
            self._stats["cooked"] += 1

            # Build signal origin
            signal = self.make_signal(raw)

            # Score: JellyScore computation (includes gates + adversarial)
            result: JellyScoreResult = self.scorer.score(
                pair, signal=signal, cross_source_count=0
            )

            # Gate check: all 6 must pass
            if result.gates.gates_passed < 6:
                self._stats["gated"] += 1
                continue

            # Stamp: create HiveCell
            cell = HiveCell(
                cell_id=result.cell_id,
                domain=self.DOMAIN,
                grade=result.tier.value,
                messages=pair["messages"],
                jelly_score=result,
                lineage=CellLineage(
                    gen_model=raw.get("gen_model", ""),
                    cook_script=self.WORKER_NAME,
                ),
                fingerprint=result.fingerprint,
                created_at=signal.collected_at,
                task_type=raw.get("task_type", ""),
                source_signal=signal.dedup_key,
            )
            cells.append(cell)
            self._stats["emitted"] += 1

        return cells

    @property
    def stats(self) -> dict:
        return dict(self._stats)
