"""Data models for SpecKit Update."""

from speckit_update.models.backup import BackupEntry
from speckit_update.models.conflict import ConflictResult
from speckit_update.models.file_analysis import FileAnalysis
from speckit_update.models.file_state import ConfidenceLevel, FileState
from speckit_update.models.fingerprint import Fingerprint, FingerprintMatch
from speckit_update.models.manifest import (
    BackupEntryDict,
    Manifest,
    ManifestDict,
    TrackedFile,
    TrackedFileDict,
)
from speckit_update.models.release import Release
from speckit_update.models.update_plan import UpdatePlan

__all__ = [
    # Enums
    "FileState",
    "ConfidenceLevel",
    # Dataclasses
    "TrackedFile",
    "BackupEntry",
    "Manifest",
    "Release",
    "ConflictResult",
    "Fingerprint",
    "FingerprintMatch",
    "FileAnalysis",
    "UpdatePlan",
    # TypedDicts
    "TrackedFileDict",
    "BackupEntryDict",
    "ManifestDict",
]
