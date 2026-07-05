"""Button platform for UniLED runtime actions."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import UniLEDConfigEntry
from .coordinator import UniLEDCoordinator
from .core import EntityCategoryKind, FeatureSpec
from .entity_metadata import (
    device_connections,
    device_identifiers,
    entity_registry_enabled_default,
    entry_identity,
    feature_translation_key,
)
from .runtime import command_button_features


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UniLEDConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniLED action buttons."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    if coordinator is None:
        return

    async_add_entities(
        UniLEDButton(coordinator, entry, feature)
        for feature in command_button_features(runtime)
    )


class UniLEDButton(CoordinatorEntity[UniLEDCoordinator], ButtonEntity):
    """Command-capable UniLED button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UniLEDCoordinator,
        entry: UniLEDConfigEntry,
        feature: FeatureSpec,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, context=feature.key)
        self._entry = entry
        self._feature = feature
        self.entity_description = ButtonEntityDescription(
            key=feature.key,
            name=feature.name,
            translation_key=feature_translation_key(feature),
            entity_category=_entity_category(feature.entity_category),
        )
        self._attr_unique_id = f"{entry_identity(entry)}_{feature.key}"
        self._attr_entity_registry_enabled_default = (
            entity_registry_enabled_default(feature)
        )

    @property
    def available(self) -> bool:
        """Return whether a refresh path is attached."""
        runtime = self.coordinator.runtime
        return runtime.session_ready or runtime.mesh_transport_ready

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

    async def async_press(self) -> None:
        """Trigger the runtime action."""
        if self._feature.key == "refresh":
            await self.coordinator.async_request_refresh()


def _entity_category(
    category: EntityCategoryKind | None,
) -> EntityCategory | None:
    if category is EntityCategoryKind.DIAGNOSTIC:
        return EntityCategory.DIAGNOSTIC
    if category is EntityCategoryKind.CONFIG:
        return EntityCategory.CONFIG
    return None
