from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    id: str
    title: str
    lang: str = "en"
    source: str
    same_as: Optional[str] = None
    enabled: bool = True
    char_count: Optional[int] = None
    table_count: Optional[int] = None


class ManifestSchema(BaseModel):
    airport: str
    iata: str
    closed_world: bool = True
    documents: List[DocumentMetadata] = Field(default_factory=list)
    do_not_ingest: List[str] = Field(default_factory=list)


class SnapshotStatusResponse(BaseModel):
    version: str
    created_at: str
    document_count: int
    total_characters: int
    languages: List[str]
    documents: List[DocumentMetadata]
    is_active: bool


class RefreshResponse(BaseModel):
    success: bool
    message: str
    snapshot: SnapshotStatusResponse

