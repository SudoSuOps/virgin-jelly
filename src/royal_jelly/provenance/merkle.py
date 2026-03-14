"""Merkle tree operations — standalone port from swarmrouter/data/factory/merkle.py.

Pure SHA-256 implementation (stdlib hashlib, no external deps).
Deterministic across runs via normalised text fingerprinting.
"""

from __future__ import annotations

import hashlib


def pair_fingerprint(pair: dict) -> str:
    """SHA-256 hash of normalised Q+A content.

    Matches the canonical fingerprint used throughout the Swarm pipeline.
    Normalisation: lowercase, collapse whitespace, concatenate question + answer.
    """
    question = ""
    answer = ""
    for msg in pair.get("messages", []):
        if msg.get("role") == "user":
            question = msg.get("content", "")
        elif msg.get("role") == "assistant":
            answer = msg.get("content", "")
    text = " ".join((question + " " + answer).lower().split())
    return hashlib.sha256(text.encode()).hexdigest()


def merkle_root(hashes: list[str]) -> str:
    """Compute the Merkle root from a list of leaf hashes.

    If the number of leaves is odd, the last leaf is duplicated.
    Empty list returns the hash of an empty string.
    """
    if not hashes:
        return hashlib.sha256(b"").hexdigest()

    layer = list(hashes)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        next_layer: list[str] = []
        for i in range(0, len(layer), 2):
            combined = layer[i] + layer[i + 1]
            next_layer.append(hashlib.sha256(combined.encode()).hexdigest())
        layer = next_layer

    return layer[0]


def merkle_proof(hashes: list[str], index: int) -> list[dict[str, str]]:
    """Generate an inclusion proof for the leaf at ``index``.

    Returns a list of ``{"hash": "...", "side": "left"|"right"}`` dicts
    that, combined with the leaf hash, reconstruct the root.
    """
    if not hashes or index < 0 or index >= len(hashes):
        return []

    layer = list(hashes)
    proof: list[dict[str, str]] = []
    idx = index

    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        if idx % 2 == 0:
            sibling = layer[idx + 1]
            proof.append({"hash": sibling, "side": "right"})
        else:
            sibling = layer[idx - 1]
            proof.append({"hash": sibling, "side": "left"})
        next_layer: list[str] = []
        for i in range(0, len(layer), 2):
            combined = layer[i] + layer[i + 1]
            next_layer.append(hashlib.sha256(combined.encode()).hexdigest())
        layer = next_layer
        idx //= 2

    return proof


def verify_proof(leaf_hash: str, proof: list[dict[str, str]], root: str) -> bool:
    """Verify that a leaf is included in the tree with the given root."""
    current = leaf_hash
    for step in proof:
        sibling = step["hash"]
        if step["side"] == "right":
            combined = current + sibling
        else:
            combined = sibling + current
        current = hashlib.sha256(combined.encode()).hexdigest()
    return current == root
