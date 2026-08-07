from swift_bridge import call_swift  # type: ignore
from typing import Literal


def handle_list_devices(type: Literal["output", "input", "all"] = "output") -> list:
    """List audio devices. type: 'output' (default), 'input', or 'all'."""
    return call_swift("sound-list-devices", {"type": type})


def handle_get_output() -> dict:
    """Get the current default audio output device."""
    return call_swift("sound-get-output")


def handle_set_output(name: str) -> dict:
    """Set the default audio output device by name (partial match). E.g. 'MacBook', 'Kilburn', 'AirPods'."""
    return call_swift("sound-set-output", {"name": name})


def handle_get_volume() -> dict:
    """Get current system output volume (0–100) and mute state."""
    return call_swift("sound-get-volume")


def handle_set_volume(level: int) -> dict:
    """Set system output volume. level: 0–100."""
    return call_swift("sound-set-volume", {"level": level})


def handle_mute() -> dict:
    """Mute system audio output."""
    return call_swift("sound-mute")


def handle_unmute() -> dict:
    """Unmute system audio output."""
    return call_swift("sound-unmute")
