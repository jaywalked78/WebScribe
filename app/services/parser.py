from __future__ import annotations

import logging
import re
from typing import Tuple, Optional

import requests
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from ..models.output import ArticleMetadata
from ..utils.cleaners import clean_text
from ..utils.extractors import extract_metadata, detect_main_content
from .markdown import MarkdownService
from ..config import settings

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)

_HEADERS = {
    "User-Agent": "ScientificHTMLParser/1.0 (+https://example.com)"
}


class HTMLParserService:
    """High-level service that orchestrates HTML fetching, parsing, and metadata extraction."""

    def __init__(self) -> None:
        self._md_service = MarkdownService()

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def fetch(self, url: str) -> str:
        """Fetch HTML content from URL with limits and timeouts.

        Raises:
            RuntimeError: If the response status is not 200 or the payload exceeds MAX_CONTENT_SIZE.
        """
        logger.info("Fetching URL %s", url)
        print(f"Fetching URL: {url}")  # Console debug
        try:
            resp = requests.get(
                url,
                headers=_HEADERS,
                timeout=settings.TIMEOUT_SECONDS,
                stream=True,
            )
            resp.raise_for_status()

            content = resp.content
            print(f"Content received: {len(content)} bytes")  # Console debug
            if len(content) > settings.MAX_CONTENT_SIZE:
                raise RuntimeError("Content size exceeds limit")
            return content.decode(resp.apparent_encoding or "utf-8", errors="replace")
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching %s: %s", url, exc)
            print(f"Error fetching {url}: {exc}")  # Console debug
            raise

    def parse(self, html: str, source_url: Optional[str] = None) -> Tuple[str, ArticleMetadata]:
        """Parse raw HTML into markdown and metadata."""
        print(f"Parsing HTML, length: {len(html)} chars")  # Console debug

        soup = BeautifulSoup(html, "html5lib")

        # Clean unwanted elements first
        self._strip_unwanted(soup)

        # Detect main content
        article_node = detect_main_content(soup)
        print(f"Main content detected: {article_node.name} element")  # Console debug

        # Extract metadata
        metadata = extract_metadata(soup, article_node, source_url)
        print(f"Metadata extracted: {metadata.title}")  # Console debug

        # Convert main content to markdown
        markdown_content = self._md_service.convert(article_node)
        print(f"Markdown conversion complete, length: {len(markdown_content)} chars")  # Console debug

        return markdown_content, metadata

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    @staticmethod
    def _strip_unwanted(soup: BeautifulSoup) -> None:
        """Remove elements that should not appear in the final output."""

        selectors = [
            "header",
            "footer",
            "nav",
            "aside",
            "script",
            "style",
            "noscript",
            "iframe",
            "form",
        ]
        for sel in selectors:
            for tag in soup.select(sel):
                tag.decompose()

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Remove empty tags
        for tag in soup.find_all():
            if not tag.text.strip() and not tag.name == "img":
                tag.decompose()

        # Normalize whitespace in text nodes
        for text_node in soup.find_all(string=True):
            if isinstance(text_node, NavigableString):
                cleaned = clean_text(str(text_node))
                text_node.replace_with(cleaned) 