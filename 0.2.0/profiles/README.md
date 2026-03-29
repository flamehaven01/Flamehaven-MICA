# MICA v0.2.0 Profiles Index

This folder contains the **optional profile candidates** being explored on top of the stable `v0.1.9` core.

These profiles are draft extensions. They are not all equally ready for adoption.

---

## Read Order

If you want the most practical profiles first:

1. `MICA_v0.2.0_DRIFT_PROFILE.md`
2. `MICA_v0.2.0_TRACK_MAP_PROFILE.md`
3. `MICA_v0.2.0_LINEAGE_PROFILE.md`

If you want the more experimental profiles:

1. `MICA_v0.2.0_CONSISTENCY_PROFILE.md`
2. `MICA_v0.2.0_RESULT_CONTRACT_PROFILE.md`
3. `MICA_v0.2.0_APPROVAL_PROFILE.md`

---

## Current v0.2.1 Triage Status

| Profile | Status |
|---|---|
| Drift | adopt now |
| Track Map | adopt now |
| Lineage | needs dogfood trace |
| Consistency | needs dogfood trace |
| Result Contract | needs dogfood trace |
| Approval | draft only |

See also:

- `..\..\docs\MICA_v0.2.1_PROFILE_STATUS_MATRIX.md`
- `..\MICA_v0.2.0_ROADMAP.md`

---

## Design Rule

Profiles must remain:

- optional
- file-based
- memory-facing

If a profile starts behaving like a runtime policy engine or substrate manager, it has crossed the MICA boundary.
