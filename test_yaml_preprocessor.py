#!/usr/bin/env python3
"""
Test script for YAML preprocessor functionality.

This script tests the YAML preprocessor by processing a sample
webhook_v3.py output and showing the preprocessed result.
"""

import os
import sys
import json
import yaml
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.yaml_preprocessor import YAMLPreprocessor
from app.services.webhook_processor import WebhookProcessor

# Sample webhook_v3.py output (simplified for testing)
SAMPLE_OUTPUT = {
    "id": "f28569cc-4309-4f4b-93ce-a588351d3405",
    "timestamp": "2025-04-26T14:07:34.058680+00:00",
    "source_url": "https://example.com/article",
    "status": "success",
    "markdown": """---
title: Example Scientific Article
source_url: "https://example.com/article"
date_processed: "2025-04-26T09:07:33.866336"
document_type: scientific_paper
doi: 10.1234/example.5678
authors:
  - "John Smith"
  - "Jane Doe"
publication_date: 2023
entities:
  physiological_parameter:
    - core temperature
    - heart rate
    - body temperature
  body_system:
    - cardiovascular
    - skin
  heat_therapy:
    - infrared sauna
    - local heat
  health_outcome:
    - detoxification
    - recovery
  toxin:
    - mercury
    - lead
    - heavy metals
mechanisms:
  cellular_mechanisms:
    - mitochondrial function
    - ATP production
  vascular_mechanisms:
    - blood flow
    - vasodilation
therapeutic_domains:
  - detoxification
  - infrared_therapy
study_type:
  - systematic_review
  - clinical_trial
sections:
  abstract:
    heading: Abstract
    keywords:
      - infrared therapy
      - detoxification
      - systematic review
  introduction:
    heading: Introduction
    keywords:
      - heat therapy
      - infrared sauna
      - therapeutic benefits
---

# Example Scientific Article

## Abstract

This systematic review examined the effects of infrared therapy on detoxification processes...

## Introduction

Infrared saunas have gained popularity for their potential health benefits...
""",
    "metadata": {
        "title": "Example Scientific Article",
        "authors": ["John Smith", "Jane Doe"],
        "publication_date": "2023-01-15"
    },
    "processing_time_ms": 150,
    "record_id": "sci123",
    "format": "yaml"
}

def test_yaml_preprocessor():
    """Test the YAML preprocessor with a sample output."""
    print("Testing YAML preprocessor...")
    
    # Create a YAML preprocessor
    preprocessor = YAMLPreprocessor()
    
    # Extract YAML from the markdown field
    markdown = SAMPLE_OUTPUT["markdown"]
    yaml_match = markdown.split("---\n", 2)
    if len(yaml_match) < 3:
        print("Error: Could not extract YAML from markdown")
        return
    
    yaml_content = yaml_match[1]
    
    # Process the YAML
    processed_yaml = preprocessor.process_yaml_string(yaml_content)
    
    if not processed_yaml:
        print("Error: Failed to process YAML")
        return
    
    # Print the original and processed YAML
    print("\n=== Original YAML ===")
    print(yaml_content)
    
    print("\n=== Processed YAML ===")
    print(processed_yaml)
    
    # Create output directory if it doesn't exist
    output_dir = Path("output/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the processed YAML to a file
    output_path = output_dir / "test_processed_yaml.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"---\n{processed_yaml}---\n\n{SAMPLE_OUTPUT['markdown'].split('---\n', 2)[2]}")
    
    print(f"\nSaved processed YAML to {output_path}")

def test_webhook_processor():
    """Test the webhook processor with a sample output."""
    print("\nTesting webhook processor...")
    
    # Create a webhook processor
    processor = WebhookProcessor()
    
    # Process the sample output
    processed_output = processor.process_webhook_response(SAMPLE_OUTPUT)
    
    # Print the processed output
    print("\n=== Processed Output ===")
    print(json.dumps(processed_output, indent=2))
    
    # Save the processed output to a file
    output_dir = Path("output/test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "test_processed_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_output, f, indent=2)
    
    print(f"\nSaved processed output to {output_path}")

if __name__ == "__main__":
    test_yaml_preprocessor()
    test_webhook_processor()
    
    print("\nTest completed successfully!") 