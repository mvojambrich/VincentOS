"""Fail-closed authority-validation boundary.

Authority comes only from the runtime operator's local registry, never from a
request, perceived signal, or metadata assertion.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuthorityResult:
    valid: bool
    status: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {"valid": self.valid, "status": self.status, "reason": self.reason}


class AuthorityValidator:
    def __init__(self, allowed_ids: set[str] | None = None, registry_path: str | None = None) -> None:
        self.registry_available = False
        self.authorities: dict[str, Any] = {}
        if allowed_ids is not None:
            self.registry_available = True
            self.authorities = {authority_id: {"active": True, "scopes": ["safety_critical"]} for authority_id in allowed_ids}
            return
        path = Path(registry_path or os.getenv("VINCENTOS_AUTHORITY_REGISTRY", "config/authority_registry.json"))
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
            authorities = content.get("authorities", {})
            if isinstance(authorities, dict):
                self.authorities = authorities
                self.registry_available = True
        except (OSError, json.JSONDecodeError):
            # A missing or malformed registry deliberately leaves the validator unavailable.
            pass

    def validate(self, authority_id: str | None) -> AuthorityResult:
        if not self.registry_available:
            return AuthorityResult(False, "UNAVAILABLE", "Authority registry is unavailable or invalid; fail-closed policy applies.")
        if not authority_id:
            return AuthorityResult(False, "MISSING", "A configured authority identifier is required for this action.")
        record = self.authorities.get(authority_id)
        if not isinstance(record, dict) or not record.get("active"):
            return AuthorityResult(False, "REJECTED", "The supplied authority identifier is not active in the runtime registry.")
        if "safety_critical" not in record.get("scopes", []):
            return AuthorityResult(False, "OUT_OF_SCOPE", "The authority identifier is not scoped for safety-critical actions.")
        return AuthorityResult(True, "VALID", "Authority identifier is active and scoped in the runtime registry.")

