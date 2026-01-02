"""Command-line interface for SpecKit Update.

This module provides the main entry point and argument parsing for
the speckit-update command.
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from speckit_update import __version__
from speckit_update.exceptions import (
    NetworkError,
    PrerequisiteError,
    RollbackError,
    SpecKitError,
    UserCancelledError,
)
from speckit_update.models import BackupEntry, ConflictResult, TrackedFile, UpdatePlan
from speckit_update.services.backup_manager import BackupManager
from speckit_update.services.conflict_detector import ConflictDetector
from speckit_update.services.github_client import GitHubClient
from speckit_update.services.manifest_manager import ManifestManager
from speckit_update.services.markdown_merger import MarkdownMerger
from speckit_update.services.release_extractor import ReleaseExtractor
from speckit_update.ui.console import console, error, header, info, success, warning
from speckit_update.ui.progress import OperationProgress, spinner
from speckit_update.ui.prompts import (
    confirm_rollback,
    confirm_update,
    show_conflict_summary,
    show_no_manifest_warning,
)
from speckit_update.ui.tables import show_update_plan
from speckit_update.utils.logging import setup_logging
from speckit_update.utils.paths import get_specify_dir


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="speckit-update",
        description="Update SpecKit installation safely, preserving customizations.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"speckit-update {__version__}",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check for updates without making changes",
    )
    parser.add_argument(
        "--proceed",
        action="store_true",
        help="Proceed with update (skip confirmation)",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback to previous version",
    )
    parser.add_argument(
        "--target-version",
        type=str,
        metavar="VERSION",
        help="Update to specific version (e.g., v0.0.79)",
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        metavar="PATH",
        help="Project directory (default: current directory)",
    )

    return parser


def validate_prerequisites(project_root: Path) -> None:
    """Validate that prerequisites are met.

    Args:
        project_root: Path to project root.

    Raises:
        PrerequisiteError: If prerequisites are not met.
    """
    # Check for .specify directory
    specify_dir = get_specify_dir(project_root)
    if not specify_dir.exists():
        raise PrerequisiteError(
            f"Not a SpecKit project: {project_root}\n"
            "No .specify/ directory found. Run 'speckit init' first."
        )


def run_check_only(
    project_root: Path,
    target_version: str | None = None,
) -> int:
    """Run check-only mode.

    Args:
        project_root: Path to project root.
        target_version: Specific version to check against (optional).

    Returns:
        Exit code.
    """
    header("SpecKit Update Check", f"Project: {project_root}")

    # Load manifest
    manager = ManifestManager(project_root)
    manifest = manager.load()

    if manifest is None:
        show_no_manifest_warning()
        info("Run without --check-only to set up manifest")
        return 0

    current_version = manifest.speckit_version
    info(f"Current version: {current_version}")

    # Fetch target release
    with GitHubClient() as client:
        if target_version:
            release = client.get_release(target_version)
        else:
            release = client.get_latest_release()

    target = release.tag_name
    info(f"Target version: {target}")

    if current_version == target:
        success("Already up to date!")
        return 0

    # For now, create a simple update plan
    # In full implementation, this would fetch upstream hashes
    plan = UpdatePlan.create(
        from_version=current_version,
        to_version=target,
        # TODO: Implement full file analysis
    )

    if plan.has_changes:
        show_update_plan(plan)
    else:
        success(f"No file changes needed for {current_version} → {target}")

    console.print()
    info("Run without --check-only to apply updates")

    return 0


def run_update(
    project_root: Path,
    target_version: str | None = None,
    proceed: bool = False,
) -> int:
    """Run update workflow.

    Args:
        project_root: Path to project root.
        target_version: Specific version to update to (optional).
        proceed: Skip confirmation if True.

    Returns:
        Exit code.
    """
    header("SpecKit Update", f"Project: {project_root}")

    # Load or create manifest
    manifest_manager = ManifestManager(project_root)
    manifest = manifest_manager.load()

    if manifest is None:
        show_no_manifest_warning()
        # TODO: Implement fingerprint detection and manifest creation
        warning("Manifest creation not yet implemented")
        return 1

    current_version = manifest.speckit_version
    info(f"Current version: {current_version}")

    # Track backup for rollback on error
    backup: BackupEntry | None = None
    backup_manager = BackupManager(project_root)

    try:
        # Fetch target release and download tarball
        with GitHubClient() as client:
            with spinner("Fetching release information..."):
                if target_version:
                    release = client.get_release(target_version)
                else:
                    release = client.get_latest_release()

            target = release.tag_name
            info(f"Target version: {target}")

            if current_version == target:
                success("Already up to date!")
                return 0

            # Download and extract release
            with spinner(f"Downloading {target}..."):
                extractor = ReleaseExtractor(client)
                extractor.download_and_extract(release)
                upstream_hashes = extractor.get_file_hashes()

        # Analyze files and create update plan
        with spinner("Analyzing files..."):
            detector = ConflictDetector(project_root, manifest, upstream_hashes)
            plan = detector.create_update_plan(current_version, target)

        if not plan.has_changes:
            success(f"No file changes needed for {current_version} → {target}")
            extractor.cleanup()
            return 0

        # Show plan and get confirmation
        show_update_plan(plan)

        if not proceed:
            if not confirm_update(plan):
                raise UserCancelledError()
        else:
            info("Proceeding with update (--proceed flag)")

        # Create backup before making changes
        with spinner("Creating backup..."):
            backup = backup_manager.create_backup(manifest, target)
            manifest.backup_history.append(backup)
        success(f"Backup created: {backup.path}")

        # Apply updates
        merge_results: list[ConflictResult] = []
        total_files = plan.total_files_affected
        merger = MarkdownMerger()

        with OperationProgress("Applying updates", total_files) as progress:
            # Add new files
            for file_path in plan.files_to_add:
                progress.update(f"Adding {file_path}")
                content = extractor.get_file_content(file_path)
                if content:
                    dest = project_root / file_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(content)
                progress.advance()

            # Update unchanged files
            for file_path in plan.files_to_update:
                progress.update(f"Updating {file_path}")
                content = extractor.get_file_content(file_path)
                if content:
                    dest = project_root / file_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(content)
                progress.advance()

            # Handle merge conflicts with 3-way merge
            for file_path in plan.files_to_merge:
                progress.update(f"Merging {file_path}")

                # Get all three versions
                current_path = project_root / file_path
                current_content = current_path.read_text() if current_path.exists() else ""

                incoming_bytes = extractor.get_file_content(file_path)
                incoming_content = incoming_bytes.decode("utf-8") if incoming_bytes else ""

                # Get base content from manifest
                tracked = next(
                    (t for t in manifest.tracked_files if t.path == file_path),
                    None,
                )
                # Base is what was originally installed
                base_content = ""
                if tracked and backup:
                    base_path = project_root / backup.path / file_path
                    if base_path.exists():
                        base_content = base_path.read_text()

                # Perform 3-way merge
                if file_path.endswith(".md"):
                    result = merger.merge(
                        base=base_content,
                        current=current_content,
                        incoming=incoming_content,
                        current_version=current_version,
                        incoming_version=target,
                    )
                else:
                    # For non-markdown files, use simple conflict markers
                    result = ConflictResult(
                        merged_content=_create_conflict_markers(
                            current_content, incoming_content, current_version, target
                        ),
                        has_conflicts=True,
                        conflict_count=1,
                    )

                # Write merged content
                current_path.write_text(result.merged_content)
                merge_results.append(result)
                progress.advance()

            # Remove files that are no longer in upstream
            for file_path in plan.files_to_remove:
                progress.update(f"Removing {file_path}")
                file_to_remove = project_root / file_path
                if file_to_remove.exists():
                    file_to_remove.unlink()
                progress.advance()

        # Update manifest with new version and hashes
        manifest.speckit_version = target
        manifest.last_updated = datetime.now()

        # Update tracked files
        new_tracked: list[TrackedFile] = []
        for file_path, file_hash in upstream_hashes.items():
            existing = next(
                (t for t in manifest.tracked_files if t.path == file_path),
                None,
            )
            if existing:
                # Check if file was merged (might be customized now)
                is_customized = file_path in plan.files_to_merge
                new_tracked.append(
                    TrackedFile(
                        path=file_path,
                        original_hash=file_hash,
                        customized=is_customized or existing.customized,
                        is_official=existing.is_official,
                    )
                )
            else:
                # New file
                new_tracked.append(
                    TrackedFile(
                        path=file_path,
                        original_hash=file_hash,
                        customized=False,
                        is_official=True,
                    )
                )

        manifest.tracked_files = new_tracked

        # Save updated manifest
        manifest_manager.save(manifest)

        # Cleanup old backups
        removed_backups = backup_manager.cleanup_old_backups(manifest)
        if removed_backups:
            info(f"Cleaned up {len(removed_backups)} old backup(s)")

        # Cleanup extractor temp files
        extractor.cleanup()

        # Show results
        console.print()
        success(f"Updated to {target}!")

        if merge_results:
            show_conflict_summary(merge_results)

        return 0

    except (SpecKitError, OSError) as e:
        # Automatic rollback on error
        if backup:
            warning("Update failed, rolling back...")
            try:
                backup_manager.restore_backup(backup)
                # Reload and save original manifest state
                original_manifest = manifest_manager.load()
                if original_manifest:
                    # Remove the failed backup from history
                    original_manifest.backup_history = [
                        b for b in original_manifest.backup_history
                        if b.path != backup.path
                    ]
                    manifest_manager.save(original_manifest)
                error(f"Update failed: {e}")
                info("Rolled back to previous state")
                return 6  # RollbackError exit code
            except RollbackError as rollback_e:
                error(f"Rollback also failed: {rollback_e}")
                error("Manual intervention may be required")
                return 6

        # No backup to rollback to
        error(f"Update failed: {e}")
        return 1


def _create_conflict_markers(
    current: str,
    incoming: str,
    current_version: str,
    incoming_version: str,
) -> str:
    """Create git-style conflict markers.

    Args:
        current: Current content.
        incoming: Incoming content.
        current_version: Current version label.
        incoming_version: Incoming version label.

    Returns:
        Content with conflict markers.
    """
    return f"""<<<<<<< Current ({current_version})
{current}
=======
{incoming}
>>>>>>> Incoming ({incoming_version})
"""


def run_rollback(project_root: Path) -> int:
    """Run rollback workflow.

    Args:
        project_root: Path to project root.

    Returns:
        Exit code.
    """
    header("SpecKit Rollback", f"Project: {project_root}")

    # Load manifest
    manifest_manager = ManifestManager(project_root)
    manifest = manifest_manager.load()

    if manifest is None:
        error("No manifest found. Cannot rollback.")
        return 1

    if not manifest.backup_history:
        error("No backups available. Cannot rollback.")
        return 1

    backup_manager = BackupManager(project_root)
    latest_backup = backup_manager.get_latest_backup(manifest)

    if latest_backup is None:
        error("No valid backup found.")
        return 1

    # Show backup info
    info(f"Most recent backup: {latest_backup.path}")
    info(f"From version: {latest_backup.from_version}")
    info(f"To version: {latest_backup.to_version}")
    info(f"Created: {latest_backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    # Confirm with user
    if not confirm_rollback():
        raise UserCancelledError()

    # Perform rollback
    try:
        with spinner("Restoring from backup..."):
            backup_manager.restore_backup(latest_backup)

        # Update manifest to reflect rollback
        manifest.speckit_version = latest_backup.from_version
        manifest.last_updated = datetime.now()

        # Remove this backup from history (it's been consumed)
        manifest.backup_history = [
            b for b in manifest.backup_history
            if b.path != latest_backup.path
        ]

        manifest_manager.save(manifest)

        success(f"Rolled back to {latest_backup.from_version}")
        return 0

    except RollbackError as e:
        error(f"Rollback failed: {e}")
        return 6


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv).

    Returns:
        Exit code.
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Set up logging
    setup_logging(verbose=args.verbose)

    try:
        # Validate prerequisites
        validate_prerequisites(args.project)

        # Route to appropriate command
        if args.rollback:
            return run_rollback(args.project)
        elif args.check_only:
            return run_check_only(args.project, args.target_version)
        else:
            return run_update(args.project, args.target_version, args.proceed)

    except UserCancelledError:
        info("Operation cancelled")
        return 5
    except PrerequisiteError as e:
        error(str(e))
        return e.exit_code
    except NetworkError as e:
        error(str(e))
        return e.exit_code
    except SpecKitError as e:
        error(str(e))
        return e.exit_code
    except KeyboardInterrupt:
        console.print()
        info("Interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
