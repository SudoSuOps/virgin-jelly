# Bee Agent Architecture

*Turn the bees into a real collector architecture instead of just a metaphor.*

A swarm of agents that can:

- Crawl real sources
- Detect signal, not noise
- Normalize it into hive cells
- Score it for Jelly vs Honey
- Coordinate so bees do not duplicate work
- Feed the vault continuously

**Bee = domain sensor + extractor + verifier-prep node**

## High-Level Pipeline

```
SOURCE → SCOUT → EXTRACTOR → FILTER → NORMALIZER → PROVENANCE → HIVE BUS → SWARMJUDGE → VAULT
```

Each Bee is not one giant agent. It is a small pipeline of components.

---

## 1. The 7 Bee Modules

### Module 1 — Scout

Finds candidate signal in the wild.

**Responsibilities:**
- Poll sources
- Watch feeds
- Detect changes
- Fetch raw documents
- Compute raw hashes
- Assign source confidence

**Inputs:** URLs, feeds, APIs, file drops, sensor logs

**Outputs:** raw payload, source metadata, fetch timestamp, content hash

Think of Scout as the forager.

---

### Module 2 — Extractor

Pulls structure from raw material without adding opinion.

**Responsibilities:**
- Parse document
- Identify entities
- Identify dates
- Identify event types
- Identify numeric facts
- Detect source type

**Outputs:** structured event draft, entity list, fact list, source anchors

**Important:** This stage stays close to first-contact reality. No long reasoning yet.

---

### Module 3 — Filter

Separates signal from noise.

**Responsibilities:**
- Dedupe near-identical events
- Reject low-information items
- Reject weak/unclear sources
- Novelty scoring
- Relevance scoring
- Urgency scoring

**Outputs:** keep / reject / hold, novelty score, relevance score, noise score

This is where you stop the hive from filling with junk.

---

### Module 4 — Normalizer

Converts extracted signal into a stable hive schema.

**Responsibilities:**
- Map events to taxonomy
- Standardize entities
- Standardize units
- Standardize timestamps
- Standardize domains
- Create canonical cell form

**Outputs:** candidate hive cell

Critical because the hive needs uniform cells.

---

### Module 5 — Provenance Attestor

Builds the chain of custody.

**Responsibilities:**
- Record exact origin
- Store raw hash
- Store normalized hash
- Store collection method
- Store Bee identity
- Store source lineage
- Detect whether content looks synthetic or derivative

**Outputs:** provenance record, proof-of-signal preimage

This is what protects virgin Jelly.

---

### Module 6 — Coordinator

Communicates with the rest of the swarm.

**Responsibilities:**
- Avoid duplicate crawling
- Lease source territories
- Assign collection windows
- Share entity watchlists
- Report hot signals
- Escalate anomalies

**Outputs:** task claims, swarm notices, domain handoffs

This is what makes many bees act like one hive.

---

### Module 7 — Hive Submitter

Sends validated candidates into the shared system.

**Responsibilities:**
- Publish candidate cell
- Attach metadata
- Attach provenance
- Attach scores
- Route to SwarmJudge
- Persist retry-safe queue entries

**Outputs:** candidate for grading, queue event, audit trail

---

## 2. The Bee Lifecycle

Every Bee runs this loop:

```
discover → fetch → parse → extract → score → normalize → attest → publish → sleep / repeat
```

The natural bee loop:

```
scout nectar → test nectar → return to hive → deposit nectar → hive processes
```

---

## 3. The Three Bee Classes

Not all bees do the same job.

### A. Scout Bees

Fast, wide, light.

**Best for:** watching many sources, detecting new documents, spotting anomalies, generating fetch candidates

They do not do heavy processing.

**They answer:** *"Is there something worth looking at?"*

### B. Worker Bees

Deeper extraction and structuring.

**Best for:** entity extraction, event parsing, schema normalization, provenance packaging

**They answer:** *"What exactly happened?"*

### C. Auditor Bees

Secondary validation before SwarmJudge.

**Best for:** duplicate detection, contradiction scan, source trust checks, synthetic contamination checks

