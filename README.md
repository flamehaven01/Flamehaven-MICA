# MICA — Memory Invocation & Context Archive for AI

**Current stable version**: v0.1.9 — Living Standard
**Next development track**: v0.2.0 — Draft branch for ASDP-derived profiles
**Type**: AI Memory Layer / Composition Contract Standard
**Scope**: Not a program. A memory layer pattern — companion files inserted into AI projects.

---

## What is MICA?

MICA gives an AI project **persistent memory** across sessions.

It is not a framework. It is not an agent OS. It is a **memory layer contract** — a declaration of what the AI should remember, how that memory is structured, and when it gets updated.

**Three files make a MICA package:**

| File | Role |
|------|------|
| `mica.yaml` | Composition contract — declares what MICA contains and how it operates |
| `*.mica.*.json` | Archive — machine-readable memory store (persists across sessions) |
| `*-playbook.*.md` | Playbook — human + AI readable context and operating procedures |

**Two modes:**

| Mode | Pattern |
|------|---------|
| `memory_injection` | Maintenance done → learnings injected into archive → next AI session reads it |
| `protocol_evolution` | Experiment cycle closes → lessons accumulate → archive evolves → next cycle improves |

**Three placement contexts** (where `mica.yaml` lives):

| Project type | mica.yaml location |
|---|---|
| Standalone project (no agent.yaml, no SKILL.md) | `[project-root]/mica.yaml` |
| Agent OS project (has agent.yaml / AGENTS.md) | `memory/mica.yaml` |
| Skill project (SKILL.md entry point) | `memory/mica.yaml` |

---

## Quick Start: Add MICA to a Project

Use the `mica-installer` skill — it handles all three contexts and both modes:

```
D:\Sanctum\Claude-Skills\mica-installer\SKILL.md
```

---

## Quick Start: Load MICA in an Existing Project

Use the `mica-context-loader` skill — it auto-detects MICA files and activates them:

```
D:\Sanctum\Claude-Skills\mica-context-loader\SKILL.md
```

---

## Folder Structure

```
Flamehaven MICA 0.1.3 - Memory Invocation & Context Archive for AI/
│
├── README.md                         <- you are here (AI + human entry point)
├── MICA_Week1_Technical_Rationale.md <- cross-version design rationale doc
│
├── 0.2.0/                            <- NEXT DEVELOPMENT TRACK (draft, not yet normative)
│   ├── README.md                                   (agentic modal draft branch)
│   ├── mica.yaml.schema.json                       (copied baseline for forward edits)
│   ├── MICA_v0.2.0_COMPOSITION_CONTRACT.md         (next composition contract draft)
│   ├── MICA_v0.2.0_EXAMPLES.md                     (next examples draft)
│   ├── MICA_v0.2.0_MIGRATION_GUIDE.md              (forward migration draft)
│   ├── mica-v0.2.0-archive-changes.schema.json     (next archive patch draft)
│   ├── mica-v0.2.0-self-test-expansion.schema.json (next PCT patch draft)
│   ├── MICA_v0.2.0_SELF_TEST_EXAMPLES.md           (next PCT examples draft)
│   └── MICA_v0.2.0_PROFILE_CANDIDATES.md           (ASDP-derived extension candidates)
│
├── 0.1.9/                            <- CURRENT STABLE VERSION (living standard)
│   ├── mica.yaml.schema.json                       (mica.yaml JSON Schema, normative)
│   ├── MICA_v0.1.9_COMPOSITION_CONTRACT.md         (placement rules + field reference)
│   ├── MICA_v0.1.9_EXAMPLES.md                     (reference examples, both modes)
│   ├── MICA_v0.1.9_MIGRATION_GUIDE.md              (0.1.8.1 -> 0.1.9 migration + compat)
│   ├── mica-v0.1.9-archive-changes.schema.json     (archive schema diff, patch-as-spec)
│   ├── mica-v0.1.9-self-test-expansion.schema.json (PCT-* check definitions)
│   └── MICA_v0.1.9_SELF_TEST_EXAMPLES.md           (PCT-* check examples, both projects)
│
├── 0.1.8.1/                          <- PRESERVED (reference + rollback point)
│   ├── mica-v0.1.8.1-universal.schema.json (base archive JSON schema, normative)
│   ├── MICA_v0.1.8.1_UNIVERSAL_USAGE.md
│   ├── PLAYBOOK.md
│   └── README.md
│
├── Legacy/                           <- PRESERVED (v0.1.3 through v0.1.8 history)
│   ├── mica-v0.1.8-minimal-instance.json  (archive bootstrap reference structure)
│   ├── mica-v0.1.8-fill-template.json     (authoring aid, not schema-valid)
│   └── [all prior schema versions v0.1.3-v0.1.8]
│
└── MICA-LAB-ANCHOR/                  <- PRESERVED (lab experiment artifacts)
    └── [lab benchmark and traceability files]
```

