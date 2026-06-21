# CAS Audit Playbook — Flamehaven Code Audit Standard

**Version**: v1.0 (aligned with CAS v0.8.2 + MICA v0.2.8)

---

## Purpose

This playbook defines how to conduct a Flamehaven CAS audit for three distinct case types.
It does not authorize claiming a review is deeper than it actually is.

---

## Before You Start

Declare the case type first. The wrong case type produces misleading evidence levels.

| Signal | Case Type |
|---|---|
| Code repo is the primary artifact | Case #1 |
| Architecture doc or governance design is the primary artifact | Case #2 |
| Both a governance design AND its corresponding codebase | Case #3 |
| Bio/scientific pipeline with reproducibility requirements | Case #3 |

---

## Case #1 — Code Review

### Target

A GitHub repository where code is the primary audit surface.

### Stage 1 — Automated 1st Pass

Run AI-SLOP-DETECTOR:

```bash
python src/slop_detector/cli.py <target_dir> --project --cross-file --no-color
```

Record:
- Deficit score per file
- Critical and high-severity patterns
- Cross-file issues (clone clusters, import cycles)

Do not skip this step and substitute manual judgment. The automated pass surfaces patterns
that manual reading misses.

### Stage 2 — CAS Profile Selection

Choose the profile:

| Deployment Context | Profile |
|---|---|
| Personal experiment / local tool | CAS-P |
| Internal enterprise use | CAS-E |
| Public distribution / Zero Trust | CAS-X |

### Stage 3 — Fill the CAS Template

Sections in priority order:

1. **0. Metadata** — project name, audit ID, deployment context
2. **2. Claim-to-Code** — every verifiable README claim → FIND-NNN verdict
3. **3.1 Module-Level** — each module: verdict, failure type, severity
4. **3.2 Production Blockers** — FIND entries for P0 issues only
5. **5.1 Dependency** — package versions, license status
6. **6. Reproducibility** — environment, execution attempts

Sections that may be light:
- 3.3 (Architectural Divergence) — only if structural mismatch found
- 3.4 (Security Architecture) — only if attack surface exists
- 8.8 (Governance) — only if CAS-E or CAS-X profile

### Stage 4 — Validate

```bash
python cas_validator.py <filled-report.md> --profile CAS-X
```

Verdict must be `VALID PROFILE` before generating HTML.

### Stage 5 — Generate Report

```bash
python cas_html_gen.py <filled-report.md> <output.html> --actionplan
```

### Output Contract

- `<name> Audit.html` — full interactive report
- `<name> Audit_actionplan.html` — priority-filtered kanban
- `.cas_validation_log/validation_runs.jsonl` — audit trail

---

## Case #2 — Semantic Modal / Architecture Design Review

### Target

Governance architecture, design documents, or semantic frameworks where code is absent,
minimal, or not the primary artifact.

### Stage 1 — Document Collection

Collect in order:
1. README and canonical project description
2. Architecture document (if exists)
3. Governance framework document (if exists)
4. Any claim-carrying surface (blog posts, papers, design proposals)

### Stage 2 — Narrative vs Reality Analysis (Section 1)

For each narrative claim:
- Identify the amplification mechanism (why this claim resonates beyond evidence)
- Assign Evidence Level:
  - A: verifiable from design artifacts
  - B: verifiable from execution results
  - C: inferred from adjacent evidence
  - D: external claim, no internal evidence

If more than 40% of verifiable claims land at Evidence Level D, note this explicitly
in the Summary Judgment.

### Stage 3 — Claim Boundary (Section 8.2)

Write both sides:
- What the project CAN fairly be described as (grounded in verifiable evidence)
- What it SHOULD NOT be described as (unverifiable amplified claims)

The claim boundary is the audit's most durable output for Case #2.

### Stage 4 — Governance Alignment (Section 8.8)

Map each stated governance control to:
- Its implementation evidence
- Its compliance status (Verified / Partial / Not assessed)

"Partial" and "Not assessed" are valid verdicts. Do not inflate to "Verified" without
concrete evidence.

### Stage 5 — Architecture Divergence (Section 3.3)

Document gaps between declared architecture and observable implementation:
- Expected component vs actual component
- Declared data flow vs traced data flow
- Stated interface vs found interface

### Stage 6 — Reader Conclusions (Section 8.3)

Write separate conclusions for:
- Investors / B2B evaluators
- Engineers / contributors
- Journalists / analysts

These audiences have different risk exposures to the same misrepresentation.

### Output Contract

- CAS report HTML (Sections 1, 3.3, 8.2, 8.3, 8.8 are the primary value)
- Action plan (optional; useful if governance gaps are actionable)

---

## Case #3 — Integrated (Code + Semantic + Governance)

### Target

Projects where a governance architecture AND its implementing codebase must be
reviewed together. Bio AI pipelines are the canonical example.

