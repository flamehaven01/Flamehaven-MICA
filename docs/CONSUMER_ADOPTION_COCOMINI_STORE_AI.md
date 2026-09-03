# Consumer Adoption: Cocomini UltimatePOS and Store AI Assist

Recorded: 2026-07-19  
Consumer root: D:/Sanctum/UltimatePOS-CodeBase-V7.1  
Purpose: cross-repository example of an invocation-first MICA package connected to a business AI RAG harness

## Adoption shape

The Cocomini consumer declares three session-start surfaces in its project-root mica.yaml:

- memory/mica_archive.json: durable business and safety invariants;
- memory/mica_playbook.md: maintenance and deployment procedure;
- docs/COCOMINI_STORE_AI_HANDOFF.md: current implementation/deployment truth, known verification, and next work.

The handoff surface is deliberately separate from the durable archive. Live counts and deployment state can change frequently; invariants such as POS system-of-record, Thai proactive language, read-only AI boundaries, evidence provenance, and package separation belong in the archive.

## Runtime AI connection

Cocomini's StoreAiAssist module has its own business-scoped SQL memory and RAG layer. This is not a replacement for MICA:

| Layer | Purpose |
|---|---|
| MICA consumer package | Helps future maintainers and AI coding agents load repository context truthfully at session start |
| Store AI memory | Preserves store conversations, analyses, operator preferences, and outcomes |
| Store AI knowledge | Supplies versioned operating policy to the retail assistant |
| UltimatePOS gateway | Supplies current scoped transaction facts and remains the system of record |

The module bundles a manifest-driven operating-knowledge pack. Its protected update action synchronizes documents using stable source identifiers, and both interactive chat and scheduled analysis retrieve bounded chunks. Durable knowledge excludes credentials and live stock/sales counts.

## Truthfulness rules demonstrated

- “Declared” and “loaded” remain separate. MICA runtime output must not claim an agent read a surface without invocation evidence.
- “Implemented,” “deployed,” “configured,” “verified,” and “planned” are separate status values in the consumer handoff.
- RAG policy is not live POS truth.
- External trend evidence must carry source, market, observation time, metric meaning, and expiry.
- A scheduled task is not considered verified until an unattended run produces auditable output.

## Validation

From the canonical MICA repository:

    python tools/mica_pct.py D:/Sanctum/UltimatePOS-CodeBase-V7.1

Optional invocation trace:

    python tools/mica_runtime.py D:/Sanctum/UltimatePOS-CodeBase-V7.1 --write-invocation-trace

Consumer-specific code, business data, provider credentials, and licensed UltimatePOS source do not belong in this canonical MICA repository. This note records the adoption pattern only.
