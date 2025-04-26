from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, HttpUrl, Field


class ArticleMetadata(BaseModel):
    """Metadata extracted from scientific article."""

    title: Optional[str] = None
    authors: Optional[List[str]] = None
    publication_date: Optional[datetime] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    keywords: Optional[List[str]] = None
    abstract: Optional[str] = None


class ParseResponse(BaseModel):
    id: str
    timestamp: datetime
    source_url: Optional[HttpUrl] = None
    status: str
    markdown: str
    metadata: ArticleMetadata
    processing_time_ms: int


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime 