from __future__ import annotations

import logging
from typing import Optional

from bs4 import BeautifulSoup, Tag

from ..models.output import ArticleMetadata

logger = logging.getLogger(__name__)


def detect_main_content(soup: BeautifulSoup) -> Tag:
    """Attempt to find the main article content node."""

    # Try <article>
    article_tag = soup.find("article")
    if article_tag:
        return article_tag

    # Heuristics: find the longest <div> or <section> with many <p>
    candidate = max(
        soup.find_all(["div", "section"], recursive=True),
        key=lambda t: len(t.get_text(strip=True)),
        default=soup.body or soup,
    )
    return candidate


def extract_metadata(soup: BeautifulSoup, content_node: Tag, source_url: Optional[str] = None) -> ArticleMetadata:  # noqa: D401
    """Extract scientific article metadata."""

    # Title
    title_tag = soup.find("meta", attrs={"name": "citation_title"}) or soup.find("title")
    title = title_tag.get("content") if title_tag and title_tag.name == "meta" else title_tag.text if title_tag else None

    # Authors
    authors_meta = soup.find_all("meta", attrs={"name": "citation_author"})
    authors = [m.get("content") for m in authors_meta if m.get("content")] or None

    # Publication date
    pub_date_meta = soup.find("meta", attrs={"name": "citation_publication_date"})
    publication_date = pub_date_meta.get("content") if pub_date_meta else None

    # Journal
    journal_meta = soup.find("meta", attrs={"name": "citation_journal_title"})
    journal = journal_meta.get("content") if journal_meta else None

    # DOI
    doi_meta = soup.find("meta", attrs={"name": "citation_doi"})
    doi = doi_meta.get("content") if doi_meta else None

    # Abstract
    abstract_meta = soup.find("meta", attrs={"name": "description"})
    abstract = abstract_meta.get("content") if abstract_meta else None

    metadata = ArticleMetadata(
        title=title,
        authors=authors,
        publication_date=publication_date,
        journal=journal,
        doi=doi,
        abstract=abstract,
    )

    return metadata 