"""Tests for empty link detection."""

from markdown_doctor.document import MarkdownDocument
from markdown_doctor.rules.empty_links import EmptyLinkUrlRule


def test_empty_link_detection() -> None:
    text = """# Links

Valid link: [Google](https://google.com)
Empty URL: [Click Here]()
Hash Only: [Skip Link](#)
"""
    doc = MarkdownDocument.from_text(text)
    rule = EmptyLinkUrlRule()
    issues = rule.check(doc)
    assert len(issues) == 2
    assert "Click Here" in issues[0].message
    assert "Skip Link" in issues[1].message
