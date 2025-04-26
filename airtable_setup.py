#!/usr/bin/env python3
"""
Airtable Setup Utility for WebScribe
------------------------------------

This script helps users set up an Airtable base with the correct structure for WebScribe.
It requires an Airtable personal access token, creates a new base, and configures the required fields.

Usage:
    python airtable_setup.py

Requirements:
    - requests
    - python-dotenv
"""

import os
import sys
import json
import time
from typing import Dict, Any, List, Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
TOKEN = os.getenv("AIRTABLE_PERSONAL_ACCESS_TOKEN")
BASE_NAME = "WebScribe Content Database"
TABLE_NAME = "Parsed Articles"

# Field configuration
FIELDS = [
    {"name": "URL", "type": "urlField"},
    {"name": "Title", "type": "singleLineText"},
    {"name": "Authors", "type": "singleLineText"},
    {"name": "PublicationDate", "type": "date"},
    {"name": "Journal", "type": "singleLineText"},
    {"name": "DOI", "type": "singleLineText"},
    {"name": "Keywords", "type": "singleLineText"},
    {"name": "Abstract", "type": "multilineText"},
    {"name": "Markdown", "type": "multilineText"},
    {"name": "ParseID", "type": "singleLineText"},
    {"name": "ProcessingTimeMs", "type": "number", "options": {"precision": 0}},
]


def print_step(step: str) -> None:
    """Print a step in the setup process."""
    print(f"\n=== {step} ===")


def check_token() -> None:
    """Check if personal access token is available and valid."""
    print_step("Checking Personal Access Token")
    
    if not TOKEN:
        print("ERROR: AIRTABLE_PERSONAL_ACCESS_TOKEN not found in environment variables or .env file")
        print("Please set your Airtable personal access token and try again:")
        print("  export AIRTABLE_PERSONAL_ACCESS_TOKEN=your_token")
        print("  or add AIRTABLE_PERSONAL_ACCESS_TOKEN=your_token to your .env file")
        sys.exit(1)
    
    # Test the token by making a simple request
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        resp = requests.get("https://api.airtable.com/v0/meta/bases", headers=headers)
        if resp.status_code == 401:
            print("ERROR: Invalid personal access token. Please check your token and try again.")
            sys.exit(1)
        resp.raise_for_status()
        print("✅ Personal access token is valid")
    except Exception as e:
        print(f"ERROR: Failed to connect to Airtable API: {e}")
        sys.exit(1)


def create_base() -> str:
    """Create a new Airtable base for WebScribe."""
    print_step("Creating Airtable Base")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": BASE_NAME,
        "tables": [
            {
                "name": TABLE_NAME,
                "fields": FIELDS
            }
        ]
    }
    
    try:
        resp = requests.post(
            "https://api.airtable.com/v0/meta/bases",
            headers=headers,
            json=payload
        )
        resp.raise_for_status()
        result = resp.json()
        base_id = result.get("id")
        print(f"✅ Created base '{BASE_NAME}' with ID: {base_id}")
        return base_id
    except Exception as e:
        print(f"ERROR: Failed to create Airtable base: {e}")
        if hasattr(e, "response") and e.response and e.response.text:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def update_env_file(base_id: str) -> None:
    """Update .env file with Airtable configuration."""
    print_step("Updating .env File")
    
    env_path = ".env"
    
    # Read existing .env content
    env_content = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            env_content = f.read().splitlines()
    
    # Variables to set
    new_vars = {
        "AIRTABLE_BASE_ID": base_id,
        "AIRTABLE_TABLE_NAME": TABLE_NAME
    }
    
    # Update or add variables
    updated = {key: False for key in new_vars}
    new_content = []
    
    for line in env_content:
        line_updated = False
        for key, value in new_vars.items():
            if line.startswith(f"{key}="):
                new_content.append(f"{key}={value}")
                updated[key] = True
                line_updated = True
                break
        if not line_updated:
            new_content.append(line)
    
    # Add missing variables
    for key, value in new_vars.items():
        if not updated[key]:
            new_content.append(f"{key}={value}")
    
    # Write updated content
    with open(env_path, "w") as f:
        f.write("\n".join(new_content) + "\n")
    
    print(f"✅ Updated .env file with Airtable configuration")


def main() -> None:
    """Main function to set up Airtable integration."""
    print("WebScribe Airtable Setup Utility")
    print("--------------------------------")
    
    check_token()
    base_id = create_base()
    update_env_file(base_id)
    
    print("\n✨ Setup Complete! ✨")
    print(f"""
Your Airtable base has been set up successfully:

  Base Name: {BASE_NAME}
  Base ID: {base_id}
  Table Name: {TABLE_NAME}

These settings have been saved to your .env file.
You can now use the Airtable integration with WebScribe!
    """)


if __name__ == "__main__":
    main() 