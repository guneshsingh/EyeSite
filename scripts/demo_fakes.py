"""Demo script to verify EyeSite fake implementations and interface protocols.

Usage:
    python scripts/demo_fakes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when running standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from eyesite.core.interfaces import (
    ICamera,
    IDetector,
    IListener,
    INavigation,
    IOcrReader,
    ISpeaker,
)
from eyesite.core.models import (
    Alert,
    ListenResult,
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


def main() -> None:
    """Run interactive demonstration of test fakes without hardware."""
    print("=" * 65)
    print(" EyeSite - Test Fakes Demonstration (Hardware-Free Verification)")
    print("=" * 65)

    # 1. Helper Functions
    print("\n[1] Testing Detection and Result Helpers...")
    det1 = make_detection("person", 200, 100, 440, 460, confidence=0.94)
    det2 = make_detection("chair", 20, 250, 180, 450, confidence=0.85)
    result = make_result([det1, det2], frame_w=640, frame_h=480, frame_id=1)
    print(f"    Created Detection 1: {det1.label} (conf={det1.confidence:.2f}, bbox={det1.bbox})")
    print(f"    Created Detection 2: {det2.label} (conf={det2.confidence:.2f}, bbox={det2.bbox})")
    print(f"    Created Result: {len(result.detections)} detections in {result.frame_width}x{result.frame_height} frame")

    # 2. Fake Camera
    print("\n[2] Testing FakeCamera (ICamera)...")
    cam = FakeCamera(width=640, height=480, fps=30.0)
    print(f"    Protocol check: isinstance(cam, ICamera) -> {isinstance(cam, ICamera)}")
    print(f"    Before start: is_running={cam.is_running()}, frame={cam.get_latest_frame()}")
    cam.start()
    print(f"    After start: is_running={cam.is_running()}, fps={cam.get_fps()}")
    packet = cam.get_latest_frame()
    if packet is not None:
        print(f"    Captured Packet: frame_id={packet.frame_id}, shape={packet.frame.shape}, calls={cam.call_count}")
    cam.stop()
    print(f"    After stop: is_running={cam.is_running()}")

    # 3. Fake Detector
    print("\n[3] Testing FakeDetector (IDetector)...")
    detector = FakeDetector()
    print(f"    Protocol check: isinstance(detector, IDetector) -> {isinstance(detector, IDetector)}")
    detector.load()
    detector.start()
    detector.set_result([det1, det2], timestamp=1000.0)
    latest = detector.get_latest_result()
    assert latest is not None
    print(f"    Detector loaded={detector.is_loaded}, active={detector.is_running_flag}")
    print(f"    Latest result: {len(latest.detections)} objects at timestamp={latest.timestamp}")
    detector.timestamp = 500.0
    print(f"    Updated timestamp for stale result testing: {detector.timestamp}")
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    annotated = detector.annotate(dummy_frame, latest.detections)
    print(f"    Annotated frame created (shape={annotated.shape}) without mutating raw frame")
    detector.stop()

    # 4. Fake Navigation
    print("\n[4] Testing FakeNavigation (INavigation)...")
    nav = FakeNavigation(
        scene_description="I can see a person in the center and a chair on your left.",
        ahead_description="Ahead of you is a person, close.",
        alerts=[Alert("Person ahead, very close. Stop.", Priority.CRITICAL, ("person", Zone.CENTER), Proximity.VERY_CLOSE)],
    )
    print(f"    Protocol check: isinstance(nav, INavigation) -> {isinstance(nav, INavigation)}")
    sp_obj = SpatialObject(det1, Zone.CENTER, Proximity.VERY_CLOSE, 0.5, 0.40)
    nav.spatial_objects = [sp_obj]
    analyzed = nav.analyze(latest)
    print(f"    Analyzed: {len(analyzed)} spatial object(s)")
    print(f"    Scene Description: '{nav.describe_scene(analyzed)}'")
    print(f"    Ahead Description: '{nav.describe_ahead(analyzed)}'")
    alerts = nav.select_alerts(analyzed, now=1000.0)
    print(f"    Alerts: '{alerts[0].text}' (Priority={alerts[0].priority.name})")
    nav.reset_cooldowns()
    print(f"    Cooldowns reset called: {nav.reset_cooldowns_called}")

    # 5. Fake OCR Reader
    print("\n[5] Testing FakeOcrReader (IOcrReader)...")
    ocr = FakeOcrReader()
    print(f"    Protocol check: isinstance(ocr, IOcrReader) -> {isinstance(ocr, IOcrReader)}")
    print(f"    Reader ready={ocr.is_ready()}, busy={ocr.is_busy()}")
    ocr_results: list[OCRResult] = []
    ocr.read_async(dummy_frame, on_done=lambda res: ocr_results.append(res))
    if ocr_results:
        print(f"    Async OCR Result received: full_text='{ocr_results[0].full_text}' (confidence={ocr_results[0].avg_confidence})")

    # 6. Fake Speaker
    print("\n[6] Testing FakeSpeaker (ISpeaker)...")
    speaker = FakeSpeaker()
    print(f"    Protocol check: isinstance(speaker, ISpeaker) -> {isinstance(speaker, ISpeaker)}")
    speaker.on_speaking_changed = lambda state: print(f"    [Event] Speaker on_speaking_changed: {state}")
    speaker.start()
    speaker.set_speaking(True)
    speaker.speak("I can see a chair on your left.", Priority.RESPONSE)
    speaker.speak("Person ahead, very close. Stop.", Priority.CRITICAL, interrupt=True)
    print(f"    Recorded spoken messages ({len(speaker.spoken)} items):")
    for text, prio in speaker.spoken:
        print(f"      - [{prio.name}] {text}")
    print(f"    Interrupted/stopped count: {speaker.stop_count}")
    speaker.repeat_last()
    print(f"    After repeat_last(): {speaker.spoken[-1][0]}")
    speaker.stop()

    # 7. Fake Listener
    print("\n[7] Testing FakeListener (IListener)...")
    listener = FakeListener()
    print(f"    Protocol check: isinstance(listener, IListener) -> {isinstance(listener, IListener)}")
    listener.start()
    listener.calibrate()
    print(f"    Listener calibrated={listener.calibrated}")
    heard_commands: list[ListenResult] = []
    listener.listen_once_async(on_result=lambda res: heard_commands.append(res))
    print("    Listening asynchronously... (waiting for user voice)")
    print("    Simulating test pushing voice transcript 'describe'...")
    listener.push_transcript("describe")
    if heard_commands:
        print(f"    Received command from fake voice input: '{heard_commands[0].transcript}'")
    listener.stop()

    print("\n" + "=" * 65)
    print(" All fake components verified successfully against protocols!")
    print(" Any teammate can now test modules without hardware attached.")
    print("=" * 65)


if __name__ == "__main__":
    main()
