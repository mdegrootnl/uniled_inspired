"""Diagnostics support for UniLED."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import UniLEDConfigEntry
from .runtime import runtime_diagnostics


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: UniLEDConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return runtime_diagnostics(entry.runtime_data, entry_data=entry.data)
