# EyeSite Test Fakes: Beginner's Guide & Viva Preparation

This document explains the test fixtures and fake classes implemented in `tests/fixtures/fakes.py` in simple, clear English. It is designed to help beginner students understand the concepts, prepare for viva/examiner questions, and see how hardware-free testing works in EyeSite.

---

## 1. Why Do We Need Fakes? (The Big Picture)

EyeSite is an assistive application that relies on physical hardware:
- A **webcam** to capture images.
- A **YOLO AI model** to detect objects.
- A **microphone** to listen for user commands.
- A **speaker** to talk back to the user.

### The Problem in Testing
If our unit tests depended on actual hardware:
1. Tests would **fail on CI/GitHub Actions** or computers without a webcam or microphone connected.
2. Running tests would cause the laptop to talk out loud (`pyttsx3`) and beep.
3. Tests would be **slow** (waiting for camera frames or heavy ML model downloads).
4. Tests would be **non-deterministic** (lighting changes, background speech, or moving objects would break tests).
5. It would be impossible to test rare edge cases (e.g. testing what happens if a detection result is 5 seconds stale, or if OCR encounters an error).

### The Solution: Fakes and Protocols
Instead of touching real hardware in tests, we create **Fake Classes** (`FakeCamera`, `FakeDetector`, `FakeSpeaker`, etc.) that implement the exact same **`typing.Protocol` interfaces** defined in `eyesite/core/interfaces.py`.
- Because Python supports structural typing (`Protocol`), the rest of the application (like `AppController`) cannot tell the difference between a real camera and `FakeCamera`.
- This principle is called **Dependency Injection** and **Test-Driven Development (TDD)**.

---

## 2. File-by-File & Class-by-Class Breakdown

### 2.1 Helper Functions in `tests/fixtures/fakes.py`

#### `make_detection(label, x1, y1, x2, y2, confidence=0.9, class_id=0) -> Detection`
- **What it does:** Quickly creates a `Detection` object without requiring manual instantiation of `BBox`.
- **How it works:** Takes simple numbers (`x1`, `y1`, `x2`, `y2`), wraps them in a frozen `BBox`, and packages them into a `Detection(label, class_id, confidence, bbox)`.
- **Why it matters:** In tests, creating 10 detections by hand with `Detection(label='person', class_id=0, confidence=0.9, bbox=BBox(x1=10, y1=10, x2=50, y2=80))` is tedious and error-prone. This helper keeps test code clean and readable.

#### `make_result(detections=None, frame_w=640, frame_h=480, frame_id=1, timestamp=None, inference_ms=15.0) -> DetectionResult`
- **What it does:** Builds a complete `DetectionResult` containing a list of `Detection` items.
- **How it works:** Defaults to the current Unix timestamp (`time.time()`) if not supplied, sets default dimensions (640x480), and packages the detections into a `DetectionResult`.

---

### 2.2 `FakeCamera` (Implements `ICamera`)

- **Protocol Contract (`ICamera`):**
  - `start() -> None`
  - `stop() -> None`
  - `get_latest_frame() -> FramePacket | None`
  - `is_running() -> bool`
  - `get_fps() -> float`
- **Internal State:**
  - `_running: bool`: Tracks whether the camera is started.
  - `call_count: int`: Counts how many times `get_latest_frame()` was called. Useful for testing frame-rate throttling and loop counts.
  - `frame: np.ndarray`: A plain black numpy array (`height x width x 3` uint8) returned when no custom packet is set.
  - `packet: FramePacket | None`: Allows tests to inject a specific preset `FramePacket`.
  - `video_path: str | None`: Optional path to a video file. When provided and OpenCV is installed, frames are read from the video using `cv2.VideoCapture`.
- **Key Behavior:**
  - When stopped (`_running == False`), `get_latest_frame()` returns `None`.
  - When started, each call to `get_latest_frame()` increments `call_count` and returns a fresh `FramePacket` with an incremented `frame_id`.
  - If a video file reaches the end, it rewinds to frame 0 for continuous looping.

---

### 2.3 `FakeDetector` (Implements `IDetector`)

