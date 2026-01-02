"""Fingerprint detection data models."""

from dataclasses import dataclass
from typing import Literal

from speckit_update.models.file_state import ConfidenceLevel


@dataclass(frozen=True)
class Fingerprint:
    """Version signature for fingerprint detection.

    Contains the expected file hashes for a specific SpecKit version,
    used to auto-detect what version is installed.
    """

    version: str
    """SpecKit version this fingerprint represents."""

    file_hashes: dict[str, str]
    """Map of relative path to expected hash."""

    @property
    def signature_files(self) -> list[str]:
        """Core files used for fast signature check.

        These 3 files are checked first for quick version detection
        covering 95%+ of installations.
        """
        return [
            ".claude/commands/speckit.specify.md",
            ".claude/commands/speckit.plan.md",
            ".specify/memory/constitution.md",
        ]

    def get_signature_hashes(self) -> dict[str, str]:
        """Get hashes for signature files only.

        Returns:
            Dict mapping signature file paths to their expected hashes.
        """
        return {
            path: hash_val
            for path, hash_val in self.file_hashes.items()
            if path in self.signature_files
        }


@dataclass(frozen=True)
class FingerprintMatch:
    """Result of version fingerprint detection.

    Produced by FingerprintDetector after analyzing project files
    against the fingerprint database.
    """

    version: str
    """Detected SpecKit version."""

    confidence: ConfidenceLevel
    """Detection confidence level."""

    match_percentage: float
    """Percentage of files matching (0.0-100.0)."""

    method: Literal["signature", "full_scan", "none"]
    """Detection method used."""

    @classmethod
    def no_match(cls) -> "FingerprintMatch":
        """Create a result indicating no version could be detected.

        Returns:
            FingerprintMatch with LOW confidence and 'none' method.
        """
        return cls(
            version="",
            confidence=ConfidenceLevel.LOW,
            match_percentage=0.0,
            method="none",
        )

    @classmethod
    def from_signature(
        cls,
        version: str,
        match_percentage: float,
    ) -> "FingerprintMatch":
        """Create a result from fast signature check.

        Args:
            version: Detected version.
            match_percentage: Percentage of signature files matched.

        Returns:
            FingerprintMatch with appropriate confidence level.
        """
        if match_percentage >= 95.0:
            confidence = ConfidenceLevel.HIGH
        elif match_percentage >= 70.0:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        return cls(
            version=version,
            confidence=confidence,
            match_percentage=match_percentage,
            method="signature",
        )

    @classmethod
    def from_full_scan(
        cls,
        version: str,
        match_percentage: float,
    ) -> "FingerprintMatch":
        """Create a result from full fingerprint scan.

        Args:
            version: Detected version.
            match_percentage: Percentage of all tracked files matched.

        Returns:
            FingerprintMatch with appropriate confidence level.
        """
        if match_percentage >= 95.0:
            confidence = ConfidenceLevel.HIGH
        elif match_percentage >= 70.0:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW

        return cls(
            version=version,
            confidence=confidence,
            match_percentage=match_percentage,
            method="full_scan",
        )
