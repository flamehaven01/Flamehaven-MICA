# Flamehaven Document SDK

A query-first library of reusable HTML design functions / modals for CAS reports
and Flamehaven document artifacts.

The goal is "show the real thing, don't persuade": turn evidence into legible
structure using a fixed visual vocabulary instead of hand-crafting a new layout
every time.

## DI-SDK-001 -- Query First

> When a document needs a visual function (chart, modal, badge, timeline,
> comparison table, collapsible, diff view, etc.), query `manifest.yaml` FIRST.
> Only search externally if no entry fits. External code enters only through the
> license gate below.

This keeps output consistent, on-brand, and cheap. Internet searches give
different results every time -- the manifest gives a deterministic answer.

## Structure

| Path | Role |
|------|------|
| `manifest.yaml` | The query index. Internal components + vendored reference demos, each mapped to its UI function and CAS use. |
| `README.md` | This file. Usage + rules. |
| `NOTICE.md` | Vendor attribution (Apache-2.0). |
| `vendor/html-effectiveness/` | Verbatim Apache-2.0 reference library (20 demos). Read as PATTERN source. |

## How To Use

1. Need a visual function -> open `manifest.yaml`, find the entry whose
   `function` matches.
2. If it is an `internal:` component, reuse the proven CAS vocabulary.
3. If it is a `vendor_html_effectiveness:` demo, open the file in `vendor/`,
   read the technique, and RE-WRITE it as a CAS component. Do not copy verbatim
   into a deliverable.

## License Posture (proportional, not excessive)

These are common HTML design techniques -- not protected expression. Copyright
covers specific code, not layout ideas or techniques.

- **Vendored verbatim copy** (`vendor/`): keeps its upstream `LICENSE`. One file,
  near-zero cost, and it is what makes the verbatim copy legitimate.
- **Our components** (re-implemented from a pattern): our own expression -> no
  attribution owed. No license headers in components, README, or reports.
- **Client deliverables**: built from our components -> zero license burden.

The entire compliance surface is: `vendor/html-effectiveness/LICENSE` +
`NOTICE.md`. Nothing else carries a license notice.

## Adding External Sources Later

Only add code from sources with an explicit permissive license (MIT / Apache-2.0
/ CC0). Vendor it under `vendor/<source>/` with its LICENSE intact, add a
`NOTICE.md` line, and register it in `manifest.yaml`. Unlicensed gallery code
(CodePen / Awwwards without a license) is pattern-reference only -- never copied.
