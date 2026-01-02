"""Tests for backup manager."""

from datetime import datetime
from pathlib import Path

import pytest

from speckit_update.exceptions import RollbackError
from speckit_update.models import BackupEntry, Manifest, TrackedFile
from speckit_update.services.backup_manager import (
    BackupManager,
    create_backup,
    restore_latest_backup,
)


class TestBackupManager:
    """Tests for BackupManager class."""

    @pytest.fixture
    def project_with_files(self, tmp_project: Path) -> Path:
        """Create a project with some tracked files."""
        # Create a tracked file
        commands_dir = tmp_project / ".claude" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        (commands_dir / "test.md").write_text("# Test content")

        # Create manifest
        manifest_path = tmp_project / ".specify" / "manifest.json"
        manifest_path.write_text('{"version": "1.0"}')

        return tmp_project

    def test_create_backup(self, project_with_files: Path) -> None:
        """Should create backup directory with files."""
        manifest = Manifest(
            speckit_version="v0.0.79",
            tracked_files=[
                TrackedFile(
                    path=".claude/commands/test.md",
                    original_hash="sha256:" + "a" * 64,
                    customized=False,
                    is_official=True,
                ),
            ],
        )

        manager = BackupManager(project_with_files)
        backup = manager.create_backup(manifest, "v0.0.80")

        assert backup.from_version == "v0.0.79"
        assert backup.to_version == "v0.0.80"
        assert backup.path.startswith(".specify/backups/")

        # Verify backup directory exists
        backup_path = project_with_files / backup.path
        assert backup_path.exists()

        # Verify file was copied
        backed_up_file = backup_path / ".claude" / "commands" / "test.md"
        assert backed_up_file.exists()
        assert backed_up_file.read_text() == "# Test content"

    def test_restore_backup(self, project_with_files: Path) -> None:
        """Should restore files from backup."""
        manifest = Manifest(
            speckit_version="v0.0.79",
            tracked_files=[
                TrackedFile(
                    path=".claude/commands/test.md",
                    original_hash="sha256:" + "a" * 64,
                    customized=False,
                    is_official=True,
                ),
            ],
        )

        manager = BackupManager(project_with_files)
        backup = manager.create_backup(manifest, "v0.0.80")

        # Modify the original file
        original_file = project_with_files / ".claude" / "commands" / "test.md"
        original_file.write_text("# Modified content")

        # Restore
        manager.restore_backup(backup)

        # Verify restored
        assert original_file.read_text() == "# Test content"

    def test_restore_nonexistent_backup_raises(self, tmp_project: Path) -> None:
        """Should raise RollbackError for missing backup."""
        manager = BackupManager(tmp_project)
        fake_backup = BackupEntry(
            timestamp=datetime.now(),
            path=".specify/backups/nonexistent",
            from_version="v0.0.79",
            to_version="v0.0.80",
        )

        with pytest.raises(RollbackError, match="not found"):
            manager.restore_backup(fake_backup)

    def test_get_latest_backup(self) -> None:
        """Should return most recent backup."""
        older = BackupEntry(
            timestamp=datetime(2026, 1, 1),
            path=".specify/backups/older",
            from_version="v0.0.78",
            to_version="v0.0.79",
        )
        newer = BackupEntry(
            timestamp=datetime(2026, 1, 2),
            path=".specify/backups/newer",
            from_version="v0.0.79",
            to_version="v0.0.80",
        )

        manifest = Manifest(backup_history=[older, newer])
        manager = BackupManager(Path("/tmp"))

        result = manager.get_latest_backup(manifest)
        assert result == newer

    def test_get_latest_backup_empty(self) -> None:
        """Should return None when no backups."""
        manifest = Manifest()
        manager = BackupManager(Path("/tmp"))

        result = manager.get_latest_backup(manifest)
        assert result is None

    def test_cleanup_old_backups(self, tmp_project: Path) -> None:
        """Should remove backups exceeding retention limit."""
        # Create 6 backup directories
        backups: list[BackupEntry] = []
        for i in range(6):
            backup_path = tmp_project / ".specify" / "backups" / f"backup_{i}"
            backup_path.mkdir(parents=True)
            (backup_path / "test.txt").write_text(f"backup {i}")

            backups.append(BackupEntry(
                timestamp=datetime(2026, 1, i + 1),
                path=f".specify/backups/backup_{i}",
                from_version=f"v0.0.{78 + i}",
                to_version=f"v0.0.{79 + i}",
            ))

        manifest = Manifest(backup_history=backups)
        manager = BackupManager(tmp_project)

        removed = manager.cleanup_old_backups(manifest)

        # Should remove oldest backup (index 0)
        assert len(removed) == 1
        assert "backup_0" in removed[0]


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_backup_helper(self, tmp_project: Path) -> None:
        """create_backup should work like manager.create_backup()."""
        (tmp_project / ".claude" / "commands").mkdir(parents=True, exist_ok=True)
        (tmp_project / ".claude" / "commands" / "test.md").write_text("test")

        manifest = Manifest(
            speckit_version="v0.0.79",
            tracked_files=[
                TrackedFile(
                    path=".claude/commands/test.md",
                    original_hash="sha256:" + "a" * 64,
                    customized=False,
                    is_official=True,
                ),
            ],
        )

        backup = create_backup(tmp_project, manifest, "v0.0.80")
        assert backup.from_version == "v0.0.79"
