# MICA Installer

This folder contains a **Windows-first MICA bootstrap installer**.

It is not a package manager installer like `ghost`.
MICA is file-based, so this installer's job is to **insert a valid MICA package into a target project**.

## What it does

Given a target project path, the installer will:

1. detect placement context
   - standalone
   - agent OS
   - skill
2. detect or accept an explicit mode
   - `memory_injection`
   - `protocol_evolution`
3. create:
   - `mica.yaml`
   - archive JSON
   - playbook Markdown
4. create `lessons/` and `exemplars/` directories when needed
5. write an installation report artifact

## What it does not do

- it does not modify runtime code
- it does not add hooks into Python or Node execution
- it does not auto-update PATH
- it does not overwrite an existing `mica.yaml` unless `-Force` is used

## Files

| File | Role |
|---|---|
| `install-mica.ps1` | main installer |

## Usage

```powershell
powershell -ExecutionPolicy Bypass -File .\install-mica.ps1 -TargetPath 'D:\Sanctum\SomeProject'
```

Optional explicit mode:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-mica.ps1 -TargetPath 'D:\Sanctum\SomeProject' -Mode protocol_evolution
```

Plan only:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-mica.ps1 -TargetPath 'D:\Sanctum\SomeProject' -PlanOnly
```

Force overwrite if a MICA package already exists:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-mica.ps1 -TargetPath 'D:\Sanctum\SomeProject' -Force
```

## Output

The installer writes a report:

- `memory/mica-install-report.json`

or, if `memory/` does not yet exist at write time:

- `[project-root]/mica-install-report.json`

## Spec source

This installer targets the stable `v0.1.9` MICA contract and reads the local spec tree in this repository.
