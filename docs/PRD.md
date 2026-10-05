# EyeSite: Product Requirements Document (PRD) and Technical Specification

| Field | Value |
|---|---|
| Product name | EyeSite |
| Document version | 1.0 (MVP specification) |
| Project type | B.Tech CSE mini-project, assistive technology prototype |
| Primary language | Python 3.10 or 3.11 |
| Primary platform | Windows / Linux / macOS desktop or laptop with webcam, microphone and speakers |
| Intended consumers of this document | (1) Student team, (2) AI coding agent (Antigravity) |

> **How to use this document with an AI coding agent:** Build strictly in the order of Section 19 (Development Phases). Do not skip phases. Every requirement has an ID (e.g. `FR-DET-03`). Interfaces in Section 11 and data structures in Section 12 are binding contracts: keep names and signatures unless a change is documented. "MUST" = required for MVP, "SHOULD" = strongly desired, "MAY" = optional.

---

## A. PRODUCT OVERVIEW

### A.1 Identity

- **Product name:** EyeSite
- **Product type:** AI-powered assistive desktop application (prototype)
- **Core principle:** *"The camera sees, and the voice tells."*
- **Target platform:** Desktop/laptop, fully offline-capable after installation (see Section 8 for one optional online dependency)
- **Intended users:** Visually impaired and low-vision users (primary); sighted helpers, teachers, evaluators (secondary)

### A.2 One-line product definition

> EyeSite is an AI-powered assistive desktop application that uses computer vision, OCR and voice interaction to help visually impaired users understand nearby objects, read visible text, and learn the approximate direction of obstacles through spoken feedback.

### A.3 Vision

A low-cost information layer, built from an ordinary webcam and open-source AI, that gives people with visual impairment more awareness of their immediate surroundings without special hardware.

### A.4 Mission

Deliver a reliable end-to-end pipeline **Camera → AI perception → understanding → voice response** that is simple, fast, honest about its limitations, and usable without looking at the screen.

### A.5 What EyeSite is NOT

EyeSite is an assistive technology **prototype**. It is **not** a replacement for a white cane, guide dog, orientation-and-mobility training, or human assistance, and must never be presented as a safety-critical navigation device. The application shows this disclaimer on first launch and speaks a short version of it.

---

## B. PROBLEM STATEMENT

Visually impaired users often cannot easily determine:

1. What objects are in front of them.
2. What printed text is visible (labels, signs, documents).
3. Whether something is on their left, ahead, or right.
4. Whether a large object is very close.

White canes and guide dogs solve mobility very well but do not provide semantic information ("that is a chair", "the sign says EXIT"). Existing commercial solutions are often expensive, mobile-only, or cloud-dependent. EyeSite explores an affordable, offline-first desktop alternative.

---

## C. USERS AND PERSONAS

### C.1 Primary persona: "Asha", low-vision or blind user

- Comfortable with keyboard and voice, prefers audio feedback.
- Needs: short, clear, non-repetitive speech; ability to interrupt; large controls; predictable behaviour.
- Cannot rely on the screen. **Every feature must be usable through voice and keyboard only.**

### C.2 Secondary persona: "Ravi", sighted helper / evaluator

- Sets up the laptop and camera, reads the on-screen status, checks logs.
- Needs: visible video feed with bounding boxes, status panel, log of spoken messages, easy start/stop.

### C.3 Secondary persona: "Examiner / demo audience"

- Needs: a clear, quick demonstration of each capability and visible proof of what the AI detected.

### C.4 Assumptions about the environment

- Camera is a laptop or USB webcam, pointed forward, held or mounted steady.
- Indoor or well-lit environments.
- Quiet-to-moderate background noise.
- English language only for MVP.

---

## D. GOALS, NON-GOALS AND SUCCESS METRICS

### D.1 Product goals

| ID | Goal |
|---|---|
| G1 | Access a webcam and process live frames reliably. |
| G2 | Detect common objects using YOLOv8n. |
| G3 | Compute approximate horizontal position (left / center / right) of each object. |
| G4 | Estimate rough proximity (very close / near / far) using bounding-box size only. |
| G5 | Read visible text on demand using EasyOCR. |
| G6 | Speak all outputs through offline text-to-speech. |
| G7 | Accept basic voice commands, plus keyboard/button equivalents. |
| G8 | Provide a simple, high-contrast Tkinter interface. |
| G9 | Integrate everything into one stable application suitable for live demonstration. |

### D.2 Non-goals (MVP)

Facial recognition, GPS/route navigation, medical features, emergency calling, cloud AI, mobile app, smart glasses, robotics, metric 3D depth, multi-language support, user accounts. See Section 18 for future scope.

### D.3 Success metrics (measured during testing)

| Metric | Target |
|---|---|
| Live processing rate (detection loop) on a mid-range laptop CPU | ≥ 8 FPS displayed video; detection at ≥ 4 inferences/second |
| Video display never blocked by speech, OCR or STT | 100% (no UI freeze > 300 ms) |
| Time from "describe" command to start of speech | ≤ 2.5 s |
| Time from "read text" command to start of speech | ≤ 6 s (first run may add model-load time; see FR-OCR-05) |
| Position classification correctness on staged test scenes | ≥ 90% |
| Voice command recognition (quiet room, clear speech) | ≥ 85% |
| Crash-free 15-minute continuous run | Yes |
| Automated tests passing | 100% of unit tests; integration tests documented |

---

## E. CORE USER JOURNEY AND INTERACTION MODEL

### E.1 Application lifecycle (startup to first spoken answer)

1. User launches `python main.py`.
2. App shows a splash/status ("Loading models…") and speaks: *"EyeSite is starting."*
3. Core loads config, initialises TTS, camera, YOLO model. EasyOCR is **lazy-loaded** on first use (or in a background thread after startup).
4. If all critical components are healthy, EyeSite speaks: *"EyeSite is ready. Say help to hear commands. Reminder: EyeSite does not replace your cane or guide."* (full disclaimer only on first run; afterwards, short version.)
5. App enters **IDLE** state: camera feed and detections are visible on screen, but no automatic speech except responses to commands.
6. User gives a command by voice (push-to-talk key) or by button/hotkey.
7. Core routes to the relevant module, builds a natural-language response, and queues it to TTS.
8. User hears the answer; app returns to IDLE (or stays in GUIDANCE mode if active).

### E.2 Operating modes (state machine)

| State | Description | Automatic speech? |
|---|---|---|
| `STARTING` | Loading resources | Only startup messages |
| `IDLE` | Camera running, waiting for commands | No |
| `GUIDANCE` | Continuous obstacle monitoring active | Yes: obstacle alerts only, rate-limited |
| `BUSY_OCR` | OCR running on a captured frame | "Reading text" acknowledgement, then result |
| `ERROR_DEGRADED` | A non-critical module failed (e.g. mic missing); app continues with reduced features | Announces the degradation once |
| `SHUTTING_DOWN` | Releasing resources | "Goodbye." |

Allowed transitions: `STARTING→IDLE`, `IDLE↔GUIDANCE`, `IDLE→BUSY_OCR→IDLE`, `GUIDANCE→BUSY_OCR→GUIDANCE`, any→`ERROR_DEGRADED` (non-fatal), any→`SHUTTING_DOWN`.

### E.3 Input methods (all MUST be supported)

| Action | Voice command (examples) | Keyboard hotkey | UI button |
|---|---|---|---|
| Describe surroundings | "describe", "what is around me", "what do you see" | `D` | Describe |
| What is ahead | "what is ahead", "what is in front" | `A` | Ahead |
| Read text | "read text", "read", "what does it say" | `R` | Read Text |
| Start guidance | "start guidance", "start guide", "navigate" | `G` | Guidance ON |
| Stop guidance | "stop guidance", "stop guide" | `G` (toggle) | Guidance OFF |
| Repeat last message | "repeat", "say again" | `P` | Repeat |
| Stop speaking | "stop", "quiet", "silence" | `Space` while speaking, or `S` | Stop Speech |
| Help | "help", "commands" | `H` | Help |
| Volume | "louder", "quieter" | `+` / `-` | Volume slider |
| Exit | "exit", "quit", "close" | `Q` or `Esc` (with confirmation) | Quit |

