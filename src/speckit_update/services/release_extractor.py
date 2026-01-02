"""Release tarball extraction and processing.

This module handles downloading, extracting, and processing
release tarballs from GitHub.
"""

import io
import tarfile
import tempfile
from pathlib import Path

from speckit_update.models import Release
from speckit_update.services.github_client import GitHubClient
from speckit_update.services.hash_utils import calculate_hash


# Official SpecKit files to track (relative paths in the repo)
SPECKIT_FILES = (
    ".claude/commands/speckit.analyze.md",
    ".claude/commands/speckit.checklist.md",
    ".claude/commands/speckit.clarify.md",
    ".claude/commands/speckit.constitution.md",
    ".claude/commands/speckit.implement.md",
    ".claude/commands/speckit.plan.md",
    ".claude/commands/speckit.specify.md",
    ".claude/commands/speckit.tasks.md",
    ".specify/memory/constitution.md",
    ".specify/templates/plan.template.md",
    ".specify/templates/spec.template.md",
    ".specify/templates/tasks.template.md",
)


class ReleaseExtractor:
    """Extracts and processes release tarballs.

    Downloads release tarballs from GitHub, extracts them to a temp
    directory, and computes hashes for all tracked files.
    """

    def __init__(self, client: GitHubClient) -> None:
        """Initialize the extractor.

        Args:
            client: GitHub client for downloading.
        """
        self.client = client
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self._extract_path: Path | None = None
        self._root_dir: Path | None = None

    def download_and_extract(self, release: Release) -> Path:
        """Download and extract a release tarball.

        Args:
            release: Release to download.

        Returns:
            Path to extracted content root directory.
        """
        # Download tarball
        tarball_data = self.client.download_tarball(release.tarball_url)

        # Create temp directory
        self._temp_dir = tempfile.TemporaryDirectory(prefix="speckit-")
        self._extract_path = Path(self._temp_dir.name)

        # Extract tarball
        with tarfile.open(fileobj=io.BytesIO(tarball_data), mode="r:gz") as tar:
            # Security: Check for path traversal
            for member in tar.getmembers():
                if member.name.startswith("/") or ".." in member.name:
                    raise ValueError(f"Unsafe path in tarball: {member.name}")
            tar.extractall(self._extract_path)

        # Find root directory (GitHub tarballs have owner-repo-hash/ prefix)
        contents = list(self._extract_path.iterdir())
        if len(contents) == 1 and contents[0].is_dir():
            self._root_dir = contents[0]
        else:
            self._root_dir = self._extract_path

        return self._root_dir

    def get_file_hashes(self) -> dict[str, str]:
        """Compute hashes for all tracked files in the extracted release.

        Returns:
            Dict mapping file paths to their hashes.

        Raises:
            RuntimeError: If no release has been extracted.
        """
        if self._root_dir is None:
            raise RuntimeError("No release extracted. Call download_and_extract first.")

        hashes: dict[str, str] = {}

        for file_path in SPECKIT_FILES:
            full_path = self._root_dir / file_path
            if full_path.exists():
                content = full_path.read_bytes()
                hashes[file_path] = calculate_hash(content)

        return hashes

    def get_file_content(self, path: str) -> bytes | None:
        """Get content of a file from the extracted release.

        Args:
            path: Relative file path.

        Returns:
            File content or None if not found.

        Raises:
            RuntimeError: If no release has been extracted.
        """
        if self._root_dir is None:
            raise RuntimeError("No release extracted. Call download_and_extract first.")

        full_path = self._root_dir / path
        if full_path.exists():
            return full_path.read_bytes()
        return None

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None
            self._extract_path = None
            self._root_dir = None

    def __enter__(self) -> "ReleaseExtractor":
        """Enter context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context manager."""
        self.cleanup()
