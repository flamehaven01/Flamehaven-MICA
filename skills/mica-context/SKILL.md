---
name: mica-context
description: Use a repository's MICA contract before changing it. Resolve the README entrypoint and manifest, emit the selected archive and playbook context, apply repository-specific memory to the requested task, and report what was actually loaded. Use when a target repository declares MICA or the user asks to use or adopt MICA.
---

# MICA Context

MICA provides one consistent use protocol, not one mandatory memory layout.
Preserve the target repository's filenames, paths, profiles, and playbook style.

## Use Existing MICA

1. Read the target repository's README and locate its `MICA:INVOKE`
   directive. Resolve exactly the manifest it names; do not guess a root-level
   `mica.yaml` when the repository declares another path.
2. Select the requested profile. If none was requested and the manifest has
   profiles, use its `default` profile. Do not add extra `always` layers to a
   profile that did not select them.
3. Run the target's context command when it provides one. Otherwise use the
   matching MICA runtime:

   ```text
   python <MICA_ROOT>/tools/mica_runtime.py <TARGET_REPO> --format context
   ```

4. Stop if context emission fails. A validator result, file list, or `CLOSED`
   summary is not a substitute for the emitted content.
5. Read the emitted archive as retained repository memory and the emitted
   playbook as repository-specific operating instructions. Identify the
   decisions, invariants, and procedures relevant to the current request
   before changing an artifact.
6. Perform the requested work under the target playbook. If current code or
   direct evidence conflicts with memory, report the conflict instead of
   silently choosing either side.
7. Report the selected profile, emitted surfaces, relevant memory applied, and
   verification actually run. Distinguish `resolved`, `emitted`, and
   `recorded`; none alone proves that a model understood or obeyed context.

## Adapt, Do Not Normalize

- Do not rename or replace a repository's archive and playbook merely to match
  MICA examples.
- Do not infer that one archive schema, directory, or playbook organization is
  universal. The manifest owns each repository's composition.
- Do not load operator-only material into agent context.
- Do not add flow, recall, handoff, trace, deployment, or SDLC machinery unless
  the repository or user explicitly requires it.
- Do not turn transient output or an unreviewed note into durable memory.

## Adopt MICA When Explicitly Requested

Use `templates/minimal-package/` only as a scaffold. Rewrite its archive and
playbook from current repository evidence, set paths in the manifest, and add
the README directive. Existing repositories may keep different paths and
formats when the runtime can resolve and emit them truthfully.

Never invent project decisions, incidents, invariants, or verification
commands to complete a template.
