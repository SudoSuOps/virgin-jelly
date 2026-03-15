# Royal Jelly Protocol

The Royal Jelly Protocol defines how raw intelligence signals become bankable, on-chain-verified AI training data.

Models come and go. The data survives every generation. Royal Jelly is the data that teaches models to think — first-contact intelligence extracted directly from real-world sources, preserved with cryptographic provenance, graded by a deterministic scoring engine.

## Tier System

| Tier | Score | Description |
|------|-------|-------------|
| **Royal Jelly** | 95-100 | First-contact intelligence. On-chain provenance via Hedera. The moat. |
| **Honey** | 85-94 | Structured intelligence derived from signal. Production grade. |
| **Pollen** | 70-84 | Commodity knowledge. Useful but common. |
| **Propolis** | <70 | Below threshold. Defense material for self-healing pipelines. |

## JellyScore — How Data Earns Its Grade

Every intelligence cell is scored by a 5-component formula. Each component maps to a concrete computation:

```
JellyScore = (
    source_confidence    * 0.25    # How trustworthy is the source?
  + gate_integrity       * 0.30    # Did it pass all 6 quality gates?
  + reasoning_depth      * 0.20    # How deep is the analysis?
  + entropy_health       * 0.10    # Is the batch diverse (not degenerate)?
  + fingerprint_unique   * 0.15    # Is this cell unique?
) * 100
```

### Source Confidence (0.25)

Computed from the EntityScorer formula:

```
source_confidence =
    source_weight       * 0.40    # Worker trust level (EDGAR=0.9, Reddit=0.5)
  + entity_richness     * 0.25    # Named entities detected (cap at 10)
  + freshness           * 0.20    # Signal age decay (168-hour half-life)
  + cross_source        * 0.15    # Independent source confirmation count
```

Canonical source weights:

| Source | Weight | Why |
|--------|--------|-----|
| EDGAR (SEC filings) | 0.90 | Government-filed, machine-readable, timestamped |
| FRED (economic data) | 0.90 | Federal Reserve, authoritative |
| OpenAlex (research) | 0.85 | Peer-reviewed papers, DOI-tracked, real signal |
| Human-verified | 0.90 | Expert-curated |
| ULI (Urban Land) | 0.80 | Industry research body |
| CRE News | 0.65 | Journalistic, verified |
| RSS feeds | 0.60 | Mixed quality |
| HackerNews | 0.50 | Community-filtered |
| Reddit | 0.50 | Community, noisy |

### Gate Integrity (0.30)

Six deterministic gates — no LLM, no subjectivity:

1. **json_valid** — If output looks like JSON, it must parse
2. **output_length** — Minimum content length (20 chars JSON, 50 chars text)
3. **numeric_verify** — Gold numeric targets present within tolerance
4. **concept_present** — 2+ domain-specific terms detected
5. **dedup** — MD5 fingerprint unique across the batch
6. **degenerate** — No pathological repetition (40+ chars repeated 3+ times)

Gate pass rate = gates_passed / 6. This is the heaviest weight because gates are non-negotiable quality floors.

### The 7th Gate: Source-at-Fault (Adversarial)

What happens when the source itself is wrong? A restated EDGAR filing, a retracted paper, a corrected article.

The adversarial gate applies a **confidence penalty** (capped at 0.50) that degrades the JellyScore. Data still flows — it just lands in a lower tier. No data is rejected, only reclassified.

| Fault Type | Penalty | Markers |
|-----------|---------|---------|
| Retraction | 0.30 | "restatement", "retracted", "withdrawn" |
| Contradiction | 0.25 | "contrary to", "disputes", "revised downward" |
| Amendment | 0.15 | "10-K/A", "10-Q/A", "amended filing" |
| Staleness | 0.10 | Signal older than 365 days |

Penalties compound additively but cap at 0.50. A cell can never lose more than half its score from source faults.

## Bee Agents — The Intelligence Collectors

Every Bee follows the same lifecycle:

```
FETCH → COOK → GATE → SCORE → STAMP → ANCHOR → EMIT
  │       │       │       │        │       │        │
  │       │       │       │        │       │        └── Classified HiveCell
  │       │       │       │        │       └── Merkle + Hedera (royal_jelly only)
  │       │       │       │        └── HIVE-{DOM}-{hash12} cell ID
  │       │       │       └── JellyScore computation
  │       │       └── 6 deterministic gates + adversarial
  │       └── Signal → training pair (messages format)
  └── Raw data from source
```

Three Bee classes:
- **Scout Bee** — Wide search, many sources, lower depth
- **Worker Bee** — Deep extraction, single source, maximum fidelity
- **Auditor Bee** — Cross-validates other bees' output

## Hedera Anchoring — Proof of Signal

Two levels of on-chain provenance:

**Batch-level** (all tiers): Merkle root of all cell fingerprints published to HCS topic. Every cell in the batch is verifiable via inclusion proof. Cost: ~$0.0008 per batch.

**Cell-level PoSg** (Royal Jelly only): Individual cells scoring 95+ receive their own HCS certificate — a compact (<1024 byte) message with cell_id, jelly_score, fingerprint, and batch proof index. This is the strongest provenance guarantee: any cell can be independently verified against the Hedera ledger.