### Why Case #3 Exists

A Case #1 review of a bio pipeline misses whether the code actually implements
the declared scientific governance. A Case #2 review misses whether the governance
is executable. Case #3 requires both passes to be linked.

### Stage 1 — Governance Architecture First (Case #2 pass)

Read the governance documents before the code. Extract:
- Stated Design Invariants (DIs) or equivalent governance rules
- Multi-domain lane structure (e.g., EQA / BAV / BSC)
- External trust anchors (DOI, published benchmarks, model version pins)
- Reproducibility commitment level

Record these as candidate DIs before opening the codebase.

### Stage 2 — Code Pass (Case #1 pass, DI-guided)

Run AI-SLOP-DETECTOR. Then cross-check each candidate DI against the code:

| Candidate DI | Code Evidence Found? | CAS Finding |
|---|---|---|
| "Arbitrary-precision required for EQA" | `mpmath` import + usage | Evidence Level A |
| "Multi-model consensus for BAV" | API calls to AF3, AF2, Boltz-2, Chai-1 | Evidence Level A |
| "Audit JSON must remain unedited" | No write path found | Evidence Level C |

Unimplemented governance DIs that are stated as active → FAIL or WARN depending on severity.

### Stage 3 — Reproducibility Audit (Section 6)

For scientific pipelines:
- Stochastic models: verify tolerance bands exist, not bit-exact hash assertions
- Deterministic models: verify environment pins (Python version, library versions, seeds)
- Record actual execution attempts with results

A pipeline that claims reproducibility but has no environment spec is Evidence Level D.

### Stage 4 — Supply Chain Trust (Section 5.2)

For bio AI, verify:
- Model version pins (not "latest")
- Data provenance (training data origin, license)
- External API dependency risk (if cloud model APIs are in the critical path)

### Stage 5 — Security Architecture (Section 3.4)

Bio pipelines often have attack vectors:
- Prompt injection via user-supplied sequences
- Data poisoning via external training sources
- PII leakage in log outputs

Map each to: Attack Vector / Control Present / Verification Status.

### Stage 6 — Governance Framework Alignment (Section 8.8)

For each governance control claimed:
- Match it to a named framework (EU AI Act, ICH E6(R3), ISO 13485, etc.)
- Verify implementation evidence
- Record Remediation Type for gaps

### Stage 7 — MICA Package Recommendation

After the CAS audit, produce a MICA package recommendation:

```
Archive DIs to declare:       <list derived from Stage 1 candidate DIs>
Binding evidence available:   <which DIs have real origin episodes>
Credibility-architecture:     <external trust anchors to formalize>
Invocation pattern:           readme_protocol (bio projects with complex surfaces)
di_policy.critical_binding_required: true (only when all critical DIs have episodes)
```

### Output Contract

- CAS report HTML (all sections populated)
- `_actionplan.html`
- MICA package recommendation (narrative in Section 9 or separate doc)
- `.cas_validation_log/validation_runs.jsonl`

---

## Evidence Level Reference

| Level | Meaning | Acceptable for PASS? |
|---|---|---|
| A | Verified from source code | Yes |
| B | Verified from execution output | Yes |
| C | Inferred from adjacent evidence | WARN only |
| D | External claim, no internal evidence | FAIL or NOTE |

---

## Failure Type Reference

| Type | Meaning |
|---|---|
| F1 | Missing — feature claimed but absent |
| F2 | Incorrect — feature present but wrong |
| F3 | Not executable — code exists but cannot run |
| F4 | Not scalable — works at demo scale only |
| F5 | Not reproducible — results cannot be replicated |
| F6 | Contradictory — claims contradict each other |
| F7 | License risk — dependency or data license conflict |

---

## Severity Reference

| Level | Meaning | Action |
|---|---|---|
| P0 | Production blocker | Must fix before deployment |
| P1 | Major issue | Fix in next release; escalates to P0 under CAS-E/X |
| P2 | Important quality gap | Address in maintenance cycle |
| P3 | Minor cleanup | Address opportunistically |

---

## Automation Gate

Run before finalizing any CAS report:

```bash
python cas_validator.py <report.md> --profile <CAS-P|CAS-E|CAS-X>
```

Exit code `0` = `VALID PROFILE`. Do not ship a report with exit code `1`.

---

## What CAS Is Not

- CAS is not a linter or static analyzer. Use AI-SLOP-DETECTOR for that.
- CAS is not a penetration test. Section 3.4 maps verifiability, not exploits.
- CAS is not a compliance certification. Section 8.8 maps alignment, not attestation.
- CAS is not a marketing review. Claim Boundary (8.2) exists to constrain claims, not amplify them.

---

*Flamehaven Internal Document | CAS Audit Playbook v1.0 | 2026-06-21*
