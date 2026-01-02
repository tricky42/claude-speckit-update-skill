# Tasks: Multi-Shell Python Support

**Input**: Design documents from `/specs/001-multi-shell-python/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Required per NFR-004 (>= 90% test coverage with pytest)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization with uv package manager and modern Python tooling

- [x] T001 Create project structure per plan.md (`src/speckit_update/`, `tests/`)
- [x] T002 Initialize pyproject.toml with uv (Python 3.14+, httpx, rich dependencies)
- [x] T003 [P] Create `.python-version` file for uv (3.14)
- [x] T004 [P] Configure ruff in pyproject.toml (line-length=88, select E,W,F,I,B,C4,UP,ARG,SIM)
- [x] T005 [P] Configure mypy in pyproject.toml (strict mode)
- [x] T006 [P] Create py.typed marker file for PEP 561
- [ ] T007 Run `uv sync --dev` to verify dependency resolution (skipped - uv not installed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Models (data-model.md)

- [x] T008 [P] Create `src/speckit_update/models/__init__.py` with exports
- [x] T009 [P] Implement FileState enum in `src/speckit_update/models/file_state.py`
- [x] T010 [P] Implement ConfidenceLevel enum in `src/speckit_update/models/file_state.py`
- [x] T011 [P] Implement TrackedFile dataclass in `src/speckit_update/models/manifest.py`
- [x] T012 [P] Implement BackupEntry dataclass in `src/speckit_update/models/backup.py`
- [x] T013 [P] Implement Manifest dataclass in `src/speckit_update/models/manifest.py`
- [x] T014 [P] Implement Release dataclass in `src/speckit_update/models/release.py`
- [x] T015 [P] Implement ConflictResult dataclass in `src/speckit_update/models/conflict.py`
- [x] T016 [P] Implement Fingerprint dataclass in `src/speckit_update/models/fingerprint.py`
- [x] T017 [P] Implement FingerprintMatch dataclass in `src/speckit_update/models/fingerprint.py`
- [x] T018 [P] Implement FileAnalysis dataclass in `src/speckit_update/models/file_analysis.py`
- [x] T019 [P] Implement UpdatePlan dataclass in `src/speckit_update/models/update_plan.py`

### TypedDict Definitions (JSON Serialization)

- [x] T020 [P] Implement TrackedFileDict, BackupEntryDict, ManifestDict in `src/speckit_update/models/manifest.py`

### Validation Utilities

- [x] T021 [P] Implement validate_path() in `src/speckit_update/utils/validation.py`
- [x] T022 [P] Implement validate_hash() in `src/speckit_update/utils/validation.py`
- [x] T023 [P] Implement validate_version() in `src/speckit_update/utils/validation.py`

### Cross-Platform Path Utilities

- [x] T024 Implement normalize_path(), paths_equal() in `src/speckit_update/utils/paths.py`

### Error Handling

- [x] T025 Implement exception hierarchy in `src/speckit_update/exceptions.py`:
  - SpecKitError (exit_code=1)
  - PrerequisiteError (exit_code=2)
  - NetworkError (exit_code=3)
  - GitError (exit_code=4)
  - UserCancelledError (exit_code=5)
  - RollbackError (exit_code=6)

### Rich UI Foundation

- [x] T026 [P] Create shared Console instance in `src/speckit_update/ui/console.py`
- [x] T027 [P] Implement setup_logging() with RichHandler in `src/speckit_update/utils/logging.py`

### Package Entry Points

- [x] T028 Create `src/speckit_update/__init__.py` with version
- [x] T029 Create `src/speckit_update/__main__.py` for `python -m speckit_update`
- [x] T030 Create `src/speckit_update/services/__init__.py`
- [x] T031 Create `src/speckit_update/ui/__init__.py`
- [x] T032 Create `src/speckit_update/utils/__init__.py`

### Foundational Tests

- [x] T033 [P] Create `tests/conftest.py` with shared fixtures (tmp_path, mock manifests)
- [x] T034 [P] Test FileState enum in `tests/unit/test_models.py`
- [x] T035 [P] Test validation functions in `tests/unit/test_validation.py`
- [x] T036 [P] Test path utilities in `tests/unit/test_paths.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Cross-Platform Update Check (Priority: P1) 🎯 MVP

**Goal**: Users on macOS/Linux can check for SpecKit updates without modifying files

**Independent Test**: Run `uv run speckit-update --check-only` on macOS/Linux and verify it reports available updates without file modifications

