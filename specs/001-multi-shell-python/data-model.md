# Data Model: Multi-Shell Python Support

**Feature**: 001-multi-shell-python
**Date**: 2026-01-02

## Overview

This document defines the Python type system for the SpecKit Update Skill. All types use Python 3.14+ typing features with strict mypy/pyright compatibility.

## Core Enumerations

### FileState

Represents the state of a tracked file during update analysis.

```python
from enum import Enum

class FileState(Enum):
    """State of a file relative to manifest and upstream."""

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
```

### ConfidenceLevel

Represents fingerprint detection confidence.

```python
class ConfidenceLevel(Enum):
    """Confidence level for version detection."""

    HIGH = "high"
    """95-100% match - safe to assume version."""

    MEDIUM = "medium"
    """70-94% match - likely correct but verify."""

    LOW = "low"
    """<70% match - treat all files as potentially customized."""
```

## Data Classes

### TrackedFile

Represents a file tracked in the manifest.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TrackedFile:
    """A file tracked in the manifest."""

    path: str
    """Relative path from project root (forward slashes)."""

    original_hash: str
    """Normalized SHA-256 hash in format 'sha256:{hex}'."""

    customized: bool
    """True if file content differs from original_hash."""

    is_official: bool
    """True if file is an official SpecKit command."""

    def __post_init__(self) -> None:
        if not self.original_hash.startswith("sha256:"):
            raise ValueError(f"Invalid hash format: {self.original_hash}")
```

### BackupEntry

Represents a backup history entry.

```python
from datetime import datetime

@dataclass(frozen=True)
class BackupEntry:
    """A backup in the manifest history."""

    timestamp: datetime
    """When the backup was created."""

    path: str
    """Relative path to backup directory."""

    from_version: str
    """SpecKit version before update."""

    to_version: str
    """SpecKit version after update."""
```

### Manifest

The root manifest document.

```python
from dataclasses import dataclass, field

@dataclass
class Manifest:
    """The .specify/manifest.json document."""

    version: str = "1.0"
    """Manifest schema version."""

    speckit_version: str = ""
    """Currently installed SpecKit version (e.g., 'v0.0.79')."""

    initialized_at: datetime = field(default_factory=datetime.now)
    """When manifest was first created."""

    last_updated: datetime = field(default_factory=datetime.now)
    """When manifest was last modified."""

    agent: str = "claude-code"
    """AI agent that manages this installation."""

    speckit_commands: list[str] = field(default_factory=list)
    """List of official SpecKit command filenames."""

    tracked_files: list[TrackedFile] = field(default_factory=list)
    """Files tracked for update management."""

    custom_files: list[str] = field(default_factory=list)
    """User-created files (never overwritten)."""

    backup_history: list[BackupEntry] = field(default_factory=list)
    """History of backups created."""
```

### Release

GitHub release metadata.

```python
@dataclass(frozen=True)
class Release:
    """GitHub release metadata."""

    tag_name: str
    """Version tag (e.g., 'v0.0.79')."""

    name: str
    """Release title."""

    published_at: datetime
    """Publication timestamp."""

    tarball_url: str
    """URL to download release tarball."""

    body: str = ""
    """Release notes markdown."""
```

### ConflictResult

Result of a 3-way merge operation.

```python
@dataclass(frozen=True)
class ConflictResult:
    """Result of merging conflicting file versions."""

    merged_content: str
    """The merged file content (may contain conflict markers)."""

    conflict_count: int
    """Number of conflict sections requiring manual resolution."""

    conflict_markers: list[tuple[int, int]]
    """Line ranges of conflict markers (start, end) pairs."""

    @property
    def has_conflicts(self) -> bool:
        """True if manual resolution is needed."""
        return self.conflict_count > 0
```

### Fingerprint

Version fingerprint for detection.

```python
@dataclass(frozen=True)
class Fingerprint:
    """Version signature for fingerprint detection."""

    version: str
    """SpecKit version this fingerprint represents."""

    file_hashes: dict[str, str]
    """Map of relative path to expected hash."""

    @property
    def signature_files(self) -> list[str]:
        """Core files used for fast signature check."""
        return [
            ".claude/commands/speckit.specify.md",
            ".claude/commands/speckit.plan.md",
            ".specify/memory/constitution.md",
        ]
```

### FingerprintMatch

Result of fingerprint detection.

```python
@dataclass(frozen=True)
class FingerprintMatch:
    """Result of version fingerprint detection."""

    version: str
    """Detected SpecKit version."""

    confidence: ConfidenceLevel
    """Detection confidence level."""

    match_percentage: float
    """Percentage of files matching (0.0-100.0)."""

    method: Literal["signature", "full_scan", "none"]
    """Detection method used."""
```

### FileAnalysis

Analysis result for a single file.

```python
@dataclass(frozen=True)
class FileAnalysis:
    """Analysis of a file's state during update check."""

    path: str
    """Relative file path."""

    state: FileState
    """Determined file state."""

    current_hash: str | None
    """Current file hash (None if file doesn't exist)."""

    manifest_hash: str | None
    """Hash recorded in manifest (None if not tracked)."""

    upstream_hash: str | None
    """Hash in upstream release (None if not in release)."""
