# MICA-LAB-ANCHOR

This folder is the stable template set for methodology/governance/reproducibility-first experiment cycles.

## Required Outputs
1. `MICA_LAB_ANCHOR_METHOD_LOCK.json`
2. `MICA_LAB_ANCHOR_RUN_CONTEXT.json`
3. `MICA_LAB_ANCHOR_ARTIFACT_MANIFEST.json`
4. `MICA_LAB_ANCHOR_STAGE_GATE_SNAPSHOT.json`
5. `MICA_LAB_ANCHOR_VERDICT_BENCHMARK.json`
6. `MICA_LAB_ANCHOR_MULTIAXIS_COMPARE_32_33_34.json`
7. `MICA_LAB_ANCHOR_TRACEABILITY_MAP.jsonl`
8. `MICA_LAB_ANCHOR_SCOPE_GUARD_REPORT.json`
9. `MICA_LAB_ANCHOR_DEVIATION_LOG.json`
10. `MICA_LAB_ANCHOR_GO_NO_GO.md`

## Execution Order (Hard Contract)
- Gate-0: method lock
- Gate-1: parity verdict benchmark (PASS/BLOCK)
- Gate-2: artifact/hash integrity
- Gate-3: 32/33/34 multiaxis compare
- Gate-4: scope guard + deviation log
- Gate-5: GO/NO-GO decision

## Notes
- This template set is for measured values and reproducibility only.
- No efficacy/safety/regulatory claims are allowed from this output set.
