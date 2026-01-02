"""Tests for manifest manager."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from speckit_update.exceptions import ManifestError
from speckit_update.models import Manifest, TrackedFile
from speckit_update.services.manifest_manager import (
    ManifestManager,
    load_manifest,
    save_manifest,
)


class TestManifestManager:
    """Tests for ManifestManager class."""

    def test_exists_false_no_file(self, tmp_project: Path) -> None:
        """Should return False when manifest doesn't exist."""
        manager = ManifestManager(tmp_project)
        assert manager.exists() is False

    def test_exists_true_with_file(self, tmp_project: Path) -> None:
        """Should return True when manifest exists."""
        manager = ManifestManager(tmp_project)
        manager.manifest_path.write_text("{}")
        assert manager.exists() is True

    def test_load_returns_none_no_file(self, tmp_project: Path) -> None:
        """Should return None when file doesn't exist."""
        manager = ManifestManager(tmp_project)
        assert manager.load() is None

    def test_load_parses_valid_json(
        self,
        tmp_project: Path,
        manifest_json_data: dict[str, Any],
    ) -> None:
        """Should parse valid manifest JSON."""
        manager = ManifestManager(tmp_project)
        manager.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manager.manifest_path.write_text(json.dumps(manifest_json_data))

        result = manager.load()
        assert result is not None
        assert result.speckit_version == "v0.0.79"

    def test_load_raises_on_invalid_json(self, tmp_project: Path) -> None:
        """Should raise ManifestError for invalid JSON."""
        manager = ManifestManager(tmp_project)
        manager.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manager.manifest_path.write_text("not valid json")

        with pytest.raises(ManifestError, match="Invalid JSON"):
            manager.load()

    def test_save_creates_file(self, tmp_project: Path) -> None:
        """Should create manifest file."""
        manager = ManifestManager(tmp_project)
        manifest = Manifest(speckit_version="v0.0.79")

        manager.save(manifest)

        assert manager.manifest_path.exists()

    def test_save_creates_directories(self, tmp_path: Path) -> None:
        """Should create parent directories if needed."""
        # Use tmp_path directly (no .specify yet)
        project = tmp_path / "new_project"
        project.mkdir()
        manager = ManifestManager(project)
        manifest = Manifest(speckit_version="v0.0.79")

        manager.save(manifest)

        assert manager.manifest_path.exists()

    def test_roundtrip(self, tmp_project: Path) -> None:
        """Save then load should preserve data."""
        manager = ManifestManager(tmp_project)
        original = Manifest(
            speckit_version="v0.0.79",
            tracked_files=[
                TrackedFile(
                    path="test.md",
                    original_hash="sha256:" + "a" * 64,
                    customized=False,
                    is_official=True,
                )
            ],
        )

        manager.save(original)
        loaded = manager.load()

        assert loaded is not None
        assert loaded.speckit_version == original.speckit_version
        assert len(loaded.tracked_files) == 1
        assert loaded.tracked_files[0].path == "test.md"

    def test_load_or_create_existing(
        self,
        tmp_project: Path,
        manifest_json_data: dict[str, Any],
    ) -> None:
        """Should load existing manifest."""
        manager = ManifestManager(tmp_project)
        manager.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manager.manifest_path.write_text(json.dumps(manifest_json_data))

        result = manager.load_or_create()
        assert result.speckit_version == "v0.0.79"

    def test_load_or_create_new(self, tmp_project: Path) -> None:
        """Should create new manifest when none exists."""
        manager = ManifestManager(tmp_project)
        result = manager.load_or_create(speckit_version="v0.0.80")
        assert result.speckit_version == "v0.0.80"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_load_manifest_helper(
        self,
        tmp_project: Path,
        manifest_json_data: dict[str, Any],
    ) -> None:
        """load_manifest should work like manager.load()."""
        manifest_path = tmp_project / ".specify" / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_json_data))

        result = load_manifest(tmp_project)
        assert result is not None
        assert result.speckit_version == "v0.0.79"

    def test_save_manifest_helper(self, tmp_project: Path) -> None:
        """save_manifest should work like manager.save()."""
        manifest = Manifest(speckit_version="v0.0.79")
        save_manifest(tmp_project, manifest)

        manifest_path = tmp_project / ".specify" / "manifest.json"
        assert manifest_path.exists()
