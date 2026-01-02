"""Validation utilities for paths, hashes, and versions."""

import re

# Regex patterns for validation
HASH_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")
VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


def validate_path(path: str) -> None:
    """Validate file path format.

    Args:
        path: The file path to validate.

    Raises:
        ValueError: If path is invalid.
    """
    if not path:
        raise ValueError("Path cannot be empty")
    if path.startswith("/") or path.startswith("\\"):
        raise ValueError("Path must be relative")
    if ".." in path:
        raise ValueError("Path cannot contain '..'")
    # Check for null bytes (security)
    if "\x00" in path:
        raise ValueError("Path cannot contain null bytes")


def validate_hash(hash_value: str) -> None:
    """Validate hash format.

    Expected format: sha256:{64 hex characters}

    Args:
        hash_value: The hash string to validate.

    Raises:
        ValueError: If hash format is invalid.
    """
    if not hash_value:
        raise ValueError("Hash cannot be empty")
    if not HASH_PATTERN.match(hash_value):
        raise ValueError(f"Invalid hash format: {hash_value}")


def validate_version(version: str) -> None:
    """Validate version format.

    Expected format: v{major}.{minor}.{patch} (e.g., v0.0.79)

    Args:
        version: The version string to validate.

    Raises:
        ValueError: If version format is invalid.
    """
    if not version:
        raise ValueError("Version cannot be empty")
    if not VERSION_PATTERN.match(version):
        raise ValueError(f"Invalid version format: {version}")


def is_valid_path(path: str) -> bool:
    """Check if path is valid without raising.

    Args:
        path: The file path to check.

    Returns:
        True if valid, False otherwise.
    """
    try:
        validate_path(path)
        return True
    except ValueError:
        return False


def is_valid_hash(hash_value: str) -> bool:
    """Check if hash is valid without raising.

    Args:
        hash_value: The hash string to check.

    Returns:
        True if valid, False otherwise.
    """
    try:
        validate_hash(hash_value)
        return True
    except ValueError:
        return False


def is_valid_version(version: str) -> bool:
    """Check if version is valid without raising.

    Args:
        version: The version string to check.

    Returns:
        True if valid, False otherwise.
    """
    try:
        validate_version(version)
        return True
    except ValueError:
        return False
