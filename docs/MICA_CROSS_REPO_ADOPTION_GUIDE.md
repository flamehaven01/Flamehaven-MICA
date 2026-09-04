# MICA Cross-Repo Adoption Guide

## Purpose

If another repository is expected to use MICA, do not hand it only a raw archive JSON or a playbook markdown.
The target repository must receive a loadable MICA package contract.

The entry point is `mica.yaml`.
The rest of the memory surface is discovered through `layers`.

For the actual authoring and AI session behavior, use the
[MICA Consumer Authoring Guide](MICA_CONSUMER_AUTHORING_GUIDE.md) and its
[minimal template](../templates/mica-consumer-minimal.yaml). This guide selects a package
shape; the authoring guide defines how the consumer writes and invokes it.

## Minimal rule

A target repository can be considered MICA-capable only when all of the following are true:

- a `mica.yaml` entrypoint exists at repo root or `memory/mica.yaml`
- the contract declares at least `archive` and `playbook`
- declared layer paths exist inside the target repo
- the consumer can load every `loading_hint: always` layer without guessing filenames

Raw files without a contract are legacy assets, not a portable MICA package.

## What the loader should do

1. Find `mica.yaml` in repo root, else `memory/mica.yaml`.
2. Parse `mica_spec`, `mode`, and `layers`.
3. Load every layer marked `loading_hint: always`.
4. Load `on_demand` layers only when task scope requires them.
5. Respect `mode`.
6. Treat flow-plane files as optional unless `flow_policy.enabled=true`.

## Recommended packaging profiles

### 1. Minimal portable package

Closest fixture: [`fixtures/memory_profiles`](../fixtures/memory_profiles)

Use this when:

- the target repo needs one governed memory package
- path stability matters more than versioned file names
- you want the easiest adoption contract

Shape:

- `mica.yaml`
- `memory/mica_archive.json`
- `memory/mica_playbook.md`

This should be the default profile for new target repos.

### 2. Historical versioned package

In use by one internal package. No public example ships for this shape.

Use this when:

- file-level version history is itself part of the operating model
- you want archive/playbook rotation via filename changes

Tradeoff:

- still portable
- but external consumers must rely on `mica.yaml` every time because filenames churn

Recommendation:

- keep this for legacy continuity
- do not make it the default new-package shape for third-party repos

### 3. Distributed read-only consumer package

Public example: [STEM-BIO-AI](https://github.com/flamehaven01/STEM-BIO-AI) (`memory/mica.yaml`)

Use this when:

- one upstream package is the single update authority
- deployed copies must consume but not mutate archive truth
- lessons may be separated from core playbook

This is the right profile for mirrored or shipped skill packages.

### 4. Router plus domain-island package

Public example: [flamehaven-audit-reports](https://github.com/flamehaven01/flamehaven-audit-reports) (`mica.yaml`), the package measured in the v3.0.0 release notes

Use this when:

- one repo covers multiple operational lanes or domains
- always-load context must stay slim
- lane-specific playbooks should load only on demand

This is the best profile for large target repos.

## Best recommendation by target type

- Small or single-domain repo: use the minimal portable profile (1).
- Large multi-domain repo: use the flamehaven-audit-reports profile.
- Distributed read-only deployed copies: use the STEM-BIO-AI profile.
- Legacy packages with filename rotation: tolerate the historical versioned profile (2), but do not treat it as the default future shape.

## Canonical cross-repo handoff format

When handing MICA to another repo, give it this bundle:

- `mica.yaml`
- `memory/` directory with every referenced layer
- optional flow-plane files only if the target actually uses flow validation:
  - `memory/mica.observe.jsonl`
  - `memory/mica.candidates.json`
  - `memory/mica.recall.jsonl`

Do not hand over only:

- archive JSON alone
- playbook markdown alone
- prose descriptions of memory layout

## Preferred target-repo install pattern

For new repos, prefer this shape:

```text
repo/
  mica.yaml
  memory/
    mica_archive.json
    mica_playbook.md
```

For large repos, prefer this shape:

```text
repo/
  mica.yaml
  memory/
    verification-ledger.mica.archive.json
    verification-ledger-playbook.md
    playbook-common.md
    playbook-domain-a.md
    playbook-domain-b.md
```

## Migration from old JSON + playbook delivery

Old model:

- archive JSON
- playbook markdown
- human explains how they relate

New model:

- archive JSON
- playbook markdown
- `mica.yaml` declares relationship explicitly
- loader resolves package without human interpretation

That is the key portability step.

## Practical rule for Flamehaven packages

If the goal is "show this MICA to another repo and let that repo use it," the package should be normalized into one of these two defaults:

- Default minimal: CAS-style stable-path package
- Default scalable: audit-reports-style router package

Everything else should be treated as compatibility mode, not the preferred forward shape.

## When the target repo needs live memory, not only governed exports

If the target repository is expected to capture sessions, maintain live memory objects,
or project slots and graph state locally, the minimal archive-plus-playbook package is not
enough.

Use the memory-first draft instead:

- [MICA_v0.2.9_MEMORY_FIRST_ARCHITECTURE.md](MICA_v0.2.9_MEMORY_FIRST_ARCHITECTURE.md)
- [templates/mica-v0.2.9-memory-first.yaml](../templates/mica-v0.2.9-memory-first.yaml)

Rule:

- if the target only needs portable governed memory, use the minimal or router package
- if the target must operate MICA as a live memory substrate, install the memory-first shape

Consumer entrypoint:

- once the memory-first shape is installed, the target repo can rebuild its derived MICA surfaces with a single command:
  `python tools/mica_memory.py <target_repo> materialize`
- this command synthesizes candidate memories from observations, rewrites archive/playbook exports, and refreshes slots/graph projections
- review and promotion remain explicit; `materialize` does not auto-approve memories

## Acceptance checklist for a target repo

A target repo is ready only if:

- `mica.yaml` exists
- every declared `always` layer exists
- `python tools/mica_pct.py <target_repo>` can resolve the package honestly
- the repo does not require filename guessing
- package shape is either minimal stable-path or router-plus-islands unless there is a strong reason otherwise