**Voice input activation (design decision):** Default is **push-to-talk**: the user holds/presses `T` (or clicks "Listen"), hears a short beep, speaks, and the app processes one command. This avoids constant false triggers from background noise and from EyeSite's own speech. An optional **continuous listening** mode (`voice.continuous_listening: true`) MAY be provided, but must pause listening while TTS is speaking.

### E.4 Example interactions (binding response style)

| User | EyeSite response |
|---|---|
| "describe" | "I can see a person in the center, a chair on your left, and a laptop on your right." |
| "what is ahead" | "Ahead of you is a person, close." / "Nothing detected ahead." |
| "read text" | "Reading text." … "I found: EXIT. Fire safety notice." |
| "read text" (nothing) | "I could not find any readable text. Try moving closer or improving the light." |
| Guidance alert | "Chair, left, close." / "Person ahead, very close. Stop." |
| Unknown speech | "Sorry, I did not understand. Say help for commands." |
| "help" | "You can say: describe, what is ahead, read text, start guidance, stop guidance, repeat, stop, louder, quieter, or exit." |

**Speech style rules:** short sentences; lead with the most important fact; no jargon; no confidence percentages spoken (only shown on screen); never claim certainty about distance in metres.

---

## F. FUNCTIONAL REQUIREMENTS

### F.1 Camera module (`FR-CAM`)

| ID | Requirement | Priority |
|---|---|---|
| FR-CAM-01 | Open the webcam using OpenCV `VideoCapture`, default device index 0, configurable. | MUST |
| FR-CAM-02 | Run frame capture in a dedicated thread that always keeps only the **latest** frame (no growing queue, no stale-frame lag). | MUST |
| FR-CAM-03 | Provide `get_latest_frame()` returning a copy of the newest frame plus a timestamp and frame id. | MUST |
| FR-CAM-04 | Configurable resolution (default 640×480) and target FPS (default 30). | MUST |
| FR-CAM-05 | Detect camera open failure or repeated read failure; attempt up to 3 reconnects with 1 s delay; then report `CAMERA_UNAVAILABLE`. | MUST |
| FR-CAM-06 | Release camera cleanly on shutdown. | MUST |
| FR-CAM-07 | Support choosing a video file instead of a webcam for testing (`camera.source: "video.mp4"`). | SHOULD |

### F.2 Object detection module (`FR-DET`)

| ID | Requirement | Priority |
|---|---|---|
| FR-DET-01 | Load YOLOv8n (`yolov8n.pt`) through Ultralytics once at startup. | MUST |
| FR-DET-02 | `detect(frame)` returns a list of `Detection` objects (label, confidence, bbox). | MUST |
| FR-DET-03 | Filter by configurable confidence threshold (default 0.45) and optional NMS IoU threshold (default 0.5). | MUST |
| FR-DET-04 | Use the 80 COCO class labels. Maintain a configurable **"relevant classes" list** for navigation alerts (see Section 13). | MUST |
| FR-DET-05 | Inference runs in its own worker thread at a configurable maximum rate (default 5 Hz), always using the latest frame. | MUST |
| FR-DET-06 | Provide temporal smoothing: an object is "confirmed" only if seen in ≥ 2 of the last 3 inferences (reduces flicker). | SHOULD |
| FR-DET-07 | Produce annotated frames for display (boxes, labels, confidence) without modifying the raw frame. | MUST |
| FR-DET-08 | Support CPU by default; use GPU automatically if available (`device: "auto"`). | SHOULD |

### F.3 Navigation / spatial-understanding module (`FR-NAV`)

| ID | Requirement | Priority |
|---|---|---|
| FR-NAV-01 | For each detection compute `center_x_ratio = (x1+x2)/2 / frame_width`. | MUST |
| FR-NAV-02 | Map to zone: `LEFT` if ratio < 0.33, `CENTER` if 0.33 ≤ ratio ≤ 0.67, `RIGHT` if > 0.67 (thresholds configurable). | MUST |
| FR-NAV-03 | Compute `area_ratio = bbox_area / frame_area` and map to proximity: `VERY_CLOSE` ≥ 0.35, `NEAR` ≥ 0.12, `FAR` otherwise (configurable, per-class overrides MAY be added). | MUST |
| FR-NAV-04 | Produce `SpatialObject` records combining detection + zone + proximity. | MUST |
| FR-NAV-05 | Generate a **scene description** sentence from a list of `SpatialObject`s (grouping duplicates: "two chairs on your left"). | MUST |
| FR-NAV-06 | Generate **obstacle alerts** only for relevant classes in `CENTER` zone (any proximity ≥ NEAR) and for `VERY_CLOSE` objects in any zone. | MUST |
| FR-NAV-07 | Implement announcement throttling: per-(label, zone) cooldown (default 6 s), global minimum interval between alerts (default 2.5 s), and "changed state" detection (announce again if proximity worsens, e.g. NEAR→VERY_CLOSE, even during cooldown). | MUST |
| FR-NAV-08 | Limit any single spoken alert/description to at most 4 items, prioritised by proximity, then zone (CENTER first), then confidence. | MUST |
| FR-NAV-09 | Provide `what_is_ahead()` summarising CENTER-zone objects only. | MUST |

### F.4 OCR module (`FR-OCR`)

| ID | Requirement | Priority |
|---|---|---|
| FR-OCR-01 | OCR runs **on demand only** (never per frame). | MUST |
| FR-OCR-02 | On command, capture the latest frame (freeze it), run EasyOCR (`en`) in a worker thread. | MUST |
| FR-OCR-03 | Pre-process the frame (grayscale, optional contrast enhancement / resize) to improve accuracy. | SHOULD |
| FR-OCR-04 | Discard text results below configurable confidence (default 0.40); merge results into reading order (top-to-bottom, left-to-right, grouped by line). | MUST |
| FR-OCR-05 | Lazy-load the EasyOCR reader in a background thread at startup (config `ocr.preload: true`); if the user asks before it is ready, speak "Text reader is still loading, please wait." | MUST |
| FR-OCR-06 | Return an `OCRResult` (full text, list of text regions, average confidence, duration). | MUST |
| FR-OCR-07 | Limit spoken text to a configurable maximum (default 400 characters), then say "There is more text. Say read text again after moving closer." | SHOULD |
| FR-OCR-08 | Handle empty results gracefully with the standard message (Section E.4). | MUST |
| FR-OCR-09 | Show the OCR text on screen in a scrollable text panel. | MUST |

### F.5 Voice output module (`FR-TTS`)

| ID | Requirement | Priority |
|---|---|---|
| FR-TTS-01 | Use `pyttsx3` (offline). | MUST |
| FR-TTS-02 | All speech goes through a single **speech queue** consumed by one dedicated worker thread that **creates and owns** the pyttsx3 engine (avoids known pyttsx3 threading/`runAndWait` issues). | MUST |
| FR-TTS-03 | Priorities: `CRITICAL` (very-close alerts, errors) > `RESPONSE` (answers to user commands) > `INFO` (guidance chatter, status). Higher priority may interrupt lower priority. | MUST |
| FR-TTS-04 | `speak(text, priority)`, `stop()`, `repeat_last()`, `set_rate()`, `set_volume()`, `is_speaking()`. | MUST |
| FR-TTS-05 | Drop queued `INFO` messages older than 3 s (stale guidance is worse than silence). | MUST |
| FR-TTS-06 | De-duplicate identical consecutive messages within the cooldown window. | MUST |
| FR-TTS-07 | Log every spoken message with timestamp to the on-screen log and log file. | MUST |
| FR-TTS-08 | Expose a "speaking" event so the STT module can pause listening (prevents self-hearing). | MUST |

### F.6 Voice input module (`FR-STT`)