**They answer:** *"Is this clean enough for the hive?"*

---

## 4. Domain-Specific Bees

This is where the moat really starts.

### Bee-CRE

**Sources:** SEC filings, FDIC bulletins, CMBS servicer data, assessor records, zoning changes, lender notices

**Event types:** loan distress, refi pressure, sales comps, cap rate shifts, tax events

### Bee-Med

**Sources:** PubMed, FDA, CMS, clinical guidelines, hospital ops data, imaging workflows

**Event types:** reimbursement changes, device approvals, treatment shifts, adverse events

### Bee-Aero

**Sources:** FAA, NTSB, NOTAM, weather feeds, incident logs, fleet maintenance bulletins

**Event types:** incident reports, route disruption, airworthiness updates, weather-risk events

### Bee-Legal

**Sources:** court opinions, agency rules, enforcement actions, public comment notices, compliance bulletins

**Event types:** regulatory shifts, new precedent, enforcement patterns

Each domain Bee has:
- Its own taxonomy
- Source map
- Entity ontology
- Scoring weights

---

## 5. The Core Hive Cell Schema

Every Bee emits the same base envelope.

```json
{
  "cell_id": "candidate_uuid",
  "domain": "cre",
  "bee_id": "bee_cre_07",
  "source_type": "regulatory_filing",
  "source_ref": "fdic_bulletin_2026_03_14_abc",
  "collected_at": "2026-03-14T14:08:11Z",
  "raw_hash": "sha256:...",
  "normalized_hash": "sha256:...",
  "event_type": "credit_tightening",
  "entities": [
    {"type": "institution", "value": "regional_bank"},
    {"type": "asset_class", "value": "office_property"}
  ],
  "facts": [
    {"field": "ltv_policy_change", "value": "tightened"},
    {"field": "market_region", "value": "sunbelt"}
  ],
  "novelty_score": 0.88,
  "relevance_score": 0.91,
  "source_confidence": 0.95,
  "synthetic_risk": 0.03,
  "candidate_grade": "jelly_candidate"
}
```

That envelope is the common language of the hive.

---

## 6. How Bees Avoid Noise

### Noise Control Layer 1 — Source Trust

Every source gets a trust profile:

| Trust Level | Description |
|-------------|-------------|
| primary | Direct filings, sensor data, government records |
| secondary | Verified reporting on primary sources |
| derivative | Summaries, aggregations, commentary |
| unknown | Unverified origin |

Primary sources are preferred for Jelly.

### Noise Control Layer 2 — Novelty Scoring

If 50 articles repeat the same event, only the earliest primary-source capture matters.

Methods:
- Semantic dedupe
- Entity overlap
- Timestamp proximity
- Hash or fingerprint matching

### Noise Control Layer 3 — Event Significance

Not all signals deserve vault space. Weighted checks:

- Does it affect a tracked entity?
- Does it change a state?
- Does it move money, policy, risk, safety, regulation, or operations?
- Is there measurable downstream impact?

### Noise Control Layer 4 — Contamination Detection

Downgrade or reject content that appears:

- Rewritten by LLMs
- Copied from summaries
- Overly derivative
- Citation-free synthetic prose

That protects virgin Jelly.

---

## 7. How Bees Coordinate Across the Swarm

### Territory Leasing

Each Bee temporarily claims a source or partition.

```
Bee-CRE-02 claims EDGAR REIT filings for 10 minutes
Bee-Med-01 claims new PubMed oncology abstracts
```

### Entity Watchlists

The hive publishes priority entities: companies, agencies, geographies, facilities, asset classes, policy topics. Bees boost those targets.

### Event Broadcast

When a Bee finds a high-signal event, it publishes:

- Event summary
- Entity list
- Urgency
- Suggested follow-up domains

Neighboring bees investigate supporting evidence.

**Example:** Bee-Fin spots lender tightening → Bee-CRE and Bee-Legal get pinged.

### Handoff Protocol

Sometimes one Bee discovers something better suited for another domain.

**Example:** Bee-Signal detects new hospital reimbursement rule → hands off to Bee-Med for deep capture.

