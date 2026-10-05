"""Unit tests verifying that fake implementations satisfy core protocols and requirements."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from eyesite.core.interfaces import (
    ICamera,
    IDetector,
    IListener,
    INavigation,
    IOcrReader,
    ISpeaker,
)
from eyesite.core.messages import NO_OBJECTS, NOTHING_AHEAD
from eyesite.core.models import (
    Alert,
    BBox,
    Detection,
    DetectionResult,
    FramePacket,
    ListenResult,
    OCRRegion,
    OCRResult,
    Priority,
    Proximity,
    SpatialObject,
    Zone,
)
from tests.fixtures.fakes import (
    FakeCamera,
    FakeDetector,
    FakeListener,
    FakeNavigation,
    FakeOcrReader,
    FakeSpeaker,
    make_detection,
    make_result,
)


def test_helpers_make_detection_and_result() -> None:
    """make_detection and make_result create well-formed data structures."""
    det = make_detection("chair", 10, 20, 110, 220, confidence=0.88, class_id=56)
    assert isinstance(det, Detection)
    assert det.label == "chair"
    assert det.confidence == 0.88
    assert det.class_id == 56
    assert det.bbox == BBox(10, 20, 110, 220)
    assert det.bbox.width == 100
    assert det.bbox.height == 200
    assert det.bbox.area == 20000

    res = make_result([det], frame_w=1280, frame_h=720, frame_id=7, timestamp=123.45)
    assert isinstance(res, DetectionResult)
    assert res.frame_width == 1280
    assert res.frame_height == 720
    assert res.frame_id == 7
    assert res.timestamp == 123.45
    assert len(res.detections) == 1
    assert res.detections[0].label == "chair"


def test_fake_camera_satisfies_protocol() -> None:
    """FakeCamera satisfies ICamera protocol and supports start/stop/counting."""
    cam = FakeCamera(width=320, height=240, fps=15.0)
    assert isinstance(cam, ICamera)
    assert not cam.is_running()
    assert cam.get_fps() == 15.0
    assert cam.get_latest_frame() is None
    assert cam.call_count == 1

    cam.start()
    assert cam.is_running()
    pkt = cam.get_latest_frame()
    assert isinstance(pkt, FramePacket)
    assert pkt.width == 320
    assert pkt.height == 240
    assert pkt.frame_id == 2
    assert pkt.frame.shape == (240, 320, 3)

    custom_pkt = FramePacket(np.ones((10, 10, 3), dtype=np.uint8), 999.0, 42, 10, 10)
    cam.packet = custom_pkt
    assert cam.get_latest_frame() is custom_pkt

    cam.stop()
    assert not cam.is_running()
    assert cam.get_latest_frame() is None


def test_fake_camera_video_source(monkeypatch: Any) -> None:
    """FakeCamera supports optional video source via OpenCV."""

    class MockCap:
        def __init__(self) -> None:
            self.opened = True
            self.reads = 0

        def isOpened(self) -> bool:
            return self.opened

        def read(self) -> tuple[bool, np.ndarray]:
            self.reads += 1
            if self.reads <= 2:
                return True, np.zeros((480, 640, 3), dtype=np.uint8)
            return False, np.zeros((0, 0, 3), dtype=np.uint8)

        def set(self, prop: int, val: int) -> bool:
            self.reads = 0
            return True

        def release(self) -> None:
            self.opened = False

    import tests.fixtures.fakes as fakes_mod

    mock_cv2 = type("MockCv2", (), {
        "VideoCapture": lambda path: MockCap(),
        "CAP_PROP_POS_FRAMES": 1,
    })
    monkeypatch.setattr(fakes_mod, "cv2", mock_cv2)

    cam = FakeCamera(video_path="sample.mp4")
    cam.start()
    assert cam.is_running()
    frame1 = cam.get_latest_frame()
    assert frame1 is not None and frame1.width == 640
    frame2 = cam.get_latest_frame()
    assert frame2 is not None
    # Third read triggers loop reset and succeeds
    frame3 = cam.get_latest_frame()
    assert frame3 is not None
    cam.stop()
    assert not cam.is_running()


def test_fake_detector_satisfies_protocol() -> None:
    """FakeDetector satisfies IDetector protocol and supports settable stale results."""
    detector = FakeDetector()
    assert isinstance(detector, IDetector)

    detector.load()
    assert detector.is_loaded
    assert detector.load_calls == 1

    detector.start()
    assert detector.is_running_flag
    detector.stop()
    assert not detector.is_running_flag

    det = make_detection("person", 100, 100, 300, 400, confidence=0.92)
    detector.set_result(detections=[det], timestamp=1000.0)
    assert detector.get_latest_result() is detector.result
    assert detector.call_count == 1
    assert detector.timestamp == 1000.0

    # Test settable timestamp for staleness testing
    detector.timestamp = 500.0
    assert detector.result.timestamp == 500.0

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    sync_dets = detector.detect_frame(frame)
    assert len(sync_dets) == 1
    assert sync_dets[0].label == "person"

    annotated = detector.annotate(frame, sync_dets)
    assert annotated is not frame
    assert annotated.shape == frame.shape


def test_fake_navigation_satisfies_protocol() -> None:
    """FakeNavigation satisfies INavigation protocol and returns preset text and alerts."""
    nav = FakeNavigation()
    assert isinstance(nav, INavigation)

    det = make_detection("laptop", 200, 200, 400, 400)
    result = make_result([det])
    objs = nav.analyze(result)
    assert nav.analyze_calls == [result]
    assert objs == []

    preset_obj = SpatialObject(det, Zone.CENTER, Proximity.NEAR, 0.5, 0.15)
    nav.spatial_objects = [preset_obj]
    assert nav.analyze(result) == [preset_obj]

    assert nav.describe_scene([preset_obj]) == NO_OBJECTS
    nav.scene_description = "I see a laptop ahead."
    assert nav.describe_scene([preset_obj]) == "I see a laptop ahead."

    assert nav.describe_ahead([preset_obj]) == NOTHING_AHEAD
    nav.ahead_description = "Ahead of you is a laptop."
    assert nav.describe_ahead([preset_obj]) == "Ahead of you is a laptop."

    alert = Alert("Watch out!", Priority.CRITICAL, ("laptop", Zone.CENTER), Proximity.NEAR)
    nav.alerts = [alert]
    assert nav.select_alerts([preset_obj], now=time.time()) == [alert]

    assert not nav.reset_cooldowns_called
    nav.reset_cooldowns()
    assert nav.reset_cooldowns_called
    assert nav.reset_cooldowns_count == 1


def test_fake_ocr_reader_satisfies_protocol() -> None:
    """FakeOcrReader satisfies IOcrReader protocol with settable ready/busy states."""
    ocr = FakeOcrReader()
    assert isinstance(ocr, IOcrReader)

    assert ocr.is_ready()
    assert not ocr.is_busy()
    ocr.preload()
    assert ocr.preload_called

    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    sync_res = ocr.read_sync(frame)
    assert isinstance(sync_res, OCRResult)
    assert sync_res.full_text == "Sample text"

    received: list[OCRResult] = []
    success = ocr.read_async(frame, on_done=lambda res: received.append(res))
    assert success
    assert len(received) == 1
    assert received[0] is ocr.result

    ocr.busy = True
    assert not ocr.read_async(frame, on_done=lambda res: None)

    ocr.busy = False
    ocr.ready = False
    assert not ocr.read_async(frame, on_done=lambda res: None)

    custom_res = OCRResult(
        "EXIT", "EXIT", [OCRRegion("EXIT", 0.99, BBox(0, 0, 50, 20))], 0.99, 10.0, 2
    )
    ocr.result = custom_res
    ocr.ready = True
    received.clear()
    assert ocr.read_async(frame, on_done=lambda res: received.append(res))
    assert received[0].full_text == "EXIT"


def test_fake_speaker_satisfies_protocol() -> None:
    """FakeSpeaker satisfies ISpeaker protocol, tracks speech, and notifies events."""
    speaker = FakeSpeaker()
    assert isinstance(speaker, ISpeaker)

    state_changes: list[bool] = []
    speaker.on_speaking_changed = lambda s: state_changes.append(s)

    speaker.start()
    assert speaker.running
    assert not speaker.is_speaking()

    speaker.set_speaking(True)
    assert speaker.is_speaking()
    assert state_changes == [True]

    speaker.speak("Hello Asha", Priority.RESPONSE)
    assert speaker.spoken == [("Hello Asha", Priority.RESPONSE)]
    assert speaker.last_response == "Hello Asha"

    speaker.speak("Stop immediately", Priority.CRITICAL, interrupt=True)
    assert speaker.stopped
    assert speaker.stop_count == 1
    assert not speaker.is_speaking()

    speaker.repeat_last()
    assert speaker.spoken[-1] == ("Hello Asha", Priority.RESPONSE)

    speaker.set_rate(180)
    assert speaker.rate == 180
    speaker.set_volume(0.8)
    assert speaker.volume == 0.8

    speaker.stop()
    assert not speaker.running


def test_fake_listener_satisfies_protocol() -> None:
    """FakeListener satisfies IListener protocol and allows tests to push results."""
    listener = FakeListener()
    assert isinstance(listener, IListener)
    assert listener.is_available()

    listener.start()
    assert listener.running
    listener.calibrate()
    assert listener.calibrated
    assert listener.calibrate_calls == 1

    # Test pushing result after listen_once_async called
    results: list[ListenResult] = []
    assert listener.listen_once_async(on_result=lambda r: results.append(r))
    assert len(results) == 0

    test_res = ListenResult(transcript="describe", error=None, duration_ms=120.0)
    listener.push_result(test_res)
    assert len(results) == 1
    assert results[0].transcript == "describe"

    # Test pushing transcript before listen_once_async (queue mode)
    listener.push_transcript("what is ahead")
    results.clear()
    assert listener.listen_once_async(on_result=lambda r: results.append(r))
    assert len(results) == 1
    assert results[0].transcript == "what is ahead"

    # Test unavailable listener
    listener.available = False
    assert not listener.is_available()
    assert not listener.listen_once_async(on_result=lambda r: None)

    listener.stop()
    assert not listener.running
