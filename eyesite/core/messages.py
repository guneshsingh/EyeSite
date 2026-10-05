"""User-facing speech and announcement message catalogue.

PRD Section M.3 specification.
All strings are defined as constants exactly as written in the PRD.
No user-facing text should be hardcoded elsewhere in the codebase.
"""

STARTING: str = "EyeSite is starting."
READY: str = "EyeSite is ready. Say help to hear commands."
DISCLAIMER: str = (
    "EyeSite is an assistive prototype. It does not replace your cane, "
    "guide dog, or a person helping you."
)
GUIDANCE_ON: str = "Guidance on."
GUIDANCE_OFF: str = "Guidance off."
OCR_START: str = "Reading text."
OCR_BUSY: str = "Still reading. Please wait."
OCR_LOADING: str = "Text reader is still loading. Please wait."
OCR_EMPTY: str = (
    "I could not find any readable text. Try moving closer or improving the light."
)
NOTHING_AHEAD: str = "Nothing detected ahead."
NO_OBJECTS: str = "I do not see any known objects."
STALE: str = "I cannot see clearly right now."
UNKNOWN_CMD: str = "Sorry, I did not understand. Say help for commands."
MIC_MISSING: str = (
    "I cannot hear you because no microphone was found. Please use the keyboard."
)
STT_OFFLINE: str = (
    "Voice commands need internet right now. Please use the keyboard."
)
CAMERA_MISSING: str = (
    "I cannot access the camera. Please check that it is connected."
)
CAMERA_LOST: str = "The camera stopped working. Trying to reconnect."
SHUTDOWN: str = "Goodbye."

# Dictionary mapping for convenient lookup
ALL_MESSAGES: dict[str, str] = {
    "STARTING": STARTING,
    "READY": READY,
    "DISCLAIMER": DISCLAIMER,
    "GUIDANCE_ON": GUIDANCE_ON,
    "GUIDANCE_OFF": GUIDANCE_OFF,
    "OCR_START": OCR_START,
    "OCR_BUSY": OCR_BUSY,
    "OCR_LOADING": OCR_LOADING,
    "OCR_EMPTY": OCR_EMPTY,
    "NOTHING_AHEAD": NOTHING_AHEAD,
    "NO_OBJECTS": NO_OBJECTS,
    "STALE": STALE,
    "UNKNOWN_CMD": UNKNOWN_CMD,
    "MIC_MISSING": MIC_MISSING,
    "STT_OFFLINE": STT_OFFLINE,
    "CAMERA_MISSING": CAMERA_MISSING,
    "CAMERA_LOST": CAMERA_LOST,
    "SHUTDOWN": SHUTDOWN,
}
