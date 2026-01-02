"""Manifest CRUD operations.

This module handles reading and writing the .specify/manifest.json file
that tracks SpecKit installation state.
"""

import json
from pathlib import Path
from typing import Any

from speckit_update.exceptions import ManifestError
from speckit_update.models import Manifest, ManifestDict
from speckit_update.utils.paths import get_manifest_path


class ManifestManager:
    """Manages manifest.json read/write operations.

    The manifest tracks:
    - Current SpecKit version
    - File hashes for customization detection
    - Backup history
    - Custom user files
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the manifest manager.

        Args:
            project_root: Path to the project root directory.
        """
        self.project_root = project_root
        self.manifest_path = get_manifest_path(project_root)

    def exists(self) -> bool:
        """Check if manifest file exists.

        Returns:
            True if manifest.json exists.
        """
        return self.manifest_path.exists()

    def load(self) -> Manifest | None:
        """Load manifest from disk.

        Returns:
            Manifest object if file exists, None otherwise.

        Raises:
            ManifestError: If the manifest exists but can't be read/parsed.
        """
        if not self.exists():
            return None

        try:
            content = self.manifest_path.read_text(encoding="utf-8")
            data: ManifestDict = json.loads(content)
            return Manifest.from_dict(data)
        except json.JSONDecodeError as e:
            raise ManifestError(f"Invalid JSON in manifest: {e}") from e
        except KeyError as e:
            raise ManifestError(f"Missing required field in manifest: {e}") from e
        except (OSError, PermissionError) as e:
            raise ManifestError(f"Cannot read manifest: {e}") from e

    def save(self, manifest: Manifest) -> None:
        """Save manifest to disk.

        Creates parent directories if needed. Writes with pretty formatting
        for human readability.

        Args:
            manifest: The manifest to save.

        Raises:
            ManifestError: If the manifest can't be written.
        """
        try:
            # Ensure directory exists
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

            # Serialize to JSON with pretty formatting
            data = manifest.to_dict()
            content = json.dumps(data, indent=2, ensure_ascii=False)

            # Write atomically (write to temp, then rename)
            temp_path = self.manifest_path.with_suffix(".tmp")
            temp_path.write_text(content + "\n", encoding="utf-8")
            temp_path.replace(self.manifest_path)
        except (OSError, PermissionError) as e:
            raise ManifestError(f"Cannot write manifest: {e}") from e

    def load_or_create(self, speckit_version: str = "") -> Manifest:
        """Load existing manifest or create a new one.

        Args:
            speckit_version: Version to set if creating new manifest.

        Returns:
            Existing or new Manifest.
        """
        existing = self.load()
        if existing is not None:
            return existing

        # Create new manifest
        manifest = Manifest(speckit_version=speckit_version)
        return manifest

    def update_version(self, manifest: Manifest, new_version: str) -> Manifest:
        """Update manifest to new version.

        Creates a new Manifest with updated version and timestamp.

        Args:
            manifest: Current manifest.
            new_version: New SpecKit version.

        Returns:
            Updated Manifest (not saved to disk).
        """
        from datetime import datetime

        return Manifest(
            version=manifest.version,
            speckit_version=new_version,
            initialized_at=manifest.initialized_at,
            last_updated=datetime.now(),
            agent=manifest.agent,
            speckit_commands=manifest.speckit_commands,
            tracked_files=manifest.tracked_files,
            custom_files=manifest.custom_files,
            backup_history=manifest.backup_history,
        )


def load_manifest(project_root: Path) -> Manifest | None:
    """Convenience function to load manifest.

    Args:
        project_root: Path to project root.

    Returns:
        Manifest if exists, None otherwise.
    """
    manager = ManifestManager(project_root)
    return manager.load()


def save_manifest(project_root: Path, manifest: Manifest) -> None:
    """Convenience function to save manifest.

    Args:
        project_root: Path to project root.
        manifest: Manifest to save.
    """
    manager = ManifestManager(project_root)
    manager.save(manifest)
