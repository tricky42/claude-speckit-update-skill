"""Tests for validation utilities."""

import pytest

from speckit_update.utils.validation import (
    is_valid_hash,
    is_valid_path,
    is_valid_version,
    validate_hash,
    validate_path,
    validate_version,
)


class TestValidatePath:
    """Tests for path validation."""

    def test_valid_relative_path(self) -> None:
        """Should accept valid relative paths."""
        validate_path(".claude/commands/test.md")
        validate_path("src/file.py")
        validate_path("simple.txt")

    def test_empty_path_raises(self) -> None:
        """Should reject empty paths."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_path("")

    def test_absolute_path_raises(self) -> None:
        """Should reject absolute paths."""
        with pytest.raises(ValueError, match="must be relative"):
            validate_path("/etc/passwd")
        with pytest.raises(ValueError, match="must be relative"):
            validate_path("\\Windows\\System32")

    def test_parent_traversal_raises(self) -> None:
        """Should reject paths with parent traversal."""
        with pytest.raises(ValueError, match="cannot contain"):
            validate_path("../etc/passwd")
        with pytest.raises(ValueError, match="cannot contain"):
            validate_path("foo/../bar")

    def test_null_byte_raises(self) -> None:
        """Should reject paths with null bytes (security)."""
        with pytest.raises(ValueError, match="null bytes"):
            validate_path("file\x00.txt")

    def test_is_valid_path_helper(self) -> None:
        """Helper should return bool without raising."""
        assert is_valid_path("valid/path.md") is True
        assert is_valid_path("../invalid") is False
        assert is_valid_path("") is False


class TestValidateHash:
    """Tests for hash validation."""

    def test_valid_sha256_hash(self) -> None:
        """Should accept valid sha256 hashes."""
        validate_hash("sha256:" + "a" * 64)
        validate_hash("sha256:" + "0" * 64)
        validate_hash("sha256:" + "abcdef0123456789" * 4)

    def test_empty_hash_raises(self) -> None:
        """Should reject empty hashes."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_hash("")

    def test_wrong_prefix_raises(self) -> None:
        """Should reject non-sha256 prefixes."""
        with pytest.raises(ValueError, match="Invalid hash format"):
            validate_hash("md5:" + "a" * 32)
        with pytest.raises(ValueError, match="Invalid hash format"):
            validate_hash("sha1:" + "a" * 40)

    def test_wrong_length_raises(self) -> None:
        """Should reject wrong hash lengths."""
        with pytest.raises(ValueError, match="Invalid hash format"):
            validate_hash("sha256:" + "a" * 63)  # Too short
        with pytest.raises(ValueError, match="Invalid hash format"):
            validate_hash("sha256:" + "a" * 65)  # Too long

    def test_invalid_hex_raises(self) -> None:
        """Should reject non-hex characters."""
        with pytest.raises(ValueError, match="Invalid hash format"):
            validate_hash("sha256:" + "g" * 64)  # 'g' is not hex

    def test_is_valid_hash_helper(self) -> None:
        """Helper should return bool without raising."""
        assert is_valid_hash("sha256:" + "a" * 64) is True
        assert is_valid_hash("invalid") is False
        assert is_valid_hash("") is False


class TestValidateVersion:
    """Tests for version validation."""

    def test_valid_versions(self) -> None:
        """Should accept valid semantic versions with 'v' prefix."""
        validate_version("v0.0.1")
        validate_version("v1.2.3")
        validate_version("v0.0.79")
        validate_version("v10.20.30")

    def test_empty_version_raises(self) -> None:
        """Should reject empty versions."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_version("")

    def test_no_v_prefix_raises(self) -> None:
        """Should reject versions without 'v' prefix."""
        with pytest.raises(ValueError, match="Invalid version format"):
            validate_version("0.0.1")
        with pytest.raises(ValueError, match="Invalid version format"):
            validate_version("1.2.3")

    def test_wrong_format_raises(self) -> None:
        """Should reject invalid version formats."""
        with pytest.raises(ValueError, match="Invalid version format"):
            validate_version("v1")
        with pytest.raises(ValueError, match="Invalid version format"):
            validate_version("v1.2")
        with pytest.raises(ValueError, match="Invalid version format"):
            validate_version("v1.2.3.4")

    def test_is_valid_version_helper(self) -> None:
        """Helper should return bool without raising."""
        assert is_valid_version("v0.0.79") is True
        assert is_valid_version("0.0.79") is False
        assert is_valid_version("") is False
