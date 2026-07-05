"""Shared protocol command types and validation."""

from __future__ import annotations

from enum import StrEnum


class CommandKind(StrEnum):
    """Normalized command intents supported by core protocols."""

    STATE_QUERY = "state_query"
    POWER = "power"
    BRIGHTNESS = "brightness"
    RGB_COLOR = "rgb_color"
    DYNAMIC_RGB_COLOR = "dynamic_rgb_color"
    RGBW_COLOR = "rgbw_color"
    RGBWW_COLOR = "rgbww_color"
    WHITE_LEVEL = "white_level"
    CCT_COLOR = "cct_color"
    EFFECT = "effect"
    LIGHT_MODE = "light_mode"
    EFFECT_SPEED = "effect_speed"
    EFFECT_LENGTH = "effect_length"
    EFFECT_DIRECTION = "effect_direction"
    EFFECT_LOOP = "effect_loop"
    SCENE_LOOP = "scene_loop"
    AUDIO_INPUT = "audio_input"
    SENSITIVITY = "sensitivity"
    ONOFF_CONFIG = "onoff_config"
    COEXISTENCE = "coexistence"
    ON_POWER = "on_power"
    EFFECT_PLAY = "effect_play"
    LIGHT_TYPE = "light_type"
    CHIP_ORDER = "chip_order"
    SCENE = "scene"


class ProtocolCommandError(ValueError):
    """Raised when a command cannot be built safely."""


class UnsupportedCommand(ProtocolCommandError):
    """Raised when a protocol family does not implement a command."""


def byte_value(value: int, *, field: str) -> int:
    """Validate and return an unsigned byte value."""
    value = int(value)
    if not 0 <= value <= 0xFF:
        raise ProtocolCommandError(f"{field} must be between 0 and 255")
    return value


def ranged_value(value: int, *, field: str, minimum: int, maximum: int) -> int:
    """Validate and return a bounded integer."""
    value = int(value)
    if not minimum <= value <= maximum:
        raise ProtocolCommandError(f"{field} must be between {minimum} and {maximum}")
    return value


def rgb_value(red: int, green: int, blue: int) -> tuple[int, int, int]:
    """Validate and return RGB bytes."""
    return (
        byte_value(red, field="red"),
        byte_value(green, field="green"),
        byte_value(blue, field="blue"),
    )
