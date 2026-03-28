# MICA Invocation Patterns v1.0

**Status:** normative usage supplement for mica-v0.1.7-universal.schema.json
**Applies to:** MICA Universal v0.1.7 + MICA-LAB v0.1.5
**Does not apply to:** v0.1.6 and earlier (deprecated)

---

## The Invocation Problem

MICA files (`*.mica.*.json`) are designed to be the operational context anchor for any AI
session working on a project. However, v0.1.7 schema defines the *content* of the archive
but does not define *how* the archive reaches the AI session.

The gap: an AI session starts without knowing MICA exists. Unless a human explicitly says
"load the MICA file", the AI proceeds without the provenance registry, design invariants,
or quality gates — defeating the purpose of the archive.

Three invocation patterns solve this. Each suits a different scope and deployment context.

---

## Pattern Index

| Pattern | Scope | Requires installation | Version-controlled with project | Token overhead |
|---------|-------|----------------------|--------------------------------|----------------|
| 1. README-as-Protocol | Project-local | No | Yes (git) | Read-time only |
| 2. Global Skill | Cross-project | Yes (CLI install) | Separate repo | Always (description) |
| 3. Workspace Directive | Workspace-local | No | Yes (CLAUDE.md) | Always loaded |

Use Pattern 1 as the **default** for any project that ships its own MICA file.
Use Pattern 2 as **fallback** or for workspaces with many MICA projects.
Use Pattern 3 as **backstop** when neither Pattern 1 nor 2 is available.

---

## Pattern 1: README-as-Protocol (Recommended)

### Concept

The project README contains an `[AI Session Protocol]` section at the very top. When an
AI reads the README — which happens at or near the start of any session — the protocol
section is encountered first. The section contains imperative, sequential instructions
that the AI must follow before doing any other work.

This mirrors the semantics of a shell script or CI pipeline file: reading the file *is*
executing it. There is no separate activation step.

### Why it works

- AI processes text sequentially. A protocol section at the top of README is encountered
  before any other content.
- The instructions are imperative: "Read X", "Extract Y", "Output Z before proceeding".
  AI systems trained on instruction-following treat these as directives, not suggestions.
- The section heading `[AI Session Protocol]` signals machine-readable intent while
  remaining human-readable.
- No installation, no global state, no token overhead outside the project.

### Template

Place this section immediately after the project title and one-line description in README:

```markdown
---

## [AI Session Protocol]

**Execute in order before any other action. Do not skip.**

**Step 1 — Load experiment baseline (if present):**
Read `memory/<project>.mica-lab.v*.json`
- `cycle_meta.stage_gate_final` must be PASS before code changes
- `track_decomposition` routes your task to the correct track
- `deviation_log` gives context on known deviations

**Step 2 — Load operational context:**
Read `memory/<project>.mica.v*.json`
- `design_invariants` (severity=critical): binding for this session
- `provenance_registry`: SHA256 map — flag modified registered files as drift
- `invoke_role_semantics`: apply anchor/bridge/hint roles per file

**Step 3 — Report before touching code:**

Output the following before any other work:
```
[SESSION READY]
Gate       : <stage_gate_final> (<passed>/<total> tests)
Track      : <active track> — <files in scope>
Invariants : <list of active critical DI IDs>
Deviations : <count> logged
```

**Critical invariants (inline):**

| ID | Rule |
|----|------|
| DI-nnn | <rule statement> |
| ... | ... |

---
```

### Required elements

1. **Section heading**: `## [AI Session Protocol]` — exact format. Brackets signal
   machine-readable intent.
2. **Imperative opener**: "Execute in order before any other action. Do not skip."
3. **Numbered steps**: Step 1 (MICA-LAB), Step 2 (MICA Universal), Step 3 (report).
4. **Inline critical invariants**: Duplicate the `severity=critical` invariants from the
   MICA JSON here. This ensures the AI has the most critical constraints even if it fails
   to load the JSON.
