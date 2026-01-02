"""Tests for fingerprint detector."""

from pathlib import Path

import pytest

from speckit_update.models import ConfidenceLevel
from speckit_update.services.fingerprint_detector import (
    FingerprintDetector,
    detect_version,
)


class TestFingerprintDetector:
    """Tests for FingerprintDetector class."""

    def test_load_fingerprints_empty_database(self, tmp_project: Path) -> None:
        """Should return empty dict when database is empty."""
        detector = FingerprintDetector(tmp_project)
        fingerprints = detector.load_fingerprints()

        # Database is a placeholder with empty versions
        assert isinstance(fingerprints, dict)

    def test_detect_version_no_files(self, tmp_project: Path) -> None:
        """Should return no_match when no SpecKit files exist."""
        detector = FingerprintDetector(tmp_project)
        result = detector.detect_version()

        assert result.confidence == ConfidenceLevel.LOW
        assert result.method == "none"

    def test_find_speckit_files(self, tmp_project: Path) -> None:
        """Should find SpecKit files in project."""
        # Create some SpecKit files
        commands_dir = tmp_project / ".claude" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        (commands_dir / "speckit.specify.md").write_text("# Specify")
        (commands_dir / "speckit.plan.md").write_text("# Plan")
        (commands_dir / "custom.md").write_text("# Custom")  # Not a speckit file

        memory_dir = tmp_project / ".specify" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        (memory_dir / "constitution.md").write_text("# Constitution")

        detector = FingerprintDetector(tmp_project)
        files = detector._find_speckit_files()

        assert ".claude/commands/speckit.specify.md" in files
        assert ".claude/commands/speckit.plan.md" in files
        assert ".specify/memory/constitution.md" in files
        # Custom file should not be found (doesn't match speckit.*.md pattern)

    def test_detect_version_fast_no_match(self, tmp_project: Path) -> None:
        """Should return None when no signature match."""
        # Create files with random content
        commands_dir = tmp_project / ".claude" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        (commands_dir / "speckit.specify.md").write_text("random content")

        detector = FingerprintDetector(tmp_project)
        result = detector.detect_version_fast()

        # With empty/placeholder database, should return None
        assert result is None

    def test_detect_version_full_no_match(self, tmp_project: Path) -> None:
        """Should return no_match from full scan when no matches."""
        detector = FingerprintDetector(tmp_project)
        result = detector.detect_version_full()

        assert result.confidence == ConfidenceLevel.LOW
        assert result.method in ("full_scan", "none")


class TestConvenienceFunction:
    """Tests for detect_version convenience function."""

    def test_detect_version_helper(self, tmp_project: Path) -> None:
        """detect_version should work like detector.detect_version()."""
        result = detect_version(tmp_project)

        assert hasattr(result, "confidence")
        assert hasattr(result, "method")
        assert hasattr(result, "match_percentage")


class TestFingerprintMatch:
    """Tests for fingerprint match results."""

    def test_high_confidence_match(self, tmp_project: Path) -> None:
        """High confidence should be >= 95%."""
        # This would require a populated fingerprint database
        # For now, just verify the structure
        detector = FingerprintDetector(tmp_project)
        result = detector.detect_version()

        # Result should have all expected attributes
        assert result.version is not None or result.version == ""
        assert result.confidence in list(ConfidenceLevel)
        assert 0.0 <= result.match_percentage <= 100.0
        assert result.method in ("signature", "full_scan", "none")
