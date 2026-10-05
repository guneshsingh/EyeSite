"""Logging initialization for EyeSite.

PRD Section F.7 (FR-CORE-05) specification.
Configures rotating log file in logs/eyesite.log plus console output.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_level: str = "INFO",
    log_file: str | Path = "logs/eyesite.log",
    max_bytes: int = 1_048_576,  # 1 MB
    backup_count: int = 3,
) -> logging.Logger:
    """Configure root logger with a rotating file handler and console handler.

    Args:
        log_level: Logging severity level (e.g. DEBUG, INFO, WARNING, ERROR).
        log_file: Path to destination log file.
        max_bytes: Maximum size of a log file before rotation.
        backup_count: Number of rotated backup files to retain.

    Returns:
        The configured root logger.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if root_logger.handlers:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s (%(threadName)s): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating File Handler
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    root_logger.info("EyeSite logging initialized at %s level", log_level.upper())
    return root_logger
