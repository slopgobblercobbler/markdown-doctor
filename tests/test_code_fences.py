"""Tests for code fence validation and repairs."""

from markdown_doctor.document import MarkdownDocument
from markdown_doctor.doctor import Doctor
from markdown_doctor.rules.code_fences import UnclosedCodeFenceRule


def test_closed_code_fence() -> None:
    text = """# Example

```python
x = 10
```

End of doc.
"""
    doc = MarkdownDocument.from_text(text)
    rule = UnclosedCodeFenceRule()
    issues = rule.check(doc)
    assert len(issues) == 0


def test_unclosed_code_fence_detected_and_fixed() -> None:
    text = """# Example

```python
print("hello world")
"""
    doctor = Doctor()
    fixed_text, result = doctor.fix_text(text)
    assert result.fixed_count == 1
    assert "```" in fixed_text.splitlines()[-1]

    # Verify newly fixed text produces 0 issues
    recheck = doctor.check_text(fixed_text)
    assert len(recheck.issues) == 0


def test_tilde_code_fence_autofix() -> None:
    text = """# Tilde Block

~~~bash
echo "test"
"""
    doctor = Doctor()
    fixed_text, result = doctor.fix_text(text)
    assert result.fixed_count == 1
    assert "~~~" in fixed_text.splitlines()[-1]
