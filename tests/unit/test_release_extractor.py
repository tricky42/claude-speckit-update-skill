"""Tests for release extractor."""

import io
import tarfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from speckit_update.models import Release
from speckit_update.services.release_extractor import (
    SPECKIT_FILES,
    ReleaseExtractor,
)


class TestReleaseExtractor:
    """Tests for ReleaseExtractor class."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock GitHub client."""
        return MagicMock()

    @pytest.fixture
    def sample_release(self) -> Release:
        """Create a sample release."""
        return Release(
            tag_name="v0.0.80",
            name="v0.0.80",
            published_at="2026-01-01T00:00:00Z",
            tarball_url="https://api.github.com/repos/github/spec-kit/tarball/v0.0.80",
            body="Release notes",
        )

    @pytest.fixture
    def sample_tarball(self, tmp_path: Path) -> bytes:
        """Create a sample tarball with SpecKit files."""
        # Create temp directory with files
        repo_dir = tmp_path / "github-spec-kit-abc123"
        repo_dir.mkdir()

        # Create some SpecKit files
        (repo_dir / ".claude" / "commands").mkdir(parents=True)
        (repo_dir / ".claude" / "commands" / "speckit.specify.md").write_text(
            "# Specify Command\n\nContent here."
        )
        (repo_dir / ".claude" / "commands" / "speckit.plan.md").write_text(
            "# Plan Command\n\nContent here."
        )

        (repo_dir / ".specify" / "memory").mkdir(parents=True)
        (repo_dir / ".specify" / "memory" / "constitution.md").write_text(
            "# Constitution\n\nRules here."
        )

        # Create tarball
        tarball_buffer = io.BytesIO()
        with tarfile.open(fileobj=tarball_buffer, mode="w:gz") as tar:
            tar.add(repo_dir, arcname=repo_dir.name)

        return tarball_buffer.getvalue()

    def test_download_and_extract(
        self,
        mock_client: MagicMock,
        sample_release: Release,
        sample_tarball: bytes,
    ) -> None:
        """Should download and extract tarball."""
        mock_client.download_tarball.return_value = sample_tarball

        extractor = ReleaseExtractor(mock_client)
        try:
            root_dir = extractor.download_and_extract(sample_release)

            assert root_dir.exists()
            assert (root_dir / ".claude" / "commands" / "speckit.specify.md").exists()
            mock_client.download_tarball.assert_called_once_with(
                sample_release.tarball_url
            )
        finally:
            extractor.cleanup()

    def test_get_file_hashes(
        self,
        mock_client: MagicMock,
        sample_release: Release,
        sample_tarball: bytes,
    ) -> None:
        """Should compute hashes for tracked files."""
        mock_client.download_tarball.return_value = sample_tarball

        extractor = ReleaseExtractor(mock_client)
        try:
            extractor.download_and_extract(sample_release)
            hashes = extractor.get_file_hashes()

            # Should have hashes for the files we created
            assert ".claude/commands/speckit.specify.md" in hashes
            assert ".claude/commands/speckit.plan.md" in hashes
            assert ".specify/memory/constitution.md" in hashes

            # Hashes should be in expected format
            for file_hash in hashes.values():
                assert file_hash.startswith("sha256:")
        finally:
            extractor.cleanup()

    def test_get_file_content(
        self,
        mock_client: MagicMock,
        sample_release: Release,
        sample_tarball: bytes,
    ) -> None:
        """Should return file content."""
        mock_client.download_tarball.return_value = sample_tarball

        extractor = ReleaseExtractor(mock_client)
        try:
            extractor.download_and_extract(sample_release)

            content = extractor.get_file_content(".claude/commands/speckit.specify.md")
            assert content is not None
            assert b"# Specify Command" in content

            # Non-existent file
            missing = extractor.get_file_content("nonexistent.md")
            assert missing is None
        finally:
            extractor.cleanup()

    def test_get_file_hashes_without_extract_raises(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Should raise if called before extract."""
        extractor = ReleaseExtractor(mock_client)

        with pytest.raises(RuntimeError, match="No release extracted"):
            extractor.get_file_hashes()

    def test_get_file_content_without_extract_raises(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Should raise if called before extract."""
        extractor = ReleaseExtractor(mock_client)

        with pytest.raises(RuntimeError, match="No release extracted"):
            extractor.get_file_content("any.md")

    def test_cleanup(
        self,
        mock_client: MagicMock,
        sample_release: Release,
        sample_tarball: bytes,
    ) -> None:
        """Should clean up temp directory."""
        mock_client.download_tarball.return_value = sample_tarball

        extractor = ReleaseExtractor(mock_client)
        root_dir = extractor.download_and_extract(sample_release)
        temp_dir = root_dir.parent

        assert temp_dir.exists()
        extractor.cleanup()
        assert not temp_dir.exists()

    def test_context_manager(
        self,
        mock_client: MagicMock,
        sample_release: Release,
        sample_tarball: bytes,
    ) -> None:
        """Should work as context manager."""
        mock_client.download_tarball.return_value = sample_tarball

        with ReleaseExtractor(mock_client) as extractor:
            root_dir = extractor.download_and_extract(sample_release)
            temp_dir = root_dir.parent
            assert temp_dir.exists()

        # After context, temp should be cleaned up
        assert not temp_dir.exists()

    def test_path_traversal_protection(
        self,
        mock_client: MagicMock,
        sample_release: Release,
    ) -> None:
        """Should reject tarballs with path traversal."""
        # Create malicious tarball with ../ path
        tarball_buffer = io.BytesIO()
        with tarfile.open(fileobj=tarball_buffer, mode="w:gz") as tar:
            # Create a malicious entry
            info = tarfile.TarInfo(name="../../../etc/passwd")
            info.size = 0
            tar.addfile(info, io.BytesIO(b""))

        mock_client.download_tarball.return_value = tarball_buffer.getvalue()

        extractor = ReleaseExtractor(mock_client)
        try:
            with pytest.raises(ValueError, match="Unsafe path"):
                extractor.download_and_extract(sample_release)
        finally:
            extractor.cleanup()


class TestSpeckitFiles:
    """Tests for SPECKIT_FILES constant."""

    def test_speckit_files_paths(self) -> None:
        """Should contain expected SpecKit file paths."""
        assert ".claude/commands/speckit.specify.md" in SPECKIT_FILES
        assert ".claude/commands/speckit.plan.md" in SPECKIT_FILES
        assert ".specify/memory/constitution.md" in SPECKIT_FILES

    def test_speckit_files_count(self) -> None:
        """Should have expected number of tracked files."""
        # Based on the SPECKIT_FILES constant in the module
        assert len(SPECKIT_FILES) == 12
