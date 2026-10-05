"""Unit tests for models, enums, dataclasses, and custom exceptions.

PRD Section L specification.
"""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from eyesite.core.models import (
    Alert,
    AppState,
    AppStatus,
    BBox,
    CameraError,
    Command,
    ConfigError,
    Detection,
    DetectionResult,
    ErrorCode,
    EyeSiteError,
    FramePacket,
    InputSource,
    Intent,
    ListenResult,
    ModelLoadError,
    OcrError,
    OCRRegion,
    OCRResult,
    Priority,
    Proximity,
    SpatialObject,
    SpeechInputError,
    SpeechItem,
    SpeechOutputError,
    UIEvent,
    UIEventType,
    UserAction,
    Zone,
)

# ---------------------------------------------------------------------------
# BBox tests
# ---------------------------------------------------------------------------


def test_bbox_properties_normal() -> None:
    """Test standard width, height, area, center_x, and center_y calculations."""
    bbox = BBox(x1=50, y1=100, x2=250, y2=400)
    assert bbox.width == 200
    assert bbox.height == 300
    assert bbox.area == 60000
    assert bbox.center_x == 150.0
    assert bbox.center_y == 250.0


def test_bbox_zero_size() -> None:
    """Test width and height when top-left equals bottom-right."""
    bbox = BBox(x1=100, y1=100, x2=100, y2=100)
    assert bbox.width == 0
    assert bbox.height == 0
    assert bbox.area == 0
    assert bbox.center_x == 100.0
    assert bbox.center_y == 100.0


def test_bbox_inverted_coordinates() -> None:
    """Test that inverted coordinates yield 0 width/height/area."""
    bbox = BBox(x1=200, y1=300, x2=100, y2=150)
    assert bbox.width == 0
    assert bbox.height == 0
    assert bbox.area == 0


def test_bbox_is_frozen() -> None:
    """BBox instances must be immutable."""
    bbox = BBox(x1=10, y1=10, x2=50, y2=50)
    with pytest.raises(FrozenInstanceError):
        bbox.x1 = 20  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


def test_enums_defined() -> None:
    """Verify enum members match Section L.1 and Section K.7 additions."""
    # Zone
    assert set(Zone) == {Zone.LEFT, Zone.CENTER, Zone.RIGHT}

    # Proximity
    assert set(Proximity) == {Proximity.FAR, Proximity.NEAR, Proximity.VERY_CLOSE}

    # Priority
    assert Priority.CRITICAL == 0
    assert Priority.RESPONSE == 1
    assert Priority.INFO == 2
    assert Priority.CRITICAL < Priority.RESPONSE < Priority.INFO

    # AppState
    assert AppState.STARTING == "STARTING"
    assert AppState.IDLE == "IDLE"
    assert AppState.GUIDANCE == "GUIDANCE"
    assert AppState.BUSY_OCR == "BUSY_OCR"
    assert AppState.ERROR_DEGRADED == "ERROR_DEGRADED"
    assert AppState.SHUTTING_DOWN == "SHUTTING_DOWN"

    # Intent
    assert Intent.DESCRIBE == "DESCRIBE"
    assert Intent.AHEAD == "AHEAD"
    assert Intent.READ_TEXT == "READ_TEXT"
    assert Intent.GUIDANCE_ON == "GUIDANCE_ON"
    assert Intent.GUIDANCE_OFF == "GUIDANCE_OFF"
    assert Intent.REPEAT == "REPEAT"
    assert Intent.STOP_SPEECH == "STOP_SPEECH"
    assert Intent.HELP == "HELP"
    assert Intent.VOLUME_UP == "VOLUME_UP"
    assert Intent.VOLUME_DOWN == "VOLUME_DOWN"
    assert Intent.EXIT == "EXIT"
    assert Intent.UNKNOWN == "UNKNOWN"

    # InputSource
    assert set(InputSource) == {InputSource.VOICE, InputSource.KEYBOARD, InputSource.BUTTON}

    # ErrorCode
    expected_errors = {
        "CAMERA_UNAVAILABLE",
        "MODEL_LOAD_FAILED",
        "OCR_NOT_READY",
        "OCR_FAILED",
        "MIC_UNAVAILABLE",
        "STT_NETWORK_ERROR",
        "TTS_FAILED",
        "CONFIG_INVALID",
        "UNKNOWN",
    }
    assert {e.value for e in ErrorCode} == expected_errors

    # UserAction (Section K.7)
    expected_actions = {
        "DESCRIBE",
        "AHEAD",
        "READ_TEXT",
        "TOGGLE_GUIDANCE",
        "LISTEN",
        "REPEAT",
        "STOP_SPEECH",
        "HELP",
        "VOLUME_UP",
        "VOLUME_DOWN",
        "QUIT",
        "RETRY_CAMERA",
    }
    assert {a.value for a in UserAction} == expected_actions

    # UIEventType (Section K.7, L.2)
    expected_events = {
        "SPOKEN_MESSAGE",
        "STATUS_CHANGED",
        "OCR_TEXT",
        "ERROR",
        "LISTENING_STARTED",
        "LISTENING_STOPPED",
        "SHOW_HELP",
    }
    assert {ev.value for ev in UIEventType} == expected_events


