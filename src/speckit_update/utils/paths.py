"""Cross-platform path handling utilities."""

from pathlib import Path, PurePath


def normalize_path(path: str | Path) -> str:
    """Normalize path for consistent comparison.

    Converts path to forward slashes and lowercase for case-insensitive
    comparison across platforms.

    Args:
        path: The path to normalize.

    Returns:
        Normalized path string with forward slashes, lowercase.
    """
    # Convert to PurePath for platform-independent handling
    pure_path = PurePath(path)
    # Use forward slashes and lowercase
    return str(pure_path).replace("\\", "/").lower()


def paths_equal(a: str | Path, b: str | Path) -> bool:
    """Compare paths case-insensitively.

    Per spec: case-preserving but case-insensitive comparison
    for consistent behavior across all platforms.

    Args:
        a: First path.
        b: Second path.

    Returns:
        True if paths are equivalent.
    """
    return normalize_path(a) == normalize_path(b)


def to_relative_path(path: Path, base: Path) -> str:
    """Convert absolute path to relative path with forward slashes.

    Args:
        path: The absolute path.
        base: The base directory.

    Returns:
        Relative path string with forward slashes.
    """
    try:
        relative = path.relative_to(base)
        return str(relative).replace("\\", "/")
    except ValueError:
        # Path is not relative to base
        return str(path).replace("\\", "/")


def ensure_forward_slashes(path: str) -> str:
    """Ensure path uses forward slashes.

    Args:
        path: Path string that may use backslashes.

    Returns:
        Path string with forward slashes only.
    """
    return path.replace("\\", "/")


def get_manifest_path(project_root: Path) -> Path:
    """Get the path to manifest.json.

    Args:
        project_root: The project root directory.

    Returns:
        Path to .specify/manifest.json
    """
    return project_root / ".specify" / "manifest.json"


def get_backup_dir(project_root: Path) -> Path:
    """Get the path to backups directory.

    Args:
        project_root: The project root directory.

    Returns:
        Path to .specify/backups/
    """
    return project_root / ".specify" / "backups"


def get_specify_dir(project_root: Path) -> Path:
    """Get the path to .specify directory.

    Args:
        project_root: The project root directory.

    Returns:
        Path to .specify/
    """
    return project_root / ".specify"
