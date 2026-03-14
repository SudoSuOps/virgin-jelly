"""Royal Jelly Protocol — top-level constants and configuration."""

# ---------------------------------------------------------------------------
# JellyScore component weights
# ---------------------------------------------------------------------------
# Each weight maps to a concrete scoring function in swarmrouter.
#
#   source_confidence  → signal/scorer.py   EntityScorer formula
#   gate_integrity     → data/factory/gates.py   6 deterministic gates
#   reasoning_depth    → data/difficulty_scorer.py   DifficultyProfile
#   entropy_health     → data/factory/entropy.py   batch health score
#   fingerprint_unique → data/factory/merkle.py   SHA-256 uniqueness
#
JELLY_WEIGHTS = {
    "source_confidence": 0.25,
    "gate_integrity": 0.30,
    "reasoning_depth": 0.20,
    "entropy_health": 0.10,
    "fingerprint_uniqueness": 0.15,
}

# ---------------------------------------------------------------------------
# Tier thresholds (0-100 scale)
# ---------------------------------------------------------------------------
TIER_THRESHOLDS = [
    (95, "royal_jelly"),
    (85, "honey"),
    (70, "pollen"),
    (0, "propolis"),
]

# ---------------------------------------------------------------------------
# Source weights — canonical trust per worker type
# ---------------------------------------------------------------------------
# Regulatory filings and human-verified data earn the highest trust.
SOURCE_WEIGHTS = {
    "edgar": 0.9,
    "fred": 0.9,
    "human": 0.9,
    "openalex": 0.85,
    "arxiv": 0.80,
    "uli": 0.8,
    "zenodo": 0.78,
    "github": 0.72,
    "cre_news": 0.65,
    "rss": 0.6,
    "webhook": 0.6,
    "hn": 0.5,
    "reddit": 0.5,
    "trending": 0.4,
}

# ---------------------------------------------------------------------------
# Gate configuration
# ---------------------------------------------------------------------------
MIN_LENGTH_JSON = 20
MIN_LENGTH_TEXT = 50
MIN_CONCEPT_HITS = 2
DEGENERATE_REPEAT_LEN = 40
DEGENERATE_MIN_REPEATS = 3

# ---------------------------------------------------------------------------
# Adversarial gate
# ---------------------------------------------------------------------------
ADVERSARIAL_PENALTY_CAP = 0.50
STALENESS_THRESHOLD_DAYS = 365

# ---------------------------------------------------------------------------
# Domain concept dictionaries (subset — full lists in swarmrouter)
# ---------------------------------------------------------------------------
DOMAIN_CONCEPTS = {
    "cre": [
        "noi", "cap rate", "dscr", "ltv", "rent", "lease", "tenant",
        "occupancy", "vacancy", "underwriting", "proforma", "escrow",
        "due diligence", "appraisal", "zoning", "square feet", "psf",
    ],
    "medical": [
        "patient", "diagnosis", "treatment", "dosage", "clinical",
        "contraindication", "adverse", "protocol", "trial", "endpoint",
        "biomarker", "cohort", "efficacy", "pathology", "therapeutic",
    ],
    "aviation": [
        "aircraft", "runway", "faa", "maintenance", "airspace",
        "atc", "metar", "ifr", "vfr", "approach", "clearance",
        "turbine", "flap", "altitude", "knots",
    ],
    "ai": [
        "model", "training", "inference", "benchmark", "dataset",
        "transformer", "attention", "embedding", "parameter", "fine-tune",
        "accuracy", "loss", "gradient", "architecture", "encoder",
        "decoder", "token", "latent", "representation", "evaluation",
        "baseline", "ablation", "performance", "framework", "pipeline",
    ],
    "economic": [
        "gdp", "inflation", "interest rate", "unemployment", "yield",
        "monetary", "fiscal", "deficit", "surplus", "fed", "treasury",
        "cpi", "pce", "employment", "recession", "growth",
    ],
    "energy": [
        "solar", "battery", "renewable", "grid", "power", "electricity",
        "emission", "carbon", "megawatt", "capacity", "generation",
        "turbine", "photovoltaic", "efficiency", "storage", "kwh",
    ],
    "climate": [
        "temperature", "emission", "carbon", "greenhouse", "warming",
        "sea level", "precipitation", "drought", "permafrost", "ice",
        "deforestation", "ecosystem", "biodiversity", "sustainability",
    ],
    "crypto": [
        "blockchain", "token", "smart contract", "consensus", "hash",
        "wallet", "defi", "liquidity", "staking", "validator",
        "protocol", "transaction", "decentralized", "ledger",
    ],
    "legal": [
        "statute", "regulation", "compliance", "court", "filing",
        "jurisdiction", "liability", "precedent", "enforcement",
        "legislation", "amendment", "ruling", "arbitration",
    ],
    "finance": [
        "revenue", "earnings", "eps", "margin", "guidance", "valuation",
        "dividend", "equity", "debt", "balance sheet", "cash flow",
        "income statement", "quarterly", "annual", "profit", "loss",
        "shareholder", "acquisition", "merger", "ipo", "underwriter",
    ],
    "software": [
        "api", "deployment", "latency", "throughput", "microservice",
        "container", "kubernetes", "database", "ci/cd", "repository",
        "dependency", "runtime", "scalability", "middleware", "endpoint",
        "refactor", "migration", "architecture", "backend", "frontend",
    ],
    "supply_chain": [
        "logistics", "inventory", "procurement", "warehouse", "fulfillment",
        "tariff", "freight", "supplier", "lead time", "demand forecast",
        "distribution", "manufacturing", "customs", "shipping", "sourcing",
        "disruption", "resilience", "just-in-time", "backlog",
    ],
    "patents": [
        "claim", "prior art", "specification", "embodiment", "apparatus",
        "method", "assignee", "patent office", "filing date", "priority",
        "novelty", "inventive step", "prosecution", "examiner", "grant",
        "infringement", "licensing", "continuation", "provisional",
    ],
}
