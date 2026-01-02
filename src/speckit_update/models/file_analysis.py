"""File analysis data model."""

from dataclasses import dataclass

from speckit_update.models.file_state import FileState


@dataclass(frozen=True)
class FileAnalysis:
    """Analysis of a file's state during update check.

    Produced by ConflictDetector for each tracked file, containing
    the determined state and all relevant hash values.
    """

    path: str
    """Relative file path."""

    state: FileState
    """Determined file state."""

    current_hash: str | None
    """Current file hash (None if file doesn't exist)."""

    manifest_hash: str | None
    """Hash recorded in manifest (None if not tracked)."""

    upstream_hash: str | None
    """Hash in upstream release (None if not in release)."""

    @property
    def is_customized(self) -> bool:
        """True if file has been modified from original."""
        if self.current_hash is None or self.manifest_hash is None:
            return False
        return self.current_hash != self.manifest_hash

    @property
    def has_upstream_changes(self) -> bool:
        """True if upstream has changes since last update."""
        if self.manifest_hash is None or self.upstream_hash is None:
            return False
        return self.manifest_hash != self.upstream_hash

    @property
    def requires_action(self) -> bool:
        """True if this file requires any action during update."""
        return self.state not in (FileState.SKIP, FileState.PRESERVE)
