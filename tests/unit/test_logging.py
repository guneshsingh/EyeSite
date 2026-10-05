"""Unit tests for logging initialization."""

import logging
from pathlib import Path

from eyesite.core.logging_setup import setup_logging


def test_setup_logging_creates_file(tmp_path: Path) -> None:
    """Test that setup_logging creates the log file and attaches handlers."""
    log_file = tmp_path / "logs" / "test_eyesite.log"
    logger = setup_logging(log_level="DEBUG", log_file=log_file)

    assert isinstance(logger, logging.Logger)
    logger.debug("Debug test message")
    logger.info("Info test message")

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Info test message" in content
    assert "Debug test message" in content
