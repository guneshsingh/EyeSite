"""Protocol definitions for EyeSite module interfaces.

PRD Section K specification.
All interfaces are defined as typing.Protocol classes.
"""

from __future__ import annotations

import queue
from collections.abc import Callable
from typing import Protocol, runtime_checkable

import numpy as np

from eyesite.core.models import (
    Alert,
    AppStatus,
    Detection,
    DetectionResult,
    FramePacket,
    ListenResult,
    OCRResult,
    Priority,
    SpatialObject,
    UIEvent,
    UserAction,
)


@runtime_checkable
class ICamera(Protocol):
    """Camera capture interface (Section K.1)."""

    def start(self) -> None:
        """Open camera and start capture thread.

        Raises:
            CameraError: If the camera cannot be opened.
        """
        ...

    def stop(self) -> None:
        """Stop capture thread and release the device."""
        ...

    def get_latest_frame(self) -> FramePacket | None:
        """Return the newest frame packet, or None if no frame is ready."""
        ...

    def is_running(self) -> bool:
        """Return True if the camera capture thread is currently running."""
        ...

    def get_fps(self) -> float:
        """Return the measured capture frame rate."""
        ...


@runtime_checkable
class IDetector(Protocol):
    """Object detector interface (Section K.2)."""

    def load(self) -> None:
        """Load detection model and warm up.

        Raises:
            ModelLoadError: If loading or initialization fails.
        """
        ...

    def start(self) -> None:
        """Start inference worker thread."""
        ...

    def stop(self) -> None:
        """Stop inference worker thread."""
        ...

    def get_latest_result(self) -> DetectionResult | None:
        """Return the newest detection result, or None if none available."""
        ...

    def detect_frame(self, frame: np.ndarray) -> list[Detection]:
        """Perform synchronous single-frame detection."""
        ...

    def annotate(
        self, frame: np.ndarray, detections: list[Detection]
    ) -> np.ndarray:
        """Draw bounding boxes and labels on a copy of the frame."""
        ...


@runtime_checkable
class INavigation(Protocol):
    """Spatial reasoning and alert generation facade (Section K.3)."""

    def analyze(self, result: DetectionResult) -> list[SpatialObject]:
        """Convert detections into spatial objects with zone and proximity."""
        ...

    def describe_scene(self, objs: list[SpatialObject]) -> str:
        """Generate a natural sentence describing all detected objects."""
        ...

    def describe_ahead(self, objs: list[SpatialObject]) -> str:
        """Summarize objects located in the CENTER zone."""
        ...

    def select_alerts(
        self, objs: list[SpatialObject], now: float
    ) -> list[Alert]:
        """Filter and select urgent obstacle alerts using cooldown policy."""
        ...

    def reset_cooldowns(self) -> None:
        """Reset internal alert cooldown timers (e.g. when guidance toggles)."""
        ...


@runtime_checkable
class IOcrReader(Protocol):
    """On-demand optical character recognition interface (Section K.4)."""

    def preload(self) -> None:
        """Load OCR engine weights in background thread."""
        ...

    def is_ready(self) -> bool:
        """Return True if OCR model is loaded and ready for inference."""
        ...

    def is_busy(self) -> bool:
        """Return True if an OCR job is currently running."""
        ...

    def read_async(
        self,
        frame: np.ndarray,
        on_done: Callable[[OCRResult], None],
    ) -> bool:
        """Enqueue an asynchronous OCR reading job.

        Returns:
            False if the reader is busy or not ready, True otherwise.
        """
        ...

    def read_sync(self, frame: np.ndarray) -> OCRResult:
        """Perform synchronous OCR recognition for testing."""
        ...


@runtime_checkable
class ISpeaker(Protocol):
    """Text-to-speech speaker interface (Section K.5)."""

    on_speaking_changed: Callable[[bool], None]

    def start(self) -> None:
        """Start TTS worker thread."""
        ...

    def stop(self) -> None:
        """Stop TTS worker thread and release engine."""
        ...

    def speak(
        self,
        text: str,
        priority: Priority = Priority.RESPONSE,
        interrupt: bool = False,
    ) -> None:
        """Enqueue speech utterance with priority and optional interruption."""
        ...

    def stop_speaking(self) -> None:
        """Interrupt current utterance and drop queued INFO items."""
        ...

    def repeat_last(self) -> None:
        """Re-speak the last spoken RESPONSE message."""
        ...

    def set_rate(self, value: int) -> None:
        """Set speech rate in words per minute."""
        ...

    def set_volume(self, value: float) -> None:
        """Set speech volume between 0.0 and 1.0."""
        ...

    def is_speaking(self) -> bool:
        """Return True if TTS engine is currently vocalizing."""
        ...


@runtime_checkable
class IListener(Protocol):
    """Speech-to-text listener interface (Section K.6)."""

    def start(self) -> None:
        """Start listener resources."""
        ...

    def stop(self) -> None:
        """Stop listener resources."""
        ...

    def calibrate(self) -> None:
        """Calibrate microphone energy threshold for ambient noise."""
        ...

    def listen_once_async(
        self, on_result: Callable[[ListenResult], None]
    ) -> bool:
        """Initiate push-to-talk voice capture asynchronously."""
        ...

    def is_available(self) -> bool:
        """Return False if no input audio device is detected."""
        ...


@runtime_checkable
class IAppController(Protocol):
    """Application controller interface for the UI (Section K.7)."""

    events: queue.Queue[UIEvent]

    def on_action(self, action: UserAction) -> None:
        """Dispatch a user action (button click or hotkey)."""
        ...

    def get_status(self) -> AppStatus:
        """Return current application status snapshot."""
        ...

    def get_display_frame(self) -> np.ndarray | None:
        """Return latest annotated frame for video rendering."""
        ...
