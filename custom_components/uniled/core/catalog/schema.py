"""Typed catalog schema."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any


class ProtocolFamily(StrEnum):
    """Known protocol families."""

    BANLANX_601 = "banlanx_601"
    BANLANX_V2 = "banlanx_v2"
    BANLANX_V3 = "banlanx_v3"
    BANLANX_60X = "banlanx_60x"
    BANLANX_6XX = "banlanx_6xx"
    BANLANX_CUSTOM_5XX = "banlanx_custom_5xx"
    BANLANX_SCENE_UI = "banlanx_scene_ui"
    BANLANX_SCENE_MESH = "banlanx_scene_mesh"
    BANLANX_CAR_LIGHTS = "banlanx_car_lights"
    BANLANX_NETWORK = "banlanx_network"
    FISH_TANK = "fish_tank"
    LEGACY_LED_CHORD = "legacy_led_chord"
    LEGACY_LED_HUE = "legacy_led_hue"
    ZENGGE_MESH = "zengge_mesh"
    PLACEHOLDER = "placeholder"
    UNKNOWN = "unknown"


class SupportLevel(StrEnum):
    """Current implementation support disposition."""

    FULL = "full"
    LIMITED = "limited"
    RECOGNIZED = "recognized"
    FILTERED = "filtered"


class TransportKind(StrEnum):
    """Transport families available to the core."""

    BLE = "ble"
    BLE_MESH = "ble_mesh"
    LAN = "lan"
    CLOUD_OPTIONAL = "cloud_optional"


CONNECT_CAPABILITY_BITS: tuple[tuple[int, str], ...] = (
    (0x01, TransportKind.BLE.value),
    (0x02, TransportKind.LAN.value),
    (0x04, TransportKind.CLOUD_OPTIONAL.value),
    (0x08, TransportKind.BLE_MESH.value),
)
SPEC_FUNCTION_BITS: tuple[tuple[int, str], ...] = (
    (0x01, "feature_0x01"),
    (0x02, "audio_controls"),
    (0x04, "feature_0x04"),
    (0x08, "feature_0x08"),
    (0x10, "feature_0x10"),
    (0x20, "feature_0x20"),
    (0x40, "feature_0x40"),
    (0x80, "feature_0x80"),
)
COLOR_CAPABILITY_LABELS: Mapping[int, tuple[str, ...]] = MappingProxyType(
    {
        0: (),
        1: ("rgb",),
        2: ("rgbw_or_cct",),
        4: ("addressable_rgb",),
        8: ("addressable_rgbw",),
    }
)


def connect_capability_names(connect_caps: int) -> tuple[str, ...]:
    """Decode the APK catalog connectCaps bitmask into transport labels."""
    return tuple(
        label
        for bit, label in CONNECT_CAPABILITY_BITS
        if int(connect_caps) & bit
    )


def spec_function_bit_names(spec_functions: int) -> tuple[str, ...]:
    """Decode the APK catalog specFunctions bitmask into stable labels."""
    return tuple(
        label
        for bit, label in SPEC_FUNCTION_BITS
        if int(spec_functions) & bit
    )


def color_capability_names(color_cap: int) -> tuple[str, ...]:
    """Return the APK catalog colorCap labels used by entity planning."""
    value = int(color_cap)
    if value in COLOR_CAPABILITY_LABELS:
        return COLOR_CAPABILITY_LABELS[value]
    return ("unknown",) if value else ()


@dataclass(frozen=True, slots=True)
class CatalogModel:
    """A single catalog model record."""

    model_id: int
    parent_id: int | None
    name: str
    friendly_name: str
    home_uri: str
    connect_caps: int
    spec_functions: int
    color_cap: int
    family: ProtocolFamily
    transports: tuple[TransportKind, ...]
    support_level: SupportLevel
    legacy_uniled_supported: bool
    features: Mapping[str, Any]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CatalogModel:
        """Create a typed model from generated catalog data."""
        return cls(
            model_id=int(data["model_id"]),
            parent_id=data["parent_id"],
            name=str(data["name"]),
            friendly_name=str(data["friendly_name"]),
            home_uri=str(data["home_uri"]),
            connect_caps=int(data["connect_caps"]),
            spec_functions=int(data["spec_functions"]),
            color_cap=int(data["color_cap"]),
            family=ProtocolFamily(str(data["family"])),
            transports=tuple(
                TransportKind(str(transport)) for transport in data["transports"]
            ),
            support_level=SupportLevel(str(data["support_level"])),
            legacy_uniled_supported=bool(data["legacy_uniled_supported"]),
            features=MappingProxyType(dict(data["features"])),
        )

    @property
    def is_user_facing(self) -> bool:
        """Return whether users should see this model."""
        return self.support_level is not SupportLevel.FILTERED

    @property
    def connect_capabilities(self) -> tuple[str, ...]:
        """Return the decoded APK connectCaps capability labels."""
        return connect_capability_names(self.connect_caps)

    @property
    def spec_function_bits(self) -> tuple[str, ...]:
        """Return decoded APK specFunctions bit labels."""
        return spec_function_bit_names(self.spec_functions)

    @property
    def color_capabilities(self) -> tuple[str, ...]:
        """Return decoded APK colorCap labels."""
        return color_capability_names(self.color_cap)

    @property
    def feature_keys(self) -> tuple[str, ...]:
        """Return sorted APK catalog extra-feature keys."""
        return tuple(sorted(str(key) for key in self.features))
