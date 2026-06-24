# MICA v0.2.8 Release Notes — Binding Depth Edition

## Summary

v0.2.8 closes the binding quality gap exposed by the alecta-stock v0.2.7 live audit:
`critical_binding_required: true` + PCT-010 PASS does not mean the bindings are real.
Three out of five production deployments had doctrinal prose in critical DI bindings
that passed without any signal.

All new signals are WARN or INFO. No existing package breaks.

---

## The Problem v0.2.8 Solves

### "Binding exists" != "binding is grounded"

In v0.2.6 and v0.2.7, PCT-010 PASS requires only that `binding.origin_episode` is
non-empty (> 10 chars). Any prose qualifies. Operationally:

```
DI-001 [critical] — PCT-010 PASS, critical_binding_required=true
  origin_episode: "Enforcement of absolute data integrity to prevent financial risks."
```

This passes identically to:

```
DI-006 [critical] — PCT-010 PASS
  origin_episode: "EXP-OS-1: fx was null on Vercel (v0.8.6), then valuation.per/pbr...
                   three separate occurrences of the same class."
```

DI-006 is grounded in a real incident with a code, a version, and a consequence.
DI-001 is a purpose statement — it rephrases the DI itself. The first tells the
host agent nothing it doesn't already know from the label.

### violation_count without a timestamp is a data defect

`binding.violation_count: 3` with `binding.last_triggered: ""` is an incoherent
record. Either the violation count is fabricated or the timestamp was never updated.
Neither is acceptable for a binding that is supposed to represent real history.

### No visibility into version lag

alecta-stock running at `mica_spec: 0.2.6` against canonical `0.2.8` produced
identical PCT-006 output to a package at `0.2.7`. Two versions behind means three
new PCT signals are invisible to operators who haven't upgraded the tools.

---

## What Shipped

| Item | Type | Summary |
|---|---|---|
| PCT-010 doctrinal WARN | Core behavior | Detects `origin_episode` with no EXP-/version/date marker |
| PCT-010 coherence WARN | Core behavior | `violation_count > 0` + empty `last_triggered` → WARN |
| PCT-012 (opt-in) | New check | `max_archive_age_days` → WARN when archive is stale |
| PCT-006 lag WARN | Core behavior | Declared `mica_spec` >= 2 versions behind canonical |
| `di_policy.max_archive_age_days` | Schema | New mica.yaml field activating PCT-012 |
| `MICA_CANONICAL_VERSION = "0.2.8"` | Tooling | Canonical version constant in mica_core.py |
| 3 new fixtures | Testing | `doctrinal_binding`, `stale_archive`, `violation_count_incoherent` |
| Tests: 7 → 10 | Testing | All GREEN |

---

## Upgrade Path

v0.2.8 is non-breaking. See `MICA_v0.2.8_MIGRATION_GUIDE.md`.

For packages with doctrinal bindings: the WARN is informational. Address it when
a real episode occurs — add an `EXP-xxx` code or version reference to `origin_episode`.
For bootstrap-phase DIs where no violation has occurred yet, the WARN is expected.

For freshness tracking: add `di_policy.max_archive_age_days` to mica.yaml. 180 days
is a reasonable default for active projects.

---

## Remaining Limits

### 1. Doctrinal detection has false negatives

The pattern `EXP-` is a naming convention, not a proof of truthfulness. A binding
like `"EXP: initial documentation"` passes the check. The validator detects common
patterns; it cannot verify narrative accuracy.

### 2. PCT-012 WARN is advisory

Archive age is context-dependent. A stable package with no meaningful changes is
not defective because of age. The WARN prompts review; the operator decides.

### 3. PCT-011 still WARN-only

Lesson ref enforcement requires the file to exist. Escalating to FAIL without a
file management workflow would block packages unnecessarily. Deferred.

### 4. binding_depth_required opt-in not implemented

FAIL escalation for doctrinal bindings (analogous to v0.2.6's `critical_binding_required`)
is the logical next step but is not v0.2.8 scope. The signal is WARN; the gate is future.
