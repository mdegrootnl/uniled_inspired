"""Config flow for UniLED Next."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ADDRESS,
    CONF_CLOUD_COUNTRY,
    CONF_CLOUD_PASSWORD,
    CONF_CLOUD_SKIP,
    CONF_CLOUD_USERNAME,
    CONF_DEVICE_ID,
    CONF_DISCOVERY_CONFIDENCE,
    CONF_DISCOVERY_MATCH,
    CONF_DISCOVERY_SOURCE,
    CONF_HOST,
    CONF_MESH_NODE_ID,
    CONF_MESH_NODE_TYPE,
    CONF_MESH_NODE_WIRING,
    CONF_MESH_UUID,
    CONF_MODEL,
    CONF_MODEL_ID,
    CONF_TRANSPORT,
    CONFIG_ENTRY_MINOR_VERSION,
    CONFIG_ENTRY_VERSION,
    DOMAIN,
    TRANSPORT_BLE,
    TRANSPORT_BLE_MESH,
    TRANSPORT_LAN,
    TRANSPORT_MANUAL,
)
from .core import default_catalog
from .core.protocols import (
    MAGICHUE_COUNTRY_SERVERS,
    MAGICHUE_DEFAULT_COUNTRY,
    ZenggeCloudError,
    async_fetch_zengge_cloud_meshes,
)
from .setup_data import (
    SetupDataError,
    SetupEntryData,
    bluetooth_setup_entry_data_from_discovery,
    lan_setup_entry_data_from_discovery,
    manual_setup_entry_data,
    manual_setup_model,
    reconfigure_entry_data,
    setup_entry_compatibility_unique_ids,
    setup_entry_requires_discovery_confirmation,
    zengge_cloud_import_supported,
    zengge_cloud_setup_entry_data,
    zengge_cloud_update_entry_data,
)

_RECONFIGURE_FIELDS = (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_ADDRESS,
    CONF_MESH_UUID,
    CONF_MESH_NODE_ID,
    CONF_MESH_NODE_TYPE,
    CONF_MESH_NODE_WIRING,
)


class UniLEDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a UniLED config flow."""

    VERSION = CONFIG_ENTRY_VERSION
    MINOR_VERSION = CONFIG_ENTRY_MINOR_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the UniLED options flow."""
        return UniLEDOptionsFlow()

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle entry reconfiguration."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        catalog = await _async_default_catalog(self.hass)

        if user_input is not None:
            updates = {
                key: user_input[key]
                for key in _RECONFIGURE_FIELDS
                if key in user_input
            }
            try:
                data = reconfigure_entry_data(
                    catalog,
                    entry.data,
                    **updates,
                )
            except SetupDataError as ex:
                errors[ex.field] = ex.reason
            else:
                if entry.unique_id is not None:
                    await self.async_set_unique_id(entry.unique_id)
                    self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data=data,
                    reload_even_if_entry_is_unchanged=False,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_reconfigure_schema(entry.data),
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}
        catalog = await _async_default_catalog(self.hass)

        if user_input is not None:
            try:
                model = manual_setup_model(
                    catalog,
                    name=str(user_input.get(CONF_MODEL, "")),
                    model_id=user_input.get(CONF_MODEL_ID),
                )
                setup = manual_setup_entry_data(
                    model,
                    transport=str(user_input.get(CONF_TRANSPORT, TRANSPORT_MANUAL)),
                    device_id=str(user_input.get(CONF_DEVICE_ID, "")),
                    host=str(user_input.get(CONF_HOST, "")),
                    address=str(user_input.get(CONF_ADDRESS, "")),
                    mesh_uuid=user_input.get(CONF_MESH_UUID),
                    mesh_node_id=user_input.get(CONF_MESH_NODE_ID),
                    mesh_node_type=user_input.get(CONF_MESH_NODE_TYPE),
                    mesh_node_wiring=user_input.get(CONF_MESH_NODE_WIRING),
                )
            except SetupDataError as ex:
                errors[ex.field] = ex.reason
            else:
                if abort := self._async_abort_if_compat_unique_id_configured(setup):
                    return abort
                await self.async_set_unique_id(
                    setup.unique_id,
                    raise_on_progress=False,
                )
                self._abort_if_unique_id_configured()
                if (
                    setup.data.get(CONF_TRANSPORT) == TRANSPORT_BLE_MESH
                    and setup.data.get(CONF_MESH_UUID)
                    and zengge_cloud_import_supported(model)
                ):
                    self._pending_zengge_cloud_setup = setup
                    return await self.async_step_zengge_cloud()
                return self.async_create_entry(
                    title=setup.title,
                    data=setup.data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MODEL): vol.In(
                        sorted(catalog.user_facing_names)
                    ),
                    vol.Optional(CONF_MODEL_ID): str,
                    vol.Required(
                        CONF_TRANSPORT,
                        default=TRANSPORT_MANUAL,
                    ): vol.In(
                        (
                            TRANSPORT_MANUAL,
                            TRANSPORT_BLE,
                            TRANSPORT_LAN,
                            TRANSPORT_BLE_MESH,
                        )
                    ),
                    vol.Optional(CONF_DEVICE_ID): str,
                    vol.Optional(CONF_HOST): str,
                    vol.Optional(CONF_ADDRESS): str,
                    vol.Optional(CONF_MESH_UUID): str,
                    vol.Optional(CONF_MESH_NODE_ID): str,
                    vol.Optional(CONF_MESH_NODE_TYPE): str,
                    vol.Optional(CONF_MESH_NODE_WIRING): str,
                }
            ),
            errors=errors,
        )

    async def async_step_bluetooth(self, discovery_info: Any) -> FlowResult:
        """Handle Bluetooth discovery."""
        catalog = await _async_default_catalog(self.hass)
        try:
            setup = bluetooth_setup_entry_data_from_discovery(catalog, discovery_info)
        except SetupDataError as ex:
            return self.async_abort(reason=ex.reason)

        if abort := self._async_abort_if_compat_unique_id_configured(setup):
            return abort
        await self.async_set_unique_id(setup.unique_id, raise_on_progress=False)
        self._abort_if_unique_id_configured()
        if setup_entry_requires_discovery_confirmation(setup):
            self._pending_bluetooth_confirmation_setup = setup
            return await self.async_step_bluetooth_confirm()

        model = catalog.resolve_name(str(setup.data.get(CONF_MODEL, "")))
        if (
            setup.data.get(CONF_TRANSPORT) == TRANSPORT_BLE_MESH
            and setup.data.get(CONF_MESH_UUID)
            and model is not None
            and zengge_cloud_import_supported(model)
        ):
            self._pending_zengge_cloud_setup = setup
            return await self.async_step_zengge_cloud()

        return self.async_create_entry(
            title=setup.title,
            data=setup.data,
        )

    async def async_step_bluetooth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Confirm catalog-only Bluetooth discovery before entry creation."""
        setup = getattr(self, "_pending_bluetooth_confirmation_setup", None)
        if setup is None:
            return self.async_abort(reason="unknown_model")

        if user_input is not None:
            if abort := await self._async_abort_if_setup_unique_id_configured(setup):
                return abort
            return self.async_create_entry(
                title=setup.title,
                data=setup.data,
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "model": str(setup.data.get(CONF_MODEL, "")),
                "address": str(setup.data.get(CONF_ADDRESS, "")),
                "discovery_source": str(setup.data.get(CONF_DISCOVERY_SOURCE, "")),
                "discovery_match": str(setup.data.get(CONF_DISCOVERY_MATCH, "")),
                "discovery_confidence": str(
                    setup.data.get(CONF_DISCOVERY_CONFIDENCE, "")
                ),
            },
        )

    async def async_step_discovery(self, discovery_info: Any) -> FlowResult:
        """Handle LAN discovery."""
        catalog = await _async_default_catalog(self.hass)
        try:
            setup = lan_setup_entry_data_from_discovery(catalog, discovery_info)
        except SetupDataError as ex:
            return self.async_abort(reason=ex.reason)

        if abort := self._async_abort_if_compat_unique_id_configured(setup):
            return abort
        await self.async_set_unique_id(setup.unique_id, raise_on_progress=False)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=setup.title,
            data=setup.data,
        )

    async def async_step_zengge_cloud(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Optionally import MagicHue/Zengge cloud mesh metadata."""
        setup = getattr(self, "_pending_zengge_cloud_setup", None)
        if setup is None:
            return self.async_abort(reason="mesh_not_supported")

        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_CLOUD_SKIP):
                if abort := await self._async_abort_if_setup_unique_id_configured(
                    setup
                ):
                    return abort
                return self.async_create_entry(title=setup.title, data=setup.data)

            username = str(user_input.get(CONF_CLOUD_USERNAME, "")).strip()
            password = str(user_input.get(CONF_CLOUD_PASSWORD, "")).strip()
            country = str(
                user_input.get(CONF_CLOUD_COUNTRY, MAGICHUE_DEFAULT_COUNTRY)
            ).strip()
            if not username:
                errors[CONF_CLOUD_USERNAME] = "required"
            if not password:
                errors[CONF_CLOUD_PASSWORD] = "required"

            if not errors:
                result = await self._async_import_zengge_cloud(
                    setup,
                    username=username,
                    password=password,
                    country=country,
                )
                if "type" in result:
                    return result
                errors = result

        return self.async_show_form(
            step_id="zengge_cloud",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_CLOUD_SKIP, default=False): bool,
                    vol.Optional(CONF_CLOUD_USERNAME): str,
                    vol.Optional(CONF_CLOUD_PASSWORD): str,
                    vol.Optional(
                        CONF_CLOUD_COUNTRY,
                        default=MAGICHUE_DEFAULT_COUNTRY,
                    ): vol.In(sorted(MAGICHUE_COUNTRY_SERVERS)),
                }
            ),
            description_placeholders={
                "mesh_uuid": hex(int(setup.data.get(CONF_MESH_UUID, 0))),
            },
            errors=errors,
        )

    async def _async_import_zengge_cloud(
        self,
        setup: SetupEntryData,
        *,
        username: str,
        password: str,
        country: str,
    ) -> FlowResult | dict[str, str]:
        catalog = await _async_default_catalog(self.hass)
        model = catalog.resolve_name(str(setup.data[CONF_MODEL]))
        if model is None or not zengge_cloud_import_supported(model):
            return {"base": "mesh_not_supported"}

        try:
            meshes = await async_fetch_zengge_cloud_meshes(
                self._async_magichue_request,
                username=username,
                password=password,
                country=country,
                mesh_uuid=int(setup.data[CONF_MESH_UUID]),
                timestamp=str(int(time.time() * 1000)),
            )
        except ZenggeCloudError as ex:
            if "login" in str(ex).lower():
                return {CONF_CLOUD_PASSWORD: "mesh_login"}
            return {"base": "mesh_fetch"}

        meshes = tuple(mesh for mesh in meshes if mesh.nodes)
        if not meshes:
            return {"base": "mesh_no_devices"}

        cloud_setup = zengge_cloud_setup_entry_data(
            model,
            meshes[0],
            address=str(setup.data.get(CONF_ADDRESS, "")),
        )
        if abort := await self._async_abort_if_setup_unique_id_configured(cloud_setup):
            return abort
        return self.async_create_entry(
            title=cloud_setup.title,
            data=cloud_setup.data,
        )

    async def _async_magichue_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await _async_magichue_request(
            self.hass,
            method,
            url,
            headers=headers,
            json=json,
        )

    def _async_abort_if_compat_unique_id_configured(
        self,
        setup: SetupEntryData,
    ) -> FlowResult | None:
        """Abort when an existing legacy unique ID represents this setup."""
        current_ids = {
            str(unique_id).casefold()
            for unique_id in self._async_current_ids()
            if unique_id
        }
        for unique_id in setup_entry_compatibility_unique_ids(setup):
            if unique_id.casefold() in current_ids:
                return self.async_abort(reason="already_configured")
        return None

    async def _async_abort_if_setup_unique_id_configured(
        self,
        setup: SetupEntryData,
    ) -> FlowResult | None:
        """Abort when this setup or a legacy-compatible ID already exists."""
        if abort := self._async_abort_if_compat_unique_id_configured(setup):
            return abort
        await self.async_set_unique_id(setup.unique_id, raise_on_progress=False)
        self._abort_if_unique_id_configured()
        return None


class UniLEDOptionsFlow(config_entries.OptionsFlow):
    """Handle UniLED options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage entry options."""
        if _entry_mesh_uuid(self.config_entry.data) is None:
            return self.async_abort(reason="mesh_not_supported")
        catalog = await _async_default_catalog(self.hass)
        model = _entry_model(catalog, self.config_entry.data)
        if model is None or not zengge_cloud_import_supported(model):
            return self.async_abort(reason="mesh_not_supported")
        return await self.async_step_zengge_cloud(user_input)

    async def async_step_zengge_cloud(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Refresh MagicHue/Zengge cloud mesh metadata for this entry."""
        mesh_uuid = _entry_mesh_uuid(self.config_entry.data)
        if mesh_uuid is None:
            return self.async_abort(reason="mesh_not_supported")
        catalog = await _async_default_catalog(self.hass)
        model = _entry_model(catalog, self.config_entry.data)
        if model is None or not zengge_cloud_import_supported(model):
            return self.async_abort(reason="mesh_not_supported")

        errors: dict[str, str] = {}
        if user_input is not None:
            username = str(user_input.get(CONF_CLOUD_USERNAME, "")).strip()
            password = str(user_input.get(CONF_CLOUD_PASSWORD, "")).strip()
            country = str(
                user_input.get(CONF_CLOUD_COUNTRY, MAGICHUE_DEFAULT_COUNTRY)
            ).strip()
            if not username:
                errors[CONF_CLOUD_USERNAME] = "required"
            if not password:
                errors[CONF_CLOUD_PASSWORD] = "required"

            if not errors:
                result = await self._async_import_zengge_cloud(
                    username=username,
                    password=password,
                    country=country,
                    mesh_uuid=mesh_uuid,
                )
                if "type" in result:
                    return result
                errors = result

        return self.async_show_form(
            step_id="zengge_cloud",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLOUD_USERNAME): str,
                    vol.Required(CONF_CLOUD_PASSWORD): str,
                    vol.Required(
                        CONF_CLOUD_COUNTRY,
                        default=MAGICHUE_DEFAULT_COUNTRY,
                    ): vol.In(sorted(MAGICHUE_COUNTRY_SERVERS)),
                }
            ),
            description_placeholders={"mesh_uuid": hex(mesh_uuid)},
            errors=errors,
        )

    async def _async_import_zengge_cloud(
        self,
        *,
        username: str,
        password: str,
        country: str,
        mesh_uuid: int,
    ) -> FlowResult | dict[str, str]:
        catalog = await _async_default_catalog(self.hass)
        model = catalog.resolve_name(str(self.config_entry.data.get(CONF_MODEL, "")))
        if model is None or not zengge_cloud_import_supported(model):
            return {"base": "mesh_not_supported"}

        try:
            meshes = await async_fetch_zengge_cloud_meshes(
                self._async_magichue_request,
                username=username,
                password=password,
                country=country,
                mesh_uuid=mesh_uuid,
                timestamp=str(int(time.time() * 1000)),
            )
        except ZenggeCloudError as ex:
            if "login" in str(ex).lower():
                return {CONF_CLOUD_PASSWORD: "mesh_login"}
            return {"base": "mesh_fetch"}

        meshes = tuple(mesh for mesh in meshes if mesh.nodes)
        if not meshes:
            return {"base": "mesh_no_devices"}

        try:
            entry_data = zengge_cloud_update_entry_data(
                self.config_entry.data,
                meshes[0],
            )
        except SetupDataError as ex:
            return {ex.field: ex.reason}

        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=entry_data,
        )
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)
        return self.async_create_entry(
            title="",
            data=dict(self.config_entry.options),
        )

    async def _async_magichue_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await _async_magichue_request(
            self.hass,
            method,
            url,
            headers=headers,
            json=json,
        )


