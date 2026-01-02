"""Rich table components for update plans and file states."""

from rich.table import Table

from speckit_update.models import FileState, UpdatePlan
from speckit_update.ui.console import console


# Color mapping for file states
STATE_COLORS = {
    FileState.ADD: "green",
    FileState.UPDATE: "yellow",
    FileState.MERGE: "red",
    FileState.REMOVE: "magenta",
    FileState.PRESERVE: "cyan",
    FileState.SKIP: "dim",
}

# Action text for file states
STATE_ACTIONS = {
    FileState.ADD: "Add",
    FileState.UPDATE: "Update",
    FileState.MERGE: "Merge (conflict)",
    FileState.REMOVE: "Remove",
    FileState.PRESERVE: "Preserve",
    FileState.SKIP: "Skip",
}


def show_update_plan(plan: UpdatePlan) -> None:
    """Display an update plan as a Rich table.

    Shows files categorized by action with color-coded status.

    Args:
        plan: The update plan to display.
    """
    if plan.is_up_to_date:
        console.print("[green]✓[/green] Already up to date!")
        return

    # Create table
    table = Table(
        title=f"Update Plan: {plan.from_version} → {plan.to_version}",
        show_header=True,
        header_style="bold",
    )
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Action", style="bold")
    table.add_column("Status")

    # Add files by category
    _add_files_to_table(table, plan.files_to_add, FileState.ADD, "New file")
    _add_files_to_table(table, plan.files_to_update, FileState.UPDATE, "Safe update")
    _add_files_to_table(table, plan.files_to_merge, FileState.MERGE, "Needs merge")
    _add_files_to_table(table, plan.files_to_remove, FileState.REMOVE, "To remove")
    _add_files_to_table(table, plan.files_to_preserve, FileState.PRESERVE, "Customized")

    console.print(table)

    # Print summary
    _print_summary(plan)


def _add_files_to_table(
    table: Table,
    files: tuple[str, ...],
    state: FileState,
    status: str,
) -> None:
    """Add files to the table with appropriate styling.

    Args:
        table: The Rich table to add rows to.
        files: List of file paths.
        state: The file state for color coding.
        status: Status text to display.
    """
    color = STATE_COLORS[state]
    action = STATE_ACTIONS[state]

    for file_path in files:
        table.add_row(
            file_path,
            f"[{color}]{action}[/{color}]",
            status,
        )


def _print_summary(plan: UpdatePlan) -> None:
    """Print summary statistics for the update plan.

    Args:
        plan: The update plan.
    """
    console.print()

    # Count by action
    counts = {
        "Add": len(plan.files_to_add),
        "Update": len(plan.files_to_update),
        "Merge": len(plan.files_to_merge),
        "Remove": len(plan.files_to_remove),
        "Preserve": len(plan.files_to_preserve),
    }

    # Show non-zero counts
    parts = []
    for action, count in counts.items():
        if count > 0:
            color = {
                "Add": "green",
                "Update": "yellow",
                "Merge": "red",
                "Remove": "magenta",
                "Preserve": "cyan",
            }[action]
            parts.append(f"[{color}]{count} {action.lower()}[/{color}]")

    if parts:
        console.print("Summary: " + ", ".join(parts))

    # Warnings
    if plan.has_conflicts:
        console.print()
        console.print(
            f"[yellow]⚠[/yellow] {len(plan.files_to_merge)} file(s) require manual merge resolution"
        )


def show_file_list(files: list[str], title: str, style: str = "cyan") -> None:
    """Display a simple list of files.

    Args:
        files: List of file paths.
        title: Title for the list.
        style: Rich style for the files.
    """
    if not files:
        return

    console.print(f"\n[bold]{title}:[/bold]")
    for file_path in files:
        console.print(f"  [{style}]{file_path}[/{style}]")
