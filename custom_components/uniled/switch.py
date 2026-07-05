"""Switch platform for UniLED command toggles."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import UniLEDConfigEntry
from .coordinator import UniLEDCoordinator
from .core import FeatureSpec
from .entity_metadata import (
    device_connections,
    device_identifiers,
    entity_registry_enabled_default,
    entry_identity,
    feature_translation_key,
    feature_translation_placeholders,
    legacy_uniled_unique_id,
)
from .runtime import (
    apply_switch_command_state,
    command_control_available,
    command_switch_features,
    control_value,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UniLEDConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniLED command switches."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    if coordinator is None:
        return

    async_add_entities(
        UniLEDCommandSwitch(coordinator, entry, feature)
        for feature in command_switch_features(runtime)
    )


class UniLEDCommandSwitch(CoordinatorEntity[UniLEDCoordinator], SwitchEntity):
    """Command-capable UniLED switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UniLEDCoordinator,
        entry: UniLEDConfigEntry,
        feature: FeatureSpec,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, context=(feature.key, feature.channel))
        self._entry = entry
        self._feature = feature
        self.entity_description = SwitchEntityDescription(
            key=feature.key,
            name=feature.name,
            translation_key=feature_translation_key(feature),
        )
        self._attr_unique_id = legacy_uniled_unique_id(entry, feature) or (
            f"{entry_identity(entry)}_{feature.key}_{feature.channel}"
        )
        self._attr_entity_registry_enabled_default = (
            entity_registry_enabled_default(feature)
        )
        placeholders = feature_translation_placeholders(feature)
        if placeholders:
            self._attr_translation_placeholders = placeholders

    @property
    def available(self) -> bool:
        """Return whether the command session is available."""
        return command_control_available(
            self.coordinator.runtime,
            self._feature.key,
            channel=self._feature.channel,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return Home Assistant device information."""
        runtime = self.coordinator.runtime
        return DeviceInfo(
            identifiers=device_identifiers(self._entry),
            connections=device_connections(self._entry),
            manufacturer="BanlanX",
            name=runtime.model.friendly_name,
            model=runtime.model.name,
            sw_version=runtime.state.firmware,
        )

    @property
    def is_on(self) -> bool | None:
        """Return the current toggle value."""
        value = control_value(
            self.coordinator.runtime,
            self._feature.key,
            channel=self._feature.channel,
        )
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_set_state(False)

    async def _async_set_state(self, value: bool) -> None:
        runtime = self.coordinator.runtime
        session = runtime.session
        if session is None:
            return

        if self._feature.key == "effect_direction":
            await session.set_effect_direction(value, channel=self._feature.channel)
        elif self._feature.key == "effect_loop":
            await session.set_effect_loop(value)
        elif self._feature.key == "scene_loop":
            await session.set_scene_loop(value)
        elif self._feature.key == "effect_play":
            await session.set_effect_play(value, channel=self._feature.channel)
        elif self._feature.key == "coexistence":
            await session.set_coexistence(value, channel=self._feature.channel)
        else:
            return

        apply_switch_command_state(
            runtime,
            self._feature.key,
            value,
            channel=self._feature.channel,
        )
        self.coordinator.async_set_updated_data(runtime.state)
