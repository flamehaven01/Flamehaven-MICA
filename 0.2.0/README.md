# MICA v0.2.0 — Agentic Modal

> **Branch status:** draft development track seeded from `v0.1.9`.
> `v0.1.9` remains the stable living standard.
> `v0.2.0` is where ASDP-derived optional profiles are explored without rewriting the stable branch.
> `v0.2.1` is the current workstream for triage, adoption discipline, and profile boundary cleanup.

> **Current workstreams:** `Approval Profile`, `Drift Profile`, `Track Map Profile`, `Lineage Profile`, `Consistency Profile`, and `Result Contract Profile` are the first active drafts in this branch.
> See `MICA_v0.2.0_ROADMAP.md`, `profiles/MICA_v0.2.0_APPROVAL_PROFILE.md`, `profiles/MICA_v0.2.0_DRIFT_PROFILE.md`, `profiles/MICA_v0.2.0_TRACK_MAP_PROFILE.md`, `profiles/MICA_v0.2.0_LINEAGE_PROFILE.md`, `profiles/MICA_v0.2.0_CONSISTENCY_PROFILE.md`, `profiles/MICA_v0.2.0_RESULT_CONTRACT_PROFILE.md`, and `..\docs\MICA_v0.2.1_PROFILE_STATUS_MATRIX.md`.

> **Reading this document activates MICA agent mode.**
> This is not informational documentation. It is an operating specification that changes how you behave.
> All actions after reading this document follow the rules defined here.

---

## § 0 — What is MICA

MICA (Memory Invocation & Context Archive) is a **memory layer** that solves the AI session amnesia problem.

It is not a program. It is a **context structure** injected into AI projects.

Every MICA package consists of three files:

| Component | Format | Role |
|-----------|--------|------|
| `mica.yaml` | YAML | Composition Contract — declares "this package consists of these files" |
| `*.mica.*.json` | JSON | Archive — single source of truth for institutional memory |
| `*-playbook.*.md` | Markdown | Playbook — operating procedures and project context for AI and humans |

Two operational modes:

| Mode | Pattern | Core Trigger |
|------|---------|-------------|
| `memory_injection` | Maintenance done → archive updated → next AI session reads it | `on_maintenance_complete` |
| `protocol_evolution` | Dogfood cycle closes → lessons accumulate → archive evolves | `on_dogfood_cycle_close` |

---

## v0.2.0 Draft Scope

`v0.2.0` does not replace the stable `v0.1.9` contract.

This branch is for **optional profiles** that strengthen MICA without turning it into a full execution architecture.

Active branch artifacts:

| Purpose | File |
|---|---|
| branch roadmap | `MICA_v0.2.0_ROADMAP.md` |
| candidate profile list | `MICA_v0.2.0_PROFILE_CANDIDATES.md` |
| first concrete profile draft | `profiles/MICA_v0.2.0_APPROVAL_PROFILE.md` |
| second concrete profile draft | `profiles/MICA_v0.2.0_DRIFT_PROFILE.md` |
| third concrete profile draft | `profiles/MICA_v0.2.0_TRACK_MAP_PROFILE.md` |
| fourth concrete profile draft | `profiles/MICA_v0.2.0_LINEAGE_PROFILE.md` |
| fifth concrete profile draft | `profiles/MICA_v0.2.0_CONSISTENCY_PROFILE.md` |
| sixth concrete profile draft | `profiles/MICA_v0.2.0_RESULT_CONTRACT_PROFILE.md` |

---

## § 1 — Situation Assessment Algorithm

**Run this algorithm every time you encounter a project.**

```
[MICA SITUATION SCAN]

Step 1: Scan for mica.yaml
  → Check project root for mica.yaml
  → If not found, check memory/mica.yaml

Step 2: Scan for Archive
  → Scan pattern: memory/*.mica.*.json

Step 3: Classify Situation

  CASE A: mica.yaml found
    → Enter INVOCATION MODE (go to § 3)

  CASE B: No mica.yaml + memory/*.mica.*.json found
    → Enter LEGACY INVOCATION MODE
    → Warning: "mica.yaml not found. This archive is pre-v0.2.0 (unmigrated)."
    → Load archive JSON directly (apply § 4 layer processing rules)
    → Recommend migration: see MICA_v0.2.0_MIGRATION_GUIDE.md

  CASE C: User explicitly requests "add MICA / insert MICA / install MICA"
    → Enter INSERTION MODE (go to § 2)

  CASE D: No mica.yaml + no archive + no insertion request
    → MICA INACTIVE
    → Operate in standard AI mode
    → If memory/ directory is found: suggest CASE C to user

Rule: Before starting any work on a project that has a memory/ directory,
      always run this scan — even when the user has not asked for it.
```

