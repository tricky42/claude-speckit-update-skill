"""Intelligent 3-way merge for markdown files.

This module implements section-based merging for markdown files,
allowing automatic merging of non-conflicting changes and generating
granular conflict markers only where necessary.
"""

import re
from dataclasses import dataclass
from typing import Sequence

from speckit_update.models import ConflictResult


@dataclass
class Section:
    """A section of a markdown document.

    Sections are delimited by headers (# ## ### etc.) and contain
    all content until the next header of equal or higher level.
    """

    header: str
    """The header line (e.g., '## Section Name')."""

    level: int
    """Header level (1-6)."""

    content: str
    """Content below the header (excluding sub-sections)."""

    @property
    def title(self) -> str:
        """Extract title text from header."""
        return self.header.lstrip("#").strip()

    @property
    def full_text(self) -> str:
        """Get full section text including header."""
        if self.content:
            return f"{self.header}\n{self.content}"
        return self.header


class MarkdownMerger:
    """Intelligent 3-way merge for markdown files.

    Uses section-based parsing to:
    1. Match sections between versions using fuzzy matching
    2. Auto-merge non-conflicting changes
    3. Generate section-level conflict markers for true conflicts
    """

    SIMILARITY_THRESHOLD = 0.8  # 80% match for renamed sections

    def __init__(self) -> None:
        """Initialize the merger."""
        pass

    def parse_sections(self, content: str) -> list[Section]:
        """Parse markdown content into sections.

        Args:
            content: Markdown content string.

        Returns:
            List of Section objects.
        """
        if not content.strip():
            return []

        sections: list[Section] = []
        lines = content.split("\n")

        current_header = ""
        current_level = 0
        current_content_lines: list[str] = []
        preamble_lines: list[str] = []
        in_preamble = True

        for line in lines:
            # Check if this is a header line
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if header_match:
                # Save previous section if exists
                if current_header:
                    sections.append(Section(
                        header=current_header,
                        level=current_level,
                        content="\n".join(current_content_lines).strip(),
                    ))
                elif in_preamble and preamble_lines:
                    # Save preamble as level 0 section
                    sections.append(Section(
                        header="",
                        level=0,
                        content="\n".join(preamble_lines).strip(),
                    ))

                in_preamble = False
                current_header = line
                current_level = len(header_match.group(1))
                current_content_lines = []
            else:
                if in_preamble:
                    preamble_lines.append(line)
                else:
                    current_content_lines.append(line)

        # Don't forget the last section
        if current_header:
            sections.append(Section(
                header=current_header,
                level=current_level,
                content="\n".join(current_content_lines).strip(),
            ))
        elif preamble_lines:
            sections.append(Section(
                header="",
                level=0,
                content="\n".join(preamble_lines).strip(),
            ))

        return sections

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings.

        Args:
            s1: First string.
            s2: Second string.

        Returns:
            Edit distance.
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Calculate cost of insertions, deletions, substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio between strings.

        Args:
            s1: First string.
            s2: Second string.

        Returns:
            Similarity ratio (0.0 to 1.0).
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        max_len = max(len(s1), len(s2))
        distance = self._levenshtein_distance(s1.lower(), s2.lower())
        return 1.0 - (distance / max_len)

    def _find_matching_section(
        self,
        section: Section,
        candidates: Sequence[Section],
    ) -> Section | None:
        """Find a matching section using fuzzy matching.

        Args:
            section: Section to match.
            candidates: Candidate sections to search.

        Returns:
            Best matching section or None.
        """
        best_match: Section | None = None
        best_score = 0.0

        for candidate in candidates:
            # Check header similarity
            score = self._similarity(section.title, candidate.title)

            if score >= self.SIMILARITY_THRESHOLD and score > best_score:
                best_score = score
                best_match = candidate

        return best_match

    def merge(
        self,
        base: str,
        current: str,
        incoming: str,
        *,
        base_version: str = "base",
        current_version: str = "current",
        incoming_version: str = "incoming",
    ) -> ConflictResult:
        """Perform 3-way merge on markdown content.

        Args:
            base: Original content (common ancestor).
            current: Current content (local modifications).
            incoming: Incoming content (upstream changes).
            base_version: Label for base version in conflict markers.
            current_version: Label for current version in conflict markers.
            incoming_version: Label for incoming version in conflict markers.

        Returns:
            ConflictResult with merged content and conflict info.
        """
        # Parse all three versions
        base_sections = self.parse_sections(base)
        current_sections = self.parse_sections(current)
        incoming_sections = self.parse_sections(incoming)

        # Use incoming structure as canonical
        merged_parts: list[str] = []
        conflict_markers: list[tuple[int, int]] = []
        current_line = 1

        for incoming_section in incoming_sections:
            # Find matching sections in base and current
            base_match = self._find_matching_section(incoming_section, base_sections)
            current_match = self._find_matching_section(incoming_section, current_sections)

            section_text: str
            has_conflict = False

            if base_match is None and current_match is None:
                # New section in incoming - just add it
                section_text = incoming_section.full_text

            elif base_match is None:
                # Section exists in current but not base, and also in incoming
                # Current added it, incoming added it - potential conflict
                if current_match and current_match.full_text != incoming_section.full_text:
                    section_text, has_conflict = self._create_conflict_marker(
                        current_match.full_text,
                        incoming_section.full_text,
                        current_version,
                        incoming_version,
                    )
                else:
                    section_text = incoming_section.full_text

            elif current_match is None:
                # Section was in base, removed in current, exists in incoming
                # User deleted it - check if incoming changed it
                if base_match.full_text == incoming_section.full_text:
                    # Incoming didn't change, respect user's deletion
                    continue
                else:
                    # Incoming changed it - conflict
                    section_text, has_conflict = self._create_conflict_marker(
                        "(section deleted)",
                        incoming_section.full_text,
                        current_version,
                        incoming_version,
                    )

            else:
                # Section exists in all three versions
                base_text = base_match.full_text
                current_text = current_match.full_text
                incoming_text = incoming_section.full_text

                if current_text == base_text:
                    # Current unchanged - take incoming
                    section_text = incoming_text

                elif incoming_text == base_text:
                    # Incoming unchanged - keep current
                    section_text = current_text

                elif current_text == incoming_text:
                    # Both changed the same way - no conflict
                    section_text = current_text

                else:
                    # Both changed differently - conflict
                    section_text, has_conflict = self._create_conflict_marker(
                        current_text,
                        incoming_text,
                        current_version,
                        incoming_version,
                    )

            if has_conflict:
                # Track conflict marker positions
                lines_in_section = section_text.count("\n") + 1
                conflict_markers.append((current_line, current_line + lines_in_section - 1))

            merged_parts.append(section_text)
            current_line += section_text.count("\n") + 2  # +1 for section, +1 for blank line

        # Check for sections in current that aren't in incoming (user additions)
        for current_section in current_sections:
            incoming_match = self._find_matching_section(current_section, incoming_sections)
            base_match = self._find_matching_section(current_section, base_sections)

            if incoming_match is None and base_match is None:
                # User added this section - preserve it
                merged_parts.append(current_section.full_text)

        merged_content = "\n\n".join(merged_parts)

        if conflict_markers:
            return ConflictResult.with_conflicts(merged_content, conflict_markers)
        return ConflictResult.clean_merge(merged_content)

    def _create_conflict_marker(
        self,
        current_text: str,
        incoming_text: str,
        current_label: str,
        incoming_label: str,
    ) -> tuple[str, bool]:
        """Create git-style conflict markers.

        Args:
            current_text: Current version text.
            incoming_text: Incoming version text.
            current_label: Label for current version.
            incoming_label: Label for incoming version.

        Returns:
            Tuple of (marked up text, True for has_conflict).
        """
        return (
            f"<<<<<<< {current_label}\n"
            f"{current_text}\n"
            f"=======\n"
            f"{incoming_text}\n"
            f">>>>>>> {incoming_label}",
            True,
        )


def merge_markdown_files(
    base_content: str,
    current_content: str,
    incoming_content: str,
    *,
    base_version: str = "base",
    current_version: str = "current",
    incoming_version: str = "incoming",
) -> ConflictResult:
    """Convenience function for 3-way markdown merge.

    Args:
        base_content: Original content.
        current_content: Current local content.
        incoming_content: Incoming upstream content.
        base_version: Label for base in markers.
        current_version: Label for current in markers.
        incoming_version: Label for incoming in markers.

    Returns:
        ConflictResult with merge outcome.
    """
    merger = MarkdownMerger()
    return merger.merge(
        base_content,
        current_content,
        incoming_content,
        base_version=base_version,
        current_version=current_version,
        incoming_version=incoming_version,
    )
