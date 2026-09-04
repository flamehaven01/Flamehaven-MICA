# MICA Cross-Repo Adoption Guide

## Purpose

If another repository is expected to use MICA, do not hand it only a raw archive JSON or a playbook markdown.
The target repository must receive a loadable MICA package contract.

The entry point is the target repository's README. Its `MICA:INVOKE` directive
resolves the repository's selected manifest; the manifest then selects the
archive and playbook through `layers`.

For the actual authoring and AI session behavior, use the
[MICA Consumer Authoring Guide](MICA_CONSUMER_AUTHORING_GUIDE.md) and its
[complete minimal package](../templates/minimal-package/). This guide shows
known package shapes; the authoring guide defines the common invocation
behavior. The examples are not a normalization mandate.

## Minimal rule

A target repository can be considered MICA-capable only when all of the following are true:

- README contains exactly one valid `MICA:INVOKE` directive near the top
- that directive resolves the package's `mica.yaml`
- the contract declares at least `archive` and `playbook`
- declared layer paths exist inside the target repo
- the consumer can load every `loading_hint: always` layer without guessing filenames

Raw files without a contract are legacy assets, not a portable MICA package.

## What the loader should do

1. Read the README's `MICA:INVOKE` directive and resolve its manifest path.
2. Run `mica_runtime.py --format context`; do not substitute a validator summary.
3. Parse `mica_spec`, `mode`, `layers`, and `invocation_protocol`.
4. **If a profile applies, the profile decides.** A requested profile, or
   `profiles.default` when none is requested, names exactly the surfaces this
   session receives. `loading_hint` does not override it: a layer marked
   `always` that the active profile does not name is deselected, not loaded.
5. Only when the package declares no profiles: load every layer marked
   `loading_hint: always`, and `on_demand` layers when task scope requires them.
6. Deliver to the agent only what `agent_context_surfaces` permits, and never a
   surface listed in `operator_only_surfaces`.
7. Respect `mode`.
8. Treat flow-plane files as optional unless `flow_policy.enabled=true`.

Loading every `always` layer regardless of the active profile is the most
likely way to get this wrong, because it looks correct and quietly delivers
more context than the package asked for.

## Observed packaging profiles

### 1. Minimal portable package

Closest fixture: [`fixtures/memory_profiles`](../fixtures/memory_profiles)

Use this when:

- the target repo needs one portable memory package
- path stability matters more than versioned file names
- you want the easiest adoption contract

Shape:

- `mica.yaml`
- `README.md`
- `memory/mica_archive.json`
- `memory/mica_playbook.md`

This is the simplest scaffold for a new target repo.

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

## Selection guidance by target type

- Small or single-domain repo: use the minimal portable profile (1).
- Large multi-domain repo: use the flamehaven-audit-reports profile.
- Distributed read-only deployed copies: use the STEM-BIO-AI profile.
- Legacy packages with filename rotation: tolerate the historical versioned profile (2), but do not treat it as the default future shape.

## Portable cross-repo package

When handing MICA to another repo, provide these roles, using paths appropriate
to that repository:

- `README.md` with the invocation directive
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

## Example target-repo layouts

For a small new repo, this is a useful scaffold:

```text
repo/
  README.md
  mica.yaml
  memory/
    mica_archive.json
    mica_playbook.md
```

For a large repo, a routed shape may be more useful:

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

Portable model:

- archive JSON
- playbook markdown
- `mica.yaml` declares relationship explicitly
- loader resolves package without human interpretation

That explicit relationship, not uniform filenames, is the key portability
step.

## Practical rule for Flamehaven packages

If the goal is "show this MICA to another repo and let that repo use it," first
preserve the target repository's own memory organization. Use these two shapes
as references when no usable organization exists:

- Default minimal: CAS-style stable-path package
- Default scalable: audit-reports-style router package

Other explicit, resolvable shapes are valid. A repository-specific layout is
not legacy merely because it differs from these examples.

The executable consumer fixtures cover three shapes without declaring one of
them canonical:

- [`consumer_legacy_root`](../fixtures/consumer_legacy_root/): root manifest
  with versioned archive and playbook paths
- [`consumer_profile_multi_playbook`](../fixtures/consumer_profile_multi_playbook/):
  profiles select distinct domain playbooks
- [`consumer_nested_launcher`](../fixtures/consumer_nested_launcher/): nested
  `memory/mica.yaml` used through an existing thin launcher

## Pre-materialized compatibility

The runtime can still read a package that declares the historical
`memory_first` mode when that package already contains its exported archive and
playbook. MICA no longer ships the separate structured-memory authoring CLI.
The stable adoption target is README, `mica.yaml`, archive, and playbook.

## Acceptance checklist for a target repo

A target repo is ready only if:

- the environment running MICA validators provides `pyyaml` and `jsonschema`
- the README-declared manifest exists
- every declared `always` layer exists
- `python <MICA_ROOT>/tools/mica_pct.py <target_repo>` can resolve the package honestly
- the repo does not require filename guessing
- the AI can identify and apply the relevant archive memory and playbook procedure
- no filename or schema is inferred merely from another repository's example
