# EyeSite Core Module: Beginner's Guide & Viva Preparation

This document explains every file, class, and function created in **Phase 0** in simple English. It is written to help you understand the architecture, explain it with confidence in your project review / viva exam, and see how data moves through EyeSite.

---

## 1. What is the Core Module?

Think of the **Core module** (`eyesite/core/`) as the **foundation and contract layer** of the entire EyeSite project:
- In a team project, multiple developers work on different modules at the same time: one person writes the camera code, another writes YOLO detection, another writes text-to-speech, and another builds the UI.
- If everyone made up their own function names or data formats, the parts would never connect.
- The Core module establishes **shared data formats (`models.py`)**, **interfaces/contracts (`interfaces.py`)**, **configuration (`config.py`)**, **logging (`logging_setup.py`)**, and **speech sentences (`messages.py`)**.
- Because Phase 0 is defined first, other team members can build and test their modules independently using fakes or mocks.

---

## 2. File-by-File Breakdown

### 2.1 `eyesite/core/models.py` (Data Structures & Types)

This file defines all data that flows between modules.

#### Enums (Sets of predefined choices)
- **`Zone`**: Represents the horizontal third of the camera frame where an object is located:
  - `LEFT`: Object is on the left third of the user's view (ratio < 0.33).
  - `CENTER`: Object is ahead/in front (0.33 ≤ ratio ≤ 0.67).
  - `RIGHT`: Object is on the right third (ratio > 0.67).
- **`Proximity`**: Coarse distance estimate derived from the bounding box's area relative to the frame:
  - `FAR`: Small box, distant object.
  - `NEAR`: Moderate box (area ratio ≥ 0.12), nearby object ("close").
  - `VERY_CLOSE`: Large box (area ratio ≥ 0.35), obstacle is right in front ("very close").
- **`Priority`** (`IntEnum`): Defines urgency for spoken announcements. Lower number means higher priority:
  - `CRITICAL` (0): Urgent obstacle alerts ("Person ahead, very close. Stop.") or critical errors. Can interrupt lower priorities.
  - `RESPONSE` (1): Direct answers to user commands ("I see two chairs on your left").
  - `INFO` (2): Routine background guidance chatter. Automatically dropped if older than 3 seconds.
- **`AppState`**: Tracks the overall operating mode of the application:
  - `STARTING`, `IDLE`, `GUIDANCE`, `BUSY_OCR`, `ERROR_DEGRADED`, `SHUTTING_DOWN`.
- **`Intent`**: Normalised purpose of a user command:
  - `DESCRIBE`, `AHEAD`, `READ_TEXT`, `GUIDANCE_ON`, `GUIDANCE_OFF`, `REPEAT`, `STOP_SPEECH`, `HELP`, `VOLUME_UP`, `VOLUME_DOWN`, `EXIT`, `UNKNOWN`.
- **`InputSource`**: Where the command came from: `VOICE`, `KEYBOARD`, or `BUTTON`.
- **`ErrorCode`**: Standard error identifiers: `CAMERA_UNAVAILABLE`, `MODEL_LOAD_FAILED`, `OCR_NOT_READY`, `OCR_FAILED`, `MIC_UNAVAILABLE`, `STT_NETWORK_ERROR`, `TTS_FAILED`, `CONFIG_INVALID`, `UNKNOWN`.
- **`UserAction`**: Physical buttons or hotkeys pressed in the UI (Section K.7).
- **`UIEventType`**: Categories of events dispatched from the controller to the UI queue.

#### Dataclasses (Structured data packets)
- **`BBox`**: Bounding box coordinates (`x1`, `y1`, `x2`, `y2`). It is `frozen=True` (immutable) to prevent bugs. Contains computed helper properties:
  - `width`: `x2 - x1`
  - `height`: `y2 - y1`
  - `area`: `width * height`
  - `center_x`: `(x1 + x2) / 2.0`
  - `center_y`: `(y1 + y2) / 2.0`
