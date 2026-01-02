"""File state and confidence level enumerations."""

from enum import Enum


class FileState(Enum):
    """State of a file relative to manifest and upstream.

    Used during update analysis to determine what action should be taken
    for each tracked file.
    """

    ADD = "add"
    """New file in upstream, not present locally."""

    REMOVE = "remove"
    """File removed from upstream, exists locally."""

    UPDATE = "update"
    """File unchanged locally, has upstream changes (safe to update)."""

    PRESERVE = "preserve"
    """File customized locally, no upstream changes (keep as-is)."""

    MERGE = "merge"
    """File customized locally AND has upstream changes (conflict)."""

    SKIP = "skip"
    """No changes needed."""


class ConfidenceLevel(Enum):
    """Confidence level for version detection.

    Used by FingerprintDetector to indicate how confident the system is
    about the detected version.
    """

    HIGH = "high"
    """95-100% match - safe to assume version."""

    MEDIUM = "medium"
    """70-94% match - likely correct but verify."""

    LOW = "low"
    """<70% match - treat all files as potentially customized."""