# ---------------------------------------------------------------------------
# Dataclass Instantiation tests
# ---------------------------------------------------------------------------


def test_frame_packet() -> None:
    """Test FramePacket creation."""
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    packet = FramePacket(
        frame=dummy_frame,
        timestamp=1000.0,
        frame_id=1,
        width=640,
        height=480,
    )
    assert packet.width == 640
    assert packet.height == 480
    assert packet.frame_id == 1


def test_detection_and_result() -> None:
    """Test Detection and DetectionResult creation."""
    bbox = BBox(10, 10, 50, 50)
    det = Detection(label="chair", class_id=56, confidence=0.85, bbox=bbox)
    res = DetectionResult(
        frame_id=1,
        timestamp=1000.0,
        frame_width=640,
        frame_height=480,
        detections=[det],
        inference_ms=45.2,
    )
    assert len(res.detections) == 1
    assert res.detections[0].label == "chair"


def test_spatial_object_and_alert() -> None:
    """Test SpatialObject and Alert creation."""
    bbox = BBox(10, 10, 200, 200)
    det = Detection(label="person", class_id=0, confidence=0.9, bbox=bbox)
    obj = SpatialObject(
        detection=det,
        zone=Zone.CENTER,
        proximity=Proximity.NEAR,
        center_x_ratio=0.5,
        area_ratio=0.2,
    )
    assert obj.zone == Zone.CENTER
    assert obj.proximity == Proximity.NEAR

    alert = Alert(
        text="Person ahead, close.",
        priority=Priority.RESPONSE,
        key=("person", Zone.CENTER),
        proximity=Proximity.NEAR,
    )
    assert alert.key == ("person", Zone.CENTER)


def test_ocr_records() -> None:
    """Test OCRRegion and OCRResult creation."""
    region = OCRRegion(text="EXIT", confidence=0.95, bbox=BBox(10, 10, 60, 30))
    res = OCRResult(
        full_text="EXIT",
        spoken_text="EXIT",
        regions=[region],
        avg_confidence=0.95,
        duration_ms=120.0,
        frame_id=42,
    )
    assert res.full_text == "EXIT"
    assert res.error is None


def test_speech_and_listen_records() -> None:
    """Test SpeechItem, ListenResult, and Command."""
    speech = SpeechItem(text="Hello", priority=Priority.INFO, created_at=100.0)
    assert speech.interrupt is False

    listen = ListenResult(transcript="describe", error=None, duration_ms=400.0)
    assert listen.transcript == "describe"

    cmd = Command(
        intent=Intent.DESCRIBE,
        raw_text="what do you see",
        match_score=1.0,
        source=InputSource.VOICE,
    )
    assert cmd.intent == Intent.DESCRIBE


def test_app_status_and_ui_event() -> None:
    """Test AppStatus and UIEvent creation."""
    status = AppStatus(
        state=AppState.IDLE,
        camera_ok=True,
        detector_ok=True,
        ocr_ready=False,
        mic_ok=True,
        tts_ok=True,
        guidance_on=False,
        fps=29.5,
        inference_ms=110.0,
    )
    assert status.state == AppState.IDLE
    assert status.last_error is None

    event = UIEvent(type=UIEventType.STATUS_CHANGED, payload={"status": status})
    assert event.type == UIEventType.STATUS_CHANGED


# ---------------------------------------------------------------------------
# Custom Exception Hierarchy tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc_cls",
    [
        CameraError,
        ModelLoadError,
        OcrError,
        SpeechInputError,
        SpeechOutputError,
        ConfigError,
    ],
)
def test_custom_exceptions_subclass_eyesite_error(exc_cls: type[EyeSiteError]) -> None:
    """All custom exceptions must inherit from EyeSiteError."""
    assert issubclass(exc_cls, EyeSiteError)
    assert issubclass(exc_cls, Exception)
    err = exc_cls("test error")
    assert isinstance(err, EyeSiteError)