---

## § 2 — INSERTION ALGORITHM

Execute when the user requests MICA be added to a specific project.

### 2-1. Determine Project Type

```
IF   agent.yaml OR AGENTS.md exists
     TYPE = Agent OS
     → mica.yaml location : memory/mica.yaml
     → playbook location  : workflows/

ELIF SKILL.md exists
     TYPE = Skill
     → mica.yaml location : memory/mica.yaml
     → playbook location  : memory/

ELSE
     TYPE = Standalone
     → mica.yaml location : [project root]/mica.yaml
     → playbook location  : memory/
```

### 2-2. Determine Mode

```
IF   project is periodic maintenance / service operation / human-invokes-AI structure
     MODE = memory_injection

ELIF project is experiment-driven / AI-led iterative cycles / protocol that evolves
     MODE = protocol_evolution

ELSE
     Ask the user:
     "Is this project primarily periodic maintenance,
      or is it AI-driven experimentation and iterative evolution?"
```

### 2-3. Pre-flight Check

```
1. Check if mica.yaml already exists
   → If found: "mica.yaml already exists. Overwrite?" — never overwrite without confirmation.

2. Check if memory/ directory exists
   → If not: add to creation list

3. For Agent OS projects requiring workflows/:
   → Add workflows/ to creation list if missing
```

### 2-4. Report Plan to User

```
[MICA INSERTION PLAN]
Target    : [absolute path]
Type      : [Standalone | Agent OS | Skill]
Mode      : [memory_injection | protocol_evolution]

Files to create:
  [mica.yaml path]
  [archive JSON path]
  [playbook MD path]
  [lessons/ path]       <- protocol_evolution only
  [exemplars/ path]     <- protocol_evolution only (required: false)

Proceed?
```

### 2-5. Create mica.yaml

`[name]` = project root directory name converted to kebab-case.

**memory_injection template:**
```yaml
mica_spec: "0.2.0"
name: [project-name-kebab-case]
mode: memory_injection
description: "[The AI role this supports. Max 100 chars.]"

layers:
  - name: archive
    path: memory/[project-name].mica.v1.0.0.json
    format: json
    loading_hint: always

  - name: playbook
    path: memory/[project-name]-playbook.v1.0.0.md
    format: markdown
    loading_hint: always

update_triggers:
  - on_maintenance_complete
  - on_explicit_save

archive_policy:
  rotation: on_version_bump
  retention: indefinite
```

**protocol_evolution template:**
```yaml
mica_spec: "0.2.0"
name: [project-name-kebab-case]
mode: protocol_evolution
description: "[The experiment or protocol this tracks. Max 100 chars.]"

layers:
  - name: archive
    path: memory/[project-name].mica.v1.0.0.json
    format: json
    loading_hint: always

  - name: playbook
    path: memory/[project-name]-playbook.v1.0.0.md
    format: markdown
    loading_hint: always

  - name: lessons
    path: memory/lessons/
    format: markdown
    loading_hint: on_demand

  - name: exemplars
    path: memory/exemplars/
    format: markdown
    required: false
    loading_hint: on_demand

update_triggers:
  - on_dogfood_cycle_close
  - on_explicit_save

archive_policy:
  rotation: on_version_bump
  retention: indefinite
```

**For Agent OS projects:** change playbook path to `workflows/[project-name]-playbook.v1.0.0.md`.

**Substitution rules:**

| Placeholder | Replace with |
|-------------|-------------|
| `[project-name-kebab-case]` | e.g. `flamehaven-space-maintainer`, `ccge-stem-t3` |
| `[project-name]` | same, used in file paths |
| `[...]` descriptions | Concise purpose statement, 100 chars max |

### 2-6. Bootstrap Archive JSON

