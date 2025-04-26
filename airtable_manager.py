#!/usr/bin/env python3
"""
Airtable Manager Utility for WebScribe
-------------------------------------

This script helps users manage their Airtable integration with WebScribe.
It provides commands to list, view, delete, and export records.

Usage:
    python airtable_manager.py <command> [options]

Commands:
    list       - List all records in the Airtable table
    view       - View a specific record by ID
    delete     - Delete a specific record by ID
    export     - Export all records to a JSON file
    
Examples:
    python airtable_manager.py list
    python airtable_manager.py view rec123456
    python airtable_manager.py delete rec123456
    python airtable_manager.py export output.json

Requirements:
    - requests
    - python-dotenv
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List, Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
TOKEN = os.getenv("AIRTABLE_PERSONAL_ACCESS_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")


class AirtableManager:
    """Utility class for managing Airtable integration."""
    
    def __init__(self):
        self.token = TOKEN
        self.base_id = BASE_ID
        self.table_name = TABLE_NAME
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        self._check_configuration()
    
    def _check_configuration(self):
        """Check if Airtable is properly configured."""
        if not all([self.token, self.base_id, self.table_name]):
            print("ERROR: Airtable configuration is incomplete.")
            print("Please make sure the following environment variables are set:")
            print("  - AIRTABLE_PERSONAL_ACCESS_TOKEN")
            print("  - AIRTABLE_BASE_ID")
            print("  - AIRTABLE_TABLE_NAME")
            print("\nYou can run airtable_setup.py to set up a new Airtable base.")
            sys.exit(1)
    
    def list_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List records in the Airtable table."""
        records = []
        offset = None
        
        while True:
            params = {"pageSize": min(limit - len(records), 100)}
            if offset:
                params["offset"] = offset
                
            try:
                resp = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params=params
                )
                resp.raise_for_status()
                result = resp.json()
                
                records.extend(result.get("records", []))
                
                # Check if we need to paginate
                offset = result.get("offset")
                if not offset or len(records) >= limit:
                    break
                    
            except Exception as e:
                print(f"ERROR: Failed to list records: {e}")
                sys.exit(1)
                
        return records
    
    def view_record(self, record_id: str) -> Dict[str, Any]:
        """View a specific record by ID."""
        try:
            resp = requests.get(
                f"{self.base_url}/{record_id}",
                headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"ERROR: Failed to retrieve record {record_id}: {e}")
            sys.exit(1)
    
    def delete_record(self, record_id: str) -> Dict[str, Any]:
        """Delete a specific record by ID."""
        try:
            resp = requests.delete(
                f"{self.base_url}/{record_id}",
                headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"ERROR: Failed to delete record {record_id}: {e}")
            sys.exit(1)
    
    def export_records(self, output_file: str) -> None:
        """Export all records to a JSON file."""
        records = self.list_records(limit=1000)  # Get up to 1000 records
        
        try:
            with open(output_file, 'w') as f:
                json.dump(records, f, indent=2)
            print(f"✅ Exported {len(records)} records to {output_file}")
        except Exception as e:
            print(f"ERROR: Failed to export records: {e}")
            sys.exit(1)


def main():
    """Main function to manage Airtable integration."""
    parser = argparse.ArgumentParser(description="Manage WebScribe Airtable integration")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all records")
    list_parser.add_argument("--limit", type=int, default=100, help="Maximum number of records to retrieve")
    
    # View command
    view_parser = subparsers.add_parser("view", help="View a specific record")
    view_parser.add_argument("record_id", help="Record ID to view")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a specific record")
    delete_parser.add_argument("record_id", help="Record ID to delete")
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export all records to a JSON file")
    export_parser.add_argument("output_file", help="Output JSON file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = AirtableManager()
    
    if args.command == "list":
        records = manager.list_records(limit=args.limit)
        print(f"Found {len(records)} records:")
        for idx, record in enumerate(records, 1):
            title = record.get("fields", {}).get("Title", "Untitled")
            url = record.get("fields", {}).get("URL", "No URL")
            print(f"{idx}. {title} [{record['id']}]")
            print(f"   URL: {url}")
            print()
    
    elif args.command == "view":
        record = manager.view_record(args.record_id)
        fields = record.get("fields", {})
        
        print(f"Record ID: {record['id']}")
        print(f"Created: {record.get('createdTime', 'Unknown')}")
        
        # Print fields in a nicer format
        for key, value in fields.items():
            if key == "Markdown" and value:
                # Truncate markdown for display
                print(f"{key}: {value[:100]}... (truncated)")
            else:
                print(f"{key}: {value}")
    
    elif args.command == "delete":
        if not args.force:
            confirm = input(f"Are you sure you want to delete record {args.record_id}? (y/N): ")
            if confirm.lower() != "y":
                print("Operation cancelled.")
                sys.exit(0)
        
        result = manager.delete_record(args.record_id)
        print(f"✅ Record {args.record_id} deleted successfully")
    
    elif args.command == "export":
        manager.export_records(args.output_file)


if __name__ == "__main__":
    main() 