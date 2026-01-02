# Feature Specification: Multi-Shell Python Support

**Feature Branch**: `001-multi-shell-python`
**Created**: 2026-01-02
**Status**: Draft
**GitHub Issue**: #15 - Multi-Shell Support (macOS/Linux)
**Input**: Rewrite the SpecKit Update Skill in modern Python (>= 3.14) with full type hints for cross-platform support

## Clarifications

### Session 2026-01-02

- Q: How should GitHub authentication tokens be stored and accessed securely? → A: Environment variable only (`GITHUB_TOKEN` or `GITHUB_PAT`)
- Q: What is the backward compatibility strategy for Windows PowerShell users? → A: Python fully replaces PowerShell; SKILL.md updated to invoke Python instead (users interact via `/speckit-update` command, not direct script calls)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cross-Platform Update Check (Priority: P1)

A developer on macOS or Linux wants to check for SpecKit updates without modifying any files, seeing a clear report of what would change.

**Why this priority**: This is the entry point for all users - they must be able to safely check for updates before committing to any changes. Without this, no other functionality is accessible.

**Independent Test**: Can be fully tested by running `speckit-update --check-only` on macOS/Linux and verifying it reports available updates without modifying any files.

**Acceptance Scenarios**:

1. **Given** a SpecKit project on macOS with manifest.json, **When** user runs `speckit-update --check-only`, **Then** system displays available updates, customized files, and potential conflicts without modifying any files
2. **Given** a SpecKit project on Linux without network access, **When** user runs `speckit-update --check-only`, **Then** system displays a clear error message about network connectivity
3. **Given** a SpecKit project with no available updates, **When** user runs `speckit-update --check-only`, **Then** system confirms the installation is up-to-date

---

### User Story 2 - Safe Update with Conflict Detection (Priority: P1)

A developer wants to update their SpecKit installation while preserving their customizations, with clear visibility into any conflicts.

**Why this priority**: Core value proposition - users need to update safely without losing their work. This is the primary use case that differentiates this tool from destructive `init --force`.

**Independent Test**: Can be tested by running `speckit-update` on a project with known customizations and verifying customizations are preserved while updates are applied.

**Acceptance Scenarios**:

1. **Given** a project with customized files and available updates, **When** user runs `speckit-update --proceed`, **Then** system updates non-customized files, preserves customized files, and reports conflicts for manual resolution
2. **Given** a project with conflicting changes (file modified locally AND upstream), **When** update runs, **Then** system applies intelligent 3-way merge for markdown files with section-level conflict markers
3. **Given** an update fails mid-process, **When** error occurs, **Then** system automatically rolls back to pre-update state using backup

---

### User Story 3 - First-Time User Onboarding (Priority: P2)

A new user wants to start using the update skill on an existing SpecKit project that doesn't have a manifest yet.

**Why this priority**: Essential for adoption - new users should have a frictionless onboarding experience with automatic version detection.

**Independent Test**: Can be tested by running the tool on an existing SpecKit project without manifest.json and verifying version is auto-detected and manifest is created.

**Acceptance Scenarios**:

1. **Given** a SpecKit project without manifest.json, **When** user runs `speckit-update`, **Then** system auto-detects installed version via fingerprinting with confidence score displayed
2. **Given** high-confidence version detection (>= 95%), **When** manifest is created, **Then** system tracks only actually customized files as modified, enabling smart merge
3. **Given** low-confidence version detection (< 70%), **When** user is prompted, **Then** system defaults to safe behavior (treating all files as potentially customized)

---

### User Story 4 - Rollback After Problematic Update (Priority: P2)

A developer wants to undo a recent update that caused issues and restore their previous working state.

**Why this priority**: Safety net for users - knowing they can always roll back encourages adoption and reduces fear of updating.

**Independent Test**: Can be tested by performing an update, then running `speckit-update --rollback` and verifying all files return to pre-update state.

**Acceptance Scenarios**:

1. **Given** a completed update with backup, **When** user runs `speckit-update --rollback`, **Then** system restores all files from most recent backup and reverts manifest
2. **Given** multiple backups exist, **When** user runs `speckit-update --rollback`, **Then** system uses most recent backup while preserving older backups
3. **Given** no backups exist, **When** user runs `speckit-update --rollback`, **Then** system displays clear message that no backups are available

---

### User Story 5 - Target Specific Version (Priority: P3)

A developer wants to update to a specific SpecKit version rather than the latest, for compatibility or testing purposes.

**Why this priority**: Power user feature - most users want latest, but version pinning is important for teams and CI/CD.

**Independent Test**: Can be tested by running `speckit-update --version v0.0.72` and verifying the exact version is installed.

**Acceptance Scenarios**:

1. **Given** a project at v0.0.70, **When** user runs `speckit-update --version v0.0.72`, **Then** system updates to exactly v0.0.72
2. **Given** a request for non-existent version, **When** user specifies invalid version, **Then** system displays available versions and suggests alternatives

---

### User Story 6 - Seamless Migration for Existing Users (Priority: P3)

