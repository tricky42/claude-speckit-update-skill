"""Tests for path utilities."""

from pathlib import Path

from speckit_update.utils.paths import (
    ensure_forward_slashes,
    get_backup_dir,
    get_manifest_path,
    get_specify_dir,
    normalize_path,
    paths_equal,
    to_relative_path,
)


class TestNormalizePath:
    """Tests for path normalization."""

    def test_forward_slashes(self) -> None:
        """Should convert backslashes to forward slashes."""
        assert "/" in normalize_path("foo\\bar\\baz")
        assert "\\" not in normalize_path("foo\\bar\\baz")

    def test_lowercase(self) -> None:
        """Should convert to lowercase."""
        result = normalize_path("FOO/Bar/BAZ.md")
        assert result == result.lower()

    def test_path_object(self) -> None:
        """Should accept Path objects."""
        result = normalize_path(Path("foo/bar"))
        assert isinstance(result, str)


class TestPathsEqual:
    """Tests for case-insensitive path comparison."""

    def test_same_path(self) -> None:
        """Identical paths should be equal."""
        assert paths_equal("foo/bar.md", "foo/bar.md") is True

    def test_case_insensitive(self) -> None:
        """Paths differing only in case should be equal."""
        assert paths_equal("FOO/bar.md", "foo/BAR.md") is True
        assert paths_equal("Foo/Bar/Baz.md", "foo/bar/baz.md") is True

    def test_different_paths(self) -> None:
        """Different paths should not be equal."""
        assert paths_equal("foo/bar.md", "foo/baz.md") is False

    def test_slash_normalization(self) -> None:
        """Backslashes and forward slashes should be treated equally."""
        assert paths_equal("foo\\bar.md", "foo/bar.md") is True
        assert paths_equal("foo\\Bar.md", "FOO/bar.md") is True

    def test_path_objects(self) -> None:
        """Should accept Path objects."""
        assert paths_equal(Path("foo/bar"), Path("FOO/BAR")) is True


class TestToRelativePath:
    """Tests for converting to relative paths."""

    def test_relative_conversion(self, tmp_path: Path) -> None:
        """Should convert absolute to relative path."""
        file_path = tmp_path / "foo" / "bar.md"
        result = to_relative_path(file_path, tmp_path)
        assert result == "foo/bar.md"

    def test_forward_slashes(self, tmp_path: Path) -> None:
        """Result should use forward slashes."""
        file_path = tmp_path / "foo" / "bar" / "baz.md"
        result = to_relative_path(file_path, tmp_path)
        assert "\\" not in result
        assert "/" in result


class TestEnsureForwardSlashes:
    """Tests for forward slash conversion."""

    def test_backslash_conversion(self) -> None:
        """Should convert backslashes."""
        assert ensure_forward_slashes("foo\\bar\\baz") == "foo/bar/baz"

    def test_mixed_slashes(self) -> None:
        """Should handle mixed slashes."""
        assert ensure_forward_slashes("foo\\bar/baz") == "foo/bar/baz"

    def test_no_change_needed(self) -> None:
        """Should not change forward slashes."""
        assert ensure_forward_slashes("foo/bar/baz") == "foo/bar/baz"


class TestPathHelpers:
    """Tests for path helper functions."""

    def test_get_manifest_path(self, tmp_path: Path) -> None:
        """Should return correct manifest path."""
        result = get_manifest_path(tmp_path)
        assert result == tmp_path / ".specify" / "manifest.json"

    def test_get_backup_dir(self, tmp_path: Path) -> None:
        """Should return correct backup directory path."""
        result = get_backup_dir(tmp_path)
        assert result == tmp_path / ".specify" / "backups"

    def test_get_specify_dir(self, tmp_path: Path) -> None:
        """Should return correct .specify directory path."""
        result = get_specify_dir(tmp_path)
        assert result == tmp_path / ".specify"
