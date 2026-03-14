"""Hedera Proof-of-Signal (PoSg) specification.

This module documents the existing Hedera infrastructure and specifies the
new cell-level anchoring protocol for Royal Jelly tier data.

Existing infrastructure (swarmrouter):
    - HederaBridge       → data/factory/hedera_bridge.py  (batch Merkle roots)
    - HederaSignalBridge → signal/integrations/hedera_bridge.py  (signal fingerprints)

Mainnet HCS topics:
    - Block:   0.0.10291833
    - Receipt: 0.0.10291834
    - Event:   0.0.10291836
    - PoE:     0.0.10291838  ← PoSg certificates published here
    - Escrow:  0.0.10294205

Cost: ~$0.0008 per HCS message
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from royal_jelly.models.cell import HiveCell
from royal_jelly.models.provenance import HederaAnchor, MerkleProof, PoSgCellAnchor
from royal_jelly.models.tier import HoneyTier

# The PoE topic is reused for PoSg cell certificates
POSG_TOPIC_ID = "0.0.10291838"


def build_posg_certificate(
    cell: HiveCell,
    batch_root: str,
    proof: MerkleProof,
    proof_index: int,
) -> dict:
    """Build a compact PoSg certificate for HCS publishing (<1024 bytes).

    Only royal_jelly tier cells are eligible for individual anchoring.
    Honey/pollen/propolis are covered by batch-level Merkle roots.

    Returns the HCS message payload as a dict.
    """
    if cell.jelly_score is None or cell.jelly_score.tier != HoneyTier.royal_jelly:
        raise ValueError(
            f"PoSg anchoring is reserved for royal_jelly tier cells. "
            f"Got tier={cell.jelly_score.tier if cell.jelly_score else 'none'}"
        )

    return {
        "type": "posg_cell",
        "cell_id": cell.cell_id,
        "jelly_score": cell.jelly_score.score,
        "tier": "royal_jelly",
        "fingerprint": cell.fingerprint[:32],
        "batch_root": batch_root[:32],
        "proof_index": proof_index,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "v": "1.0",
    }


def build_posg_anchor(
    cell: HiveCell,
    batch_root: str,
    proof: MerkleProof,
    anchor: HederaAnchor,
) -> PoSgCellAnchor:
    """Build a complete PoSg anchor record after Hedera publishing."""
    if cell.jelly_score is None:
        raise ValueError("Cell must have a JellyScore to create PoSg anchor")

    return PoSgCellAnchor(
        cell_id=cell.cell_id,
        cell_fingerprint=cell.fingerprint,
        jelly_score=cell.jelly_score.score,
        tier="royal_jelly",
        batch_merkle_root=batch_root,
        batch_merkle_proof=proof,
        hedera_anchor=anchor,
    )


# ---------------------------------------------------------------------------
# Batch-level anchoring (documents existing swarmrouter implementation)
# ---------------------------------------------------------------------------

BATCH_MESSAGE_FORMAT = {
    "type": "pair_batch",
    "merkle_root": "<SHA256 hex>",
    "timestamp": "<ISO 8601>",
    "version": "1.0",
    "publisher": "swarmandbee.hbar",
    "domain": "<cre|medical|aviation>",
    "total_pairs": 0,
    "gate_pass_rate": 0.0,
    "file_sha256": "<hash>",
}

SIGNAL_MESSAGE_FORMAT = {
    "t": "signal",
    "h": "<SHA256 hash>",
    "p": 1,
    "d": "<domain>",
    "w": "<worker>",
    "c": 0.0,
    "ts": "<compact ISO>",
    "v": "1.0",
    "pub": "swarmandbee.hbar",
    "n": "<80 chars max summary>",
}
