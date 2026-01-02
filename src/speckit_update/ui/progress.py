"""Progress bars and spinners for operations."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TransferSpeedColumn,
)

from speckit_update.ui.console import console


@contextmanager
def spinner(description: str) -> Generator[None]:
    """Show a spinner for indeterminate operations.

    Args:
        description: Text to show next to the spinner.

    Yields:
        None (context manager).
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description, total=None)
        yield


@contextmanager
def progress_bar(
    description: str,
    total: int,
) -> Generator[Progress]:
    """Show a progress bar for determinate operations.

    Args:
        description: Text to show with the progress bar.
        total: Total number of steps.

    Yields:
        Progress object for updating.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description, total=total)
        yield progress


def download_with_progress(
    client: httpx.Client,
    url: str,
    description: str = "Downloading",
) -> bytes:
    """Download content with a progress bar.

    Args:
        client: httpx client to use.
        url: URL to download.
        description: Text to show during download.

    Returns:
        Downloaded content as bytes.
    """
    with (
        Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=console,
            transient=True,
        ) as progress,
        client.stream("GET", url) as response,
    ):
        response.raise_for_status()

        # Get content length if available
        total = int(response.headers.get("content-length", 0))
        task = progress.add_task(description, total=total or None)

        # Download with progress
        chunks: list[bytes] = []
        for chunk in response.iter_bytes():
            chunks.append(chunk)
            progress.update(task, advance=len(chunk))

        return b"".join(chunks)


class OperationProgress:
    """Track progress of multi-step operations.

    Provides a simple interface for updating progress during
    multi-file operations.
    """

    def __init__(self, description: str, total: int) -> None:
        """Initialize operation progress.

        Args:
            description: Description of the operation.
            total: Total number of steps.
        """
        self.description = description
        self.total = total
        self._progress: Progress | None = None
        self._task: TaskID | None = None

    def __enter__(self) -> "OperationProgress":
        """Enter context and start progress display."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            console=console,
            transient=True,
        )
        self._progress.__enter__()
        self._task = self._progress.add_task(self.description, total=self.total)
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context and clean up."""
        if self._progress:
            self._progress.__exit__(*args)

    def advance(self, description: str | None = None) -> None:
        """Advance progress by one step.

        Args:
            description: Optional new description.
        """
        if self._progress and self._task is not None:
            if description:
                self._progress.update(self._task, description=description, advance=1)
            else:
                self._progress.update(self._task, advance=1)

    def update(self, description: str) -> None:
        """Update the progress description without advancing.

        Args:
            description: New description.
        """
        if self._progress and self._task is not None:
            self._progress.update(self._task, description=description)
