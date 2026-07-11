# MICA Agent Guide Template

Copy this guide into a target repository only after replacing the placeholders with
repository-specific paths, invariants, and verification commands. It is an operating
contract for an AI maintainer, not a general project description.

## Session Start

1. Find `mica.yaml` at repository root; otherwise use `memory/mica.yaml`.
2. Read every layer declared with `loading_hint: always`.
3. Read an `on_demand` layer only when the task requires that domain.
4. State the declared and resolved archive and playbook surfaces before editing.
5. Call invocation `recorded` only after a valid trace exists; otherwise report declared or resolved state.
6. Run the repository's declared verification command before claiming the package is ready.

Do not guess filenames, infer missing context, or silently replace a declared surface
with a similar document.

## Working Rules

- Treat the archive as the source of project invariants and prior decisions.
- Treat the playbook as the task procedure and validation route.
- Keep facts, hypotheses, and operator review material distinct.
- Do not promote a transient note, tool output, or unreviewed recall into project truth.
- Do not load an `operator_only` surface into agent context unless the contract explicitly permits it.
- If a required surface is absent, stale, or contradictory, report the condition before editing the governed area.

## Session End

Report declared/resolved/recorded state separately, what changed, and which verification
ran. Use the existing MICA invocation trace command when the target requires operational
provenance; a null session ID is not proof of an individually identified AI session.
Update the archive or playbook only through the target repository's declared update trigger
and authority. Do not create a parallel memory file merely to preserve a session summary.
