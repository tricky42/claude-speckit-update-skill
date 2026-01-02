"""Normalized SHA-256 hashing utilities.

This module provides hash calculation with normalization to ensure
consistent hashes across platforms and editors:
- Remove BOM (0xFEFF)
- Convert CRLF to LF
- Strip trailing whitespace per line
"""

import hashlib
from pathlib import Path


def normalize_content(content: bytes) -> bytes:
    """Normalize content for consistent hashing.

    Applies the following normalizations:
    1. Remove UTF-8 BOM if present (0xEF 0xBB 0xBF)
    2. Convert CRLF to LF
    3. Strip trailing whitespace from each line
    4. Ensure single trailing newline

    Args:
        content: Raw file content as bytes.

    Returns:
        Normalized content as bytes.
    """
    # Decode to string (handle BOM automatically with utf-8-sig)
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        # If not valid UTF-8, return content as-is for binary files
        return content

    # Normalize line endings: CRLF -> LF
    text = text.replace("\r\n", "\n")

    # Strip trailing whitespace from each line
    lines = text.split("\n")
    lines = [line.rstrip() for line in lines]
    text = "\n".join(lines)

    # Ensure single trailing newline (if file had content)
    if text and not text.endswith("\n"):
        text += "\n"

    return text.encode("utf-8")


def calculate_hash(content: bytes) -> str:
    """Calculate normalized SHA-256 hash of content.

    Args:
        content: Raw file content as bytes.

    Returns:
        Hash in format 'sha256:{64 hex characters}'.
    """
    normalized = normalize_content(content)
    hash_obj = hashlib.sha256(normalized)
    return f"sha256:{hash_obj.hexdigest()}"


def calculate_file_hash(path: Path) -> str:
    """Calculate normalized SHA-256 hash of a file.

    Args:
        path: Path to the file.

    Returns:
        Hash in format 'sha256:{64 hex characters}'.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        PermissionError: If the file can't be read.
    """
    content = path.read_bytes()
    return calculate_hash(content)


def get_normalized_hash(file_path: str | Path) -> str:
    """Get normalized hash for a file path.

    Convenience function matching PowerShell Get-NormalizedHash interface.

    Args:
        file_path: Path to the file (string or Path object).

    Returns:
        Hash in format 'sha256:{64 hex characters}'.
    """
    return calculate_file_hash(Path(file_path))


def hashes_match(hash1: str, hash2: str) -> bool:
    """Compare two hashes for equality.

    Args:
        hash1: First hash value.
        hash2: Second hash value.

    Returns:
        True if hashes are identical.
    """
    return hash1 == hash2


def is_content_modified(
    current_hash: str,
    original_hash: str,
) -> bool:
    """Check if content has been modified from original.

    Args:
        current_hash: Current file hash.
        original_hash: Original hash from manifest.

    Returns:
        True if the file has been modified.
    """
    return current_hash != original_hash
