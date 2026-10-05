"""Fake implementations of EyeSite core interfaces for testing without hardware.

PRD Section K and NFR-09 specification.
"""

from __future__ import annotations

import time
from collections.abc import Callable

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

from eyesite.core.messages import NO_OBJECTS, NOTHING_AHEAD
from eyesite.core.models import (
    Alert,
    BBox,
    Detection,
    DetectionResult,
    ErrorCode,
    FramePacket,
    ListenResult,
    OCRRegion,
    OCRResult,
    Priority,
    SpatialObject,
)


def make_detection(
    label: str, x1: int, y1: int, x2: int, y2: int, confidence: float = 0.9, class_id: int = 0
) -> Detection:
    """Create a Detection object with a validated BBox."""
    return Detection(label, class_id, confidence, BBox(int(x1), int(y1), int(x2), int(y2)))


def make_result(
    detections: list[Detection] | None = None,
    frame_w: int = 640,
    frame_h: int = 480,
    frame_id: int = 1,
    timestamp: float | None = None,
    inference_ms: float = 15.0,
) -> DetectionResult:
    """Create a DetectionResult with optional custom timestamp and detections."""
    ts = time.time() if timestamp is None else timestamp
    return DetectionResult(frame_id, ts, frame_w, frame_h, list(detections or []), inference_ms)


def _default_ocr_result() -> OCRResult:
    reg = OCRRegion("Sample text", 0.95, BBox(10, 10, 100, 40))
    return OCRResult("Sample text", "Sample text", [reg], 0.95, 45.0, 1, None)


class FakeCamera:
    """Fake camera implementing ICamera (Section K.1)."""

    def __init__(
        self,
        frame: np.ndarray | None = None,
        packet: FramePacket | None = None,
        video_path: str | None = None,
        width: int = 640,
        height: int = 480,
        fps: float = 30.0,
        running: bool = False,
    ) -> None:
        self.width, self.height, self.fps, self.video_path = width, height, fps, video_path
        self.call_count, self.packet, self._running, self._cap = 0, packet, running, None
        self.frame = frame if frame is not None else np.zeros((height, width, 3), dtype=np.uint8)

    def start(self) -> None:
        """Start fake capture, opening optional video source."""
        self._running = True
        if self.video_path is not None:
            if cv2 is None:
                raise RuntimeError("OpenCV (cv2) is required for video-file source.")
            self._cap = cv2.VideoCapture(self.video_path)
            if not self._cap.isOpened():
                raise RuntimeError(f"Could not open video file: {self.video_path}")

    def stop(self) -> None:
        """Stop fake capture and release video file."""
        self._running, self._cap = False, (self._cap.release() if self._cap else None)

    def is_running(self) -> bool:
        """Return True if capture is active."""
        return self._running

    def get_fps(self) -> float:
        """Return capture frame rate."""
        return self.fps

    def get_latest_frame(self) -> FramePacket | None:
        """Return next frame packet or None if stopped."""
        self.call_count += 1
        if not self._running:
            return None
        if self._cap is not None and cv2 is not None:
            ret, frame = self._cap.read()
            if not ret:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self._cap.read()
            if ret:
                return FramePacket(
                    frame, time.time(), self.call_count, frame.shape[1], frame.shape[0]
                )
            return None
        if self.packet is not None:
            return self.packet
        return FramePacket(self.frame.copy(), time.time(), self.call_count, self.width, self.height)


