"""Update plan data model."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UpdatePlan:
    """Complete update analysis ready for execution.

    Aggregates all file analyses into actionable lists categorized
    by the type of action needed.
    """

    from_version: str
    """Current SpecKit version."""

    to_version: str
    """Target SpecKit version."""

    files_to_add: tuple[str, ...] = field(default_factory=tuple)
    """New files to create."""

    files_to_update: tuple[str, ...] = field(default_factory=tuple)
    """Existing files to overwrite (safe)."""

    files_to_merge: tuple[str, ...] = field(default_factory=tuple)
    """Files requiring conflict resolution."""

    files_to_remove: tuple[str, ...] = field(default_factory=tuple)
    """Files to delete."""

    files_to_preserve: tuple[str, ...] = field(default_factory=tuple)
    """Customized files to keep unchanged."""

    @property
    def has_changes(self) -> bool:
        """True if any updates are available."""
        return bool(
            self.files_to_add
            or self.files_to_update
            or self.files_to_merge
            or self.files_to_remove
        )

    @property
    def has_conflicts(self) -> bool:
        """True if manual merge resolution needed."""
        return bool(self.files_to_merge)

    @property
    def total_files_affected(self) -> int:
        """Total number of files that will be modified."""
        return (
            len(self.files_to_add)
            + len(self.files_to_update)
            + len(self.files_to_merge)
            + len(self.files_to_remove)
        )

    @property
    def is_up_to_date(self) -> bool:
        """True if no updates are needed."""
        return self.from_version == self.to_version and not self.has_changes

    @classmethod
    def up_to_date(cls, version: str) -> "UpdatePlan":
        """Create a plan indicating no updates are needed.

        Args:
            version: Current and target version (same).

        Returns:
            UpdatePlan with no changes.
        """
        return cls(from_version=version, to_version=version)

    @classmethod
    def create(
        cls,
        from_version: str,
        to_version: str,
        *,
        add: list[str] | None = None,
        update: list[str] | None = None,
        merge: list[str] | None = None,
        remove: list[str] | None = None,
        preserve: list[str] | None = None,
    ) -> "UpdatePlan":
        """Create an update plan with the specified file lists.

        Args:
            from_version: Current SpecKit version.
            to_version: Target SpecKit version.
            add: Files to add.
            update: Files to update.
            merge: Files requiring merge.
            remove: Files to remove.
            preserve: Files to preserve.

        Returns:
            UpdatePlan with the specified actions.
        """
        return cls(
            from_version=from_version,
            to_version=to_version,
            files_to_add=tuple(add or []),
            files_to_update=tuple(update or []),
            files_to_merge=tuple(merge or []),
            files_to_remove=tuple(remove or []),
            files_to_preserve=tuple(preserve or []),
        )
