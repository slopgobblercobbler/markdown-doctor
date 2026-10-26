"""Tests for configuration loading."""

from pathlib import Path
from markdown_doctor.config import DoctorConfig


def test_default_config() -> None:
    cfg = DoctorConfig()
    assert cfg.is_rule_enabled("broken-anchor-link") is True
    assert cfg.allow_hard_breaks is False


def test_load_pyproject_toml(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.markdown-doctor]
ignore = ["trailing-whitespace"]
allow_hard_breaks = true
default_alt_prefix = "Figure:"
""",
        encoding="utf-8",
    )

    cfg = DoctorConfig.load(pyproject)
    assert cfg.is_rule_enabled("trailing-whitespace") is False
    assert cfg.is_rule_enabled("broken-anchor-link") is True
    assert cfg.allow_hard_breaks is True
    assert cfg.default_alt_prefix == "Figure:"


def test_load_dot_config_file(tmp_path: Path) -> None:
    dot_cfg = tmp_path / ".markdown-doctor.toml"
    dot_cfg.write_text(
        """
rules = ["broken-anchor-link", "unclosed-code-fence"]
allow_hard_breaks = false
""",
        encoding="utf-8",
    )

    cfg = DoctorConfig.load(dot_cfg)
    assert cfg.is_rule_enabled("broken-anchor-link") is True
    assert cfg.is_rule_enabled("unclosed-code-fence") is True
    assert cfg.is_rule_enabled("trailing-whitespace") is False
