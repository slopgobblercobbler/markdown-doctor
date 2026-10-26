"""Command-line interface for markdown-doctor."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import List, Optional

from markdown_doctor import __version__
from markdown_doctor.config import DoctorConfig
from markdown_doctor.doctor import Doctor
from markdown_doctor.reporter import Reporter


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for markdown-doctor CLI."""
    parser = argparse.ArgumentParser(
        prog="markdown-doctor",
        description="Production-grade Markdown linter, anchor validator, and automated repair doctor.",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit.",
    )

    subparsers = parser.add_subparsers(dest="subcommand", title="subcommands")

    # Shared argument configuration helper
    def add_common_args(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "paths",
            nargs="*",
            default=["."],
            help="Files or directories to scan (default: current directory).",
        )
        p.add_argument(
            "--format",
            choices=["text", "json", "github", "compact"],
            default="text",
            help="Output report format (default: text).",
        )
        p.add_argument(
            "--config",
            type=Path,
            default=None,
            help="Path to custom configuration file (.markdown-doctor.toml or pyproject.toml).",
        )
        p.add_argument(
            "--rule",
            action="append",
            dest="rules",
            help="Explicitly enable rule(s) by ID (can be specified multiple times).",
        )
        p.add_argument(
            "--ignore-rule",
            action="append",
            dest="ignore_rules",
            help="Disable specific rule(s) by ID (can be specified multiple times).",
        )
        p.add_argument(
            "--allow-hard-breaks",
            action="store_true",
            help="Allow exactly 2 trailing spaces on lines (CommonMark hard breaks).",
        )
        p.add_argument(
            "--default-alt-prefix",
            default="",
            help="Optional prefix for auto-generated image alt text.",
        )

    # 1. Check subcommand
    check_parser = subparsers.add_parser(
        "check",
        help="Scan Markdown documents for errors and broken links.",
    )
    add_common_args(check_parser)
    check_parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically apply safe repairs to fixable issues.",
    )
    check_parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit with code 0 even if issues are detected.",
    )

    # 2. Lint subcommand (alias for check)
    lint_parser = subparsers.add_parser(
        "lint",
        help="Alias for 'check'. Scan Markdown documents for errors.",
    )
    add_common_args(lint_parser)
    lint_parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically apply safe repairs to fixable issues.",
    )
    lint_parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit with code 0 even if issues are detected.",
    )

    # 3. Fix subcommand
    fix_parser = subparsers.add_parser(
        "fix",
        help="Automatically repair broken anchors, unclosed code blocks, missing alt text, and formatting.",
    )
    add_common_args(fix_parser)
    fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show proposed changes without modifying files on disk.",
    )
    fix_parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit with code 0 even if remaining unfixable issues exist.",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for markdown-doctor CLI."""
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()

    # If no subcommand passed or paths directly passed, handle gracefully
    # e.g. `markdown-doctor README.md` or `markdown-doctor`
    known_commands = {"check", "lint", "fix"}
    if not argv or (argv[0] not in known_commands and not argv[0].startswith("-")):
        argv = ["check"] + argv

    args = parser.parse_args(argv)

    # Load configuration
    cfg = DoctorConfig.load(config_path=args.config)
    if args.rules:
        cfg.enabled_rules = set(args.rules)
    if args.ignore_rules:
        cfg.disabled_rules.update(args.ignore_rules)
    if args.allow_hard_breaks:
        cfg.allow_hard_breaks = True
    if args.default_alt_prefix:
        cfg.default_alt_prefix = args.default_alt_prefix

    doctor = Doctor(config=cfg)
    target_paths = [Path(p) for p in args.paths]
    reporter = Reporter(stream=sys.stdout, format_type=args.format)

    is_fix = (args.subcommand == "fix") or getattr(args, "fix", False)
    dry_run = getattr(args, "dry_run", False)

    if is_fix:
        report = doctor.run_fix(target_paths, dry_run=dry_run)
    else:
        report = doctor.run_check(target_paths)

    reporter.render(report, is_fix_mode=is_fix, dry_run=dry_run)

    if getattr(args, "exit_zero", False):
        return 0

    return 0 if report.is_clean else 1


if __name__ == "__main__":
    sys.exit(main())
