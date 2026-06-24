# MICA v0.2.7 Runtime Protocol

Canonical execution rules for MICA sessions.
v0.2.7 adds: COMPACT_MODE formal definition, DI namespace extension, PCT applicability matrix, core boundary statement.

---

## 1. Core Boundary

MICA means:

- **Memory Invocation** — locate and activate the declared memory package at session start
- **Context Archive** — maintain an authoritative, versioned record of invariants, decisions, and lessons
- **AI session activation** — ensure the model loads and declares the correct state before any work begins

If a feature does not strengthen one of those three functions, it is not part of MICA core.

### What belongs inside MICA

- `mica.yaml` composition contract
- Archive loading and rotation rules
- Playbook loading and operating-order rules
- Optional lessons or exemplar layers when declared by the contract
- PCT package validation (001–011)
- Runtime activation summary and session opening report
- Drift detection tied to memory, docs, code, and invariants
- Truthful declaration of what was loaded, what is authoritative, and what is provisional

### What does not belong inside MICA core

- Broad repository standardization for unrelated repos
- Generic repo governance scorecards
- Cross-repo compliance loops
- Release marketing surfaces
- Approval bureaucracy not required for session activation

Adjacent systems (RosettaStone, CAS, governance tools) may consume MICA output but are not part of MICA core.

---

## 2. Session Entry States

A runtime begins in exactly one of these states:

| State | Condition | pct= |
|---|---|---|
| `INVOCATION_MODE` | `mica.yaml` present | CLOSED or INCOMPLETE |
| `COMPACT_MODE` | No `mica.yaml`, archive present, intentional deployment | LEGACY |
| `LEGACY_MODE` | No `mica.yaml`, archive present, pre-migration | LEGACY |
| `INSERTION_MODE` | User explicitly requests MICA install | — |
| `INACTIVE` | Nothing detected | INACTIVE |

**COMPACT_MODE vs LEGACY_MODE distinction:** Both produce `pct=LEGACY` at runtime. The distinction is semantic and operator-declared: a COMPACT deployment is a deliberate architectural choice (archive + playbook sufficient, no mica.yaml needed), not a migration artifact. Declare intent in the archive's `project.status` field or `mica_spec` field. Runtime behavior is identical; the distinction affects governance expectations.

---

## 3. Detection Order

### Step 1 — locate package markers

Check in this order:

1. `mica.yaml` at project root
2. `memory/mica.yaml`
3. `memory/*.mica.*.json`

### Step 2 — classify

- `mica.yaml` found → `INVOCATION_MODE`
- Archive only → `LEGACY_MODE` (runtime); treat as `COMPACT_MODE` if intentional
- Explicit install request → `INSERTION_MODE`
- None found → `INACTIVE`

### Step 3 — behavior per state

#### `INVOCATION_MODE`

1. Run `mica_pct.py` — verify package integrity (PCT-001 through PCT-011)
2. Run `mica_runtime.py` — emit session summary
3. Load archive layer
4. Load playbook layer
5. Treat surfaced critical DI candidates as active session guards

#### `COMPACT_MODE` / `LEGACY_MODE`

1. Print: `[MICA] Legacy archive detected. Running without mica.yaml.`
2. Load archive directly
3. Load playbook if resolvable
4. PCT-001 reports FAIL (no mica.yaml); overall pct=LEGACY
5. Recommend migration to `mica.yaml` for LEGACY; no recommendation for COMPACT

#### `INSERTION_MODE`

1. Classify project type
2. Choose mode (`memory_injection` or `protocol_evolution`)
3. Choose invocation pattern
4. Report planned files before writing — never overwrite existing `mica.yaml`

---

## 4. Invocation Hierarchy

MICA cannot assume that an AI session will read the right files automatically. The practical model is a three-tier hierarchy:

### Natural

The agent reads the project surface voluntarily.

Expected order: `README.md` → `mica.yaml` → archive JSON → playbook → lessons/exemplars if declared.

Use when the host already explores context carefully.

```bash
python tools/mica_invoke.py . --mode natural
```

### Guided

The host agent or wrapper explicitly requests the MICA packet first.

The packet contains: archive JSON + playbook + declared-active DIs from mica.yaml.

Use when the host is known to skip context reading without explicit direction.

```bash
python tools/mica_invoke.py . --mode guided
```

### Forced

The invocation hook or system prompt injects the MICA summary directly.

Use when natural or guided modes have failed or are insufficient. Forced mode bypasses voluntary reading by placing the session summary into the system context.

```bash
python tools/mica_invoke.py . --format hook
```

---

## 5. PCT Applicability Matrix

Which PCT checks apply in which state:

| Check | INVOCATION_MODE | COMPACT/LEGACY_MODE | Notes |
|---|---|---|---|
| PCT-001 (mica.yaml present) | ✓ PASS/FAIL | FAIL (expected) | Fails by definition in COMPACT |
| PCT-002 (required fields valid) | ✓ | skip | Requires mica.yaml |
| PCT-003 (layer paths exist) | ✓ | skip | Requires mica.yaml |
| PCT-004 (mode coherence) | ✓ | skip | Requires mica.yaml |
| PCT-005 (archive mica_spec) | ✓ | skip | |
| PCT-006 (spec alignment) | ✓ | skip | |
| PCT-007 (invocation_protocol) | ✓ | skip | |
| PCT-008 (hook coherence) | ✓ | skip | |
| PCT-009 (package summary) | ✓ | partial | Only failing check is PCT-001 |
| PCT-010 (critical binding) | ✓ WARN/FAIL | skip | FAIL only when `critical_binding_required: true` |
| PCT-011 (lesson_ref paths) | ✓ WARN | skip | |

**CLOSED CONTRACT** requires all HARD_FAIL checks to pass. COMPACT/LEGACY deployments cannot achieve CLOSED CONTRACT — `pct=LEGACY` is the expected and valid terminal state for those modes.

---

## 6. DI Namespace Modes (v0.2.7)

Three namespace conventions are formally supported. Declare in `mica.yaml` under `di_policy.namespace_mode`:

| Mode | Pattern | Example | When to use |
|---|---|---|---|
| `sequential` | `DI-NNN` | `DI-001` | Default. Single-lane or simple systems. |
| `domain_namespaced` | `DI-[DOMAIN]-NNN` | `DI-EQA-001`, `DI-BIO-003` | Multi-lane systems where sequential IDs lose semantic meaning. DOMAIN must be uppercase alpha-start. |
| `legacy_inv` | `INV-NNN` | `INV-009` | Grandfathered prefix from pre-v0.2.4 archives. Migrate to `DI-NNN` at next major revision. |

All three modes are validated by the pattern `^(DI|INV)(-[A-Z][A-Z0-9]*)?-\d+$` in `mica-v0.2.7-archive-di-binding.schema.json`.

Mixed-mode (e.g., some `DI-xxx` and some `DI-EQA-xxx` in the same archive) is not prohibited by schema but is discouraged. `namespace_mode` describes the dominant convention.

---

## 7. Closed Contract Definition

`pct=CLOSED` requires:

- PCT-001 PASS
- PCT-002 PASS
- PCT-003 PASS
- PCT-004 PASS
- PCT-007 PASS or INFO
- PCT-008 PASS or INFO
- PCT-010 PASS, WARN, or INFO (never FAIL — FAIL only when `critical_binding_required: true`)
- PCT-011 PASS, WARN, or INFO

INFO and WARN checks do not break CLOSED CONTRACT. Only FAIL on a HARD_FAIL check breaks it.

`pct=LEGACY` is correct and non-defective for COMPACT_MODE and LEGACY_MODE deployments.
