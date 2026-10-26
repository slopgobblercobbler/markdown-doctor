"""Tests for image alt text validation and repairs."""

from markdown_doctor.doctor import Doctor
from markdown_doctor.document import MarkdownDocument
from markdown_doctor.rules.image_alt import MissingImageAltRule


def test_valid_image_alt() -> None:
    text = "![Application Architecture Diagram](assets/arch.png)"
    doc = MarkdownDocument.from_text(text)
    rule = MissingImageAltRule()
    issues = rule.check(doc)
    assert len(issues) == 0


def test_missing_image_alt_detected_and_fixed() -> None:
    text = "Check this diagram: ![](/path/to/system-architecture.png)"
    doctor = Doctor()
    fixed_text, result = doctor.fix_text(text)
    assert result.fixed_count == 1
    assert "![System architecture](/path/to/system-architecture.png)" in fixed_text

    # Recheck clean
    recheck = doctor.check_text(fixed_text)
    assert len(recheck.issues) == 0


def test_html_img_missing_alt_fixed() -> None:
    text = 'Look at this: <img src="images/database_schema.png">'
    doctor = Doctor()
    fixed_text, result = doctor.fix_text(text)
    assert result.fixed_count == 1
    assert 'alt="Database schema"' in fixed_text


def test_html_img_empty_alt_fixed() -> None:
    text = 'Look at this: <img src="flowchart.svg" alt="">'
    doctor = Doctor()
    fixed_text, result = doctor.fix_text(text)
    assert result.fixed_count == 1
    assert 'alt="Flowchart"' in fixed_text
