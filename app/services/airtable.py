from __future__ import annotations

import logging
import json
from typing import Dict, Any, Optional, List, Union

import requests

from ..config import settings
from ..models.output import ParseResponse

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)


class AirtableService:
    """Service for interacting with Airtable API to sync parsed content."""

    def __init__(self):
        self.api_key = settings.AIRTABLE_PERSONAL_ACCESS_TOKEN
        self.base_id = settings.AIRTABLE_BASE_ID
        self.table_name = settings.AIRTABLE_TABLE_NAME
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def is_configured(self) -> bool:
        """Check if Airtable integration is configured properly."""
        return bool(self.api_key and self.base_id and self.table_name)

    def sync_parsed_content(self, response: ParseResponse) -> Dict[str, Any]:
        """Sync parsed content to Airtable, creating or updating records as needed.
        
        Args:
            response: The parsed content response
            
        Returns:
            Dict containing the Airtable API response
            
        Raises:
            RuntimeError: If the Airtable API request fails
        """
        if not self.is_configured():
            logger.warning("Airtable integration not configured, skipping sync")
            return {"status": "skipped", "reason": "not_configured"}

        # If we have a record_id, update existing record, otherwise create new
        if response.record_id:
            return self._update_record(response)
        else:
            return self._create_record(response)

    def _create_record(self, response: ParseResponse) -> Dict[str, Any]:
        """Create a new record in Airtable with parsed content."""
        payload = self._prepare_record_payload(response)
        
        try:
            logger.info("Creating new Airtable record")
            resp = requests.post(
                self.base_url,
                headers=self.headers,
                json={"fields": payload},
                timeout=settings.TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info("Created Airtable record with ID: %s", result.get("id"))
            return result
        except Exception as exc:
            logger.error("Failed to create Airtable record: %s", exc)
            raise RuntimeError(f"Airtable API error: {exc}") from exc

    def _update_record(self, response: ParseResponse) -> Dict[str, Any]:
        """Update an existing record in Airtable with parsed content."""
        payload = self._prepare_record_payload(response)
        
        try:
            logger.info("Updating Airtable record: %s", response.record_id)
            resp = requests.patch(
                f"{self.base_url}/{response.record_id}",
                headers=self.headers,
                json={"fields": payload},
                timeout=settings.TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            result = resp.json()
            logger.info("Updated Airtable record: %s", response.record_id)
            return result
        except Exception as exc:
            logger.error("Failed to update Airtable record: %s", exc)
            raise RuntimeError(f"Airtable API error: {exc}") from exc

    def _prepare_record_payload(self, response: ParseResponse) -> Dict[str, Any]:
        """Prepare the record payload to send to Airtable."""
        # Convert metadata to a format Airtable can store
        metadata = response.metadata.dict()
        
        # Handle authors list by converting to comma-separated string if present
        if metadata.get("authors"):
            metadata["authors"] = ", ".join(metadata["authors"])
            
        # Handle keywords list by converting to comma-separated string if present
        if metadata.get("keywords"):
            metadata["keywords"] = ", ".join(metadata["keywords"])
            
        # Construct payload with fields matching Airtable schema
        payload = {
            "URL": str(response.source_url) if response.source_url else None,
            "Title": metadata.get("title"),
            "Authors": metadata.get("authors"),
            "PublicationDate": metadata.get("publication_date").isoformat() if metadata.get("publication_date") else None,
            "Journal": metadata.get("journal"),
            "DOI": metadata.get("doi"),
            "Keywords": metadata.get("keywords"),
            "Abstract": metadata.get("abstract"),
            "Markdown": response.markdown,
            "ParseID": response.id,
            "ProcessingTimeMs": response.processing_time_ms,
        }
        
        # Remove None values to avoid overwriting existing data with nulls
        return {k: v for k, v in payload.items() if v is not None} 