Existing users on any platform should experience no change in their workflow when the implementation switches from PowerShell to Python.

**Why this priority**: Migration must be invisible - users interact via `/speckit-update` command, not direct script invocation.

**Independent Test**: Can be tested by verifying `/speckit-update` command produces identical output and behavior after Python migration.

**Acceptance Scenarios**:

1. **Given** an existing user on Windows/macOS/Linux, **When** they run `/speckit-update` after migration, **Then** behavior and output are identical to previous implementation
2. **Given** an existing manifest.json from PowerShell version, **When** Python implementation reads it, **Then** all data is preserved and updates work correctly

---

### Edge Cases

- What happens when the user's Python version is below 3.14?
  - System displays clear error with upgrade instructions
- How does system handle network timeouts during GitHub API calls?
  - Configurable timeout with retry logic (3 attempts, exponential backoff)
- What happens when file system permissions prevent writing?
  - Clear error message identifying the problematic path with permission requirements
- How does system handle corrupted manifest.json?
  - Backup corrupt file, attempt repair, or recreate with version detection
- What happens during concurrent updates (user runs twice)?
  - Lock file prevents concurrent execution with clear message

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run on Windows 10+, macOS 12+, and Linux (Ubuntu 20.04+, Debian 11+, Fedora 36+)
- **FR-002**: System MUST require Python >= 3.14 with type checking enabled
- **FR-003**: System MUST provide identical CLI interface to PowerShell version (`--check-only`, `--version`, `--rollback`, `--proceed`)
- **FR-004**: System MUST read and write manifest.json with 100% schema compatibility
- **FR-005**: System MUST detect customized files using normalized SHA-256 hashing (CRLF/LF normalization, BOM removal)
- **FR-006**: System MUST fetch releases from GitHub API with rate limit handling; authentication via `GITHUB_TOKEN` or `GITHUB_PAT` environment variable (no other storage mechanisms)
- **FR-007**: System MUST perform intelligent 3-way merge for markdown files with section-level conflict markers
- **FR-008**: System MUST create timestamped backups before any file modifications
- **FR-009**: System MUST automatically roll back on errors during update process
- **FR-010**: System MUST detect installed version via fingerprint matching for projects without manifest
- **FR-011**: System MUST handle cross-platform path separators transparently
- **FR-012**: System MUST preserve all custom user commands (never overwrite user-created files in `.claude/commands/`)
- **FR-013**: System MUST fully replace PowerShell implementation; SKILL.md updated to invoke Python (no PowerShell wrapper or dual implementation)
- **FR-014**: System MUST use modern Python typing throughout (TypedDict, dataclasses, Literal, Protocol)
- **FR-015**: System MUST provide verbose logging mode for debugging (`--verbose`)

### Non-Functional Requirements

- **NFR-001**: Check-only operations MUST complete in under 2 seconds on standard hardware
- **NFR-002**: Full updates MUST complete in under 5 seconds (excluding download time)
- **NFR-003**: System MUST have 100% type coverage verifiable with mypy/pyright in strict mode
- **NFR-004**: System MUST have >= 90% test coverage with pytest
- **NFR-005**: System MUST work offline for operations not requiring GitHub API
- **NFR-006**: System MUST produce zero dependencies beyond Python standard library (except requests for HTTP)

### Key Entities

- **Manifest**: JSON document tracking SpecKit version, file hashes, customization flags, and backup history
- **TrackedFile**: Individual file with path, original_hash, customized flag, and is_official flag
- **FileState**: Enumeration of file states (add, remove, update, preserve, merge, skip)
- **Release**: GitHub release metadata with tag_name, assets, and tarball_url
- **Backup**: Timestamped snapshot with from_version, to_version, and file contents
- **ConflictResult**: Merge outcome with conflict_count, merged_content, and conflict_markers
- **Fingerprint**: Version signature with file hashes and confidence score

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users on macOS/Linux can successfully update SpecKit installations (measured by successful update completions)
- **SC-002**: Check-only operations complete in under 2 seconds for 95% of executions
- **SC-003**: Full updates complete in under 5 seconds for 95% of executions (excluding network)
- **SC-004**: Zero data loss incidents reported (customizations always preserved or backed up)
- **SC-005**: First-time users with existing installations experience zero manual conflicts for unmodified files
- **SC-006**: All 193 existing test scenarios pass when migrated to pytest
- **SC-007**: Type checker reports zero errors in strict mode
- **SC-008**: Existing users on all platforms experience seamless migration (identical `/speckit-update` behavior)

## Assumptions

- Python 3.14+ is available or can be installed on target platforms
- Users have read/write access to their project directories
- GitHub API is accessible (with graceful degradation for rate limits)
- Users are familiar with command-line interfaces
- Network connectivity is available for fetching updates (offline mode for cached operations)

## Out of Scope

- GUI interface (CLI only)
- Automatic installation of Python
- Support for Python versions below 3.14
- Integration with package managers (pip/conda distribution)
- Real-time sync with GitHub (polling-based updates only)
- Multi-project batch updates
