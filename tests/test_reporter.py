"""Tests for Reporter output formatting."""

import io
from pathlib import Path
from markdown_doctor.models import CheckResult, DoctorReport, Issue, Severity
from markdown_doctor.reporter import Reporter


def test_reporter_plain_text_clean():
    stream = io.StringIO()
    reporter = Reporter(stream=stream, format_type="text")
    report = DoctorReport(results=[CheckResult(file_path=Path("doc.md"), issues=[])])
    reporter.render(report, is_fix_mode=False, dry_run=False)
    output = stream.getvalue()
    assert "Inspection" in output
    assert "All clean!" in output


def test_reporter_plain_text_with_issues():
    stream = io.StringIO()
    reporter = Reporter(stream=stream, format_type="text")
    issue = Issue(
        rule_id="broken-anchor-link",
        message="Anchor not found",
        file_path=Path("doc.md"),
        line=10,
        column=5,
        severity=Severity.ERROR,
        fixable=True,
        context="[test](#bad)",
    )
    res = CheckResult(file_path=Path("doc.md"), issues=[issue], fixed_count=2)
    report = DoctorReport(results=[res])
    reporter.render(report, is_fix_mode=True, dry_run=True)
    output = stream.getvalue()
    assert "(dry-run)" in output
    assert "Would fix 2 issue(s)" in output
    assert "line 10:5" in output
    assert "broken-anchor-link" in output
    assert "[autofixable]" in output
    assert "Applied 2 automated fix(es)" in output


def test_reporter_compact_format():
    stream = io.StringIO()
    reporter = Reporter(stream=stream, format_type="compact")
    issue = Issue(
        rule_id="test-rule",
        message="Something wrong",
        file_path=Path("sample.md"),
        line=3,
        column=1,
        severity=Severity.WARNING,
    )
    report = DoctorReport(results=[CheckResult(file_path=Path("sample.md"), issues=[issue])])
    reporter.render(report)
    output = stream.getvalue()
    assert "sample.md:3:1: WARNING: Something wrong [test-rule]" in output


def test_reporter_empty_report():
    stream = io.StringIO()
    reporter = Reporter(stream=stream, format_type="text")
    report = DoctorReport(results=[])
    reporter.render(report)
    output = stream.getvalue()
    assert "No markdown documents discovered" in output


def test_reporter_plain_renderer_directly():
    stream = io.StringIO()
    reporter = Reporter(stream=stream, format_type="text")
    reporter.console = None  # Force plain renderer
    issue = Issue(
        rule_id="test-rule",
        message="A plain issue",
        file_path=Path("plain.md"),
        line=1,
        column=1,
        severity=Severity.ERROR,
        fixable=True,
        context="some context",
    )
    res = CheckResult(file_path=Path("plain.md"), issues=[issue], fixed_count=1)
    report = DoctorReport(results=[res])
    reporter.render(report, is_fix_mode=True, dry_run=False)
    output = stream.getvalue()
    assert "plain.md" in output
    assert "Fixed 1 issue(s)" in output
    assert "A plain issue" in output
    assert "some context" in output
    assert "Applied 1 automated fix(es)" in output

