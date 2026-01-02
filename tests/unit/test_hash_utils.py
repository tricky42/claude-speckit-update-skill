"""Tests for hash utilities."""

from pathlib import Path

import pytest

from speckit_update.services.hash_utils import (
    calculate_file_hash,
    calculate_hash,
    hashes_match,
    is_content_modified,
    normalize_content,
)


class TestNormalizeContent:
    """Tests for content normalization."""

    def test_removes_bom(self) -> None:
        """Should remove UTF-8 BOM."""
        # UTF-8 BOM followed by "hello"
        content = b"\xef\xbb\xbfhello"
        result = normalize_content(content)
        assert not result.startswith(b"\xef\xbb\xbf")
        assert result == b"hello\n"

    def test_converts_crlf_to_lf(self) -> None:
        """Should convert CRLF line endings to LF."""
        content = b"line1\r\nline2\r\nline3"
        result = normalize_content(content)
        assert b"\r\n" not in result
        assert result == b"line1\nline2\nline3\n"

    def test_strips_trailing_whitespace(self) -> None:
        """Should strip trailing whitespace from each line."""
        content = b"line1   \nline2\t\t\nline3  \n"
        result = normalize_content(content)
        assert result == b"line1\nline2\nline3\n"

    def test_ensures_trailing_newline(self) -> None:
        """Should ensure single trailing newline."""
        content = b"no trailing newline"
        result = normalize_content(content)
        assert result.endswith(b"\n")
        assert result == b"no trailing newline\n"

    def test_preserves_empty_lines(self) -> None:
        """Should preserve empty lines in content."""
        content = b"line1\n\nline3"
        result = normalize_content(content)
        assert result == b"line1\n\nline3\n"


class TestCalculateHash:
    """Tests for hash calculation."""

    def test_returns_sha256_format(self) -> None:
        """Should return hash in sha256:hex format."""
        result = calculate_hash(b"test content")
        assert result.startswith("sha256:")
        assert len(result) == 7 + 64  # "sha256:" + 64 hex chars

    def test_consistent_hash(self) -> None:
        """Same content should produce same hash."""
        content = b"test content"
        hash1 = calculate_hash(content)
        hash2 = calculate_hash(content)
        assert hash1 == hash2

    def test_different_content_different_hash(self) -> None:
        """Different content should produce different hash."""
        hash1 = calculate_hash(b"content 1")
        hash2 = calculate_hash(b"content 2")
        assert hash1 != hash2

    def test_normalized_before_hash(self) -> None:
        """Content should be normalized before hashing."""
        # Same content with different line endings should hash the same
        unix = b"line1\nline2"
        windows = b"line1\r\nline2"
        assert calculate_hash(unix) == calculate_hash(windows)


class TestCalculateFileHash:
    """Tests for file hashing."""

    def test_hashes_file(self, tmp_path: Path) -> None:
        """Should hash file contents."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")

        result = calculate_file_hash(file_path)
        assert result.startswith("sha256:")

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing file."""
        file_path = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            calculate_file_hash(file_path)

    def test_consistent_with_calculate_hash(self, tmp_path: Path) -> None:
        """File hash should match direct content hash."""
        content = "test content"
        file_path = tmp_path / "test.txt"
        file_path.write_text(content)

        file_hash = calculate_file_hash(file_path)
        content_hash = calculate_hash(content.encode())
        assert file_hash == content_hash


class TestHashHelpers:
    """Tests for hash helper functions."""

    def test_hashes_match_true(self) -> None:
        """Should return True for matching hashes."""
        hash1 = "sha256:" + "a" * 64
        hash2 = "sha256:" + "a" * 64
        assert hashes_match(hash1, hash2) is True

    def test_hashes_match_false(self) -> None:
        """Should return False for different hashes."""
        hash1 = "sha256:" + "a" * 64
        hash2 = "sha256:" + "b" * 64
        assert hashes_match(hash1, hash2) is False

    def test_is_content_modified_true(self) -> None:
        """Should return True when content is modified."""
        current = "sha256:" + "a" * 64
        original = "sha256:" + "b" * 64
        assert is_content_modified(current, original) is True

    def test_is_content_modified_false(self) -> None:
        """Should return False when content is unchanged."""
        same_hash = "sha256:" + "a" * 64
        assert is_content_modified(same_hash, same_hash) is False
