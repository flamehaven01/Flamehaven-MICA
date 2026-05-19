# MICA v0.2.5 Runtime Protocol

Canonical execution rules for MICA sessions.
Updated in v0.2.5 to separate guard candidate surfacing from enforcement,
and to reflect the corrected pct_status() behavior.

---

## 1. Session Entry States

A runtime begins in exactly one of these states:

- `INVOCATION_MODE`: `mica.yaml` present
- `LEGACY_MODE`: no `mica.yaml`, but legacy archive (`*.mica.*.json`) exists
- `INSERTION_MODE`: user explicitly asks to add or install MICA
- `INACTIVE`: nothing detected

---

## 2. Detection Order

### Step 1 — locate package markers

Check in this order:

1. project root `mica.yaml`
2. `memory/mica.yaml`
3. `memory/*.mica.*.json`

### Step 2 — classify

- `mica.yaml` found → `INVOCATION_MODE`
- archive only → `LEGACY_MODE`
- explicit install request → `INSERTION_MODE`
- none found → `INACTIVE`

### Step 3 — behavior

#### `INVOCATION_MODE`

1. run `mica_pct.py` — verify package integrity (PCT-001 through PCT-011)
2. run `mica_runtime.py` — emit session summary
3. load archive layer
4. load playbook layer
5. treat surfaced critical DI candidates as active session guards

#### `LEGACY_MODE`

1. print: `[MICA] Legacy archive detected. Running without mica.yaml.`
2. load archive directly
3. load playbook if resolvable
4. recommend migration to `mica.yaml`

#### `INSERTION_MODE`

1. classify project type
2. choose mode
3. choose invocation pattern
4. report planned files before writing (never overwrite existing `mica.yaml`)

#### `INACTIVE`

1. print: `[MICA] INACTIVE -- no mica.yaml found in this project.`
2. proceed without MICA guards

---

## 3. Required Runtime Output

### Text mode

```text
[MICA LOADED] project-name v1.2.3
Mode      : protocol_evolution
Pattern   : hook_trigger
Invariants: 2 critical, 3 high
PCT       : CLOSED
Last upd  : 2026-05-19

Active critical invariant candidates:
  DI-001: no-destructive-resets
    Evidence: EXP-017: force-reset deleted uncommitted work [2x violated]
  DI-002: billing-thresholds-are-measured
```

"Active critical invariant candidates" replaces v0.2.4's "Active critical invariants"
to reflect that mica_runtime.py surfaces these — it does not enforce them.

Evidence line appears only when `binding.origin_episode` is present.

### Hook mode

Default (no `hook_output` policy):

```text
[MICA] project-name v1.2.3 | mode=protocol_evolution | pattern=hook_trigger | DI=2crit/3high | pct=CLOSED | last=2026-05-19
[MICA:DI] DI-001(critical): no-destructive-resets [2x]
[MICA:DI] DI-002(critical): billing-thresholds-are-measured
```

`pct=CLOSED` reflects the full PCT-001 through PCT-011 verdict (v0.2.5 correction).
In v0.2.4, `pct=CLOSED` reflected only a shallow path/field check.

With `hook_output: {max_di_lines: 1, di_filter: violations_only}`:

```text
[MICA] project-name v1.2.3 | mode=protocol_evolution | pattern=hook_trigger | DI=2crit/3high | pct=CLOSED | last=2026-05-19
[MICA:DI] DI-001(critical): no-destructive-resets [2x]
```

`[Nx]` suffix appears only when `binding.violation_count > 0`.

---

## 4. Session Guard Rule

`mica_runtime.py` surfaces critical DI candidates. The host AI agent is responsible
for treating them as session guards and enforcing them.

For each critical DI candidate surfaced:

- treat it as an active guard for the session
- if a proposed action would violate it, stop immediately
- state the invariant ID, label, and binding evidence if present
- require explicit user acknowledgment before proceeding

Binding evidence provides the WHY. Surface it when a guard fires:

```text
[GUARD] DI-001 no-destructive-resets: about to run git reset --hard
Evidence: EXP-017: force-reset deleted uncommitted work [2x violated]
Proceed? This requires explicit acknowledgment.
```

**What mica_runtime.py does:** emits the summary and DI candidate list.
**What the host agent does:** decides whether a proposed action violates a DI,
stops, surfaces evidence, and requests acknowledgment.

mica_runtime.py is a summary emitter, not a command interceptor.

High/medium/low invariants are advisory unless the project elevates them.

---

## 5. PCT-010 and PCT-011 Behavior

### PCT-010 — binding completeness

- WARN when critical DIs lack `binding.origin_episode`
- PASS when all critical DIs are bound
- Does not affect CLOSED CONTRACT status
- Maturity path: escalates to FAIL when `binding_required: true` is set in mica.yaml
  (planned v0.2.6); global FAIL reviewed at v0.3.0

### PCT-011 — lesson_ref existence

- WARN when `binding.lesson_ref` path does not exist on disk
- PASS when all declared `lesson_ref` paths exist
- INFO when no `lesson_ref` fields are declared
- Does not affect CLOSED CONTRACT status

---

## 6. pct= Field Semantics (v0.2.5 correction)

The `pct=` field in hook output and JSON summary reflects the full PCT verdict.

| Value | Meaning |
|-------|---------|
| `CLOSED` | PCT-001 through PCT-011 run; no hard-fail checks failed |
| `INCOMPLETE` | One or more hard-fail checks (PCT-001, 002, 003, 004, 007, 008) failed |
| `LEGACY` | No mica.yaml; running from legacy archive |
| `INACTIVE` | No mica.yaml and no legacy archive found |

In v0.2.4, `CLOSED` only meant that mica.yaml fields were present and paths existed.
In v0.2.5, `CLOSED` means the same thing as `CLOSED CONTRACT` from `mica_pct.py`.

---

## 7. Insertion Protocol

### Project type

- `Agent OS`: `agent.yaml` or `AGENTS.md` present
- `Skill`: `SKILL.md` present
- `Standalone`: otherwise

### Mode selection

- `memory_injection` for maintenance/service operations
- `protocol_evolution` for AI-led iterative protocol work

### Invocation pattern selection

- `hook_trigger` if a pre-prompt hook exists and is maintained
- otherwise prefer `readme_protocol`

### Bootstrap

1. Use `templates/mica-v0.2.4-archive-bootstrap.json`
2. Leave `design_invariants` empty initially
3. Populate DIs from the first real maintenance session
4. Add `binding` blocks to critical DIs as violations are observed — not speculatively

---

## 8. Minimal Operational Contract

A package is operationally sound when all of the following hold:

1. `mica.yaml` exists or legacy archive is detectable
2. archive and playbook paths resolve
3. `mica_pct.py` returns CLOSED CONTRACT (WARN on PCT-010/011 is acceptable)
4. `mica_runtime.py` can emit text or hook summary with accurate pct= field
5. critical DI candidates can be surfaced with binding evidence for host agent enforcement

---

## 9. What Changed from v0.2.4

| Area | v0.2.4 | v0.2.5 |
|------|--------|--------|
| pct_status() | Shallow: checked mica.yaml fields + path existence | Delegates to run_pct_checks(); matches mica_pct.py |
| pct= field accuracy | Could diverge from mica_pct.py verdict | Always matches mica_pct.py verdict |
| YAML fallback parser | Flat-line; lost nested structures | Indentation-aware; parses all MICA structures |
| Guard language | "install as active guard" | "surface as guard candidate; host agent enforces" |
| Fixtures | None | 4 test packages in fixtures/ |
| Shared core | None | mica_core.py |
