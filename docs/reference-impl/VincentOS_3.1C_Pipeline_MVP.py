"""
VincentOS 3.1C — Cognitive Pipeline MVP
Status: Historical Prototype / Baseline Freeze
Behavior: Immutable
Purpose: Reference Implementation of the VincentOS Cognitive Pipeline

This file demonstrates the early VincentOS cognitive pipeline:

IC → CL → PE → OM → FL

This implementation predates the formal VincentOS 4.0.1 architectural
specification and is preserved as a reference artifact.

It illustrates how governed cognition may be structured in practice,
but it is not the VincentOS architecture itself.

This code is not production software.

Authoritative architecture documents:
- docs/foundations.md
- docs/specs/VincentOS_4.0.1_MasterSpec.md

Any changes beyond this point require a version increment.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any
from datetime import datetime, timezone
import uuid

app = FastAPI(title="VincentOS 3.1C MVP",
              description="Cognitive Operating System Prototype (API-first)",
              version="3.1C")

CONTEXT_STORE: Dict[str, Any] = {}
AUDIT_LOG: List[Dict[str, Any]] = []


def generate_context_id() -> str:
    return f"ctx-{uuid.uuid4()}"


def current_time() -> str:
    return datetime.now(timezone.utc).isoformat()


class InputContextRequest(BaseModel):
    node_id: str
    input_payload: str
    metadata: Dict[str, Any] = {}


class CognitiveLensRequest(BaseModel):
    context_id: str
    lens_profile: str = "default"


class ProcessingRequest(BaseModel):
    context_id: str
    instruction: str


class OutputModeRequest(BaseModel):
    context_id: str
    format: str = "text"


class FeedbackRequest(BaseModel):
    context_id: str
    feedback_type: str
    feedback_payload: str


@app.post("/ic/ingest")
def ingest_input(request: InputContextRequest):
    """
    Stage 1: Input Context (IC)
    - Accepts raw input
    - Creates a context snapshot
    """
    context_id = generate_context_id()

    CONTEXT_STORE[context_id] = {
        "context_id": context_id,
        "node_id": request.node_id,
        "input_payload": request.input_payload,
        "metadata": request.metadata,
        "created_at": current_time(),
        "snapshots": []
    }

    return {"status": "ingested", "context_id": context_id}


@app.post("/cl/lens")
def apply_cognitive_lens(request: CognitiveLensRequest):
    """
    Stage 2: Cognitive Lens (CL)
    - Normalizes perspective
    - Tags intent
    - Applies lens profile
    """
    context = CONTEXT_STORE.get(request.context_id)
    if not context:
        return {"error": "Context not found"}

    lens_result = {
        "lens_profile": request.lens_profile,
        "intent": "analysis",
        "tags": ["vincentos", "mvp"],
        "timestamp": current_time()
    }

    context["snapshots"].append({"stage": "CL", "data": lens_result})

    return lens_result


@app.post("/pe/process")
def process_reasoning(request: ProcessingRequest):
    """
    Stage 3: Processing Engine (PE)
    - Simulates reasoning
    - Generates decision trace
    - Invokes RIL placeholder
    """
    context = CONTEXT_STORE.get(request.context_id)
    if not context:
        return {"error": "Context not found"}

    decision_trace = {
        "instruction": request.instruction,
        "result": f"Processed instruction: {request.instruction}",
        "ril_check": "PASSED (placeholder)",
        "timestamp": current_time()
    }

    context["snapshots"].append({"stage": "PE", "data": decision_trace})

    AUDIT_LOG.append({
        "context_id": request.context_id,
        "event": "PE_EXECUTION",
        "timestamp": current_time()
    })

    return decision_trace


@app.post("/om/render")
def render_output(request: OutputModeRequest):
    """
    Stage 4: Output Mode (OM)
    - Formats output for delivery
    """
    context = CONTEXT_STORE.get(request.context_id)
    if not context:
        return {"error": "Context not found"}

    output = {
        "format": request.format,
        "output": f"VincentOS output rendered in {request.format} mode.",
        "timestamp": current_time()
    }

    context["snapshots"].append({"stage": "OM", "data": output})

    return output


@app.post("/fl/feedback")
def feedback_loop(request: FeedbackRequest):
    """
    Stage 5: Feedback Loop (FL)
    - Accepts user/system feedback
    - Prepares for future adaptation
    """
    context = CONTEXT_STORE.get(request.context_id)
    if not context:
        return {"error": "Context not found"}

    feedback = {
        "type": request.feedback_type,
        "payload": request.feedback_payload,
        "timestamp": current_time()
    }

    context["snapshots"].append({"stage": "FL", "data": feedback})

    return {"status": "feedback recorded"}


@app.get("/context/{context_id}")
def get_context(context_id: str):
    """
    Retrieve full context snapshot history
    """
    return CONTEXT_STORE.get(context_id, {"error": "Context not found"})


@app.get("/contexts")
def list_contexts():
    """
    List all context IDs
    """
    return {"contexts": list(CONTEXT_STORE.keys())}


@app.get("/audit/logs")
def get_audit_logs():
    """
    Retrieve audit logs (RIL / Governance hooks)
    """
    return AUDIT_LOG


@app.get("/health")
def health_check():
    """
    System heartbeat
    """
    return {
        "status": "healthy",
        "vincentos_version": "3.1C",
        "timestamp": current_time()
    }


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_dashboard():
    return FileResponse("static/index.html")