### Tests for User Story 1 ⚠️

**NOTE: Write tests FIRST, ensure they FAIL before implementation**

- [x] T037 [P] [US1] Unit test for hash_utils in `tests/unit/test_hash_utils.py`
- [ ] T038 [P] [US1] Unit test for github_client in `tests/unit/test_github_client.py`
- [x] T039 [P] [US1] Unit test for manifest_manager in `tests/unit/test_manifest_manager.py`
- [x] T040 [P] [US1] Unit test for conflict_detector in `tests/unit/test_conflict_detector.py`
- [ ] T041 [P] [US1] Integration test for check-only workflow in `tests/integration/test_check_only.py`

### Implementation for User Story 1

#### Core Services (PowerShell → Python Migration)

- [x] T042 [US1] Implement get_normalized_hash() in `src/speckit_update/services/hash_utils.py`:
  - Remove BOM (0xFEFF)
  - Convert CRLF → LF
  - Strip trailing whitespace per line
  - Return sha256:{hex} format
- [x] T043 [US1] Implement GitHubClient class in `src/speckit_update/services/github_client.py`:
  - get_latest_release() → Release
  - get_release(version: str) → Release
  - download_tarball(url: str) → bytes
  - Rate limit handling with exponential backoff
  - GITHUB_TOKEN/GITHUB_PAT environment variable support
- [x] T044 [US1] Implement ManifestManager in `src/speckit_update/services/manifest_manager.py`:
  - load(path: Path) → Manifest | None
  - save(manifest: Manifest, path: Path) → None
  - JSON serialization with TypedDict
- [x] T045 [US1] Implement ConflictDetector in `src/speckit_update/services/conflict_detector.py`:
  - analyze_file(tracked: TrackedFile, upstream_hash: str | None) → FileAnalysis
  - create_update_plan(manifest: Manifest, release: Release) → UpdatePlan
  - FileState determination logic per data-model.md flowchart

#### Rich UI Components

- [x] T046 [P] [US1] Implement update plan table in `src/speckit_update/ui/tables.py`:
  - show_update_plan(plan: UpdatePlan) with columns: File, Status, Action
  - Color-coded actions: green (add), yellow (update), red (merge)
- [x] T047 [P] [US1] Implement progress bars in `src/speckit_update/ui/progress.py`:
  - download_with_progress(url: str) → bytes
  - SpinnerColumn for indeterminate operations

#### CLI Implementation

- [x] T048 [US1] Implement CLI argument parsing in `src/speckit_update/cli.py`:
  - --check-only flag
  - --verbose flag
  - argparse with subcommands
- [x] T049 [US1] Implement check_only workflow in `src/speckit_update/cli.py`:
  - Load manifest
  - Fetch latest release
  - Analyze conflicts
  - Display Rich table
  - Exit without modifications

#### Data Files

- [x] T050 [US1] Copy `data/speckit-fingerprints.json` to `src/speckit_update/data/`

**Checkpoint**: User Story 1 complete - `--check-only` works on all platforms

---

## Phase 4: User Story 2 - Safe Update with Conflict Detection (Priority: P1) 🎯 MVP

**Goal**: Users can update SpecKit while preserving customizations with intelligent merge

**Independent Test**: Run `uv run speckit-update --proceed` on a project with known customizations and verify customizations preserved

### Tests for User Story 2 ⚠️

- [x] T051 [P] [US2] Unit test for backup_manager in `tests/unit/test_backup_manager.py`
- [x] T052 [P] [US2] Unit test for markdown_merger in `tests/unit/test_markdown_merger.py`
- [ ] T053 [P] [US2] Integration test for update workflow in `tests/integration/test_update_workflow.py`

### Implementation for User Story 2

#### Backup Service

- [x] T054 [US2] Implement BackupManager in `src/speckit_update/services/backup_manager.py`:
  - create_backup(manifest: Manifest) → BackupEntry
  - Timestamped directories in .specify/backups/
  - Retention management (keep 5 most recent)

#### Markdown Merger (3-Way Merge)

- [x] T055 [US2] Implement MarkdownMerger in `src/speckit_update/services/markdown_merger.py`:
  - parse_sections(content: str) → list[Section]
  - match_sections_fuzzy(base: list, current: list, incoming: list) using Levenshtein
  - merge(base: str, current: str, incoming: str) → ConflictResult
  - Section-level conflict markers
  - 80% similarity threshold for renamed sections

