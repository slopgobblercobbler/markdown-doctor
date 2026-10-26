"""Tests for trailing whitespace validation and repairs."""

from markdown_doctor.doctor import Doctor
from markdown_doctor.document import MarkdownDocument
from markdown_doctor.rules.trailing_whitespace import TrailingWhitespaceRule


def test_trailing_whitespace_detected_and_fixed() -> None:
    text = "Line 1   \nLine 2\t\nLine 3\n"
    doctor = Doctor()
    fixed_text, result = doctor.fix_text(text)
    assert result.fixed_count == 2
    assert fixed_text == "Line 1\nLine 2\nLine 3\n"


def test_allow_hard_breaks() -> None:
    text = "First line with hard break  \nSecond line\n"
    rule_strict = TrailingWhitespaceRule(allow_hard_breaks=False)
    doc = MarkdownDocument.from_text(text)
    assert len(rule_strict.check(doc)) == 1

    rule_lenient = TrailingWhitespaceRule(allow_hard_breaks=True)
    assert len(rule_lenient.check(doc)) == 0

    # 3 spaces should still be flagged even with allow_hard_breaks
    text_three_spaces = "First line with three spaces   \nSecond line\n"
    doc_three = MarkdownDocument.from_text(text_three_spaces)
    assert len(rule_lenient.check(doc_three)) == 1
