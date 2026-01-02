"""Backup and restore operations.

This module handles creating timestamped backups before updates
and restoring from backups when rollback is needed.
"""

import shutil
from datetime import datetime
from pathlib import Path

from speckit_update.exceptions import RollbackError, SpecKitError
from speckit_update.models import BackupEntry, Manifest
from speckit_update.utils.paths import get_backup_dir


class BackupManager:
    """Manages backup creation and restoration.

    Creates timestamped backup directories containing all tracked files
    before any modification. Supports rollback to most recent backup.
    """

    MAX_BACKUPS = 5  # Retention limit

    def __init__(self, project_root: Path) -> None:
        """Initialize the backup manager.

        Args:
            project_root: Path to project root.
        """
        self.project_root = project_root
        self.backup_dir = get_backup_dir(project_root)

    def create_backup(
        self,
        manifest: Manifest,
        to_version: str,
    ) -> BackupEntry:
        """Create a timestamped backup of all tracked files.

        Args:
            manifest: Current manifest with tracked files.
            to_version: Target version for the update.

        Returns:
            BackupEntry with backup metadata.

        Raises:
            SpecKitError: If backup creation fails.
        """
        timestamp = datetime.now()
        backup_name = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = self.backup_dir / backup_name

        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)

            # Copy all tracked files
            for tracked_file in manifest.tracked_files:
                source = self.project_root / tracked_file.path
                if source.exists():
                    dest = backup_path / tracked_file.path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)

            # Also backup manifest itself
            manifest_source = self.project_root / ".specify" / "manifest.json"
            if manifest_source.exists():
                manifest_dest = backup_path / ".specify" / "manifest.json"
                manifest_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(manifest_source, manifest_dest)

            return BackupEntry(
                timestamp=timestamp,
                path=f".specify/backups/{backup_name}",
                from_version=manifest.speckit_version,
                to_version=to_version,
            )

        except OSError as e:
            raise SpecKitError(f"Failed to create backup: {e}") from e

    def restore_backup(self, backup: BackupEntry) -> None:
        """Restore files from a backup.

        Args:
            backup: The backup entry to restore from.

        Raises:
            RollbackError: If restore fails.
        """
        backup_path = self.project_root / backup.path

        if not backup_path.exists():
            raise RollbackError(f"Backup directory not found: {backup.path}")

        try:
            # Restore all files from backup
            for item in backup_path.rglob("*"):
                if item.is_file():
                    # Calculate relative path from backup
                    rel_path = item.relative_to(backup_path)
                    dest = self.project_root / rel_path

                    # Create parent directories
                    dest.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file back
                    shutil.copy2(item, dest)

        except OSError as e:
            raise RollbackError(f"Failed to restore backup: {e}") from e

    def get_latest_backup(self, manifest: Manifest) -> BackupEntry | None:
        """Get the most recent backup from manifest history.

        Args:
            manifest: Manifest containing backup history.

        Returns:
            Most recent BackupEntry or None if no backups exist.
        """
        if not manifest.backup_history:
            return None

        # Sort by timestamp descending
        sorted_backups = sorted(
            manifest.backup_history,
            key=lambda b: b.timestamp,
            reverse=True,
        )
        return sorted_backups[0]

    def cleanup_old_backups(self, manifest: Manifest) -> list[str]:
        """Remove old backups exceeding retention limit.

        Keeps the MAX_BACKUPS most recent backups.

        Args:
            manifest: Manifest containing backup history.

        Returns:
            List of removed backup paths.
        """
        if len(manifest.backup_history) <= self.MAX_BACKUPS:
            return []

        # Sort by timestamp descending
        sorted_backups = sorted(
            manifest.backup_history,
            key=lambda b: b.timestamp,
            reverse=True,
        )

        # Identify backups to remove
        backups_to_remove = sorted_backups[self.MAX_BACKUPS:]
        removed_paths: list[str] = []

        for backup in backups_to_remove:
            backup_path = self.project_root / backup.path
            if backup_path.exists():
                try:
                    shutil.rmtree(backup_path)
                    removed_paths.append(backup.path)
                except OSError:
                    # Log but don't fail if cleanup fails
                    pass

        return removed_paths

    def list_backups(self) -> list[Path]:
        """List all backup directories.

        Returns:
            List of backup directory paths.
        """
        if not self.backup_dir.exists():
            return []

        return sorted(
            [d for d in self.backup_dir.iterdir() if d.is_dir()],
            key=lambda p: p.name,
            reverse=True,
        )


def create_backup(
    project_root: Path,
    manifest: Manifest,
    to_version: str,
) -> BackupEntry:
    """Convenience function to create a backup.

    Args:
        project_root: Path to project root.
        manifest: Current manifest.
        to_version: Target version.

    Returns:
        BackupEntry for the created backup.
    """
    manager = BackupManager(project_root)
    return manager.create_backup(manifest, to_version)


def restore_latest_backup(
    project_root: Path,
    manifest: Manifest,
) -> BackupEntry | None:
    """Convenience function to restore the latest backup.

    Args:
        project_root: Path to project root.
        manifest: Manifest containing backup history.

    Returns:
        Restored BackupEntry or None if no backups.
    """
    manager = BackupManager(project_root)
    backup = manager.get_latest_backup(manifest)

    if backup is None:
        return None

    manager.restore_backup(backup)
    return backup
