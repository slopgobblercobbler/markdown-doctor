"""CLI integration tests."""

import json
from pathlib import Path
from markdown_doctor.cli import main


def test_cli_clean_file(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "clean.md"
    doc.write_text("# Title\n\nAll content is clean.\n", encoding="utf-8")

    code = main(["check", str(doc)])
    assert code == 0
    captured = capsys.readouterr()
    assert "All clean!" in captured.out or "0 remaining issues" in captured.out


def test_cli_broken_file_check(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "broken.md"
    doc.write_text("# Title\n\nBroken [link](#non-existent).\n", encoding="utf-8")

    code = main(["check", str(doc)])
    assert code == 1
    captured = capsys.readouterr()
    assert "broken-anchor-link" in captured.out


def test_cli_lint_alias(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "test.md"
    doc.write_text("# Test\n\nContent.\n", encoding="utf-8")

    code = main(["lint", str(doc)])
    assert code == 0


def test_cli_exit_zero_flag(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "broken.md"
    doc.write_text("# Title\n\n[empty]()\n", encoding="utf-8")

    code = main(["check", str(doc), "--exit-zero"])
    assert code == 0


def test_cli_fix_file(tmp_path: Path) -> None:
    doc = tmp_path / "needs_fix.md"
    doc.write_text("# Title   \n\n```python\nprint('hello')\n", encoding="utf-8")

    code = main(["fix", str(doc)])
    assert code == 0

    fixed_content = doc.read_text(encoding="utf-8")
    assert "# Title\n" in fixed_content
    assert "```\n" in fixed_content or fixed_content.endswith("```")


def test_cli_fix_dry_run(tmp_path: Path) -> None:
    doc = tmp_path / "dry_run.md"
    original = "# Title   \n"
    doc.write_text(original, encoding="utf-8")

    code = main(["fix", str(doc), "--dry-run"])
    # File content should NOT have changed on disk
    assert doc.read_text(encoding="utf-8") == original


def test_cli_json_format(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "test.md"
    doc.write_text("# Title\n\nLine with space  \n", encoding="utf-8")

    code = main(["check", str(doc), "--format", "json"])
    assert code == 1
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "summary" in data
    assert "files" in data
    assert data["summary"]["total_issues"] >= 1


def test_cli_github_format(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "test.md"
    doc.write_text("# Title\n\n[empty]()\n", encoding="utf-8")

    code = main(["check", str(doc), "--format", "github"])
    assert code == 1
    captured = capsys.readouterr()
    assert "::warning file=" in captured.out or "::error file=" in captured.out


def test_cli_rule_flags(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "test.md"
    doc.write_text("# Title\n\nLine with trailing space \n", encoding="utf-8")

    # Disable trailing-whitespace rule
    code = main(["check", str(doc), "--ignore-rule", "trailing-whitespace"])
    assert code == 0
