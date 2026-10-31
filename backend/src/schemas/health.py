from typing import Dict, Any
from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    status: str = "ok"
    details: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str = "healthy"
    app_name: str
    environment: str
    version: str = "0.1.0"
    active_llm: str
    guardrail_model: str
    services: Dict[str, ServiceStatus] = Field(default_factory=dict)

