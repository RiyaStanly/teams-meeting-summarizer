"""Pydantic schemas for API request/response validation."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    """Request schema for /summarize endpoint."""

    transcript: str = Field(..., description="Meeting transcript text", min_length=10)
    meeting_id: Optional[str] = Field(None, description="Optional meeting identifier")
    metadata: Optional[Dict] = Field(None, description="Optional metadata dictionary")
    ner_backend: Optional[str] = Field(
        "spacy", description="NER backend to use ('spacy' or 'huggingface')"
    )


class EntityInfo(BaseModel):
    """Entity information schema."""

    entity: str
    count: int
    examples: Optional[List[Dict]] = None
    avg_confidence: Optional[float] = None


class EntitiesResponse(BaseModel):
    """Entities response schema."""

    backend: str
    total_unique_entities: int
    entity_types: List[str]
    entities_by_type: Dict[str, List[EntityInfo]]


class SummarizeResponse(BaseModel):
    """Response schema for /summarize endpoints."""

    meeting_id: str
    summary: str
    entities: Dict
    metadata: Dict
    transcript_length: int
    cleaned_transcript_length: int
    summary_length: int
    compression_ratio: float = Field(
        ..., description="Summary length as percentage of transcript length"
    )


class HealthResponse(BaseModel):
    """Response schema for /health endpoint."""

    status: str
    model_loaded: bool
    ner_backend: str
    version: str
