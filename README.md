<p align="center">
  <img src="https://raw.githubusercontent.com/flamehaven01/Flamehaven-MICA/main/docs/assets/mica-logo.png" alt="MICA -- Memory Invocation &amp; Context Archive" width="520"/>
</p>

<p align="center">
  <a href="https://github.com/flamehaven01/Flamehaven-MICA/actions/workflows/ci.yml"><img src="https://github.com/flamehaven01/Flamehaven-MICA/actions/workflows/ci.yml/badge.svg" alt="CI"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License"/></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"/></a>
  <img src="https://img.shields.io/badge/release-v3.2.0-green.svg" alt="v3.2.0"/>
</p>

<p align="center"><b>README invokes. MICA loads memory and playbook.</b></p>

MICA is **Memory Invocation & Context Archive**. It gives a repository a small,
portable way to tell an AI session what the project already knows and how work
must be done.

```text
README.md              session entrypoint
  -> mica.yaml         manifest and selection
       -> archive      retained decisions and invariants
       -> playbook     operating instructions
            -> session context
```

That is the product. Validation, traces, digests, handoff, flow checks, and
measurement are optional support. They must not replace or obscure this path.

## The Core Contract

**README invokes.** A repository using `readme_protocol` carries one directive
near the top of its README:

```markdown
<!-- MICA:INVOKE manifest="mica.yaml" -->
```

The surrounding explanation belongs to the repository. MICA verifies only that
the directive exists once and resolves to the same manifest the tools use.

**`mica.yaml` selects.** It is the single authority for archive and playbook
paths. Those paths are not repeated in the README.

**The archive remembers.** It contains decisions, invariants, and the evidence
or incident that made them durable. It is not a session log or a dump of every
past interaction.

**The playbook instructs.** It tells a human or AI how this repository is
actually operated: what to read, what to preserve, how to verify work, and what
to do when memory conflicts with current reality.

**The runtime emits context.** It reads exactly the selected agent-context
surfaces, verifies their bytes, and writes their contents to stdout. An
incomplete contract emits no context.

## First Run

```bash
git clone https://github.com/flamehaven01/Flamehaven-MICA.git
cd Flamehaven-MICA
pip install -r requirements-dev.txt
```

Load the complete starter package:

```text
python tools/mica_runtime.py templates/minimal-package --format context
[MICA CONTEXT] example-project
Profile: default
--- MICA SURFACE BEGIN role=archive path=memory/mica_archive.json
...
--- MICA SURFACE BEGIN role=playbook path=memory/mica_playbook.md
...
```

The output between each `BEGIN` and `END` marker is the actual selected memory,
not a summary of filenames. Pipe or attach that output to the session mechanism
used by your agent host.

Check the entrypoint and package composition separately:

```text
python tools/mica_pct.py templates/minimal-package
PCT-007 [PASS] primary_pattern valid: readme_protocol; entrypoint=README.md -> mica.yaml; invoked=archive, playbook; context=archive, playbook; operator=none
Contract : CLOSED
Overall: CLOSED CONTRACT
```

`CLOSED` means the declared entrypoint and selected files resolved. It does not
prove that an external agent host attached stdout to a model. A digest-bound
invocation trace can record the selected bytes, but it remains evidence about
the invocation mechanism, not proof of model cognition.

## Use MICA as an AI

Use [the `mica-context` skill](skills/mica-context/SKILL.md) when your agent host
supports repository skills. It fixes the behavior that must be consistent:

1. enter through the repository README
2. resolve the manifest it names
3. emit the selected archive and playbook
4. apply relevant memory and procedure to the current task
5. report what was actually resolved, emitted, and verified

The skill does not impose one archive schema or playbook layout. Existing MICA
packages evolved with their repositories; their manifest remains the authority
for paths, profiles, and composition.

Use [the `mica-author` skill](skills/mica-author/SKILL.md) only when explicitly
creating or changing a package. It invokes an existing package before editing,
preserves repository-owned structure, and verifies that the resulting archive
and playbook still emit as session context. It does not generate project memory
from source-code summaries.

For hosts that discover only repository-level instruction files, copy the
one-line [Claude or Codex adapter](templates/adapters/). The adapter points to
the skill/runtime; it does not copy MICA policy into `CLAUDE.md` or `AGENTS.md`.

## Adopt MICA

For a repository that does not yet use MICA, start with
[templates/minimal-package/](templates/minimal-package/) as a scaffold:

```text
README.md
mica.yaml
memory/
  mica_archive.json
  mica_playbook.md
```

