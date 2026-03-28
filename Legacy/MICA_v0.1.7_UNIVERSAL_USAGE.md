# MICA v0.1.7 Universal Usage Rules

Status: normative usage note for mica-v0.1.7-universal.schema.json

## 1\. When to use v0.1.7 universal

Use 
0.1.7 universal for:

* maintainer archives
* operational knowledge handoff
* product or site governance memory
* documentation or deployment continuity artifacts
* cross-environment context archives that must remain implementation-stable

Do not use it for:

* parity-driven laboratory protocols
* experimental track orchestration that requires explicit cycle contracts
* methodology locks that depend on lab-only stage semantics

## 2\. Scoring model

Normative family:

* weighted\_sum\_with\_fail\_closed\_gates\_v1

Normative rule:

* admit an item only if gate checks pass
* then compute score = sum\_i(w\_i \* x\_i) with normalized weights
* clamp final score to \[0,1]

Required scoring fields:

* 
function
* weights
* components
* gate\_policy
* tie\_breakers

## 3\. Gate model

Universal scoring is fail-closed.
If any admission gate fails, the item must not enter the compiled view.

Minimum expected gates:

* similarity floor
* trust floor
* anchor trust floor

## 4\. Scope vs examples

scope is normative.
Examples are optional and non-normative.
Examples illustrate behavior; they do not define required behavior.

## 5\. Lineage rule

Historical lineage may reference the Week 1 semantic-collapse report and weighted-product scoring.
That lineage is informative only.
The current normative universal model is the weighted-sum plus fail-closed gate model.

## 6\. Selection rule

* use mica-lab-v0.1.5.schema.json for laboratory-grade governance
* use mica-v0.1.7-universal.schema.json for broad operational portability

## 7\. Invocation

v0.1.7 schema defines archive content but not how the archive reaches an AI session.
Three normative invocation patterns are defined in `MICA_INVOCATION_PATTERNS_v1.0.md`:

* Pattern 1 (README-as-Protocol): project-local, git-versioned, no installation required. Recommended default.
* Pattern 2 (Global Skill): cross-project, Agent Skills format, requires CLI installation.
* Pattern 3 (Workspace Directive): CLAUDE.md backstop, workspace-level.

Any project shipping a MICA v0.1.7 archive MUST implement Pattern 1 at minimum.

Known schema gaps addressed by invocation patterns (candidates for v0.1.8):
* invocation_protocol field
* session_report_format field
* drift_response_policy field
* inline_invariants_format field
* track_map field (universal equivalent of MICA-LAB track_decomposition)