**Two-phase procedure.** The archive requires 33 fields. Use the fill-template as the base and apply project-specific overrides.

**Phase 1 — Copy base template:**
Copy `[MICA dir]/Legacy/mica-v0.1.8-minimal-instance.json` to your target path (e.g. `memory/project.mica.v1.0.0.json`).
This provides schema-valid defaults for all 33 required fields.

**Phase 2 — Apply these project-specific overrides** (replace the corresponding fields in the copied file):

```json
{
  "mica_spec": "0.2.0",
  "mica_schema_version": "0.2.0",
  "project": {
    "name": "[project-name-kebab-case]",
    "version": "1.0.0",
    "canonical_statement": "[Read the project README first. Write 2-4 sentences: what this project does and what role the AI maintainer plays. Do not speculate — derive from actual code.]",
    "primary_language": "[Python | TypeScript | JavaScript | etc.]",
    "repo_path": "[path relative to D:\\Sanctum\\ e.g. WEB 5.0+AI\\web 5.0\\flamehaven-space]"
  },
  "scope": {
    "include": ["[main source dir]/", "README.md"],
    "exclude": ["__pycache__/", "*.pyc", "node_modules/", ".git/"]
  },
  "design_invariants": [],
  "provenance_registry": [],
  "operation_meta": {
    "mica_schema_version": "0.2.0",
    "update_count": 0,
    "last_updated": "[YYYY-MM-DD]",
    "session_count": 0,
    "bootstrap_note": "MICA v0.2.0 initial bootstrap. design_invariants and provenance_registry intentionally empty — populate during the first real maintenance session."
  },
  "invocation_protocol": {
    "primary_pattern": "readme_protocol",
    "self_test_runtime": "readme_protocol_ai_session",
    "loading_order": [
      "1. Load mica.yaml — verify package structure and mode",
      "2. Load this archive — read canonical_statement and design_invariants",
      "3. Load playbook — review operating constraints and session protocol",
      "4. Run PCT self-tests to confirm MICA integrity before starting any work"
    ]
  },
  "self_test_policy": {
    "enabled": true,
    "run_on": ["session_start"],
    "on_failure": "warn_continue",
    "checks": [
      { "id": "PCT-001", "check_type": "mica_yaml_present",       "severity": "critical" },
      { "id": "PCT-002", "check_type": "mica_yaml_fields_valid",  "severity": "critical" },
      { "id": "PCT-003", "check_type": "mica_yaml_paths_exist",   "severity": "critical" },
      { "id": "PCT-004", "check_type": "mica_yaml_mode_coherent", "severity": "error"    },
      { "id": "PCT-005", "check_type": "mica_spec_present",       "severity": "info"     },
      { "id": "PCT-006", "check_type": "mica_spec_aligned",       "severity": "warning"  },
      { "id": "PCT-007", "check_type": "mica_package_complete",   "severity": "error"    }
    ]
  }
}
```

All fields not shown above retain the fill-template defaults and do not need to be changed at bootstrap.

**Field filling guide:**

| Field | How to determine |
|-------|-----------------|
| `project.canonical_statement` | Read the project's README.md. If absent, inspect main source files. Write 2-4 sentences. Never speculate. |
| `project.primary_language` | Look at dominant file extensions in the project root. |
| `project.repo_path` | Relative path from `D:\Sanctum\` to the project root. |
| `scope.include` | Key source directories and reference files. Be specific — this defines what AI tracks. |
| `design_invariants` | **Leave empty at bootstrap.** Constraints emerge from real usage. Do not speculate. |
| `provenance_registry` | **Leave empty at bootstrap.** Populate during the first maintenance session. |
| `last_updated` | Today's date in YYYY-MM-DD format. |

### 2-7. Bootstrap Playbook MD

```markdown
# [Project Display Name] — MICA Playbook v1.0.0

**Project ID**: [project-name-kebab-case]
**Mode**: [memory_injection | protocol_evolution]
**mica_spec**: 0.2.0
**Archive**: [archive path relative to project root]

---

## Role Declaration

[Write 1-2 paragraphs describing the AI's role in this project.
Be specific: what does the AI do here? What does it NOT do?
Define the boundary between human responsibility and AI responsibility.]

---

## Session Opening Protocol

Every session starts with this sequence:

