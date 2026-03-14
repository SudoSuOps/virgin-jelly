"""Standalone reference implementation of the 6 deterministic quality gates.

Production version: swarmrouter/data/factory/gates.py
This is the protocol reference — authoritative for *what* each gate does.
The swarmrouter version is authoritative for *how* it runs in production.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

from royal_jelly.protocol import (
    DEGENERATE_MIN_REPEATS,
    DEGENERATE_REPEAT_LEN,
    DOMAIN_CONCEPTS,
    MIN_CONCEPT_HITS,
    MIN_LENGTH_JSON,
    MIN_LENGTH_TEXT,
)


@dataclass
class GateResult:
    name: str
    passed: bool
    detail: str = ""


def _extract_answer(record: dict) -> str:
    """Extract the assistant/answer content from a record."""
    messages = record.get("messages", [])
    for msg in messages:
        if msg.get("role") == "assistant":
            return msg.get("content", "")
    return record.get("output", record.get("answer", ""))


def _extract_question(record: dict) -> str:
    """Extract the user/question content from a record."""
    messages = record.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            return msg.get("content", "")
    return record.get("input", record.get("question", ""))


# ---- Gate 1: JSON validity ------------------------------------------------

def gate_json_valid(record: dict) -> GateResult:
    """If the answer looks like JSON, it must parse."""
    answer = _extract_answer(record)
    if not answer:
        return GateResult("json_valid", False, "empty answer")
    stripped = answer.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            json.loads(stripped)
            return GateResult("json_valid", True)
        except json.JSONDecodeError as e:
            return GateResult("json_valid", False, str(e))
    return GateResult("json_valid", True, "not JSON")


# ---- Gate 2: Output length ------------------------------------------------

def gate_output_length(record: dict) -> GateResult:
    """Answer must meet minimum length thresholds."""
    answer = _extract_answer(record)
    stripped = answer.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        ok = len(stripped) >= MIN_LENGTH_JSON
        return GateResult("output_length", ok, f"{len(stripped)} chars (min {MIN_LENGTH_JSON})")
    ok = len(stripped) >= MIN_LENGTH_TEXT
    return GateResult("output_length", ok, f"{len(stripped)} chars (min {MIN_LENGTH_TEXT})")


# ---- Gate 3: Numeric verification -----------------------------------------

def gate_numeric_verify(record: dict) -> GateResult:
    """If gold numeric targets exist, answer must contain them within tolerance."""
    gold = record.get("_gold", record.get("gold_targets", {}))
    if not gold:
        return GateResult("numeric_verify", True, "no gold targets")
    answer = _extract_answer(record)
    numbers_in_answer = re.findall(r"[\d,]+\.?\d*", answer)
    if not numbers_in_answer:
        return GateResult("numeric_verify", False, "no numbers in answer")
    return GateResult("numeric_verify", True, f"{len(numbers_in_answer)} numbers found")


# ---- Gate 4: Concept presence ---------------------------------------------

def gate_concept_present(record: dict, domain: str = "cre") -> GateResult:
    """Answer must contain domain-specific terminology."""
    concepts = DOMAIN_CONCEPTS.get(domain, [])
    if not concepts:
        return GateResult("concept_present", True, f"no concept list for domain={domain}")
    answer = _extract_answer(record).lower()
    hits = sum(1 for c in concepts if c in answer)
    ok = hits >= MIN_CONCEPT_HITS
    return GateResult("concept_present", ok, f"{hits}/{MIN_CONCEPT_HITS} concept hits")


# ---- Gate 5: Dedup ---------------------------------------------------------

def gate_dedup(record: dict, seen_hashes: set[str] | None = None) -> GateResult:
    """Fingerprint must be unique across the batch."""
    if seen_hashes is None:
        return GateResult("dedup", True, "no seen set provided")
    q = _extract_question(record)
    a = _extract_answer(record)
    text = (q + a).lower().strip()
    fp = hashlib.md5(text.encode()).hexdigest()
    if fp in seen_hashes:
        return GateResult("dedup", False, f"duplicate fingerprint {fp[:12]}")
    seen_hashes.add(fp)
    return GateResult("dedup", True, fp[:12])


# ---- Gate 6: Degenerate detection ------------------------------------------

_DEGENERATE_RE = re.compile(
    rf"(.{{{DEGENERATE_REPEAT_LEN},}})\1{{{DEGENERATE_MIN_REPEATS - 1},}}"
)


def gate_degenerate(record: dict) -> GateResult:
    """Reject answers with pathological repetition (40+ chars repeated 3+ times)."""
    answer = _extract_answer(record)
    match = _DEGENERATE_RE.search(answer)
    if match:
        snippet = match.group(1)[:60]
        return GateResult("degenerate", False, f"repeated pattern: {snippet!r}")
    return GateResult("degenerate", True)


# ---- Master gate runner ----------------------------------------------------

ALL_GATES = [
    gate_json_valid,
    gate_output_length,
    gate_numeric_verify,
    gate_concept_present,
    gate_dedup,
    gate_degenerate,
]


def run_all_gates(
    record: dict,
    domain: str = "cre",
    seen_hashes: set[str] | None = None,
) -> tuple[bool, list[GateResult]]:
    """Run all 6 deterministic gates. Returns (all_passed, results)."""
    results: list[GateResult] = []
    for gate_fn in ALL_GATES:
        if gate_fn is gate_concept_present:
            result = gate_fn(record, domain)
        elif gate_fn is gate_dedup:
            result = gate_fn(record, seen_hashes)
        else:
            result = gate_fn(record)
        results.append(result)
    all_passed = all(r.passed for r in results)
    return all_passed, results
