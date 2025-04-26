import re

_whitespace_re = re.compile(r"\s+")


def clean_text(text: str) -> str:  # noqa: D401
    """Collapse repeated whitespace and strip leading/trailing."""
    return _whitespace_re.sub(" ", text).strip() 