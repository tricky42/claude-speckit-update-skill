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

**Decision**: Use `httpx` for HTTP

**Rationale**:
- Modern, type-safe HTTP client
- Full type annotations for mypy strict mode
- Sync and async support (using sync for this project)
- Better timeout handling than requests
- `requests`-compatible API for easy migration
- Active development and excellent documentation

**Implementation**:
```python
import httpx

def get_latest_release() -> Release:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            "https://api.github.com/repos/github/spec-kit/releases/latest",
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        response.raise_for_status()
        return Release.from_dict(response.json())
```

**Alternatives Considered**:
- `requests`: Battle-tested but incomplete type stubs, aging API
- `urllib.request` (stdlib): Works but verbose, poor ergonomics
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

**Decision**: Use `logging` module integrated with Rich

**Rationale**:
- Stdlib logging for structured logging
- Rich's `RichHandler` for beautiful console output
- `--verbose` maps to DEBUG level with detailed output
- Automatic syntax highlighting for tracebacks

**Implementation**:
```python
import logging
from rich.logging import RichHandler

def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
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

### 11. Package Manager Choice

**Decision**: Use `uv` for package management

**Rationale**:
- 10-100x faster than pip for installs and resolves
- Written in Rust, single binary, no Python bootstrap needed
- Drop-in replacement for pip, pip-tools, virtualenv
- Excellent lockfile support (`uv.lock`)
- Built-in Python version management
- Growing ecosystem adoption (Astral, same team as Ruff)

**Project Setup**:
```bash
# Initialize project
uv init speckit-update
cd speckit-update

# Add dependencies
uv add httpx rich
uv add --dev pytest pytest-cov mypy ruff

# Run commands
uv run speckit-update --check-only
uv run pytest
uv run mypy src/
```

**pyproject.toml structure**:
```toml
[project]
name = "speckit-update"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "httpx>=0.27",
    "rich>=13.0",
]

[project.scripts]
speckit-update = "speckit_update.cli:main"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "mypy>=1.8",
    "ruff>=0.3",
]
```

**Alternatives Considered**:
- pip + venv: Standard but slow, no lockfile
- poetry: Good but slower, heavier
- pdm: Modern but less adoption than uv
- hatch: Good for publishing but uv faster for development

### 12. Terminal UI Library

**Decision**: Use `Rich` for all terminal output

**Rationale**:
- Beautiful, modern terminal output with zero configuration
- Tables, progress bars, syntax highlighting, panels
- Markdown rendering in terminal
- Full type annotations for mypy
- Cross-platform (Windows, macOS, Linux)
- Active maintenance by Will McGugan

**Key Rich Components Used**:

```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

console = Console()

# Update plan table
def show_update_plan(plan: UpdatePlan) -> None:
    table = Table(title="Update Plan", show_header=True)
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("Action", style="green")

    for file in plan.files_to_add:
        table.add_row(file, "New", "[green]Add[/green]")
    for file in plan.files_to_update:
        table.add_row(file, "Changed", "[yellow]Update[/yellow]")
    for file in plan.files_to_merge:
        table.add_row(file, "Conflict", "[red]Merge[/red]")

    console.print(table)

# Progress for downloads
def download_with_progress(url: str) -> bytes:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Downloading...", total=None)
        # ... download logic
    return data

# Status messages
console.print("[green]✓[/green] Update complete!")
console.print(Panel("Conflicts require manual resolution", title="Warning", style="yellow"))
```

**Alternatives Considered**:
- Plain print(): Works but ugly, no colors
- colorama: Colors only, no tables/progress
- click.echo(): Tied to Click framework
- textual: TUI apps (overkill for CLI output)

### 13. Linting and Formatting

**Decision**: Use `ruff` for both linting and formatting

**Rationale**:
- 10-100x faster than flake8 + black + isort combined
- Single tool replaces multiple tools
- Written in Rust, excellent performance
- Full compatibility with Black formatting
- Includes import sorting (isort replacement)
- Active development, growing rule set

**Configuration in pyproject.toml**:
```toml
[tool.ruff]
target-version = "py314"
line-length = 88

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**Alternatives Considered**:
- black + isort + flake8: Traditional but slow, multiple configs
- pylint: Comprehensive but slow, noisy
- pyright: Type checker only (using mypy)

## Resolved Clarifications

All NEEDS CLARIFICATION items from Technical Context have been resolved through this research. No outstanding unknowns remain.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hash algorithm mismatch | Low | High | Comprehensive test suite comparing Python and PowerShell outputs |
| Path case sensitivity edge cases | Medium | Medium | Extensive cross-platform testing |
| Performance regression | Low | Medium | Benchmark suite comparing to PowerShell baseline |
| Migration breaks existing manifests | Low | High | Backward compatibility tests with real-world manifests |
