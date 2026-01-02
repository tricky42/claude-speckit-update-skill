"""Rich-integrated logging setup."""

import logging
from typing import Literal

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    *,
    verbose: bool = False,
    console: Console | None = None,
) -> logging.Logger:
    """Set up logging with Rich handler.

    Args:
        verbose: If True, set level to DEBUG. Otherwise INFO.
        console: Optional Rich console to use. Creates new one if not provided.

    Returns:
        Configured logger for speckit_update.
    """
    if console is None:
        console = Console()

    # Determine log level
    level = logging.DEBUG if verbose else logging.INFO

    # Configure Rich handler
    handler = RichHandler(
        console=console,
        show_time=verbose,
        show_path=verbose,
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
    )
    handler.setLevel(level)

    # Configure logger
    logger = logging.getLogger("speckit_update")
    logger.setLevel(level)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the speckit_update logger.

    Returns:
        The configured logger, or a basic one if not set up.
    """
    return logging.getLogger("speckit_update")


LogLevel = Literal["debug", "info", "warning", "error"]


def log(
    message: str,
    level: LogLevel = "info",
) -> None:
    """Log a message at the specified level.

    Convenience function for quick logging without getting the logger.

    Args:
        message: The message to log.
        level: Log level (debug, info, warning, error).
    """
    logger = get_logger()
    log_func = getattr(logger, level)
    log_func(message)
