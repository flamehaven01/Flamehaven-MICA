# Invocation Capsule Fixture Playbook

Demonstrates digest-bound invocation evidence (mica.invocation.v2).

- Each loaded surface is hashed before delivery.
- `delivery_state` is `resolved` for manual runs; only an adapter may claim `emitted`.
- `capsule_hash` excludes the absolute `project_root` so it reproduces across platforms.
