"""Tests for fix engine and position preservation."""

from markdown_doctor.doctor import Doctor


def test_multiple_fixes_on_different_lines() -> None:
    text = """# Title

Line with trailing spaces   
Another trailing line  
Image without alt: ![](/images/diagram.png)

```bash
echo "unclosed code block"
"""
    doctor = Doctor()
    fixed_text, result = doctor.fix_text(text)
    assert result.fixed_count >= 4
    # Code fence closed
    assert fixed_text.endswith("```\n") or fixed_text.endswith("```")
    # Trailing spaces removed
    assert "Line with trailing spaces\n" in fixed_text
    # Image alt added
    assert "![Diagram](/images/diagram.png)" in fixed_text