- **Protocol Contract (`IDetector`):**
  - `load() -> None`
  - `start() -> None`
  - `stop() -> None`
  - `get_latest_result() -> DetectionResult | None`
  - `detect_frame(frame: np.ndarray) -> list[Detection]`
  - `annotate(frame: np.ndarray, detections: list[Detection]) -> np.ndarray`
- **Internal State:**
  - `result: DetectionResult`: The preset detection result returned to callers.
  - `timestamp`: A settable property on the detector. Changing `detector.timestamp = time.time() - 5.0` allows tests to simulate stale frames to ensure the app handles lag gracefully.
  - `call_count: int`: Counts calls to `get_latest_result()`.
  - `load_calls: int`: Verifies that model loading was invoked.
- **Key Behavior:**
  - `set_result(detections, ...)`: Updates the current `DetectionResult` on the fly.
  - `detect_frame(frame)`: Returns the current detections for synchronous single-frame testing.
  - `annotate(frame, detections)`: Returns a copy of the frame without modifying the original frame in-place (satisfying FR-DET-07). Draws green bounding boxes if OpenCV is present.

---

### 2.4 `FakeNavigation` (Implements `INavigation`)

- **Protocol Contract (`INavigation`):**
  - `analyze(result: DetectionResult) -> list[SpatialObject]`
  - `describe_scene(objs: list[SpatialObject]) -> str`
  - `describe_ahead(objs: list[SpatialObject]) -> str`
  - `select_alerts(objs: list[SpatialObject], now: float) -> list[Alert]`
  - `reset_cooldowns() -> None`
- **Internal State:**
  - `spatial_objects: list[SpatialObject]`: Preset spatial objects to return from `analyze()`.
  - `scene_description: str`: Preset sentence for `describe_scene()` (defaults to `NO_OBJECTS`).
  - `ahead_description: str`: Preset sentence for `describe_ahead()` (defaults to `NOTHING_AHEAD`).
  - `alerts: list[Alert]`: Preset alerts returned by `select_alerts()`.
  - `reset_cooldowns_called: bool`: Set to `True` whenever `reset_cooldowns()` is called.
  - Call recording lists (`analyze_calls`, `describe_scene_calls`, `describe_ahead_calls`, `select_alerts_calls`): Enable tests to inspect exactly what data was passed to navigation.

---

### 2.5 `FakeOcrReader` (Implements `IOcrReader`)

- **Protocol Contract (`IOcrReader`):**
  - `preload() -> None`
  - `is_ready() -> bool`
  - `is_busy() -> bool`
  - `read_async(frame: np.ndarray, on_done: Callable[[OCRResult], None]) -> bool`
  - `read_sync(frame: np.ndarray) -> OCRResult`
- **Internal State:**
  - `ready: bool`: Settable flag indicating if OCR weights are loaded.
  - `busy: bool`: Settable flag indicating whether an OCR job is currently running.
  - `result: OCRResult`: The preset text result returned.
- **Key Behavior:**
  - If `ready == False` or `busy == True`, `read_async()` immediately returns `False` without calling `on_done`.
  - Otherwise, it synchronously calls `on_done(self.result)` and returns `True`. This lets async controller tests verify text handling without launching background threads.

---

### 2.6 `FakeSpeaker` (Implements `ISpeaker`)

- **Protocol Contract (`ISpeaker`):**
  - `on_speaking_changed: Callable[[bool], None]`
  - `start() -> None`
  - `stop() -> None`
  - `speak(text: str, priority: Priority = Priority.RESPONSE, interrupt: bool = False) -> None`
  - `stop_speaking() -> None`
  - `repeat_last() -> None`
  - `set_rate(value: int) -> None`
  - `set_volume(value: float) -> None`
  - `is_speaking() -> bool`
- **Internal State:**
  - `spoken: list[tuple[str, Priority]]`: History of all spoken messages and their priorities in chronological order.
  - `last_response: str | None`: Stores the last `Priority.RESPONSE` message for `repeat_last()`.
  - `stopped: bool` and `stop_count: int`: Tracks speech interruptions and cancellations.
  - `_is_speaking: bool`: Queryable vocalization state.
