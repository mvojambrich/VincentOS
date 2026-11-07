"""Small ALE reference boundary for conflicts in otherwise admissible work."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ArbitrationDecision:
    decision: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"decision": self.decision, "reason": self.reason}


class ArbitrationEngine:
    def resolve(self, has_conflict: bool) -> ArbitrationDecision:
        if has_conflict:
            return ArbitrationDecision("HOLD", "Conflicting provenance was declared; a new, corroborated context is required before processing can resume.")
        return ArbitrationDecision("ALLOW", "No declared conflict requires arbitration in this reference runtime.")

