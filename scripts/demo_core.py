"""Demo script to verify Phase 0 core contracts, configuration, and models.

Usage:
    python scripts/demo_core.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when running standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from eyesite.core.config import load_config
from eyesite.core.events import (
    create_spoken_message_event,
    create_status_changed_event,
)
from eyesite.core.logging_setup import setup_logging
from eyesite.core.messages import DISCLAIMER, READY, STARTING
from eyesite.core.models import (
    AppState,
    AppStatus,
    BBox,
    Detection,
    Priority,
    Proximity,
    SpatialObject,
    Zone,
)


def main() -> None:
    """Run interactive demonstration of Phase 0 core components."""
    # 1. Initialize logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger("demo_core")
    logger.info("Initializing Phase 0 demo...")

    print("=" * 60)
    print(" EyeSite - Phase 0 Core Verification Demo")
    print("=" * 60)

    # 2. Test Configuration Loading
    print("\n[1] Loading configuration from config.yaml...")
    cfg = load_config()
    print(f"    Camera resolution: {cfg.camera.width}x{cfg.camera.height} @ {cfg.camera.fps} FPS")
    print(f"    YOLO model path:   {cfg.detection.model_path}")
    print(f"    Confidence thresh: {cfg.detection.confidence}")
    print(f"    Left zone bound:   < {cfg.navigation.left_max}")
    print(f"    Right zone bound:  > {cfg.navigation.right_min}")
    print(f"    Relevant classes:  {len(cfg.navigation.relevant_classes)} classes configured")

    # 3. Test BBox Calculations
    print("\n[2] Testing BBox calculations...")
    bbox = BBox(x1=100, y1=80, x2=340, y2=400)
    print(f"    BBox coordinates: ({bbox.x1}, {bbox.y1}) to ({bbox.x2}, {bbox.y2})")
    print(f"    Width:    {bbox.width} px")
    print(f"    Height:   {bbox.height} px")
    print(f"    Area:     {bbox.area} px^2")
    print(f"    Center:   ({bbox.center_x}, {bbox.center_y})")

    # 4. Test SpatialObject Construction
    print("\n[3] Creating sample Detection and SpatialObject...")
    detection = Detection(label="person", class_id=0, confidence=0.88, bbox=bbox)
    frame_w, frame_h = cfg.camera.width, cfg.camera.height
    center_x_ratio = bbox.center_x / frame_w
    area_ratio = bbox.area / (frame_w * frame_h)

    zone = Zone.CENTER if cfg.navigation.left_max <= center_x_ratio <= cfg.navigation.right_min else Zone.LEFT
    proximity = Proximity.NEAR if area_ratio >= cfg.navigation.near_area_ratio else Proximity.FAR

    spatial_obj = SpatialObject(
        detection=detection,
        zone=zone,
        proximity=proximity,
        center_x_ratio=center_x_ratio,
        area_ratio=area_ratio,
    )
    print(f"    Object: {spatial_obj.detection.label} (confidence: {spatial_obj.detection.confidence:.2f})")
    print(f"    Zone: {spatial_obj.zone.value} (ratio: {spatial_obj.center_x_ratio:.2f})")
    print(f"    Proximity: {spatial_obj.proximity.value} (area ratio: {spatial_obj.area_ratio:.3f})")

    # 5. Test UI Events
    print("\n[4] Creating sample UI Events...")
    msg_event = create_spoken_message_event("Person ahead, close.", Priority.RESPONSE)
    print(f"    Event: {msg_event.type.value} -> payload: {msg_event.payload}")

    status = AppStatus(
        state=AppState.IDLE,
        camera_ok=True,
        detector_ok=True,
        ocr_ready=True,
        mic_ok=True,
        tts_ok=True,
        guidance_on=False,
        fps=30.0,
        inference_ms=125.0,
    )
    status_event = create_status_changed_event(status)
    print(f"    Event: {status_event.type.value} -> state: {status_event.payload['status'].state.value}")

    # 6. Test Message Catalogue
    print("\n[5] Message catalogue samples:")
    print(f"    STARTING:   \"{STARTING}\"")
    print(f"    READY:      \"{READY}\"")
    print(f"    DISCLAIMER: \"{DISCLAIMER}\"")

    # 7. Check Dummy Frame
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    print(f"\n[6] NumPy check: created dummy BGR frame shape={dummy_frame.shape}")

    print("\n" + "=" * 60)
    print(" [SUCCESS] Phase 0 core contracts verified!")
    print("=" * 60)


if __name__ == "__main__":
    main()
