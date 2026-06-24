# MICA v0.2.8 Approval Note

## Approval Status

Approved as the correct successor to v0.2.7.

Central judgment: v0.2.7 formalized the deployment model. v0.2.8 addresses the gap
exposed by the alecta-stock v0.2.7 audit: `critical_binding_required: true` + PCT-010
PASS does not mean the bindings are real. Three out of five production deployments
had doctrinal prose in critical DI bindings that passed without signal.

---

## Why v0.2.8 is the right design

### 1. Doctrinal detection is pattern-based, not intent-based

The validator cannot judge whether an origin_episode is truthful. It CAN detect
structural markers of real incidents: episode codes (`EXP-xxx`), version references
(`v0.8.6`), dates (`2026-04-07`), issue numbers (`#123`). Absence of all markers
is a reliable proxy for a doctrinal binding (a rephrasing of the DI statement).

alecta-stock DI-001: `"Enforcement of absolute data integrity to prevent financial risks."`
alecta-stock DI-006: `"EXP-OS-1: fx was null on Vercel (v0.8.6)..."`

The first passes the structural check — it is non-empty and > 10 chars. The second
is demonstrably incident-grounded. v0.2.8 makes that difference visible as a WARN.

### 2. WARN, not FAIL, is the correct escalation

Doctrinal bindings are not invalid — they represent intent before violations have
been observed. Failing them would break all bootstrapped packages and contradict
v0.2.4's design principle: binding is retrospective, not speculative. WARN is the
correct level: "this binding has not been grounded in a real incident yet."

A future `binding_depth_required: true` opt-in could escalate to FAIL for packages
that have matured past the bootstrap phase. That is not v0.2.8 scope.

### 3. violation_count coherence is a data integrity check

`violation_count > 0` with empty `last_triggered` is a field-level defect, not a
policy disagreement. This is always worth flagging — there is no valid reason for
a non-zero violation count without a timestamp. The WARN is unconditional.

### 4. PCT-012 freshness is the right opt-in model

A global freshness check would fail dormant-but-stable packages (flamehaven-space
hasn't changed in months, but the invariants are still valid). Opt-in per package
via `max_archive_age_days` matches the `critical_binding_required` precedent:
package authors declare maturity, not the spec.

### 5. PCT-006 lag threshold closes the version visibility gap

alecta-stock at v0.2.6 and Flamehaven-CAS at ghost v0.2.10 both produced identical
PCT-006 PASS/INFO with no signal of drift. Two versions behind canonical is a
meaningful signal worth surfacing. Three new features (doctrinal check, coherence
check, freshness check) are invisible to operators running v0.2.6.

---

## Remaining Limits

### 1. Doctrinal detection has false negatives

A binding like `"EXP: initial documentation episode"` would pass the pattern check
(it starts with "EXP") despite being fabricated. The pattern check catches common
real-world doctrinal bindings but cannot detect deliberate workarounds. Trust the
operator; flag the obvious cases.

### 2. PCT-012 WARN is not operational policy

Staleness is context-dependent. A 400-day-old archive in a stable, unchanged system
is not defective. The WARN surfaces the age; the operator decides what to do.

### 3. PCT-011 escalation remains deferred

Lesson ref enforcement requires the file to exist before the check can pass.
No change in v0.2.8.

---

## Short Verdict

> v0.2.8 is approved because it converts the binding quality gap — exposed by the
> alecta-stock live audit — into actionable PCT signals, without breaking any existing
> package or changing any CLOSED CONTRACT verdict.
