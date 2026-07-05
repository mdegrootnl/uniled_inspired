"""Light platform for UniLED."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_TRANSITION,
    ATTR_WHITE,
    EFFECT_OFF,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
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
    apply_light_command_state,
    apply_select_command_state,
    apply_sp6xx_sound_brightness_ignored,
    async_apply_legacy_set_state_service,
    async_ensure_banlanx_v23_rgb_effect,
    async_ensure_banlanx_v23_white_effect,
    async_ensure_sp6xx_white_mode,
    banlanx_v23_brightness_uses_white_level,
    cct_levels_for_kelvin,
    channel_state,
    color_command_level,
    command_light_features,
    control_value,
    effect_channel_allows_commands,
    effect_command_value,
    light_color_mode,
    light_supported_color_modes,
    light_uses_static_color_command,
    select_options,
    set_zengge_mesh_brightness,
    set_zengge_mesh_color_temp,
    set_zengge_mesh_effect,
    set_zengge_mesh_power,
    set_zengge_mesh_rgb,
    set_zengge_mesh_white,
    sp6xx_brightness_uses_white_level,
    suppress_sp6xx_sound_brightness_command,
    zengge_mesh_command_ready,
)

_COLOR_MODE_MAP = {
    "brightness": ColorMode.BRIGHTNESS,
    "color_temp": ColorMode.COLOR_TEMP,
    "onoff": ColorMode.ONOFF,
    "rgb": ColorMode.RGB,
    "rgbw": ColorMode.RGBW,
    "rgbww": ColorMode.RGBWW,
    "white": ColorMode.WHITE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UniLEDConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up UniLED lights."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator
    if coordinator is None:
        return

    async_add_entities(
        UniLEDLight(coordinator, entry, feature)
        for feature in command_light_features(runtime)
    )


class UniLEDLight(CoordinatorEntity[UniLEDCoordinator], LightEntity):
    """Command-capable UniLED light."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_min_color_temp_kelvin = 2700
    _attr_max_color_temp_kelvin = 6500

    def __init__(
        self,
        coordinator: UniLEDCoordinator,
        entry: UniLEDConfigEntry,
        feature: FeatureSpec,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator, context=feature.channel)
        self._entry = entry
        self._feature = feature
        self._channel = feature.channel
        self._mesh_node = feature.implementation_hint == "zengge_mesh_node"
        self._attr_unique_id = legacy_uniled_unique_id(entry, feature) or (
            _light_unique_id(entry_identity(entry), feature)
        )
        self._attr_entity_registry_enabled_default = (
            entity_registry_enabled_default(feature)
        )
        self._attr_name = None if feature.key == "main_light" else feature.name
        translation_key = feature_translation_key(feature)
        if translation_key is not None:
            self._attr_translation_key = translation_key
        placeholders = feature_translation_placeholders(feature)
        if placeholders:
            self._attr_translation_placeholders = placeholders

    @property
    def available(self) -> bool:
        """Return whether the command session is available."""
        runtime = self.coordinator.runtime
        if self._mesh_node:
            return zengge_mesh_command_ready(runtime, self._channel)
        return runtime.session_ready

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
    def is_on(self) -> bool:
        """Return whether the light is on."""
        return bool(channel_state(self.coordinator.runtime, self._channel).power)

    @property
    def brightness(self) -> int | None:
        """Return brightness."""
        return channel_state(self.coordinator.runtime, self._channel).brightness

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return RGB color."""
        return channel_state(self.coordinator.runtime, self._channel).rgb

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return RGBW color."""
        return channel_state(self.coordinator.runtime, self._channel).rgbw

    @property
    def rgbww_color(self) -> tuple[int, int, int, int, int] | None:
        """Return RGBWW color."""
        return channel_state(self.coordinator.runtime, self._channel).rgbww

    @property
    def white(self) -> int | None:
        """Return white level."""
        value = channel_state(
            self.coordinator.runtime,
            self._channel,
        ).extra.get("white_level")
        return value if isinstance(value, int) else None

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return color temperature in Kelvin."""
        return channel_state(
            self.coordinator.runtime,
            self._channel,
        ).color_temp_kelvin

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Return supported color modes."""
        return {
            _COLOR_MODE_MAP[mode]
            for mode in light_supported_color_modes(
                self.coordinator.runtime,
                channel=self._channel,
            )
        }

    @property
    def color_mode(self) -> ColorMode:
        """Return the current color mode."""
        return _COLOR_MODE_MAP[
            light_color_mode(
                self.coordinator.runtime,
                channel=self._channel,
            )
        ]

    @property
    def supported_features(self) -> LightEntityFeature:
        """Return supported light features."""
        features = LightEntityFeature(0)
        if self.effect_list:
            features |= LightEntityFeature.EFFECT
        if self._mesh_node:
            features |= LightEntityFeature.TRANSITION
        return features

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        value = control_value(
            self.coordinator.runtime,
            "effect",
            channel=self._channel,
        )
        return value if isinstance(value, str) else EFFECT_OFF

    @property
    def effect_list(self) -> list[str] | None:
        """Return available effects."""
        options = select_options(
            self.coordinator.runtime,
            "effect",
            channel=self._channel,
        )
        return list(options) if options else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        runtime = self.coordinator.runtime
        if self._mesh_node:
            await self._async_turn_on_mesh(**kwargs)
            return

        session = runtime.session
        if session is None:
            return

        if ATTR_EFFECT in kwargs and effect_channel_allows_commands(
            runtime,
            channel=self._channel,
        ):
            effect = kwargs[ATTR_EFFECT]
            effect_value = effect_command_value(
                runtime,
                effect,
                channel=self._channel,
            )
            if isinstance(effect_value, tuple):
                await session.set_light_mode(effect_value[0], effect_value[1])
            else:
                await session.set_effect(effect_value, channel=self._channel)
            apply_select_command_state(
                runtime,
                "effect",
                effect,
                channel=self._channel,
            )

        static_color = light_uses_static_color_command(
            runtime,
            channel=self._channel,
        )
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        command_level = color_command_level(
            runtime,
            brightness,
            channel=self._channel,
        )

        if ATTR_RGBWW_COLOR in kwargs:
            red, green, blue, cold, warm = kwargs[ATTR_RGBWW_COLOR]
            await session.set_rgbww_color(
                red,
                green,
                blue,
                cold,
                warm,
                channel=self._channel,
                level=command_level,
                static=static_color,
            )
            apply_light_command_state(
                runtime,
                channel=self._channel,
                rgbww=(red, green, blue, cold, warm),
                brightness=brightness,
                cct=(cold, warm),
            )
        elif ATTR_RGBW_COLOR in kwargs:
            red, green, blue, white = kwargs[ATTR_RGBW_COLOR]
            await async_ensure_banlanx_v23_rgb_effect(
                runtime,
                channel=self._channel,
            )
            await session.set_rgbw_color(
                red,
                green,
                blue,
                white,
                channel=self._channel,
                level=command_level,
                static=static_color,
            )
            apply_light_command_state(
                runtime,
                channel=self._channel,
                rgbw=(red, green, blue, white),
                brightness=brightness,
                white=white,
            )
        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            level = brightness
            if level is None:
                level = self.white
            if level is None:
                level = self.brightness
            if level is None:
                level = 0xFF
            cold, warm = cct_levels_for_kelvin(
                kwargs[ATTR_COLOR_TEMP_KELVIN],
                level=level,
            )
            await session.set_cct_color(
                cold,
                warm,
                channel=self._channel,
                static=static_color,
            )
            apply_light_command_state(
                runtime,
                channel=self._channel,
                brightness=level,
                color_temp_kelvin=kwargs[ATTR_COLOR_TEMP_KELVIN],
                cct=(cold, warm),
            )
        elif ATTR_WHITE in kwargs:
            await async_ensure_sp6xx_white_mode(runtime, channel=self._channel)
            await async_ensure_banlanx_v23_white_effect(
                runtime,
                channel=self._channel,
            )
            if suppress_sp6xx_sound_brightness_command(
                runtime,
                channel=self._channel,
            ):
                apply_sp6xx_sound_brightness_ignored(
                    runtime,
                    channel=self._channel,
                )
            else:
                if banlanx_v23_brightness_uses_white_level(
                    runtime,
                    channel=self._channel,
                ):
                    await session.set_white_brightness(
                        kwargs[ATTR_WHITE],
                        channel=self._channel,
                    )
                else:
                    await session.set_white_level(
                        kwargs[ATTR_WHITE],
                        channel=self._channel,
                    )
                apply_light_command_state(
                    runtime,
                    channel=self._channel,
                    brightness=kwargs[ATTR_WHITE],
                    white=kwargs[ATTR_WHITE],
                )
        elif ATTR_RGB_COLOR in kwargs:
            red, green, blue = kwargs[ATTR_RGB_COLOR]
            await async_ensure_banlanx_v23_rgb_effect(
                runtime,
                channel=self._channel,
            )
            if static_color:
                await session.set_rgb_color(
                    red,
                    green,
                    blue,
                    channel=self._channel,
                    level=command_level,
                )
            else:
                await session.set_dynamic_rgb_color(
                    red,
                    green,
                    blue,
                    channel=self._channel,
                )
            apply_light_command_state(
                runtime,
                channel=self._channel,
                rgb=(red, green, blue),
                brightness=brightness if static_color else None,
            )
        elif ATTR_BRIGHTNESS in kwargs:
            if suppress_sp6xx_sound_brightness_command(
                runtime,
                channel=self._channel,
            ):
                apply_sp6xx_sound_brightness_ignored(
                    runtime,
                    channel=self._channel,
                )
            elif banlanx_v23_brightness_uses_white_level(
                runtime,
                channel=self._channel,
            ):
                await session.set_white_brightness(
                    kwargs[ATTR_BRIGHTNESS],
                    channel=self._channel,
                )
                apply_light_command_state(
                    runtime,
                    channel=self._channel,
                    brightness=kwargs[ATTR_BRIGHTNESS],
                    white=kwargs[ATTR_BRIGHTNESS],
                )
            elif (
                sp6xx_brightness_uses_white_level(runtime, channel=self._channel)
                or (
                    "white"
                    in light_supported_color_modes(runtime, channel=self._channel)
                    and light_color_mode(runtime, channel=self._channel) == "white"
                )
            ):
                await session.set_white_level(
                    kwargs[ATTR_BRIGHTNESS],
                    channel=self._channel,
                )
                apply_light_command_state(
                    runtime,
                    channel=self._channel,
                    brightness=kwargs[ATTR_BRIGHTNESS],
                    white=kwargs[ATTR_BRIGHTNESS],
                )
            else:
                await session.set_brightness(
                    kwargs[ATTR_BRIGHTNESS],
                    channel=self._channel,
                )
                apply_light_command_state(
                    runtime,
                    channel=self._channel,
                    brightness=kwargs[ATTR_BRIGHTNESS],
                )
        elif ATTR_EFFECT not in kwargs:
            await session.set_power(True, channel=self._channel)
            apply_light_command_state(runtime, channel=self._channel, power=True)
        elif not channel_state(runtime, self._channel).power:
            await session.set_power(True, channel=self._channel)
            apply_light_command_state(runtime, channel=self._channel, power=True)

        self.coordinator.async_set_updated_data(runtime.state)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        runtime = self.coordinator.runtime
        if self._mesh_node:
            if zengge_mesh_command_ready(runtime, self._channel):
                await set_zengge_mesh_power(
                    runtime,
                    self._channel,
                    False,
                    gradual_seconds=_transition_seconds(
                        kwargs.get(ATTR_TRANSITION),
                    ),
                )
                self.coordinator.async_set_updated_data(runtime.state)
            return

        session = runtime.session
        if session is None:
            return
        await session.set_power(False, channel=self._channel)
        apply_light_command_state(runtime, channel=self._channel, power=False)
        self.coordinator.async_set_updated_data(runtime.state)

    async def async_set_uniled_state(self, **kwargs: Any) -> None:
        """Apply the old UniLED set_state entity service."""
        runtime = self.coordinator.runtime
        changed = await async_apply_legacy_set_state_service(
            runtime,
            kwargs,
            channel=self._channel,
        )
        if changed:
            self.coordinator.async_set_updated_data(runtime.state)

    async def _async_turn_on_mesh(self, **kwargs: Any) -> None:
        """Turn on a Zengge mesh node light."""
        runtime = self.coordinator.runtime
        if not zengge_mesh_command_ready(runtime, self._channel):
            return

        sent = False
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        gradual_seconds = _transition_seconds(kwargs.get(ATTR_TRANSITION))

        if ATTR_EFFECT in kwargs and kwargs[ATTR_EFFECT] != EFFECT_OFF:
            effect_value = effect_command_value(
                runtime,
                kwargs[ATTR_EFFECT],
                channel=self._channel,
            )
            if isinstance(effect_value, tuple):
                effect_value = effect_value[-1]
            await set_zengge_mesh_effect(runtime, self._channel, effect_value)
            sent = True

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            level = brightness
            if level is None:
                level = self.brightness
            if level is None:
                level = 0xFF
            await set_zengge_mesh_color_temp(
                runtime,
                self._channel,
                kwargs[ATTR_COLOR_TEMP_KELVIN],
                level=level,
                gradual_seconds=gradual_seconds,
            )
            sent = True
        elif ATTR_WHITE in kwargs:
            await set_zengge_mesh_white(
                runtime,
                self._channel,
                kwargs[ATTR_WHITE],
                gradual_seconds=gradual_seconds,
            )
            sent = True
        elif ATTR_RGB_COLOR in kwargs:
            red, green, blue = kwargs[ATTR_RGB_COLOR]
            await set_zengge_mesh_rgb(
                runtime,
                self._channel,
                red,
                green,
                blue,
                gradual_seconds=gradual_seconds,
            )
            sent = True
            if brightness is not None:
                await set_zengge_mesh_brightness(
                    runtime,
                    self._channel,
                    brightness,
                    gradual_seconds=gradual_seconds,
                )
        elif brightness is not None:
            await set_zengge_mesh_brightness(
                runtime,
                self._channel,
                brightness,
                gradual_seconds=gradual_seconds,
            )
            sent = True

        if not sent and ATTR_EFFECT not in kwargs:
            await set_zengge_mesh_power(
                runtime,
                self._channel,
                True,
                gradual_seconds=gradual_seconds,
            )
        elif not channel_state(runtime, self._channel).power:
            await set_zengge_mesh_power(
                runtime,
                self._channel,
                True,
                gradual_seconds=gradual_seconds,
            )

        self.coordinator.async_set_updated_data(runtime.state)


def _transition_seconds(value: Any) -> float:
    """Return a non-negative HA transition value for mesh gradual fields."""
    if value is None:
        return 0.0
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return 0.0
    return seconds if seconds > 0.0 else 0.0


def _light_unique_id(entry_id: str, feature: FeatureSpec) -> str:
    if feature.key == "main_light":
        return f"{entry_id}_light_{feature.channel}"
    return f"{entry_id}_{feature.key}"
