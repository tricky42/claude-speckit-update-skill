"""Automatic version detection via fingerprinting.

This module detects the installed SpecKit version by comparing
file hashes against a database of known version signatures.
"""

import json
from pathlib import Path

from speckit_update.models import Fingerprint, FingerprintMatch
from speckit_update.services.hash_utils import calculate_file_hash


class FingerprintDetector:
    """Detects installed SpecKit version via fingerprinting.

    Uses a two-phase approach:
    1. Fast signature check (3 core files) - covers 95%+ of cases
    2. Full fingerprint scan (all tracked files) - fallback for edge cases
    """

    # Core signature files for fast detection
    SIGNATURE_FILES = [
        ".claude/commands/speckit.specify.md",
        ".claude/commands/speckit.plan.md",
        ".specify/memory/constitution.md",
    ]

    def __init__(self, project_root: Path) -> None:
        """Initialize the detector.

        Args:
            project_root: Path to project root.
        """
        self.project_root = project_root
        self._fingerprints: dict[str, Fingerprint] | None = None

    def load_fingerprints(self) -> dict[str, Fingerprint]:
        """Load fingerprint database from bundled JSON.

        Returns:
            Dict mapping version to Fingerprint.
        """
        if self._fingerprints is not None:
            return self._fingerprints

        # Load from bundled data file
        data_path = Path(__file__).parent.parent / "data" / "speckit-fingerprints.json"

        if not data_path.exists():
            self._fingerprints = {}
            return self._fingerprints

        try:
            with open(data_path, encoding="utf-8") as f:
                data = json.load(f)

            self._fingerprints = {}
            versions_data = data.get("versions", {})

            for version, hashes in versions_data.items():
                if isinstance(hashes, dict):
                    self._fingerprints[version] = Fingerprint(
                        version=version,
                        file_hashes=hashes,
                    )

            return self._fingerprints

        except (json.JSONDecodeError, OSError):
            self._fingerprints = {}
            return self._fingerprints

    def detect_version_fast(self) -> FingerprintMatch | None:
        """Attempt fast version detection using signature files.

        Checks only the 3 core signature files for quick detection.
        Covers 95%+ of installations.

        Returns:
            FingerprintMatch if high-confidence match found, None otherwise.
        """
        fingerprints = self.load_fingerprints()

        if not fingerprints:
            return None

        # Calculate hashes for signature files
        current_hashes: dict[str, str] = {}
        for file_path in self.SIGNATURE_FILES:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    current_hashes[file_path] = calculate_file_hash(full_path)
                except OSError:
                    continue

        if not current_hashes:
            return None

        # Check each version for signature match
        best_match: tuple[str, float] | None = None

        for version, fingerprint in fingerprints.items():
            matches = 0
            total = 0

            for sig_file in self.SIGNATURE_FILES:
                if sig_file in fingerprint.file_hashes:
                    total += 1
                    if (
                        current_hashes.get(sig_file)
                        == fingerprint.file_hashes[sig_file]
                    ):
                        matches += 1

            if total > 0:
                match_pct = (matches / total) * 100
                if match_pct == 100.0:
                    # Perfect signature match
                    return FingerprintMatch.from_signature(version, match_pct)
                elif best_match is None or match_pct > best_match[1]:
                    best_match = (version, match_pct)

        # Return best partial match if above threshold
        if best_match and best_match[1] >= 70.0:
            return FingerprintMatch.from_signature(best_match[0], best_match[1])

        return None

    def detect_version_full(self) -> FingerprintMatch:
        """Perform full fingerprint scan of all tracked files.

        Checks all files in the fingerprint database for comprehensive
        version detection. Used when fast detection fails.

        Returns:
            FingerprintMatch with best match or no_match result.
        """
        fingerprints = self.load_fingerprints()

        if not fingerprints:
            return FingerprintMatch.no_match()

        # Calculate hashes for all existing files that might be tracked
        all_files = self._find_speckit_files()
        current_hashes: dict[str, str] = {}

        for file_path in all_files:
            try:
                current_hashes[file_path] = calculate_file_hash(
                    self.project_root / file_path
                )
            except OSError:
                continue

        if not current_hashes:
            return FingerprintMatch.no_match()

        # Score each version
        best_match: tuple[str, float] | None = None

        for version, fingerprint in fingerprints.items():
            matches = 0
            total = len(fingerprint.file_hashes)

            if total == 0:
                continue

            for file_path, expected_hash in fingerprint.file_hashes.items():
                if current_hashes.get(file_path) == expected_hash:
                    matches += 1

            match_pct = (matches / total) * 100

            if best_match is None or match_pct > best_match[1]:
                best_match = (version, match_pct)

        if best_match and best_match[1] >= 50.0:
            return FingerprintMatch.from_full_scan(best_match[0], best_match[1])

        return FingerprintMatch.no_match()

    def detect_version(self) -> FingerprintMatch:
        """Detect installed version using best available method.

        Tries fast signature check first, falls back to full scan.

        Returns:
            FingerprintMatch with detection result.
        """
        # Try fast detection first
        fast_result = self.detect_version_fast()
        if fast_result is not None:
            return fast_result

        # Fall back to full scan
        return self.detect_version_full()

    def _find_speckit_files(self) -> list[str]:
        """Find all potential SpecKit files in project.

        Returns:
            List of relative file paths.
        """
        files: list[str] = []

        # Check .claude/commands/
        commands_dir = self.project_root / ".claude" / "commands"
        if commands_dir.exists():
            for f in commands_dir.glob("speckit.*.md"):
                files.append(f".claude/commands/{f.name}")

        # Check .specify/
        specify_dir = self.project_root / ".specify"
        if specify_dir.exists():
            # Check memory/
            memory_dir = specify_dir / "memory"
            if memory_dir.exists():
                for f in memory_dir.glob("*.md"):
                    files.append(f".specify/memory/{f.name}")

            # Check templates/
            templates_dir = specify_dir / "templates"
            if templates_dir.exists():
                for f in templates_dir.glob("*.md"):
                    files.append(f".specify/templates/{f.name}")

        return files


def detect_version(project_root: Path) -> FingerprintMatch:
    """Convenience function to detect SpecKit version.

    Args:
        project_root: Path to project root.

    Returns:
        FingerprintMatch with detection result.
    """
    detector = FingerprintDetector(project_root)
    return detector.detect_version()
