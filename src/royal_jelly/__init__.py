"""Royal Jelly Protocol — intelligence grading, provenance, and verification for AI training data."""

from royal_jelly.models.tier import HoneyTier, tier_from_score
from royal_jelly.scoring.jelly_score import JellyScorer

__version__ = "0.1.0"
__all__ = ["HoneyTier", "tier_from_score", "JellyScorer"]
