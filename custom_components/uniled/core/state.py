"""Home Assistant-independent normalized device state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

RGBColor = tuple[int, int, int]
RGBWColor = tuple[int, int, int, int]
RGBWWColor = tuple[int, int, int, int, int]


class ParseNotificationError(ValueError):
    """Raised when a device notification cannot be parsed safely."""


@dataclass(slots=True)
class ChannelState:
    """Normalized state for one logical controller channel."""

    channel_id: int
    power: bool | None = None
    brightness: int | None = None
    rgb: RGBColor | None = None
    rgbw: RGBWColor | None = None
    rgbww: RGBWWColor | None = None
    color_temp_kelvin: int | None = None
    effect: str | None = None
    effect_number: int | None = None
    effect_type: str | None = None
    effect_speed: int | None = None
    effect_length: int | None = None
    effect_direction: bool | None = None
    effect_loop: bool | None = None
    light_mode: str | None = None
    light_mode_number: int | None = None
    audio_input: int | str | None = None
    sensitivity: int | None = None
    chip_order: int | None = None
    cold_white: int | None = None
    warm_white: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DeviceState:
    """Normalized state for a controller device."""

    available: bool = True
    model: str | None = None
    firmware: str | None = None
    channels: dict[int, ChannelState] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    last_update: datetime | None = None
    raw: bytes | None = None

    def channel(self, channel_id: int) -> ChannelState | None:
        """Return a parsed channel by ID."""
        return self.channels.get(channel_id)