- **`FramePacket`**: Output of the camera. Contains raw BGR numpy image frame, timestamp, frame ID, width, and height.
- **`Detection`**: A single object found by YOLO (`label`, `class_id`, `confidence`, `bbox`).
- **`DetectionResult`**: All detections found in one frame, along with inference latency (`inference_ms`).
- **`SpatialObject`**: A detection combined with spatial positioning: which `Zone`, what `Proximity`, and numerical ratios (`center_x_ratio`, `area_ratio`).
- **`Alert`**: Filtered guidance warning to be spoken (`text`, `priority`, `key`, `proximity`).
- **`OCRRegion`**: A piece of text located on an image with confidence and bounding box.
- **`OCRResult`**: Aggregated OCR result: `full_text` for screen, `spoken_text` for TTS, regions, average confidence, duration, and optional error code.
- **`SpeechItem`**: An item waiting in the text-to-speech priority queue.
- **`ListenResult`**: Result from voice recognition containing transcript and error status.
- **`Command`**: Output of the command parser combining matched `Intent`, raw text, and confidence.
- **`AppStatus`**: Diagnostic snapshot for the UI status bar (camera status, FPS, inference time, etc.).
- **`UIEvent`**: Packaging format for thread-safe UI communication (`type`, `payload`).

#### Custom Exceptions (Section L.3)
All inherit from `EyeSiteError`:
- `CameraError`, `ModelLoadError`, `OcrError`, `SpeechInputError`, `SpeechOutputError`, `ConfigError`.
- **Why?** This prevents raw library exceptions (like an OpenCV crash) from taking down the app, allowing graceful degradation and user-friendly error announcements.

---

### 2.2 `eyesite/core/interfaces.py` (Contracts / Protocols)

Python's `typing.Protocol` is used to define interfaces. A class does not need to explicitly inherit from a Protocol; as long as it has the same methods and signatures, Python recognizes that it satisfies the contract (structural subtyping / duck typing).

1. **`ICamera`**: Standardizes starting/stopping video capture and retrieving the newest frame (`get_latest_frame`).
2. **`IDetector`**: Standardizes loading YOLO, running asynchronous frame inference, synchronous single-frame detection, and drawing bounding boxes (`annotate`).
3. **`INavigation`**: Standardizes converting raw detections into spatial objects (`analyze`), generating descriptive sentences (`describe_scene`, `describe_ahead`), and throttling alerts (`select_alerts`).
4. **`IOcrReader`**: Standardizes asynchronous (`read_async`) and synchronous (`read_sync`) OCR reading.
5. **`ISpeaker`**: Standardizes queuing speech (`speak`), interrupting speech (`stop_speaking`), repeating the last message, and changing volume/rate.
6. **`IListener`**: Standardizes push-to-talk voice capture (`listen_once_async`), ambient noise calibration, and checking microphone availability.
7. **`IAppController`**: Interface presented to the Tkinter UI to handle button clicks (`on_action`), inspect status (`get_status`), read the display frame (`get_display_frame`), and consume events (`events` queue).

---

### 2.3 `eyesite/core/config.py` (Configuration Management)

- **Purpose**: Reads all tunables from `config.yaml` so there are **no hardcoded numbers** in the code (NFR-11).
- **Sub-dataclasses**: `AppConfig`, `CameraConfig`, `DetectionConfig`, `NavigationConfig`, `OcrConfig`, `VoiceOutputConfig`, `VoiceInputConfig`, `UIConfig`.
- **`load_config(path)`**:
  - If the file is missing, it logs a warning and uses safe defaults.
  - If individual keys are omitted in the YAML, it keeps their default values.
  - If extra/unknown keys exist, it ignores them with a warning.
  - If a setting has an invalid value (e.g. negative FPS, confidence > 1.0, or `left_max >= right_min`), it raises `ConfigError`.

---

### 2.4 `eyesite/core/logging_setup.py` (Central Logging)

- **`setup_logging(...)`**:
  - Logs to both the **console** (for developers during testing) and a **rotating file** `logs/eyesite.log`.
  - **Rotation**: Once the log file reaches 1 MB, it is renamed to `eyesite.log.1` and a new file starts. EyeSite keeps up to 3 backup files. This ensures the app will never fill up the user's hard drive.
  - Formatter includes the timestamp, severity level, logger name, thread name, and message.

---

### 2.5 `eyesite/core/messages.py` (Spoken Sentences Catalogue)

- Every user-facing sentence lives in this file as a constant string.
- Examples: `STARTING`, `READY`, `DISCLAIMER`, `GUIDANCE_ON`, `GUIDANCE_OFF`, `OCR_EMPTY`, `NOTHING_AHEAD`, `STALE`, `UNKNOWN_CMD`.
- **Why?** Having all sentences in one file allows easy rewording, tone adjustment, and future language translation without hunting through code.

