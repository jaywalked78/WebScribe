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

        # Handle headings with explicit formatting
        if node.name in self.heading_map:
            heading_text = node.get_text(strip=True)
            return f"{self.heading_map[node.name]}{heading_text}"
        
        # Handle paragraphs and divs
        if node.name in {"p", "div"}:
            # Process child elements to preserve nested structure
            inner_text = []
            for child in node.children:
                inner_text.append(self._convert_node(child))
            return " ".join(text for text in inner_text if text.strip())
        
        # Handle lists
        if node.name in {"ul", "ol"}:
            return self._convert_list(node)
        
        # Handle list items
        if node.name == "li":
            # Process child elements to preserve nested items
            inner_text = []
            for child in node.children:
                inner_text.append(self._convert_node(child))
            return f"- {' '.join(text for text in inner_text if text.strip())}"
        
        # Handle images
        if node.name == "img":
            alt = node.get("alt", "")
            src = node.get("src", "")
            return f"![{alt}]({src})"
        
        # Handle links
        if node.name == "a":
            href = node.get("href", "#")
            text = node.get_text(strip=True)
            return f"[{text}]({href})"
        
        # Handle tables
        if node.name == "table":
            return self._convert_table(node)

        # Handle text formatting
        if node.name == "strong" or node.name == "b":
            return f"**{node.get_text(strip=True)}**"
        if node.name == "em" or node.name == "i":
            return f"*{node.get_text(strip=True)}*"
        if node.name == "code":
            return f"`{node.get_text(strip=True)}`"
        if node.name == "pre":
            return f"```\n{node.get_text(strip=False)}\n```"
        if node.name == "blockquote":
            lines = node.get_text(strip=True).split('\n')
            return '\n'.join(f"> {line}" for line in lines)

        # Recursively handle containers that might have headings/structures inside
        if node.find(list(self.heading_map.keys()), recursive=True):
            inner_parts = []
            for child in node.children:
                inner_parts.append(self._convert_node(child))
            return "\n\n".join(part for part in inner_parts if part)

        # Fallback to text
        return node.get_text(strip=True)

    def _convert_list(self, node: Tag) -> str:
        lines: list[str] = []
        ordered = node.name == "ol"
        
        for idx, li in enumerate(node.find_all("li", recursive=False), start=1):
            prefix = f"{idx}. " if ordered else "- "
            
            # Process child elements to handle nested lists
            inner_text = []
            for child in li.children:
                if isinstance(child, Tag) and child.name in {"ul", "ol"}:
                    # Handle nested lists with proper indentation
                    nested_list = self._convert_list(child)
                    inner_text.append("\n" + "\n".join("  " + line for line in nested_list.split("\n")))
                else:
                    inner_text.append(self._convert_node(child))
            
            lines.append(prefix + " ".join(text for text in inner_text if text.strip()))
        
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