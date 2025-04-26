from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict

import requests

from ..config import settings
from ..models.output import ParseResponse

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)


class WebhookService:
    """Deliver payloads to configured webhook URL with retries and HMAC signature."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _compute_signature(self, payload: str) -> str:
        secret = (settings.WEBHOOK_SECRET or "").encode()
        return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()

    def deliver(self, response: ParseResponse) -> None:  # noqa: D401
        if not settings.WEBHOOK_URL:
            logger.debug("Webhook URL not configured, skipping delivery")
            return

        payload_str = response.json()
        signature = self._compute_signature(payload_str)

        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature,
            "User-Agent": "ScientificHTMLParserWebhook/1.0",
        }

        delay = 1.0
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info("Sending webhook attempt %s to %s", attempt, settings.WEBHOOK_URL)
                resp = requests.post(
                    settings.WEBHOOK_URL,
                    data=payload_str,
                    headers=headers,
                    timeout=settings.TIMEOUT_SECONDS,
                )
                if resp.status_code // 100 == 2:
                    logger.info("Webhook delivered successfully")
                    return
                raise RuntimeError(f"Received status {resp.status_code}")
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Webhook attempt %s failed: %s", attempt, exc)
                if attempt == self.max_retries:
                    logger.error("Max retries reached, giving up")
                    return
                time.sleep(delay)
                delay *= self.backoff_factor 