| ID | Requirement | Priority |
|---|---|---|
| FR-STT-01 | Use `SpeechRecognition` with `Microphone` (PyAudio). | MUST |
| FR-STT-02 | Calibrate for ambient noise once at startup (≈ 1 s) and on demand. | MUST |
| FR-STT-03 | Push-to-talk capture with timeout (default 5 s wait, 6 s phrase limit). | MUST |
| FR-STT-04 | Recognise using the Google Web Speech engine (`recognize_google`) when internet is available; **fallback** to an offline engine (Vosk, or PocketSphinx) if configured. If neither works, degrade to keyboard/buttons only and announce it. | MUST (online), SHOULD (offline fallback) |
| FR-STT-05 | Return raw transcript to the **Command Parser** (in Core), not to other modules directly. | MUST |
| FR-STT-06 | Run listening in a worker thread; never block the UI. | MUST |
| FR-STT-07 | Handle `WaitTimeoutError`, `UnknownValueError`, `RequestError` distinctly (see Section 15). | MUST |
| FR-STT-08 | Play a short start-listening beep and a stop-listening beep (generated with `winsound`/`simpleaudio` or a bundled WAV). | SHOULD |

### F.7 Core / integration module (`FR-CORE`)

| ID | Requirement | Priority |
|---|---|---|
| FR-CORE-01 | `AppController` owns all modules, the state machine, and the event queue. | MUST |
| FR-CORE-02 | Implement the **Command Parser**: normalise text (lowercase, strip punctuation), match against intent keyword sets, return a `Command` with intent and confidence. Fuzzy matching (e.g. `difflib`) SHOULD be used for near-misses. | MUST |
| FR-CORE-03 | Route intents to handlers (`DESCRIBE`, `AHEAD`, `READ_TEXT`, `GUIDANCE_ON`, `GUIDANCE_OFF`, `REPEAT`, `STOP_SPEECH`, `HELP`, `VOLUME_UP`, `VOLUME_DOWN`, `EXIT`, `UNKNOWN`). | MUST |
| FR-CORE-04 | Load configuration from `config.yaml` with defaults and validation; missing keys fall back to defaults. | MUST |
| FR-CORE-05 | Central logging (file `logs/eyesite.log` + console) with rotation. | MUST |
| FR-CORE-06 | Startup health check for each module with results shown in the UI and summarised by voice. | MUST |
| FR-CORE-07 | Graceful shutdown: stop threads in order (STT → GUIDANCE → detection → OCR → TTS → camera), join with timeouts, release resources. | MUST |
| FR-CORE-08 | Ensure no module calls another module's internals: all cross-module communication goes through interfaces defined in Section 11 or events in Section 10.4. | MUST |

### F.8 UI module (`FR-UI`)

See Section 14 for the full UI specification. Key requirements: live annotated video, status bar, large accessible buttons, spoken-message log, OCR text panel, keyboard shortcuts for every action, high-contrast theme, UI updates only from the Tkinter main thread.

---

## G. NON-FUNCTIONAL REQUIREMENTS

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Performance | Video display stays smooth regardless of inference, OCR or speech activity (separate threads). |
| NFR-02 | Latency | End-to-end response latencies per Section D.3. |
| NFR-03 | Reliability | No unhandled exception may crash the app; errors are logged and announced in plain language. |
| NFR-04 | Accessibility | Every function reachable without the mouse and without seeing the screen. UI font ≥ 16 pt; buttons ≥ 48 px high; contrast ratio ≥ 7:1 (WCAG AAA target). |
| NFR-05 | Privacy | No frames, audio, or text are stored or transmitted, except the audio clip sent to Google for STT when online mode is used. Disclose this in the README and on the Help screen. Logs contain text only, never images. |
| NFR-06 | Offline capability | Detection, OCR, TTS work fully offline. STT is online by default with optional offline fallback. |
| NFR-07 | Portability | Runs on Windows 10/11 (primary), and Linux/macOS with documented setup differences. |
| NFR-08 | Maintainability | Modular code, type hints, docstrings, PEP 8 (checked with `ruff` or `flake8`), no module > ~400 lines. |
| NFR-09 | Testability | Modules depend on interfaces so they can be tested with mocks (fake camera, fake detector, fake TTS). |
| NFR-10 | Resource use | Steady-state RAM < 3 GB; CPU use may be high but must not starve the UI thread. |
| NFR-11 | Configurability | All thresholds and timings live in `config.yaml`; no magic numbers in code. |

---

## H. SYSTEM ARCHITECTURE

### H.1 Architectural style

A **layered, modular, multi-threaded desktop architecture** with a central controller (orchestrator). Modules do not know about each other; they expose small interfaces and communicate through the controller and thread-safe queues.

### H.2 Logical architecture

```
                        ┌───────────────────────────────────────────┐
                        │                 UI (Tkinter)              │
                        │  video panel · buttons · status · logs    │
                        └───────────────▲──────────────┬────────────┘
                     display data / status │             │ user actions (buttons/hotkeys)
                                           │             ▼
┌──────────────┐  frames   ┌───────────────┴─────────────────────────┐   text    ┌──────────────┐
│ Camera       │──────────►│           Core: AppController           │◄──────────│ Voice Input  │
│ (thread)     │           │  state machine · command parser ·       │ transcript│ (STT thread) │
└──────────────┘           │  event queue · config · logging         │           └──────────────┘
                           └───┬────────────┬───────────┬────────┬───┘
                               │            │           │        │ speak(text, priority)
                     frame     ▼            ▼           ▼        ▼
                        ┌──────────┐  ┌───────────┐ ┌────────┐ ┌───────────────┐
                        │ Detector │  │Navigation │ │  OCR   │ │ Voice Output  │
                        │ (thread) │─►│ Analyzer  │ │(worker)│ │ (TTS thread)  │
                        └──────────┘  └───────────┘ └────────┘ └───────────────┘
```

### H.3 Threading model

