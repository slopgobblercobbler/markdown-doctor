"""Tests for frontmatter YAML validation and repairs."""

from markdown_doctor.doctor import Doctor
from markdown_doctor.document import MarkdownDocument
from markdown_doctor.rules.frontmatter import FrontmatterRule


def test_valid_frontmatter() -> None:
    text = """---
title: Production Doc
version: 1.0.0
draft: false
---

# Title
"""
    doc = MarkdownDocument.from_text(text)
    rule = FrontmatterRule()
    issues = rule.check(doc)
    assert len(issues) == 0


def test_unclosed_frontmatter_fixed() -> None:
    text = """---
title: Unclosed Document
tags: [a, b]
"""
    doctor = Doctor()
    fixed_text, result = doctor.fix_text(text)
    assert result.fixed_count == 1
    assert "---" in fixed_text.splitlines()[-1]


def test_invalid_yaml_syntax() -> None:
    text = """---
title: [unclosed list
invalid: ::::
---

# Title
"""
    doc = MarkdownDocument.from_text(text)
    rule = FrontmatterRule()
    issues = rule.check(doc)
    assert len(issues) == 1
    assert "invalid-frontmatter" in issues[0].rule_id
    assert issues[0].fixable is False


def test_frontmatter_delimiter_whitespace_fixed() -> None:
    text = """---   
title: Trailing spaces on delimiter
---   

# Title
"""
    doctor = Doctor()
    fixed_text, result = doctor.fix_text(text)
    assert result.fixed_count == 2
    assert fixed_text.startswith("---\ntitle:")


def test_frontmatter_malformed_delimiter() -> None:
    text = """----
title: Bad Delimiter
---

# Title
"""
    doctor = Doctor()
    fixed_text, result = doctor.fix_text(text)
    assert result.fixed_count == 1
    assert fixed_text.startswith("---\ntitle:")