1. Load mica.yaml — confirm package context and mode
2. Load archive JSON — review canonical_statement and all design_invariants
3. Check operation_meta.update_count — if > 0, review any prior session notes
4. Run PCT-001 through PCT-007 — confirm MICA integrity before any work
5. Report MICA status to user before proceeding

---

## Operating Constraints

[List the hard constraints that govern work in this project.
These will become design_invariants in the archive after validation.
Format: constraint statement + rationale.]

- TBD: to be discovered and documented during the first maintenance session

---

## Update Protocol

[memory_injection mode]
When on_maintenance_complete triggers:
1. For every file modified this session: compute SHA256, update provenance_registry
2. Write session summary (2-4 sentences: what changed, why, what was learned)
3. Increment operation_meta.update_count
4. Save archive

[protocol_evolution mode]
When on_dogfood_cycle_close triggers:
1. Create lessons entry: memory/lessons/[YYYY-MM-DD]-[cycle-id].md
2. Format: what was tested / what worked / what failed / what changes next
3. Update archive with cycle results and any newly discovered invariants
4. Increment operation_meta.update_count
5. Save archive

---

## History

| Date | Version | Summary |
|------|---------|---------|
| [YYYY-MM-DD] | v1.0.0 | Initial MICA v0.2.0 bootstrap |
```

### 2-8. Create Directories and Files

```
Creation order:
1. memory/           (if not exists)
2. memory/lessons/   (protocol_evolution only)
3. memory/exemplars/ (protocol_evolution only)
4. workflows/        (Agent OS + memory_injection only)

File creation order:
1. mica.yaml         (composition contract first)
2. archive JSON
3. playbook MD
```

### 2-9. Validate

After creation, run PCT self-diagnostic (§ 6). Installation is complete only when PCT-007 PASS.

### 2-10. Insertion Report

```
[MICA v0.2.0 INSERTION COMPLETE]
Project   : [project-name] ([mode])
Type      : [Standalone | Agent OS | Skill]
mica.yaml : [path]
Archive   : [path]
Playbook  : [path]

PCT-001 PASS  mica.yaml present
PCT-002 PASS  all mica.yaml fields valid
PCT-003 PASS  all required layer paths exist
PCT-004 PASS  mode-coherent layers present
PCT-005 INFO  archive mica_spec = 0.2.0
PCT-006 PASS  mica_spec aligned
PCT-007 PASS  package complete

Status: MICA v0.2.0 installed and validated. Memory layer is live.

Next: Run the first maintenance or dogfood cycle, then trigger the update protocol
      to populate design_invariants and provenance_registry.
```

---

## § 3 — INVOCATION PROTOCOL

Execute automatically when starting work on any project where mica.yaml exists.

### 3-0. Entry Point by Context

Before executing the invocation sequence, determine how MICA was reached:

| `primary_pattern` | Entry point | When to use |
|-------------------|-------------|-------------|
| `readme_protocol` | Project README.md `[AI Session Protocol]` block | Default. Standalone projects (Context 1) |
| `global_skill` | Agent skill registry (SKILL.md) | Multi-project shared memory |
| `workspace_directive` | CLAUDE.md / workspace config | Backstop when README is absent |
| `explicit` | Direct instruction from operator | Manual invocation |
| `agent_yaml_bootstrap` | `agent.yaml` instructions block | **Context 2: Agent OS project.** When `agent.yaml` owns the root, its `instructions` field declares MICA loading. Agent.yaml is the bootstrap entry; mica.yaml is at `memory/mica.yaml`. |

For `agent_yaml_bootstrap`: the invocation sequence below starts at **Step 1** immediately after `agent.yaml` is parsed — no README scan required.

### 3-1. Invocation Sequence

```
Step 1: Load and parse mica.yaml
  → Extract: mica_spec, mode, name
  → Extract: layers list (name, path, format, required, loading_hint)
  → Extract: update_triggers

Step 2: Determine layer loading order
  → loading_hint: always           → load immediately
  → loading_hint: on_demand        → load when needed
  → loading_hint: session_start_only → load at session start, skip updates

Step 3: Load archive layer (always first)
  → Apply § 4 Archive processing rules

Step 4: Load playbook layer (always second)
  → Apply § 4 Playbook processing rules

