# README invocation block

Copy the block below into the target repository's `README.md`, near the top,
where a session will read it before doing anything else.

This is the entrypoint. Without it a package has memory and no way in: the
archive and playbook sit on disk and nothing opens them. `mica.yaml` says which
files are memory; the README is what makes a session go and read it.

Replace `<path>` and the profile names. Delete lines that do not apply.

---

## The block

```markdown
## MICA memory

<!-- MICA:INVOKE manifest="mica.yaml" -->

This repository carries its memory as a MICA package. Before doing work here,
load it.

1. Read `mica.yaml` at the repository root. It declares which files hold this
   project's memory and which of them a session receives.
2. Read the archive it names. That is what this project has already decided and
   must not relearn. Its design invariants are binding.
3. Read the playbook it names. That is how work is done here.
4. Load the selected surfaces into this session before making changes.

    python tools/mica_runtime.py . --format context

   Use `--profile <name>` when the task matches one:

   | Profile | Use it for |
   |---|---|
   | `default` | routine work |
   | `<name>` | `<when this profile is the right one>` |

   The active profile decides what you receive. A layer marked
   `loading_hint: always` that the profile does not name is deselected, not
   loaded.

Do not guess filenames, infer missing context, or replace a declared surface
with your own summary of it. If a declared surface is missing or unreadable,
stop and report that rather than proceeding without it.
```

---

## What a reader has to be able to do with it

The block is not decoration. A session that reads it must be able to reach the
memory without asking anything else:

- exactly one `MICA:INVOKE` directive must point to the package's `mica.yaml`
- the archive and playbook it declares must exist and be readable
- the profiles the table lists must exist in `invocation_protocol.profiles`

`python tools/mica_pct.py <path>` checks the directive, manifest, archive,
playbook, and declared profiles. It does not parse or standardise the surrounding
prose. The consumer owns its README; MICA verifies only that the entrypoint is
real and resolves to the same manifest the tools use.

## Where the block goes

Near the top, before installation or usage instructions. A session that reads
the first screen of a README and starts working should already have been told
to load the memory. A block at the bottom is a block that gets read after the
work is done.

## What not to put in it

- The memory itself. The block points at the archive and playbook; it does not
  summarise them. A summary in the README is a second copy that drifts.
- Anything an operator should see but an agent should not. That belongs in
  `invocation_protocol.operator_only_surfaces`.
- Version numbers of the tools. The package declares `mica_spec`; the README
  does not need to repeat it.
