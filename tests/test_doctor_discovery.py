"""Tests for Doctor file discovery, exclusions, and custom rules."""

from pathlib import Path
from markdown_doctor.config import DoctorConfig
from markdown_doctor.doctor import Doctor
from markdown_doctor.rules.trailing_whitespace import TrailingWhitespaceRule


def test_doctor_file_discovery_and_exclusions(tmp_path: Path):
    sub = tmp_path / "docs"
    sub.mkdir()
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    f1 = sub / "doc1.md"
    f1.write_text("# Doc 1\n", encoding="utf-8")
    f2 = sub / "doc2.markdown"
    f2.write_text("# Doc 2\n", encoding="utf-8")
    ignored = git_dir / "ignored.md"
    ignored.write_text("# Ignored\n", encoding="utf-8")

    doctor = Doctor()
    discovered = doctor.discover_files([tmp_path])
    assert f1.resolve() in discovered
    assert f2.resolve() in discovered
    assert ignored.resolve() not in discovered


def test_doctor_custom_rules():
    custom_rule = TrailingWhitespaceRule(allow_hard_breaks=True)
    doctor = Doctor(rules=[custom_rule])
    assert len(doctor.rules) == 1
    assert doctor.rules[0] is custom_rule

    # Verify clean text check returns no issues
    res = doctor.check_text("# Clean\n")
    assert res.is_clean


def test_doctor_fix_clean_text():
    doctor = Doctor()
    text = "# Clean Content\n\nNo issues here.\n"
    fixed, res = doctor.fix_text(text)
    assert fixed == text
    assert res.is_clean
    assert res.fixed_count == 0


def test_doctor_check_unreadable_file(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist.md"
    doctor = Doctor()
    res = doctor.check_file(non_existent)
    assert not res.is_clean
    assert res.issues[0].rule_id == "read-error"
