"""4.0.1-aligned reference runtime: RIL → IC → CL → PE → OM → FL."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from .arbitration import ArbitrationEngine
from .authority import AuthorityValidator
from .governance import RILEngine
from .models import CognitiveLensRequest, FeedbackRequest, InputContextRequest, OutputModeRequest, ProcessingRequest
from .packets import CognitivePacket
from .recovery import recovery_view
from .storage import RuntimeStore


class PipelineError(Exception):
    def __init__(self, message: str, status_code: int = 409) -> None:
        self.message, self.status_code = message, status_code
        super().__init__(message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class VincentRuntime:
    def __init__(self, store: RuntimeStore | None = None, ril: RILEngine | None = None, authority: AuthorityValidator | None = None, arbitration: ArbitrationEngine | None = None) -> None:
        self.store = store or RuntimeStore()
        self.ril = ril or RILEngine()
        self.authority = authority or AuthorityValidator()
        self.arbitration = arbitration or ArbitrationEngine()

    def _context(self, context_id: str) -> Dict[str, Any]:
        context = self.store.get_context(context_id)
        if context is None:
            raise PipelineError("Context not found", 404)
        return context

    @staticmethod
    def _stage(context: Dict[str, Any]) -> str:
        return context["snapshots"][-1]["stage"] if context["snapshots"] else "RIL"

    def _require_stage(self, context: Dict[str, Any], expected: str) -> None:
        actual = self._stage(context)
        if actual != expected:
            raise PipelineError(f"Pipeline order violation: this stage requires {expected}; current stage is {actual}.")

    @staticmethod
    def _ril_snapshot(context: Dict[str, Any]) -> Dict[str, Any]:
        return context["snapshots"][0]["data"]

    @staticmethod
    def _packet(context_id: str, stage: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return CognitivePacket(packet_id=f"pkt-{uuid4()}", correlation_id=context_id, packet_type=f"{stage}_PACKET", stage=stage, created_at=now(), payload=payload).as_dict()

    def _record(self, context_id: str, stage: str, data: Dict[str, Any], event: str | None = None, actor: str = "runtime", reason: str = "") -> None:
        timestamp = now()
        snapshot = {**data, "packet": self._packet(context_id, stage, data)}
        self.store.add_snapshot(context_id, stage, snapshot, timestamp)
        self.store.add_audit_event(context_id, event or f"{stage}_EXECUTION", snapshot, timestamp, actor, reason)

    def _contain(self, context_id: str, event: str, detail: Dict[str, Any], reason: str) -> None:
        self.store.set_runtime_state(context_id, "CONTAINMENT")
        self.store.add_audit_event(context_id, event, detail, now(), "ril", reason)

    def ingest(self, request: InputContextRequest) -> Dict[str, Any]:
        """Run RIL before admitting information to IC or containment storage."""
        context_id, created_at = f"ctx-{uuid4()}", now()
        ril = self.ril.assess_input(request.input_payload, request.metadata).as_dict()
        self.store.create_context({"context_id": context_id, "node_id": request.node_id, "input_payload": request.input_payload, "metadata": request.metadata, "created_at": created_at})
        self._record(context_id, "RIL", {**ril, "timestamp": now()}, "RIL_GATE_DECISION", "ril", ril["reason"])
        if ril["classification"] == "Untrusted":
            self._contain(context_id, "RIL_CONTAINMENT", ril, ril["reason"])
            return {"status": "contained", "context_id": context_id, "ril": ril, "recovery": recovery_view(self._context(context_id))}
        memory_status = "CANDIDATE_REVIEW_REQUIRED" if ril["classification"] == "Verified" else "NOT_CANONICAL"
        self._record(context_id, "IC", {"classification": ril["classification"], "memory_admissibility": memory_status, "timestamp": now()}, reason="Input is admissible to IC; no canonical memory write occurs.")
        return {"status": "ingested", "context_id": context_id, "ril": ril, "memory_admissibility": memory_status}

    def apply_lens(self, request: CognitiveLensRequest) -> Dict[str, Any]:
        context = self._context(request.context_id)
        self._require_stage(context, "IC")
        result = {"lens_profile": request.lens_profile, "intent": "analysis", "tags": ["vincentos", "reference-runtime-v0.1"], "timestamp": now()}
        self._record(request.context_id, "CL", result)
        return result

    def process(self, request: ProcessingRequest) -> Dict[str, Any]:
        context = self._context(request.context_id)
        self._require_stage(context, "CL")
        authority = self.authority.validate(request.authority_id).as_dict()
        ril = self.ril.assess_processing(self._ril_snapshot(context), request.instruction, bool(authority["valid"])).as_dict()
        arbitration = self.arbitration.resolve(bool(context["metadata"].get("provenance_conflict", False))).as_dict()
        self.store.add_audit_event(request.context_id, "AUTHORITY_VALIDATION", authority, now(), "authority-validator", authority["reason"])
        self.store.add_audit_event(request.context_id, "RIL_PROCESSING_DECISION", ril, now(), "ril", ril["reason"])
        self.store.add_audit_event(request.context_id, "ALE_ARBITRATION_DECISION", arbitration, now(), "ale", arbitration["reason"])

        if ril["decision"] != "ALLOW":
            self._contain(request.context_id, "RIL_PROCESSING_CONTAINMENT", ril, ril["reason"])
            result = {"instruction": request.instruction, "result": "Processing blocked by RIL governance.", "ril": ril, "authority": authority, "arbitration": arbitration, "timestamp": now()}
        elif arbitration["decision"] != "ALLOW":
            self.store.set_runtime_state(request.context_id, "HOLD")
            result = {"instruction": request.instruction, "result": "Processing held by ALE arbitration.", "ril": ril, "authority": authority, "arbitration": arbitration, "timestamp": now()}
        else:
            result = {"instruction": request.instruction, "result": f"Processed instruction: {request.instruction}", "ril": ril, "authority": authority, "arbitration": arbitration, "timestamp": now()}
        self._record(request.context_id, "PE", result)
        return result

    def render(self, request: OutputModeRequest) -> Dict[str, Any]:
        context = self._context(request.context_id)
        self._require_stage(context, "PE")
        processing_result = context["snapshots"][-1]["data"]
        if processing_result["ril"]["decision"] != "ALLOW" or processing_result["arbitration"]["decision"] != "ALLOW":
            raise PipelineError("Output is unavailable: governance has placed this context in containment or hold mode.", 403)
        output = {"format": request.format, "output": f"VincentOS output rendered in {request.format} mode.", "timestamp": now()}
        self._record(request.context_id, "OM", output)
        return output

    def record_feedback(self, request: FeedbackRequest) -> Dict[str, str]:
        context = self._context(request.context_id)
        self._require_stage(context, "OM")
        self._record(request.context_id, "FL", {"type": request.feedback_type, "payload": request.feedback_payload, "timestamp": now()})
        return {"status": "feedback recorded", "context_id": request.context_id}

    def hold_memory_promotion(self, context_id: str) -> Dict[str, Any]:
        context = self._context(context_id)
        detail = {"decision": "HOLD", "reason": "Canonical-memory promotion is disabled in this reference runtime pending CEGS reversibility and human-review controls."}
        self.store.add_audit_event(context_id, "CEGS_MEMORY_WRITE_HELD", detail, now(), "cegs", detail["reason"])
        return {"context_id": context_id, "runtime_state": context["runtime_state"], **detail}

    def get_context(self, context_id: str) -> Dict[str, Any]:
        return self._context(context_id)

    def get_audit_logs(self, context_id: str | None = None) -> List[Dict[str, Any]]:
        return self.store.audit_events(context_id)

    def get_recovery(self, context_id: str) -> Dict[str, Any]:
        return recovery_view(self._context(context_id))

    def policy_description(self) -> Dict[str, Any]:
        return {**self.ril.description(), "authority_validation": "Authority is validated only by the configured runtime registry; request metadata is never authority.", "telemetry": "Events are ordered, hash-linked, and redacted for common secret field names. Local SQLite is not tamper-proof.", "memory": "Canonical memory promotion is held until CEGS review, reversibility, and human-governance controls exist."}

