"""Parser for Markdown files extracting structural elements for linting."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import yaml

from markdown_doctor.document import MarkdownDocument
from markdown_doctor.models import (
    DocCodeFence,
    DocFrontmatter,
    DocHeading,
    DocLink,
)
from markdown_doctor.slug import HeadingSlugTracker


class MarkdownParser:
    """Parses markdown text into structured elements for linting."""

    # Matches ATX headings: # Heading
    ATX_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)(?:\s+#+)?$")

    # Matches code fence openers: ```lang or ~~~lang
    CODE_FENCE_OPEN_RE = re.compile(r"^(\s{0,3})(`{3,}|~{3,})\s*([a-zA-Z0-9_\-\.\+]*).*$")

    # Matches inline markdown links and images: [text](url) or ![alt](url)
    MARKDOWN_LINK_RE = re.compile(r"(!?)\[((?:[^\[\]]|\\\[|\\\])*)\]\(([^)]*)\)")

    # Matches HTML <img> tag
    HTML_IMG_RE = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)

    # Matches HTML <a> tag
    HTML_A_RE = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.IGNORECASE | re.DOTALL)

    # Matches HTML tags with id or name attribute (anchor targets)
    HTML_ANCHOR_TARGET_RE = re.compile(
        r"""<(?:[a-zA-Z0-9]+)\b[^>]*(?:\bid|\bname)=["']([^"']+)["'][^>]*>""",
        re.IGNORECASE,
    )

    def parse(self, text: str, file_path: Path) -> MarkdownDocument:
        """Parse full markdown text into a MarkdownDocument."""
        lines = text.splitlines()

        doc = MarkdownDocument(
            file_path=file_path,
            raw_content=text,
            lines=lines,
            slug_tracker=HeadingSlugTracker(),
        )

        # 1. Parse Frontmatter
        fm_end_line = self._parse_frontmatter(doc, lines)

        # 2. Parse Code Fences
        self._parse_code_fences(doc, lines, start_after_line=fm_end_line)

        # 3. Parse Headings & HTML Anchors
        self._parse_headings_and_anchors(doc, lines, start_after_line=fm_end_line)

        # 4. Parse Links & Images
        self._parse_links_and_images(doc, lines, start_after_line=fm_end_line)

        return doc

    def _parse_frontmatter(self, doc: MarkdownDocument, lines: List[str]) -> int:
        """Parse YAML frontmatter if present at the start of the document.

        Returns the 1-indexed line number where frontmatter ends, or 0 if none.
        """
        if not lines:
            return 0

        first_line = lines[0].strip()
        if first_line != "---":
            return 0

        # Look for closing delimiter ---
        fm_lines: List[str] = []
        closed = False
        end_idx = -1

        for idx in range(1, len(lines)):
            line = lines[idx]
            if line.strip() == "---":
                closed = True
                end_idx = idx
                break
            fm_lines.append(line)

        raw_fm = "\n".join(fm_lines)
        start_line = 1
        end_line = end_idx + 1 if closed else len(lines)

        is_valid = True
        error_msg: Optional[str] = None
        data: Optional[Dict[str, Any]] = None

        if not closed:
            is_valid = False
            error_msg = "Frontmatter opened with '---' but never closed with matching '---'"
        else:
            try:
                loaded = yaml.safe_load(raw_fm)
                if loaded is not None and not isinstance(loaded, dict):
                    is_valid = False
                    error_msg = f"Frontmatter must be a YAML mapping (got {type(loaded).__name__})"
                else:
                    data = loaded if isinstance(loaded, dict) else {}
            except yaml.YAMLError as exc:
                is_valid = False
                error_msg = f"YAML syntax error: {str(exc)}"

        doc.frontmatter = DocFrontmatter(
            raw=raw_fm,
            start_line=start_line,
            end_line=end_line,
            is_closed=closed,
            is_valid=is_valid,
            error=error_msg,
            data=data,
        )

        return end_line if closed else len(lines)

    def _parse_code_fences(
        self, doc: MarkdownDocument, lines: List[str], start_after_line: int
    ) -> None:
        """Find all code fences and register line numbers inside them."""
        in_fence = False
        current_fence_char = ""
        current_fence_len = 0
        current_lang = ""
        current_start_line = 0
        fence_lines: List[str] = []

        for idx in range(start_after_line, len(lines)):
            line_num = idx + 1
            line = lines[idx]

            if not in_fence:
                match = self.CODE_FENCE_OPEN_RE.match(line)
                if match:
                    fence_str = match.group(2)
                    current_fence_char = fence_str[0]
                    current_fence_len = len(fence_str)
                    current_lang = match.group(3).strip()
                    current_start_line = line_num
                    in_fence = True
                    fence_lines = []
                    doc.code_fence_line_numbers.add(line_num)
            else:
                doc.code_fence_line_numbers.add(line_num)
                # Check for closing fence
                # Closing fence has >= opening fence length of same char and only spaces after
                close_pattern = rf"^\s{{0,3}}{re.escape(current_fence_char)}{{{current_fence_len},}}\s*$"
                if re.match(close_pattern, line):
                    # Closed
                    doc.code_fences.append(
                        DocCodeFence(
                            fence_char=current_fence_char,
                            fence_length=current_fence_len,
                            language=current_lang,
                            start_line=current_start_line,
                            end_line=line_num,
                            is_closed=True,
                            content="\n".join(fence_lines),
                        )
                    )
                    in_fence = False
                else:
                    fence_lines.append(line)

        if in_fence:
            # Unclosed code fence
            doc.code_fences.append(
                DocCodeFence(
                    fence_char=current_fence_char,
                    fence_length=current_fence_len,
                    language=current_lang,
                    start_line=current_start_line,
                    end_line=None,
                    is_closed=False,
                    content="\n".join(fence_lines),
                )
            )

    def _parse_headings_and_anchors(
        self, doc: MarkdownDocument, lines: List[str], start_after_line: int
    ) -> None:
        """Find headings (ATX and Setext) and HTML anchor targets."""
        for idx in range(start_after_line, len(lines)):
            line_num = idx + 1
            if doc.is_line_in_code_fence(line_num):
                continue

            line = lines[idx]

            # 1. ATX heading (# ...)
            atx_match = self.ATX_HEADING_RE.match(line)
            if atx_match:
                level = len(atx_match.group(1))
                heading_text = atx_match.group(2).strip()
                slug = doc.slug_tracker.register_heading(heading_text)
                doc.headings.append(
                    DocHeading(
                        level=level,
                        text=heading_text,
                        slug=slug,
                        line=line_num,
                        raw=line,
                    )
                )
                continue

            # 2. Setext heading (=== or --- under a text line)
            if idx + 1 < len(lines):
                next_line = lines[idx + 1]
                next_line_num = idx + 2
                if not doc.is_line_in_code_fence(next_line_num):
                    if line.strip() and not line.strip().startswith(("#", "-", "*", ">")):
                        if re.match(r"^={2,}\s*$", next_line):
                            heading_text = line.strip()
                            slug = doc.slug_tracker.register_heading(heading_text)
                            doc.headings.append(
                                DocHeading(
                                    level=1,
                                    text=heading_text,
                                    slug=slug,
                                    line=line_num,
                                    raw=f"{line}\n{next_line}",
                                )
                            )
                        elif re.match(r"^-{2,}\s*$", next_line):
                            heading_text = line.strip()
                            slug = doc.slug_tracker.register_heading(heading_text)
                            doc.headings.append(
                                DocHeading(
                                    level=2,
                                    text=heading_text,
                                    slug=slug,
                                    line=line_num,
                                    raw=f"{line}\n{next_line}",
                                )
                            )

            # 3. HTML anchors: <a id="..." name="..."> or <span id="...">
            for match in self.HTML_ANCHOR_TARGET_RE.finditer(line):
                target_id = match.group(1)
                doc.slug_tracker.register_custom_anchor(target_id)

    def _parse_links_and_images(
        self, doc: MarkdownDocument, lines: List[str], start_after_line: int
    ) -> None:
        """Find all markdown links, images, and HTML links/images (ignoring inline code spans)."""
        for idx in range(start_after_line, len(lines)):
            line_num = idx + 1
            if doc.is_line_in_code_fence(line_num):
                continue

            line = lines[idx]
            inline_code_spans = self._extract_inline_code_spans(line)

            # Markdown [text](url) and ![alt](url)
            for match in self.MARKDOWN_LINK_RE.finditer(line):
                # Skip if link is inside inline backticks `[text](url)`
                if self._is_in_spans(match.start(), match.end(), inline_code_spans):
                    continue

                is_img = match.group(1) == "!"
                text = match.group(2)
                raw_target = match.group(3).strip()

                # target might have title: url "title"
                url_part = raw_target.split()[0] if raw_target else ""
                # Strip wrapping <> if format is <url>
                if url_part.startswith("<") and url_part.endswith(">"):
                    url_part = url_part[1:-1]

                # Extract anchor if present
                anchor: Optional[str] = None
                if "#" in url_part:
                    parts = url_part.split("#", 1)
                    anchor = parts[1]

                is_relative = not (
                    url_part.startswith(("http://", "https://", "mailto:", "ftp://", "#"))
                )

                doc.links.append(
                    DocLink(
                        text=text,
                        url=url_part,
                        line=line_num,
                        column=match.start() + 1,
                        is_image=is_img,
                        raw=match.group(0),
                        anchor=anchor,
                        is_relative=is_relative,
                    )
                )

            # HTML <img ...>
            for match in self.HTML_IMG_RE.finditer(line):
                if self._is_in_spans(match.start(), match.end(), inline_code_spans):
                    continue

                tag_attrs = match.group(1)
                src_match = re.search(r"""src=["']([^"']*)["']""", tag_attrs, re.IGNORECASE)
                alt_match = re.search(r"""alt=["']([^"']*)["']""", tag_attrs, re.IGNORECASE)

                url = src_match.group(1) if src_match else ""
                alt = alt_match.group(1) if alt_match else ""

                doc.links.append(
                    DocLink(
                        text=alt,
                        url=url,
                        line=line_num,
                        column=match.start() + 1,
                        is_image=True,
                        raw=match.group(0),
                    )
                )

    def _extract_inline_code_spans(self, line: str) -> List[Tuple[int, int]]:
        """Return start and end indices of all inline code backtick spans on a line."""
        spans: List[Tuple[int, int]] = []
        for match in re.finditer(r"(`+)(.+?)\1", line):
            spans.append((match.start(), match.end()))
        return spans

    def _is_in_spans(self, start: int, end: int, spans: List[Tuple[int, int]]) -> bool:
        """Check if range [start, end] falls within any of the code spans."""
        for s, e in spans:
            if s <= start and end <= e:
                return True
        return False