#### Rich UI for Updates

- [x] T056 [P] [US2] Implement confirmation prompts in `src/speckit_update/ui/prompts.py`:
  - confirm_update(plan: UpdatePlan) → bool
  - show_conflict_summary(results: list[ConflictResult])
- [x] T057 [P] [US2] Implement status messages in `src/speckit_update/ui/console.py`:
  - success(), warning(), error() with symbols ✓, ⚠, ✗

#### Update Workflow

- [x] T058 [US2] Implement --proceed workflow in `src/speckit_update/cli.py`:
  - Create backup before modifications
  - Download and extract release tarball
  - Apply updates to non-customized files
  - Invoke 3-way merge for conflict files
  - Update manifest with new hashes
  - Cleanup old backups

#### Auto-Rollback

- [x] T059 [US2] Implement automatic rollback on error in `src/speckit_update/cli.py`:
  - Wrap update in try/except
  - On error: restore from backup, revert manifest
  - Exit code 6 for rollback

**Checkpoint**: User Stories 1 AND 2 complete - full update workflow works

---

## Phase 5: User Story 3 - First-Time User Onboarding (Priority: P2)

**Goal**: New users get automatic version detection when no manifest exists

**Independent Test**: Run tool on existing SpecKit project without manifest.json and verify version auto-detected

### Tests for User Story 3 ⚠️

- [x] T060 [P] [US3] Unit test for fingerprint_detector in `tests/unit/test_fingerprint_detector.py`
- [ ] T061 [P] [US3] Integration test for onboarding in `tests/integration/test_onboarding.py`

### Implementation for User Story 3

- [x] T062 [US3] Implement FingerprintDetector in `src/speckit_update/services/fingerprint_detector.py`:
  - load_fingerprints() → dict[str, Fingerprint] from bundled JSON
  - detect_version_fast(project_root: Path) → FingerprintMatch | None (3 signature files)
  - detect_version_full(project_root: Path) → FingerprintMatch (12 files, fuzzy)
  - Confidence scoring: High (95-100%), Medium (70-94%), Low (<70%)
- [ ] T063 [US3] Implement first-run flow in `src/speckit_update/cli.py`:
  - Detect no manifest exists
  - Run fingerprint detection
  - Display confidence with Rich panel
  - Create manifest with detected version
  - Low confidence: treat all files as customized

**Checkpoint**: User Story 3 complete - frictionless onboarding works

---

## Phase 6: User Story 4 - Rollback After Problematic Update (Priority: P2)

**Goal**: Users can restore previous state after a problematic update

**Independent Test**: Perform update, then run `--rollback` and verify all files restored

### Tests for User Story 4 ⚠️

- [ ] T064 [P] [US4] Unit test for rollback in `tests/unit/test_backup_manager.py::test_restore`
- [ ] T065 [P] [US4] Integration test for rollback in `tests/integration/test_rollback.py`

### Implementation for User Story 4

- [ ] T066 [US4] Implement restore_backup() in `src/speckit_update/services/backup_manager.py`:
  - Find most recent backup from manifest.backup_history
  - Restore all files from backup directory
  - Revert manifest to pre-update state
- [ ] T067 [US4] Implement --rollback CLI in `src/speckit_update/cli.py`:
  - Check backups exist
  - Confirm with user
  - Execute restore
  - Display success with Rich

**Checkpoint**: User Story 4 complete - rollback functionality works

---

## Phase 7: User Story 5 - Target Specific Version (Priority: P3)

**Goal**: Users can update to a specific version instead of latest

**Independent Test**: Run `--version v0.0.72` and verify exact version installed

### Tests for User Story 5 ⚠️

- [ ] T068 [P] [US5] Integration test for version targeting in `tests/integration/test_version_target.py`

### Implementation for User Story 5

- [ ] T069 [US5] Add --version parameter to CLI in `src/speckit_update/cli.py`
- [ ] T070 [US5] Implement get_release(version) call path in update workflow
- [ ] T071 [US5] Handle non-existent version with suggestions (list available versions)

**Checkpoint**: User Story 5 complete - version targeting works

---

## Phase 8: User Story 6 - Seamless Migration (Priority: P3)

**Goal**: Existing users experience identical behavior after Python migration

**Independent Test**: Compare output before/after migration for identical behavior

### Tests for User Story 6 ⚠️