Critical for swarm efficiency.

---

## 8. Bee Pre-Scoring

Before SwarmJudge, each Bee creates a pre-score.

```
CandidateScore =
  0.30 × source_confidence
+ 0.25 × novelty
+ 0.20 × relevance
+ 0.15 × provenance_completeness
+ 0.10 × contamination_cleanliness
```

**Routing by threshold:**

| Score | Route |
|-------|-------|
| 0.85+ | Jelly candidate |
| 0.65–0.84 | Honey candidate |
| < 0.65 | Reject or archive |

Keeps SwarmJudge focused on the strongest material.

---

## 9. Software Design

Microservice-style implementation.

### Services

| Service | Role |
|---------|------|
| bee-scout | Source discovery and monitoring |
| bee-fetcher | Raw document retrieval |
| bee-extractor | Entity and event extraction |
| bee-filter | Noise rejection and scoring |
| bee-normalizer | Schema standardization |
| bee-provenance | Chain of custody builder |
| bee-coordinator | Swarm coordination and territory leasing |
| bee-submit | Candidate publishing to hive bus |

### Shared Infrastructure

- Queue / bus
- Vector or fingerprint dedupe store
- Source registry
- Entity registry
- Provenance ledger
- Raw document archive
- Candidate cell database

### Storage Layers

| Layer | Contents |
|-------|----------|
| Raw source archive | Unmodified fetched documents |
| Normalized candidate cells | Structured, schema-compliant cells |
| Graded vault | Royal Jelly + Honey (post-SwarmJudge) |
| Rejected/noise archive | Below threshold, audit preserved |
| Audit logs | Full trace of every decision |

---

## 10. Event Bus Topics

Full traceability through the pipeline.

```
source.discovered
source.fetched
signal.extracted
signal.filtered
signal.normalized
signal.attested
signal.submitted
signal.graded
signal.vaulted
signal.rejected
```

---

## 11. SwarmJudge Interface

A Bee does not make the final Royal Jelly decision alone. It hands off to SwarmJudge.

```json
{
  "candidate_cell": {},
  "provenance_record": {},
  "raw_source_pointer": "r2://swarm-vault/raw/...",
  "pre_scores": {
    "source_confidence": 0.95,
    "novelty": 0.88,
    "relevance": 0.91,
    "synthetic_risk": 0.03
  }
}
```

SwarmJudge performs: contradiction testing, entity verification, cross-source support, schema validity, grade assignment.

That separation matters.

---

## 12. The Jelly Protection Rule

**Critical design rule:**

> Bees may structure reality, but they may not interpret reality too early.

**Allowed in Bee stage:**
- Extraction
- Normalization
- Provenance
- Classification

**Not allowed in Bee stage:**
- Long reasoning
- Forecasting
- Strategic opinion
- Scenario narratives

Those belong in Honey and above.

**That's what preserves the virgin layer.**

---

## 13. Deployment Pattern

### CPU Hive Nodes

Run: scout bees, fetchers, filters, normalizers, provenance services, coordinators

Perfect for high-parallel lightweight tasks.

### GPU Rails

Run: deep extraction models, semantic dedupe, SwarmJudge, contamination detection, ontology matching, downstream Honey generation

Fits the sovereign compute model.

---

## 14. The v1 Build — Start With One Domain

Do not start with every domain. Start with one.

### Bee-CRE v1 Stack

- 10–20 primary sources
- One canonical event schema
- One entity ontology
- Novelty + provenance + relevance scoring
- SwarmJudge grading
- Jelly vault output

### v1 Target Outputs

- 100 clean candidate cells/day
- 10–20 Jelly-grade cells/day
- Dedupe rate under control
- Full audit trail

That proves the concept.

---

## 15. Architecture Thesis

> Bee agents are domain-specific signal miners that capture first-contact reality, normalize it into canonical hive cells, and deliver provenance-backed candidates into the Royal Jelly grading system.

---

## Next: Production Bee Agent Spec

Folder layout, service names, queue topics, JSON schemas, scoring formulas.

---

*Swarm & Bee AI — Bee Agent Architecture v1*
