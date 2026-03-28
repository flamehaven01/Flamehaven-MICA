# MICA v0.2.0 self_test_policy — Package Completeness Examples

`self_test_policy` block examples for two projects.  
These blocks are checks **added** to the `self_test_policy` field in the existing v0.1.8.1 archive JSON.  
Existing checks (provenance, design_invariant, etc.) are preserved as-is.

---

## Example A: flamehaven-space (memory_injection)

```json
"self_test_policy": {
  "enabled": true,
  "run_on": ["session_start", "pre_handoff"],
  "on_failure": "require_acknowledgment",
  "note": "v0.2.0 package completeness checks. Run in order — hard-fail checks stop session before softer checks execute.",
  "checks": [

    {
      "id": "PCT-001",
      "description": "mica.yaml composition contract exists at project root",
      "check_type": "mica_yaml_present",
      "severity": "critical",
      "on_fail": "HALT: composition contract missing. AI cannot verify package integrity. Locate or create mica.yaml before proceeding.",
      "expression": "file_exists('mica.yaml')"
    },

    {
      "id": "PCT-002",
      "description": "mica.yaml contains required fields: mica_spec, mode, and at least 2 layers",
      "check_type": "mica_yaml_fields_valid",
      "severity": "critical",
      "on_fail": "HALT: mica.yaml is malformed. Required fields (mica_spec, mode, layers) must be present.",
      "target": "mica.yaml root",
      "expression": "exists($.mica_spec) and exists($.mode) and len($.layers) >= 2"
    },

    {
      "id": "PCT-003",
      "description": "All required layer paths declared in mica.yaml exist on disk",
      "check_type": "mica_yaml_paths_exist",
      "severity": "critical",
      "on_fail": "HALT: ghost path detected in mica.yaml. Declared layer file does not exist. Verify paths or update mica.yaml.",
      "target": "mica.yaml layers[].path where required != false",
      "expression": "all($.layers[?(@.required != false)], file_exists($.path))"
    },

    {
      "id": "PCT-004",
      "description": "memory_injection mode requires archive layer + playbook layer",
      "check_type": "mica_yaml_mode_coherent",
      "severity": "error",
      "on_fail": "ACKNOWLEDGE: mode=memory_injection requires both 'archive' and 'playbook' layers. Package composition is incomplete for this mode.",
      "target": "mica.yaml mode + layers[].name",
      "expression": "any($.layers, $.name == 'archive') and any($.layers, $.name == 'playbook')"
    },

    {
      "id": "PCT-005",
      "description": "Archive JSON mica_spec field presence (legacy detection)",
      "check_type": "mica_spec_present",
      "severity": "info",
      "on_fail": "INFO: archive does not have mica_spec field (legacy-valid, COMPAT-001). Add mica_spec: '0.2.0' on next maintenance version bump.",
      "target": "memory/flamehaven-space-maintainer.mica.v1.2.7.json root"
    },

    {
      "id": "PCT-006",
      "description": "mica.yaml mica_spec and archive mica_spec are aligned when both present",
      "check_type": "mica_spec_aligned",
      "severity": "warning",
      "on_fail": "WARN: version axis mismatch. mica.yaml and archive are on different mica_spec versions. Sync on next maintenance cycle.",
      "target": "mica.yaml mica_spec vs archive mica_spec",
      "expression": "not exists($.mica_spec) or ($.mica_spec == mica_yaml.mica_spec)"
    },

    {
      "id": "PCT-007",
      "description": "Umbrella: MICA package is in closed, trustworthy contract state",
      "check_type": "mica_package_complete",
      "severity": "error",
      "on_fail": "ACKNOWLEDGE: MICA package is not fully closed. Review PCT-001 through PCT-006 results. Package is readable but not machine-verified complete.",
      "expression": "PCT-001.pass and PCT-002.pass and PCT-003.pass and PCT-004.pass"
    }

  ]
}
```

---

## Example B: CareChainGovernanceEngine (protocol_evolution)

