"""Conflict result data model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConflictResult:
    """Result of merging conflicting file versions.

    Produced by MarkdownMerger when performing 3-way merge on files
    that have both local customizations and upstream changes.
    """

    merged_content: str
    """The merged file content (may contain conflict markers)."""

    conflict_count: int
    """Number of conflict sections requiring manual resolution."""

    conflict_markers: tuple[tuple[int, int], ...]
    """Line ranges of conflict markers (start, end) pairs."""

    @property
    def has_conflicts(self) -> bool:
        """True if manual resolution is needed."""
        return self.conflict_count > 0

    @classmethod
    def clean_merge(cls, content: str) -> "ConflictResult":
        """Create a result representing a clean merge with no conflicts.

        Args:
            content: The successfully merged content.

        Returns:
            ConflictResult with zero conflicts.
        """
        return cls(
            merged_content=content,
            conflict_count=0,
            conflict_markers=(),
        )

    @classmethod
    def with_conflicts(
        cls,
        content: str,
        markers: list[tuple[int, int]],
    ) -> "ConflictResult":
        """Create a result with conflict markers.

        Args:
            content: The merged content containing conflict markers.
            markers: List of (start_line, end_line) tuples for each conflict.

        Returns:
            ConflictResult with conflict information.
        """
        return cls(
            merged_content=content,
            conflict_count=len(markers),
            conflict_markers=tuple(markers),
        )
