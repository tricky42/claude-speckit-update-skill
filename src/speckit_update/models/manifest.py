"""Manifest and TrackedFile data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict


class TrackedFileDict(TypedDict):
    """JSON representation of TrackedFile."""

    path: str
    original_hash: str
    customized: bool
    is_official: bool


class BackupEntryDict(TypedDict):
    """JSON representation of BackupEntry."""

    timestamp: str  # ISO 8601 format
    path: str
    from_version: str
    to_version: str


class ManifestDict(TypedDict):
    """JSON representation of Manifest."""

    version: str
    speckit_version: str
    initialized_at: str  # ISO 8601 format
    last_updated: str  # ISO 8601 format
    agent: str
    speckit_commands: list[str]
    tracked_files: list[TrackedFileDict]
    custom_files: list[str]
    backup_history: list[BackupEntryDict]


@dataclass(frozen=True)
class TrackedFile:
    """A file tracked in the manifest.

    Represents a single file that the update system tracks for changes.
    The hash is used to detect customizations.
    """

    path: str
    """Relative path from project root (forward slashes)."""

    original_hash: str
    """Normalized SHA-256 hash in format 'sha256:{hex}'."""

    customized: bool
    """True if file content differs from original_hash."""

    is_official: bool
    """True if file is an official SpecKit command."""

    def __post_init__(self) -> None:
        """Validate hash format on creation."""
        if not self.original_hash.startswith("sha256:"):
            raise ValueError(f"Invalid hash format: {self.original_hash}")

    def to_dict(self) -> TrackedFileDict:
        """Convert to JSON-serializable dict."""
        return TrackedFileDict(
            path=self.path,
            original_hash=self.original_hash,
            customized=self.customized,
            is_official=self.is_official,
        )

    @classmethod
    def from_dict(cls, data: TrackedFileDict) -> "TrackedFile":
        """Create from JSON dict."""
        return cls(
            path=data["path"],
            original_hash=data["original_hash"],
            customized=data["customized"],
            is_official=data["is_official"],
        )


@dataclass
class Manifest:
    """The .specify/manifest.json document.

    Root document tracking SpecKit installation state, file hashes,
    and backup history.
    """

    version: str = "1.0"
    """Manifest schema version."""

    speckit_version: str = ""
    """Currently installed SpecKit version (e.g., 'v0.0.79')."""

    initialized_at: datetime = field(default_factory=datetime.now)
    """When manifest was first created."""

    last_updated: datetime = field(default_factory=datetime.now)
    """When manifest was last modified."""

    agent: str = "claude-code"
    """AI agent that manages this installation."""

    speckit_commands: list[str] = field(default_factory=list)
    """List of official SpecKit command filenames."""

    tracked_files: list[TrackedFile] = field(default_factory=list)
    """Files tracked for update management."""

    custom_files: list[str] = field(default_factory=list)
    """User-created files (never overwritten)."""

    backup_history: list["BackupEntry"] = field(default_factory=list)
    """History of backups created."""

    def to_dict(self) -> ManifestDict:
        """Convert to JSON-serializable dict."""

        return ManifestDict(
            version=self.version,
            speckit_version=self.speckit_version,
            initialized_at=self.initialized_at.isoformat(),
            last_updated=self.last_updated.isoformat(),
            agent=self.agent,
            speckit_commands=self.speckit_commands,
            tracked_files=[f.to_dict() for f in self.tracked_files],
            custom_files=self.custom_files,
            backup_history=[b.to_dict() for b in self.backup_history],
        )

    @classmethod
    def from_dict(cls, data: ManifestDict) -> "Manifest":
        """Create from JSON dict."""
        from speckit_update.models.backup import BackupEntry

        return cls(
            version=data["version"],
            speckit_version=data["speckit_version"],
            initialized_at=datetime.fromisoformat(data["initialized_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            agent=data["agent"],
            speckit_commands=data["speckit_commands"],
            tracked_files=[TrackedFile.from_dict(f) for f in data["tracked_files"]],
            custom_files=data["custom_files"],
            backup_history=[BackupEntry.from_dict(b) for b in data["backup_history"]],
        )


# Import BackupEntry type for forward reference
from speckit_update.models.backup import BackupEntry as BackupEntry  # noqa: E402, F401
