"""Hive Cell — the canonical unit of intelligence in the Royal Jelly Protocol."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from royal_jelly.models.score import JellyScoreResult


class CellLineage(BaseModel):
    """Provenance chain for how this cell was produced.

    Maps to the ``_cell`` metadata stamped by ``HiveCellStamper`` in
    swarmrouter/data/hivecell.py.
    """

    gen_model: str = ""
    cook_script: str = ""
    cook_run: str = ""
    source_model: str = ""


class HiveCell(BaseModel):
    """A single Hive Cell — the atomic unit of verified intelligence.

    Schema-compatible with ``HiveCellStamper.stamp()`` output at
    swarmrouter/data/hivecell.py:202-237, extended with JellyScore.

    The ``cell_id`` format is ``HIVE-{DOMAIN_3}-{fingerprint_12}`` where
    DOMAIN_3 is a 3-letter domain code (CRE, MED, AVI, etc.) and
    fingerprint_12 is the first 12 hex chars of the SHA-256 content hash.
    """

    cell_id: str = Field(
        ..., pattern=r"^HIVE-[A-Z]{3}-.{12}$",
        description="Canonical cell identifier",
    )
    domain: str
    grade: str = Field(
        ..., description="royal_jelly | honey | pollen | propolis"
    )
    messages: list[dict[str, str]] = Field(
        ..., description="Chat-format messages: [{role, content}, ...]"
    )
    jelly_score: Optional[JellyScoreResult] = None
    lineage: CellLineage = Field(default_factory=CellLineage)
    fingerprint: str = Field(..., description="SHA-256 of normalised Q+A content")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    task_type: str = ""
    source_signal: str = Field(
        default="", description="Signal ID that originated this cell"
    )
