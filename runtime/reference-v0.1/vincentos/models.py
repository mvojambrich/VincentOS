"""Request schemas for the public runtime interface."""

from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


class InputContextRequest(BaseModel):
    node_id: str = Field(..., min_length=1, examples=["mobile-demo"])
    input_payload: str = Field(..., min_length=1, examples=["Summarize this request."])
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CognitiveLensRequest(BaseModel):
    context_id: str
    lens_profile: str = Field(default="default", min_length=1)


class ProcessingRequest(BaseModel):
    context_id: str
    instruction: str = Field(..., min_length=1)
    authority_id: str | None = Field(default=None, examples=["operator-demo"])


class OutputModeRequest(BaseModel):
    context_id: str
    format: Literal["text", "json", "markdown"] = "text"


class FeedbackRequest(BaseModel):
    context_id: str
    feedback_type: str = Field(..., min_length=1)
    feedback_payload: str = Field(..., min_length=1)