- **Key Behavior:**
  - Calling `speak("...", interrupt=True)` or `stop_speaking()` sets `stopped = True` and calls `set_speaking(False)`.
  - Calling `set_speaking(True/False)` automatically invokes the `on_speaking_changed` callback, allowing the voice input module to test self-hearing prevention.

---

### 2.7 `FakeListener` (Implements `IListener`)

- **Protocol Contract (`IListener`):**
  - `start() -> None`
  - `stop() -> None`
  - `calibrate() -> None`
  - `listen_once_async(on_result: Callable[[ListenResult], None]) -> bool`
  - `is_available() -> bool`
- **Internal State:**
  - `available: bool`: Settable flag simulating whether a microphone is connected.
  - `calibrated: bool`: Tracks ambient noise calibration calls.
  - `_pending_callback`: Stores the callback provided in `listen_once_async()`.
  - `_queued_results`: Stores results queued before listening started.
- **Key Behavior (Push-to-Talk Simulation):**
  - In unit tests, we cannot speak into a real microphone. Instead, the test calls `listener.listen_once_async(callback)`.
  - The test then simulates the user speaking by calling `listener.push_transcript("describe")` or `listener.push_result(ListenResult(...))`.
  - This immediately executes the callback with the fake speech result!

---

## 3. How Data Flows in a Hardware-Free Test

Here is an example of an end-to-end user journey tested using only our fake objects:

```
[Test Script]
     │
     ├─► 1. Camera: fake_cam.frame = custom_image
     │
     ├─► 2. Detector: fake_detector.set_result([make_detection("person", ...)])
     │
     ├─► 3. Controller asks Detector for result
     │
     ├─► 4. Controller asks Navigation to describe scene
     │        fake_nav.scene_description = "I see a person ahead, close."
     │
     ├─► 5. Controller tells Speaker to speak
     │        fake_speaker.speak(...)
     │
     └─► 6. Test Assertion:
              assert fake_speaker.spoken[-1] == ("I see a person ahead, close.", Priority.RESPONSE)
```

**Zero hardware touched, zero network requests, 100% fast and deterministic!**

---

## 4. Interface Changes

**No interfaces were changed or modified.**
All fake classes strictly implement the signatures and protocols defined in `eyesite/core/interfaces.py` and `docs/PRD.md` Section K.

---

## 5. Potential Examiner / Viva Questions & Answers

### Q1: What is `typing.Protocol` and how does it differ from an Abstract Base Class (`ABC`)?
- **Answer:** An `ABC` uses *nominal subtyping*: a class must explicitly inherit from the ABC (`class RealCamera(ICamera)`).
- A `Protocol` (PEP 544) uses *structural subtyping* (duck typing): if a class has methods matching the names and signatures of the Protocol, Python considers it an implementation of that Protocol, even if it does not inherit from it. This keeps modules completely decoupled.

### Q2: Why is `make_detection` using an immutable `BBox`?
- **Answer:** `BBox` is a frozen dataclass (`@dataclass(frozen=True)`). Bounding box coordinates should never be mutated unexpectedly by another module (which would cause subtle bugs in spatial zoning). New bounding boxes are created instead.

### Q3: How do we test stale detection results?
- **Answer:** EyeSite has a rule that if a detection result is older than 1.5 seconds, the app should announce "I cannot see clearly right now." With `FakeDetector`, we can set `detector.timestamp = time.time() - 2.0`. The controller will see this old timestamp and trigger the stale-result logic without having to wait in real time.

### Q4: How does `FakeListener` simulate voice input?
- **Answer:** Instead of capturing microphone audio, `FakeListener` exposes `push_transcript(text)`. When the controller starts listening via `listen_once_async(on_result)`, the test calls `listener.push_transcript("describe")`, which immediately fires the callback with `ListenResult(transcript="describe")`.

### Q5: How do we ensure these fakes don't break when interfaces change?
- **Answer:** We have automated unit tests in `tests/unit/test_fakes.py` that run `isinstance(fake, Protocol)` using `@runtime_checkable`. If any method signature or attribute is missing or mismatched, `pytest` fails immediately.
