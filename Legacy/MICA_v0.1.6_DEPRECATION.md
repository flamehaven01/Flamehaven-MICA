# MICA v0.1.6 Universal Deprecation Notice

Status: deprecated
Deprecated schema: mica-v0.1.6-universal.schema.json
Replacement: mica-v0.1.7-universal.schema.json

Reason for deprecation:
- scoring_policy.function remained pseudo-code rather than a normative structured model
- weights were not required by schema, leaving implementers without a deterministic interpretation surface
- scope was optional while xamples created a stronger implied priority than intended

Impact:
- v0.1.6 may still be readable as a provisional draft
- v0.1.6 should not be used as the normative universal contract for new archives or implementations

Migration guidance:
1. move to mica-v0.1.7-universal.schema.json
2. provide explicit scoring weights
3. use fail-closed gate policy for admission
4. treat scope as normative and xamples as optional
