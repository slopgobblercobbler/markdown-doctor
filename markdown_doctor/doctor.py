"""Core linter and fixer engine for markdown-doctor."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import List, Optional, Tuple

from markdown_doctor.config import DoctorConfig
from markdown_doctor.document import MarkdownDocument
from markdown_doctor.fixer import MarkdownFixer
from markdown_doctor.models import CheckResult, DoctorReport, Issue
from markdown_doctor.rules import get_default_rules
from markdown_doctor.rules.base import BaseRule
from markdown_doctor.rules.image_alt import MissingImageAltRule
from markdown_doctor.rules.trailing_whitespace import TrailingWhitespaceRule


class Doctor:
    """Markdown health checker and autofix engine."""

    def __init__(
        self,
        config: Optional[DoctorConfig] = None,
        rules: Optional[List[BaseRule]] = None,
    ) -> None:
        self.config = config or DoctorConfig()

        if rules is not None:
            self.rules = rules
        else:
            base_rules = get_default_rules()
            # Configure rule instances according to config options
            for r in base_rules:
                if isinstance(r, TrailingWhitespaceRule):
                    r.allow_hard_breaks = self.config.allow_hard_breaks
                elif isinstance(r, MissingImageAltRule):
                    r.default_alt_prefix = self.config.default_alt_prefix

            # Filter rules enabled by config
            self.rules = [r for r in base_rules if self.config.is_rule_enabled(r.rule_id)]

    def check_text(self, text: str, file_path: Optional[Path] = None) -> CheckResult:
        """Run all active rules on an in-memory markdown string."""
        path = file_path or Path("untitled.md")
        doc = MarkdownDocument.from_text(text, path)
        issues: List[Issue] = []

        for rule in self.rules:
            detected = rule.check(doc)
            issues.extend(detected)

        return CheckResult(file_path=path, issues=issues)

    def fix_text(self, text: str, file_path: Optional[Path] = None) -> Tuple[str, CheckResult]:
        """Check and autofix in-memory markdown string."""
        initial_result = self.check_text(text, file_path)
        if not initial_result.issues:
            return text, initial_result

        fixed_content, count = MarkdownFixer.apply_fixes(text, initial_result.issues)

        # Re-check to report remaining issues after fix
        final_result = self.check_text(fixed_content, file_path)
        final_result.fixed_count = count
        return fixed_content, final_result

    def check_file(self, file_path: Path) -> CheckResult:
        """Inspect a file on disk."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            return self.check_text(content, file_path)
        except Exception as exc:
            from markdown_doctor.models import Severity

            issue = Issue(
                rule_id="read-error",
                message=f"Failed to read file: {exc}",
                file_path=file_path,
                line=1,
                column=1,
                severity=Severity.ERROR,
            )
            return CheckResult(file_path=file_path, issues=[issue])

    def fix_file(self, file_path: Path, dry_run: bool = False) -> Tuple[str, CheckResult]:
        """Check and apply fixes to a file on disk."""
        content = file_path.read_text(encoding="utf-8", errors="replace")
        fixed_content, result = self.fix_text(content, file_path)

        if not dry_run and result.fixed_count > 0:
            file_path.write_text(fixed_content, encoding="utf-8")

        return fixed_content, result

    def discover_files(self, targets: List[Path]) -> List[Path]:
        """Find all markdown files matching targets while respecting exclude patterns."""
        discovered: List[Path] = []

        for target in targets:
            if target.is_file():
                if not self._is_excluded(target):
                    discovered.append(target.resolve())
            elif target.is_dir():
                for ext in ("*.md", "*.markdown"):
                    for file_path in target.rglob(ext):
                        if not self._is_excluded(file_path):
                            discovered.append(file_path.resolve())

        # Sort and remove duplicates
        unique_paths = sorted(set(discovered), key=lambda p: str(p))
        return unique_paths

    def _is_excluded(self, path: Path) -> bool:
        """Check if path matches any configured exclude pattern."""
        parts = path.parts
        for exclude in self.config.excludes:
            # Check against directory parts
            if exclude in parts:
                return True
            # Check against relative path glob
            if fnmatch.fnmatch(str(path), exclude) or fnmatch.fnmatch(path.name, exclude):
                return True
        return False

    def run_check(self, targets: List[Path]) -> DoctorReport:
        """Check all discovered files and aggregate diagnostic report."""
        files = self.discover_files(targets)
        report = DoctorReport()

        for file_path in files:
            res = self.check_file(file_path)
            report.results.append(res)

        return report

    def run_fix(self, targets: List[Path], dry_run: bool = False) -> DoctorReport:
        """Fix all discovered files and return report of applied and remaining issues."""
        files = self.discover_files(targets)
        report = DoctorReport()

        for file_path in files:
            _, res = self.fix_file(file_path, dry_run=dry_run)
            report.results.append(res)

        return report
