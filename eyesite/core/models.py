"""Shared data structures, enums, dataclasses, and custom exceptions for EyeSite.

PRD Section L specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Enums (PRD Section L.1 + Section K.7 additions)
# ---------------------------------------------------------------------------


class Zone(str, Enum):
    """Horizontal zone of an object within the camera frame."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Proximity(str, Enum):
    """Estimated proximity based on bounding-box area ratio."""

    FAR = "far"
    NEAR = "near"
    VERY_CLOSE = "very_close"


class Priority(IntEnum):
    """Speech priority where a lower integer value means higher priority."""

    CRITICAL = 0
    RESPONSE = 1
    INFO = 2


class AppState(str, Enum):
    """Application operating state for the state machine."""

    STARTING = "STARTING"
    IDLE = "IDLE"
    GUIDANCE = "GUIDANCE"
    BUSY_OCR = "BUSY_OCR"
    ERROR_DEGRADED = "ERROR_DEGRADED"
    SHUTTING_DOWN = "SHUTTING_DOWN"


class Intent(str, Enum):
    """Supported voice and command intents."""

    DESCRIBE = "DESCRIBE"
    AHEAD = "AHEAD"
    READ_TEXT = "READ_TEXT"
    GUIDANCE_ON = "GUIDANCE_ON"
    GUIDANCE_OFF = "GUIDANCE_OFF"
    REPEAT = "REPEAT"
    STOP_SPEECH = "STOP_SPEECH"
    HELP = "HELP"
    VOLUME_UP = "VOLUME_UP"
    VOLUME_DOWN = "VOLUME_DOWN"
    EXIT = "EXIT"
    UNKNOWN = "UNKNOWN"


class InputSource(str, Enum):
    """Source of a user command."""

    VOICE = "VOICE"
    KEYBOARD = "KEYBOARD"
    BUTTON = "BUTTON"


class ErrorCode(str, Enum):
    """Standardized error codes for reporting system failures."""

    CAMERA_UNAVAILABLE = "CAMERA_UNAVAILABLE"
    MODEL_LOAD_FAILED = "MODEL_LOAD_FAILED"
    OCR_NOT_READY = "OCR_NOT_READY"
    OCR_FAILED = "OCR_FAILED"
    MIC_UNAVAILABLE = "MIC_UNAVAILABLE"
    STT_NETWORK_ERROR = "STT_NETWORK_ERROR"
    TTS_FAILED = "TTS_FAILED"
    CONFIG_INVALID = "CONFIG_INVALID"
    UNKNOWN = "UNKNOWN"


class UserAction(str, Enum):
    """User actions triggered via UI buttons or hotkeys (Section K.7)."""

    DESCRIBE = "DESCRIBE"
    AHEAD = "AHEAD"
    READ_TEXT = "READ_TEXT"
    TOGGLE_GUIDANCE = "TOGGLE_GUIDANCE"
    LISTEN = "LISTEN"
    REPEAT = "REPEAT"
    STOP_SPEECH = "STOP_SPEECH"
    HELP = "HELP"
    VOLUME_UP = "VOLUME_UP"
    VOLUME_DOWN = "VOLUME_DOWN"
    QUIT = "QUIT"
    RETRY_CAMERA = "RETRY_CAMERA"


class UIEventType(str, Enum):
    """Types of events dispatched to the UI event queue (Section K.7, L.2)."""

    SPOKEN_MESSAGE = "SPOKEN_MESSAGE"
    STATUS_CHANGED = "STATUS_CHANGED"
    OCR_TEXT = "OCR_TEXT"
    ERROR = "ERROR"
    LISTENING_STARTED = "LISTENING_STARTED"
    LISTENING_STOPPED = "LISTENING_STOPPED"
    SHOW_HELP = "SHOW_HELP"


# ---------------------------------------------------------------------------
# Records / Dataclasses (PRD Section L.2)
# ---------------------------------------------------------------------------


@dataclass
class FramePacket:
    """A single captured camera frame with metadata."""

    frame: np.ndarray  # BGR format
    timestamp: float
    frame_id: int
    width: int
    height: int


@dataclass(frozen=True)
class BBox:
    """Bounding box coordinates [x1, y1, x2, y2]."""

    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        """Horizontal width of the box in pixels."""
        return max(0, self.x2 - self.x1)

    @property
    def height(self) -> int:
        """Vertical height of the box in pixels."""
        return max(0, self.y2 - self.y1)

    @property
    def area(self) -> int:
        """Pixel area of the bounding box."""
        return self.width * self.height

    @property
    def center_x(self) -> float:
        """Horizontal center coordinate of the bounding box."""
        return (self.x1 + self.x2) / 2.0

    @property
    def center_y(self) -> float:
        """Vertical center coordinate of the bounding box."""
        return (self.y1 + self.y2) / 2.0


@dataclass
class Detection:
    """Single object detection from YOLO."""

    label: str
    class_id: int
    confidence: float
    bbox: BBox


@dataclass
class DetectionResult:
    """Collection of detections for a specific frame."""

    frame_id: int
    timestamp: float
    frame_width: int
    frame_height: int
    detections: list[Detection]
    inference_ms: float


@dataclass
class SpatialObject:
    """Object detection enriched with spatial positioning and proximity."""

    detection: Detection
    zone: Zone
    proximity: Proximity
    center_x_ratio: float
    area_ratio: float


@dataclass
class Alert:
    """Guidance alert to be spoken to the user."""

    text: str
    priority: Priority
    key: tuple[str, Zone]
    proximity: Proximity


@dataclass
class OCRRegion:
    """A detected text region with confidence and bounding box."""

    text: str
    confidence: float
    bbox: BBox


@dataclass
class OCRResult:
    """Result of an on-demand OCR reading job."""

    full_text: str
    spoken_text: str
    regions: list[OCRRegion]
    avg_confidence: float
    duration_ms: float
    frame_id: int
    error: ErrorCode | None = None


@dataclass
class SpeechItem:
    """Queued text item waiting to be synthesized by TTS."""

    text: str
    priority: Priority
    created_at: float
    interrupt: bool = False


@dataclass
class ListenResult:
    """Result from voice input capture and speech recognition."""

    transcript: str | None
    error: ErrorCode | None
    duration_ms: float


@dataclass
class Command:
    """Parsed user command with matched intent and metadata."""

    intent: Intent
    raw_text: str
    match_score: float
    source: InputSource


@dataclass
class AppStatus:
    """System status snapshot for UI and diagnostic reporting."""

    state: AppState
    camera_ok: bool
    detector_ok: bool
    ocr_ready: bool
    mic_ok: bool
    tts_ok: bool
    guidance_on: bool
    fps: float
    inference_ms: float
    last_error: ErrorCode | None = None


@dataclass
class UIEvent:
    """Event dispatched from the controller to the UI queue."""

    type: UIEventType
    payload: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Custom Exceptions (PRD Section L.3)
# ---------------------------------------------------------------------------


class EyeSiteError(Exception):
    """Base exception for all EyeSite system errors."""


class CameraError(EyeSiteError):
    """Raised when camera initialization, capture, or stream fails."""


class ModelLoadError(EyeSiteError):
    """Raised when YOLO or another ML model fails to load."""


class OcrError(EyeSiteError):
    """Raised when OCR reader fails to load or process an image."""


class SpeechInputError(EyeSiteError):
    """Raised when microphone or speech recognition fails."""


class SpeechOutputError(EyeSiteError):
    """Raised when TTS synthesis or playback fails."""


class ConfigError(EyeSiteError):
    """Raised when configuration values are invalid or missing."""
