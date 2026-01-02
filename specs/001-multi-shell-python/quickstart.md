# Quickstart: Multi-Shell Python Support Development

**Feature**: 001-multi-shell-python
**Date**: 2026-01-02

## Prerequisites

- Python 3.14 or higher
- `uv` package manager (install from https://docs.astral.sh/uv/)
- Git

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip (if you have Python already)
pip install uv
```

### Verify Installation

```bash
uv --version
# Should output: uv 0.x.x or higher

python --version
# Should output: Python 3.14.x or higher (uv can install this for you)
```

## Project Setup

### 1. Clone and Navigate

```bash
cd claude-speckit-update-skill
```

### 2. Install Dependencies with uv

```bash
# uv automatically creates virtual environment and installs dependencies
uv sync

# Or install with dev dependencies
uv sync --dev
```

This installs:
- `httpx` for HTTP requests
- `rich` for beautiful terminal output
- `pytest` and `pytest-cov` for testing (dev)
- `mypy` for type checking (dev)
- `ruff` for linting and formatting (dev)

### 3. Verify Setup

```bash
# Run the CLI
uv run speckit-update --help

# Run tests
uv run pytest

# Type check
uv run mypy src/
```

## Development Commands

### Run the CLI

```bash
# Check for updates
uv run speckit-update --check-only

# Update with confirmation
uv run speckit-update --proceed

# Target specific version
uv run speckit-update --version v0.0.79

# Rollback last update
uv run speckit-update --rollback

# Verbose logging
uv run speckit-update --check-only --verbose
```

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=speckit_update --cov-report=term-missing

# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Specific test file
uv run pytest tests/unit/test_hash_utils.py

# Specific test
uv run pytest tests/unit/test_hash_utils.py::test_normalize_crlf

# Watch mode (re-run on changes)
uv run pytest-watch
```

### Type Checking

```bash
# Run mypy in strict mode
uv run mypy src/speckit_update --strict

# Run pyright (alternative)
uv run pyright src/speckit_update
```

### Code Quality

```bash
# Check with ruff (fast!)
uv run ruff check src/ tests/

# Fix auto-fixable issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/

# Check formatting without changes
uv run ruff format --check src/ tests/
```

### All Quality Checks (CI-style)

```bash
# Run all checks
uv run ruff check src/ tests/ && \
uv run ruff format --check src/ tests/ && \
uv run mypy src/ --strict && \
uv run pytest --cov=speckit_update
```

## Project Structure

```
# Project root (uv-managed)
pyproject.toml               # Project config, dependencies, tool settings
uv.lock                      # Locked dependencies (committed to git)
.python-version              # Python version for uv

src/speckit_update/
├── __init__.py              # Package init
├── __main__.py              # Entry point for `python -m speckit_update`
├── cli.py                   # CLI argument parsing and orchestration
├── models/                  # Data structures
│   ├── manifest.py          # Manifest, TrackedFile
│   ├── file_state.py        # FileState enum
│   └── ...
├── services/                # Business logic
│   ├── hash_utils.py        # File hashing
│   ├── github_client.py     # GitHub API with httpx
│   └── ...
├── ui/                      # Rich-based UI components
│   ├── console.py           # Shared Rich console
│   ├── tables.py            # Update plan tables
│   ├── progress.py          # Progress bars
│   └── prompts.py           # Styled prompts
└── utils/                   # Utilities
    ├── paths.py             # Cross-platform paths
    └── logging.py           # Rich-integrated logging
```

## Adding Dependencies

```bash
# Add runtime dependency
uv add httpx

# Add dev dependency
uv add --dev pytest-watch

# Remove dependency
uv remove some-package

# Update all dependencies
uv lock --upgrade
uv sync
```

## Common Development Tasks

### Adding a New Service

1. Create file in `src/speckit_update/services/`:

```python
# src/speckit_update/services/my_service.py
"""My service module."""

from speckit_update.models import SomeModel

def do_something(input: SomeModel) -> str:
    """Do something with input."""
    ...
```

2. Add tests in `tests/unit/`:

```python
# tests/unit/test_my_service.py
import pytest
from speckit_update.services.my_service import do_something

def test_do_something():
    result = do_something(...)
    assert result == expected
```

3. Export from `services/__init__.py`:

```python
from .my_service import do_something

__all__ = [..., "do_something"]
```

### Adding a Rich UI Component

```python
# src/speckit_update/ui/my_component.py
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def show_status(message: str, success: bool = True) -> None:
    """Display a status message with appropriate styling."""
    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")

def show_file_table(files: list[str], title: str) -> None:
    """Display a table of files."""
    table = Table(title=title)
    table.add_column("File", style="cyan")
    for file in files:
        table.add_row(file)
    console.print(table)
```

### Migrating a PowerShell Function

1. Find the PowerShell function in `scripts/modules/`
2. Create equivalent Python function with same logic
3. Use the same function name (converted to snake_case)
4. Add comprehensive tests
5. Verify hash/behavior compatibility with existing data

Example migration:

```powershell
# PowerShell: HashUtils.psm1
function Get-NormalizedHash {
    param([string]$Content)
    # Remove BOM, normalize CRLF, trim lines
    ...
}
```

```python
# Python: services/hash_utils.py
def get_normalized_hash(content: bytes) -> str:
    """Calculate normalized SHA-256 hash.

    Normalization:
    1. Remove BOM if present
    2. Convert CRLF to LF
    3. Strip trailing whitespace per line
    4. Encode as UTF-8
    5. Return sha256:{hex}
    """
    ...
```

## Testing Against PowerShell

To verify Python produces identical results to PowerShell:

```bash
# Generate test fixtures from PowerShell
pwsh -File scripts/generate_test_fixtures.ps1

# Run compatibility tests
uv run pytest tests/compatibility/ -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub API token for higher rate limits | None |
| `GITHUB_PAT` | Alternative name for GitHub token | None |
| `SPECKIT_VERBOSE` | Enable verbose logging | `false` |
| `NO_COLOR` | Disable Rich colors (for CI) | Not set |

## Debugging

### Enable Debug Logging

```python
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[RichHandler(rich_tracebacks=True)]
)
```

Or via CLI:
```bash
uv run speckit-update --check-only --verbose
```

### Inspect Manifest

```python
from speckit_update.services.manifest_manager import load_manifest
from pathlib import Path

manifest = load_manifest(Path(".specify/manifest.json"))
print(f"Version: {manifest.speckit_version}")
print(f"Tracked files: {len(manifest.tracked_files)}")
```

### Test Hash Calculation

```python
from speckit_update.services.hash_utils import get_normalized_hash
from pathlib import Path

content = Path("some/file.md").read_bytes()
hash_value = get_normalized_hash(content)
print(hash_value)  # sha256:abc123...
```

### Interactive REPL with Project Loaded

```bash
uv run python
>>> from speckit_update.services import *
>>> from speckit_update.models import *
```

## Troubleshooting

### "Module not found" errors

Ensure dependencies are synced:
```bash
uv sync --dev
```

### Type checking errors

Make sure you're using Python 3.14+:
```bash
uv run python --version
```

### Tests failing on Windows

Path normalization issues - ensure using `pathlib.Path` consistently.

### Hash mismatch with PowerShell

Check normalization order:
1. BOM removal
2. CRLF → LF
3. Trailing whitespace strip
4. UTF-8 encode
5. SHA-256 hash

### Rich output looks wrong

Check terminal capabilities:
```python
from rich.console import Console
console = Console()
console.print(console.options)
```

For CI environments, set `NO_COLOR=1` to disable colors.
