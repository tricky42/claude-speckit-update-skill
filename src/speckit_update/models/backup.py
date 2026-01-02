"""Backup entry data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from speckit_update.models.manifest import BackupEntryDict


@dataclass(frozen=True)
class BackupEntry:
    """A backup in the manifest history.

    Records when a backup was created and what version transition it represents.
    """

    timestamp: datetime
    """When the backup was created."""

    path: str
    """Relative path to backup directory."""

    from_version: str
    """SpecKit version before update."""

    to_version: str
    """SpecKit version after update."""

    def to_dict(self) -> "BackupEntryDict":
        """Convert to JSON-serializable dict."""
        from speckit_update.models.manifest import BackupEntryDict

        return BackupEntryDict(
            timestamp=self.timestamp.isoformat(),
            path=self.path,
            from_version=self.from_version,
            to_version=self.to_version,
        )

    @classmethod
    def from_dict(cls, data: "BackupEntryDict") -> "BackupEntry":
        """Create from JSON dict."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            path=data["path"],
            from_version=data["from_version"],
            to_version=data["to_version"],
        )
