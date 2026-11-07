"""VincentOS 4.0.1-aligned Reference Runtime v0.1 API entry point."""

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException

from vincentos.core import PipelineError, VincentRuntime
from vincentos.models import CognitiveLensRequest, FeedbackRequest, InputContextRequest, OutputModeRequest, ProcessingRequest

runtime = VincentRuntime()
app = FastAPI(title="VincentOS 4.0.1-aligned Reference Runtime v0.1", description="A limited, governed reference runtime for the VincentOS architecture.", version="0.1.0")


def execute(operation):  # type: ignore[no-untyped-def]
    try:
        return operation()
    except PipelineError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error


@app.get("/", tags=["System"])
def service_overview() -> Dict[str, Any]:
    return {"service": "VincentOS 4.0.1-aligned Reference Runtime", "version": "0.1.0", "pipeline": "RIL → IC → CL → PE → OM → FL", "implemented_boundaries": ["RIL", "authority validation", "ALE hold", "UTSS-style telemetry", "FRMS containment", "CEGS memory hold"], "model_integration": "not enabled in v0.1"}


@app.post("/ic/ingest", tags=["Pipeline"])
def ingest_input(request: InputContextRequest) -> Dict[str, Any]:
    return runtime.ingest(request)


@app.post("/cl/lens", tags=["Pipeline"])
def apply_cognitive_lens(request: CognitiveLensRequest) -> Dict[str, Any]:
    return execute(lambda: runtime.apply_lens(request))


@app.post("/pe/process", tags=["Pipeline"])
def process_reasoning(request: ProcessingRequest) -> Dict[str, Any]:
    """Evaluate RIL policy, then simulate processing only when governance allows it."""
    return execute(lambda: runtime.process(request))


@app.post("/om/render", tags=["Pipeline"])
def render_output(request: OutputModeRequest) -> Dict[str, Any]:
    return execute(lambda: runtime.render(request))


@app.post("/fl/feedback", tags=["Pipeline"])
def feedback_loop(request: FeedbackRequest) -> Dict[str, str]:
    return execute(lambda: runtime.record_feedback(request))


@app.get("/context/{context_id}", tags=["Governance"])
def get_context(context_id: str) -> Dict[str, Any]:
    return execute(lambda: runtime.get_context(context_id))


@app.get("/audit/logs", tags=["Governance"])
def get_audit_logs(context_id: str | None = None) -> List[Dict[str, Any]]:
    return runtime.get_audit_logs(context_id)


@app.get("/governance/policies", tags=["Governance"])
def get_policies() -> Dict[str, Any]:
    return runtime.policy_description()


@app.get("/recovery/{context_id}", tags=["Recovery"])
def get_recovery(context_id: str) -> Dict[str, Any]:
    return execute(lambda: runtime.get_recovery(context_id))


@app.post("/memory/{context_id}/promote", tags=["Memory"])
def promote_memory(context_id: str) -> Dict[str, Any]:
    """Record a CEGS hold: canonical-memory writes are intentionally unavailable."""
    return execute(lambda: runtime.hold_memory_promotion(context_id))


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    return {"status": "healthy", "vincentos_version": "reference-runtime-v0.1", "storage": "sqlite"}

