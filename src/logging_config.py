"""Central logging configuration for the application.

Configures the root logger with:
- Console: WARNING and above (keeps terminal output minimal).
- Rotating file (app.log): DEBUG and above (full detail for debugging).

Usage: call setup_logging() once at application startup (e.g. in app.py main()).
Other modules use logging.getLogger(__name__) and log as needed.
"""

import logging
from logging.handlers import RotatingFileHandler


def setup_logging(log_file: str = "app.log") -> None:
    """
    Configure the root logger with console and rotating file handlers.
    Safe to call multiple times; only the first call adds handlers.
    """
    root = logging.getLogger()
    if root.handlers:
        return

    # --- Handlers ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # terminal: WARNING and above only

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,  # rotate when file hits 5 MB
        backupCount=3,  # keep up to 3 old rotated files (app.log.1, .2, .3)
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # file: everything

    # --- Formatter ---
    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "  # timestamp: when the event occurred
            "%(levelname)s | "  # DEBUG / INFO / WARNING / ERROR / CRITICAL
            "%(filename)s:"  # source file where the log call was made
            "%(lineno)d | "  # line number in that file
            "%(message)s"  # message: what you passed to logger.info(...) etc.
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # --- Root logger ---
    logging.basicConfig(
        level=logging.DEBUG,  # gate: records must pass this before handlers
        handlers=[console_handler, file_handler],
    )
