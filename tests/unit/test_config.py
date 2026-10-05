"""Unit tests for configuration loading and validation.

PRD Section P.2: Defaults on missing keys; invalid values raise ConfigError.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from eyesite.core.config import EyeSiteConfig, load_config, validate_config
from eyesite.core.models import ConfigError


def test_load_config_default_when_file_missing(tmp_path: Path) -> None:
    """Missing config file should fall back to built-in defaults without error."""
    non_existent = tmp_path / "non_existent.yaml"
    cfg = load_config(non_existent)
    assert isinstance(cfg, EyeSiteConfig)
    assert cfg.camera.width == 640
    assert cfg.camera.height == 480
    assert cfg.detection.confidence == 0.45
    assert cfg.navigation.left_max == 0.33
    assert cfg.navigation.right_min == 0.67


def test_load_existing_config_yaml() -> None:
    """The root config.yaml should load cleanly and match Section M.1 values."""
    cfg = load_config("config.yaml")
    assert cfg.app.first_run_disclaimer is True
    assert cfg.camera.source == 0
    assert cfg.camera.fps == 30
    assert cfg.detection.model_path == "assets/yolov8n.pt"
    assert cfg.detection.max_rate_hz == 5
    assert cfg.navigation.cooldown_s == 6.0
    assert "person" in cfg.navigation.relevant_classes
    assert cfg.ocr.preload is True
    assert cfg.voice_output.rate == 170
    assert cfg.voice_input.mode == "push_to_talk"
    assert cfg.ui.theme == "high_contrast"


def test_missing_subkeys_fall_back_to_defaults(tmp_path: Path) -> None:
    """A partial config YAML file should populate missing keys with defaults."""
    partial_yaml = tmp_path / "partial.yaml"
    content = {
        "camera": {"width": 1280},
        "detection": {"confidence": 0.60},
    }
    with open(partial_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(content, f)

    cfg = load_config(partial_yaml)
    assert cfg.camera.width == 1280
    assert cfg.camera.height == 480  # Default preserved
    assert cfg.detection.confidence == 0.60
    assert cfg.detection.iou == 0.5  # Default preserved
    assert cfg.navigation.left_max == 0.33  # Subconfig completely defaulted


def test_unknown_keys_ignored_without_failure(tmp_path: Path) -> None:
    """Unrecognized keys should trigger a warning but not fail validation."""
    custom_yaml = tmp_path / "unknown.yaml"
    content = {
        "camera": {"width": 640, "unexpected_setting": 999},
        "extra_section": {"foo": "bar"},
    }
    with open(custom_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(content, f)

    cfg = load_config(custom_yaml)
    assert cfg.camera.width == 640


@pytest.mark.parametrize(
    "invalid_kwargs",
    [
        {"camera": {"width": 0}},
        {"camera": {"fps": -1}},
        {"detection": {"confidence": 1.5}},
        {"detection": {"confidence": -0.1}},
        {"detection": {"iou": 2.0}},
        {"detection": {"max_rate_hz": 0}},
        {"detection": {"stale_after_s": -0.5}},
        {"navigation": {"left_max": 0.8, "right_min": 0.2}},  # left >= right
        {"navigation": {"near_area_ratio": 0.5, "very_close_area_ratio": 0.2}},  # near >= very_close
        {"navigation": {"cooldown_s": -1.0}},
        {"voice_output": {"volume": 1.5}},
        {"voice_output": {"rate": 0}},
    ],
)
def test_invalid_values_raise_config_error(tmp_path: Path, invalid_kwargs: dict) -> None:
    """Invalid parameter values must raise ConfigError."""
    bad_yaml = tmp_path / "bad.yaml"
    with open(bad_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(invalid_kwargs, f)

    with pytest.raises(ConfigError):
        load_config(bad_yaml)


def test_malformed_yaml_raises_config_error(tmp_path: Path) -> None:
    """Corrupted/non-YAML text files should raise ConfigError."""
    malformed_yaml = tmp_path / "malformed.yaml"
    malformed_yaml.write_text("app: [broken: yaml: {", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(malformed_yaml)


def test_non_dict_yaml_raises_config_error(tmp_path: Path) -> None:
    """YAML file containing a list instead of a dict mapping should raise ConfigError."""
    list_yaml = tmp_path / "list.yaml"
    list_yaml.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(list_yaml)


def test_validate_config_direct() -> None:
    """Directly validating an EyeSiteConfig instance."""
    cfg = EyeSiteConfig()
    validate_config(cfg)  # Default config is valid
