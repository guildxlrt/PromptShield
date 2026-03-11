from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    prompt: str = Field(..., description="Prompt to scan")
    context: Optional[str] = Field(None, description="System/LLM context")


class ScanResponse(BaseModel):
    scan_id: UUID
    verdict: Literal["pass", "blocked", "flag"]
    threat_type: Literal["prompt_injection", "jailbreak", "none"]
    confidence: float
    reason: str
    sanitized_prompt: str
    pipeline_layer: Literal["regex", "embedding", "llm", "none"]
