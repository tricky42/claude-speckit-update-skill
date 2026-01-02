# Quickstart: Multi-Shell Python Support Development

**Feature**: 001-multi-shell-python
**Date**: 2026-01-02

## Prerequisites

- Python 3.14 or higher
- pip (comes with Python)
- Git

### Verify Python Version

```bash
python --version
# Should output: Python 3.14.x or higher
```

## Project Setup

### 1. Clone and Navigate

```bash
cd claude-speckit-update-skill
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 3. Install in Development Mode

```bash
pip install -e ".[dev]"
```

This installs:
- The `speckit_update` package in editable mode
- `requests` for HTTP
- `pytest` and `pytest-cov` for testing
- `mypy` for type checking

## Development Commands

### Run the CLI

```bash
# Check for updates
python -m speckit_update --check-only

# Update with confirmation
python -m speckit_update --proceed

# Target specific version
python -m speckit_update --version v0.0.79

# Rollback last update
python -m speckit_update --rollback

# Verbose logging
python -m speckit_update --check-only --verbose
```

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=speckit_update --cov-report=term-missing

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_hash_utils.py

# Specific test
pytest tests/unit/test_hash_utils.py::test_normalize_crlf
```

### Type Checking

```bash
# Run mypy in strict mode
mypy src/speckit_update --strict

# Run pyright (alternative)
pyright src/speckit_update
```

### Code Quality

```bash
# Format with black
black src/ tests/

# Sort imports
isort src/ tests/

# Lint with ruff
ruff check src/ tests/
```

## Project Structure

```
src/speckit_update/
├── __init__.py           # Package init
├── __main__.py           # Entry point for `python -m speckit_update`
├── cli.py                # CLI argument parsing and orchestration
├── models/               # Data structures
│   ├── manifest.py       # Manifest, TrackedFile
│   ├── file_state.py     # FileState enum
│   └── ...
├── services/             # Business logic
│   ├── hash_utils.py     # File hashing
│   ├── github_client.py  # GitHub API
│   └── ...
└── utils/                # Utilities
    ├── paths.py          # Cross-platform paths
    └── logging.py        # Logging setup
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

### Adding a New Model

1. Create or update file in `src/speckit_update/models/`:

```python
# src/speckit_update/models/my_model.py
from dataclasses import dataclass

@dataclass(frozen=True)
class MyModel:
    """Description of my model."""
    field: str
```

2. Export from `models/__init__.py`:

```python
from .my_model import MyModel

__all__ = [..., "MyModel"]
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
pytest tests/compatibility/ -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub API token for higher rate limits | None |
| `GITHUB_PAT` | Alternative name for GitHub token | None |
| `SPECKIT_VERBOSE` | Enable verbose logging | `false` |

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or via CLI:
```bash
python -m speckit_update --check-only --verbose
```

### Inspect Manifest

```python
from speckit_update.services.manifest_manager import load_manifest

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

## Troubleshooting

### "Module not found" errors

Ensure you've installed in development mode:
```bash
pip install -e ".[dev]"
```

### Type checking errors

Make sure you're using Python 3.14+:
```bash
python --version
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
