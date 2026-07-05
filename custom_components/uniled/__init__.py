"""UniLED Next integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .const import (
    CONF_ADDRESS,
    CONF_HOST,
    CONF_TRANSPORT,
    CONFIG_ENTRY_MINOR_VERSION,
    CONFIG_ENTRY_VERSION,
    DOMAIN,
    TRANSPORT_BLE,
    TRANSPORT_BLE_MESH,
    TRANSPORT_LAN,
)
from .core import DeviceState, ProtocolFamily, default_catalog
from .runtime import RuntimeSetupError, UniLEDRuntime, build_runtime
from .setup_data import SetupDataError, migrate_legacy_entry_data

_ISSUE_MIGRATION_FAILED = "migration_failed"
_ISSUE_SETUP_INVALID = "setup_invalid"
SERVICE_SET_STATE = "set_state"

PLATFORMS: list[str] = [
    "sensor",
    "light",
    "number",
    "select",
    "switch",
    "scene",
    "button",
]


if TYPE_CHECKING:
    type UniLEDConfigEntry = ConfigEntry[UniLEDRuntime]
else:
    type UniLEDConfigEntry = Any


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up integration-wide UniLED services."""
    import voluptuous as vol
    from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
    from homeassistant.helpers import config_validation as cv
    from homeassistant.helpers import service

    from .lan import async_start_spnet_discovery

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_SET_STATE,
        entity_domain=LIGHT_DOMAIN,
        schema=_legacy_set_state_schema(cv, vol),
        func="async_set_uniled_state",
    )
    await hass.async_add_executor_job(default_catalog)
    async_start_spnet_discovery(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: UniLEDConfigEntry) -> bool:
    """Set up UniLED from a config entry."""
    from .coordinator import UniLEDCoordinator

    catalog = await hass.async_add_executor_job(default_catalog)
    try:
        runtime = build_runtime(entry.data, catalog=catalog)
    except RuntimeSetupError as ex:
        _create_config_entry_issue(
            hass,
            entry,
            _ISSUE_SETUP_INVALID,
            field=ex.field,
            reason=ex.reason,
        )
        return False
    _delete_config_entry_issue(hass, entry, _ISSUE_SETUP_INVALID)
    coordinator = UniLEDCoordinator(hass, entry, runtime)
    runtime.coordinator = coordinator
    try:
        _attach_runtime_transports(
            hass,
            entry.data,
            runtime,
            notification_callback=coordinator.apply_notification,
            mesh_notification_callback=coordinator.apply_mesh_notification,
        )
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = runtime
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        await runtime.async_close()
        if getattr(entry, "runtime_data", None) is runtime:
            entry.runtime_data = None
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: UniLEDConfigEntry) -> bool:
    """Unload a UniLED config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_close()
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: UniLEDConfigEntry) -> bool:
    """Migrate legacy UniLED config-entry data into the new schema."""
    catalog = await hass.async_add_executor_job(default_catalog)
    try:
        data = migrate_legacy_entry_data(catalog, entry.data)
    except SetupDataError as ex:
        _create_config_entry_issue(
            hass,
            entry,
            _ISSUE_MIGRATION_FAILED,
            field=ex.field,
            reason=ex.reason,
        )
        return False
    _delete_config_entry_issue(hass, entry, _ISSUE_MIGRATION_FAILED)

    hass.config_entries.async_update_entry(
        entry,
        data=data,
        version=CONFIG_ENTRY_VERSION,
        minor_version=CONFIG_ENTRY_MINOR_VERSION,
    )
    return True


def _legacy_set_state_schema(cv: Any, vol: Any) -> dict[Any, Any]:
    """Return the compatibility schema for old UniLED's light service."""
    byte = vol.All(vol.Coerce(int), vol.Clamp(min=0, max=255))
    return {
        vol.Optional("power"): cv.boolean,
        vol.Optional("effect"): str,
        vol.Optional("effect_speed"): byte,
        vol.Optional("effect_length"): byte,
        vol.Optional("effect_direction"): cv.boolean,
        vol.Optional("effect_loop"): cv.boolean,
        vol.Optional("effect_play"): cv.boolean,
        vol.Optional("sensitivity"): byte,
        vol.Optional("rgb_color"): vol.All(
            vol.Coerce(tuple),
            vol.ExactSequence((byte,) * 3),
        ),
        vol.Optional("rgbw_color"): vol.All(
            vol.Coerce(tuple),
            vol.ExactSequence((byte,) * 4),
        ),
        vol.Optional("rgbww_color"): vol.All(
            vol.Coerce(tuple),
            vol.ExactSequence((byte,) * 5),
        ),
        vol.Optional("white"): byte,
        vol.Optional("brightness"): byte,
        vol.Optional("transition"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("color_temp_kelvin"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    }


def _create_config_entry_issue(
    hass: HomeAssistant,
    entry: UniLEDConfigEntry,
    issue_key: str,
    *,
    field: str,
    reason: str,
) -> None:
    """Create a Home Assistant repair issue for unsafe entry data."""
    from homeassistant.helpers import issue_registry as ir

    issue_id = _config_entry_issue_id(issue_key, entry)
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        data={
            "entry_id": str(getattr(entry, "entry_id", "")),
            "field": field,
            "reason": reason,
        },
        is_fixable=False,
        severity=ir.IssueSeverity.ERROR,
        translation_key=issue_key,
        translation_placeholders=_config_entry_issue_placeholders(
            entry,
            field=field,
            reason=reason,
        ),
    )


def _delete_config_entry_issue(
    hass: HomeAssistant,
    entry: UniLEDConfigEntry,
    issue_key: str,
) -> None:
    """Delete a config-entry repair issue after the entry becomes valid."""
    from homeassistant.helpers import issue_registry as ir

    ir.async_delete_issue(hass, DOMAIN, _config_entry_issue_id(issue_key, entry))


def _config_entry_issue_id(issue_key: str, entry: UniLEDConfigEntry) -> str:
    """Return the stable repair issue ID for a config entry."""
    entry_id = str(getattr(entry, "entry_id", "")).strip() or "unknown"
    return f"{issue_key}_{entry_id}"


def _config_entry_issue_placeholders(
    entry: UniLEDConfigEntry,
    *,
    field: str,
    reason: str,
) -> dict[str, str]:
    """Return sanitized repair translation placeholders."""
    title = str(getattr(entry, "title", "")).strip() or "UniLED entry"
    return {
        "field": field,
        "reason": reason,
        "title": title,
    }


def _attach_runtime_transports(
    hass: HomeAssistant,
    entry_data: dict[str, Any],
    runtime: UniLEDRuntime,
    *,
    notification_callback: Callable[[bytes], DeviceState | None],
    mesh_notification_callback: Callable[[bytes], DeviceState | None],
) -> str | None:
    """Attach safe runtime transports based on the resolved model."""
    from .bluetooth import (
        UniLEDBLETransport,
        UniLEDZenggeMeshTransport,
        ble_device_name,
    )
    from .core.protocols import SPTechLANProtocol
    from .core.transports import (
        ble_profile_for_model,
        lan_profile_for_model,
        mesh_profile_for_model,
    )
    from .lan import UniLEDLANTransport, lan_device_name

    address = str(entry_data.get(CONF_ADDRESS, "")).strip()
    host = str(entry_data.get(CONF_HOST, "")).strip()
    transport_kind = str(entry_data.get(CONF_TRANSPORT, "")).strip()
    if (
        transport_kind in {"", TRANSPORT_BLE}
        and runtime.protocol_ready
        and address
        and (profile := ble_profile_for_model(runtime.model)) is not None
    ):
        runtime.attach_transport(
            UniLEDBLETransport(
                hass,
                address=address,
                name=ble_device_name(runtime.model.name, address),
                profile=profile,
                notification_callback=notification_callback,
            )
        )
        return "ble"

    if (
        transport_kind in {"", TRANSPORT_BLE_MESH}
        and runtime.model.family is ProtocolFamily.ZENGGE_MESH
        and address
        and (profile := mesh_profile_for_model(runtime.model)) is not None
    ):
        runtime.attach_zengge_mesh_transport(
            UniLEDZenggeMeshTransport(
                hass,
                address=address,
                name=ble_device_name(runtime.model.name, address),
                profile=profile,
                notification_callback=mesh_notification_callback,
            ),
            address=address,
        )
        return "ble_mesh"

    if (
        transport_kind == TRANSPORT_LAN
        and host
        and (profile := lan_profile_for_model(runtime.model)) is not None
    ):
        transport = UniLEDLANTransport(
            hass,
            host=host,
            name=lan_device_name(runtime.model.name, host),
            profile=profile,
        )
        if profile.command_protocol_known and runtime.model.name == "SP541E":
            runtime.protocol = SPTechLANProtocol(model_name=runtime.model.name)
            runtime.lan_profile = profile
            runtime.attach_transport(transport)
            runtime.state.diagnostics.update(
                {
                    "lan_transport_ready": True,
                    "lan_manual_host_configured": True,
                    "lan_protocol": "sptech",
                }
            )
        else:
            runtime.attach_lan_transport(
                transport,
                host=host,
                profile=profile,
            )
        return "lan"

    return None
