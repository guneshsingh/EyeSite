"""Unit tests for the message catalogue constants.

PRD Section M.3 specification.
Verifies that all required keys are defined and match the exact binding wording.
"""

import eyesite.core.messages as msg


def test_all_required_message_keys_exist() -> None:
    """Verify that every key from PRD Section M.3 exists."""
    expected_keys = [
        "STARTING",
        "READY",
        "DISCLAIMER",
        "GUIDANCE_ON",
        "GUIDANCE_OFF",
        "OCR_START",
        "OCR_BUSY",
        "OCR_LOADING",
        "OCR_EMPTY",
        "NOTHING_AHEAD",
        "NO_OBJECTS",
        "STALE",
        "UNKNOWN_CMD",
        "MIC_MISSING",
        "STT_OFFLINE",
        "CAMERA_MISSING",
        "CAMERA_LOST",
        "SHUTDOWN",
    ]
    for key in expected_keys:
        assert hasattr(msg, key), f"Missing message constant: {key}"
        val = getattr(msg, key)
        assert isinstance(val, str), f"Message {key} must be a string"
        assert len(val.strip()) > 0, f"Message {key} must not be empty"


def test_message_exact_content() -> None:
    """Verify exact strings match PRD Section M.3."""
    assert msg.STARTING == "EyeSite is starting."
    assert msg.READY == "EyeSite is ready. Say help to hear commands."
    assert (
        msg.DISCLAIMER
        == "EyeSite is an assistive prototype. It does not replace your cane, guide dog, or a person helping you."
    )
    assert msg.GUIDANCE_ON == "Guidance on."
    assert msg.GUIDANCE_OFF == "Guidance off."
    assert msg.OCR_START == "Reading text."
    assert msg.OCR_BUSY == "Still reading. Please wait."
    assert msg.OCR_LOADING == "Text reader is still loading. Please wait."
    assert (
        msg.OCR_EMPTY
        == "I could not find any readable text. Try moving closer or improving the light."
    )
    assert msg.NOTHING_AHEAD == "Nothing detected ahead."
    assert msg.NO_OBJECTS == "I do not see any known objects."
    assert msg.STALE == "I cannot see clearly right now."
    assert (
        msg.UNKNOWN_CMD
        == "Sorry, I did not understand. Say help for commands."
    )
    assert (
        msg.MIC_MISSING
        == "I cannot hear you because no microphone was found. Please use the keyboard."
    )
    assert (
        msg.STT_OFFLINE
        == "Voice commands need internet right now. Please use the keyboard."
    )
    assert (
        msg.CAMERA_MISSING
        == "I cannot access the camera. Please check that it is connected."
    )
    assert (
        msg.CAMERA_LOST
        == "The camera stopped working. Trying to reconnect."
    )
    assert msg.SHUTDOWN == "Goodbye."


def test_all_messages_map_consistency() -> None:
    """Verify that the ALL_MESSAGES dict contains all constants."""
    assert len(msg.ALL_MESSAGES) == 18
    for key, value in msg.ALL_MESSAGES.items():
        assert getattr(msg, key) == value
