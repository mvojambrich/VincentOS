# VincentOS 4.0.1-aligned Reference Runtime v0.1

This is a small executable reference runtime for selected VincentOS 4.0.1 architecture boundaries. It is **not** the complete VincentOS architecture and is not production software.

Implemented reference boundaries: RIL pre-IC gating, fail-closed authority validation, ALE-style holds, structured telemetry, containment recovery status, and canonical-memory protection.

`RIL → IC → CL → PE → OM → FL`

## Run locally

```text
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## Authority registry for safety-critical demonstrations

Safety-critical actions fail closed unless `config/authority_registry.json` contains an active, safety-critical authority. This project includes `operator-demo` for local demonstration. Submit `"authority_id": "operator-demo"` to `POST /pe/process` when testing a safety-critical request.

Set `VINCENTOS_AUTHORITY_REGISTRY` to use another registry file. This local JSON registry is a reference boundary, not a production identity or authorization system.

## Key endpoints

- `POST /ic/ingest` — RIL classification and IC admission or containment.
- `POST /cl/lens` — cognitive lens for admitted contexts.
- `POST /pe/process` — authority validation, RIL processing decision, and ALE decision.
- `POST /om/render` — only for permitted work.
- `GET /audit/logs` — ordered, hash-linked telemetry events.
- `GET /recovery/{context_id}` — containment/hold recovery guidance.
- `POST /memory/{context_id}/promote` — demonstrates that canonical memory writes are held.

Read [RUNTIME_EVOLUTION_SPEC.md](RUNTIME_EVOLUTION_SPEC.md) for the exact scope, safeguards, and limits.

