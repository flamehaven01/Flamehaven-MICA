# MICA Week 1 Technical Rationale

Primary source:
- MICA_Technical_Report_Week1.docx

Status:
- technical rationale only
- not the normative schema contract

## What the Week 1 report contributes
The Week 1 report remains important because it establishes:
- the five-axis scoring lineage: sim, ecency, invoke, 	rust, continuity
- the core pipeline order: collect -> normalize -> score -> dedup -> budget -> map -> handoff -> ledger
- the original semantic-collapse execution concept
- the first explicit articulation of provenance, anchor, and append-only ledger invariants

## What the Week 1 report does not settle
The report does not fully settle the universal normative model because:
- the weighted-product scoring rule is brittle across heterogeneous environments
- the scores are explicitly described there as semantic approximations
- the report states that calibration data was absent
- the experiment was a single semantic-collapse instance, not a universal implementation standard

## Why v0.1.7 universal diverges from v0.1.4 lineage
0.1.7 universal keeps the Week 1 conceptual structure but changes the normative scoring core.

Week 1 / v0.1.4 lineage:
- weighted product
- semantic-collapse first
- strong conceptual demonstration

v0.1.7 universal normative model:
- weighted sum
- explicit weights
- fail-closed admission gates
- implementation stability across languages and runtimes

## Final interpretation
The Week 1 report is authoritative as lineage and rationale.
The schema is authoritative as the normative contract.
When they differ, the current schema wins for implementation.
