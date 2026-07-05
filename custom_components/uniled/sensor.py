"""Sensor platform for UniLED diagnostics."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
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
    feature_translation_placeholders,
    legacy_uniled_unique_id,
)
from .runtime import diagnostic_sensor_features

_MAX_NATIVE_STATE_LENGTH = 255
_OVERLONG_DIAGNOSTIC_STATE = "see_attributes"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UniLEDConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniLED diagnostic sensors."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    if coordinator is None:
        return

    async_add_entities(
        UniLEDDiagnosticSensor(
            coordinator,
            entry,
            feature,
        )
        for feature in diagnostic_sensor_features(runtime)
    )


class UniLEDDiagnosticSensor(CoordinatorEntity[UniLEDCoordinator], SensorEntity):
    """Diagnostic sensor backed by catalog/runtime data."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UniLEDCoordinator,
        entry: UniLEDConfigEntry,
        feature: FeatureSpec,
    ) -> None:
        """Initialize the diagnostic sensor."""
        super().__init__(coordinator)
        self._entry = entry
        description = SensorEntityDescription(
            key=feature.key,
            name=feature.name,
            translation_key=feature_translation_key(feature),
            entity_category=_entity_category(feature.entity_category),
            native_unit_of_measurement=feature.unit,
        )
        self.entity_description = description
        self._attr_unique_id = legacy_uniled_unique_id(entry, feature) or (
            f"{entry_identity(entry)}_{description.key}"
        )
        self._attr_entity_registry_enabled_default = (
            entity_registry_enabled_default(feature)
        )
        placeholders = feature_translation_placeholders(feature)
        if placeholders:
            self._attr_translation_placeholders = placeholders

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
    def native_value(self) -> str | int | bool | None:
        """Return the current diagnostic value."""
        value = self.coordinator.runtime.diagnostic_value(self.entity_description.key)
        if isinstance(value, str) and len(value) > _MAX_NATIVE_STATE_LENGTH:
            return _OVERLONG_DIAGNOSTIC_STATE
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return full diagnostic text when it cannot fit in the HA state."""
        value = self.coordinator.runtime.diagnostic_value(self.entity_description.key)
        if not isinstance(value, str) or len(value) <= _MAX_NATIVE_STATE_LENGTH:
            return None
        return {
            "diagnostic_value": value,
            "diagnostic_value_length": len(value),
        }


def _entity_category(
    category: EntityCategoryKind | None,
) -> EntityCategory | None:
    if category is EntityCategoryKind.DIAGNOSTIC:
        return EntityCategory.DIAGNOSTIC
    if category is EntityCategoryKind.CONFIG:
        return EntityCategory.CONFIG
    return None
