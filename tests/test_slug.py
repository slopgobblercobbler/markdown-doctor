"""Tests for anchor slug generation and tracking."""

from markdown_doctor.slug import HeadingSlugTracker, slugify_heading


def test_slugify_heading_basic() -> None:
    assert slugify_heading("Introduction") == "introduction"
    assert slugify_heading("Getting Started") == "getting-started"
    assert slugify_heading("Quickstart Guide (v2.0)") == "quickstart-guide-v20"


def test_slugify_heading_punctuation() -> None:
    assert slugify_heading("What's New in 2026?!") == "whats-new-in-2026"
    assert slugify_heading("C++ & Python: Best Friends") == "c-python-best-friends"
    assert slugify_heading("`config.json` Settings") == "configjson-settings"
    assert slugify_heading("[Link Title](https://example.com)") == "link-title"


def test_slugify_heading_accents() -> None:
    # Unicode normalize
    assert slugify_heading("Résumé & Über") == "resume-uber"


def test_heading_slug_tracker_duplicates() -> None:
    tracker = HeadingSlugTracker()
    assert tracker.register_heading("Options") == "options"
    assert tracker.register_heading("Options") == "options-1"
    assert tracker.register_heading("Options") == "options-2"
    assert tracker.register_heading("Advanced") == "advanced"

    assert tracker.contains("options")
    assert tracker.contains("options-1")
    assert tracker.contains("options-2")
    assert tracker.contains("advanced")
    assert not tracker.contains("non-existent")


def test_heading_slug_tracker_custom_html_anchors() -> None:
    tracker = HeadingSlugTracker()
    tracker.register_custom_anchor("custom-target")
    tracker.register_custom_anchor("#another-target")

    assert tracker.contains("custom-target")
    assert tracker.contains("another-target")
    assert tracker.contains("#custom-target")