---

## Version History

| Version | Status | Key addition |
|---------|--------|--------------|
| **v0.2.0** | Draft | Forward development branch for optional ASDP-derived profiles |
| **v0.1.9** | ✅ Current stable | `mica.yaml` composition contract, 3 placement contexts, PCT-* self-tests |
| v0.1.8.1 | Preserved | Archive schema patch: self-test expressions, runtime declaration, track authority |
| v0.1.8 | Preserved | Universal model with self-test architecture |
| v0.1.7 | Legacy | Universal usage discipline |
| v0.1.3–v0.1.6 | Legacy | Schema evolution history |

---

## Branching Rule

- `0.1.9/` is frozen as the current stable living standard.
- `0.2.0/` is the forward development branch.
- New version work happens in a new folder, never by overwriting the stable branch.
- Root `README.md` is the only moving pointer between stable and draft tracks.

---

## v0.1.9 Key Design Decisions

1. **`mica.yaml` composition contract**: A single file declares "this project's MICA consists of these files". Fills the v0.1.8.x gap where nothing declared what a MICA package *was*.
2. **patch-as-spec**: v0.1.9 changes to archive JSON are expressed as diff documents (`mica-v0.1.9-archive-changes.schema.json`), not copies. Prevents silent two-file divergence.
3. **`additionalProperties: false` everywhere**: Prevents gitagent's mistake where example fields existed outside the schema.
4. **STC-* vs PCT-* separation**: STC = internal JSON consistency (v0.1.8.1), PCT = package completeness (v0.1.9 new). Orthogonal layers.
5. **3 placement contexts**: MICA adapts to standalone, Agent OS, and Skill project structures without schema changes.

---

## Live Deployments (v0.1.9)

| Project | Mode | mica.yaml |
|---------|------|-----------|
| `flamehaven-space` | `memory_injection` | `D:\Sanctum\WEB 5.0+AI\web 5.0\flamehaven-space\mica.yaml` |
| `CareChainGovernanceEngine` | `protocol_evolution` | `D:\Sanctum\CareChainGovernanceEngine\mica.yaml` |

---

## AI Entry Points

### 최우선 진입점 (여기서 시작)

> AI가 MICA를 처음 다룰 때는 이 파일 하나만 읽으면 된다:
> **`0.1.9\README.md`** — MICA Agentic Modal
>
> 이 문서 하나로 삽입(insertion), 인보케이션(invocation), 레이어 처리,
> AI 행동 통합, 갱신, 거버넌스, PCT 자가 진단까지 전부 커버된다.

### 세부 참조 문서

| 목적 | 파일 |
|------|------|
| **MICA 전체 운영 모달 (AI 필독)** | `0.1.9\README.md` |
| mica.yaml 전체 필드 + placement 규칙 | `0.1.9\MICA_v0.1.9_COMPOSITION_CONTRACT.md` |
| mica.yaml 예제 (두 모드 모두) | `0.1.9\MICA_v0.1.9_EXAMPLES.md` |
| v0.1.8.1 → v0.1.9 마이그레이션 | `0.1.9\MICA_v0.1.9_MIGRATION_GUIDE.md` |
| PCT-* 체크 정의 | `0.1.9\mica-v0.1.9-self-test-expansion.schema.json` |
| mica.yaml JSON Schema | `0.1.9\mica.yaml.schema.json` |
| archive JSON 기반 스키마 | `0.1.8.1\mica-v0.1.8.1-universal.schema.json` |

### 다음 버전 설계 작업

| 목적 | 파일 |
|------|------|
| `0.2.0` draft branch entry point | `0.2.0\README.md` |
| ASDP-derived extension candidates | `0.2.0\MICA_v0.2.0_PROFILE_CANDIDATES.md` |
