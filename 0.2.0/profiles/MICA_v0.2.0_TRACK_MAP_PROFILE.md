# MICA v0.2.0 Track Map Profile

Status:
- draft optional profile
- not part of the stable `v0.1.9` baseline
- intended for projects whose memory should be organized by meaningful internal subdomains rather than treated as one flat whole
- v0.2.1 triage status: `adopt now`

## v0.2.1 Triage Note

Status: `adopt now`

Minimal adoption contract:
- `track_map`
- optional `track_authority_hint`

Do not use when:
- the project is genuinely single-surface
- track labels would add classification ceremony without reducing ambiguity

## Purpose

The `Track Map Profile` gives MICA a structured way to describe **project subdomains**.

Instead of treating the project as one undifferentiated unit, it allows memory, invariants, and drift to be associated with named tracks.

This is useful when a project has clearly distinct zones such as:

- mathematical core
- documentation
- dashboard or interface
- tests
- data pipeline

## Design Rule

The track layer must:

- remain optional
- remain file-based
- remain descriptive, not orchestration-heavy
- help organize memory rather than create a new runtime subsystem

The purpose is mapping and scoping, not execution.

## Core Idea

Base MICA already knows:

- what the project is
- what files make up the memory package
- what invariants and lessons exist

The `Track Map Profile` adds one more question:

`Which part of the project does this memory or constraint belong to?`

That reduces ambiguity and makes later profiles more useful.

## Proposed Components

### 1. track_map

Defines the named tracks that matter in a given project.

Draft structure:

```yaml
track_map:
  - id: TRK-001
    name: math_core
    purpose: numerical model, scoring logic, physical consistency
    primary_surfaces:
      - code
      - archive
      - playbook
  - id: TRK-002
    name: docs
    purpose: canonical explanation and written narrative
    primary_surfaces:
      - readme
      - playbook
      - changelog
  - id: TRK-003
    name: dashboard
    purpose: user-visible explanation and interface outputs
    primary_surfaces:
      - ui
      - docs
  - id: TRK-004
    name: tests
    purpose: regression and validity checks
    primary_surfaces:
      - tests
      - archive
```

### 2. track_specific_invariants

Allows invariants to declare their primary track.

Draft example:

```yaml
track_specific_invariants:
  - invariant_id: DI-001
    track: math_core
  - invariant_id: DI-003
    track: code_hygiene
```

This makes it clearer where a rule belongs and where violations should be interpreted first.

### 3. track_specific_drift

Allows drift classes to be scoped to particular tracks.

Draft example:

```yaml
track_specific_drift:
  - drift_id: DRF-001
    track: math_core
  - drift_id: DRF-004
    track: docs
```

This prevents every drift event from being treated as equally global.

### 4. track_authority_hint

Optional hint about who or what artifact has strongest authority for a given track.

Draft example:

```yaml
track_authority_hint:
  - track: math_core
    authority_surface: code
  - track: docs
    authority_surface: playbook
  - track: dashboard
    authority_surface: ui
```

This does not replace approval or governance logic.
It simply helps later sessions decide where to look first.

## Suggested Placement

Recommended minimal placement:

1. define `track_map` in `mica.yaml`
2. explain track meanings in the playbook
3. let lessons reference track ids when recording failures or updates

Current recommendation:
- keep the profile lightweight
- use it as an index and scoping layer
- avoid turning it into a dependency graph

## Relationship to Drift Profile

The `Track Map Profile` makes drift more precise.

Without track mapping:

- drift is global and vague

With track mapping:

- drift can be classified as belonging primarily to `math_core`, `docs`, `dashboard`, or another declared track

That makes response and repair much clearer.

## Relationship to design_invariants

The `Track Map Profile` does not create new invariants.

It gives existing invariants a clearer home.

Example:

- `DI-001 no-arbitrary-weights` belongs to `math_core`
- `DI-003 ascii-source-only` belongs to `code_hygiene`

This improves interpretation, prioritization, and later drift analysis.

## Why This Matters for Flamehaven-TOE

For `Flamehaven-TOE`, track mapping is especially natural because the project already behaves like multiple linked but distinct systems:

- mathematical formulation
- documentation and narrative explanation
- dashboard-facing explanation surfaces
- tests and cross-check logic

Without track mapping, all of these sit in one memory bucket.
With track mapping, lessons and drift events can be attached to the part of the project they actually belong to.

That makes the memory system more actionable without making it more coupled.

## Minimal Adoption Candidate

The smallest useful version of this profile would add only:

- `track_map`
- optional `track_authority_hint`

and delay track-specific invariants or drift bindings until actual dogfood cycles show they are needed.

## Risks

Main risks of this profile:

- inventing too many tracks
- turning track labels into bureaucracy
- confusing map structure with actual authority

That is why the first version should keep the number of tracks small and tied to real project maintenance patterns.

## Acceptance Test

The profile is worth keeping only if, in dogfood use:

- it makes lessons easier to classify
- it helps drift events point to the right repair surface faster
- it reduces session ambiguity without overcomplicating the package

## Current Decision

Keep the `Track Map Profile` in `v0.2.0` as a draft profile candidate.

It is a strong complement to the `Drift Profile`, especially for research-heavy or multi-surface projects such as `Flamehaven-TOE`.
