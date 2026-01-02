"""Shared Rich console instance and output utilities."""

from rich.console import Console
from rich.panel import Panel
from rich.style import Style

# Shared console instance for all UI output
console = Console()

# Styles for different message types
STYLE_SUCCESS = Style(color="green", bold=True)
STYLE_WARNING = Style(color="yellow", bold=True)
STYLE_ERROR = Style(color="red", bold=True)
STYLE_INFO = Style(color="cyan")
STYLE_DIM = Style(dim=True)


def success(message: str) -> None:
    """Print a success message with green checkmark.

    Args:
        message: The success message to display.
    """
    console.print(f"[green]✓[/green] {message}")


def warning(message: str) -> None:
    """Print a warning message with yellow warning symbol.

    Args:
        message: The warning message to display.
    """
    console.print(f"[yellow]⚠[/yellow] {message}", style="bold")


def error(message: str) -> None:
    """Print an error message with red X symbol.

    Args:
        message: The error message to display.
    """
    console.print(f"[red]✗[/red] {message}", style="bold red")


def info(message: str) -> None:
    """Print an info message with cyan color.

    Args:
        message: The info message to display.
    """
    console.print(f"[cyan]ℹ[/cyan] {message}")


def dim(message: str) -> None:
    """Print a dimmed message for less important info.

    Args:
        message: The message to display dimmed.
    """
    console.print(message, style=STYLE_DIM)


def header(title: str, subtitle: str | None = None) -> None:
    """Print a styled header panel.

    Args:
        title: The main header text.
        subtitle: Optional subtitle text.
    """
    content = f"[bold]{title}[/bold]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, expand=False))


def section(title: str) -> None:
    """Print a section divider.

    Args:
        title: The section title.
    """
    console.print()
    console.rule(f"[bold]{title}[/bold]")
    console.print()


def blank_line() -> None:
    """Print a blank line."""
    console.print()


def print_version_info(current: str, target: str) -> None:
    """Print version transition information.

    Args:
        current: Current SpecKit version.
        target: Target SpecKit version.
    """
    if current == target:
        console.print(f"[green]Up to date:[/green] {current}")
    else:
        console.print(f"[cyan]Current:[/cyan] {current} → [green]Target:[/green] {target}")
