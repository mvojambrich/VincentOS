"""Reality Integrity Layer (RIL): the non-bypassable pre-IC gate.

This module implements the supplied RIL as transparent prototype policy code.
Its inputs are assertions supplied in request metadata, not independently
verified evidence; production verification requires trusted external systems.
"""

from dataclasses import dataclass
from typing import Any, Dict, Literal

Decision = Literal["ALLOW", "CONTAIN", "BLOCK"]
Classification = Literal["Verified", "Probable", "Untrusted"]


@dataclass(frozen=True)
class RILDecision:
    classification: Classification
    decision: Decision
    authority_aligned: bool
    mode: Literal["normal", "support", "clarification", "containment"]
    confidence: float
    provenance: str
    reason: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "classification": self.classification,
            "decision": self.decision,
            "authority_aligned": self.authority_aligned,
            "mode": self.mode,
            "confidence": self.confidence,
            "provenance": self.provenance,
            "reason": self.reason,
        }


class RILEngine:
    """Deterministic implementation of the RIL rules for Runtime v0.1."""

    BLOCK_PATTERNS = ("ignore previous", "bypass security", "exfiltrate", "delete all")
    SAFETY_CRITICAL_PATTERNS = ("deploy", "production", "transfer", "purchase", "send email", "publish")
    TRUSTED_SOURCES = {"demo", "swagger", "internal", "system", "verified"}

    def assess_input(self, input_payload: str, metadata: Dict[str, Any]) -> RILDecision:
        content = input_payload.lower()
        source = str(metadata.get("source", "unknown")).strip().lower()
        provenance = str(metadata.get("provenance", source if source != "unknown" else "")).strip()
        source_count = metadata.get("source_count", 1 if provenance else 0)
        # Authority is intentionally unresolved here; it is checked by the
        # AuthorityValidator only when a safety-critical action is requested.
        authority_aligned = False

        if any(term in content for term in self.BLOCK_PATTERNS):
            return RILDecision("Untrusted", "CONTAIN", authority_aligned, "containment", 0.98, provenance or "none", "Containment required: high-risk pattern detected.")
        if not provenance or source not in self.TRUSTED_SOURCES:
            return RILDecision("Untrusted", "CONTAIN", authority_aligned, "clarification", 0.80, provenance or "none", "Clarification required: provenance is absent or not trusted in v0.1.")
        if isinstance(source_count, int) and source_count >= 2:
            return RILDecision("Verified", "ALLOW", authority_aligned, "normal", 0.90, provenance, "Admissible: multiple declared sources and trusted provenance.")
        return RILDecision("Probable", "ALLOW", authority_aligned, "normal", 0.70, provenance, "Admissible as Probable only: single-source input cannot become Verified.")

    def assess_processing(self, ril: Dict[str, Any], instruction: str, authority_aligned: bool) -> RILDecision:
        """Apply non-escalation safeguards for safety-critical actions."""
        content = instruction.lower()
        critical = next((term for term in self.SAFETY_CRITICAL_PATTERNS if term in content), None)
        if ril["classification"] == "Untrusted":
            return RILDecision("Untrusted", "CONTAIN", authority_aligned, "containment", ril["confidence"], ril["provenance"], "Containment required: Untrusted inputs cannot enter cognitive processing.")
        if critical and not authority_aligned:
            return RILDecision(ril["classification"], "BLOCK", False, "containment", 0.95, ril["provenance"], f"Blocked: safety-critical action '{critical}' lacks a valid authority chain.")
        if critical and ril["classification"] == "Untrusted":
            return RILDecision("Untrusted", "BLOCK", authority_aligned, "containment", 0.98, ril["provenance"], f"Blocked: safety-critical action '{critical}' requires a non-Untrusted classification.")
        return RILDecision(ril["classification"], "ALLOW", authority_aligned, "normal", ril["confidence"], ril["provenance"], "Processing permitted by RIL.")

    def description(self) -> Dict[str, Any]:
        return {
            "engine": "Reality Integrity Layer (RIL) v0.1",
            "position": "mandatory pre-IC gate",
            "classifications": ["Verified", "Probable", "Untrusted"],
            "trusted_sources": sorted(self.TRUSTED_SOURCES),
            "block_patterns": list(self.BLOCK_PATTERNS),
            "safety_critical_patterns": list(self.SAFETY_CRITICAL_PATTERNS),
            "authority_requirement": "Safety-critical actions require a valid result from the runtime AuthorityValidator.",
            "memory_rule": "single-source input is never classified Verified",
        }

