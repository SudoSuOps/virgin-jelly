"""Signal origin model — Pydantic upgrade of the swarmrouter Signal dataclass."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SignalOrigin(BaseModel):
    """Where the intelligence came from.

    Maps to ``BaseWorker.Signal`` in swarmrouter/signal/workers/base_worker.py.
    The ``source_weight`` field carries the worker's canonical trust level
    (e.g. EDGAR = 0.9, Reddit = 0.5).
    """

    source_worker: str = Field(
        ..., description="Worker that collected this signal (e.g. 'edgar', 'fred')"
    )
    source_url: str = Field(
        ..., description="URL or URI of the original source document"
    )
    source_weight: float = Field(
        ge=0.0, le=1.0,
        description="Canonical trust level from the worker class attribute",
    )
    collected_at: datetime
    dedup_key: str = Field(
        ..., description="MD5 hash of normalised title — used for 72-hour dedup window"
    )
    domain: str = Field(..., description="cre, medical, aviation, ai, etc.")
    signal_type: str = Field(
        ..., description="filing, economic, news, research, incident, etc."
    )
    priority: int = Field(ge=1, le=5, description="1=critical … 5=background")
    entities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
