# Contract Floor Playbook

## Why this fixture exists

`0.2.4` is the lowest contract version in `SUPPORTED_CONTRACT_VERSIONS`. It is
the floor because that contract introduced `binding.origin_episode`, the archive
binding model `PCT-010` and `PCT-011` check. Below it, there is nothing for
those checks to read.

The floor was decided from live consumer packages, none of which live in this
repository. An external package can change or disappear, so the boundary this
project publishes is pinned here instead.

## What it asserts

A package declaring the floor contract resolves end to end and draws no
compatibility warning from `PCT-006`.