```json
{
  "type": "posg_cell",
  "cell_id": "HIVE-CRE-a7f3bc91e4d2",
  "jelly_score": 97.3,
  "tier": "royal_jelly",
  "fingerprint": "sha256[:32]",
  "batch_root": "merkle[:32]",
  "proof_index": 42,
  "ts": "2026-03-14T12:00:00Z",
  "v": "1.0"
}
```

## Temperature × Prompt Alignment — Critical Finding

**Date**: 2026-03-14 · **Model**: SwarmCurator-9B · **Domain**: Aviation (OpenAlex)

The single largest quality lever in the pipeline is the interaction between **inference temperature** and **prompt trajectory alignment**. This is not intuitive — temperature is usually treated as a minor knob. In the RJ pipeline, it's the difference between Pollen and Honey.

### The Data

| | Temp 0.7 (old) | Temp 0.05 (current) |
|---|---|---|
| **Avg JellyScore** | 77.2 | 85.9 |
| **Honey rate** | 0.7% (3/428) | 93.9% (706/752) |
| **Pollen** | 94.6% | 4.3% |
| **reasoning_depth** | ~0.75 | ~0.996 |
| **concept_present gate** | ~13% pass | ~96% pass |

Same model. Same papers. Same pipeline. The only changes: temperature 0.7 → 0.05, and prompts aligned to the JellyScore trajectory.

### Why Temperature Matters

The `reasoning_depth` scorer checks for 5 trajectory keywords (IDENTIFY, CALCULATE, ANALYZE, EVALUATE, RECOMMEND) plus causal connectors (because, therefore, if/then). The [cook-domain-prompts](https://github.com/SudoSuOps/cook-domian-prompts) library embeds all of these in every instruction.

At **temp 0.7**: The model paraphrases. "IDENTIFY" becomes "Let's look at." "CALCULATE" becomes "The numbers suggest." The scorer can't find the markers → `reasoning_depth` = 0.75 → Pollen.

At **temp 0.05** (greedy): The model follows the instruction literally. Every trajectory keyword appears verbatim. Every causal connector is present. `reasoning_depth` = 0.996 → Honey.

The `concept_present` gate shows the same pattern. The prompt says "Use domain terminology: aircraft, airspace, altitude, approach, clearance, maintenance, knots." At greedy temp, these exact terms appear. At higher temp, the model substitutes synonyms ("plane" for "aircraft", "height" for "altitude") → gate fails.

### The Rule

**For RJ-scored cooking, always use temperature 0.05.** The prompts are engineered to produce specific markers. Higher temperature defeats that engineering. This is not a creativity task — it's a compliance task. The model must emit what the scorer looks for.

### Prompt Architecture

Every domain prompt follows this structure (see [cook-domain-prompts](https://github.com/SudoSuOps/cook-domian-prompts)):

```
System: "You are a [domain expert]..." + RJ_SYSTEM_SUFFIX
  ↳ "Always structure responses using this trajectory:
     IDENTIFY → CALCULATE → ANALYZE → EVALUATE → RECOMMEND.
     Use precise numbers. Use causal language."

Instruction: "Analyze this [domain] research using the full 5-step trajectory:
  1. IDENTIFY [domain-specific focus]
  2. CALCULATE [domain-specific metrics] — show the math
  3. ANALYZE [causal reasoning] — use because/therefore/consequently
  4. EVALUATE [conditional reasoning] — use if/then/unless
  5. RECOMMEND [actionable output]
  Include [domain terminology list]."
```

The scorer checks for all of these markers deterministically. The prompt guarantees they appear. The temperature guarantees the prompt is followed literally.

**Bottom line: The prompt is the bottleneck, not the model. Temperature locks the prompt compliance.**

---

## Quick Start

```python
from royal_jelly import JellyScorer, HoneyTier

scorer = JellyScorer(domain="cre", source_weight=0.9)

pair = {
    "messages": [
        {"role": "user", "content": "What is the cap rate for this property?"},
        {"role": "assistant", "content": "Based on the NOI of $650,000 and..."},
    ]
}

result = scorer.score(pair)
print(result.score)       # 87.4
print(result.tier)        # HoneyTier.honey
print(result.cell_id)     # HIVE-CRE-a7f3bc91e4d2
print(result.gates.gates_passed)  # 6
```

### Reference Bee Agent

```python
from royal_jelly.agents.bee_cre_edgar import BeeCREEdgar

bee = BeeCREEdgar(dry_run=True)
cells = bee.process()

for cell in cells:
    print(f"{cell.cell_id}: {cell.grade} ({cell.jelly_score.score})")
```

## Docs

The protocol whitepapers are in [`docs/`](docs/):

- [Royal Jelly Thesis](docs/ROYAL_JELLY_THESIS.md) — Why real-signal data is the scarcest asset in AI
- [Royal Jelly Protocol (RJP-1)](docs/ROYAL_JELLY_PROTOCOL.md) — The 5-gate verification framework
- [Proof of Signal](docs/PROOF_OF_SIGNAL.md) — Cryptographic attestation for training data provenance
- [Signal Mining Network](docs/SIGNAL_MINING_NETWORK.md) — 100 agents as intelligence miners
- [Bee Agent Architecture](docs/BEE_AGENT_ARCHITECTURE.md) — 7-module agent pipeline

## License

MIT
