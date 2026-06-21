# SDK Vendor Attribution

This SDK vendors third-party components under their original licenses.
Each vendored source retains its upstream LICENSE file. Do not strip them.

---

## vendor/html-effectiveness

- **Upstream**: https://github.com/ThariqS/html-effectiveness
- **Author**: Thariq Shihipar (ThariqS)
- **License**: Apache License 2.0 (see `vendor/html-effectiveness/LICENSE`)
- **Companion page**: https://thariqs.github.io/html-effectiveness/
- **Vendored**: 2026-06-21
- **Contents**: 20 self-contained HTML demos + index, illustrating the
  "Unreasonable Effectiveness of HTML" thesis (agents emit interactive HTML,
  not markdown).
- **Modifications**: None. Files are vendored verbatim as a reference library.
  When a demo is adapted into a CAS component, record the derivation in
  `manifest.yaml` under the component's `derived_from` field and note changes
  here per Apache-2.0 Section 4(b).

Apache-2.0 requires: retain the LICENSE, retain attribution, and state changes
on modification. All three are satisfied by keeping `vendor/html-effectiveness/LICENSE`
intact and recording any derivations in this file.
