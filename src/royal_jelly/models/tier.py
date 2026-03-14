"""Royal Jelly tier system — 4 tiers mapped to score thresholds."""

from enum import Enum

from royal_jelly.protocol import TIER_THRESHOLDS


class HoneyTier(str, Enum):
    """The four tiers of the Royal Jelly Protocol.

    royal_jelly  (95-100)  First-contact intelligence, on-chain provenance.
    honey        (85-94)   Structured intelligence derived from signal.
    pollen       (70-84)   Commodity knowledge, useful but common.
    propolis     (<70)     Below threshold — defense material for self-healing.
    """

    royal_jelly = "royal_jelly"
    honey = "honey"
    pollen = "pollen"
    propolis = "propolis"


_TIER_MAP = {name: HoneyTier(name) for _, name in TIER_THRESHOLDS}


def tier_from_score(score: float) -> HoneyTier:
    """Map a 0-100 JellyScore to a tier."""
    for threshold, name in TIER_THRESHOLDS:
        if score >= threshold:
            return _TIER_MAP[name]
    return HoneyTier.propolis
