"""Shared test fixtures for speckit_update tests."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from speckit_update.models import (
    BackupEntry,
    ConfidenceLevel,
    ConflictResult,
    FileAnalysis,
    FileState,
    Fingerprint,
    FingerprintMatch,
    Manifest,
    Release,
    TrackedFile,
    UpdatePlan,
)


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with .specify structure.

    Args:
        tmp_path: pytest's temporary path fixture.

    Returns:
        Path to the temporary project root.
    """
    # Create .specify directory structure
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir()
    (specify_dir / "backups").mkdir()
    (specify_dir / "memory").mkdir()

    # Create .claude/commands directory
    claude_dir = tmp_path / ".claude" / "commands"
    claude_dir.mkdir(parents=True)

    return tmp_path


@pytest.fixture
def sample_tracked_file() -> TrackedFile:
    """Create a sample TrackedFile for testing."""
    return TrackedFile(
        path=".claude/commands/speckit.specify.md",
        original_hash="sha256:" + "a" * 64,
        customized=False,
        is_official=True,
    )


@pytest.fixture
def sample_manifest() -> Manifest:
    """Create a sample Manifest for testing."""
    return Manifest(
        version="1.0",
        speckit_version="v0.0.79",
        initialized_at=datetime(2026, 1, 1, 12, 0, 0),
        last_updated=datetime(2026, 1, 2, 14, 30, 0),
        agent="claude-code",
        speckit_commands=["speckit.specify.md", "speckit.plan.md"],
        tracked_files=[
            TrackedFile(
                path=".claude/commands/speckit.specify.md",
                original_hash="sha256:" + "a" * 64,
                customized=False,
                is_official=True,
            ),
            TrackedFile(
                path=".claude/commands/speckit.plan.md",
                original_hash="sha256:" + "b" * 64,
                customized=True,
                is_official=True,
            ),
        ],
        custom_files=[".claude/commands/my-custom.md"],
        backup_history=[
            BackupEntry(
                timestamp=datetime(2026, 1, 1, 12, 0, 0),
                path=".specify/backups/2026-01-01_12-00-00",
                from_version="v0.0.78",
                to_version="v0.0.79",
            )
        ],
    )


@pytest.fixture
def sample_release() -> Release:
    """Create a sample Release for testing."""
    return Release(
        tag_name="v0.0.80",
        name="SpecKit v0.0.80",
        published_at=datetime(2026, 1, 3, 10, 0, 0),
        tarball_url="https://github.com/github/spec-kit/archive/v0.0.80.tar.gz",
        body="## What's New\n\n- Feature X\n- Bug fix Y",
    )


@pytest.fixture
def sample_update_plan() -> UpdatePlan:
    """Create a sample UpdatePlan for testing."""
    return UpdatePlan.create(
        from_version="v0.0.79",
        to_version="v0.0.80",
        add=[".claude/commands/new-command.md"],
        update=[".claude/commands/speckit.specify.md"],
        merge=[".claude/commands/speckit.plan.md"],
        preserve=[".claude/commands/custom.md"],
    )


@pytest.fixture
def sample_fingerprint_match() -> FingerprintMatch:
    """Create a sample FingerprintMatch for testing."""
    return FingerprintMatch(
        version="v0.0.79",
        confidence=ConfidenceLevel.HIGH,
        match_percentage=100.0,
        method="signature",
    )


@pytest.fixture
def manifest_json_data() -> dict[str, Any]:
    """Create sample manifest JSON data for testing serialization."""
    return {
        "version": "1.0",
        "speckit_version": "v0.0.79",
        "initialized_at": "2026-01-01T12:00:00",
        "last_updated": "2026-01-02T14:30:00",
        "agent": "claude-code",
        "speckit_commands": ["speckit.specify.md"],
        "tracked_files": [
            {
                "path": ".claude/commands/speckit.specify.md",
                "original_hash": "sha256:" + "a" * 64,
                "customized": False,
                "is_official": True,
            }
        ],
        "custom_files": [],
        "backup_history": [],
    }
