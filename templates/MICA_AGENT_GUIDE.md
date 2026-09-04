# MICA Agent Guide Template

When the agent host supports repository skills, prefer
`skills/mica-context/SKILL.md` from the MICA release. This file remains a
copyable fallback for hosts that cannot load a skill.

Copy this guide into a target repository only after replacing the placeholders with
repository-specific paths, invariants, and verification commands. It is an operating
contract for an AI maintainer, not a general project description.

## Session Start

1. Read the repository README and locate its single `MICA:INVOKE` directive.
   Do not infer a manifest path that the README did not declare.
2. Run `python tools/mica_runtime.py . --format context`. Stop if it refuses
   to emit; a summary or a successful validator is not substitute context.
3. Resolve the active memory profile. If `invocation_protocol.profiles` exists,
   the requested profile -- or `default` when none is requested -- names exactly
   the surfaces emitted, and a layer marked `loading_hint: always` that the
   profile does not name is deselected. Only when the package declares no
   profiles, emit every layer declared with `loading_hint: always`.
4. Use the emitted archive as retained project memory and the emitted playbook
   as the operating procedure before editing.
5. Call invocation `recorded` only after a valid trace exists; otherwise report
   resolved or emitted state.
6. Run the repository's declared verification command before claiming the
   package is ready.

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

Report resolved/emitted/recorded state separately, what changed, and which verification
ran. Use the existing MICA invocation trace command when the target requires operational
provenance; a null session ID is not proof of an individually identified AI session.
Update the archive or playbook only through the target repository's declared update trigger
and authority. Do not create a parallel memory file merely to preserve a session summary.
