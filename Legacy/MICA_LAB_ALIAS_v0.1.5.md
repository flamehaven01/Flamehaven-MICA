# MICA Lab Alias v0.1.5

Status: active lab alias
Canonical schema: mica-lab-v0.1.5.schema.json
Source lineage: mica-v0.1.5.schema.json

Purpose:
- Preserve the RExSyn / lab-governance style schema as a hard-governance experimental profile.
- Keep cycle-oriented fields, parity contracts, and track-style enforcement available for laboratory or tightly gated methodology workflows.

Use this schema when:
- parity or extension contracts must be explicit
- experimental tracks or stage-gates are first-class requirements
- governance must remain laboratory-grade and fail-closed
- methodology locking is more important than broad interoperability

Do not use this schema when:
- the archive must work across heterogeneous products, maintenance systems, documentation hubs, or operational environments
- cross-runtime portability matters more than lab-cycle specificity

Relationship:
- mica-v0.1.5.schema.json is the original source form
- mica-lab-v0.1.5.schema.json is the explicit lab alias for practical use
- mica-v0.1.7-universal.schema.json is the universal branch and should not be treated as a drop-in replacement for lab workflows
