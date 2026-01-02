# SpecKit Safe Update

This skill provides safe update capabilities for GitHub SpecKit installations, preserving customizations while applying template updates.

**Installation**: Available via plugin (`/plugin marketplace add NotMyself/claude-plugins` then `/plugin install speckit-updater`) or manual Git clone. See [README.md](../../README.md#installation) for details.

## What to do when this skill is invoked

When the user invokes `/speckit-updater`, you should:

1. **Run the update CLI** without any flags (check-only mode first):
   ```bash
   uv run speckit-update --check-only
   ```

2. **Parse the output** and present it to the user:
   - Show current version vs. available version
   - Show files that will be updated/added/removed
   - Show any conflicts detected
   - Show files that will be preserved (customized)

3. **Ask the user for approval** to proceed with the update

4. **If approved**, run with `--proceed` flag:
   ```bash
   uv run speckit-update --proceed
   ```

5. **If declined**, inform the user the update was cancelled

**Special cases:**
- If user requests check-only: run with `--check-only` and show the report
- If user requests rollback: run with `--rollback` and confirm restoration
- If user requests specific version: include `--target-version` parameter

## Commands

### /speckit-updater

Updates SpecKit templates, commands, and scripts while preserving customizations.

**Usage:**
- `/speckit-updater` - Check for updates and show summary
- `/speckit-updater --proceed` - Proceed with update after approval
- `/speckit-updater --check-only` - Check for updates without applying (default)
- `/speckit-updater --target-version v0.0.79` - Update to specific version
- `/speckit-updater --rollback` - Restore from previous backup
- `/speckit-updater --verbose` - Enable debug logging

**Process:**
1. Validates prerequisites (Python 3.14+, .specify/ directory exists)
2. Loads or creates manifest (.specify/manifest.json)
3. Fetches target version from GitHub Releases API
4. Compares file hashes to identify customizations
5. Creates timestamped backup before modifications
6. Applies selective updates preserving customized files
7. Performs intelligent 3-way merge for conflicts (section-level for markdown)
8. Updates manifest with new version and hashes
9. Manages backup retention (keeps last 5)

**When you invoke this command, I will:**
1. Execute the speckit-update CLI
2. Present the update summary showing proposed changes
3. Wait for your approval via chat conversation
4. After approval: automatically run with `--proceed` flag to execute
5. Guide you through any conflict markers that need resolution
6. Report results with detailed summary

**Conversational Workflow:** The skill uses a two-step approval process:
- **Step 1**: `--check-only` shows summary → waits for approval
- **Step 2**: After approval, run with `--proceed` → applies updates

**Requirements:**
- Python 3.14+ installed
- `uv` package manager installed
- Internet connection for fetching updates from GitHub
- Write permissions to .specify/ and .claude/ directories

**Entry point command:**
```bash
uv run speckit-update [parameters]
```

## Features

- **Customization Preservation**: Automatically detects and preserves user customizations using normalized file hashing
- **Intelligent 3-Way Merge**: Section-based merge for markdown files with 80% fuzzy matching for renamed sections
- **Version Tracking**: Maintains `.specify/manifest.json` with file hashes, version info, and backup history
- **Automatic Backups**: Creates timestamped backups in `.specify/backups/` with automatic retention management
- **Fail-Fast with Rollback**: Automatically rolls back on any error, restoring pre-update state
- **Dry-Run Mode**: `--check-only` shows exactly what would change without applying updates
- **First-Run Detection**: Automatically detects installed version via fingerprinting for new users
- **Custom Command Safety**: User-created commands never overwritten
- **Rich CLI Output**: Beautiful terminal output with progress bars, tables, and colored status messages

## Architecture

### Python Modules (src/speckit_update/)
- **hash_utils**: Normalized SHA-256 hashing (handles line endings, trailing whitespace, BOM)
- **github_client**: GitHub Releases API with rate limit handling and retry logic
- **manifest_manager**: Manifest CRUD operations with JSON serialization
- **backup_manager**: Backup creation, restoration, and retention management
- **conflict_detector**: File state analysis and update plan creation
- **markdown_merger**: Intelligent 3-way merge with section-level conflict markers
- **fingerprint_detector**: Automatic version detection via file fingerprinting

### Workflow
1. Prerequisites validation (.specify/ directory exists)
2. Manifest loading/creation (with automatic version detection for first-time users)
3. GitHub API query for target version
4. File state analysis (6 actions: add/remove/merge/preserve/update/skip)
5. User confirmation with change preview (Rich tables)
6. Backup creation (timestamped)
7. Selective file updates with automatic rollback on error
8. Conflict resolution (3-way merge with section-level markers)
9. Manifest update (version, file hashes, customization flags)
10. Backup cleanup (keep 5 most recent)
11. Detailed summary display

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Prerequisites not met |
| 3 | Network/API error |
| 4 | Git error |
| 5 | User cancelled |
| 6 | Rollback required (automatic) |
