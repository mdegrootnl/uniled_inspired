"""Number platform for UniLED command controls."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberEntityDescription
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
    apply_number_command_state,
    command_control_available,
    command_number_features,
    control_value,
    onoff_command_values,
    set_zengge_mesh_effect,
    zengge_mesh_command_ready,
    zengge_mesh_effect_command_values,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UniLEDConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniLED command numbers."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    if coordinator is None:
        return

    async_add_entities(
        UniLEDCommandNumber(coordinator, entry, feature)
        for feature in command_number_features(runtime)
    )


class UniLEDCommandNumber(CoordinatorEntity[UniLEDCoordinator], NumberEntity):
    """Command-capable UniLED number."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UniLEDCoordinator,
        entry: UniLEDConfigEntry,
        feature: FeatureSpec,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator, context=(feature.key, feature.channel))
        self._entry = entry
        self._feature = feature
        self.entity_description = NumberEntityDescription(
            key=feature.key,
            name=feature.name,
            translation_key=feature_translation_key(feature),
            native_min_value=feature.minimum,
            native_max_value=feature.maximum,
            native_step=feature.step or 1,
            native_unit_of_measurement=feature.unit,
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
    def native_value(self) -> int | None:
        """Return the current command value."""
        value = control_value(
            self.coordinator.runtime,
            self._feature.key,
            channel=self._feature.channel,
        )
        return value if isinstance(value, int) else None

    async def async_set_native_value(self, value: float) -> None:
        """Set a command number value."""
        runtime = self.coordinator.runtime
        int_value = int(value)
        if self._feature.implementation_hint == "zengge_mesh_node":
            if not zengge_mesh_command_ready(runtime, self._feature.channel):
                return
            if self._feature.key == "effect_speed":
                effect, speed, level = zengge_mesh_effect_command_values(
                    runtime,
                    self._feature.channel,
                    speed=int_value,
                )
            elif self._feature.key == "effect_level":
                effect, speed, level = zengge_mesh_effect_command_values(
                    runtime,
                    self._feature.channel,
                    level=int_value,
                )
            else:
                return
            await set_zengge_mesh_effect(
                runtime,
                self._feature.channel,
                effect,
                speed=speed,
                level=level,
            )
            self.coordinator.async_set_updated_data(runtime.state)
            return

        session = runtime.session
        if session is None:
            return

        if self._feature.key == "effect_speed":
            await session.set_effect_speed(int_value, channel=self._feature.channel)
        elif self._feature.key == "effect_length":
            await session.set_effect_length(int_value, channel=self._feature.channel)
        elif self._feature.key == "audio_sensitivity":
            await session.set_sensitivity(int_value, channel=self._feature.channel)
        elif self._feature.key == "onoff_pixels":
            effect, speed, pixels = onoff_command_values(runtime, pixels=int_value)
            await session.set_onoff_config(
                effect,
                speed,
                pixels,
                channel=self._feature.channel,
            )
        elif self._feature.key == "segment_count":
            await session.set_segment_count(
                int_value,
                channel=self._feature.channel,
            )
        elif self._feature.key == "segment_pixels":
            await session.set_segment_pixels(
                int_value,
                channel=self._feature.channel,
            )
        else:
            return

        apply_number_command_state(
            runtime,
            self._feature.key,
            int_value,
            channel=self._feature.channel,
        )
        self.coordinator.async_set_updated_data(runtime.state)
