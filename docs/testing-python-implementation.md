# Testing the Python Implementation

This guide covers how to test the new Python-based SpecKit Update implementation.

## Prerequisites

### Python 3.14+

The implementation requires Python 3.14 or later. Verify your version:

```bash
python3 --version
# Should output: Python 3.14.x
```

### uv Package Manager

Install `uv` if not already installed:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

## Quick Start

```bash
# Clone the repository
cd /path/to/claude-speckit-update-skill

# Install dependencies
uv sync --dev

# Run all unit tests
uv run pytest tests/unit/ -v

# Run with coverage
uv run pytest tests/unit/ --cov=speckit_update --cov-report=term-missing
```

## Running Tests

### Unit Tests

Run the full unit test suite (128 tests):

```bash
uv run pytest tests/unit/ -v
```

Run specific test files:

```bash
# Test hash utilities
uv run pytest tests/unit/test_hash_utils.py -v

# Test manifest management
uv run pytest tests/unit/test_manifest_manager.py -v

# Test conflict detection
uv run pytest tests/unit/test_conflict_detector.py -v

# Test markdown merger (3-way merge)
uv run pytest tests/unit/test_markdown_merger.py -v

# Test fingerprint detection
uv run pytest tests/unit/test_fingerprint_detector.py -v

# Test backup manager
uv run pytest tests/unit/test_backup_manager.py -v

# Test release extractor
uv run pytest tests/unit/test_release_extractor.py -v
```

### Test Coverage

Run tests with coverage report:

```bash
# Terminal report with missing lines
uv run pytest tests/unit/ --cov=speckit_update --cov-report=term-missing

# HTML coverage report
uv run pytest tests/unit/ --cov=speckit_update --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

Current coverage: **74%** on core business logic (excluding UI/CLI layers).

### Running Specific Test Classes

```bash
# Run all tests in a class
uv run pytest tests/unit/test_hash_utils.py::TestCalculateHash -v

# Run a single test
uv run pytest tests/unit/test_hash_utils.py::TestCalculateHash::test_returns_sha256_format -v
```

## Code Quality Checks

### Type Checking (mypy)

Run mypy in strict mode:

```bash
uv run mypy src/ --strict
```

Expected output: `Success: no issues found in 31 source files`

### Linting (ruff)

Check for linting issues:

```bash
uv run ruff check src/ tests/
```

Auto-fix issues:

```bash
uv run ruff check src/ tests/ --fix
```

### Formatting (ruff)

Check formatting:

```bash
uv run ruff format src/ tests/ --check
```

Apply formatting:

```bash
uv run ruff format src/ tests/
```

## Manual CLI Testing

### Check-Only Mode

Test the update check without making changes:

```bash
# From a SpecKit project directory
cd /path/to/your-speckit-project

# Run check-only
uv run --project /path/to/claude-speckit-update-skill speckit-update --check-only

# With verbose output
uv run --project /path/to/claude-speckit-update-skill speckit-update --check-only --verbose
```

### Version Targeting

Check for a specific version:

```bash
uv run speckit-update --check-only --target-version v0.0.80
```

### Rollback Testing

Test rollback functionality (requires existing backup):

```bash
uv run speckit-update --rollback
```

## Testing Scenarios

### Scenario 1: Fresh Project (No Manifest)

Test first-run onboarding with automatic version detection:

1. Create a test SpecKit project without `.specify/manifest.json`
2. Run `speckit-update --check-only`
3. Verify fingerprint detection identifies the installed version
4. Check confidence score is displayed

### Scenario 2: Update Available

1. Use a project with an older SpecKit version in manifest
2. Run `speckit-update --check-only`
3. Verify update plan shows files to add/update/preserve
4. Run `speckit-update --proceed` to apply updates
5. Verify backup was created in `.specify/backups/`

### Scenario 3: Customized Files

1. Modify a tracked file (e.g., add custom content to a command)
2. Run `speckit-update --check-only`
3. Verify file is detected as "customized" (PRESERVE state)
4. If upstream also changed, verify MERGE state with conflict markers

### Scenario 4: Rollback After Update

1. Perform an update with `speckit-update --proceed`
2. Run `speckit-update --rollback`
3. Verify files are restored to pre-update state
4. Verify manifest version is reverted

### Scenario 5: Invalid Version

Test error handling for non-existent versions:

```bash
uv run speckit-update --target-version v99.99.99 --check-only
```

Should display available versions and suggestions.

## Test Data Locations

- **Unit test fixtures**: `tests/conftest.py`
- **Fingerprint database**: `src/speckit_update/data/speckit-fingerprints.json`
- **Sample manifests**: Created dynamically in tests using `tmp_path` fixture

## Debugging Tests

### Verbose pytest output

```bash
uv run pytest tests/unit/ -v --tb=long
```

### Stop on first failure

```bash
uv run pytest tests/unit/ -x
```

### Run with print statements visible

```bash
uv run pytest tests/unit/ -s
```

### Debug specific test

```bash
uv run pytest tests/unit/test_hash_utils.py::TestCalculateHash::test_returns_sha256_format -v --tb=long -s
```

## Environment Variables

For GitHub API testing with authentication:

```bash
# Set GitHub token for higher rate limits
export GITHUB_TOKEN=ghp_your_token_here
# or
export GITHUB_PAT=ghp_your_token_here

# Then run tests
uv run pytest tests/unit/test_github_client.py -v
```

## Continuous Integration

The test suite is designed to run in CI environments:

```bash
# Full CI check
uv sync --dev
uv run mypy src/ --strict
uv run ruff check src/ tests/
uv run pytest tests/unit/ --cov=speckit_update --cov-fail-under=74
```

## Troubleshooting

### Python Version Mismatch

If `uv` downloads a different Python version:

```bash
# Check .python-version file
cat .python-version
# Should be: 3.14

# Force specific Python
uv run --python 3.14 pytest tests/unit/ -v
```

### Import Errors

If you see import errors, ensure the package is installed:

```bash
uv sync --dev
uv pip list | grep speckit
```

### Coverage Below Threshold

The coverage threshold is set to 74%. If tests fail due to coverage:

```bash
# Check which lines are missing coverage
uv run pytest tests/unit/ --cov=speckit_update --cov-report=term-missing

# Focus on files with low coverage:
# - github_client.py (23%) - requires network mocking
# - fingerprint_detector.py (37%) - needs fingerprint database tests
```

## Test Architecture

```
tests/
├── conftest.py              # Shared fixtures (manifests, releases, etc.)
└── unit/
    ├── test_backup_manager.py       # Backup/restore operations
    ├── test_conflict_detector.py    # File state analysis
    ├── test_fingerprint_detector.py # Version detection
    ├── test_github_client.py        # API client (mocked)
    ├── test_hash_utils.py           # Normalized hashing
    ├── test_manifest_manager.py     # Manifest CRUD
    ├── test_markdown_merger.py      # 3-way merge
    ├── test_models.py               # Data models
    ├── test_paths.py                # Path utilities
    ├── test_release_extractor.py    # Tarball extraction
    └── test_validation.py           # Input validation
```

## Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Development setup and architecture
- [spec.md](../specs/001-multi-shell-python/spec.md) - Feature specification
- [plan.md](../specs/001-multi-shell-python/plan.md) - Implementation plan
