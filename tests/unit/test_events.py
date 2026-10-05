"""Unit tests for UI event helper functions."""

from eyesite.core.events import (
    create_error_event,
    create_listening_started_event,
    create_listening_stopped_event,
    create_ocr_text_event,
    create_show_help_event,
    create_spoken_message_event,
    create_status_changed_event,
)
from eyesite.core.models import (
    AppState,
    AppStatus,
    ErrorCode,
    Priority,
    UIEventType,
)


def test_create_spoken_message_event() -> None:
    """Test SPOKEN_MESSAGE event construction."""
    event = create_spoken_message_event("Testing speech", Priority.CRITICAL)
    assert event.type == UIEventType.SPOKEN_MESSAGE
    assert event.payload["message"] == "Testing speech"
    assert event.payload["priority"] == Priority.CRITICAL


def test_create_status_changed_event() -> None:
    """Test STATUS_CHANGED event construction."""
    status = AppStatus(
        state=AppState.GUIDANCE,
        camera_ok=True,
        detector_ok=True,
        ocr_ready=True,
        mic_ok=True,
        tts_ok=True,
        guidance_on=True,
        fps=30.0,
        inference_ms=100.0,
    )
    event = create_status_changed_event(status)
    assert event.type == UIEventType.STATUS_CHANGED
    assert event.payload["status"].state == AppState.GUIDANCE


def test_create_ocr_text_event() -> None:
    """Test OCR_TEXT event construction."""
    event = create_ocr_text_event("Hello World", "Hello World spoken")
    assert event.type == UIEventType.OCR_TEXT
    assert event.payload["full_text"] == "Hello World"
    assert event.payload["spoken_text"] == "Hello World spoken"


def test_create_error_event() -> None:
    """Test ERROR event construction."""
    event = create_error_event(
        ErrorCode.CAMERA_UNAVAILABLE,
        "Cannot open camera 0",
        details={"device_index": 0},
    )
    assert event.type == UIEventType.ERROR
    assert event.payload["error_code"] == "CAMERA_UNAVAILABLE"
    assert event.payload["message"] == "Cannot open camera 0"
    assert event.payload["details"]["device_index"] == 0


def test_listening_events() -> None:
    """Test LISTENING_STARTED and LISTENING_STOPPED events."""
    start_ev = create_listening_started_event()
    assert start_ev.type == UIEventType.LISTENING_STARTED

    stop_ev = create_listening_stopped_event()
    assert stop_ev.type == UIEventType.LISTENING_STOPPED


def test_show_help_event() -> None:
    """Test SHOW_HELP event."""
    help_ev = create_show_help_event("Commands list")
    assert help_ev.type == UIEventType.SHOW_HELP
    assert help_ev.payload["help_text"] == "Commands list"
