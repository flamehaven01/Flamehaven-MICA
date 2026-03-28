# MICA-LAB-ANCHOR One-Page Runbook

## Load Order (Strict)
1. `MICA_LAB_ANCHOR_METHOD_LOCK.json`
2. `MICA_LAB_ANCHOR_RUN_CONTEXT.json`
3. `MICA_LAB_ANCHOR_ARTIFACT_MANIFEST.json`
4. `MICA_LAB_ANCHOR_STAGE_GATE_SNAPSHOT.json`
5. `MICA_LAB_ANCHOR_VERDICT_BENCHMARK.json`
6. `MICA_LAB_ANCHOR_MULTIAXIS_COMPARE_32_33_34.json`
7. `MICA_LAB_ANCHOR_SCOPE_GUARD_REPORT.json`
8. `MICA_LAB_ANCHOR_DEVIATION_LOG.json`
9. `MICA_LAB_ANCHOR_GO_NO_GO.md`

## Verification Commands (3)
```powershell
# 1) JSON parse check (all JSON/JSONL first line)
$root='D:\Sanctum\Flamehaven-Labs\Rexsyn Experiment\EXP-034-METHODLOCK-MODAL-EXPANSION\MICA-LAB-ANCHOR';
Get-ChildItem $root -File -Include *.json,*.jsonl | ForEach-Object {
  if ($_.Extension -eq '.json') { Get-Content $_.FullName -Raw | ConvertFrom-Json | Out-Null }
  else { (Get-Content $_.FullName -TotalCount 1 | ConvertFrom-Json) | Out-Null }
}; 'JSON_PARSE=PASS'

# 2) parity/order/hold contract check
$ml=Get-Content "$root\MICA_LAB_ANCHOR_METHOD_LOCK.json" -Raw | ConvertFrom-Json;
$ok = ($ml.parity_contract.metric -eq 'sample_arm_balanced_accuracy') -and ([double]$ml.parity_contract.target_value -eq 1.0) -and ($ml.parity_contract.must_pass_before_extension -eq $true) -and (($ml.track_order -join ',') -eq 'Track-A,Track-B,Track-C,Track-D') -and ($ml.hold_behavior -eq 'rerun_from_first_failed_gate');
if(-not $ok){ throw 'METHOD_LOCK_CONTRACT_FAIL' }; 'METHOD_LOCK_CONTRACT=PASS'

# 3) manifest sha256 integrity check (entries where exists=true)
$mf=Get-Content "$root\MICA_LAB_ANCHOR_ARTIFACT_MANIFEST.json" -Raw | ConvertFrom-Json;
$errs=@(); foreach($e in $mf.entries){ if($e.exists -eq $true){ if(-not (Test-Path $e.path)){ $errs += "missing:$($e.path)"; continue }; $h=(Get-FileHash -LiteralPath $e.path -Algorithm SHA256).Hash.ToLower(); if($h -ne ([string]$e.sha256).ToLower()){ $errs += "hash_mismatch:$($e.path)" } } }
if($errs.Count -gt 0){ $errs | ForEach-Object { Write-Output $_ }; throw 'MANIFEST_INTEGRITY_FAIL' }; 'MANIFEST_INTEGRITY=PASS'
```

## Operational Rule
- Any verification failure => `HOLD` and rerun from `first_failed_gate`.
