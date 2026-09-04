---
name: mica-author
description: Create, maintain, optimize, or retire a repository-owned MICA package from current repository evidence. Use when the user explicitly asks to add MICA or change its archive, playbook, manifest, profiles, or retained context.
---

# MICA Author

MICA authoring changes what future AI sessions receive. Treat each existing
package as an independent object owned by its repository, not as an instance to
normalize to the latest example.

## Establish the Starting Point

1. Inspect the target README, manifest, archive, playbook, source, tests,
   runbooks, decision records, and relevant version-control evidence.
2. If MICA already exists, invoke it with the `mica-context` skill before
   editing it. Preserve its paths, schema, profiles, and vocabulary unless the
   user requests a migration or current evidence shows concrete ambiguity or
   breakage.
3. If MICA does not exist, use
   [`templates/minimal-package`](../../templates/minimal-package/) only as a
   scaffold. Replace every example with target-repository evidence.

## Create or Maintain the Four Roles

- README: add exactly one entrypoint directive naming the real manifest.
- Manifest: declare the repository-owned archive and playbook paths and select
  only the surfaces needed by each profile.
- Archive: retain only durable decisions, invariants, incidents, and origins
  supported by inspectable evidence. Omit unknown claims or mark them
  non-binding; never invent history to complete a shape.
- Playbook: record the operating and verification procedures the repository
  actually uses. Do not turn generic MICA policy into repository policy.

Update the archive when durable project truth changes. Update the playbook when
the real work or verification route changes. Do not promote transient session
output, guesses, or unreviewed summaries into either surface.

## Optimize Useful Context

1. Choose representative tasks and profiles before changing composition.
2. Record the selected roles and emitted byte count for each baseline.
3. Remove stale paths and duplicate instructions. Move domain-only procedure to
   a selected physical playbook or profile when that reduces irrelevant context
   without hiding a required invariant.
4. Emit context again and run the target repository's task-specific checks.
   Fewer bytes alone do not prove better context or better work.

## Retire Safely

- Preserve the target format's replacement or supersession evidence instead of
  silently deleting durable history.
- Remove a surface from the manifest only after no profile, launcher, or runtime
  consumer depends on it.
- Do not rewrite an existing package solely to match current MICA templates.

## Verify and Report

Run both checks after an authoring change:

```text
python <MICA_ROOT>/tools/mica_pct.py <TARGET_REPO>
python <MICA_ROOT>/tools/mica_runtime.py <TARGET_REPO> --format context
```

Report the evidence inspected, files changed, selected profile and surfaces,
context-byte delta when optimizing, checks actually run, and unresolved
unknowns. A closed contract proves resolution and emission, not that a model
understood the context.

Keep version axes distinct: the MICA tool release versions the tools,
`mica_spec` versions the invocation contract, and the consumer repository owns
any project or artifact version. Do not describe consumer memory as a MICA tool
release artifact.

For rationale and detailed role guidance, read
[`MICA_CONSUMER_AUTHORING_GUIDE.md`](../../docs/MICA_CONSUMER_AUTHORING_GUIDE.md).
