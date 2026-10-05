"""Configuration loader and schema validator for EyeSite.

PRD Section M.1 specification.
Loads `config.yaml`, applies sensible defaults for missing keys,
and validates types and numeric ranges.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from eyesite.core.models import ConfigError

logger = logging.getLogger(__name__)

DEFAULT_RELEVANT_CLASSES: list[str] = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "bus",
    "truck",
    "chair",
    "couch",
    "bed",
    "dining table",
    "potted plant",
    "bench",
    "tv",
    "laptop",
    "dog",
    "cat",
    "suitcase",
    "backpack",
    "toilet",
    "refrigerator",
    "door",
]


@dataclass
class AppConfig:
    """Application-level configuration."""

    first_run_disclaimer: bool = True
    log_level: str = "INFO"


@dataclass
class CameraConfig:
    """Camera capture configuration."""

    source: int | str = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    mirror: bool = False


@dataclass
class DetectionConfig:
    """YOLO detection settings."""

    model_path: str = "assets/yolov8n.pt"
    confidence: float = 0.45
    iou: float = 0.5
    imgsz: int = 640
    max_rate_hz: int = 5
    device: str = "auto"
    smoothing_window: int = 3
    smoothing_min_hits: int = 2
    stale_after_s: float = 1.5


@dataclass
class NavigationConfig:
    """Spatial analysis and alert throttling configuration."""

    left_max: float = 0.33
    right_min: float = 0.67
    near_area_ratio: float = 0.12
    very_close_area_ratio: float = 0.35
    cooldown_s: float = 6.0
    global_min_interval_s: float = 2.5
    max_items_spoken: int = 4
    relevant_classes: list[str] = field(
        default_factory=lambda: list(DEFAULT_RELEVANT_CLASSES)
    )


@dataclass
class OcrConfig:
    """Optical character recognition configuration."""

    languages: list[str] = field(default_factory=lambda: ["en"])
    preload: bool = True
    min_confidence: float = 0.40
    max_spoken_chars: int = 400
    gpu: bool = False


@dataclass
class VoiceOutputConfig:
    """Text-to-speech configuration."""

    rate: int = 170
    volume: float = 0.9
    info_max_age_s: float = 3.0


@dataclass
class VoiceInputConfig:
    """Speech-to-text configuration."""

    mode: str = "push_to_talk"
    timeout_s: int = 5
    phrase_time_limit_s: int = 6
    engine: str = "google"
    ambient_calibration_s: int = 1


@dataclass
class UIConfig:
    """User interface display and accessibility settings."""

    theme: str = "high_contrast"
    font_size: int = 16
    show_confidence: bool = True


@dataclass
class EyeSiteConfig:
    """Complete system configuration root."""

    app: AppConfig = field(default_factory=AppConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    navigation: NavigationConfig = field(default_factory=NavigationConfig)
    ocr: OcrConfig = field(default_factory=OcrConfig)
    voice_output: VoiceOutputConfig = field(default_factory=VoiceOutputConfig)
    voice_input: VoiceInputConfig = field(default_factory=VoiceInputConfig)
    ui: UIConfig = field(default_factory=UIConfig)


def validate_config(cfg: EyeSiteConfig) -> None:
    """Validate configuration ranges and relationships.

    Raises:
        ConfigError: If critical configuration rules are violated.
    """
    # Camera validation
    if cfg.camera.width <= 0 or cfg.camera.height <= 0:
        raise ConfigError(
            f"Invalid camera resolution: {cfg.camera.width}x{cfg.camera.height}"
        )
    if cfg.camera.fps <= 0:
        raise ConfigError(f"Camera FPS must be positive, got {cfg.camera.fps}")

    # Detection validation
    if not (0.0 <= cfg.detection.confidence <= 1.0):
        raise ConfigError(
            f"Detection confidence must be in [0, 1], got {cfg.detection.confidence}"
        )
    if not (0.0 <= cfg.detection.iou <= 1.0):
        raise ConfigError(
            f"Detection IoU must be in [0, 1], got {cfg.detection.iou}"
        )
    if cfg.detection.max_rate_hz <= 0:
        raise ConfigError(
            f"max_rate_hz must be > 0, got {cfg.detection.max_rate_hz}"
        )
    if cfg.detection.stale_after_s <= 0:
        raise ConfigError(
            f"stale_after_s must be > 0, got {cfg.detection.stale_after_s}"
        )

    # Navigation validation
    if not (0.0 < cfg.navigation.left_max < cfg.navigation.right_min < 1.0):
        raise ConfigError(
            f"Navigation zones invalid: left_max ({cfg.navigation.left_max}) "
            f"must be < right_min ({cfg.navigation.right_min}) in range (0, 1)"
        )
    if not (
        0.0
        < cfg.navigation.near_area_ratio
        < cfg.navigation.very_close_area_ratio
        <= 1.0
    ):
        raise ConfigError(
            "Navigation proximity invalid: near_area_ratio "
            f"({cfg.navigation.near_area_ratio}) must be < "
            f"very_close_area_ratio ({cfg.navigation.very_close_area_ratio})"
        )
    if cfg.navigation.cooldown_s < 0:
        raise ConfigError("cooldown_s cannot be negative")
    if cfg.navigation.global_min_interval_s < 0:
        raise ConfigError("global_min_interval_s cannot be negative")

    # Voice output validation
    if not (0.0 <= cfg.voice_output.volume <= 1.0):
        raise ConfigError(
            f"Voice volume must be in [0.0, 1.0], got {cfg.voice_output.volume}"
        )
    if cfg.voice_output.rate <= 0:
        raise ConfigError(
            f"Voice rate must be positive, got {cfg.voice_output.rate}"
        )


def _build_subconfig(cls: type, raw: dict[str, Any] | None) -> Any:
    """Instantiate a dataclass with values from raw dict, falling back to defaults."""
    if not raw or not isinstance(raw, dict):
        return cls()

    kwargs: dict[str, Any] = {}
    valid_fields = cls.__dataclass_fields__  # type: ignore[attr-defined]

    for key, val in raw.items():
        if key in valid_fields:
            kwargs[key] = val
        else:
            logger.warning("Ignoring unrecognized config key in %s: %s", cls.__name__, key)

    return cls(**kwargs)


def load_config(config_path: str | Path | None = None) -> EyeSiteConfig:
    """Load configuration from a YAML file with fallback to defaults.

    Args:
        config_path: Path to config.yaml. Defaults to 'config.yaml' in current directory.

    Returns:
        Validated EyeSiteConfig instance.

    Raises:
        ConfigError: If the YAML is malformed or invalid values are given.
    """
    target = Path(config_path) if config_path else Path("config.yaml")

    if not target.exists():
        logger.warning("Config file '%s' not found; using built-in defaults.", target)
        cfg = EyeSiteConfig()
        validate_config(cfg)
        return cfg

    try:
        with open(target, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Malformed YAML in '{target}': {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Failed to read config file '{target}': {exc}") from exc

    if raw is None:
        raw = {}
    elif not isinstance(raw, dict):
        raise ConfigError(
            f"Config file '{target}' must contain a YAML mapping, got {type(raw).__name__}"
        )

    try:
        cfg = EyeSiteConfig(
            app=_build_subconfig(AppConfig, raw.get("app")),
            camera=_build_subconfig(CameraConfig, raw.get("camera")),
            detection=_build_subconfig(DetectionConfig, raw.get("detection")),
            navigation=_build_subconfig(NavigationConfig, raw.get("navigation")),
            ocr=_build_subconfig(OcrConfig, raw.get("ocr")),
            voice_output=_build_subconfig(VoiceOutputConfig, raw.get("voice_output")),
            voice_input=_build_subconfig(VoiceInputConfig, raw.get("voice_input")),
            ui=_build_subconfig(UIConfig, raw.get("ui")),
        )
    except Exception as exc:
        raise ConfigError(f"Failed to parse config: {exc}") from exc

    validate_config(cfg)
    return cfg
