"""Scene platform for UniLED scene recall."""

from __future__ import annotations

from typing import Any

from homeassistant.components.scene import Scene
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
from .runtime import apply_scene_command_state, command_scene_features


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UniLEDConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniLED scene recall entities."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    if coordinator is None:
        return

    async_add_entities(
        UniLEDScene(coordinator, entry, feature)
        for feature in command_scene_features(runtime)
    )


class UniLEDScene(CoordinatorEntity[UniLEDCoordinator], Scene):
    """Command-capable UniLED scene recall."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UniLEDCoordinator,
        entry: UniLEDConfigEntry,
        feature: FeatureSpec,
    ) -> None:
        """Initialize the scene entity."""
        super().__init__(coordinator, context=feature.channel)
        self._entry = entry
        self._feature = feature
        self._attr_unique_id = legacy_uniled_unique_id(entry, feature) or (
            f"{entry_identity(entry)}_{feature.key}"
        )
        self._attr_entity_registry_enabled_default = (
            entity_registry_enabled_default(feature)
        )
        self._attr_name = feature.name
        translation_key = feature_translation_key(feature)
        if translation_key is not None:
            self._attr_translation_key = translation_key
        placeholders = feature_translation_placeholders(feature)
        if placeholders:
            self._attr_translation_placeholders = placeholders

    @property
    def available(self) -> bool:
        """Return whether the command session is available."""
        return self.coordinator.runtime.session_ready

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

    async def async_activate(self, **kwargs: Any) -> None:
        """Recall this UniLED scene."""
        runtime = self.coordinator.runtime
        session = runtime.session
        if session is None:
            return

        await session.set_scene(self._feature.channel)
        apply_scene_command_state(
            runtime,
            self._feature.channel,
        )
        self.coordinator.async_set_updated_data(runtime.state)