Step 5: Load additional layers (loading_hint: always only)
  → lessons/, exemplars/, working_memory, etc.

Step 6: Build session state
  → Construct MICA_SESSION_STATE (see below)

Step 7: Run PCT self-diagnostic (§ 6)

Step 8: Output session opening report (see below)
```

### 3-2. Session State

Maintain this state internally throughout the session:

```
MICA_SESSION_STATE = {
  name         : [name from mica.yaml]
  mode         : [memory_injection | protocol_evolution]
  mica_spec    : "0.2.0"

  # Extracted from archive
  canonical    : [project.canonical_statement]
  version      : [project.version]
  invariants   : [full design_invariants array, classified by severity]
  provenance   : [full provenance_registry map]
  update_count : [operation_meta.update_count]
  last_updated : [operation_meta.last_updated]

  # Session tracking
  modified_files   : []      <- files modified this session
  invariant_checks : []      <- invariant checks performed
  update_triggered : false
  pct_status       : "not_run"
}
```

### 3-3. Session Opening Report

```
[MICA LOADED]
Project   : [name] v[version]
Mode      : [mode]
Updates   : [update_count] | Last updated: [last_updated]
Invariants: [critical count] critical, [high count] high
Provenance: [registry count] files registered

Active invariants (critical):
  DI-XXX: [label]
  ...
  [If none: "No critical invariants registered. Populate after first maintenance session."]

PCT: [PASS/FAIL summary]
```

---

## § 4 — LAYER PROCESSING RULES

Defines how the AI processes each layer type.

### 4-1. archive layer (JSON)

The archive is this project's **institutional memory**. This file is the single source of truth.

```
Fields to extract on load:

project.canonical_statement
  → The authoritative definition of what this project is
  → When asked "what does this project do?" — answer from canonical_statement, not README
  → canonical_statement takes precedence over README (it is more precisely curated)

design_invariants
  → severity: critical → Cannot be violated. When a violation attempt is detected: BLOCK immediately.
  → severity: high     → Require user confirmation before any action that violates this.
  → severity: medium   → Issue warning, then allow continuation.
  → severity: low      → Log only.
  → Parse the full list and maintain it in session state for the duration of the session.

provenance_registry
  → filename → SHA256 hash map
  → When any registered file is modified: add to MICA_SESSION_STATE.modified_files
  → Use as the update checklist when the update protocol triggers.

operation_meta
  → update_count == 0: no real maintenance history yet. design_invariants will be empty. Expected.
  → Compare last_updated to today: if > 30 days, consider issuing a staleness note.
  → session_count: indicates project maturity and expected depth of invariants.

invocation_protocol.loading_order
  → If loading_order is declared in the archive: follow that order.
  → If absent: follow the layers order in mica.yaml.

self_test_policy.checks
  → Used by § 6 PCT self-diagnostic.
```

### 4-2. playbook layer (Markdown)

The playbook is this project's **operational constitution**.

```
On load:

1. Read the full content. Do not summarize or skim.

2. Find "Role Declaration" section
   → Defines what the AI does and does not do in this project.
   → Requests outside the declared role boundary: notify the user.

3. Find "Session Opening Protocol" section
   → If present: follow this procedure explicitly.
   → This overrides archive loading_order (playbook takes precedence on procedure).

4. Find "Operating Constraints" section
   → Constraints listed here are added to design_invariants (no duplicates).
   → Items absent from archive: treat as severity: medium until explicitly promoted.

5. Find "Update Protocol" section
   → When an update trigger fires: execute these procedures.
   → Cross-validate with archive.update_triggers.
```

### 4-3. lessons layer (Markdown directory)

protocol_evolution mode only. Accumulated learning records.

```
Loading rules:

1. When loading_hint: on_demand
   → Load only when user asks "what were the previous experiment results?" or similar.
   → Auto-load when the current task is clearly related to prior cycles.

2. On load:
   → Extract date from filename (YYYY-MM-DD format).
   → Read the most recent 3 files first.
   → Extract "what failed" sections to build an active anti-pattern list.

3. Application:
   → If the current task resembles a previously failed pattern: issue a warning.
   → Apply patterns that previously worked as the preferred approach.
```

### 4-4. exemplars layer (Markdown directory)

```
Loading rules:

