#!/usr/bin/env python3
"""
Webhook Processor Integration

This script demonstrates how to integrate the webhook_processor.py with the 
existing webhook_v3.py to preprocess YAML before it reaches n8n.

This integration sits between webhook_v3.py's output and n8n.
"""

import os
import json
import logging
from typing import Dict, List, Any, Union

from ..config import settings
from .webhook_processor import WebhookProcessor

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)

# Flag to enable/disable YAML preprocessing
ENABLE_YAML_PREPROCESSING = os.environ.get("ENABLE_YAML_PREPROCESSING", "true").lower() in ("true", "1", "yes")

class WebhookIntegration:
    """
    A wrapper around the webhook_v3 WebhookService that integrates YAML preprocessing.
    This class demonstrates how to integrate the webhook_processor with webhook_v3.
    """
    
    def __init__(self, webhook_service):
        """
        Initialize the integration with the original webhook service.
        
        Args:
            webhook_service: The original webhook_v3 WebhookService instance
        """
        self.webhook_service = webhook_service
        self.webhook_processor = WebhookProcessor() if ENABLE_YAML_PREPROCESSING else None
    
    def deliver(self, payload) -> bool:
        """
        Process the payload with YAML preprocessing and then deliver.
        
        Args:
            payload: The payload to process and deliver
            
        Returns:
            bool: True if delivery was successful, False otherwise
        """
        try:
            if not ENABLE_YAML_PREPROCESSING or self.webhook_processor is None:
                # If preprocessing is disabled, just pass through to the original service
                return self.webhook_service.deliver(payload)
            
            # Convert payload to dict if it's not already
            payload_dict = payload.dict() if hasattr(payload, 'dict') and callable(getattr(payload, 'dict')) else payload
            
            # Process the payload with YAML preprocessing
            processed_payload = self.webhook_processor.process_webhook_response(payload_dict)
            
            # Forward to n8n if configured
            if self.webhook_processor.n8n_webhook_url:
                return self.webhook_processor.forward_to_n8n(processed_payload)
            else:
                # If no n8n webhook URL is configured, fall back to the original delivery
                logger.info("N8N_WEBHOOK_URL not configured, falling back to original delivery method")
                return self.webhook_service.deliver(payload)
            
        except Exception as e:
            logger.error(f"Error in integrated delivery: {e}")
            # Attempt to deliver with the original service as a fallback
            return self.webhook_service.deliver(payload)


def integrate_with_webhook_v3():
    """
    How to integrate with webhook_v3.py:
    
    1. In webhook_v3.py, import the WebhookIntegration class:
       from .webhook_processor_integration import WebhookIntegration, ENABLE_YAML_PREPROCESSING
    
    2. After creating the WebhookService instance, wrap it with WebhookIntegration:
       
       # Original code
       webhook_service = WebhookService()
       
       # Add this code
       if ENABLE_YAML_PREPROCESSING:
           webhook_service = WebhookIntegration(webhook_service)
    
    3. The rest of the code can remain unchanged, as the WebhookIntegration
       class provides the same interface as WebhookService.
    """
    pass


# Example manual integration
if __name__ == "__main__":
    # This is an example of how to manually integrate with an existing webhook_v3 instance
    from .webhook_v3 import WebhookService
    
    # Create the original webhook service
    webhook_service = WebhookService()
    
    # Wrap it with our integration
    integrated_service = WebhookIntegration(webhook_service)
    
    # Use the integrated service instead of the original
    # For example, in test_webhook_v3.py, you would replace:
    # webhook.deliver(response1)
    # with:
    # integrated_service.deliver(response1) 