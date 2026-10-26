"""Tests for markdown parsing."""

from pathlib import Path
from markdown_doctor.document import MarkdownDocument


def test_parse_frontmatter_valid() -> None:
    text = """---
title: My Document
author: Alice
tags:
  - markdown
  - doctor
---

# Heading 1
Some body text.
"""
    doc = MarkdownDocument.from_text(text)
    assert doc.frontmatter is not None
    assert doc.frontmatter.is_closed is True
    assert doc.frontmatter.is_valid is True
    assert doc.frontmatter.data["title"] == "My Document"
    assert doc.frontmatter.data["author"] == "Alice"
    assert doc.frontmatter.data["tags"] == ["markdown", "doctor"]


def test_parse_frontmatter_unclosed() -> None:
    text = """---
title: Unclosed
author: Bob
# Heading
"""
    doc = MarkdownDocument.from_text(text)
    assert doc.frontmatter is not None
    assert doc.frontmatter.is_closed is False
    assert doc.frontmatter.is_valid is False


def test_parse_code_fences() -> None:
    text = """# Code example

```python
def hello():
    print("world")
```

~~~bash
echo "test"
~~~

```markdown
Unclosed block
"""
    doc = MarkdownDocument.from_text(text)
    assert len(doc.code_fences) == 3
    # 1st fence
    assert doc.code_fences[0].fence_char == "`"
    assert doc.code_fences[0].language == "python"
    assert doc.code_fences[0].is_closed is True
    # 2nd fence
    assert doc.code_fences[1].fence_char == "~"
    assert doc.code_fences[1].language == "bash"
    assert doc.code_fences[1].is_closed is True
    # 3rd fence
    assert doc.code_fences[2].is_closed is False
    assert doc.code_fences[2].language == "markdown"


def test_parse_headings_atx_and_setext() -> None:
    text = """# Main Title

## Section A

### Subsection A.1

Section B
=========

Subsection B.1
--------------
"""
    doc = MarkdownDocument.from_text(text)
    headings = doc.headings
    assert len(headings) == 5
    assert headings[0].level == 1
    assert headings[0].text == "Main Title"
    assert headings[0].slug == "main-title"

    assert headings[1].level == 2
    assert headings[1].text == "Section A"

    assert headings[2].level == 3
    assert headings[2].text == "Subsection A.1"

    # Setext H1
    assert headings[3].level == 1
    assert headings[3].text == "Section B"

    # Setext H2
    assert headings[4].level == 2
    assert headings[4].text == "Subsection B.1"


def test_parse_links_and_images() -> None:
    text = """Check [documentation](https://example.com/docs) and [local](#section).
Look at ![Architecture](./img/arch.png) and ![Missing alt](./img/empty.png).
<img src="logo.png" alt="Logo">
<a href="#custom">Anchor Link</a>
"""
    doc = MarkdownDocument.from_text(text)
    # Check links
    links = doc.links
    assert len(links) >= 5

    # Check images identified
    images = [l for l in links if l.is_image]
    assert len(images) == 3
    assert images[0].text == "Architecture"
    assert images[1].text == "Missing alt"
    assert images[2].text == "Logo"
