"""Command-line interface for SpecKit Update.

This module provides the main entry point and argument parsing for
the speckit-update command.
"""

import argparse
import sys
from pathlib import Path

from speckit_update import __version__
from speckit_update.exceptions import (
    NetworkError,
    PrerequisiteError,
    SpecKitError,
    UserCancelledError,
)
from speckit_update.models import UpdatePlan
from speckit_update.services.conflict_detector import ConflictDetector
from speckit_update.services.github_client import GitHubClient
from speckit_update.services.manifest_manager import ManifestManager
from speckit_update.ui.console import console, error, header, info, success, warning
from speckit_update.ui.prompts import show_no_manifest_warning
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
    manager = ManifestManager(project_root)
    manifest = manager.load()

    if manifest is None:
        show_no_manifest_warning()
        # TODO: Implement fingerprint detection and manifest creation
        warning("Manifest creation not yet implemented")
        return 1

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

    # TODO: Implement full update workflow
    # - Create backup
    # - Download release
    # - Analyze files
    # - Apply updates
    # - Handle conflicts
    # - Update manifest

    warning("Full update workflow not yet implemented")
    info("Use --check-only to see available updates")

    return 0


def run_rollback(project_root: Path) -> int:
    """Run rollback workflow.

    Args:
        project_root: Path to project root.

    Returns:
        Exit code.
    """
    header("SpecKit Rollback", f"Project: {project_root}")

    # Load manifest
    manager = ManifestManager(project_root)
    manifest = manager.load()

    if manifest is None:
        error("No manifest found. Cannot rollback.")
        return 1

    if not manifest.backup_history:
        error("No backups available. Cannot rollback.")
        return 1

    # TODO: Implement rollback workflow
    warning("Rollback not yet implemented")

    return 0


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
