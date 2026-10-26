# markdown-doctor

[![CI](https://github.com/slopgobblercobbler/markdown-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/slopgobblercobbler/markdown-doctor/actions)
[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org/project/markdown-doctor/)
[![Python versions](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)](https://pypi.org/project/markdown-doctor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![WCAG 2.1](https://img.shields.io/badge/Accessibility-WCAG%201.1.1-green.svg)](https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html)

> Production-grade Markdown linter, broken anchor detector, and automated repair doctor.

`markdown-doctor` is a developer CLI utility and Python library designed to keep documentation, blogs, and static sites healthy across large repositories. It detects broken internal anchor links, unclosed code fences, missing alt text on images, trailing spaces, and invalid frontmatter YAML—with automated autofixes.

---

## Features

- **Broken Internal Anchor Links**: Validates intra-document links (`[link](#my-heading)`) against GitHub/CommonMark slugified headings and custom HTML anchor targets (`<a id="...">`). Provides Levenshtein-based fuzzy match suggestions and automated repair.
- **Relative Link & Cross-File Anchors**: Resolves local file links (`[guide](./docs/guide.md#installation)`) and verifies that target files and cross-document anchors exist.
- **Unclosed Code Fences**: Catches opening code blocks (```` ``` ```` or `~~~`) that were never terminated, preventing broken rendering in documentation generators (MkDocs, VitePress, Docusaurus, GitHub Pages). Automatically inserts matching closing fences at document boundaries.
- **Accessibility & Missing Alt Text (WCAG 1.1.1)**: Detects markdown images (`![]()`) and HTML `<img>` tags missing alternative text. Generates descriptive, human-readable alt text based on image filenames.
- **YAML Frontmatter Linter**: Validates Jekyll/Hugo/Astro/Docusaurus YAML frontmatter delimiters and syntax using PyYAML SafeLoader. Automatically fixes malformed opening delimiters and closes unclosed frontmatter blocks.
- **Trailing Whitespace Removal**: Normalizes lines with trailing spaces or tabs, while supporting CommonMark two-space hard line breaks when enabled.
- **Flexible Formats**: Outputs formatted rich color terminal output, compact Unix output, machine-readable JSON, or GitHub Actions workflow annotations (`::error` and `::warning`).

---

## Installation

### Via pip

```bash
pip install markdown-doctor
```

### Via pipx (recommended for standalone CLI usage)

```bash
pipx install markdown-doctor
```

---

## Quickstart & CLI Usage

### Check Markdown Documents

Scan documents in the current directory or specific files:

```bash
# Scan all Markdown files in the current workspace
markdown-doctor check

# Scan specific files or directories
markdown-doctor check README.md docs/

# Alias: 'lint'
markdown-doctor lint docs/
```

### Automatically Fix Issues

Repair all autofixable issues in-place:

```bash
# Automatically repair all documents in-place
markdown-doctor fix

# Preview changes without modifying files on disk
markdown-doctor fix --dry-run

# Run check with autofix enabled
markdown-doctor check --fix
```

### Output Formats

```bash
# JSON output for CI pipelines and scripts
markdown-doctor check --format json

# GitHub Actions workflow annotations
markdown-doctor check --format github

# Compact format for quick grep / editor integration
markdown-doctor check --format compact
```

---

## Command-Line Options

| Flag | Description |
| --- | --- |
| `check [paths...]` | Scan Markdown documents for diagnostics (exit 0 if clean, 1 if issues found). |
| `lint [paths...]` | Alias for `check`. |
| `fix [paths...]` | Automatically repair autofixable issues in target files. |
| `--dry-run` | Preview repairs without modifying files on disk (use with `fix`). |
| `--format {text,json,github,compact}` | Report output format (default: `text`). |
| `--config PATH` | Path to custom configuration file (`pyproject.toml` or `.markdown-doctor.toml`). |
| `--rule RULE` | Explicitly enable specific rule(s) by ID. |
| `--ignore-rule RULE` | Disable specific rule(s) by ID. |
| `--allow-hard-breaks` | Permit exactly 2 trailing spaces on lines (CommonMark hard line breaks). |
| `--default-alt-prefix PREFIX` | Custom prefix to prepend to auto-generated image alt text. |
| `--exit-zero` | Always exit with code 0 even if issues are detected. |
| `-V, --version` | Display version number and exit. |

---

## Rules Reference

| Rule ID | Severity | Autofixable | Description |
| --- | --- | --- | --- |
| `broken-anchor-link` | Error | Yes | Internal anchor link (`#heading`) does not match any heading or HTML anchor target. |
| `broken-relative-link` | Error | No | Referenced local file target does not exist on disk. |
| `broken-relative-anchor` | Error | No | Anchor target does not exist in referenced Markdown file. |
| `unclosed-code-fence` | Error | Yes | Code fence (```` ``` ```` or `~~~`) was opened but never closed. |
| `missing-image-alt` | Warning | Yes | Image is missing descriptive alt text (accessibility violation WCAG 1.1.1). |
| `invalid-frontmatter` | Error | Yes | YAML frontmatter has syntax errors, malformed delimiters, or is unclosed. |
| `trailing-whitespace` | Warning | Yes | Line has trailing whitespace characters. |
| `empty-link-url` | Warning | No | Link destination is empty or placeholder `#`. |

---

## Configuration

`markdown-doctor` can be configured via `pyproject.toml` or a dedicated `.markdown-doctor.toml` file in your repository root:

### In `pyproject.toml`

```toml
[tool.markdown-doctor]
# Glob patterns to exclude from scanning
exclude = [
    ".git",
    "node_modules",
    ".venv",
    "build",
    "dist"
]

# Disable specific rules
ignore = [
    "empty-link-url"
]

# Permit 2 trailing spaces for CommonMark hard line breaks
allow_hard_breaks = true

# Custom prefix for generated image alt text
default_alt_prefix = "Figure:"
```

### In `.markdown-doctor.toml`

```toml
rules = ["broken-anchor-link", "unclosed-code-fence", "missing-image-alt"]
allow_hard_breaks = true
```

---

## Python API Usage

You can embed `markdown-doctor` directly into your Python tools, test suites, or documentation generators:

```python
from markdown_doctor import Doctor, DoctorConfig

# Initialize doctor with custom configuration
config = DoctorConfig(allow_hard_breaks=True)
doctor = Doctor(config=config)

# Check an in-memory markdown string
markdown_text = """
# Quickstart

See [Instalation](#instalation).

```python
print("Hello world")
"""

result = doctor.check_text(markdown_text)
for issue in result.issues:
    print(f"Line {issue.line}: {issue.message} [{issue.rule_id}]")

# Automatically fix text
fixed_text, result = doctor.fix_text(markdown_text)
print(f"Applied {result.fixed_count} fixes!")
print(fixed_text)
```

---

## GitHub Actions CI Integration

Add `markdown-doctor` to your GitHub Actions workflow (`.github/workflows/markdown-doctor.yml`) to automatically check documentation on every pull request:

```yaml
name: Markdown Health Check

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint-docs:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install markdown-doctor
        run: pip install markdown-doctor

      - name: Run markdown-doctor
        run: markdown-doctor check --format github
```

---

## Contributing

Contributions are welcome!

1. Fork the repository on GitHub.
2. Clone your fork and create a new feature branch.
3. Install development dependencies:
   ```bash
   pip install -e .[dev]
   ```
4. Run the test suite:
   ```bash
   pytest
   ```
5. Submit a pull request.

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).
