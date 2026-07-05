"""Select platform for UniLED command choices."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
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
    apply_select_command_state,
    command_control_available,
    command_select_features,
    control_value,
    effect_channel_allows_commands,
    effect_command_value,
    light_mode_command_values,
    light_type_command_values,
    onoff_command_values,
    select_command_value,
    select_options,
    set_zengge_mesh_effect,
    zengge_mesh_command_ready,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UniLEDConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniLED command selects."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    if coordinator is None:
        return

    async_add_entities(
        UniLEDCommandSelect(coordinator, entry, feature)
        for feature in command_select_features(runtime)
    )


class UniLEDCommandSelect(CoordinatorEntity[UniLEDCoordinator], SelectEntity):
    """Command-capable UniLED select."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: UniLEDCoordinator,
        entry: UniLEDConfigEntry,
        feature: FeatureSpec,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator, context=(feature.key, feature.channel))
        self._entry = entry
        self._feature = feature
        self.entity_description = SelectEntityDescription(
            key=feature.key,
            name=feature.name,
            translation_key=feature_translation_key(feature),
            options=list(feature.options),
        )
        self._attr_unique_id = legacy_uniled_unique_id(entry, feature) or (
            f"{entry_identity(entry)}_{feature.key}_{feature.channel}"
        )
        self._attr_entity_registry_enabled_default = (
            entity_registry_enabled_default(feature)
        )
        self._mesh_node = feature.implementation_hint == "zengge_mesh_node"
        placeholders = feature_translation_placeholders(feature)
        if placeholders:
            self._attr_translation_placeholders = placeholders

    @property
    def available(self) -> bool:
        """Return whether the command session is available."""
        if self._mesh_node:
            return zengge_mesh_command_ready(
                self.coordinator.runtime,
                self._feature.channel,
            )
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
    def options(self) -> list[str]:
        """Return available select options."""
        return list(
            select_options(
                self.coordinator.runtime,
                self._feature.key,
                channel=self._feature.channel,
            )
        )

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        value = control_value(
            self.coordinator.runtime,
            self._feature.key,
            channel=self._feature.channel,
        )
        return value if isinstance(value, str) else None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        runtime = self.coordinator.runtime
        if self._mesh_node:
            if not zengge_mesh_command_ready(runtime, self._feature.channel):
                return
            effect_value = effect_command_value(
                runtime,
                option,
                channel=self._feature.channel,
            )
            if isinstance(effect_value, tuple):
                effect_value = effect_value[-1]
            await set_zengge_mesh_effect(
                runtime,
                self._feature.channel,
                effect_value,
            )
            self.coordinator.async_set_updated_data(runtime.state)
            return

        session = runtime.session
        if session is None:
            return

        if self._feature.key == "effect" and not effect_channel_allows_commands(
            runtime,
            channel=self._feature.channel,
        ):
            return

        raw_value = select_command_value(
            runtime,
            self._feature.key,
            option,
            channel=self._feature.channel,
        )
        if self._feature.key == "audio_input":
            await session.set_audio_input(raw_value, channel=self._feature.channel)
        elif self._feature.key == "effect":
            effect_value = effect_command_value(
                runtime,
                option,
                channel=self._feature.channel,
            )
            if isinstance(effect_value, tuple):
                await session.set_light_mode(effect_value[0], effect_value[1])
            else:
                await session.set_effect(effect_value, channel=self._feature.channel)
        elif self._feature.key == "light_mode":
            mode_effect = light_mode_command_values(
                runtime,
                raw_value,
                channel=self._feature.channel,
            )
            if mode_effect is None:
                await session.set_light_mode(raw_value)
            else:
                await session.set_light_mode(mode_effect[0], mode_effect[1])
        elif self._feature.key == "light_type":
            command = light_type_command_values(
                runtime,
                raw_value,
                channel=self._feature.channel,
            )
            await session.set_light_type(
                command.light_type,
                command.chip_order,
                command.mode,
                command.effect,
                power=command.power,
                refresh=command.refresh,
                channel=self._feature.channel,
            )
        elif self._feature.key == "chip_order":
            await session.set_chip_order(raw_value, channel=self._feature.channel)
        elif self._feature.key == "onoff_effect":
            effect, speed, pixels = onoff_command_values(runtime, effect=raw_value)
            await session.set_onoff_config(
                effect,
                speed,
                pixels,
                channel=self._feature.channel,
            )
        elif self._feature.key == "onoff_speed":
            effect, speed, pixels = onoff_command_values(runtime, speed=raw_value)
            await session.set_onoff_config(
                effect,
                speed,
                pixels,
                channel=self._feature.channel,
            )
        elif self._feature.key == "on_power":
            await session.set_on_power(raw_value, channel=self._feature.channel)
        else:
            return

        apply_select_command_state(
            runtime,
            self._feature.key,
            option,
            channel=self._feature.channel,
        )
        self.coordinator.async_set_updated_data(runtime.state)
