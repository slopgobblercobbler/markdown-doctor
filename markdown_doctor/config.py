"""Configuration management for markdown-doctor."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore # Python < 3.11
    except ImportError:
        try:
            import toml as tomllib  # type: ignore
        except ImportError:
            tomllib = None  # type: ignore


DEFAULT_INCLUDES = ["**/*.md", "**/*.markdown"]
DEFAULT_EXCLUDES = [
    ".git",
    ".github",
    ".tox",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    "site-packages",
    ".pytest_cache",
    ".mypy_cache",
]


@dataclass
class DoctorConfig:
    """Configuration options for markdown-doctor."""

    includes: List[str] = field(default_factory=lambda: list(DEFAULT_INCLUDES))
    excludes: List[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDES))
    enabled_rules: Optional[Set[str]] = None
    disabled_rules: Set[str] = field(default_factory=set)
    allow_hard_breaks: bool = False
    default_alt_prefix: str = ""

    @classmethod
    def load(cls, config_path: Optional[Path] = None, base_dir: Optional[Path] = None) -> DoctorConfig:
        """Load configuration from explicit path, pyproject.toml, or .markdown-doctor.toml."""
        base = base_dir or Path.cwd()

        if config_path and config_path.is_file():
            return cls._from_file(config_path)

        # Check default locations
        candidates = [
            base / ".markdown-doctor.toml",
            base / "pyproject.toml",
        ]

        for cand in candidates:
            if cand.is_file():
                cfg = cls._from_file(cand)
                if cfg:
                    return cfg

        return cls()

    @classmethod
    def _from_file(cls, path: Path) -> DoctorConfig:
        """Parse configuration file."""
        if tomllib is None:
            return cls()

        try:
            content = path.read_text(encoding="utf-8")
            data = tomllib.loads(content)
        except Exception:
            return cls()

        # If pyproject.toml, extract [tool.markdown-doctor]
        if path.name == "pyproject.toml":
            tool_section = data.get("tool", {})
            section = tool_section.get("markdown-doctor") or tool_section.get("markdown_doctor")
            if not isinstance(section, dict):
                return cls()
        else:
            section = data

        return cls._from_dict(section)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> DoctorConfig:
        cfg = cls()
        if "include" in data and isinstance(data["include"], list):
            cfg.includes = [str(x) for x in data["include"]]
        if "exclude" in data and isinstance(data["exclude"], list):
            cfg.excludes = [str(x) for x in data["exclude"]]
        if "rules" in data and isinstance(data["rules"], list):
            cfg.enabled_rules = set(data["rules"])
        if "ignore" in data and isinstance(data["ignore"], list):
            cfg.disabled_rules = set(data["ignore"])
        if "allow_hard_breaks" in data:
            cfg.allow_hard_breaks = bool(data["allow_hard_breaks"])
        if "default_alt_prefix" in data:
            cfg.default_alt_prefix = str(data["default_alt_prefix"])

        return cfg

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Determine if a rule should run given configuration filters."""
        if rule_id in self.disabled_rules:
            return False
        if self.enabled_rules is not None:
            return rule_id in self.enabled_rules
        return True
