"""Anchor slug generation adhering to GitHub/CommonMark markdown conventions."""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, Set


def slugify_heading(text: str) -> str:
    """Convert heading text to a URL anchor slug.

    Follows GitHub Flavored Markdown slug generation:
    1. Strip leading/trailing whitespace.
    2. Remove inline markdown links (keep link text).
    3. Remove inline formatting (backticks, bold, italics, strikethrough).
    4. Strip punctuation / special symbols except hyphens, underscores, and alphanumerics.
    5. Convert spaces to hyphens.
    6. Lowercase everything.
    """
    # Remove markdown link syntax [text](url) -> text
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove HTML tags <... >
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    # Remove inline backticks `code` -> code
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    # Remove bold/italic markers
    cleaned = re.sub(r"[*_~]{1,3}", "", cleaned)

    # Normalize unicode characters
    cleaned = unicodedata.normalize("NFKD", cleaned)
    # Lowercase
    cleaned = cleaned.strip().lower()

    # Remove all characters that are not alphanumeric, whitespace, hyphen or underscore
    # Note: Keep non-ASCII word characters for international headings
    cleaned = re.sub(r"[^\w\s\-]", "", cleaned)

    # Replace whitespace sequences with a single hyphen
    slug = re.sub(r"\s+", "-", cleaned)

    # Remove leading/trailing hyphens if created
    slug = slug.strip("-")

    return slug


class HeadingSlugTracker:
    """Tracks headings within a document and assigns GitHub-style unique slug IDs."""

    def __init__(self) -> None:
        self._counts: Dict[str, int] = {}
        self._all_slugs: Set[str] = set()

    def register_heading(self, heading_text: str) -> str:
        """Register a heading and return its unique anchor slug (e.g. 'title', 'title-1')."""
        base_slug = slugify_heading(heading_text)
        if not base_slug:
            base_slug = "section"

        if base_slug not in self._counts:
            self._counts[base_slug] = 0
            final_slug = base_slug
        else:
            self._counts[base_slug] += 1
            final_slug = f"{base_slug}-{self._counts[base_slug]}"

        self._all_slugs.add(final_slug)
        return final_slug

    def register_custom_anchor(self, anchor_id: str) -> None:
        """Register a custom anchor from HTML attribute like <a id="..."> or <a name="...">."""
        cleaned = anchor_id.strip().lstrip("#").lower()
        if cleaned:
            self._all_slugs.add(cleaned)

    @property
    def slugs(self) -> Set[str]:
        """Return the set of all valid anchor IDs in the document."""
        return set(self._all_slugs)

    def contains(self, slug: str) -> bool:
        """Check if a slug exists in the document (case-insensitive and lstripped)."""
        normalized = slug.strip().lstrip("#").lower()
        return normalized in self._all_slugs
