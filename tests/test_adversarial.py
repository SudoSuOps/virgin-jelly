"""Tests for the source-at-fault adversarial gate."""

from datetime import datetime, timedelta, timezone

from royal_jelly.models.signal import SignalOrigin
from royal_jelly.scoring.adversarial import SourceFaultDetector


def _make_signal(url: str = "https://test.com", age_days: int = 0, **kwargs) -> SignalOrigin:
    collected = datetime.now(timezone.utc) - timedelta(days=age_days)
    defaults = dict(
        source_worker="test",
        source_url=url,
        source_weight=0.9,
        collected_at=collected,
        dedup_key="test",
        domain="cre",
        signal_type="filing",
        priority=2,
    )
    defaults.update(kwargs)
    return SignalOrigin(**defaults)


class TestSourceFaultDetector:

    def setup_method(self):
        self.detector = SourceFaultDetector()

    def test_clean_signal(self):
        """No fault markers → no penalty."""
        signal = _make_signal()
        result = self.detector.detect(signal, "Normal filing content about NOI and cap rates.")
        assert result.source_fault_detected is False
        assert result.confidence_penalty == 0.0

    def test_retraction_marker(self):
        """Content with retraction marker → 0.30 penalty."""
        signal = _make_signal()
        result = self.detector.detect(signal, "This filing was retracted due to accounting errors.")
        assert result.source_fault_detected is True
        assert result.confidence_penalty == 0.30
        assert "retraction" in result.fault_type

    def test_amendment_marker_in_url(self):
        """Amendment filing type in URL → 0.15 penalty."""
        signal = _make_signal(url="https://sec.gov/filing/10-K/A/2026")
        result = self.detector.detect(signal, "Amended annual report showing revised figures.")
        assert result.source_fault_detected is True
        assert result.confidence_penalty >= 0.15
        assert "amendment" in result.fault_type

    def test_contradiction_marker(self):
        """Contradiction in content → 0.25 penalty."""
        signal = _make_signal()
        result = self.detector.detect(
            signal,
            "These figures are contrary to what was previously reported."
        )
        assert result.source_fault_detected is True
        assert result.confidence_penalty == 0.25
        assert "contradiction" in result.fault_type

    def test_staleness(self):
        """Signal older than 365 days → 0.10 penalty."""
        signal = _make_signal(age_days=400)
        result = self.detector.detect(signal, "Normal content.")
        assert result.source_fault_detected is True
        assert result.confidence_penalty == 0.10
        assert "stale" in result.fault_type

    def test_compound_penalties(self):
        """Multiple faults compound additively."""
        signal = _make_signal(url="https://sec.gov/10-K/A", age_days=400)
        result = self.detector.detect(
            signal,
            "The restated filing contradicts prior reports."
        )
        assert result.source_fault_detected is True
        # retraction(0.30) + amendment(0.15) + stale(0.10) = 0.55 → capped at 0.50
        assert result.confidence_penalty <= 0.50

    def test_penalty_cap_at_050(self):
        """Compound penalties must never exceed 0.50."""
        signal = _make_signal(url="https://sec.gov/10-K/A", age_days=500)
        result = self.detector.detect(
            signal,
            "This retracted filing is contrary to the amended submission."
        )
        assert result.confidence_penalty <= 0.50

    def test_evidence_trail(self):
        """Evidence should explain what triggered the fault."""
        signal = _make_signal()
        result = self.detector.detect(signal, "The report was withdrawn from publication.")
        assert "retraction marker" in result.evidence
        assert "'withdrawn'" in result.evidence

    def test_fresh_signal_no_stale_penalty(self):
        """A signal from today should not get a staleness penalty."""
        signal = _make_signal(age_days=0)
        result = self.detector.detect(signal, "Fresh filing content.")
        assert result.source_fault_detected is False
