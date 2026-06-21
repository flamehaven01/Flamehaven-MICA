# SDK Component Selection Protocol (agent-grade)

How an AI agent decides which SDK modal to place in each document section.
This is the "MICA agent-grade" judgment layer: selection is reasoned from the
manifest, not hardcoded.

Governing rules: **DI-SDK-001** (query manifest first) and **DI-SDK-002**
(selection is agent-judged).

---

## Input

A document section with:
- its **content type** (see classification below)
- its **evidence level** (A / B / C / D, from the CAS audit)
- the **case type** (#1 Code / #2 Semantic / #3 Integrated)
- the **canvas slot** (which page, single-file vs multi-page)

## Procedure

1. **Classify the section's content type:**

   | Content type | Signal |
   |---|---|
   | verdict | a PASS/WARN/FAIL/NOTE judgment on a claim/module |
   | metric | a top-line number (score, percent, count) |
   | evidence-excerpt | code or data shown as proof |
   | comparison | two or more options/states weighed |
   | timeline | ordered events (incident, reproduction, audit chain) |
   | architecture | components, data flow, failure paths |
   | provenance | where evidence came from, or a scope caveat |
   | inspectability | what the reader can independently check |
   | navigation | routing across a multi-page report |

2. **Query `manifest.yaml`** for entries whose `when` trigger matches the
   content type. Collect candidates.

3. **Prefer internal vocabulary** over vendored patterns when both fit. Internal
   components are proven, on-brand, and license-clean. Vendored entries are
   pattern sources to re-implement.

4. **Apply the interaction policy:**
   - functional interaction (hover, collapsible, copy, tabs, click-expand,
     keyboard-nav, jump-links) is allowed where it aids the reader
   - any entry marked `interaction: decorative` or carrying an `avoid:` field is
     rejected for deliverables

5. **Apply the honesty rule (binding):** the visual must encode epistemics.
   - higher evidence level (A/B) -> full-strength rendering
   - lower evidence level (C/D) -> visibly weaker (muted chip, "unverified"
     treatment). Never render a Level-D claim as polished as a Level-A claim.
   - emptiness is surfaced, never hidden.

6. **Bind** the section to the chosen component. Record the binding in the
   generation manifest so the choice is auditable.

---

## Default bindings (starting point, not a cage)

| Content type | First-choice component |
|---|---|
| verdict | `badge-verdict` (+ `chip` for level/type) |
| metric | `metric` |
| evidence-excerpt | `code-frame` |
| comparison | `evidence-table` or pattern from `research-concept-explainer` |
| timeline | pattern from `incident-report` |
| architecture | pattern from `code-understanding` / `flowchart-diagram` |
| provenance | `callout` |
| inspectability | `evidence-table` |
| navigation | `preview-dock` |

The agent may override a default when the section's specifics justify it. The
override reason should be recordable.

---

## Why agent-judged, not hardcoded

A fixed table cannot weigh evidence level, case type, canvas slot, and reader
audience at once. The agent reads the manifest's `when` triggers and the rules
above and decides per section -- the same way a human designer would, but
auditable through the recorded bindings.
