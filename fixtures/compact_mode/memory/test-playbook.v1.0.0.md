# Compact Mode Fixture Playbook

This fixture represents an intentional COMPACT_MODE deployment.

## Operating Rules

- No mica.yaml. pct=LEGACY is the expected terminal state.
- Archive + playbook are the authoritative memory surfaces.
- DI-001 is enforced: absence of mica.yaml is a deliberate architectural choice.
