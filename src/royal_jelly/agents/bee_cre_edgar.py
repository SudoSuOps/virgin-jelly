"""Bee-CRE-EDGAR — reference Bee agent wrapping the EDGAR signal worker.

This is the reference implementation of a production Bee agent. It
demonstrates the full Royal Jelly lifecycle applied to SEC EDGAR filings
(10-K, 10-Q, 8-K) from REITs.

EDGAR filings earn SOURCE_WEIGHT = 0.9 — the highest trust level for
automated sources. Regulatory filings are first-contact intelligence:
filed directly with the SEC, machine-readable (XBRL), and time-stamped
by a government agency.

Production version: swarmrouter/signal/workers/worker_edgar.py
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from royal_jelly.agents.base_bee import BaseBee
from royal_jelly.models.signal import SignalOrigin

# REIT tickers tracked by the EDGAR worker
REIT_TICKERS = [
    "PLD",   # Prologis — industrial REIT
    "DRE",   # Duke Realty
    "REXR",  # Rexford Industrial
    "STAG",  # STAG Industrial
    "FR",    # First Industrial
    "EGP",   # EastGroup Properties
    "TRNO",  # Terreno Realty
    "COLD",  # Americold — cold storage REIT
    "PSA",   # Public Storage
    "EXR",   # Extra Space Storage
    "DLR",   # Digital Realty — data center
    "EQIX",  # Equinix — data center
    "AMT",   # American Tower
    "SPG",   # Simon Property Group — retail
    "O",     # Realty Income — STNL
]

# SEC EDGAR API base
EDGAR_API = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
EDGAR_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"


class BeeCREEdgar(BaseBee):
    """Reference Bee-CRE agent for SEC EDGAR REIT filings.

    Lifecycle:
        1. FETCH   — Pull recent filings from EDGAR submissions API
        2. COOK    — Transform filing metadata + XBRL facts into messages-format pair
        3. GATE    — 6 deterministic gates (via JellyScorer)
        4. SCORE   — JellyScore with source_weight=0.9
        5. STAMP   — HiveCell with HIVE-CRE-{fingerprint}
        6. ANCHOR  — (optional) Merkle + Hedera PoSg for royal_jelly tier
        7. EMIT    — Classified cell ready for ledger registration
    """

    WORKER_NAME = "bee_cre_edgar"
    SOURCE_WEIGHT = 0.9
    DOMAIN = "cre"

    def __init__(self, tickers: list[str] | None = None, dry_run: bool = False):
        super().__init__(dry_run=dry_run)
        self.tickers = tickers or REIT_TICKERS

    def fetch(self) -> list[dict]:
        """Fetch recent filings from SEC EDGAR.

        In the reference implementation, this returns mock data demonstrating
        the expected schema. Production implementations should use the EDGAR
        submissions API with proper User-Agent headers.
        """
        if self.dry_run:
            return [self._mock_filing()]

        # Production: iterate tickers, call EDGAR API, extract recent filings
        # This reference implementation delegates to the mock for portability
        return [self._mock_filing()]

    def cook(self, raw: dict) -> dict | None:
        """Transform an EDGAR filing into a training pair.

        Generates a CRE analysis prompt + response from the filing data,
        producing a messages-format pair suitable for model training.
        """
        ticker = raw.get("ticker", "UNKNOWN")
        form = raw.get("form", "10-K")
        period = raw.get("period", "")
        facts = raw.get("xbrl_facts", {})

        # Build analysis prompt from filing metadata
        question = (
            f"Analyze the {form} filing for {ticker} "
            f"(period ending {period}). "
            f"Evaluate the REIT's financial health based on the reported metrics."
        )

        # Build structured response from XBRL facts
        metrics = []
        for fact_name, value in facts.items():
            metrics.append(f"- {fact_name}: {value}")
        metrics_text = "\n".join(metrics) if metrics else "No XBRL facts available."

        answer = (
            f"## {ticker} — {form} Analysis (Period: {period})\n\n"
            f"### Key Metrics\n{metrics_text}\n\n"
            f"### Assessment\n"
            f"Based on the reported financials, this filing shows "
            f"the REIT's operational performance for the period. "
            f"The metrics should be evaluated against sector benchmarks "
            f"and prior period performance to identify trends.\n\n"
            f"### Risk Factors\n"
            f"Investors should review management discussion and analysis (MD&A) "
            f"for forward-looking statements and identified risk factors. "
            f"Key areas: occupancy trends, lease expirations, debt maturity schedule, "
            f"and capital expenditure plans.\n\n"
            f"Source: SEC EDGAR {form} filing, CIK {raw.get('cik', 'N/A')}"
        )

        return {
            "messages": [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ]
        }

    def make_signal(self, raw: dict) -> SignalOrigin:
        """Build SignalOrigin from an EDGAR filing record."""
        title = f"{raw.get('ticker', '')}_{raw.get('form', '')}_{raw.get('period', '')}"
        dedup_key = hashlib.md5(title.lower().encode()).hexdigest()

        filed_at = raw.get("filed_at")
        if isinstance(filed_at, str):
            filed_at = datetime.fromisoformat(filed_at)
        if filed_at is None:
            filed_at = datetime.now(timezone.utc)

        return SignalOrigin(
            source_worker=self.WORKER_NAME,
            source_url=raw.get("url", f"https://sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={raw.get('cik', '')}"),
            source_weight=self.SOURCE_WEIGHT,
            collected_at=filed_at,
            dedup_key=dedup_key,
            domain=self.DOMAIN,
            signal_type="filing",
            priority=2,
            entities=[raw.get("ticker", ""), raw.get("company", "")],
            metadata={"form": raw.get("form", ""), "cik": raw.get("cik", "")},
        )

    @staticmethod
    def _mock_filing() -> dict[str, Any]:
        """Return a mock EDGAR filing for testing the full Bee lifecycle."""
        return {
            "ticker": "PLD",
            "company": "Prologis Inc",
            "cik": "0001045609",
            "form": "10-K",
            "period": "2025-12-31",
            "filed_at": "2026-02-28T16:00:00Z",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001045609",
            "xbrl_facts": {
                "Revenue": "$8.02B",
                "NOI": "$6.31B",
                "FFO_per_share": "$5.62",
                "Occupancy": "97.2%",
                "Total_Assets": "$93.4B",
                "Total_Debt": "$28.7B",
                "LTV": "30.7%",
                "DSCR": "4.8x",
                "Cap_Rate_Implied": "4.2%",
                "Lease_Expirations_2026": "8.3%",
                "Development_Pipeline": "$4.1B",
                "Same_Store_NOI_Growth": "7.8%",
            },
            "task_type": "financial_analysis",
            "gen_model": "bee_cre_edgar_v1",
        }
