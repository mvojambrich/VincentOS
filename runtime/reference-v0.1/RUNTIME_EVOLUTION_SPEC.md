# VincentOS 4.0.1-aligned Reference Runtime v0.1

## Scope and honesty boundary

This is an executable **reference runtime**, not an implementation of the complete VincentOS 4.0.1 architecture. It exercises selected architecture boundaries: RIL, authority validation, ALE-style holds, UTSS-style telemetry, FRMS-style containment, and CEGS memory protection.

## Reference flow

`RIL → IC → CL → PE → OM → FL`

Each stage carries a cognitive packet with a packet ID, correlation ID, stage, timestamp, and payload. Packets are stored as snapshots for traceability.

## GSM and RIL

RIL is a mandatory, non-bypassable pre-IC gate. It classifies incoming information as `Verified`, `Probable`, or `Untrusted` before IC can execute.

- `Verified` requires two or more declared sources and trusted declared provenance. It is only a **candidate for later memory review**, not canonical history.
- `Probable` is admissible for routine cognition but is never canonical memory.
- `Untrusted` enters clarification or containment before IC. It cannot enter CL, PE, OM, or feedback.
- Realism or a signal does not establish authority. Authority is evaluated independently.

## Authority hierarchy

Safety-critical actions (for example, deployment, production, transfer, purchase, publication, or email sending) require a valid authority result from `AuthorityValidator` and a non-Untrusted RIL classification.

The validator recognizes only active, safety-critical identifiers in the runtime operator's `config/authority_registry.json` file (or the path named by `VINCENTOS_AUTHORITY_REGISTRY`). If that registry is absent, invalid, or does not recognize the supplied `authority_id`, safety-critical work fails closed. Request metadata never grants authority.

Human intervention does not directly override an RIL containment result. It may provide new corroborated evidence or a valid authority record, which must begin as a **new context** and pass RIL again.

## ALE reference boundary

When `metadata.provenance_conflict` is declared, the runtime records an ALE decision of `HOLD`. It does not render output. Resolution requires external corroboration and a new context; the runtime does not self-arbitrate conflicting evidence.

## UTSS-style telemetry

Every RIL, authority, arbitration, stage, containment, and memory-hold decision becomes a structured audit event with:

- event ID and monotonic sequence number
- context/correlation ID
- actor, reason, timestamp, and decision data
- a previous-hash and event hash
- redaction of common secret field names

The local SQLite event chain is **tamper-evident for accidental changes only**. It is not tamper-proof, lossless distributed telemetry, or a production UTSS implementation.

## FRMS-style containment and recovery

The runtime has explicit `ACTIVE`, `HOLD`, and `CONTAINMENT` states. `GET /recovery/{context_id}` reports a safe next step. It does not resume or override a failed context; it directs the operator to create a new context with corrected external evidence.

## CEGS memory protection

Canonical-memory promotion is disabled. `POST /memory/{context_id}/promote` records a `HOLD` decision rather than writing memory. Full memory promotion remains out of scope until reversibility, snapshots/deltas, review, and human governance are implemented.

## Deliberate non-goals

- No model provider, autonomous execution, or external system action.
- No full CPS multi-node routing, CEGS growth system, UTSS infrastructure, or FRMS rollback engine.
- No authentication, multi-tenant security, encryption, or external provenance registry.
- No claim that metadata declarations are independently verified facts.