- [ ] T072 [P] [US6] Compatibility test for manifest reading in `tests/compatibility/test_manifest_compat.py`
- [ ] T073 [P] [US6] Hash compatibility test (Python vs PowerShell fixtures) in `tests/compatibility/test_hash_compat.py`

### Implementation for User Story 6

- [ ] T074 [US6] Update SKILL.md to invoke Python:
  ```markdown
  ## Execution
  uv run speckit-update $ARGUMENTS
  ```
- [ ] T075 [US6] Verify exit codes match PowerShell implementation (0-6)
- [ ] T076 [US6] Test with real manifests from PowerShell version

**Checkpoint**: User Story 6 complete - seamless migration verified

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final quality improvements across all stories

- [ ] T077 [P] Run `uv run mypy src/ --strict` - fix all errors
- [ ] T078 [P] Run `uv run ruff check src/ tests/` - fix all linting issues
- [ ] T079 [P] Run `uv run ruff format src/ tests/` - format all code
- [ ] T080 [P] Run `uv run pytest --cov=speckit_update` - achieve >= 90% coverage
- [ ] T081 Verify performance: check-only < 2s, full update < 5s
- [ ] T082 Test on all platforms: Windows 10+, macOS 12+, Ubuntu 20.04+
- [ ] T083 Run quickstart.md validation end-to-end
- [ ] T084 Final commit and push to feature branch

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ──────────────────────────────────────┐
                                                      │
Phase 2: Foundational ◄───────────────────────────────┘
    │
    │  ⚠️ BLOCKS ALL USER STORIES
    ▼
┌───────────────────────────────────────────────────────────────────┐
│  Phase 3: US1 (P1) ──┐                                            │
│                      │ MVP complete                               │
│  Phase 4: US2 (P1) ──┘                                            │
│                                                                   │
│  Phase 5: US3 (P2) ──────────────────────────────────────────────│
│  Phase 6: US4 (P2) ──────────────────────────────────────────────│
│                                                                   │
│  Phase 7: US5 (P3) ──────────────────────────────────────────────│
│  Phase 8: US6 (P3) ──────────────────────────────────────────────│
└───────────────────────────────────────────────────────────────────┘
    │
    ▼
Phase 9: Polish
```

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (P1) | Phase 2 | US2 (same priority) |
| US2 (P1) | Phase 2 | US1 (same priority) |
| US3 (P2) | Phase 2 | US4, US5, US6 |
| US4 (P2) | Phase 2, BackupManager from US2 | US3, US5, US6 |
| US5 (P3) | Phase 2, GitHubClient from US1 | US3, US4, US6 |
| US6 (P3) | Phase 2 | US3, US4, US5 |

### Within Each User Story

1. Tests written FIRST, verify they FAIL
2. Models before services
3. Services before CLI integration
4. UI components can parallel with services
5. Story complete before moving to next priority

---

## Parallel Opportunities

### Setup Phase (all parallel)
```bash
# Can run simultaneously:
T003: .python-version
T004: ruff config
T005: mypy config
T006: py.typed
```

### Foundational Models (all parallel)
```bash
# Can run simultaneously:
T009-T019: All dataclass implementations
T021-T023: All validation functions
T026-T027: UI foundation
```

### User Story 1 Tests (all parallel)
```bash
# Can run simultaneously:
T037: test_hash_utils.py
T038: test_github_client.py
T039: test_manifest_manager.py
T040: test_conflict_detector.py
```

### User Story 1 UI (parallel with services)
```bash
# Can run while services implemented:
T046: tables.py
T047: progress.py
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (~1 hour)
2. Complete Phase 2: Foundational (~4 hours)
3. Complete Phase 3: US1 Check-Only (~8 hours)
4. **VALIDATE**: Test `--check-only` on macOS/Linux
5. Complete Phase 4: US2 Update (~8 hours)
6. **VALIDATE**: Test `--proceed` with customized files
7. **MVP COMPLETE**: Core update workflow functional

### Full Feature (Add P2 + P3)

8. Phase 5: US3 Onboarding (~4 hours)
9. Phase 6: US4 Rollback (~2 hours)
10. Phase 7: US5 Version Target (~2 hours)
11. Phase 8: US6 Migration (~2 hours)
12. Phase 9: Polish (~4 hours)

**Estimated Total: 35-40 hours**

---

## Notes

- All tasks use `uv run` for Python execution
- Rich library for ALL terminal output (no plain print)
- httpx for ALL HTTP operations (no requests)
- mypy strict mode enforced throughout
- Commit after each task or logical group
- Run tests after each phase completion
