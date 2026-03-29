[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TargetPath,

    [ValidateSet("auto", "memory_injection", "protocol_evolution")]
    [string]$Mode = "auto",

    [ValidateSet("auto", "standalone", "agent_os", "skill")]
    [string]$Context = "auto",

    [string]$ProjectName = "",
    [switch]$Force,
    [switch]$PlanOnly
)

$ErrorActionPreference = "Stop"

function Write-Info($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success($Message) {
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-WarnMsg($Message) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Convert-ToKebabCase([string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Name)) { return "" }
    $value = $Name -replace '([a-z0-9])([A-Z])', '$1-$2'
    $value = $value -replace '[^A-Za-z0-9]+', '-'
    $value = $value.Trim('-').ToLowerInvariant()
    return $value
}

function Ensure-Dir([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Get-PrimaryLanguage([string]$ProjectRoot) {
    $counts = @{
        Python = (Get-ChildItem -Recurse -File -LiteralPath $ProjectRoot -Include *.py -ErrorAction SilentlyContinue | Measure-Object).Count
        TypeScript = (Get-ChildItem -Recurse -File -LiteralPath $ProjectRoot -Include *.ts,*.tsx -ErrorAction SilentlyContinue | Measure-Object).Count
        JavaScript = (Get-ChildItem -Recurse -File -LiteralPath $ProjectRoot -Include *.js,*.jsx -ErrorAction SilentlyContinue | Measure-Object).Count
        Rust = (Get-ChildItem -Recurse -File -LiteralPath $ProjectRoot -Include *.rs -ErrorAction SilentlyContinue | Measure-Object).Count
        Go = (Get-ChildItem -Recurse -File -LiteralPath $ProjectRoot -Include *.go -ErrorAction SilentlyContinue | Measure-Object).Count
    }

    $winner = $counts.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 1
    if ($winner.Value -gt 0) { return $winner.Key }
    return "Unknown"
}

function Get-DefaultScopeInclude([string]$ProjectRoot) {
    $candidates = @("src", "app", "lib", "server", "client")
    $result = @()
    foreach ($candidate in $candidates) {
        $full = Join-Path $ProjectRoot $candidate
        if (Test-Path -LiteralPath $full) {
            $result += "$candidate/"
        }
    }
    if (Test-Path -LiteralPath (Join-Path $ProjectRoot "README.md")) {
        $result += "README.md"
    }
    if ($result.Count -eq 0) {
        $result += "."
    }
    return $result
}

function Get-CanonicalStatement([string]$ProjectRoot, [string]$ResolvedProjectName, [string]$ResolvedMode, [string]$PrimaryLanguage) {
    $readme = Join-Path $ProjectRoot "README.md"
    $headline = ""
    if (Test-Path -LiteralPath $readme) {
        $headline = Get-Content -LiteralPath $readme -TotalCount 20 | Where-Object { $_ -match '^\s*#' } | Select-Object -First 1
        if ($headline) {
            $headline = ($headline -replace '^\s*#+\s*', '').Trim()
        }
    }

    if (-not $headline) {
        $headline = $ResolvedProjectName
    }

    if ($ResolvedMode -eq "protocol_evolution") {
        return "$headline is a $PrimaryLanguage project using MICA as a protocol-evolution memory layer. The AI maintainer should preserve project identity, accumulate lessons across cycles, and keep archive and playbook aligned with actual project changes."
    }

    return "$headline is a $PrimaryLanguage project using MICA as a memory-injection layer. The AI maintainer should recover project context quickly, preserve institutional memory across sessions, and update the archive after meaningful maintenance work."
}

function Get-Context([string]$ProjectRoot, [string]$RequestedContext) {
    if ($RequestedContext -ne "auto") { return $RequestedContext }

    if ((Test-Path -LiteralPath (Join-Path $ProjectRoot "agent.yaml")) -or
        (Test-Path -LiteralPath (Join-Path $ProjectRoot "AGENTS.md"))) {
        return "agent_os"
    }

    if (Test-Path -LiteralPath (Join-Path $ProjectRoot "SKILL.md")) {
        return "skill"
    }

    return "standalone"
}

function Get-Mode([string]$ProjectRoot, [string]$RequestedMode) {
    if ($RequestedMode -ne "auto") { return $RequestedMode }

    $signals = @(
        (Join-Path $ProjectRoot "memory\lessons"),
        (Join-Path $ProjectRoot "memory\exemplars"),
        (Join-Path $ProjectRoot "memory\MEMORY_LAYER_CONVENTIONS.md")
    )

    foreach ($signal in $signals) {
        if (Test-Path -LiteralPath $signal) {
            return "protocol_evolution"
        }
    }

    return "memory_injection"
}

function New-MicaYamlContent(
    [string]$Name,
    [string]$ResolvedMode,
    [string]$Description,
    [string]$ArchivePath,
    [string]$PlaybookPath
) {
    $lines = @()
    $lines += 'mica_spec: "0.1.9"'
    $lines += "name: $Name"
    $lines += "mode: $ResolvedMode"
    $lines += "description: ""$Description"""
    $lines += ""
    $lines += "layers:"
    $lines += "  - name: archive"
    $lines += "    path: $ArchivePath"
    $lines += "    format: json"
    $lines += "    loading_hint: always"
    $lines += ""
    $lines += "  - name: playbook"
    $lines += "    path: $PlaybookPath"
    $lines += "    format: markdown"
    $lines += "    loading_hint: always"

    if ($ResolvedMode -eq "protocol_evolution") {
        $lines += ""
        $lines += "  - name: lessons"
        $lines += "    path: memory/lessons/"
        $lines += "    format: markdown"
        $lines += "    loading_hint: on_demand"
        $lines += ""
        $lines += "  - name: exemplars"
        $lines += "    path: memory/exemplars/"
        $lines += "    format: markdown"
        $lines += "    required: false"
        $lines += "    loading_hint: on_demand"
    }

    $lines += ""
    $lines += "update_triggers:"
    if ($ResolvedMode -eq "protocol_evolution") {
        $lines += "  - on_dogfood_cycle_close"
    } else {
        $lines += "  - on_maintenance_complete"
    }
    $lines += "  - on_explicit_save"
    $lines += ""
    $lines += "archive_policy:"
    $lines += "  rotation: on_version_bump"
    $lines += "  retention: indefinite"

    return ($lines -join "`r`n") + "`r`n"
}

function New-PlaybookContent(
    [string]$ResolvedProjectName,
    [string]$ResolvedMode,
    [string]$CanonicalStatement
) {
    $modeLine = if ($ResolvedMode -eq "protocol_evolution") {
        "Dogfood or experiment cycles should accumulate lessons and update the archive only after cycle closeout."
    } else {
        "Maintenance sessions should update the archive after meaningful maintenance completion."
    }

    @"
# $ResolvedProjectName MICA Playbook

## Canonical Role

$CanonicalStatement

## Operating Mode

- mode: `$ResolvedMode`
- $modeLine

## Session Rules

1. Read `mica.yaml` first.
2. Read the archive canonical statement and current design invariants.
3. Use this playbook to recover operating constraints before changing project memory.
4. Update the archive only after a meaningful maintenance or cycle boundary.

## Initial Notes

- This is an installer-generated bootstrap playbook.
- Replace placeholder guidance with project-specific operating rules during the first real session.
"@
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$micaRoot = Split-Path -Parent $scriptDir

$specRoot = Join-Path $micaRoot "0.1.9"
$legacyRoot = Join-Path $micaRoot "Legacy"
$baseArchiveTemplate = Join-Path $legacyRoot "mica-v0.1.8-minimal-instance.json"

if (-not (Test-Path -LiteralPath $TargetPath)) {
    throw "Target path does not exist: $TargetPath"
}

$projectRoot = (Resolve-Path -LiteralPath $TargetPath).Path
$resolvedContext = Get-Context -ProjectRoot $projectRoot -RequestedContext $Context
$resolvedMode = Get-Mode -ProjectRoot $projectRoot -RequestedMode $Mode
$resolvedProjectName = if ([string]::IsNullOrWhiteSpace($ProjectName)) {
    Convert-ToKebabCase -Name (Split-Path -Leaf $projectRoot)
} else {
    Convert-ToKebabCase -Name $ProjectName
}

if ([string]::IsNullOrWhiteSpace($resolvedProjectName)) {
    throw "Could not derive a valid project name."
}

$existingCandidates = @(
    (Join-Path $projectRoot "mica.yaml"),
    (Join-Path $projectRoot "memory\mica.yaml")
) | Where-Object { Test-Path -LiteralPath $_ }

if ($existingCandidates.Count -gt 0 -and -not $Force) {
    throw "Existing MICA package detected: $($existingCandidates -join ', '). Use -Force to overwrite."
}

$memoryDir = Join-Path $projectRoot "memory"
$workflowsDir = Join-Path $projectRoot "workflows"

switch ($resolvedContext) {
    "agent_os" {
        $micaYamlPath = Join-Path $memoryDir "mica.yaml"
        $playbookRelative = "workflows/$resolvedProjectName-playbook.v1.0.0.md"
    }
    "skill" {
        $micaYamlPath = Join-Path $memoryDir "mica.yaml"
        $playbookRelative = "memory/$resolvedProjectName-playbook.v1.0.0.md"
    }
    default {
        $micaYamlPath = Join-Path $projectRoot "mica.yaml"
        $playbookRelative = "memory/$resolvedProjectName-playbook.v1.0.0.md"
    }
}

$archiveRelative = "memory/$resolvedProjectName.mica.v1.0.0.json"
$archivePath = Join-Path $projectRoot ($archiveRelative -replace '/', '\')
$playbookPath = Join-Path $projectRoot ($playbookRelative -replace '/', '\')
$reportPath = Join-Path $memoryDir "mica-install-report.json"

$primaryLanguage = Get-PrimaryLanguage -ProjectRoot $projectRoot
$canonicalStatement = Get-CanonicalStatement -ProjectRoot $projectRoot -ResolvedProjectName $resolvedProjectName -ResolvedMode $resolvedMode -PrimaryLanguage $primaryLanguage
$scopeInclude = Get-DefaultScopeInclude -ProjectRoot $projectRoot

$plan = [ordered]@{
    target = $projectRoot
    context = $resolvedContext
    mode = $resolvedMode
    project_name = $resolvedProjectName
    mica_yaml = $micaYamlPath
    archive = $archivePath
    playbook = $playbookPath
    lessons = if ($resolvedMode -eq "protocol_evolution") { Join-Path $memoryDir "lessons" } else { $null }
    exemplars = if ($resolvedMode -eq "protocol_evolution") { Join-Path $memoryDir "exemplars" } else { $null }
    primary_language = $primaryLanguage
}

Write-Info "MICA install plan"
$plan.GetEnumerator() | ForEach-Object {
    if ($null -ne $_.Value -and $_.Value -ne "") {
        Write-Host ("  {0}: {1}" -f $_.Key, $_.Value)
    }
}

if ($PlanOnly) {
    Write-Success "Plan only completed. No files were written."
    return
}

Ensure-Dir $memoryDir
if ($resolvedContext -eq "agent_os") {
    Ensure-Dir $workflowsDir
}

if ($resolvedMode -eq "protocol_evolution") {
    Ensure-Dir (Join-Path $memoryDir "lessons")
    Ensure-Dir (Join-Path $memoryDir "exemplars")
}

if (-not (Test-Path -LiteralPath $baseArchiveTemplate)) {
    throw "Base archive template not found: $baseArchiveTemplate"
}

$archive = Get-Content -LiteralPath $baseArchiveTemplate -Raw | ConvertFrom-Json -Depth 100
$archive.mica_spec = "0.1.9"
$archive.mica_schema_version = "0.1.9"
$archive.project.name = $resolvedProjectName
$archive.project.version = "1.0.0"
$archive.project.canonical_statement = $canonicalStatement
$archive.project.primary_language = $primaryLanguage
$archive.project.repo_path = $projectRoot.Replace("D:\Sanctum\", "")
$archive.scope.include = $scopeInclude
$archive.scope.exclude = @("__pycache__/", "*.pyc", "node_modules/", ".git/")
$archive.design_invariants = @()
$archive.provenance_registry = @()
$archive.operation_meta.mica_schema_version = "0.1.9"
$archive.operation_meta.update_count = 0
$archive.operation_meta.last_updated = (Get-Date).ToString("yyyy-MM-dd")
$archive.operation_meta.session_count = 0
$archive.operation_meta.bootstrap_note = "MICA v0.1.9 initial bootstrap. design_invariants and provenance_registry intentionally empty — populate during the first real maintenance session."
$archive.invocation_protocol.primary_pattern = "readme_protocol"
$archive.invocation_protocol.self_test_runtime = "readme_protocol_ai_session"
$archive.invocation_protocol.loading_order = @(
    "1. Load mica.yaml — verify package structure and mode",
    "2. Load this archive — read canonical_statement and design_invariants",
    "3. Load playbook — review operating constraints and session protocol",
    "4. Run PCT self-tests to confirm MICA integrity before starting any work"
)

$yaml = New-MicaYamlContent -Name $resolvedProjectName -ResolvedMode $resolvedMode -Description $canonicalStatement.Substring(0, [Math]::Min(100, $canonicalStatement.Length)) -ArchivePath $archiveRelative -PlaybookPath $playbookRelative
$playbook = New-PlaybookContent -ResolvedProjectName $resolvedProjectName -ResolvedMode $resolvedMode -CanonicalStatement $canonicalStatement

Ensure-Dir (Split-Path -Parent $playbookPath)
Set-Content -LiteralPath $micaYamlPath -Value $yaml -Encoding UTF8
$archive | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $archivePath -Encoding UTF8
Set-Content -LiteralPath $playbookPath -Value $playbook -Encoding UTF8

$report = [ordered]@{
    mica_installer_version = "v0.1.9-bootstrap"
    installed_at = (Get-Date).ToString("o")
    target = $projectRoot
    context = $resolvedContext
    mode = $resolvedMode
    project_name = $resolvedProjectName
    files_created = @(
        $micaYamlPath,
        $archivePath,
        $playbookPath
    )
    lessons_created = ($resolvedMode -eq "protocol_evolution")
    exemplars_created = ($resolvedMode -eq "protocol_evolution")
    validation_summary = @{
        mica_yaml_present = (Test-Path -LiteralPath $micaYamlPath)
        archive_present = (Test-Path -LiteralPath $archivePath)
        playbook_present = (Test-Path -LiteralPath $playbookPath)
        mode_coherent = if ($resolvedMode -eq "protocol_evolution") {
            (Test-Path -LiteralPath (Join-Path $memoryDir "lessons"))
        } else {
            $true
        }
    }
}

$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Success "MICA package installed"
Write-Success "mica.yaml: $micaYamlPath"
Write-Success "archive:   $archivePath"
Write-Success "playbook:  $playbookPath"
Write-Success "report:    $reportPath"
