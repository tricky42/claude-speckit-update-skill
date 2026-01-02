# Research: Multi-Shell Python Support

**Feature**: 001-multi-shell-python
**Date**: 2026-01-02

## Research Topics

### 1. Python 3.14 Typing Features

**Decision**: Use Python 3.14's native typing without third-party libraries

**Rationale**: Python 3.14 includes all required typing features natively:
- `dataclasses` for immutable data structures
- `TypedDict` for JSON schema typing
- `Literal` for constrained string types
- `Protocol` for structural subtyping
- `Self` type for fluent interfaces

**Alternatives Considered**:
- Pydantic: More features but adds dependency (rejected per NFR-006)
- attrs: Similar to dataclasses but external (rejected per NFR-006)
- typing_extensions: Not needed with Python 3.14+

### 2. HTTP Client Choice

**Decision**: Use `requests` library for HTTP

**Rationale**:
- Battle-tested, stable API
- Excellent error handling
- Simple retry logic with urllib3
- Well-documented
- Only external dependency needed

**Alternatives Considered**:
- `urllib.request` (stdlib): Works but verbose, poor ergonomics
- `httpx`: Modern but adds dependency complexity, async not needed
- `aiohttp`: Async not required for this use case

### 3. Cross-Platform Path Handling

**Decision**: Use `pathlib.Path` with custom case-insensitive comparison

**Rationale**:
- `pathlib` is modern, Pythonic, cross-platform
- Custom comparison layer ensures consistent behavior
- Path normalization handles separators automatically

**Implementation**:
```python
from pathlib import Path, PurePath

def normalize_for_comparison(path: str | Path) -> str:
    """Normalize path for case-insensitive comparison."""
    return str(PurePath(path)).replace("\\", "/").lower()
```

**Alternatives Considered**:
- `os.path`: Older API, less readable
- Platform detection with conditional logic: Fragile, violates consistency goal

### 4. JSON Schema Handling

**Decision**: Use `TypedDict` for manifest schema with manual validation

**Rationale**:
- TypedDict provides compile-time type checking
- Manual validation gives precise error messages
- No external dependency required

**Schema Definition**:
```python
class TrackedFileDict(TypedDict):
    path: str
    original_hash: str
    customized: bool
    is_official: bool

class ManifestDict(TypedDict):
    version: str
    speckit_version: str
    initialized_at: str
    last_updated: str
    agent: str
    speckit_commands: list[str]
    tracked_files: list[TrackedFileDict]
    custom_files: list[str]
    backup_history: list[BackupHistoryDict]
```

**Alternatives Considered**:
- JSON Schema validation library: Adds dependency
- Pydantic models: Adds dependency
- No typing: Loses type safety benefits

### 5. Hashing Algorithm

**Decision**: SHA-256 with content normalization (matching PowerShell)

**Rationale**:
- Must be 100% compatible with existing manifest hashes
- SHA-256 is standard, secure, available in stdlib
- Normalization rules must match exactly:
  1. Convert CRLF → LF
  2. Strip trailing whitespace per line
  3. Remove BOM (0xFEFF) if present
  4. Compute hash
  5. Format as `sha256:{hex}`

**Implementation**:
```python
import hashlib

def get_normalized_hash(content: bytes) -> str:
    # Remove BOM
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]

    # Decode and normalize
    text = content.decode('utf-8', errors='replace')
    lines = text.replace('\r\n', '\n').split('\n')
    normalized = '\n'.join(line.rstrip() for line in lines)

    # Hash
    hash_bytes = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    return f"sha256:{hash_bytes}"
```

### 6. Markdown 3-Way Merge Strategy

**Decision**: Section-based parsing with Levenshtein distance for fuzzy matching

**Rationale**:
- Matches existing PowerShell MarkdownMerger behavior
- Section headers (`#`, `##`, etc.) define merge units
- 80% similarity threshold for renamed section matching
- Produces section-level conflict markers, not file-level

**Algorithm**:
1. Parse both files into sections (header + content)
2. Match sections by header text (exact or fuzzy)
3. For each section pair:
   - If only in incoming: add
   - If only in current: preserve
   - If in both and same: keep
   - If in both and different: merge or mark conflict
4. Use incoming structure as canonical ordering

**Alternatives Considered**:
- Line-based diff: Too granular, poor UX
- Full-file conflict markers: Poor for large files
- External merge tool: Adds dependency

### 7. Testing Framework

**Decision**: pytest with pytest-cov

**Rationale**:
- pytest is Python standard for testing
- Fixtures map well to Pester's BeforeAll/BeforeEach
- parametrize decorator replaces Pester's TestCases
- pytest-cov for coverage (90% target)

**Test Migration Strategy**:
```
Pester Pattern          → pytest Pattern
------------------------   -----------------
Describe                → class Test*
Context                 → nested class or methods
It                      → def test_*
BeforeAll               → @pytest.fixture(scope="class")
BeforeEach              → @pytest.fixture
Mock                    → unittest.mock or pytest-mock
Should -Be              → assert ==
Should -Throw           → pytest.raises
```

### 8. CLI Argument Parsing

**Decision**: Use `argparse` from stdlib

**Rationale**:
- Standard library, no dependency
- Sufficient for our simple CLI
- Maps directly to PowerShell parameters

**CLI Interface**:
```
speckit-update [--check-only] [--version VERSION] [--rollback] [--proceed] [--verbose]
```

**Alternatives Considered**:
- click: Popular but adds dependency
- typer: Modern but adds dependency
- sys.argv manual: Too primitive

### 9. Logging Strategy

**Decision**: Use `logging` module with custom formatter

**Rationale**:
- Stdlib logging is sufficient
- `--verbose` maps to DEBUG level
- Normal output via print() to stdout
- Errors via logging to stderr

**Implementation**:
```python
import logging

def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        stream=sys.stderr
    )
```

### 10. Fingerprint Database Distribution

**Decision**: Bundle as JSON file in package data

**Rationale**:
- Same approach as PowerShell (`data/speckit-fingerprints.json`)
- No network required for version detection
- Updates come with new releases
- ~69KB file, acceptable size

**Location**: `src/speckit_update/data/speckit-fingerprints.json`

**Access**:
```python
from importlib.resources import files

def load_fingerprints() -> dict:
    data_file = files('speckit_update.data').joinpath('speckit-fingerprints.json')
    return json.loads(data_file.read_text())
```

## Resolved Clarifications

All NEEDS CLARIFICATION items from Technical Context have been resolved through this research. No outstanding unknowns remain.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hash algorithm mismatch | Low | High | Comprehensive test suite comparing Python and PowerShell outputs |
| Path case sensitivity edge cases | Medium | Medium | Extensive cross-platform testing |
| Performance regression | Low | Medium | Benchmark suite comparing to PowerShell baseline |
| Migration breaks existing manifests | Low | High | Backward compatibility tests with real-world manifests |
