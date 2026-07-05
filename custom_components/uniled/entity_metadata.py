"""Home Assistant entity metadata helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import (
    CONF_ADDRESS,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_MESH_UUID,
    CONF_MODEL,
    CONF_TRANSPORT,
    DOMAIN,
    TRANSPORT_BLE,
    TRANSPORT_BLE_MESH,
    TRANSPORT_LAN,
    TRANSPORT_MANUAL,
)
from .core import EntityCategoryKind, FeatureSpec, PlatformKind

_OUTPUT_SCOPED_KEYS = {
    "audio_sensitivity",
    "chip_order",
    "effect",
    "effect_direction",
    "effect_length",
    "effect_speed",
}
_MESH_NODE_KEYS = {"effect", "effect_level", "effect_speed"}
_CONNECTION_BLUETOOTH = "bluetooth"
_CONNECTION_NETWORK_MAC = "mac"
_LEGACY_SP541E_ENTITY_SUFFIXES = {
    PlatformKind.LIGHT: {"main_light": "strip"},
    PlatformKind.NUMBER: {
        "audio_sensitivity": "sensitivity",
        "effect_speed": "effect_speed",
        "effect_length": "effect_length",
    },
    PlatformKind.SELECT: {
        "audio_input": "audio_input",
        "light_mode": "light_mode",
    },
    PlatformKind.SENSOR: {"effect_type": "effect_type"},
    PlatformKind.SWITCH: {
        "effect_direction": "effect_direction",
        "effect_loop": "effect_loop",
        "effect_play": "effect_play",
    },
}
_LEGACY_BLE_MASTER_CHANNEL_MODELS = {"SP601E", "SP602E", "SP608E"}
_LEGACY_BLE_LIGHT_SUFFIXES = {
    "main_light": "strip",
    "output_1_light": "strip",
    "output_2_light": "strip",
    "output_3_light": "strip",
    "output_4_light": "strip",
    "output_5_light": "strip",
    "output_6_light": "strip",
    "output_7_light": "strip",
    "output_8_light": "strip",
}
_LEGACY_BLE_ENTITY_SUFFIXES = {
    PlatformKind.LIGHT: _LEGACY_BLE_LIGHT_SUFFIXES,
    PlatformKind.NUMBER: {
        "audio_sensitivity": "sensitivity",
        "effect_speed": "effect_speed",
        "effect_length": "effect_length",
        "onoff_pixels": "onoff_pixels",
    },
    PlatformKind.SCENE: {
        f"scene_{scene_id}": f"scene_{scene_id}" for scene_id in range(9)
    },
    PlatformKind.SELECT: {
        "audio_input": "audio_input",
        "chip_order": "chip_order",
        "effect": "effect",
        "light_mode": "light_mode",
        "light_type": "light_type",
        "on_power": "on_power",
        "onoff_effect": "onoff_effect",
        "onoff_speed": "onoff_speed",
    },
    PlatformKind.SENSOR: {"effect_type": "effect_type"},
    PlatformKind.SWITCH: {
        "coexistence": "coexistence",
        "effect_direction": "effect_direction",
        "effect_loop": "effect_loop",
        "effect_play": "effect_play",
        "scene_loop": "scene_loop",
    },
}


def entry_identity(entry: Any) -> str:
    """Return the stable identity base for a Home Assistant config entry."""
    unique_id = str(getattr(entry, "unique_id", "") or "").strip()
    if unique_id:
        return unique_id

    data = getattr(entry, "data", {})
    if isinstance(data, Mapping):
        if identity := entry_data_identity(data):
            return identity

    return str(getattr(entry, "entry_id", "") or "").strip() or "unknown"


def entry_data_identity(data: Mapping[str, Any]) -> str | None:
    """Derive the setup unique ID from normalized config-entry data."""
    transport = str(data.get(CONF_TRANSPORT, "") or "").strip()
    model = str(data.get(CONF_MODEL, "") or "").strip()
    address = str(data.get(CONF_ADDRESS, "") or "").strip()
    host = str(data.get(CONF_HOST, "") or "").strip()
    device_id = str(data.get(CONF_DEVICE_ID, "") or "").strip()

    if transport in {"", TRANSPORT_BLE} and address:
        return f"ble:{address.casefold()}"
    if transport == TRANSPORT_LAN and _looks_like_mac_address(device_id):
        return device_id.casefold()
    if transport == TRANSPORT_LAN and host:
        return f"lan:{host.casefold()}"
    if transport == TRANSPORT_BLE_MESH:
        if device_id:
            return device_id
        mesh_uuid = _positive_int(data.get(CONF_MESH_UUID))
        if model and model != "RG4":
            if address:
                return f"ble_mesh:{address.casefold()}"
            if mesh_uuid:
                return f"ble_mesh:{model.casefold()}:{hex(mesh_uuid)}"
        if mesh_uuid:
            return f"zng_mesh_{hex(mesh_uuid)}"
        if address:
            return f"ble_mesh:{address.casefold()}"
    if transport == TRANSPORT_MANUAL and device_id:
        if model:
            return f"manual:{model}:{device_id.casefold()}"
        return f"manual:{device_id.casefold()}"

    if host:
        return f"lan:{host.casefold()}"
    if address:
        return f"ble:{address.casefold()}"
    if device_id:
        return device_id
    return None


def device_identifiers(entry: Any) -> set[tuple[str, str]]:
    """Return stable Home Assistant device-registry identifiers."""
    return {(DOMAIN, entry_identity(entry))}


def device_connections(entry: Any) -> set[tuple[str, str]]:
    """Return stable Home Assistant device-registry connections."""
    data = getattr(entry, "data", {})
    if not isinstance(data, Mapping):
        return set()

    transport = str(data.get(CONF_TRANSPORT, "") or "").strip()
    address = str(data.get(CONF_ADDRESS, "") or "").strip()
    if address and transport in {TRANSPORT_BLE, TRANSPORT_BLE_MESH}:
        return {(_CONNECTION_BLUETOOTH, address)}
    device_id = str(data.get(CONF_DEVICE_ID, "") or "").strip()
    if transport == TRANSPORT_LAN and _looks_like_mac_address(device_id):
        return {(_CONNECTION_NETWORK_MAC, device_id)}
    unique_id = str(getattr(entry, "unique_id", "") or "").strip()
    if transport == TRANSPORT_LAN and _looks_like_mac_address(unique_id):
        return {(_CONNECTION_NETWORK_MAC, unique_id)}
    return set()


def legacy_uniled_unique_id(entry: Any, feature: FeatureSpec) -> str | None:
    """Return an old-UniLED-compatible unique ID for migrated entities."""
    data = getattr(entry, "data", {})
    if not isinstance(data, Mapping):
        return None
    if unique_id := _legacy_direct_ble_unique_id(entry, data, feature):
        return unique_id
    if unique_id := _legacy_zengge_mesh_unique_id(entry, data, feature):
        return unique_id
    if str(data.get(CONF_MODEL, "") or "").strip() != "SP541E":
        return None
    if str(data.get(CONF_TRANSPORT, "") or "").strip() != TRANSPORT_LAN:
        return None

    suffix = _LEGACY_SP541E_ENTITY_SUFFIXES.get(feature.platform, {}).get(
        feature.key
    )
    if suffix is None:
        return None
    return f"_{entry_identity(entry)}_{suffix}"


def _legacy_direct_ble_unique_id(
    entry: Any,
    data: Mapping[str, Any],
    feature: FeatureSpec,
) -> str | None:
    if str(data.get(CONF_TRANSPORT, "") or "").strip() != TRANSPORT_BLE:
        return None

    base_unique_id = str(getattr(entry, "unique_id", "") or "").strip()
    if not _looks_like_mac_address(base_unique_id):
        return None

    suffix = _LEGACY_BLE_ENTITY_SUFFIXES.get(feature.platform, {}).get(
        feature.key
    )
    if suffix is None:
        return None

    model = str(data.get(CONF_MODEL, "") or "").strip()
    channel_identity = _legacy_ble_channel_identity(model, feature)
    if channel_identity:
        return f"_{base_unique_id}_{channel_identity}_{suffix}"
    return f"_{base_unique_id}_{suffix}"


def _legacy_ble_channel_identity(model: str, feature: FeatureSpec) -> str | None:
    if model not in _LEGACY_BLE_MASTER_CHANNEL_MODELS:
        return None
    channel = int(feature.channel)
    if channel == 0:
        return "master"
    return f"channel_{channel}"


def _legacy_zengge_mesh_unique_id(
    entry: Any,
    data: Mapping[str, Any],
    feature: FeatureSpec,
) -> str | None:
    if str(data.get(CONF_TRANSPORT, "") or "").strip() != TRANSPORT_BLE_MESH:
        return None
    if str(data.get(CONF_MODEL, "") or "").strip() != "RG4":
        return None
    if feature.implementation_hint not in {"zengge_mesh_node", "zengge_mesh_panel"}:
        return None
    if feature.platform is PlatformKind.LIGHT:
        pass
    elif (
        feature.platform is PlatformKind.SENSOR
        and feature.implementation_hint == "zengge_mesh_panel"
    ):
        pass
    else:
        return None

    node_id = int(feature.channel)
    if node_id <= 0:
        return None
    return f"_{entry_identity(entry)}_node_{node_id}"


def _looks_like_mac_address(value: str) -> bool:
    parts = value.split(":")
    if len(parts) != 6:
        return False
    return all(len(part) == 2 and _is_hex_byte(part) for part in parts)


def _is_hex_byte(value: str) -> bool:
    return all(char in "0123456789abcdefABCDEF" for char in value)


def feature_translation_key(feature: FeatureSpec) -> str | None:
    """Return the Home Assistant translation key for a planned feature."""
    if feature.implementation_hint == "zengge_mesh_panel":
        return "mesh_panel_status"

    if feature.platform is PlatformKind.LIGHT:
        if feature.key == "main_light":
            return None
        if feature.implementation_hint == "legacy_uniled_output":
            return "output_light"
        if feature.implementation_hint == "zengge_mesh_node":
            return "mesh_node_light"
        return feature.key

    if feature.platform is PlatformKind.SCENE and feature.key.startswith("scene_"):
        return "scene_slot"

    if feature.implementation_hint == "zengge_mesh_node":
        if feature.key in _MESH_NODE_KEYS:
            return f"mesh_node_{feature.key}"
        return feature.key

    if (
        feature.channel
        and feature.key in _OUTPUT_SCOPED_KEYS
        and feature.entity_category is not EntityCategoryKind.DIAGNOSTIC
    ):
        return f"output_{feature.key}"

    return feature.key


def feature_translation_placeholders(feature: FeatureSpec) -> dict[str, str] | None:
    """Return translation placeholders for dynamic feature names."""
    if feature.implementation_hint == "zengge_mesh_panel":
        return {"node": str(int(feature.channel))}

    if feature.platform is PlatformKind.SCENE and feature.key.startswith("scene_"):
        return {"slot": str(int(feature.channel) + 1)}

    if feature.implementation_hint == "zengge_mesh_node":
        return {"node": str(int(feature.channel))}

    if (
        feature.channel
        and (
            feature.implementation_hint == "legacy_uniled_output"
            or feature.key in _OUTPUT_SCOPED_KEYS
        )
        and feature.entity_category is not EntityCategoryKind.DIAGNOSTIC
    ):
        return {"output": str(int(feature.channel))}

    return None


def entity_registry_enabled_default(feature: FeatureSpec) -> bool:
    """Return the default enabled state for Home Assistant's entity registry."""
    return bool(feature.enabled_by_default)


def _positive_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value if value > 0 else None
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = int(text, 0)
    except ValueError:
        return None
    return parsed if parsed > 0 else None
