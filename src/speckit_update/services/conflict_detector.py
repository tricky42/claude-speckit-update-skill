"""File state analysis and conflict detection.

This module analyzes files to determine their state relative to the
manifest and upstream release, categorizing them for update actions.
"""

from pathlib import Path

from speckit_update.models import (
    FileAnalysis,
    FileState,
    Manifest,
    Release,
    TrackedFile,
    UpdatePlan,
)
from speckit_update.services.hash_utils import calculate_file_hash


class ConflictDetector:
    """Detects file states and creates update plans.

    Analyzes each tracked file to determine whether it should be:
    - Added (new in upstream)
    - Updated (unchanged locally, changed upstream)
    - Merged (changed locally AND upstream - conflict)
    - Preserved (changed locally, unchanged upstream)
    - Removed (deleted from upstream)
    - Skipped (no changes needed)
    """

    def __init__(
        self,
        project_root: Path,
        manifest: Manifest,
        upstream_hashes: dict[str, str],
    ) -> None:
        """Initialize the conflict detector.

        Args:
            project_root: Path to project root.
            manifest: Current manifest.
            upstream_hashes: Map of file paths to upstream hashes.
        """
        self.project_root = project_root
        self.manifest = manifest
        self.upstream_hashes = upstream_hashes
        self._tracked_by_path: dict[str, TrackedFile] = {
            f.path: f for f in manifest.tracked_files
        }

    def analyze_file(self, path: str) -> FileAnalysis:
        """Analyze a single file's state.

        Args:
            path: Relative file path.

        Returns:
            FileAnalysis with determined state.
        """
        tracked = self._tracked_by_path.get(path)
        upstream_hash = self.upstream_hashes.get(path)
        file_path = self.project_root / path

        # Get current hash if file exists
        current_hash: str | None = None
        if file_path.exists():
            try:
                current_hash = calculate_file_hash(file_path)
            except (OSError, PermissionError):
                current_hash = None

        # Get manifest hash
        manifest_hash = tracked.original_hash if tracked else None

        # Determine state using flowchart logic
        state = self._determine_state(
            tracked=tracked,
            current_hash=current_hash,
            manifest_hash=manifest_hash,
            upstream_hash=upstream_hash,
        )

        return FileAnalysis(
            path=path,
            state=state,
            current_hash=current_hash,
            manifest_hash=manifest_hash,
            upstream_hash=upstream_hash,
        )

    def _determine_state(
        self,
        *,
        tracked: TrackedFile | None,
        current_hash: str | None,
        manifest_hash: str | None,
        upstream_hash: str | None,
    ) -> FileState:
        """Determine file state based on hashes.

        Implements the state determination flowchart from data-model.md.

        Args:
            tracked: TrackedFile from manifest (if exists).
            current_hash: Current file hash (if file exists).
            manifest_hash: Hash from manifest.
            upstream_hash: Hash from upstream release.

        Returns:
            Appropriate FileState.
        """
        # Is file in manifest?
        if tracked is None:
            # Not tracked - is it in upstream?
            if upstream_hash is not None:
                return FileState.ADD
            return FileState.SKIP

        # File is in manifest - is it in upstream?
        if upstream_hash is None:
            # Removed from upstream
            if tracked.customized:
                return FileState.PRESERVE
            return FileState.REMOVE

        # File is in both manifest and upstream
        # Is it customized locally?
        is_customized = current_hash != manifest_hash if current_hash else False

        if not is_customized:
            # Not customized - check for upstream changes
            if manifest_hash != upstream_hash:
                return FileState.UPDATE
            return FileState.SKIP

        # File is customized - check for upstream changes
        if manifest_hash != upstream_hash:
            return FileState.MERGE
        return FileState.PRESERVE

    def analyze_all_files(self) -> list[FileAnalysis]:
        """Analyze all tracked and upstream files.

        Returns:
            List of FileAnalysis for all files.
        """
        # Collect all unique paths
        paths = set(self._tracked_by_path.keys())
        paths.update(self.upstream_hashes.keys())

        # Analyze each
        analyses = [self.analyze_file(path) for path in sorted(paths)]
        return analyses

    def create_update_plan(
        self,
        from_version: str,
        to_version: str,
    ) -> UpdatePlan:
        """Create an update plan from file analyses.

        Args:
            from_version: Current SpecKit version.
            to_version: Target SpecKit version.

        Returns:
            UpdatePlan ready for execution.
        """
        analyses = self.analyze_all_files()

        add_files: list[str] = []
        update_files: list[str] = []
        merge_files: list[str] = []
        remove_files: list[str] = []
        preserve_files: list[str] = []

        for analysis in analyses:
            match analysis.state:
                case FileState.ADD:
                    add_files.append(analysis.path)
                case FileState.UPDATE:
                    update_files.append(analysis.path)
                case FileState.MERGE:
                    merge_files.append(analysis.path)
                case FileState.REMOVE:
                    remove_files.append(analysis.path)
                case FileState.PRESERVE:
                    preserve_files.append(analysis.path)
                case FileState.SKIP:
                    pass  # No action needed

        return UpdatePlan.create(
            from_version=from_version,
            to_version=to_version,
            add=add_files,
            update=update_files,
            merge=merge_files,
            remove=remove_files,
            preserve=preserve_files,
        )


def detect_conflicts(
    project_root: Path,
    manifest: Manifest,
    upstream_hashes: dict[str, str],
    target_version: str,
) -> UpdatePlan:
    """Convenience function to detect conflicts and create update plan.

    Args:
        project_root: Path to project root.
        manifest: Current manifest.
        upstream_hashes: Map of file paths to upstream hashes.
        target_version: Target SpecKit version.

    Returns:
        UpdatePlan for the update.
    """
    detector = ConflictDetector(project_root, manifest, upstream_hashes)
    return detector.create_update_plan(
        from_version=manifest.speckit_version,
        to_version=target_version,
    )