def _entry_mesh_uuid(entry_data: dict[str, Any]) -> int | None:
    if entry_data.get(CONF_TRANSPORT) != TRANSPORT_BLE_MESH:
        return None
    try:
        mesh_uuid = int(entry_data.get(CONF_MESH_UUID, 0))
    except (TypeError, ValueError):
        return None
    if mesh_uuid <= 0:
        return None
    return mesh_uuid


async def _async_default_catalog(hass: Any) -> Any:
    """Load the bundled catalog outside Home Assistant's event loop."""
    return await hass.async_add_executor_job(default_catalog)


def _entry_model(catalog: Any, entry_data: Mapping[str, Any]) -> Any | None:
    model_name = str(entry_data.get(CONF_MODEL, "")).strip()
    if not model_name:
        return None
    return catalog.resolve_name(model_name)


def _reconfigure_schema(entry_data: Mapping[str, Any]) -> vol.Schema:
    fields: dict[Any, Any] = {}
    transport = _entry_transport(entry_data)
    if transport == TRANSPORT_BLE:
        fields[
            vol.Required(CONF_ADDRESS, default=_entry_text(entry_data, CONF_ADDRESS))
        ] = str
    elif transport == TRANSPORT_LAN:
        fields[
            vol.Required(
                CONF_HOST,
                default=_entry_text(entry_data, CONF_HOST, "ip_address", CONF_ADDRESS),
            )
        ] = str
        fields[
            vol.Optional(
                CONF_DEVICE_ID,
                default=_entry_text(entry_data, CONF_DEVICE_ID),
            )
        ] = str
    elif transport == TRANSPORT_BLE_MESH:
        fields[
            vol.Optional(CONF_ADDRESS, default=_entry_text(entry_data, CONF_ADDRESS))
        ] = str
        fields[
            vol.Optional(
                CONF_MESH_UUID,
                default=_entry_int_text(entry_data, CONF_MESH_UUID),
            )
        ] = str
        fields[
            vol.Optional(
                CONF_MESH_NODE_ID,
                default=_entry_int_text(entry_data, CONF_MESH_NODE_ID),
            )
        ] = str
        fields[
            vol.Optional(
                CONF_MESH_NODE_TYPE,
                default=_entry_int_text(entry_data, CONF_MESH_NODE_TYPE),
            )
        ] = str
        fields[
            vol.Optional(
                CONF_MESH_NODE_WIRING,
                default=_entry_int_text(entry_data, CONF_MESH_NODE_WIRING),
            )
        ] = str
    else:
        fields[
            vol.Required(
                CONF_DEVICE_ID,
                default=_entry_text(entry_data, CONF_DEVICE_ID, CONF_ADDRESS),
            )
        ] = str
    return vol.Schema(fields)


