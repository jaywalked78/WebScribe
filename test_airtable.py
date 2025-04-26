#!/usr/bin/env python3
"""
WebScribe Airtable Integration Test
----------------------------------

This script tests the Airtable integration by:
1. Parsing a URL
2. Syncing the content with Airtable
3. Updating the same record with a new parse

Usage:
    python test_airtable.py URL
    
Example:
    python test_airtable.py https://example.com/article
"""

import sys
import json
import time
from typing import Dict, Any, Optional
import argparse
import uuid
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from app.services.parser import HTMLParserService
from app.services.airtable import AirtableService
from app.models.output import ParseResponse, ArticleMetadata


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test WebScribe Airtable integration")
    parser.add_argument("url", help="URL to parse")
    return parser.parse_args()


def main():
    """Main function to test Airtable integration."""
    args = parse_args()
    
    # Create services
    parser = HTMLParserService()
    airtable = AirtableService()
    
    if not airtable.is_configured():
        print("ERROR: Airtable integration not configured.")
        print("Please set AIRTABLE_PERSONAL_ACCESS_TOKEN, AIRTABLE_BASE_ID, and AIRTABLE_TABLE_NAME in .env file.")
        print("You can use airtable_setup.py to set up a new Airtable base.")
        sys.exit(1)
    
    # Step 1: Parse URL
    print(f"Fetching and parsing URL: {args.url}")
    try:
        html_content = parser.fetch(args.url)
        markdown_content, metadata = parser.parse(html_content, args.url)
    except Exception as e:
        print(f"ERROR: Failed to parse URL: {e}")
        sys.exit(1)
    
    # Create response object
    response_id = str(uuid.uuid4())
    response = ParseResponse(
        id=response_id,
        timestamp=datetime.now(timezone.utc),
        source_url=args.url,
        status="success",
        markdown=markdown_content,
        metadata=metadata,
        processing_time_ms=int(time.time() * 1000),
        record_id=None  # No record ID for initial creation
    )
    
    # Step 2: Create a new record in Airtable
    print("\nCreating new record in Airtable...")
    try:
        result = airtable.sync_parsed_content(response)
        record_id = result.get("id")
        print(f"Created Airtable record with ID: {record_id}")
    except Exception as e:
        print(f"ERROR: Failed to create Airtable record: {e}")
        sys.exit(1)
    
    # Step 3: Update the same record with slightly modified content
    print("\nUpdating the record...")
    time.sleep(1)  # Short delay
    
    # Modify response for update
    response.record_id = record_id
    response.id = str(uuid.uuid4())  # New unique ID
    response.timestamp = datetime.now(timezone.utc)
    response.markdown = markdown_content + "\n\n---\n\nUpdated on " + datetime.now(timezone.utc).isoformat()
    
    try:
        result = airtable.sync_parsed_content(response)
        print(f"Updated Airtable record with ID: {record_id}")
    except Exception as e:
        print(f"ERROR: Failed to update Airtable record: {e}")
        sys.exit(1)
    
    print("\n✅ Airtable integration test completed successfully!")
    print(f"You can view your Airtable record at: https://airtable.com/{airtable.base_id}/{airtable.table_name}")


if __name__ == "__main__":
    main() 