"""Event constructors and utilities for the UI event queue.

All event payloads follow the UIEventType enum defined in PRD Section L.
"""

from __future__ import annotations

from typing import Any

from eyesite.core.models import (
    AppStatus,
    ErrorCode,
    Priority,
    UIEvent,
    UIEventType,
)


def create_spoken_message_event(
    message: str,
    priority: Priority = Priority.RESPONSE,
) -> UIEvent:
    """Create a SPOKEN_MESSAGE event for UI message logging."""
    return UIEvent(
        type=UIEventType.SPOKEN_MESSAGE,
        payload={"message": message, "priority": int(priority)},
    )


def create_status_changed_event(status: AppStatus) -> UIEvent:
    """Create a STATUS_CHANGED event to update UI indicators."""
    return UIEvent(
        type=UIEventType.STATUS_CHANGED,
        payload={"status": status},
    )


def create_ocr_text_event(
    full_text: str,
    spoken_text: str = "",
) -> UIEvent:
    """Create an OCR_TEXT event to display recognized text in the UI."""
    return UIEvent(
        type=UIEventType.OCR_TEXT,
        payload={"full_text": full_text, "spoken_text": spoken_text},
    )


def create_error_event(
    error_code: ErrorCode,
    message: str,
    details: dict[str, Any] | None = None,
) -> UIEvent:
    """Create an ERROR event to show an alert banner and notify the user."""
    payload: dict[str, Any] = {
        "error_code": str(error_code.value),
        "message": message,
    }
    if details:
        payload["details"] = details
    return UIEvent(
        type=UIEventType.ERROR,
        payload=payload,
    )


def create_listening_started_event() -> UIEvent:
    """Create a LISTENING_STARTED event to turn on the listening indicator."""
    return UIEvent(type=UIEventType.LISTENING_STARTED, payload={})


def create_listening_stopped_event() -> UIEvent:
    """Create a LISTENING_STOPPED event to turn off the listening indicator."""
    return UIEvent(type=UIEventType.LISTENING_STOPPED, payload={})


def create_show_help_event(help_text: str = "") -> UIEvent:
    """Create a SHOW_HELP event to trigger display of the help dialog."""
    return UIEvent(
        type=UIEventType.SHOW_HELP,
        payload={"help_text": help_text},
    )
