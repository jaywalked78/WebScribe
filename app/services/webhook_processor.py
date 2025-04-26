#!/usr/bin/env python3
"""
Webhook Processor for Scientific HTML Parser

This script acts as an intermediary between webhook_v3.py and n8n,
extracting YAML front matter from the markdown field, preprocessing it
to make it more n8n-friendly, and then repackaging the response.

This simplifies the structure for easier JavaScript parsing in n8n workflows.
"""

import os
import re
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

from ..config import settings
from .yaml_preprocessor import YAMLPreprocessor

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)

class WebhookProcessor:
    """
    Process webhook responses from webhook_v3.py, applying YAML preprocessing
    before sending to n8n for further integration.
    """
    
    def __init__(self):
        """Initialize the processor with configuration from environment variables."""
        self.n8n_webhook_url = os.environ.get("N8N_WEBHOOK_URL", "")
        self.secret_key = os.environ.get("WEBHOOK_SECRET", "")
        self.max_retries = int(os.environ.get("WEBHOOK_MAX_RETRIES", "3"))
        self.retry_delay = float(os.environ.get("WEBHOOK_RETRY_DELAY", "2.0"))
        self.verify_ssl = not os.environ.get("WEBHOOK_SKIP_SSL_VERIFY", "").lower() in ("true", "1", "yes")
        self.save_local_files = os.environ.get("SAVE_LOCAL_FILES", "true").lower() in ("true", "1", "yes")
        self.output_dir = os.environ.get("OUTPUT_DIR", "output/md")
        self.convert_to_json = os.environ.get("CONVERT_TO_JSON", "false").lower() in ("true", "1", "yes")
        
        # Create yaml preprocessor instance
        self.yaml_preprocessor = YAMLPreprocessor()
    
    def process_webhook_response(self, webhook_response: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
        """
        Process the webhook response by extracting and preprocessing the YAML front matter.
        
        Args:
            webhook_response: Response from webhook_v3.py, either a single dict or a list of dicts
            
        Returns:
            Union[Dict, List[Dict]]: Processed response with simplified YAML
        """
        if isinstance(webhook_response, list):
            # Process a list of responses
            processed_responses = []
            for response in webhook_response:
                processed_responses.append(self._process_single_response(response))
            return processed_responses
        else:
            # Process a single response
            return self._process_single_response(webhook_response)
    
    def _process_single_response(self, response: Dict) -> Dict:
        """
        Process a single webhook response by extracting and preprocessing the YAML.
        
        Args:
            response: Single response dict from webhook_v3.py
            
        Returns:
            Dict: Processed response with simplified YAML
        """
        try:
            # Check if markdown field exists
            if 'markdown' not in response or not response['markdown']:
                logger.warning("No markdown field found in response")
                return response
            
            markdown = response['markdown']
            
            # Extract YAML front matter
            yaml_match = re.search(r'^---\n(.*?)\n---', markdown, re.DOTALL)
            if not yaml_match:
                logger.warning("No YAML front matter found in markdown")
                return response
            
            yaml_content = yaml_match.group(1)
            remaining_content = markdown[yaml_match.end():]
            
            # Process the YAML using our preprocessor
            processed_yaml = self.yaml_preprocessor.process_yaml_string(yaml_content)
            
            if processed_yaml:
                # Reconstruct the markdown with processed YAML
                processed_markdown = f"---\n{processed_yaml}---\n\n{remaining_content}"
                
                # Update the response with the processed markdown
                response['markdown'] = processed_markdown
                
                # Add a processing note to the response
                response['yaml_preprocessed'] = True
                response['yaml_preprocessed_timestamp'] = datetime.now().isoformat()
            else:
                logger.error("Failed to process YAML content")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return response
    
    def forward_to_n8n(self, processed_response: Union[Dict, List[Dict]]) -> bool:
        """
        Forward the processed response to n8n webhook.
        
        Args:
            processed_response: The processed response to forward
            
        Returns:
            bool: True if forwarding was successful, False otherwise
        """
        if not self.n8n_webhook_url:
            logger.warning("N8N_WEBHOOK_URL is not configured, not forwarding")
            return False
        
        try:
            # Convert to JSON string
            payload_json = json.dumps(processed_response)
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Send to n8n webhook
            response = requests.post(
                self.n8n_webhook_url, 
                data=payload_json, 
                headers=headers,
                verify=self.verify_ssl
            )
            
            # Check response status
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Successfully forwarded to n8n: Status {response.status_code}")
                return True
            else:
                logger.error(f"Failed to forward to n8n: Status {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error forwarding to n8n: {e}")
            return False
    
    def process_and_forward(self, webhook_response: Union[Dict, List[Dict]]) -> bool:
        """
        Process the webhook response and forward it to n8n.
        
        Args:
            webhook_response: Response from webhook_v3.py
            
        Returns:
            bool: True if processing and forwarding was successful, False otherwise
        """
        # Process the response
        processed_response = self.process_webhook_response(webhook_response)
        
        # Save locally if configured
        if self.save_local_files:
            self._save_local_files(processed_response)
        
        # Forward to n8n
        return self.forward_to_n8n(processed_response)
    
    def _save_local_files(self, processed_response: Union[Dict, List[Dict]]) -> None:
        """
        Save processed response to local files for debugging and reference.
        
        Args:
            processed_response: The processed response to save
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = Path(self.output_dir) / "processed"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save as JSON file
            output_path = output_dir / f"processed_response_{timestamp}.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_response, f, indent=2)
            
            logger.info(f"Saved processed response to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving processed response: {e}")


# Example usage in a webhook handler
def process_webhook(request_data: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """
    Process a webhook request and return the processed response.
    
    Args:
        request_data: The data from the webhook request
        
    Returns:
        Union[Dict, List[Dict]]: The processed response
    """
    processor = WebhookProcessor()
    processed_response = processor.process_webhook_response(request_data)
    
    # Optionally forward to n8n
    if processor.n8n_webhook_url:
        processor.forward_to_n8n(processed_response)
    
    return processed_response 