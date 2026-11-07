"""FRMS-inspired containment status for the reference runtime."""

from typing import Any, Dict


def recovery_view(context: Dict[str, Any]) -> Dict[str, Any]:
    state = context["runtime_state"]
    if state == "CONTAINMENT":
        return {"context_id": context["context_id"], "state": state, "mode": "Safe Mode", "next_step": "Obtain new corroborated provenance or authority evidence, then create a new context. This context cannot be overridden."}
    if state == "HOLD":
        return {"context_id": context["context_id"], "state": state, "mode": "Targeted Subsystem Recovery", "next_step": "Resolve the provenance conflict externally and create a new context with corroborated evidence."}
    return {"context_id": context["context_id"], "state": state, "mode": "Normal", "next_step": "No recovery action is required."}