```

### UpdatePlan

Aggregated update analysis.

```python
@dataclass(frozen=True)
class UpdatePlan:
    """Complete update analysis ready for execution."""

    from_version: str
    """Current SpecKit version."""

    to_version: str
    """Target SpecKit version."""

    files_to_add: list[str]
    """New files to create."""

    files_to_update: list[str]
    """Existing files to overwrite (safe)."""

    files_to_merge: list[str]
    """Files requiring conflict resolution."""

    files_to_remove: list[str]
    """Files to delete."""

    files_to_preserve: list[str]
    """Customized files to keep unchanged."""

    @property
    def has_changes(self) -> bool:
        """True if any updates are available."""
        return bool(
            self.files_to_add
            or self.files_to_update
            or self.files_to_merge
            or self.files_to_remove
        )

    @property
    def has_conflicts(self) -> bool:
        """True if manual merge resolution needed."""
        return bool(self.files_to_merge)
```

## TypedDict Definitions (JSON Serialization)

For JSON I/O compatibility with existing manifests:

```python
from typing import TypedDict

class TrackedFileDict(TypedDict):
    """JSON representation of TrackedFile."""
    path: str
    original_hash: str
    customized: bool
    is_official: bool

class BackupEntryDict(TypedDict):
    """JSON representation of BackupEntry."""
    timestamp: str  # ISO 8601 format
    path: str
    from_version: str
    to_version: str

class ManifestDict(TypedDict):
    """JSON representation of Manifest."""
    version: str
    speckit_version: str
    initialized_at: str  # ISO 8601 format
    last_updated: str    # ISO 8601 format
    agent: str
    speckit_commands: list[str]
    tracked_files: list[TrackedFileDict]
    custom_files: list[str]
    backup_history: list[BackupEntryDict]
```

## Protocol Definitions

For dependency injection and testing:

```python
from typing import Protocol

class HashCalculator(Protocol):
    """Protocol for hash calculation service."""

    def calculate_hash(self, content: bytes) -> str:
        """Calculate normalized hash for content."""
        ...

    def calculate_file_hash(self, path: Path) -> str:
        """Calculate normalized hash for file."""
        ...

class GitHubClient(Protocol):
    """Protocol for GitHub API interactions."""

    def get_latest_release(self) -> Release:
        """Fetch latest SpecKit release."""
        ...

    def get_release(self, version: str) -> Release:
        """Fetch specific SpecKit release."""
        ...

    def download_tarball(self, url: str) -> bytes:
        """Download release tarball."""
        ...

class ManifestStore(Protocol):
    """Protocol for manifest persistence."""

    def load(self) -> Manifest | None:
        """Load manifest from disk."""
        ...

    def save(self, manifest: Manifest) -> None:
        """Save manifest to disk."""
        ...
```

## Validation Rules

### Path Validation

```python
def validate_path(path: str) -> None:
    """Validate file path format."""
    if not path:
        raise ValueError("Path cannot be empty")
    if path.startswith("/") or path.startswith("\\"):
        raise ValueError("Path must be relative")
    if ".." in path:
        raise ValueError("Path cannot contain '..'")
```

### Hash Validation

```python
import re

HASH_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")

def validate_hash(hash_value: str) -> None:
    """Validate hash format."""
    if not HASH_PATTERN.match(hash_value):
        raise ValueError(f"Invalid hash format: {hash_value}")
```

### Version Validation

```python
VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")

def validate_version(version: str) -> None:
    """Validate version format."""
    if not VERSION_PATTERN.match(version):
        raise ValueError(f"Invalid version format: {version}")
```

## State Transitions

### Manifest Lifecycle

```
                    ┌─────────────┐
                    │   (none)    │
                    └──────┬──────┘
                           │ create (first run)
                           ▼
                    ┌─────────────┐
      ┌────────────►│   Active    │◄────────────┐
      │             └──────┬──────┘             │
      │                    │ update             │
      │ rollback           ▼                    │ update success
      │             ┌─────────────┐             │
      └─────────────│  Updating   ├─────────────┘
                    └──────┬──────┘
                           │ error
                           ▼
                    ┌─────────────┐
                    │  Rollback   │
                    └─────────────┘
```

### FileState Determination

```
Is file in manifest? ──No──► Is file in upstream? ──Yes──► ADD
        │                              │
        │                              No
        │                              ▼
        │                            SKIP
        Yes
        │
        ▼
Is file in upstream? ──No──► REMOVE (if not custom)
        │                    PRESERVE (if custom)
        │
        Yes
        │
        ▼
Is file customized? ──No──► Has upstream changes? ──No──► SKIP
        │                              │
        │                              Yes
        │                              ▼
        │                            UPDATE
        Yes
        │
        ▼
Has upstream changes? ──No──► PRESERVE
        │
        Yes
        │
        ▼
      MERGE
```

## Relationships

```
Manifest
    │
    ├── 1:N ──► TrackedFile
    │
    ├── 1:N ──► BackupEntry
    │
    └── 1:N ──► custom_files (strings)

Release ◄── fetched from ── GitHubClient

UpdatePlan
    │
    └── derived from ── Manifest + Release + current files

ConflictResult ◄── produced by ── MarkdownMerger
```
