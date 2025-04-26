from __future__ import annotations

import logging
from bs4 import Tag, NavigableString, BeautifulSoup

logger = logging.getLogger(__name__)


class MarkdownService:
    """Convert BeautifulSoup node into Markdown text."""

    heading_map = {
        "h1": "# ",
        "h2": "## ",
        "h3": "### ",
        "h4": "#### ",
        "h5": "##### ",
        "h6": "###### ",
    }

    def convert(self, node: Tag) -> str:  # noqa: D401
        """Traverse and convert node to markdown."""
        parts: list[str] = []
        for child in node.children:
            parts.append(self._convert_node(child))
        return "\n\n".join(part for part in parts if part)

    def _convert_node(self, node) -> str:  # noqa: ANN001
        if isinstance(node, NavigableString):
            return str(node).strip()
        if not isinstance(node, Tag):
            return ""

        if node.name in self.heading_map:
            return f"{self.heading_map[node.name]}{node.get_text(strip=True)}"
        if node.name in {"p", "div"}:
            return node.get_text(strip=True)
        if node.name in {"ul", "ol"}:
            return self._convert_list(node)
        if node.name == "li":
            return f"- {node.get_text(strip=True)}"
        if node.name == "img":
            alt = node.get("alt", "")
            src = node.get("src", "")
            return f"![{alt}]({src})"
        if node.name == "a":
            href = node.get("href", "#")
            text = node.get_text(strip=True)
            return f"[{text}]({href})"
        if node.name == "table":
            return self._convert_table(node)

        # Fallback to text
        return node.get_text(strip=True)

    def _convert_list(self, node: Tag) -> str:
        lines: list[str] = []
        ordered = node.name == "ol"
        for idx, li in enumerate(node.find_all("li", recursive=False), start=1):
            prefix = f"{idx}. " if ordered else "- "
            lines.append(prefix + li.get_text(strip=True))
        return "\n".join(lines)

    def _convert_table(self, node: Tag) -> str:
        rows = node.find_all("tr")
        if not rows:
            return ""

        def cell_text(cell):
            return cell.get_text(strip=True)

        header_cells = rows[0].find_all(["th", "td"])
        header = " | ".join(cell_text(c) for c in header_cells)
        separator = " | ".join(["---" for _ in header_cells])
        lines = [f"| {header} |", f"| {separator} |"]

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            lines.append("| " + " | ".join(cell_text(c) for c in cells) + " |")
        return "\n".join(lines) 