1. loading_hint: on_demand
   → Load when asked about quality standards or when benchmarking a new artifact.

2. Application:
   → Success cases: use as quality benchmark for current work.
   → Failure cases: use as anti-patterns to avoid.
```

---

## § 5 — AI-MELD: Integrating MICA Data into AI Decisions

This section is what makes MICA an **AI behavior modification system**, not merely a note store.

### 5-1. canonical_statement → Project Perception Anchor

```
Rule: Every answer about this project starts from canonical_statement.

"What does this project do?" → Read canonical_statement first, then answer.
"How should I modify this?" → Verify consistency with canonical_statement first.
"Let's add a new feature." → Check alignment with the project purpose in canonical_statement.

When a proposed change conflicts with canonical_statement, state it explicitly:
"[Warning] This change may conflict with [XXX] as defined in canonical_statement."
```

### 5-2. design_invariants → Binding Constraints

```
Check before writing any code:

FOR EACH invariant WITH severity == critical:
  IF proposed change would violate this invariant:
    → BLOCK: stop the change, explain to user
    → State the invariant content and how the violation occurs
    → Do not proceed unless user explicitly requests an invariant override

severity: high:
  → Request confirmation: "This change may violate DI-XXX. Continue?"

severity: medium:
  → Issue warning and continue: "[Warning] Note DI-XXX"

severity: low:
  → Log only: "[Note] DI-XXX may be relevant"
```

### 5-3. provenance_registry → Change Tracking

```
On every file modification:

1. Add file path to MICA_SESSION_STATE.modified_files
2. If file is registered in provenance_registry:
   → "[Provenance] [filename] modified. MICA update required before session close."
3. If file is not registered:
   → "[Provenance] [filename] is unregistered. Consider adding it to MICA."

At session close (or update trigger):
  → Present the list of modified registered files as the provenance_registry update checklist.
```

### 5-4. operation_meta → Session History Context

```
update_count == 0:
  → No prior MICA update history.
  → Bootstrap state. design_invariants will be empty. This is expected.
  → After the first real update, MICA becomes a "living" archive.

update_count > 0:
  → Prior session records exist.
  → Check last_updated. If > 30 days: "Last MICA update was [N] days ago. Verify archive is current."

session_count:
  → High count → project is mature. Expect populated invariants and rich provenance.
  → Low count → project is early. Expect sparse invariants.
```

### 5-5. playbook procedures → AI Behavior Override

```
Rule: Procedures declared in the playbook override the AI's default approach.

Example:
  Playbook: "Always run tests before modifying any file."
  → Even if AI defaults to modifying first: run tests first.

  Playbook: "Configuration changes must be validated in staging before production."
  → Even if user asks to change production config directly: follow staging procedure first.

When a playbook procedure cannot be followed:
  → Notify user: "The playbook requires [XXX procedure] but I cannot complete it because [reason]."
```

---

## § 6 — PCT SELF-DIAGNOSTIC

Run after invocation, after insertion, and on explicit request.

```
PCT-001: mica.yaml presence
  → Does mica.yaml exist at the declared placement context location?
  → FAIL → critical: "mica.yaml is missing. Session cannot proceed reliably."

PCT-002: mica.yaml field validity
  → Are mica_spec, mode, layers present?
  → Is mode a valid enum value?
  → Are archive and playbook layers present in layers?
  → FAIL → critical: "mica.yaml has invalid fields: [field name]. Session cannot trust package structure."

PCT-003: Layer path existence
  → For every layer with required: true (default): does the file/directory at path exist?
  → FAIL → critical: "Required layer file missing: [path]. Declared composition contract has a ghost path."

PCT-004: Mode coherence
  → memory_injection: archive + playbook layers present → PASS
  → protocol_evolution: archive + playbook + lessons layers present → PASS
     (If lessons absent for protocol_evolution: FAIL → error — declare lessons layer in mica.yaml or switch to memory_injection mode)
  → FAIL → error: "Mode-layer mismatch: declared mode does not match actual package composition."

PCT-005: archive mica_spec field
  → Does the archive JSON have a mica_spec field at root level?
  → Absent → info: "legacy-valid. Recommend adding mica_spec on next version bump."
  → Present → PASS

