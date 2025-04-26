from typing import Optional

from pydantic import BaseModel, HttpUrl, Field, AnyUrl


class ParseRequest(BaseModel):
    """Request body for /parse endpoint."""

    html: str = Field(..., description="Raw HTML content to parse")
    source_url: Optional[AnyUrl] = Field(None, description="Original URL of the HTML source")
    record_id: Optional[str] = Field(None, description="External record ID (e.g., from Airtable) for tracking")


class ParseURLRequest(BaseModel):
    """Request body for /parse-url endpoint."""

    url: AnyUrl = Field(..., description="URL to fetch and parse")
    record_id: Optional[str] = Field(None, description="External record ID (e.g., from Airtable) for tracking") 