5. **Session report format**: Forces structured output confirming context was loaded.

### Inline invariants — why duplicate them

The MICA JSON is the authoritative source. However, inline invariants in README serve
two additional purposes:

- **Fail-safe**: If the AI cannot read the JSON (path error, encoding issue), the critical
  rules are still visible.
- **Human visibility**: Developers see the constraints without opening the JSON.

If the JSON and README diverge, the JSON takes precedence. Update README inline invariants
whenever the JSON `design_invariants` with severity=critical change.

### Track routing (optional but recommended)

If the project uses MICA-LAB `track_decomposition`, add a routing table:

```markdown
**Track routing:**

| Task involves | Track | Canonical files |
|---|---|---|
| [component A] | A | [file list] |
| [component B] | B | [file list] |
| ...           | ...| ...         |
```

This allows the AI to immediately identify which track a task belongs to without reading
the MICA-LAB JSON first.

### Provenance drift reminder

Add this to the bottom of the protocol section:

```markdown
**After any code change to a registered file:**
Note which files were modified and remind the user:
"Update memory/*.mica.*.json provenance_registry SHA256 hashes before next session."
```

---

## Pattern 2: Global Skill (Agent Skills Format)

### Concept

A `SKILL.md` file installed in the AI's skill registry causes the AI to automatically
activate MICA loading whenever it detects a project with MICA files. The activation
decision is driven by the `description` field in the SKILL.md frontmatter.

This pattern uses the [Agent Skills](https://agentskills.io/) open format.

### How Agent Skills activation works

At startup, the AI loads `name` + `description` for all installed skills (~100 tokens
each). When the AI begins working on a task, it evaluates whether any skill's description
matches the current context. If a match is found, the full skill body is loaded.

The `description` field is the trigger — there is no separate `auto_adoption` field.
Description clarity determines activation reliability.

### SKILL.md template

```markdown
---
name: mica-context-loader
description: Auto-load and validate MICA operational context anchors when the working
  project contains memory/*.mica.*.json files. Activates before any maintenance,
  refactor, or pipeline work to establish provenance registry (SHA256), design
  invariants, track decomposition, and quality gates. Use when the working directory
  has a memory/ folder with MICA universal or MICA-LAB JSON files.
---

# MICA Context Loader

**Role**: Automatic MICA context hydration and validation layer.
**Problem solved**: MICA files exist in the project but AI does not know to load them.
This skill makes loading automatic when MICA files are present.

## Trigger Detection

Activate immediately when ANY of these conditions are true:
1. Working directory contains `memory/*.mica.*.json`
2. User mentions "MICA", "provenance registry", or "stage_gate_final"
3. User asks to make changes to a project — check for MICA files first

Do not wait for user instruction. If MICA files exist, load them.

## Loading Sequence

Step 1: Discover MICA files
  glob: memory/*.mica*.json
  identify: universal file (*.mica.v*.json)
  identify: lab file (*.mica-lab*.json)

Step 2: Load MICA-LAB first (if present)
  extract: cycle_meta.stage_gate_final
  extract: track_decomposition
  extract: deviation_log

Step 3: Load MICA Universal
  extract: design_invariants (critical severity first)
  extract: provenance_registry (SHA256 map)
  extract: invoke_role_semantics

Step 4: Validate provenance (existence check)
  for each path in provenance_registry: verify file exists
  flag missing files as DRIFT WARNING
  do NOT block on hash mismatch — report and continue

Step 5: Output session opening report (see format below)

## Session Opening Report

[MICA LOADED]
Project    : <project.name> v<project.version>
Gate       : <stage_gate_final> (<passed>/<total> tests)
Invariants : <count> critical, <count> high
Tracks     : <track decomposition summary>
Provenance : <N> files registered
Deviations : <count> logged

Active DIs (critical):
  DI-xxx: <label>
  ...

## invoke_role_semantics Application

anchor -> treat as ground truth; never contradict without explicit user override
bridge -> check before cross-component changes
hint   -> advisory; can be overridden by current code state
none   -> use only if directly relevant

## Provenance Drift Protocol

After any code change to a registered file:
"[MICA REMINDER] Registered file modified: <filename>.
Update memory/*.mica.*.json provenance_registry SHA256 before next session."

## Quality Gate Enforcement

stage_gate_final == PASS   -> proceed normally
stage_gate_final == HOLD   -> warn before proceeding
stage_gate_final == BLOCK  -> strong warning; do not add features
```

### Installation

```
Dev path    : D:\<workspace>\Claude-Skills\mica-context-loader\SKILL.md
Install path: C:\Users\<user>\.claude\plugins\marketplaces\anthropics-skills\mica-context-loader\SKILL.md
```

Restart the AI CLI after installation.

### Progressive disclosure

The Agent Skills format loads skill name+description at startup for all installed skills.
The full body is only loaded when the skill is activated. This means:

- Startup overhead = ~100 tokens (name + description only)
- Activation overhead = full body, only when MICA project is detected
- Non-MICA sessions pay only the description cost

### Limitation

The skill must be installed per machine/user. It is not project-local. If the AI is
running in a new environment (cloud CI, another developer's machine), the skill is not
present. Pattern 1 (README-as-Protocol) has no such limitation.

**Recommendation**: Use Pattern 2 as a complement to Pattern 1, not as a replacement.

---

## Pattern 3: Workspace Directive (CLAUDE.md)

### Concept

A `CLAUDE.md` file in the workspace root contains a directive instructing the AI to
always check for and load MICA files when starting work in any project directory.

This is a workspace-level backstop. It does not require per-project README changes or
skill installation.

### Template

Add to `CLAUDE.md` under a "MICA Context Loading" section:

```markdown
## MICA Context Loading

When beginning work in any project directory:
1. Check for `memory/*.mica*.json` files
2. If found: follow the loading sequence in README `[AI Session Protocol]` section,
   or if README has no protocol section, load manually:
   - MICA-LAB first (*.mica-lab.*.json) -> stage_gate_final, tracks, deviations
   - MICA Universal (*.mica.v*.json) -> design_invariants, provenance_registry
3. If not found: proceed without MICA context
```

### Limitation

CLAUDE.md is always loaded, so this directive consumes tokens in every session regardless
of whether the project has MICA files. Pattern 1 incurs no overhead in non-MICA projects.

Use Pattern 3 only as a backstop when Pattern 1 is not yet implemented in a project.

---

## Comparison and Selection

```
New project with MICA file
  -> Use Pattern 1 (README-as-Protocol)
  -> Pattern 2 as personal fallback (install once)
  -> Pattern 3 only if workspace has many MICA projects without Protocol sections

Existing project being retrofitted with MICA
  -> Add Pattern 1 first (cheapest, no install)
  -> Then add MICA JSON and validate provenance

Cross-project tool (e.g. the mica-context-loader skill itself)
  -> Pattern 2 is the natural home

CI/CD environment (no human, no skill install)
  -> Pattern 1 only (README is always available)
  -> Add explicit MICA loading step in CI script if AI is invoked
```

---

## Gap Analysis: What v0.1.7 Schema Does Not Cover

The following aspects are handled by invocation patterns but are absent from the
mica-v0.1.7-universal.schema.json. These are candidates for v0.1.8 schema additions.

### Gap 1: invocation_protocol field

The schema has no field declaring how the archive should be loaded. A future schema
could add:

```json
"invocation_protocol": {
  "type": "object",
  "properties": {
    "primary_pattern": {
      "type": "string",
      "enum": ["readme_protocol", "global_skill", "workspace_directive", "explicit"]
    },
    "readme_section_heading": {
      "type": "string",
      "description": "Expected heading in README that triggers loading. Default: [AI Session Protocol]"
    },
    "skill_name": {
      "type": "string",
      "description": "Agent Skills name if Pattern 2 is used."
    },
    "loading_order": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Ordered list: mica-lab file first, then universal."
    }
  }
}
```

### Gap 2: session_report_format field

The schema has no prescribed format for the session opening report. The AI produces
different report formats across sessions. A normative `session_report_format` would
ensure consistency:

```json
"session_report_format": {
  "type": "object",
  "properties": {
    "required_fields": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Fields that must appear in the session opening report."
    },
    "format_template": {
      "type": "string",
      "description": "Freeform template string with {placeholders}."
    }
  }
}
```

### Gap 3: drift_response_policy field

When `provenance_registry` SHA256 hashes do not match current files, the schema
prescribes no response behavior. A `drift_response_policy` would normalize this:

```json
"drift_response_policy": {
  "type": "object",
  "properties": {
    "on_hash_mismatch": {
      "type": "string",
      "enum": ["warn_continue", "warn_block", "silent"]
    },
    "on_file_missing": {
      "type": "string",
      "enum": ["warn_continue", "warn_block", "silent"]
    },
    "reminder_after_change": {
      "type": "boolean",
      "description": "If true, AI reminds user to update provenance_registry after modifying registered files."
    }
  }
}
```

### Gap 4: inline_invariants field

The schema stores design invariants as machine-readable JSON. There is no field for
the human/AI-readable inline version that Pattern 1 README embeds. This duplication
is currently unmanaged — JSON and README can drift apart.

A future schema could include:

```json
"inline_invariants_format": {
  "type": "string",
  "enum": ["markdown_table", "numbered_list", "none"],
  "description": "Format for embedding design_invariants in README. 'none' means no inline duplication."
}
```

### Gap 5: No normative track routing declaration

`track_decomposition` (MICA-LAB only) exists but is absent from the universal schema.
Projects using the universal schema have no standard way to declare which files belong
to which logical track. This makes README routing tables manually maintained.

A lightweight `track_map` field in universal could solve this:

```json
"track_map": {
  "type": "object",
  "additionalProperties": {
    "type": "object",
    "properties": {
      "label": {"type": "string"},
      "files": {"type": "array", "items": {"type": "string"}}
    }
  }
}
```

---

## Full Invocation Flow (combined patterns)

```
Session start
  |
  +-- CLAUDE.md loaded (Pattern 3 backstop)
  |   -> "check for MICA files if present"
  |
  +-- AI opens project directory
  |
  +-- AI reads README.md  <-- Pattern 1 triggers here
  |   -> encounters [AI Session Protocol] section
  |   -> Step 1: read MICA-LAB json
  |   -> Step 2: read MICA Universal json
  |   -> Step 3: output [SESSION READY] report
  |   -> invariants loaded, track identified
  |
  +-- OR: AI starts task without reading README
      -> mica-context-loader skill activates  <-- Pattern 2 triggers here
         (detects memory/*.mica*.json in working directory)
      -> same loading sequence as Pattern 1
      -> [MICA LOADED] report output

Work begins with full context anchor active.
```

---

## Normative Constraint

When a project ships a MICA file:

1. The README MUST contain an `[AI Session Protocol]` section (Pattern 1).
2. The section MUST include the 3-step loading sequence.
3. The section MUST include inline critical invariants (severity=critical from MICA JSON).
4. The section MUST include a `[SESSION READY]` report format.
5. The MICA JSON provenance_registry MUST be updated after any registered file changes.

Compliance with these constraints is sufficient to satisfy MICA's context continuity
goal across AI sessions, regardless of whether Pattern 2 or 3 is also in use.

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-03-17 | Initial normative invocation patterns document. Derived from RexBio Pipeline v3.0.1 implementation experience. Generalized for cross-architecture use. |
