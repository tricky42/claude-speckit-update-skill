# Implementation Plan: Multi-Shell Python Support

**Branch**: `001-multi-shell-python` | **Date**: 2026-01-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-multi-shell-python/spec.md`

## Summary

Rewrite the SpecKit Update Skill from PowerShell to modern Python (>= 3.14) with full type hints, enabling cross-platform support on macOS, Linux, and Windows. The Python implementation fully replaces PowerShell with no wrapper or dual implementation needed. Users interact via the `/speckit-update` command in Claude Code, which will invoke Python instead of PowerShell.

## Technical Context

**Language/Version**: Python 3.14+ (required for modern typing features: TypedDict, dataclasses, Literal, Protocol)
**Primary Dependencies**: Standard library only + `requests` for HTTP (NFR-006)
**Storage**: JSON files (manifest.json in `.specify/`), local file system for backups
**Testing**: pytest with pytest-cov for coverage reporting (>= 90% target)
**Target Platform**: Windows 10+, macOS 12+, Linux (Ubuntu 20.04+, Debian 11+, Fedora 36+)
**Project Type**: Single CLI application
**Performance Goals**: <2s check-only, <5s full update (excluding network)
**Constraints**: Zero external dependencies beyond requests, offline-capable for non-network operations
**Scale/Scope**: Single-project updates, ~50 tracked files typical, ~5 backup retention

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Modular Architecture | **ADAPT** | Python modules replace PowerShell modules; same responsibility split |
| II. Fail-Fast with Rollback | **PASS** | Preserved: backup before modify, auto-rollback on error |
| III. Customization Detection via Normalized Hashing | **PASS** | Same algorithm: CRLF→LF, trim whitespace, remove BOM, SHA-256 |
| IV. User Confirmation Required | **PASS** | Conversational workflow via Claude Code maintained |
| V. Testing Discipline | **ADAPT** | pytest replaces Pester; same coverage goals |
| VI. Architectural Verification | **PASS** | Text-only I/O constraint respected; Python subprocess same as PowerShell |

**Module Import Rules Note**: The PowerShell constitution prohibits nested module imports. For Python, we use standard Python imports which handle scope correctly. Each module imports its dependencies directly - this is idiomatic Python and doesn't cause scope isolation issues like PowerShell.

## Project Structure

### Documentation (this feature)

```
specs/001-multi-shell-python/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```
src/
├── speckit_update/
│   ├── __init__.py
│   ├── __main__.py           # CLI entry point
│   ├── cli.py                # Argument parsing, main orchestration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── manifest.py       # Manifest, TrackedFile dataclasses
│   │   ├── file_state.py     # FileState enum
│   │   ├── release.py        # Release dataclass
│   │   ├── backup.py         # Backup dataclass
│   │   └── conflict.py       # ConflictResult dataclass
│   ├── services/
│   │   ├── __init__.py
│   │   ├── hash_utils.py     # Normalized hashing (replaces HashUtils.psm1)
│   │   ├── github_client.py  # GitHub API (replaces GitHubApiClient.psm1)
│   │   ├── manifest_manager.py   # CRUD ops (replaces ManifestManager.psm1)
│   │   ├── backup_manager.py     # Backup/restore (replaces BackupManager.psm1)
│   │   ├── conflict_detector.py  # File analysis (replaces ConflictDetector.psm1)
│   │   ├── fingerprint_detector.py # Version detection (replaces FingerprintDetector.psm1)
│   │   └── markdown_merger.py    # 3-way merge (replaces MarkdownMerger.psm1)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── paths.py          # Cross-platform path handling
│   │   └── logging.py        # Verbose logging setup
│   └── data/
│       └── speckit-fingerprints.json  # Bundled fingerprint database
│
├── py.typed                  # PEP 561 marker for type checking
└── pyproject.toml           # Project configuration

tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_hash_utils.py
│   ├── test_github_client.py
│   ├── test_manifest_manager.py
│   ├── test_backup_manager.py
│   ├── test_conflict_detector.py
│   ├── test_fingerprint_detector.py
│   └── test_markdown_merger.py
├── integration/
│   └── test_update_workflow.py
└── fixtures/
    ├── sample-manifests/
    └── mock-responses/
```

**Structure Decision**: Single CLI application structure. The `src/speckit_update/` layout follows Python packaging best practices with clear separation between models (data structures), services (business logic), and utils (cross-cutting concerns).

## Module Mapping (PowerShell → Python)

| PowerShell Module | Python Module | Responsibility |
|-------------------|---------------|----------------|
| `HashUtils.psm1` | `services/hash_utils.py` | Normalized SHA-256 hashing |
| `GitHubApiClient.psm1` | `services/github_client.py` | GitHub Releases API |
| `ManifestManager.psm1` | `services/manifest_manager.py` | Manifest CRUD |
| `BackupManager.psm1` | `services/backup_manager.py` | Backup/restore operations |
| `ConflictDetector.psm1` | `services/conflict_detector.py` | File state analysis |
| `FingerprintDetector.psm1` | `services/fingerprint_detector.py` | Version auto-detection |
| `MarkdownMerger.psm1` | `services/markdown_merger.py` | Intelligent 3-way merge |
| `update-orchestrator.ps1` | `cli.py` | Main entry point and workflow |

## Key Design Decisions

### 1. Type System Strategy

Use Python 3.14's modern typing throughout:

```python
from dataclasses import dataclass
from typing import TypedDict, Literal, Protocol
from enum import Enum

class FileState(Enum):
    ADD = "add"
    REMOVE = "remove"
    UPDATE = "update"
    PRESERVE = "preserve"
    MERGE = "merge"
    SKIP = "skip"

@dataclass(frozen=True)
class TrackedFile:
    path: str
    original_hash: str
    customized: bool
    is_official: bool
```

### 2. Path Handling Strategy

Case-preserving, case-insensitive comparison across all platforms:

```python
from pathlib import PurePath

def normalize_path(path: str) -> str:
    """Normalize path for consistent comparison."""
    return str(PurePath(path)).lower()

def paths_equal(a: str, b: str) -> bool:
    """Compare paths case-insensitively."""
    return normalize_path(a) == normalize_path(b)
```

### 3. Error Handling Strategy

Custom exception hierarchy with exit codes matching PowerShell:

```python
class SpecKitError(Exception):
    exit_code: int = 1

class PrerequisiteError(SpecKitError):
    exit_code = 2

class NetworkError(SpecKitError):
    exit_code = 3

class GitError(SpecKitError):
    exit_code = 4

class UserCancelledError(SpecKitError):
    exit_code = 5

class RollbackError(SpecKitError):
    exit_code = 6
```

### 4. SKILL.md Integration

Update SKILL.md to invoke Python:

```markdown
## Execution
python -m speckit_update $ARGUMENTS
```

## Complexity Tracking

*No constitution violations requiring justification.*

| Aspect | Complexity | Justification |
|--------|------------|---------------|
| Module count | 7 services | Direct 1:1 mapping from PowerShell modules |
| Dependencies | 1 external (requests) | Minimal; stdlib for everything else |
| Test migration | 193 → pytest | Same scenarios, different framework |