class FakeDetector:
    """Fake object detector implementing IDetector (Section K.2)."""

    def __init__(
        self,
        result: DetectionResult | None = None,
        loaded: bool = False,
        running: bool = False,
    ) -> None:
        self.result = result if result is not None else make_result()
        self.is_loaded, self.is_running_flag = loaded, running
        self.call_count, self.load_calls = 0, 0
        self.detect_frame_detections: list[Detection] | None = None

    @property
    def timestamp(self) -> float:
        """Settable timestamp of the current result for staleness testing."""
        return self.result.timestamp

    @timestamp.setter
    def timestamp(self, value: float) -> None:
        self.result.timestamp = value

    def set_result(
        self,
        detections: list[Detection] | None = None,
        timestamp: float | None = None,
        frame_w: int = 640,
        frame_h: int = 480,
        frame_id: int = 1,
        inference_ms: float = 15.0,
    ) -> DetectionResult:
        """Set and return a new detection result."""
        self.result = make_result(detections, frame_w, frame_h, frame_id, timestamp, inference_ms)
        return self.result

    def load(self) -> None:
        """Simulate loading model."""
        self.load_calls, self.is_loaded = self.load_calls + 1, True

    def start(self) -> None:
        """Start inference worker."""
        self.is_running_flag = True

    def stop(self) -> None:
        """Stop inference worker."""
        self.is_running_flag = False

    def get_latest_result(self) -> DetectionResult | None:
        """Return newest detection result."""
        self.call_count += 1
        return self.result

    def detect_frame(self, frame: np.ndarray) -> list[Detection]:
        """Perform synchronous single-frame detection."""
        if self.detect_frame_detections is not None:
            return self.detect_frame_detections
        return list(self.result.detections)

    def annotate(self, frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
        """Return a copy of frame with bounding boxes drawn."""
        annotated = frame.copy()
        if cv2 is not None:
            for d in detections:
                cv2.rectangle(
                    annotated, (d.bbox.x1, d.bbox.y1), (d.bbox.x2, d.bbox.y2), (0, 255, 0), 2
                )
        return annotated


class FakeNavigation:
    """Fake navigation module implementing INavigation (Section K.3)."""

    def __init__(
        self,
        spatial_objects: list[SpatialObject] | None = None,
        scene_description: str = NO_OBJECTS,
        ahead_description: str = NOTHING_AHEAD,
        alerts: list[Alert] | None = None,
    ) -> None:
        self.spatial_objects, self.alerts = list(spatial_objects or []), list(alerts or [])
        self.scene_description, self.ahead_description = scene_description, ahead_description
        self.reset_cooldowns_called, self.reset_cooldowns_count = False, 0
        self.analyze_calls: list[DetectionResult] = []
        self.describe_scene_calls: list[list[SpatialObject]] = []
        self.describe_ahead_calls: list[list[SpatialObject]] = []
        self.select_alerts_calls: list[tuple[list[SpatialObject], float]] = []

    def analyze(self, result: DetectionResult) -> list[SpatialObject]:
        """Record call and return preset spatial objects."""
        self.analyze_calls.append(result)
        return self.spatial_objects

    def describe_scene(self, objs: list[SpatialObject]) -> str:
        """Record call and return preset scene description."""
        self.describe_scene_calls.append(objs)
        return self.scene_description

    def describe_ahead(self, objs: list[SpatialObject]) -> str:
        """Record call and return preset ahead description."""
        self.describe_ahead_calls.append(objs)
        return self.ahead_description

    def select_alerts(self, objs: list[SpatialObject], now: float) -> list[Alert]:
        """Record call and return preset alerts."""
        self.select_alerts_calls.append((objs, now))
        return list(self.alerts)

    def reset_cooldowns(self) -> None:
        """Record cooldown reset invocation."""
        self.reset_cooldowns_called, self.reset_cooldowns_count = (
            True,
            self.reset_cooldowns_count + 1,
        )


class FakeOcrReader:
    """Fake OCR reader implementing IOcrReader (Section K.4)."""

    def __init__(
        self,
        ready: bool = True,
        busy: bool = False,
        result: OCRResult | None = None,
    ) -> None:
        self.ready, self.busy, self.preload_called = ready, busy, False
        self.read_async_calls: list[np.ndarray] = []
        self.read_sync_calls: list[np.ndarray] = []
        self.result = result if result is not None else _default_ocr_result()

    def preload(self) -> None:
        """Simulate preloading model."""
        self.preload_called, self.ready = True, True

    def is_ready(self) -> bool:
        """Return True if ready."""
        return self.ready

    def is_busy(self) -> bool:
        """Return True if busy."""
        return self.busy

    def read_async(self, frame: np.ndarray, on_done: Callable[[OCRResult], None]) -> bool:
        """Deliver preset OCR result if ready and not busy."""
        if not self.ready or self.busy:
            return False
        self.read_async_calls.append(frame)
        on_done(self.result)
        return True

    def read_sync(self, frame: np.ndarray) -> OCRResult:
        """Return synchronous OCR result."""
        self.read_sync_calls.append(frame)
        return self.result


class FakeSpeaker:
    """Fake text-to-speech engine implementing ISpeaker (Section K.5)."""

    def __init__(self, rate: int = 170, volume: float = 0.9) -> None:
        self.rate, self.volume = rate, volume
        self.spoken: list[tuple[str, Priority]] = []
        self.last_response: str | None = None
        self.running, self.stopped, self.stop_count, self.repeat_calls, self._is_speaking = (
            False,
            False,
            0,
            0,
            False,
        )
        self.on_speaking_changed: Callable[[bool], None] = lambda _: None

    def start(self) -> None:
        """Start speaker worker."""
        self.running = True

    def stop(self) -> None:
        """Stop speaker worker."""
        self.running = False

    def speak(
        self, text: str, priority: Priority = Priority.RESPONSE, interrupt: bool = False
    ) -> None:
        """Record utterance into spoken list."""
        self.spoken.append((text, priority))
        if priority == Priority.RESPONSE:
            self.last_response = text
        if interrupt:
            self.stop_speaking()

    def stop_speaking(self) -> None:
        """Interrupt current speech."""
        self.stopped, self.stop_count = True, self.stop_count + 1
        self.set_speaking(False)

    def repeat_last(self) -> None:
        """Re-speak last recorded RESPONSE message."""
        self.repeat_calls += 1
        if self.last_response is not None:
            self.speak(self.last_response, Priority.RESPONSE)

    def set_rate(self, value: int) -> None:
        """Set speech rate."""
        self.rate = value

    def set_volume(self, value: float) -> None:
        """Set speech volume."""
        self.volume = value

    def is_speaking(self) -> bool:
        """Return True if speaking."""
        return self._is_speaking

    def set_speaking(self, speaking: bool) -> None:
        """Update speaking state and notify callback."""
        self._is_speaking = speaking
        if self.on_speaking_changed is not None:
            self.on_speaking_changed(speaking)


class FakeListener:
    """Fake speech listener implementing IListener (Section K.6)."""

    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.running, self.calibrated, self.calibrate_calls, self.listen_calls = (
            False,
            False,
            0,
            0,
        )
        self._queued_results: list[ListenResult] = []
        self._pending_callback: Callable[[ListenResult], None] | None = None

    def start(self) -> None:
        """Start listener."""
        self.running = True

    def stop(self) -> None:
        """Stop listener."""
        self.running, self._pending_callback = False, None

    def calibrate(self) -> None:
        """Simulate ambient noise calibration."""
        self.calibrated, self.calibrate_calls = True, self.calibrate_calls + 1

    def is_available(self) -> bool:
        """Return True if mic available."""
        return self.available

    def listen_once_async(self, on_result: Callable[[ListenResult], None]) -> bool:
        """Trigger push-to-talk listen."""
        if not self.available:
            return False
        self.listen_calls += 1
        if self._queued_results:
            result = self._queued_results.pop(0)
            on_result(result)
            return True
        self._pending_callback = on_result
        return True

    def push_result(self, result: ListenResult) -> None:
        """Deliver or enqueue a ListenResult."""
        if self._pending_callback is not None:
            cb = self._pending_callback
            self._pending_callback = None
            cb(result)
        else:
            self._queued_results.append(result)

    def push_transcript(
        self,
        transcript: str | None,
        error: ErrorCode | None = None,
        duration_ms: float = 100.0,
    ) -> None:
        """Convenience helper to push a transcript string as ListenResult."""
        self.push_result(ListenResult(transcript, error, duration_ms))
