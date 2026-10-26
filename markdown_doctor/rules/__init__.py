"""Rules package for markdown-doctor."""

from __future__ import annotations

from typing import Dict, List, Type

from markdown_doctor.rules.anchors import BrokenAnchorRule
from markdown_doctor.rules.base import BaseRule
from markdown_doctor.rules.code_fences import UnclosedCodeFenceRule
from markdown_doctor.rules.empty_links import EmptyLinkUrlRule
from markdown_doctor.rules.frontmatter import FrontmatterRule
from markdown_doctor.rules.image_alt import MissingImageAltRule
from markdown_doctor.rules.trailing_whitespace import TrailingWhitespaceRule

DEFAULT_RULE_CLASSES: List[Type[BaseRule]] = [
    BrokenAnchorRule,
    UnclosedCodeFenceRule,
    MissingImageAltRule,
    TrailingWhitespaceRule,
    FrontmatterRule,
    EmptyLinkUrlRule,
]


def get_default_rules() -> List[BaseRule]:
    """Instantiate and return standard rules."""
    return [cls() for cls in DEFAULT_RULE_CLASSES]


def get_rule_by_id(rule_id: str) -> BaseRule | None:
    """Retrieve rule instance by rule ID."""
    for cls in DEFAULT_RULE_CLASSES:
        instance = cls()
        if instance.rule_id == rule_id:
            return instance
    return None


__all__ = [
    "BaseRule",
    "BrokenAnchorRule",
    "UnclosedCodeFenceRule",
    "MissingImageAltRule",
    "TrailingWhitespaceRule",
    "FrontmatterRule",
    "EmptyLinkUrlRule",
    "DEFAULT_RULE_CLASSES",
    "get_default_rules",
    "get_rule_by_id",
]
