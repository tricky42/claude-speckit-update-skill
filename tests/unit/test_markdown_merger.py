"""Tests for markdown merger."""

import pytest

from speckit_update.services.markdown_merger import (
    MarkdownMerger,
    Section,
    merge_markdown_files,
)


class TestSectionParsing:
    """Tests for section parsing."""

    def test_parse_simple_sections(self) -> None:
        """Should parse basic markdown sections."""
        content = """# Header 1

Content under header 1.

## Header 2

Content under header 2.
"""
        merger = MarkdownMerger()
        sections = merger.parse_sections(content)

        assert len(sections) == 2
        assert sections[0].header == "# Header 1"
        assert sections[0].level == 1
        assert "Content under header 1" in sections[0].content
        assert sections[1].header == "## Header 2"
        assert sections[1].level == 2

    def test_parse_empty_content(self) -> None:
        """Should handle empty content."""
        merger = MarkdownMerger()
        sections = merger.parse_sections("")
        assert sections == []

    def test_parse_preamble(self) -> None:
        """Should capture content before first header."""
        content = """Some preamble text.

# First Header

Content.
"""
        merger = MarkdownMerger()
        sections = merger.parse_sections(content)

        assert len(sections) == 2
        assert sections[0].level == 0
        assert "preamble" in sections[0].content

    def test_section_title(self) -> None:
        """Should extract title from header."""
        section = Section(
            header="## My Section Title",
            level=2,
            content="Content here.",
        )
        assert section.title == "My Section Title"


class TestMerging:
    """Tests for 3-way merge."""

    def test_clean_merge_no_changes(self) -> None:
        """Should merge cleanly when no conflicts."""
        base = "# Header\n\nBase content."
        current = "# Header\n\nBase content."
        incoming = "# Header\n\nBase content."

        result = merge_markdown_files(base, current, incoming)

        assert result.has_conflicts is False
        assert result.conflict_count == 0

    def test_clean_merge_incoming_only(self) -> None:
        """Should take incoming changes when current unchanged."""
        base = "# Header\n\nOriginal."
        current = "# Header\n\nOriginal."
        incoming = "# Header\n\nUpdated content."

        result = merge_markdown_files(base, current, incoming)

        assert result.has_conflicts is False
        assert "Updated content" in result.merged_content

    def test_clean_merge_current_only(self) -> None:
        """Should keep current changes when incoming unchanged."""
        base = "# Header\n\nOriginal."
        current = "# Header\n\nMy customization."
        incoming = "# Header\n\nOriginal."

        result = merge_markdown_files(base, current, incoming)

        assert result.has_conflicts is False
        assert "My customization" in result.merged_content

    def test_conflict_both_changed(self) -> None:
        """Should create conflict when both changed differently."""
        base = "# Header\n\nOriginal."
        current = "# Header\n\nCurrent change."
        incoming = "# Header\n\nIncoming change."

        result = merge_markdown_files(base, current, incoming)

        assert result.has_conflicts is True
        assert result.conflict_count >= 1
        assert "<<<<<<<" in result.merged_content
        assert "=======" in result.merged_content
        assert ">>>>>>>" in result.merged_content

    def test_new_section_in_incoming(self) -> None:
        """Should add new sections from incoming."""
        base = "# Header 1\n\nContent."
        current = "# Header 1\n\nContent."
        incoming = "# Header 1\n\nContent.\n\n## New Section\n\nNew content."

        result = merge_markdown_files(base, current, incoming)

        assert result.has_conflicts is False
        assert "New Section" in result.merged_content
        assert "New content" in result.merged_content

    def test_preserve_user_additions(self) -> None:
        """Should preserve sections added by user."""
        base = "# Header 1\n\nContent."
        current = "# Header 1\n\nContent.\n\n## My Custom Section\n\nMy content."
        incoming = "# Header 1\n\nContent."

        result = merge_markdown_files(base, current, incoming)

        assert result.has_conflicts is False
        assert "My Custom Section" in result.merged_content

    def test_same_changes_no_conflict(self) -> None:
        """Should not conflict when both made same change."""
        base = "# Header\n\nOriginal."
        current = "# Header\n\nSame update."
        incoming = "# Header\n\nSame update."

        result = merge_markdown_files(base, current, incoming)

        assert result.has_conflicts is False


class TestLevenshteinDistance:
    """Tests for similarity calculation."""

    def test_identical_strings(self) -> None:
        """Should return 0 distance for identical strings."""
        merger = MarkdownMerger()
        assert merger._levenshtein_distance("hello", "hello") == 0

    def test_single_edit(self) -> None:
        """Should return 1 for single character difference."""
        merger = MarkdownMerger()
        assert merger._levenshtein_distance("hello", "hallo") == 1

    def test_similarity_identical(self) -> None:
        """Should return 1.0 for identical strings."""
        merger = MarkdownMerger()
        assert merger._similarity("hello", "hello") == 1.0

    def test_similarity_empty(self) -> None:
        """Should handle empty strings."""
        merger = MarkdownMerger()
        assert merger._similarity("", "") == 1.0
        assert merger._similarity("hello", "") == 0.0


class TestConvenienceFunction:
    """Tests for merge_markdown_files."""

    def test_with_version_labels(self) -> None:
        """Should use provided version labels in markers."""
        base = "# Header\n\nOriginal."
        current = "# Header\n\nCurrent."
        incoming = "# Header\n\nIncoming."

        result = merge_markdown_files(
            base,
            current,
            incoming,
            current_version="v0.0.79",
            incoming_version="v0.0.80",
        )

        assert result.has_conflicts is True
        assert "v0.0.79" in result.merged_content
        assert "v0.0.80" in result.merged_content
