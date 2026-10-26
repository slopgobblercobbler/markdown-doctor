"""Base class and registry for linting rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from markdown_doctor.document import MarkdownDocument
from markdown_doctor.models import Issue, Severity


class BaseRule(ABC):
    """Abstract base class for all markdown-doctor rules."""

    rule_id: str
    description: str
    severity: Severity = Severity.ERROR
    fixable: bool = False

    @abstractmethod
    def check(self, doc: MarkdownDocument) -> List[Issue]:
        """Inspect a parsed document and return any issues discovered."""
        pass