```json
"self_test_policy": {
  "enabled": true,
  "run_on": ["session_start", "pre_handoff", "on_demand"],
  "on_failure": "require_acknowledgment",
  "note": "v0.2.0 package completeness checks for protocol_evolution mode. lessons layer is required. exemplars is optional (required: false in mica.yaml).",
  "checks": [

    {
      "id": "PCT-001",
      "description": "mica.yaml composition contract exists at project root",
      "check_type": "mica_yaml_present",
      "severity": "critical",
      "on_fail": "HALT: composition contract missing.",
      "expression": "file_exists('mica.yaml')"
    },

    {
      "id": "PCT-002",
      "description": "mica.yaml contains required fields: mica_spec, mode, and at least 2 layers",
      "check_type": "mica_yaml_fields_valid",
      "severity": "critical",
      "on_fail": "HALT: mica.yaml malformed.",
      "target": "mica.yaml root",
      "expression": "exists($.mica_spec) and exists($.mode) and len($.layers) >= 2"
    },

    {
      "id": "PCT-003",
      "description": "All required layer paths declared in mica.yaml exist on disk",
      "check_type": "mica_yaml_paths_exist",
      "severity": "critical",
      "on_fail": "HALT: ghost path in mica.yaml. lessons/ or archive path missing.",
      "target": "mica.yaml layers[].path where required != false",
      "expression": "all($.layers[?(@.required != false)], file_exists($.path))"
    },

    {
      "id": "PCT-004",
      "description": "protocol_evolution mode requires archive + playbook + lessons layers",
      "check_type": "mica_yaml_mode_coherent",
      "severity": "error",
      "on_fail": "ACKNOWLEDGE: mode=protocol_evolution requires 'archive', 'playbook', and 'lessons' layers. lessons/ directory is essential for dogfood cycle tracking.",
      "target": "mica.yaml mode + layers[].name",
      "expression": "any($.layers, $.name == 'archive') and any($.layers, $.name == 'playbook') and any($.layers, $.name == 'lessons')"
    },

    {
      "id": "PCT-005",
      "description": "Archive mica_spec field presence (template-valid detection)",
      "check_type": "mica_spec_present",
      "severity": "info",
      "on_fail": "INFO: CCGE BASELINE archive has mica_schema_version='baseline-draft' (template-valid, COMPAT-004). When instantiating for a target repo, add mica_spec: '0.2.0'.",
      "target": "memory/CCGE_TARGET_MICA_ARCHIVE_BASELINE.json root"
    },

    {
      "id": "PCT-006",
      "description": "mica.yaml and archive mica_spec are aligned when both present",
      "check_type": "mica_spec_aligned",
      "severity": "warning",
      "on_fail": "WARN: version axis drift. Align on next dogfood cycle close.",
      "target": "mica.yaml mica_spec vs archive mica_spec",
      "expression": "not exists($.mica_spec) or ($.mica_spec == mica_yaml.mica_spec)"
    },

    {
      "id": "PCT-007",
      "description": "Umbrella: MICA package is in closed, trustworthy contract state",
      "check_type": "mica_package_complete",
      "severity": "error",
      "on_fail": "ACKNOWLEDGE: MICA package not fully closed. Review PCT-001 through PCT-006.",
      "expression": "PCT-001.pass and PCT-002.pass and PCT-003.pass and PCT-004.pass"
    }

  ]
}
```

---

## Severity Decision Table

| Check | Severity | Reason |
|-------|----------|------|
| `mica_yaml_present` | `critical` | If the contract itself is missing, nothing can be trusted |
| `mica_yaml_fields_valid` | `critical` | Incomplete contract = equivalent to having none |
| `mica_yaml_paths_exist` | `critical` | A contract pointing to non-existent files = ghost contract |
| `mica_yaml_mode_coherent` | `error` | Mode mismatch = readable but structurally incorrect |
| `mica_spec_present` | `info` | legacy is valid; resolve on next version bump |
| `mica_spec_aligned` | `warning` | drift = readable but version axis is misaligned |
| `mica_package_complete` | `error` | First 4 must pass for a complete contract |

---

## Coexistence with v0.1.8.1 Existing Checks

Package completeness checks (PCT-*) are placed before the existing v0.1.8.1 checks.

```
Order:
  PCT-001 ~ PCT-007  ← v0.2.0 new (package completeness)
  STC-001+           ← v0.1.8.1 existing (internal consistency)
```

Existing checks (provenance_sha256_format, design_invariant_severity_valid, etc.) are preserved as-is.  
PCT-* checks verify "whether the MICA package is closed,"  
while existing checks verify "whether the archive JSON is internally consistent."  
The two layers are mutually complementary.

