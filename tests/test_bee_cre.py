"""Tests for the reference Bee-CRE-EDGAR agent."""

from royal_jelly.agents.bee_cre_edgar import BeeCREEdgar, REIT_TICKERS
from royal_jelly.models.cell import HiveCell
from royal_jelly.models.tier import HoneyTier


class TestBeeCREEdgar:

    def test_mock_lifecycle(self):
        """Full Bee lifecycle with mock EDGAR data → produces HiveCell."""
        bee = BeeCREEdgar(dry_run=True)
        cells = bee.process()

        assert len(cells) >= 1
        cell = cells[0]

        # Cell structure
        assert isinstance(cell, HiveCell)
        assert cell.cell_id.startswith("HIVE-CRE-")
        assert cell.domain == "cre"
        assert cell.grade in ["royal_jelly", "honey", "pollen", "propolis"]

        # Messages format
        assert len(cell.messages) == 2
        assert cell.messages[0]["role"] == "user"
        assert cell.messages[1]["role"] == "assistant"
        assert "PLD" in cell.messages[0]["content"]

        # JellyScore attached
        assert cell.jelly_score is not None
        assert cell.jelly_score.score > 0
        assert cell.jelly_score.gates.gates_passed == 6

        # Fingerprint
        assert len(cell.fingerprint) == 64

    def test_stats_tracking(self):
        """Bee should track processing statistics."""
        bee = BeeCREEdgar(dry_run=True)
        bee.process()
        stats = bee.stats
        assert stats["fetched"] >= 1
        assert stats["cooked"] >= 1
        assert stats["emitted"] >= 1

    def test_reit_tickers(self):
        """REIT ticker list should include key industrial names."""
        assert "PLD" in REIT_TICKERS   # Prologis
        assert "COLD" in REIT_TICKERS  # Americold
        assert "O" in REIT_TICKERS     # Realty Income

    def test_source_weight(self):
        """EDGAR bee should carry 0.9 source weight — regulatory filings."""
        bee = BeeCREEdgar(dry_run=True)
        assert bee.SOURCE_WEIGHT == 0.9
        assert bee.DOMAIN == "cre"

    def test_mock_filing_has_xbrl(self):
        """Mock filing should include XBRL facts for realistic testing."""
        filing = BeeCREEdgar._mock_filing()
        assert "xbrl_facts" in filing
        facts = filing["xbrl_facts"]
        assert "NOI" in facts
        assert "Cap_Rate_Implied" in facts
        assert "Occupancy" in facts
        assert "LTV" in facts
        assert "DSCR" in facts

    def test_cook_output_format(self):
        """Cook should produce messages-format pair."""
        bee = BeeCREEdgar(dry_run=True)
        filing = BeeCREEdgar._mock_filing()
        pair = bee.cook(filing)
        assert pair is not None
        assert "messages" in pair
        assert len(pair["messages"]) == 2
        assert pair["messages"][0]["role"] == "user"
        assert pair["messages"][1]["role"] == "assistant"
        # Content should reference the ticker and filing type
        assert "PLD" in pair["messages"][0]["content"]
        assert "10-K" in pair["messages"][0]["content"]