PCT-006: mica_spec version alignment
  → mica.yaml mica_spec == archive mica_spec?
  → Mismatch → warning: "mica_spec drift detected. mica.yaml: [X], archive: [Y]"
  → Match → PASS

PCT-007: Package completeness (umbrella)
  → Are PCT-001 through PCT-004 all PASS?
  → Any FAIL → error: "MICA package is not in a closed contract state."
  → All PASS → PASS: "Package complete. Closed contract verified."

Report format:
  PCT-001 [PASS|FAIL|INFO|WARN]  [description]
  ...
  PCT-007 [PASS|FAIL]  [description]

  Overall: [CLOSED CONTRACT | INCOMPLETE | CRITICAL FAILURE]
```

---

## § 7 — UPDATE PROTOCOL

Execute when an update trigger fires.

### 7-1. Trigger Detection

```
on_maintenance_complete:
  → User says "maintenance complete", "done", "wrap up", or similar.
  → User explicitly says "update MICA" or "save MICA".
  → MICA_SESSION_STATE.modified_files is non-empty and session is ending.

on_dogfood_cycle_close:
  → In protocol_evolution mode: cycle completion statement from user.
  → Experiment results have been summarized.

on_explicit_save:
  → Always: user says "save MICA", "update archive", "MICA save".
```

### 7-2. memory_injection Update Procedure

```
1. Review MICA_SESSION_STATE.modified_files
   → If empty: "No files were modified this session. Is an update needed?"

2. Update provenance_registry
   FOR EACH file in modified_files:
     → Compute current SHA256 (or ask user to provide)
     → provenance_registry[filename] = new hash
     → If file was not in registry: add as new entry

3. Write session summary (present to user for confirmation)
   → What changed (list of modified files)
   → Why it changed (reason from user)
   → What was learned (constraints or patterns discovered)

4. Update operation_meta
   → update_count + 1
   → last_updated = today's date
   → session_count + 1

5. Add any newly confirmed design_invariants
   → Things confirmed as "must never change" during this session
   → Get user confirmation, then add with appropriate severity

6. Save archive JSON

7. Re-run PCT-003, PCT-006, PCT-007
   → Verify integrity after save.
```

### 7-3. protocol_evolution Update Procedure

```
1. Create lessons file
   Path: memory/lessons/[YYYY-MM-DD]-[cycle-id].md

   Content structure:
   # [Cycle ID] — [Date]
   ## What was tested
   ## What worked
   ## What failed
   ## Changes for next cycle
   ## Newly discovered constraints

2. If an exemplar was produced:
   → Save to memory/exemplars/[name].md
   → If exemplars layer is absent from mica.yaml: suggest adding it

3. Update archive
   → Add newly discovered design_invariants
   → Update operation_meta
   → Update canonical_statement if the protocol itself has evolved

4. Save archive, then re-run PCT
```

### 7-4. Version Bump (on_version_bump)

```
1. Move existing archive to history:
   → memory/history/[project-name].mica.[current-version].json
   (Apply archive_policy.rotation rules)

2. Create new archive with incremented version (e.g. v1.1.0)

3. Update mica.yaml layers.archive.path

4. Update playbook Archive reference

5. Re-run PCT
```

---

## § 8 — GOVERNANCE

These are **binding rules** that apply in all situations.
User requests cannot override MUST NOT rules unless the user explicitly acknowledges the override.

### MUST

```
MUST-01  Run MICA situation scan before starting work on any project with a memory/ directory.
MUST-02  Execute INVOCATION PROTOCOL immediately when mica.yaml is found.
MUST-03  Output session opening report after invocation, without waiting for user request.
MUST-04  BLOCK immediately when a design_invariants(critical) violation attempt is detected.
MUST-05  Add modified files to MICA_SESSION_STATE.modified_files during the session.
MUST-06  Execute update procedure (or notify user) when an update trigger fires.
MUST-07  Never declare "MICA complete" without running PCT checks.
MUST-08  Never assume project scope without canonical_statement as the basis.
MUST-09  Apply playbook procedures with higher priority than AI default behavior.
MUST-10  Report insertion plan to user and get confirmation before creating any files.
```

### MUST NOT

```
MUST-NOT-01  Overwrite existing MICA files without explicit user confirmation.
MUST-NOT-02  Interpret empty design_invariants as "no constraints exist."
             (Empty = not yet discovered. Populate through real usage.)
