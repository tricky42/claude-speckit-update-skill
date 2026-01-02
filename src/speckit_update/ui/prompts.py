"""Styled prompts and confirmations."""

from rich.panel import Panel
from rich.prompt import Confirm

from speckit_update.models import ConflictResult, UpdatePlan
from speckit_update.ui.console import console


def confirm_update(plan: UpdatePlan) -> bool:
    """Prompt user to confirm update.

    Args:
        plan: The update plan to confirm.

    Returns:
        True if user confirms, False otherwise.
    """
    if not plan.has_changes:
        console.print("[green]✓[/green] Already up to date!")
        return False

    # Show warning for conflicts
    if plan.has_conflicts:
        console.print(
            Panel(
                f"[yellow]⚠ Warning:[/yellow] {len(plan.files_to_merge)} file(s) "
                "have conflicts that will require manual resolution.",
                title="Conflicts Detected",
                border_style="yellow",
            )
        )

    # Show summary
    console.print()
    console.print(f"[bold]Update Summary:[/bold]")
    console.print(f"  Version: {plan.from_version} → {plan.to_version}")
    console.print(f"  Files affected: {plan.total_files_affected}")

    if plan.files_to_add:
        console.print(f"    [green]+ {len(plan.files_to_add)} new[/green]")
    if plan.files_to_update:
        console.print(f"    [yellow]~ {len(plan.files_to_update)} updated[/yellow]")
    if plan.files_to_merge:
        console.print(f"    [red]⚠ {len(plan.files_to_merge)} conflicts[/red]")
    if plan.files_to_remove:
        console.print(f"    [magenta]- {len(plan.files_to_remove)} removed[/magenta]")

    console.print()
    return Confirm.ask("Proceed with update?", default=False)


def confirm_rollback() -> bool:
    """Prompt user to confirm rollback.

    Returns:
        True if user confirms, False otherwise.
    """
    console.print(
        Panel(
            "[yellow]This will restore all files from the most recent backup.[/yellow]\n"
            "Any changes made after the last update will be preserved.",
            title="Rollback Confirmation",
            border_style="yellow",
        )
    )
    return Confirm.ask("Proceed with rollback?", default=False)


def show_conflict_summary(results: list[ConflictResult]) -> None:
    """Show summary of conflict resolution results.

    Args:
        results: List of merge results.
    """
    clean_merges = sum(1 for r in results if not r.has_conflicts)
    conflicts = sum(1 for r in results if r.has_conflicts)
    total_markers = sum(r.conflict_count for r in results)

    console.print()
    console.print("[bold]Merge Results:[/bold]")

    if clean_merges > 0:
        console.print(f"  [green]✓ {clean_merges} file(s) merged cleanly[/green]")

    if conflicts > 0:
        console.print(
            f"  [yellow]⚠ {conflicts} file(s) have {total_markers} conflict marker(s)[/yellow]"
        )
        console.print()
        console.print(
            "[dim]Resolve conflicts by editing files and removing conflict markers.[/dim]"
        )


def show_version_detected(version: str, confidence: str, method: str) -> None:
    """Show version detection result.

    Args:
        version: Detected version.
        confidence: Confidence level (HIGH, MEDIUM, LOW).
        method: Detection method used.
    """
    confidence_colors = {
        "HIGH": "green",
        "MEDIUM": "yellow",
        "LOW": "red",
    }
    color = confidence_colors.get(confidence.upper(), "white")

    console.print(
        Panel(
            f"[bold]Detected Version:[/bold] {version}\n"
            f"[bold]Confidence:[/bold] [{color}]{confidence}[/{color}]\n"
            f"[bold]Method:[/bold] {method}",
            title="Version Detection",
            border_style=color,
        )
    )


def show_no_manifest_warning() -> None:
    """Show warning when no manifest exists."""
    console.print(
        Panel(
            "[yellow]No manifest.json found.[/yellow]\n\n"
            "This appears to be the first time running speckit-update.\n"
            "Version detection will be attempted to create an initial manifest.",
            title="First Run Detected",
            border_style="yellow",
        )
    )
