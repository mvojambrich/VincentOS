"""CPS reference packet envelope used between runtime stages."""

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class CognitivePacket:
    packet_id: str
    correlation_id: str
    packet_type: str
    stage: str
    created_at: str
    payload: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

