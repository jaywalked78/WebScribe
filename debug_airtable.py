#!/usr/bin/env python3
"""
Airtable Debugging Script
------------------------
Tests connectivity and checks field names in your Airtable table.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration
TOKEN = os.getenv("AIRTABLE_PERSONAL_ACCESS_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

def check_configuration():
    """Check if all required environment variables are set."""
    if not all([TOKEN, BASE_ID, TABLE_NAME]):
        print("ERROR: Missing required environment variables.")
        print(f"AIRTABLE_PERSONAL_ACCESS_TOKEN: {'✓' if TOKEN else '✗'}")
        print(f"AIRTABLE_BASE_ID: {'✓' if BASE_ID else '✗'}")
        print(f"AIRTABLE_TABLE_NAME: {'✓' if TABLE_NAME else '✗'}")
        sys.exit(1)
    
    print("✓ All required environment variables are set")

def get_table_schema():
    """Get the table schema to check field names."""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
    
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        tables = resp.json().get("tables", [])
        
        # Find our table
        target_table = None
        for table in tables:
            if table.get("name") == TABLE_NAME:
                target_table = table
                break
        
        if not target_table:
            print(f"ERROR: Table '{TABLE_NAME}' not found in base '{BASE_ID}'")
            print("Available tables:")
            for table in tables:
                print(f"  - {table.get('name')}")
            sys.exit(1)
        
        print(f"✓ Found table: {TABLE_NAME}")
        return target_table
    except Exception as e:
        print(f"ERROR: Failed to get table schema: {e}")
        if hasattr(e, "response") and e.response:
            print(f"Response: {e.response.text}")
        sys.exit(1)

def test_record_update(record_id):
    """Test updating a record to see the exact error."""
    if not record_id:
        print("No record ID provided, skipping update test")
        return
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{record_id}"
    
    # Send a minimal payload to test
    payload = {
        "fields": {
            "Title": "Test Update",
            "URL": "https://example.com/test"
        }
    }
    
    try:
        resp = requests.patch(url, headers=headers, json=payload)
        resp.raise_for_status()
        print("✓ Successfully updated test record")
        return resp.json()
    except Exception as e:
        print(f"ERROR: Failed to update record: {e}")
        if hasattr(e, "response") and e.response:
            print(f"Response: {e.response.text}")

def main():
    """Main function to run tests."""
    print("Airtable Debugging Script")
    print("------------------------")
    
    # Check configuration
    check_configuration()
    
    # Get table schema to check field names
    table = get_table_schema()
    
    print("\nField names in your Airtable table:")
    for field in table.get("fields", []):
        field_name = field.get("name")
        field_type = field.get("type")
        print(f"  - {field_name} ({field_type})")
    
    # Test updating a record if provided
    if len(sys.argv) > 1:
        record_id = sys.argv[1]
        print(f"\nTesting update with record ID: {record_id}")
        test_record_update(record_id)
    else:
        print("\nTip: Provide a record ID as a command line argument to test updating a record")

if __name__ == "__main__":
    main() 