def _entry_transport(entry_data: Mapping[str, Any]) -> str:
    transport = str(entry_data.get(CONF_TRANSPORT, "")).strip()
    if transport == "net":
        return TRANSPORT_LAN
    if transport == "zng":
        return TRANSPORT_BLE_MESH
    if transport:
        return transport
    if entry_data.get(CONF_MESH_UUID) is not None or entry_data.get("mesh_id"):
        return TRANSPORT_BLE_MESH
    if _entry_text(entry_data, CONF_HOST, "ip_address"):
        return TRANSPORT_LAN
    if _entry_text(entry_data, CONF_ADDRESS):
        return TRANSPORT_BLE
    return TRANSPORT_MANUAL


def _entry_text(entry_data: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(entry_data.get(key, "")).strip()
        if value:
            return value
    return ""


def _entry_int_text(entry_data: Mapping[str, Any], key: str) -> str:
    value = entry_data.get(key)
    if isinstance(value, int):
        return hex(value)
    return str(value or "").strip()


async def _async_magichue_request(
    hass: Any,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    session = async_get_clientsession(hass)
    async with session.request(
        method,
        url,
        headers=headers,
        json=json,
    ) as response:
        if response.status != 200:
            raise ZenggeCloudError(f"HTTP {response.status}")
        payload = await response.json()
    if not isinstance(payload, dict):
        raise ZenggeCloudError("MagicHue response was not a JSON object")
    return payload
