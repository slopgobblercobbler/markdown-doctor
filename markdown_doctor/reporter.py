"""Diagnostic reporting and output formatters for markdown-doctor."""

from __future__ import annotations

import json
import sys
from typing import TextIO

from markdown_doctor.models import DoctorReport, Severity

try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False


def _get_status_symbols(stream: TextIO) -> tuple[str, str]:
    """Return encoding-safe check and cross symbols for the current terminal stream."""
    encoding = getattr(stream, "encoding", "utf-8") or "utf-8"
    try:
        "✓✗".encode(encoding)
        return "✓", "✗"
    except Exception:
        return "[PASS]", "[FAIL]"


class Reporter:
    """Formats and prints markdown diagnostic reports."""

    def __init__(self, stream: TextIO = sys.stdout, format_type: str = "text") -> None:
        self.stream = stream
        self.format_type = format_type
        self.check_sym, self.cross_sym = _get_status_symbols(stream)
        if _HAS_RICH:
            self.console = Console(file=stream, highlight=False, legacy_windows=False)
        else:
            self.console = None

    def render(self, report: DoctorReport, is_fix_mode: bool = False, dry_run: bool = False) -> None:
        """Render report to configured stream."""
        if self.format_type == "json":
            self._render_json(report, is_fix_mode, dry_run)
        elif self.format_type == "github":
            self._render_github_actions(report)
        elif self.format_type == "compact":
            self._render_compact(report)
        else:
            self._render_text(report, is_fix_mode, dry_run)

    def _render_json(self, report: DoctorReport, is_fix_mode: bool, dry_run: bool) -> None:
        payload = {
            "summary": {
                "total_files": report.total_files,
                "clean_files": report.clean_files,
                "total_issues": report.total_issues,
                "total_fixed": report.total_fixed,
                "errors": report.total_errors,
                "warnings": report.total_warnings,
                "is_clean": report.is_clean,
                "fix_mode": is_fix_mode,
                "dry_run": dry_run,
            },
            "files": [
                {
                    "file": str(res.file_path),
                    "is_clean": res.is_clean,
                    "fixed_count": res.fixed_count,
                    "issues": [issue.as_dict() for issue in res.issues],
                }
                for res in report.results
            ],
        }
        self.stream.write(json.dumps(payload, indent=2) + "\n")

    def _render_github_actions(self, report: DoctorReport) -> None:
        for res in report.results:
            for issue in res.issues:
                level = "error" if issue.severity == Severity.ERROR else "warning"
                line = issue.line
                col = issue.column
                msg = f"{issue.message} [{issue.rule_id}]"
                self.stream.write(
                    f"::{level} file={res.file_path},line={line},col={col}::{msg}\n"
                )

    def _render_compact(self, report: DoctorReport) -> None:
        for res in report.results:
            for issue in res.issues:
                sev = issue.severity.value.upper()
                self.stream.write(
                    f"{res.file_path}:{issue.line}:{issue.column}: {sev}: {issue.message} [{issue.rule_id}]\n"
                )

    def _render_text(self, report: DoctorReport, is_fix_mode: bool, dry_run: bool) -> None:
        if self.console and _HAS_RICH:
            self._render_text_rich(report, is_fix_mode, dry_run)
        else:
            self._render_text_plain(report, is_fix_mode, dry_run)

    def _render_text_rich(self, report: DoctorReport, is_fix_mode: bool, dry_run: bool) -> None:
        assert self.console is not None

        # Print header
        mode_str = " (dry-run)" if dry_run else ""
        action_name = "Autofix" if is_fix_mode else "Inspection"
        self.console.print(f"[bold cyan]markdown-doctor[/bold cyan] {action_name}{mode_str}")
        self.console.print("=" * 60)

        if not report.results:
            self.console.print("[yellow]No markdown documents discovered.[/yellow]")
            return

        for res in report.results:
            if res.is_clean and res.fixed_count == 0:
                continue

            self.console.print(f"\n[bold underline]{res.file_path}[/bold underline]")

            if res.fixed_count > 0:
                dry_prefix = "[DRY-RUN] Would fix" if dry_run else "Fixed"
                self.console.print(f"  [green]{self.check_sym} {dry_prefix} {res.fixed_count} issue(s)[/green]")

            for issue in res.issues:
                sev_color = "red" if issue.severity == Severity.ERROR else "yellow"
                fix_badge = " [green]\\[autofixable][/green]" if issue.fixable else ""
                self.console.print(
                    f"  line {issue.line}:{issue.column} - "
                    f"[{sev_color} bold]{issue.severity.value}[/{sev_color} bold] "
                    f"[dim]({issue.rule_id})[/dim]{fix_badge}: {issue.message}"
                )
                if issue.context:
                    self.console.print(f"    [dim]>[/dim] {issue.context.strip()}")

        self.console.print("\n" + "=" * 60)
        # Summary
        if report.is_clean:
            self.console.print(
                f"[bold green]{self.check_sym} All clean![/bold green] Scanned {report.total_files} file(s) with 0 remaining issues."
            )
            if report.total_fixed > 0:
                self.console.print(f"[green]Applied {report.total_fixed} automated fix(es).[/green]")
        else:
            self.console.print(
                f"[bold red]{self.cross_sym} Found {report.total_issues} issue(s)[/bold red] "
                f"({report.total_errors} errors, {report.total_warnings} warnings) "
                f"across {report.total_files} file(s)."
            )
            if report.total_fixed > 0:
                self.console.print(f"[green]Applied {report.total_fixed} automated fix(es).[/green]")

    def _render_text_plain(self, report: DoctorReport, is_fix_mode: bool, dry_run: bool) -> None:
        mode_str = " (dry-run)" if dry_run else ""
        action_name = "Autofix" if is_fix_mode else "Inspection"
        self.stream.write(f"markdown-doctor {action_name}{mode_str}\n")
        self.stream.write("=" * 60 + "\n")

        if not report.results:
            self.stream.write("No markdown documents discovered.\n")
            return

        for res in report.results:
            if res.is_clean and res.fixed_count == 0:
                continue

            self.stream.write(f"\n{res.file_path}\n")
            if res.fixed_count > 0:
                dry_prefix = "[DRY-RUN] Would fix" if dry_run else "Fixed"
                self.stream.write(f"  ✓ {dry_prefix} {res.fixed_count} issue(s)\n")

            for issue in res.issues:
                fix_badge = " [autofixable]" if issue.fixable else ""
                self.stream.write(
                    f"  line {issue.line}:{issue.column} - {issue.severity.value.upper()} "
                    f"({issue.rule_id}){fix_badge}: {issue.message}\n"
                )
                if issue.context:
                    self.stream.write(f"    > {issue.context.strip()}\n")

        self.stream.write("\n" + "=" * 60 + "\n")
        if report.is_clean:
            self.stream.write(
                f"✓ All clean! Scanned {report.total_files} file(s) with 0 remaining issues.\n"
            )
            if report.total_fixed > 0:
                self.stream.write(f"Applied {report.total_fixed} automated fix(es).\n")
        else:
            self.stream.write(
                f"✗ Found {report.total_issues} issue(s) "
                f"({report.total_errors} errors, {report.total_warnings} warnings) "
                f"across {report.total_files} file(s).\n"
            )
            if report.total_fixed > 0:
                self.stream.write(f"Applied {report.total_fixed} automated fix(es).\n")
