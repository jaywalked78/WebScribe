import pytest

from app.services.parser import HTMLParserService


def test_simple_paragraph():
    html = "<html><body><article><p>Hello world.</p></article></body></html>"
    md, meta = HTMLParserService().parse(html)
    assert "Hello world." in md
    assert meta.title is None 