from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    document_title: str
    source_file: str
    snippet: str
    confidence: Optional[float] = None


class ChatRequest(BaseModel):
    query: str = Field(..., description="Passenger question or statement")
    strategy: Literal["okf", "rag"] = Field(default="okf", description="Knowledge retrieval strategy")
    session_id: Optional[str] = Field(default=None, description="Conversation session ID")
    user_id: Optional[str] = Field(default=None, description="Optional passenger/device user ID")
    language: Optional[str] = Field(default="en", description="Preferred response language: en, hi, es")
    stream: bool = Field(default=False, description="Whether to stream response via SSE")


class ChatResponse(BaseModel):
    answer: str
    strategy_used: str
    session_id: str
    citations: List[Citation] = Field(default_factory=list)
    latency_ms: float
    abstained: bool = False
    tokens_used: Optional[int] = None


class StreamChunk(BaseModel):
    chunk: str
    is_final: bool = False
    citations: Optional[List[Citation]] = None
    abstained: bool = False

