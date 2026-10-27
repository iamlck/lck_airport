from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    text: str
    detected_language: str
    duration_seconds: float
    confidence: Optional[float] = None


class SynthesisRequest(BaseModel):
    text: str
    language: str = "en"
    voice_speed: float = 1.0


class VisemeCue(BaseModel):
    time_ms: int
    viseme: str


class SynthesisResponse(BaseModel):
    audio_base64: str
    audio_format: str = "wav"
    language: str
    duration_ms: int
    visemes: List[VisemeCue] = []