---

### 2.6 `eyesite/core/events.py` (UI Event Helpers)

- Helper functions (`create_spoken_message_event`, `create_status_changed_event`, `create_error_event`, etc.) that package information into typed `UIEvent` objects.
- The UI thread polls the event queue to update the screen without freezing or locking worker threads.

---

## 3. How Data Flows Through EyeSite

Here is the step-by-step journey of data when a user says **"describe"**:

```
[Webcam Hardware]
       │
       ▼
1. Camera module grabs BGR frame -> stores latest FramePacket
       │
       ▼
2. YOLO Detector runs inference on the latest frame -> produces DetectionResult (boxes, labels, confidence)
       │
       ▼
3. User says "describe" -> Microphone -> SpeechListener -> transcript string
       │
       ▼
4. CommandParser matches transcript -> Command(intent=DESCRIBE)
       │
       ▼
5. AppController asks Navigation module to analyze DetectionResult:
   - Calculates horizontal ratio: center_x / frame_width -> maps to Zone (LEFT, CENTER, RIGHT)
   - Calculates area ratio: bbox_area / frame_area -> maps to Proximity (FAR, NEAR, VERY_CLOSE)
   - Groups items and builds sentence: "I can see a person in the center, close, and a chair on your left."
       │
       ▼
6. Controller calls Speaker.speak(text, Priority.RESPONSE)
   - Sentence enters PriorityQueue[SpeechItem]
   - Dedicated TTS worker thread synthesizes audio via pyttsx3
       │
       ▼
7. Controller emits UIEvent(SPOKEN_MESSAGE) -> UI event queue -> Tkinter message log displays text
```

---

## 4. Interface Changes

Under standard rule 9, any addition or modification to the PRD specification must be documented here:

1. **`UserAction` Enum**:
   - *Rationale*: PRD Section K.7 defines `IAppController.on_action(action: UserAction)` for UI button/hotkey inputs, but Section L omitted `UserAction` in its enum list.
   - *Values added*: `DESCRIBE`, `AHEAD`, `READ_TEXT`, `TOGGLE_GUIDANCE`, `LISTEN`, `REPEAT`, `STOP_SPEECH`, `HELP`, `VOLUME_UP`, `VOLUME_DOWN`, `QUIT`, `RETRY_CAMERA`.
2. **`UIEventType` Enum**:
   - *Rationale*: PRD Section L.2 referenced `type: UIEventType` in `UIEvent`, and Section K.7 referenced event types. The explicit enum was declared in `models.py`.
   - *Values added*: `SPOKEN_MESSAGE`, `STATUS_CHANGED`, `OCR_TEXT`, `ERROR`, `LISTENING_STARTED`, `LISTENING_STOPPED`, `SHOW_HELP`.

---

## 5. Potential Examiner / Viva Questions & Answers

### Q1: Why use `typing.Protocol` instead of standard abstract base classes (`abc.ABC`)?
**Answer:** `typing.Protocol` provides **structural subtyping** (static duck typing). Classes don't need to explicitly inherit from a base class to be considered valid implementations. This allows us to write lightweight test fakes (`FakeCamera`, `FakeDetector`, `FakeSpeaker`) without modifying production classes.

### Q2: Why is `BBox` a frozen dataclass?
**Answer:** Bounding boxes represent immutable geometric coordinates. Freezing them prevents accidental in-place mutation by different threads or helper functions, eliminating race conditions.

### Q3: Why is speech priority an `IntEnum` where lower values have higher priority?
**Answer:** Python's standard `PriorityQueue` sorts elements in ascending order (smallest first). Assigning `CRITICAL = 0`, `RESPONSE = 1`, and `INFO = 2` allows Python's queue to naturally pop the most urgent messages first without custom comparison logic.

### Q4: How does the configuration system handle missing or invalid keys?
**Answer:** `load_config()` uses dataclass defaults for any omitted keys. For invalid values (such as negative camera dimensions or confidence outside `[0.0, 1.0]`), it raises a custom `ConfigError`, preventing the application from running in an unstable state.

### Q5: Why is central logging configured with rotation?
**Answer:** Assistive applications often run continuously. An unrotated log file could grow indefinitely and consume the user's disk space. `RotatingFileHandler` caps each file at 1 MB and retains only the 3 most recent backups.