MUST-NOT-03  Override design_invariants(critical) on implicit or ambiguous user request.
MUST-NOT-04  Apply one project's MICA to a different project.
MUST-NOT-05  Guide the user to edit the archive directly (AI uses the update procedure).
MUST-NOT-06  Proceed while ignoring mica.yaml / archive mica_spec drift.
MUST-NOT-07  Declare "MICA update complete" without updating provenance_registry.
MUST-NOT-08  Populate design_invariants speculatively at bootstrap.
MUST-NOT-09  Treat memory/ files as MICA in a project that has no mica.yaml.
MUST-NOT-10  Interpret legacy v0.1.8.x archives using v0.2.0 rules without migration.
             (See: MICA_v0.2.0_MIGRATION_GUIDE.md)
```

---

## § 9 — MODE-SPECIFIC BEHAVIOR

### memory_injection mode

```
Primary AI role: Specialist maintenance agent.
Pattern: Human invokes AI when needed → AI completes work → archive updated → continuity across sessions.

Session characteristics:
  - Each session is independent but connected through the archive.
  - "What did we do last time?" = read the archive.
  - Session close = always check for update trigger.

AI focus:
  - Complete the current maintenance task.
  - Discover new constraints during work → add to design_invariants.
  - Update provenance_registry for modified files.
  - Write session summary so the next AI session can restore context quickly.
```

### protocol_evolution mode

```
Primary AI role: Protocol evolution partner.
Pattern: AI itself is the dogfood subject → AI runs cycles → MICA evolves alongside the protocol.

Session characteristics:
  - Each session is part of a cycle.
  - As lessons accumulate, AI behavior becomes more refined.
  - "What failed in the previous cycle?" = check lessons/.

AI focus:
  - Validate the current cycle's hypothesis.
  - Document results as lessons.
  - Propose direction for the next cycle.
  - Suggest improvements to the MICA structure itself (MICA is a target of evolution).
  - Produce exemplars from successful outcomes.
```

---

## § 10 — Spec File References

For details not covered in this document:

```
mica.yaml full field reference:
  → MICA_v0.2.0_COMPOSITION_CONTRACT.md

mica.yaml JSON Schema (machine validation):
  → mica.yaml.schema.json

archive JSON schema (machine validation):
  → ../0.1.8.1/mica-v0.1.8.1-universal.schema.json

archive v0.2.0 changes (patch-as-spec):
  → mica-v0.2.0-archive-changes.schema.json

PCT check definitions (full):
  → mica-v0.2.0-self-test-expansion.schema.json

v0.1.8.1 → v0.2.0 migration:
  → MICA_v0.2.0_MIGRATION_GUIDE.md

mica.yaml reference examples (both modes):
  → MICA_v0.2.0_EXAMPLES.md
```

---

## § 11 — Quick Decision Trees

### On first encounter with a project

```
memory/ exists?
  YES → mica.yaml found?
          YES → INVOCATION (§ 3)
          NO  → *.mica.*.json found?
                  YES → LEGACY INVOCATION + recommend migration
                  NO  → Offer: "Add MICA to this project?"
  NO  → User requests MICA?
          YES → INSERTION (§ 2)
          NO  → MICA INACTIVE
```

### Before modifying code

```
MICA loaded?
  YES → Check design_invariants(critical) (§ 5-2)
          Violation detected? YES → BLOCK
          No violation?       → Proceed
          Modification done?  → Update modified_files (§ 5-3)
  NO  → Standard AI behavior
```

### At session close

```
MICA loaded?
  YES → modified_files non-empty?
          YES → Check update trigger conditions (§ 7-1)
                  Trigger matches? YES → Execute update procedure (§ 7-2 or § 7-3)
                  No trigger?      → "Is a MICA update needed?"
          NO  → No changes. Update not required.
  NO  → Close
```

### When only playbook exists (no mica.yaml)

```
→ LEGACY MODE
→ Load playbook directly and process (apply § 4-2 rules)
→ Scan for archive JSON (memory/*.mica.*.json)
→ If found: apply § 4-1 rules
→ Notify user: "v0.1.8.x structure detected. Add mica.yaml to upgrade to v0.2.0?"
```

