"""Tests for anchor and relative link validation."""

from pathlib import Path
import pytest
from markdown_doctor.doctor import Doctor
from markdown_doctor.document import MarkdownDocument
from markdown_doctor.rules.anchors import BrokenAnchorRule


def test_valid_internal_anchors() -> None:
    text = """# Getting Started

Go to [Installation](#installation) or [Usage](#usage).

## Installation
Step 1...

## Usage
Run tool...
"""
    rule = BrokenAnchorRule()
    doc = MarkdownDocument.from_text(text)
    issues = rule.check(doc)
    assert len(issues) == 0


def test_broken_internal_anchor_with_fuzzy_match() -> None:
    text = """# Getting Started

Read [install](#instalation).

## Installation
Content here.
"""
    rule = BrokenAnchorRule()
    doc = MarkdownDocument.from_text(text)
    issues = rule.check(doc)
    assert len(issues) == 1
    issue = issues[0]
    assert issue.rule_id == "broken-anchor-link"
    assert "Did you mean '#installation'?" in issue.message
    assert issue.fixable is True
    assert issue.fix is not None
    assert issue.fix.replacement == "[install](#installation)"


def test_custom_html_anchors() -> None:
    text = """# Header

Jump to <a id="deep-dive"></a> or [dive here](#deep-dive).
"""
    rule = BrokenAnchorRule()
    doc = MarkdownDocument.from_text(text)
    issues = rule.check(doc)
    assert len(issues) == 0


def test_relative_file_link(tmp_path: Path) -> None:
    file1 = tmp_path / "index.md"
    file2 = tmp_path / "guide.md"
    file2.write_text("# Guide\n\n## Advanced Tips\nCool tips.\n", encoding="utf-8")

    file1.write_text(
        """# Index

See [Guide](guide.md) and [Tips](guide.md#advanced-tips).
Also see [Broken Link](missing.md) and [Broken Cross-Anchor](guide.md#wrong-anchor).
""",
        encoding="utf-8",
    )

    doc = MarkdownDocument.from_file(file1)
    rule = BrokenAnchorRule()
    issues = rule.check(doc)

    rule_ids = [i.rule_id for i in issues]
    assert "broken-relative-link" in rule_ids
    assert "broken-relative-anchor" in rule_ids
    assert len(issues) == 2
