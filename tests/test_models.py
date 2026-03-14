"""Tests for Royal Jelly Pydantic models — round-trip, validation, constraints."""

import pytest
from datetime import datetime, timezone

from royal_jelly.models.tier import HoneyTier, tier_from_score
from royal_jelly.models.signal import SignalOrigin
from royal_jelly.models.score import (
    GateResults, ScoreComponents, AdversarialResult, JellyScoreResult,
)
from royal_jelly.models.cell import HiveCell, CellLineage
from royal_jelly.models.provenance import (
    MerkleProof, HederaAnchor, QualityGuarantee, PoSgCellAnchor,
)


# -- Tier tests --

class TestTierFromScore:
    def test_royal_jelly(self):
        assert tier_from_score(100.0) == HoneyTier.royal_jelly
        assert tier_from_score(95.0) == HoneyTier.royal_jelly

    def test_honey(self):
        assert tier_from_score(94.9) == HoneyTier.honey
        assert tier_from_score(85.0) == HoneyTier.honey

    def test_pollen(self):
        assert tier_from_score(84.9) == HoneyTier.pollen
        assert tier_from_score(70.0) == HoneyTier.pollen

    def test_propolis(self):
        assert tier_from_score(69.9) == HoneyTier.propolis
        assert tier_from_score(0.0) == HoneyTier.propolis

    def test_boundary_exact(self):
        assert tier_from_score(95) == HoneyTier.royal_jelly
        assert tier_from_score(85) == HoneyTier.honey
        assert tier_from_score(70) == HoneyTier.pollen


# -- Signal tests --

class TestSignalOrigin:
    def test_round_trip(self):
        sig = SignalOrigin(
            source_worker="edgar",
            source_url="https://sec.gov/filing/123",
            source_weight=0.9,
            collected_at=datetime(2026, 3, 14, tzinfo=timezone.utc),
            dedup_key="abc123",
            domain="cre",
            signal_type="filing",
            priority=2,
            entities=["PLD", "Prologis"],
        )
        data = sig.model_dump()
        restored = SignalOrigin.model_validate(data)
        assert restored.source_worker == "edgar"
        assert restored.source_weight == 0.9
        assert restored.entities == ["PLD", "Prologis"]

    def test_invalid_priority(self):
        with pytest.raises(Exception):
            SignalOrigin(
                source_worker="test",
                source_url="http://test",
                source_weight=0.5,
                collected_at=datetime.now(timezone.utc),
                dedup_key="x",
                domain="cre",
                signal_type="test",
                priority=10,  # Out of range
            )

    def test_invalid_weight(self):
        with pytest.raises(Exception):
            SignalOrigin(
                source_worker="test",
                source_url="http://test",
                source_weight=1.5,  # Out of range
                collected_at=datetime.now(timezone.utc),
                dedup_key="x",
                domain="cre",
                signal_type="test",
                priority=3,
            )


# -- Score model tests --

class TestGateResults:
    def test_all_pass(self):
        g = GateResults()
        assert g.gates_passed == 6
        assert g.gate_pass_rate == 1.0

    def test_one_fail(self):
        g = GateResults(dedup=False)
        assert g.gates_passed == 5
        assert abs(g.gate_pass_rate - 5 / 6) < 0.001

    def test_all_fail(self):
        g = GateResults(
            json_valid=False, output_length=False, numeric_verify=False,
            concept_present=False, dedup=False, degenerate=False,
        )
        assert g.gates_passed == 0
        assert g.gate_pass_rate == 0.0


class TestAdversarialResult:
    def test_no_fault(self):
        a = AdversarialResult()
        assert a.source_fault_detected is False
        assert a.confidence_penalty == 0.0

    def test_penalty_cap(self):
        with pytest.raises(Exception):
            AdversarialResult(confidence_penalty=0.6)  # Over 0.5 cap


# -- Cell tests --

class TestHiveCell:
    def test_valid_cell(self):
        cell = HiveCell(
            cell_id="HIVE-CRE-a7f3bc91e4d2",
            domain="cre",
            grade="royal_jelly",
            messages=[
                {"role": "user", "content": "What is NOI?"},
                {"role": "assistant", "content": "Net Operating Income is..."},
            ],
            fingerprint="a" * 64,
        )
        assert cell.domain == "cre"
        assert cell.grade == "royal_jelly"

    def test_invalid_cell_id(self):
        with pytest.raises(Exception):
            HiveCell(
                cell_id="BAD-FORMAT",
                domain="cre",
                grade="honey",
                messages=[],
                fingerprint="x" * 64,
            )

    def test_json_round_trip(self):
        cell = HiveCell(
            cell_id="HIVE-AVI-123456789012",
            domain="aviation",
            grade="honey",
            messages=[
                {"role": "user", "content": "Explain METAR"},
                {"role": "assistant", "content": "METAR is a weather report format..."},
            ],
            fingerprint="b" * 64,
            task_type="weather",
        )
        json_str = cell.model_dump_json()
        restored = HiveCell.model_validate_json(json_str)
        assert restored.cell_id == cell.cell_id
        assert restored.task_type == "weather"


# -- Provenance tests --

class TestMerkleProof:
    def test_round_trip(self):
        proof = MerkleProof(
            leaf_hash="a" * 64,
            proof=[
                {"hash": "b" * 64, "side": "right"},
                {"hash": "c" * 64, "side": "left"},
            ],
            root="d" * 64,
        )
        data = proof.model_dump()
        restored = MerkleProof.model_validate(data)
        assert len(restored.proof) == 2


class TestPoSgCellAnchor:
    def test_valid_anchor(self):
        anchor = PoSgCellAnchor(
            cell_id="HIVE-CRE-a7f3bc91e4d2",
            cell_fingerprint="a" * 64,
            jelly_score=97.3,
        )
        assert anchor.tier == "royal_jelly"

    def test_below_threshold(self):
        with pytest.raises(Exception):
            PoSgCellAnchor(
                cell_id="HIVE-CRE-a7f3bc91e4d2",
                cell_fingerprint="a" * 64,
                jelly_score=80.0,  # Below 95 threshold
            )
