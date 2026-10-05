# EyeSite

EyeSite is an AI-powered assistive desktop application that uses computer vision, OCR, and voice interaction to help visually impaired users understand nearby objects, read visible text, and learn the approximate direction of obstacles through spoken feedback.

*Core principle: "The camera sees, and the voice tells."*

> **Disclaimer:** EyeSite is an assistive technology prototype. It is **not** a replacement for a white cane, guide dog, or human mobility assistance.

---

## 1. Prerequisites

- **Python:** Python 3.10 or 3.11 (64-bit recommended)
- **OS:** Windows 10/11, Linux, or macOS
- **Hardware:** Webcam, microphone, and speakers

---

## 2. Quick Setup (Windows)

Open PowerShell in the project directory:

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. (Recommended) Install CPU-only PyTorch first to save disk space and avoid CUDA overhead:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 3. Install remaining dependencies:
pip install -r requirements.txt

# 4. (Optional) Audio input with PyAudio:
# If 'pip install pyaudio' fails on Windows, install using pipwin:
pip install pipwin
pipwin install pyaudio
```

### Quick Setup (macOS / Linux)

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Linux system packages (for PortAudio and TTS):
# sudo apt update && sudo apt install -y portaudio19-dev espeak

# 3. Install PyTorch (CPU) and dependencies:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pip install pyaudio
```

---

## 3. Running Checks and Tests

Run the test suite and code quality checks:

### Windows (PowerShell):
```powershell
.\scripts\check.ps1
```

### Linux / macOS:
```bash
bash scripts/check.sh
```

Or run tools directly:
```bash
pytest
ruff check .
```

---

## 4. Running Demos and Applications

```bash
# Run the Phase 0 core verification demo:
python scripts/demo_core.py

# Run main application (Phase 0 prints version and exits):
python main.py
```

---

## 5. Project Structure

```
eyesite/
├── main.py                     # Entry point
├── config.yaml                 # Tunable system configuration
├── requirements.txt            # Pinned dependencies
├── README.md                   # Setup guide and documentation
├── docs/
│   ├── PRD.md                  # Product Requirements Document
│   └── notes/
│       └── core.md             # Beginner guide for Phase 0 core
├── eyesite/
│   ├── core/                   # Shared contracts, models, interfaces, config
│   ├── camera/                 # Camera capture module (Phase 1)
│   ├── detection/              # YOLO object detection (Phase 2)
│   ├── navigation/             # Spatial reasoning and alerts (Phase 3)
│   ├── ocr/                    # EasyOCR text reader (Phase 6)
│   ├── voice/                  # TTS speaker and STT listener (Phase 4, 7)
│   └── ui/                     # Tkinter user interface (Phase 9)
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures and fakes
├── scripts/
│   ├── check.ps1 / check.sh    # Quality check scripts
│   └── demo_core.py            # Phase 0 verification demo
└── logs/                       # Rotating application logs
```