Replace every example decision and instruction with evidence from the target
repository. Do not rename an existing archive or playbook merely to match this
example; declare its real path in the manifest. The detailed README block is in
[templates/MICA_README_INVOCATION.md](templates/MICA_README_INVOCATION.md).
Lifecycle and evidence guidance is in the
[consumer authoring guide](docs/MICA_CONSUMER_AUTHORING_GUIDE.md).

A minimal manifest is deliberately small:

```yaml
mica_spec: "0.2.9"
name: example-project
mode: memory_injection

layers:
  - name: archive
    path: memory/mica_archive.json
    format: json
    loading_hint: always
  - name: playbook
    path: memory/mica_playbook.md
    format: markdown
    loading_hint: always

invocation_protocol:
  primary_pattern: readme_protocol
  agent_context_surfaces: [archive, playbook]
  profiles:
    default:
      surfaces: [archive, playbook]
```

Use a released MICA checkout or a deliberately vendored runtime:

```text
python <MICA_ROOT>/tools/mica_runtime.py <TARGET_REPO> --format context
```

Do not proceed if it refuses to emit. A repository may expose a shorter local
command, but that command must preserve the same selected context.

## Consumer CI

Consumers may call the reusable workflow without copying MICA's CI policy:

```yaml
jobs:
  mica:
    uses: flamehaven01/Flamehaven-MICA/.github/workflows/mica-consumer.yml@v3.2.0
    with:
      project-root: .
      profile: default
```

The workflow validates the package and proves that the selected context can be
emitted. It reports only the byte count and does not upload archive or playbook
content. CI is a deterministic support check; the AI still has to consume and
apply the emitted context during the real session.

## Profiles

Profiles are optional selectors, not a second memory system. They let a task
receive only the relevant parts of a playbook while the archive remains present.

```yaml
invocation_protocol:
  primary_pattern: readme_protocol
  profiles:
    default:
      surfaces: [archive, playbook]
    incident:
      surfaces: [archive, playbook]
      sections:
        playbook: [Incident Runbook]
```

```text
python tools/mica_runtime.py fixtures/memory_profiles --profile incident --format context
[MICA CONTEXT] memory-profiles
Profile: incident
--- MICA SURFACE BEGIN role=archive path=memory/mica_archive.json
...
--- MICA SURFACE BEGIN role=playbook path=memory/mica_playbook.md
## Incident Runbook
...
```

The context emitter excludes unselected sections and every operator-only
surface. The digest describes the emitted slice, not the whole source file.

## Support Tools

These tools support the core contract; none is required to write useful memory
or a useful playbook.

| Tool | Purpose |
|---|---|
| `mica_runtime.py` | Resolve and emit selected session context |
| `mica_pct.py` | Validate the README entrypoint and package composition |
| `mica_invocation.py` | Inspect invocation trace evidence |
| `mica_handoff.py` | Validate optional cross-session handoff state |
| `mica_measure.py` | Report context size; it does not measure work quality |

Flow, candidate promotion, recall telemetry, and handoff remain available for
consumers that explicitly need them. They are extensions below the core and are
disabled by default.

## Truth Boundaries

- `resolved` means MICA found and read the selected bytes.
- `emitted` means `--format context` wrote those bytes to stdout.
- `recorded` means an invocation trace describes selected bytes.
- None of these alone proves an external model received, understood, or obeyed
  the context.
- Archive memory can become stale. When memory and current repository reality
  disagree, report the conflict; do not silently prefer either.

## Development

```bash
pytest -v
ruff check tools/ tests/
ruff format --check tools/ tests/
```

The fixture map and expected behavior live in
[fixtures/README.md](fixtures/README.md). Intentional validator-output changes
must regenerate `tests/golden/pct_output.json` with
`python tests/test_golden_pct.py --update`.

## Documents

- [Consumer authoring guide](docs/MICA_CONSUMER_AUTHORING_GUIDE.md)
- [Cross-repository adoption guide](docs/MICA_CROSS_REPO_ADOPTION_GUIDE.md)
- [Thin Claude/Codex adapters](templates/adapters/)
- [v3.2.0 release notes](docs/MICA_v3.2.0_RELEASE_NOTES.md)
- [v3.0.0 declaration](docs/MICA_v3.0.0_DECLARATION.md)
- [v3.1.0 release notes](docs/MICA_v3.1.0_RELEASE_NOTES.md)
- [v3.0.1 release notes](docs/MICA_v3.0.1_RELEASE_NOTES.md)
- [Changelog](CHANGELOG.md)

## License

MIT. See [LICENSE](LICENSE).