| Thread | Owner | Purpose | Rule |
|---|---|---|---|
| Main / UI | Tkinter | Rendering, user input | Never runs inference, OCR, STT, or blocking I/O. UI updates come only via `root.after()` polling of a thread-safe `queue.Queue`. |
| CameraThread | Camera module | Grab frames | Overwrites a single "latest frame" slot under a lock. |
| DetectionThread | Detector | YOLO inference at ≤ 5 Hz | Reads latest frame, publishes `DetectionResult`. |
| GuidanceLogic (may run inside DetectionThread callback or the controller's event loop) | Navigation | Turns detections into alerts | Pure functions; no I/O. |
| OCRWorker | OCR module | One-shot OCR jobs | Single worker; rejects a new job while one runs ("Still reading"). |
| STTThread | Voice input | Push-to-talk capture and recognition | Paused while TTS speaks. |
| TTSThread | Voice output | Owns pyttsx3 engine and speech queue | Only thread that touches pyttsx3. |

### H.4 Data flow (per user command "describe")

1. UI/STT produces raw text → `AppController.handle_input(text, source)`.
2. Command Parser → `Command(intent=DESCRIBE)`.
3. Controller asks Detector for `get_latest_result()`.
4. Controller passes it to Navigation → `SpatialObject[]` → `describe_scene()` string.
5. Controller calls `tts.speak(text, Priority.RESPONSE)`.
6. Controller emits `SPOKEN_MESSAGE` event to UI for the log.

### H.5 Data flow (GUIDANCE mode)

`Camera → Detector (5 Hz) → Navigation.analyze() → AlertPolicy (cooldown/priority) → TTS (INFO or CRITICAL) → UI log`

### H.6 Communication mechanism (binding)

- **Latest-value slots** (lock-protected) for camera frames and latest detection results.
- **`queue.Queue`** for: UI events (controller → UI), speech requests (controller → TTS), input events (STT/UI → controller).
- **Callbacks** are allowed only for: `TTS.on_speaking_changed`, `STT.on_transcript`, `OCR.on_result`; callbacks must only enqueue events, never touch the UI directly.

---

## I. MODULE SPECIFICATIONS

### I.1 Recommended project structure

```
eyesite/
├── main.py                     # entry point
├── config.yaml                 # all tunables
├── requirements.txt
├── README.md
├── docs/
│   ├── PRD.md                  # this document
│   ├── architecture.md
│   └── user_guide.md
├── eyesite/
│   ├── __init__.py
│   ├── core/
│   │   ├── controller.py       # AppController + state machine
│   │   ├── command_parser.py   # intents, fuzzy matching
│   │   ├── config.py           # load/validate config
│   │   ├── events.py           # Event types + dataclasses
│   │   ├── models.py           # shared dataclasses / enums
│   │   └── logging_setup.py
│   ├── camera/camera.py
│   ├── detection/detector.py
│   ├── navigation/
│   │   ├── spatial.py          # zone + proximity
│   │   ├── describer.py        # sentence generation
│   │   └── alert_policy.py     # cooldown / priority
│   ├── ocr/reader.py
│   ├── voice/
│   │   ├── speaker.py          # TTS
│   │   └── listener.py         # STT
│   └── ui/
│       ├── app_window.py
│       └── theme.py
├── assets/beep_start.wav, beep_stop.wav
├── tests/
│   ├── unit/…
│   ├── integration/…
│   └── fixtures/ (sample images, sample video, fake modules)
└── logs/
```

### I.2 Camera module

- **Class:** `CameraStream` (implements `ICamera`).
- **Behaviour:** starts thread on `start()`. Loop: `cap.read()`; on success, store `(frame, timestamp, frame_id)` under lock; on failure, increment failure counter; after 30 consecutive failures trigger reconnect logic (FR-CAM-05).
- **Config:** `camera.source`, `camera.width`, `camera.height`, `camera.fps`, `camera.mirror` (default false).
- **Output:** `FramePacket`.

### I.3 Detection module

- **Class:** `YoloDetector` (implements `IDetector`).
- **Steps per inference:** get latest frame → skip if `frame_id` unchanged → `model.predict(frame, conf=…, iou=…, imgsz=640, verbose=False)` → convert to `Detection[]` → apply smoothing → store `DetectionResult`.
- **Warm-up:** run one dummy inference at startup so first real inference is fast.
- **Publishing:** `get_latest_result()` returns the newest `DetectionResult` (with `frame_id`, `frame_size`, timestamp, detections).
- **Staleness rule:** a result older than 1.5 s is considered stale; consumers must not describe stale data (say "I cannot see clearly right now" instead).

### I.4 Navigation module

Three cooperating pieces, all **pure Python with no hardware access** (easy to unit-test):

1. `SpatialAnalyzer.analyze(result) -> list[SpatialObject]`: zone + proximity.
2. `SceneDescriber`:
   - `describe_scene(objs) -> str`
   - `describe_ahead(objs) -> str`
   - `format_alert(obj) -> str`
3. `AlertPolicy.select_alerts(objs, now) -> list[Alert]`: applies relevance filter, cooldowns, state-change logic, max items.

**Description grammar (binding):**

- Group by (label, zone), count objects: `"a chair"`, `"two chairs"`, `"several chairs"` (≥ 4).
- Zone phrases: `LEFT → "on your left"`, `CENTER → "in the center"` (for description) or `"ahead"` (for alerts), `RIGHT → "on your right"`.
- Proximity words appended for `NEAR` ("close") and `VERY_CLOSE` ("very close"). `FAR` adds nothing.
- Join with commas and "and". Example: `"I can see a person ahead, close, two chairs on your left, and a laptop on your right."`
- No detections: `"I do not see any known objects."`
- Ordering: CENTER, then LEFT, then RIGHT; within a zone, nearest first.

**Proximity honesty rule:** proximity is a heuristic from box size and is class-dependent (a small bottle close to the camera may look like a large chair far away). The MVP therefore uses only the coarse words "close" and "very close", never metres or centimetres.

### I.5 OCR module

- **Class:** `EasyOcrReader` (implements `IOcrReader`).
- **Flow:** `read_async(frame) -> job_id`; result delivered via callback/event as `OCRResult`.
- **Pre-processing (configurable):** resize so longest side ≈ 1280 px, convert to grayscale, apply CLAHE contrast, optional sharpening.
- **Post-processing:** filter by confidence, sort regions by `(round(y_center / line_height), x)` to form lines, join lines with ". " for TTS and "\n" for display, collapse whitespace, drop strings of ≤ 1 character unless alphanumeric-dominant.
- **Concurrency:** one job at a time; `is_busy()` exposed.

### I.6 Voice output module

- **Class:** `PyttsxSpeaker` (implements `ISpeaker`).
- **Internals:** `PriorityQueue[SpeechItem]`; worker loop creates engine inside the thread, applies rate/volume, speaks with `engine.say()` + `engine.runAndWait()`. Interruption: use `engine.stop()` from a safe path (documented workaround: on interrupt, set an `interrupt` flag, call `engine.stop()`, then continue loop). If a specific OS proves unreliable, the agent MAY re-create the engine per utterance (document the reason).
- **Defaults:** rate 170 wpm, volume 0.9, voice = first English voice found.
- **Events:** emits `SPEAKING_STARTED` / `SPEAKING_FINISHED`.

### I.7 Voice input module

- **Class:** `SpeechListener` (implements `IListener`).
- **Flow:** `listen_once()` in worker thread → beep → `recognizer.listen(source, timeout, phrase_time_limit)` → recognise → enqueue `TRANSCRIPT` event (or error event) → beep.
- **Self-hearing prevention:** refuse to start (or discard result) if TTS is speaking. Wait up to 1 s after TTS finishes before opening the mic.
- **Ambient calibration:** `recognizer.adjust_for_ambient_noise(source, duration=1)`; `dynamic_energy_threshold = True`.

### I.8 Core module

- **`AppController`:** constructed with dependency-injected module instances (real or fake). Methods: `start()`, `stop()`, `handle_input(text, source)`, `on_button(action)`, `tick()` (periodic, drives guidance), `get_status()`.
- **`CommandParser.parse(text) -> Command`:**
  1. Normalise.
  2. Exact phrase and keyword match against the intent table (Section 13.2).
  3. If no match, fuzzy match with `difflib.get_close_matches` (cutoff 0.75) over known phrases.
  4. Otherwise `UNKNOWN`.
- **Guidance loop:** driven by a controller timer (every 200 ms) that pulls the latest detection result, runs Navigation, and enqueues speech.

### I.9 UI module

See Section 14.

---

## J. TECHNOLOGY STACK (BASELINE)

| Area | Technology | Notes |
|---|---|---|
| Language | Python 3.10/3.11 | 3.12+ may have wheel gaps for some AI packages; pin to 3.10 or 3.11. |
| Camera / image | `opencv-python` | Capture, preprocessing, drawing. |
| Detection | `ultralytics` (YOLOv8n) | `yolov8n.pt` auto-downloads once; bundle the file in the repo/assets to guarantee offline demo. |
| OCR | `easyocr` | Requires PyTorch; ~200 MB models downloaded on first use. Pre-download and cache before demo (`~/.EasyOCR`). |
| TTS | `pyttsx3` | Offline; uses SAPI5 (Windows), NSSpeechSynthesizer (macOS), eSpeak (Linux). |
| STT | `SpeechRecognition` + `PyAudio` | Google Web Speech (online). |
| UI | `tkinter` + `Pillow` (`ImageTk`) | Video shown via `PhotoImage`. |
| Config | `PyYAML` | `config.yaml`. |
| Testing | `pytest`, `pytest-mock`, `pytest-cov` | |
| Lint/format | `ruff` (or flake8) + `black` | |
| VCS | Git + GitHub | Branching in Section 19.4. |
| Numerics | `numpy` | |

### J.1 Recommended deviations and additions (with reasons)

| Recommendation | Reason |
|---|---|
| Add **Pillow** | Required to display OpenCV frames in Tkinter. |
| Add **PyYAML** | Keeps thresholds out of code (NFR-11). |
| Add **push-to-talk** as default STT trigger | Continuous listening produces false triggers and picks up the app's own speech. Cheap to implement and much more reliable in a demo. |
| Add optional **Vosk** as offline STT fallback | `recognize_google` needs internet; a college demo room's Wi-Fi is unreliable. This is optional and does not replace SpeechRecognition (Vosk plugs into the same wrapper approach). |
| Pin exact versions in `requirements.txt` | AI packages break across versions; reproducibility matters for a demo. |
| Use a dedicated TTS worker thread that owns the engine | `pyttsx3` is known to hang or throw "run loop already started" when called from multiple threads. |
| Use `numpy<2` if the chosen torch/easyocr versions require it | Known compatibility issues; the agent must verify with a clean-venv install test in Phase 0. |

None of these replace the baseline technologies; they support them.

### J.2 Dependency installation notes (for setup docs)

- Create a virtual environment; install `torch` CPU wheel first if disk space is a concern.
- `PyAudio` on Windows: use `pip install pyaudio` (or `pipwin install pyaudio` if wheel is missing); on Linux install `portaudio19-dev`; on macOS `brew install portaudio`.
- Linux TTS needs `espeak`/`espeak-ng` installed.

---

## K. INTERFACES / INTERNAL APIs

All interfaces are Python `typing.Protocol` or `abc.ABC` classes in `eyesite/core/interfaces.py`. Concrete classes implement them; tests use fakes. (Signatures only. Implementation is out of scope for this document.)

### K.1 ICamera

| Method | Signature | Description |
|---|---|---|
| `start` | `() -> None` | Open camera, start capture thread. Raises `CameraError` if it cannot open. |
| `stop` | `() -> None` | Stop thread and release device. |
| `get_latest_frame` | `() -> FramePacket \| None` | Latest frame copy or `None` if none yet. |
| `is_running` | `() -> bool` | |
| `get_fps` | `() -> float` | Measured capture FPS. |

### K.2 IDetector

| Method | Signature | Description |
|---|---|---|
| `load` | `() -> None` | Load model and warm up. Raises `ModelLoadError`. |
| `start` / `stop` | `() -> None` | Start/stop inference thread reading from an injected `ICamera`. |
| `get_latest_result` | `() -> DetectionResult \| None` | Newest result. |
| `detect_frame` | `(frame: np.ndarray) -> list[Detection]` | Synchronous single-frame detect (used in tests and OCR-free flows). |
| `annotate` | `(frame, detections) -> np.ndarray` | Returns a copy with boxes and labels drawn. |

### K.3 INavigation (façade over the three navigation classes)

| Method | Signature | Description |
|---|---|---|
| `analyze` | `(result: DetectionResult) -> list[SpatialObject]` | Zone and proximity. |
| `describe_scene` | `(objs: list[SpatialObject]) -> str` | Natural sentence. |
| `describe_ahead` | `(objs) -> str` | CENTER-zone summary. |
| `select_alerts` | `(objs, now: float) -> list[Alert]` | Policy-filtered alerts with text and priority. |
| `reset_cooldowns` | `() -> None` | Called when guidance is toggled. |

### K.4 IOcrReader

| Method | Signature | Description |
|---|---|---|
| `preload` | `() -> None` | Load reader (background). |
| `is_ready` / `is_busy` | `() -> bool` | |
| `read_async` | `(frame: np.ndarray, on_done: Callable[[OCRResult], None]) -> bool` | Returns `False` if busy or not ready. |
| `read_sync` | `(frame: np.ndarray) -> OCRResult` | For tests. |

### K.5 ISpeaker

| Method | Signature | Description |
|---|---|---|
| `start` / `stop` | `() -> None` | Manage worker thread. |
| `speak` | `(text: str, priority: Priority = Priority.RESPONSE, interrupt: bool = False) -> None` | Enqueue speech. |
| `stop_speaking` | `() -> None` | Interrupt current utterance and clear INFO queue. |
| `repeat_last` | `() -> None` | Re-speak last RESPONSE message. |
| `set_rate` / `set_volume` | `(value) -> None` | |
| `is_speaking` | `() -> bool` | |
| `on_speaking_changed` | `Callable[[bool], None]` (settable) | Emits state changes. |

### K.6 IListener

| Method | Signature | Description |
|---|---|---|
| `start` / `stop` | `() -> None` | |
| `calibrate` | `() -> None` | Ambient noise. |
| `listen_once_async` | `(on_result: Callable[[ListenResult], None]) -> bool` | Begin push-to-talk capture. |
| `is_available` | `() -> bool` | False if no mic. |

### K.7 IAppController (used by UI)

| Method | Description |
|---|---|
| `on_action(action: UserAction)` | Buttons/hotkeys → same path as voice intents. |
| `get_status() -> AppStatus` | Snapshot for the status bar. |
| `events: queue.Queue[UIEvent]` | UI polls this. |
| `get_display_frame() -> np.ndarray \| None` | Latest annotated frame for the video panel. |

---

## L. DATA STRUCTURES

Defined as `@dataclass` (frozen where noted) and `Enum` in `eyesite/core/models.py`.

### L.1 Enums

```
Zone:        LEFT, CENTER, RIGHT
Proximity:   FAR, NEAR, VERY_CLOSE
Priority:    CRITICAL=0, RESPONSE=1, INFO=2        # lower number = higher priority
AppState:    STARTING, IDLE, GUIDANCE, BUSY_OCR, ERROR_DEGRADED, SHUTTING_DOWN
Intent:      DESCRIBE, AHEAD, READ_TEXT, GUIDANCE_ON, GUIDANCE_OFF, REPEAT,
             STOP_SPEECH, HELP, VOLUME_UP, VOLUME_DOWN, EXIT, UNKNOWN
InputSource: VOICE, KEYBOARD, BUTTON
ErrorCode:   CAMERA_UNAVAILABLE, MODEL_LOAD_FAILED, OCR_NOT_READY, OCR_FAILED,
             MIC_UNAVAILABLE, STT_NETWORK_ERROR, TTS_FAILED, CONFIG_INVALID, UNKNOWN
```

### L.2 Records

| Structure | Fields |
|---|---|
| `FramePacket` | `frame: np.ndarray (BGR)`, `timestamp: float`, `frame_id: int`, `width: int`, `height: int` |
| `BBox` (frozen) | `x1, y1, x2, y2: int` with properties `width`, `height`, `area`, `center_x`, `center_y` |
| `Detection` | `label: str`, `class_id: int`, `confidence: float`, `bbox: BBox` |
| `DetectionResult` | `frame_id: int`, `timestamp: float`, `frame_width: int`, `frame_height: int`, `detections: list[Detection]`, `inference_ms: float` |
| `SpatialObject` | `detection: Detection`, `zone: Zone`, `proximity: Proximity`, `center_x_ratio: float`, `area_ratio: float` |
| `Alert` | `text: str`, `priority: Priority`, `key: tuple[str, Zone]`, `proximity: Proximity` |
| `OCRRegion` | `text: str`, `confidence: float`, `bbox: BBox` |
| `OCRResult` | `full_text: str`, `spoken_text: str`, `regions: list[OCRRegion]`, `avg_confidence: float`, `duration_ms: float`, `frame_id: int`, `error: ErrorCode \| None` |
| `SpeechItem` | `text: str`, `priority: Priority`, `created_at: float`, `interrupt: bool` |
| `ListenResult` | `transcript: str \| None`, `error: ErrorCode \| None`, `duration_ms: float` |
| `Command` | `intent: Intent`, `raw_text: str`, `match_score: float`, `source: InputSource` |
| `AppStatus` | `state: AppState`, `camera_ok: bool`, `detector_ok: bool`, `ocr_ready: bool`, `mic_ok: bool`, `tts_ok: bool`, `guidance_on: bool`, `fps: float`, `inference_ms: float`, `last_error: ErrorCode \| None` |
| `UIEvent` | `type: UIEventType`, `payload: dict` where `UIEventType ∈ {SPOKEN_MESSAGE, STATUS_CHANGED, OCR_TEXT, ERROR, LISTENING_STARTED, LISTENING_STOPPED, SHOW_HELP}` |

### L.3 Custom exceptions

`EyeSiteError` (base) → `CameraError`, `ModelLoadError`, `OcrError`, `SpeechInputError`, `SpeechOutputError`, `ConfigError`.

---

## M. CONFIGURATION, VOCABULARY AND MESSAGE CATALOGUE

### M.1 `config.yaml` (default values, binding names)

```yaml
app:
  first_run_disclaimer: true
  log_level: INFO
camera:
  source: 0            # int index or path to video file
  width: 640
  height: 480
  fps: 30
  mirror: false
detection:
  model_path: assets/yolov8n.pt
  confidence: 0.45
  iou: 0.5
  imgsz: 640
  max_rate_hz: 5
  device: auto
  smoothing_window: 3
  smoothing_min_hits: 2
  stale_after_s: 1.5
navigation:
  left_max: 0.33
  right_min: 0.67
  near_area_ratio: 0.12
  very_close_area_ratio: 0.35
  cooldown_s: 6.0
  global_min_interval_s: 2.5
  max_items_spoken: 4
  relevant_classes: [person, bicycle, car, motorcycle, bus, truck, chair, couch,
                     bed, dining table, potted plant, bench, tv, laptop, dog, cat,
                     suitcase, backpack, toilet, refrigerator, door]   # only labels YOLO supports
ocr:
  languages: [en]
  preload: true
  min_confidence: 0.40
  max_spoken_chars: 400
  gpu: false
voice_output:
  rate: 170
  volume: 0.9
  info_max_age_s: 3.0
voice_input:
  mode: push_to_talk       # or continuous
  timeout_s: 5
  phrase_time_limit_s: 6
  engine: google           # google | vosk
  ambient_calibration_s: 1
ui:
  theme: high_contrast
  font_size: 16
  show_confidence: true
```

> Note: "door" is not a COCO class; the agent must validate `relevant_classes` against the model's class names at startup and log/skip unknown entries.

### M.2 Intent vocabulary (seed phrases for the Command Parser)

| Intent | Phrases (case-insensitive, substring or fuzzy match) |
|---|---|
| DESCRIBE | describe, what do you see, what is around me, look around, describe surroundings |
| AHEAD | what is ahead, what is in front, anything ahead, in front of me |
| READ_TEXT | read text, read this, read, what does it say, read the sign |
| GUIDANCE_ON | start guidance, start guide, guide me, navigate, start navigation, turn on guidance |
| GUIDANCE_OFF | stop guidance, stop guide, stop navigation, turn off guidance |
| REPEAT | repeat, say again, say that again, what did you say |
| STOP_SPEECH | stop, quiet, silence, be quiet, shut up → treated as STOP_SPEECH (not EXIT) |
| HELP | help, commands, what can you do, instructions |
| VOLUME_UP | louder, volume up, speak louder |
| VOLUME_DOWN | quieter, softer, volume down, speak softer |
| EXIT | exit, quit, close app, close eyesite, goodbye |

**Disambiguation rules:** "stop" alone → `STOP_SPEECH`. "stop guidance" → `GUIDANCE_OFF` (longer phrase wins). `EXIT` from voice requires the phrase to contain "exit", "quit" or "close"; the app asks "Say yes to confirm exit" (confirmation via next push-to-talk) or, if keyboard, shows a confirmation dialog.

### M.3 Message catalogue (all user-facing strings in one `messages.py` for easy editing)

| Key | Text |
|---|---|
| `STARTING` | "EyeSite is starting." |
| `READY` | "EyeSite is ready. Say help to hear commands." |
| `DISCLAIMER` | "EyeSite is an assistive prototype. It does not replace your cane, guide dog, or a person helping you." |
| `GUIDANCE_ON` | "Guidance on." |
| `GUIDANCE_OFF` | "Guidance off." |
| `OCR_START` | "Reading text." |
| `OCR_BUSY` | "Still reading. Please wait." |
| `OCR_LOADING` | "Text reader is still loading. Please wait." |
| `OCR_EMPTY` | "I could not find any readable text. Try moving closer or improving the light." |
| `NOTHING_AHEAD` | "Nothing detected ahead." |
| `NO_OBJECTS` | "I do not see any known objects." |
| `STALE` | "I cannot see clearly right now." |
| `UNKNOWN_CMD` | "Sorry, I did not understand. Say help for commands." |
| `MIC_MISSING` | "I cannot hear you because no microphone was found. Please use the keyboard." |
| `STT_OFFLINE` | "Voice commands need internet right now. Please use the keyboard." |
| `CAMERA_MISSING` | "I cannot access the camera. Please check that it is connected." |
| `CAMERA_LOST` | "The camera stopped working. Trying to reconnect." |
| `SHUTDOWN` | "Goodbye." |

---

## N. UI SPECIFICATION

### N.1 Design principles

1. **Audio first, screen second.** The UI exists mainly for helpers, evaluators and low-vision users.
2. High contrast (black background, white/yellow text, blue-ish focus rings), large fonts, large clickable areas.
3. Everything reachable by keyboard with a visible focus indicator (Tab order defined).
4. The UI is never the only feedback channel.

### N.2 Main window layout (single window, default 1100×700, resizable, min 900×600)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ EyeSite: The camera sees, and the voice tells.              [Help] [Quit]    │  Header
├───────────────────────────────────────────────┬──────────────────────────────┤
│                                               │  STATUS                      │
│                                               │  State:  IDLE                │
│                                               │  Camera: OK   Detector: OK   │
│          LIVE VIDEO (annotated)               │  OCR: Ready   Mic: OK        │
│          with boxes, labels, zone lines       │  Guidance: OFF               │
│          (L | C | R guide lines)              │  FPS 24 · Inference 142 ms   │
│                                               ├──────────────────────────────┤
│                                               │  LAST DETECTIONS             │
│                                               │  person · center · close     │
│                                               │  chair · left · far          │
├───────────────────────────────────────────────┼──────────────────────────────┤
│ [ Describe (D) ] [ Ahead (A) ] [ Read Text (R) ]                             │
│ [ Guidance ON/OFF (G) ] [ Listen (T) ] [ Repeat (P) ] [ Stop Speech (S) ]    │  Controls
├──────────────────────────────────────────────────────────────────────────────┤
│ SPOKEN MESSAGES LOG (timestamped, scrollable)  │  OCR TEXT (scrollable)      │
├──────────────────────────────────────────────────────────────────────────────┤
│ Status bar: ● Listening… / Speaking… / Idle    Volume [────●───]             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### N.3 UI component requirements

| ID | Component | Requirement |
|---|---|---|
| FR-UI-01 | Video panel | Renders annotated frames at ≥ 10 UI refreshes/s via `root.after(33-66ms)`; scales preserving aspect ratio; overlays two vertical zone lines at 33%/67% (toggleable). |
| FR-UI-02 | Status panel | Shows `AppStatus` fields with colour **and** text (never colour alone): OK / Loading / Error. |
| FR-UI-03 | Detections list | Latest 8 confirmed detections with label, zone, proximity, and (optionally) confidence. |
| FR-UI-04 | Control buttons | One per action in Section E.3, with hotkey in label, font ≥ 16 pt, height ≥ 48 px, tooltips. |
| FR-UI-05 | Listening indicator | Prominent "● LISTENING" badge while STT is active; changes to "SPEAKING" while TTS runs. |
| FR-UI-06 | Message log | Appends each spoken message with time; capped at 200 lines. |
| FR-UI-07 | OCR panel | Shows last OCR text; "Copy" button; read-only. |
| FR-UI-08 | Help dialog | Lists all commands, hotkeys, disclaimer, and privacy note (audio sent to Google when online STT is used). |
| FR-UI-09 | Error banner | Non-blocking red banner with plain-language message and suggested fix; also spoken. |
| FR-UI-10 | Keyboard | Hotkeys per E.3; Tab order: Describe → Ahead → Read → Guidance → Listen → Repeat → Stop → Volume → Help → Quit. |
| FR-UI-11 | Theme | `high_contrast` default; `light` optional. |
| FR-UI-12 | Thread safety | UI reads only from the controller's event queue and `get_display_frame()`; no direct calls into worker threads. |
| FR-UI-13 | Window close | Same shutdown path as Quit; confirm only if OCR job running. |

---

## O. ERROR HANDLING MATRIX

| Scenario | Detection | System behaviour | User feedback (voice + UI) | Recovery |
|---|---|---|---|---|
| Camera not found at startup | `VideoCapture.isOpened() == False` | State `ERROR_DEGRADED`; detection/OCR disabled | `CAMERA_MISSING` | Retry 3× at start; user can press `F5` / "Retry camera" button |
| Camera disconnects mid-run | 30 consecutive read failures | Attempt reconnect 3×, 1 s apart | `CAMERA_LOST`; if failed: `CAMERA_MISSING` | Auto reconnect; else manual retry |
| YOLO model file missing/corrupt | `ModelLoadError` | Try download once if internet; else fatal for detection features | "Object detection is unavailable." | Log exact path; documented fix |
| Inference exception | try/except around predict | Skip the frame, count errors; after 10 consecutive failures disable detection and announce | "Object detection stopped." | Manual restart button |
| No detections | Empty list | Normal path | `NO_OBJECTS` / `NOTHING_AHEAD` | n/a |
| Stale detection result | `age > stale_after_s` | Do not describe old data | `STALE` | Auto when new result arrives |
| OCR not ready | `is_ready() == False` | Reject job | `OCR_LOADING` | Auto when ready |
| OCR busy | `is_busy()` | Reject new job | `OCR_BUSY` | n/a |
| OCR exception | try/except in worker | Return `OCRResult(error=OCR_FAILED)` | "Sorry, I could not read the text." | Retry allowed |
| OCR no text | Empty filtered list | Normal | `OCR_EMPTY` | n/a |
| No microphone | `MIC_UNAVAILABLE` at start | Disable voice input; keyboard/buttons still work | `MIC_MISSING` | "Re-scan microphone" button |
| STT timeout (silence) | `WaitTimeoutError` | End listening quietly | Short "I did not hear anything." | User retries |
| STT unintelligible | `UnknownValueError` | Treat as no result | `UNKNOWN_CMD` | User retries |
| STT network failure | `RequestError` | Switch to offline engine if configured; else disable online STT | `STT_OFFLINE` | Auto retry after 60 s |
| TTS engine failure | Exception in speaker thread | Re-create engine once; if it fails again, fall back to on-screen text only and show banner | Banner: "Speech unavailable" | Restart button |
| Speech queue overflow | Queue size > 20 | Drop oldest `INFO` items | none | n/a |
| Config invalid / missing | Validation error | Use defaults, log warnings | Banner only | Fix file |
| Unhandled exception in any worker thread | Thread wrapper with try/except + logging | Log stack trace, mark module unhealthy, continue app | "A problem occurred. Some features may be unavailable." | Restart button |
| Low light / blurry frame | Mean brightness < 40 or Laplacian variance low (SHOULD) | Add warning to descriptions/OCR results | "It is very dark. Results may be poor." | User improves lighting |
| Rapid repeated commands | Debounce 500 ms per intent | Ignore duplicates | none | n/a |

---

## P. TESTING STRATEGY

### P.1 Test levels

| Level | Scope | Tooling |
|---|---|---|
| Unit | Pure logic and each module with fakes | pytest, pytest-mock |
| Integration | Module pairs and full pipeline with fake camera (video file) | pytest |
| System / manual | Real webcam, mic, speakers | Test checklist |
| Non-functional | Performance, 15-min soak, resource use | Manual scripts + logs |

### P.2 Required unit tests (minimum)

| Module | Tests |
|---|---|
| Navigation: zone | Boundary values 0.0, 0.32, 0.33, 0.50, 0.67, 0.68, 1.0 → correct zone |
| Navigation: proximity | Area ratios around 0.11/0.12/0.34/0.35 → correct label |
| Navigation: describer | 0/1/2/5 objects, duplicates grouped, ordering CENTER→LEFT→RIGHT, max 4 items, pluralisation |
| Navigation: alert policy | Cooldown blocks repeat; alert re-fires after cooldown; proximity worsening bypasses cooldown; non-relevant classes ignored; global interval respected |
| Detection | Confidence filter; BBox properties; smoothing (2/3 hits); annotate does not mutate input |
| OCR | Sorting into reading order; confidence filtering; empty result; truncation at max chars (uses mocked EasyOCR output) |
| Command parser | Every seed phrase → correct intent; punctuation/case; fuzzy near-misses ("desribe"); "stop" vs "stop guidance"; unknown text → UNKNOWN |
| Speaker | Priority ordering; stale INFO dropped; duplicate suppression; repeat_last (with fake engine) |
| Listener | Error mapping for timeout/unknown/request errors (mock `speech_recognition`) |
| Config | Defaults on missing keys; invalid values raise `ConfigError` or fall back |
| Controller | State transitions; intent routing calls right module (all mocks); OCR rejected while busy |

### P.3 Integration tests

1. **Video → detection → navigation → text:** feed a recorded test video and assert a description containing expected labels.
2. **Command → speech:** simulate transcript "describe" with a fake detector and fake speaker; assert the spoken text.
3. **Guidance loop:** feed synthetic detection sequence; assert alerts are throttled as specified.
4. **Shutdown:** start all real modules with fakes for hardware; call `stop()`; assert all threads end within 5 s.
5. **Degradation:** simulate missing mic/camera; assert app still starts with the right status and message.

### P.4 Manual acceptance test checklist (for demo readiness)

| # | Test | Pass criteria |
|---|---|---|
| 1 | Launch app | Window opens; ready message spoken ≤ 20 s |
| 2 | Person centered ~1 m away, say "what is ahead" | "Ahead of you is a person…" |
| 3 | Chair left, laptop right, "describe" | Correct sides in the sentence |
| 4 | Hold printed page, "read text" | Main words spoken, text shown in panel |
| 5 | Blank wall, "read text" | `OCR_EMPTY` message |
| 6 | Guidance on, walk toward a chair | Alerts spaced by cooldown; "very close" escalation |
| 7 | Say "stop" mid-sentence | Speech interrupted ≤ 500 ms |
| 8 | Unplug mic / mute network | Correct degradation message; keyboard still works |
| 9 | Cover camera | Camera/dark warning, no crash |
| 10 | 15-minute soak with guidance on | No crash, memory stable (± 300 MB) |
| 11 | Use app with monitor turned off | All functions still usable by hotkeys and voice |

### P.5 Quality gates

- `pytest` all green; coverage ≥ 70% overall and ≥ 90% on `navigation/` and `core/command_parser.py`.
- Lint clean (`ruff`).
- No TODOs left in MVP code paths.

---

## Q. SAFETY, ETHICS, PRIVACY AND LIMITATIONS

- **Safety disclaimer** shown and spoken on first launch; included in README and Help.
- **Known limitations (must be documented and spoken in Help where relevant):** single camera gives no true depth; proximity is approximate; only 80 COCO classes; misses small, transparent or unusual objects; reflective/low-light/motion-blur conditions degrade accuracy; OCR struggles with curved, small, stylised or handwritten text; STT may misrecognise accents or noisy input; latency of 0.2 to several seconds exists.
- **Wording discipline:** never say "safe", "clear path" or "no obstacle". Use "Nothing detected ahead" (statement about the software, not the world).
- **Privacy:** no image or audio persistence; no analytics; online STT sends audio to Google (disclosed); logs store text only.
- **Bias/fairness note:** detection accuracy varies by object appearance and lighting; the project report should mention this.

---

## R. SCOPE

### R.1 IN the MVP

Webcam capture · YOLOv8n detection · left/center/right zoning · coarse proximity · scene description · "what is ahead" · rate-limited obstacle alerts (guidance mode) · on-demand OCR · offline TTS with priorities · push-to-talk voice commands with keyboard/button equivalents · Tkinter high-contrast UI · config file · logging · error handling · unit and integration tests · documentation and demo script.

### R.2 OUT of the MVP (intentionally)

Facial recognition · GPS / turn-by-turn navigation · medical or emergency features · cloud AI / LLM scene captioning · mobile app · smart glasses / wearables · robotics · metric depth estimation or stereo/LiDAR · multi-language · custom-trained models · currency/colour recognition · user profiles · installers/packaging.

---

## S. FUTURE SCOPE (clearly not part of MVP)

| Priority | Feature | Notes |
|---|---|---|
| F1 | Monocular depth estimation (e.g. MiDaS-small) for better proximity | Replaces bbox-area heuristic |
| F2 | Offline STT as default (Vosk/Whisper-tiny) | Removes internet dependency |
| F3 | Continuous wake-word listening ("Hey EyeSite") | Needs noise robustness |
| F4 | Multi-language OCR and TTS (e.g. Hindi + English) | EasyOCR supports Hindi; needs Hindi TTS voice |
| F5 | Richer scene captioning with a small vision-language model | Optional, offline if feasible |
| F6 | Currency and colour identification | Custom model / rules |
| F7 | Object tracking (IDs across frames) for approach/recede detection | e.g. ByteTrack |
| F8 | Spatial audio / stereo beeps for direction | Non-speech cues |
| F9 | Wearable/mobile port (Android, Raspberry Pi + camera) | Separate project |
| F10 | User-trainable "known objects" | Custom YOLO fine-tune |
| F11 | Packaged installer (PyInstaller) | Distribution |

---

## T. DEVELOPMENT PHASES (INCREMENTAL BUILD PLAN)

### T.1 Rules for the coding agent

1. Build **one phase at a time**; after each phase run the phase's tests and demonstrate the acceptance criteria before continuing.
2. Never implement features listed in R.2.
3. Follow interfaces in Section K and data structures in Section L exactly; if a change is needed, update this PRD's interface table and note it in `docs/architecture.md`.
4. Write tests **with** each module, not afterwards.
5. Keep each module usable stand-alone through a small `if __name__ == "__main__":` demo or `scripts/` runner.
6. No hard-coded thresholds; read from config.
7. Commit after each completed task with a meaningful message.

### T.2 Phases

| Phase | Name | Deliverables | Acceptance criteria |
|---|---|---|---|
| **0** | Setup | Repo, venv, `requirements.txt` (pinned), folder structure, logging, config loader, `models.py`, `interfaces.py`, message catalogue, CI-style local script (`pytest` + `ruff`) | Clean-venv install works; `pytest` runs (even with placeholder tests); `python main.py` prints version and exits |
| **1** | Camera | `CameraStream`, fake camera (video file), demo script showing feed with FPS | Live feed at ≥ 15 FPS; unplug test triggers reconnect logic; unit tests pass |
| **2** | Detection | `YoloDetector`, annotate, smoothing, demo script | Boxes drawn on live feed; ≥ 4 inferences/s on CPU; tests pass |
| **3** | Navigation | Spatial analyzer, describer, alert policy (pure logic) | All navigation unit tests pass; demo prints descriptions for a recorded video |
| **4** | Voice output | `PyttsxSpeaker` with queue, priorities, interruption | Priority and interruption tests pass with fake engine; manual test with real voice |
| **5** | Core v1 (no UI) | `AppController`, state machine, command parser, keyboard-driven console loop | Typing "describe" / "what is ahead" speaks correct sentences from live camera |
| **6** | OCR | `EasyOcrReader`, preload, async job, integration into controller | "read text" works on a printed page; busy/loading/empty cases handled |
| **7** | Voice input | `SpeechListener` push-to-talk, calibration, error mapping, self-hearing guard | Spoken commands trigger the same handlers as typed ones; mic-missing degradation works |
| **8** | Guidance mode | Continuous alerts through controller tick with throttling | Manual test #6 passes; unit + integration guidance tests pass |
| **9** | Tkinter UI | Full layout per Section N, hotkeys, theme, event-queue integration | Every action available by button, hotkey, and voice; no UI freeze during OCR/speech |
| **10** | Hardening | Error matrix fully implemented, soak test, performance tuning, low-light warning | Manual checklist P.4 fully passes |
| **11** | Documentation and demo | README, setup guide, user guide, architecture doc, test report, demo script, screenshots | A new person can install and run using README alone |

### T.3 Suggested prompts pattern for Antigravity (per phase)

> "Read `docs/PRD.md`. Implement **Phase N** only. Follow interfaces in Section K and models in Section L. Create the listed files, write the unit tests described in Section P.2 for this phase, run `pytest` and `ruff`, and report results. Do not implement anything from later phases."

### T.4 Git workflow

- `main` (stable, demo-ready), `develop` (integration), feature branches `feature/phase-N-name`.
- Conventional commit messages (`feat:`, `fix:`, `test:`, `docs:`).
- Tag `v0.N` after each phase; tag `v1.0` for final submission.
- Suggested team split if applicable: Detection · OCR · Voice · Navigation · Core/integration · UI/testing/docs (matches the project's functional areas).

---

## U. RISKS AND MITIGATIONS

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| EasyOCR/PyTorch install issues or huge size | Medium | High | Pin versions; test in clean venv in Phase 0; pre-download models; document CPU-only torch install |
| pyttsx3 threading bugs | High | Medium | Single owner thread (FR-TTS-02); fallback to per-utterance engine |
| PyAudio install failure on Windows | Medium | High | Documented wheel install; keyboard fallback keeps demo alive |
| Internet unavailable during demo | Medium | Medium | Offline Vosk fallback; keyboard/buttons; recorded backup demo video |
| Low FPS on weak laptop | Medium | Medium | Lower `imgsz` to 480/320; reduce `max_rate_hz`; YOLOv8n already smallest |
| False/flickering detections | High | Medium | Confidence threshold, temporal smoothing, class filtering |
| Speech overload in guidance mode | High | High | Cooldowns, global interval, top-4 rule, stale-drop rule |
| Overclaiming safety | Medium | High | Disclaimer, wording discipline (Section Q) |
| Scope creep | High | High | Section R.2 is binding; new ideas go to Section S |

---

## V. DEMO PLAN (FOR EVALUATION)

1. Introduce concept and disclaimer (30 s).
2. Launch app; show status panel and live detections (1 min).
3. "Describe" with 2 to 3 objects placed left/center/right (1 min).
4. "What is ahead" with and without an object in front (30 s).
5. "Read text" with a printed sheet, then blank paper (1 min).
6. Guidance mode: walk an object toward the camera to show throttled alerts and escalation (1 min).
7. Show interruption ("stop") and repeat (30 s).
8. Show graceful degradation (unplug mic or say gibberish) (30 s).
9. Show tests passing and architecture diagram (1 min).
10. State limitations and future scope honestly (1 min).

Prepare a **backup**: pre-recorded video file as `camera.source`, and a recorded screen capture of a successful run.

---

## W. GLOSSARY

| Term | Meaning |
|---|---|
| COCO | Dataset defining the 80 object classes YOLOv8n detects |
| OCR | Optical Character Recognition: converting image text to machine text |
| TTS / STT | Text-to-speech / speech-to-text |
| Zone | Horizontal third of the frame: LEFT, CENTER, RIGHT |
| Proximity | Coarse closeness label from bounding-box size (not real distance) |
| Push-to-talk | Voice input that listens only while/after the user triggers it |
| Guidance mode | Continuous, rate-limited obstacle alerts |
| Debounce | Ignoring repeats of an action within a short window |

---

## X. OPEN DECISIONS FOR THE TEAM (resolve before or during Phase 0)

1. Confirm target OS for the demo laptop (Windows assumed).
2. Confirm whether an offline STT fallback (Vosk) will be included in MVP or left as F2.
3. Confirm whether speech should be English-only (assumed yes).
4. Confirm the final list of `relevant_classes` after validating against the YOLO model's class names.
5. Confirm team member assignments to modules.

---

*End of PRD v1.0*
