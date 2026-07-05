"""Home Assistant-independent config-entry data helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .const import (
    CONF_ADDRESS,
    CONF_DEVICE_ID,
    CONF_DISCOVERY_CONFIDENCE,
    CONF_DISCOVERY_MATCH,
    CONF_DISCOVERY_RESPONSE_HEX,
    CONF_DISCOVERY_SOURCE,
    CONF_HOST,
    CONF_MESH_KEY,
    CONF_MESH_LTK,
    CONF_MESH_NODE_ID,
    CONF_MESH_NODE_TYPE,
    CONF_MESH_NODE_WIRING,
    CONF_MESH_NODES,
    CONF_MESH_PASSWORD,
    CONF_MESH_PLACE_ID,
    CONF_MESH_PLACE_NAME,
    CONF_MESH_UUID,
    CONF_MODEL,
    CONF_MODEL_ID,
    CONF_TRANSPORT,
    DISCOVERY_CONFIDENCE_DISCOVERED_ONLY,
    DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
    DISCOVERY_CONFIDENCE_VERIFIED,
    DISCOVERY_MATCH_EXACT_LABEL,
    DISCOVERY_MATCH_SAFE_SUFFIX,
    DISCOVERY_MATCH_SPNET_MODEL_ID,
    DISCOVERY_MATCH_TELINK_MESH,
    DISCOVERY_SOURCE_BLUETOOTH,
    DISCOVERY_SOURCE_LAN,
    TRANSPORT_BLE,
    TRANSPORT_BLE_MESH,
    TRANSPORT_LAN,
    TRANSPORT_MANUAL,
)
from .core import (
    CatalogModel,
    ModelCatalog,
    ProtocolFamily,
    TransportKind,
    protocol_for_model,
)
from .core.protocols import ZenggeCloudMesh
from .core.transports import (
    BLEMeshAdvertisement,
    lan_profile_for_model,
    mesh_profile_for_model,
    parse_spnet_discovery_response,
    telink_mesh_advertisement,
)

_UNSET = object()
_DISCOVERY_NAME_SUFFIX_SEPARATORS = (" ", "-", "_", "(", "[", "#", ":")


class SetupDataError(ValueError):
    """Raised when config-entry data cannot be safely created."""

    def __init__(self, field: str, reason: str) -> None:
        """Store the field and error translation reason."""
        super().__init__(reason)
        self.field = field
        self.reason = reason


@dataclass(frozen=True, slots=True)
class SetupEntryData:
    """Resolved data needed to create a Home Assistant config entry."""

    unique_id: str
    title: str
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class BluetoothDiscoveryEvidence:
    """Resolved Bluetooth discovery evidence before config-entry creation."""

    model: CatalogModel
    match: str
    confidence: str

    def entry_data(self) -> dict[str, str]:
        """Return config-entry data fields describing discovery provenance."""
        return {
            CONF_DISCOVERY_SOURCE: DISCOVERY_SOURCE_BLUETOOTH,
            CONF_DISCOVERY_MATCH: self.match,
            CONF_DISCOVERY_CONFIDENCE: self.confidence,
        }


def bluetooth_setup_entry_data(
    catalog: ModelCatalog,
    *,
    name: str,
    address: str = "",
    manufacturer_data: Mapping[int, bytes | bytearray] | None = None,
    connectable: bool | None = None,
) -> SetupEntryData:
    """Build validated config-entry data for Bluetooth discovery."""
    name = str(name).strip()
    address = str(address).strip()
    if connectable is False:
        raise SetupDataError(CONF_ADDRESS, "not_connectable")

    mesh_advert = telink_mesh_advertisement(manufacturer_data or {})
    evidence = bluetooth_discovery_evidence(
        catalog,
        name=name,
        mesh_advert=mesh_advert,
    )

    if evidence is None or not evidence.model.is_user_facing:
        raise SetupDataError(CONF_MODEL, "unknown_model")
    model = evidence.model

    if TransportKind.BLE_MESH in model.transports:
        address = _normalized_address(address)
        return _ble_mesh_setup_entry_data(
            model,
            address=address,
            mesh_advert=mesh_advert,
            discovery=evidence.entry_data(),
        )
    if TransportKind.BLE not in model.transports:
        raise SetupDataError(CONF_TRANSPORT, "unsupported_ble_transport")

    address = _normalized_address(address)
    unique_id = f"ble:{address.casefold()}"
    return SetupEntryData(
        unique_id=unique_id,
        title=model.friendly_name,
        data={
            CONF_MODEL: model.name,
            CONF_MODEL_ID: model.model_id,
            CONF_ADDRESS: address,
            CONF_TRANSPORT: TRANSPORT_BLE,
            **evidence.entry_data(),
        },
    )


def bluetooth_setup_entry_data_from_discovery(
    catalog: ModelCatalog,
    discovery_info: Any,
) -> SetupEntryData:
    """Build setup data from a Home Assistant Bluetooth discovery object."""
    name = str(
        _discovery_value(discovery_info, "name")
        or _discovery_value(discovery_info, "local_name")
        or ""
    ).strip()
    manufacturer_data = _discovery_value(discovery_info, "manufacturer_data")
    connectable = _discovery_value(discovery_info, "connectable")
    return bluetooth_setup_entry_data(
        catalog,
        name=name,
        address=str(_discovery_value(discovery_info, "address") or "").strip(),
        manufacturer_data=manufacturer_data
        if isinstance(manufacturer_data, Mapping)
        else None,
        connectable=connectable if isinstance(connectable, bool) else None,
    )


def setup_entry_requires_discovery_confirmation(setup: SetupEntryData) -> bool:
    """Return whether discovery evidence is too weak to auto-create an entry."""
    return (
        setup.data.get(CONF_DISCOVERY_CONFIDENCE)
        == DISCOVERY_CONFIDENCE_DISCOVERED_ONLY
    )


def setup_entry_compatibility_unique_ids(setup: SetupEntryData) -> tuple[str, ...]:
    """Return legacy config-entry IDs that should also block this setup."""
    transport = setup.data.get(CONF_TRANSPORT)
    if transport == TRANSPORT_LAN:
        device_id = str(setup.data.get(CONF_DEVICE_ID, "")).strip()
        if not _looks_like_mac_address(device_id):
            return ()
        candidates = [device_id]
        lowered = device_id.casefold()
        if lowered != device_id:
            candidates.append(lowered)
        return tuple(candidates)

    if transport != TRANSPORT_BLE:
        return ()

    address = str(setup.data.get(CONF_ADDRESS, "")).strip()
    if not address:
        return ()

    candidates = [address]
    lowered = address.casefold()
    if lowered != address:
        candidates.append(lowered)
    return tuple(candidates)


def bluetooth_discovery_evidence(
    catalog: ModelCatalog,
    *,
    name: str,
    mesh_advert: BLEMeshAdvertisement | None = None,
) -> BluetoothDiscoveryEvidence | None:
    """Resolve Bluetooth advertisement evidence to a conservative model match."""
    match = _bluetooth_discovery_match(catalog, str(name).strip())
    if match is None and mesh_advert is not None:
        model = catalog.resolve_name("RG4")
        if model is not None:
            return BluetoothDiscoveryEvidence(
                model=model,
                match=DISCOVERY_MATCH_TELINK_MESH,
                confidence=_bluetooth_discovery_confidence(model),
            )
        return None
    if match is None:
        return None

    model, match_type = match
    return BluetoothDiscoveryEvidence(
        model=model,
        match=match_type,
        confidence=_bluetooth_discovery_confidence(model),
    )


def lan_setup_entry_data_from_spnet_response(
    catalog: ModelCatalog,
    response: bytes,
    *,
    source: str = "",
) -> SetupEntryData:
    """Build setup data from a verified SPNet LAN discovery response."""
    parsed = parse_spnet_discovery_response(response, source=str(source).strip())
    if parsed is None:
        raise SetupDataError(CONF_MODEL, "unknown_model")
    if parsed.model_id is None or parsed.model_id not in catalog.model_ids:
        raise SetupDataError(CONF_MODEL_ID, "unknown_model_id")

    model = catalog.get_model_id(parsed.model_id)
    if not model.is_user_facing:
        raise SetupDataError(CONF_MODEL, "unknown_model")
    profile = lan_profile_for_model(model)
    if (
        profile is None
        or not profile.command_protocol_known
        or model.name != "SP541E"
    ):
        raise SetupDataError(CONF_TRANSPORT, "unsupported_lan_transport")

    host = _normalized_host(parsed.source or "")
    device_id = parsed.mac_address or host
    unique_id = device_id.casefold() if parsed.mac_address else f"lan:{host.casefold()}"
    return SetupEntryData(
        unique_id=unique_id,
        title=f"{model.friendly_name} {host}",
        data={
            CONF_MODEL: model.name,
            CONF_MODEL_ID: model.model_id,
            CONF_DEVICE_ID: device_id,
            CONF_HOST: host,
            CONF_TRANSPORT: TRANSPORT_LAN,
            CONF_DISCOVERY_SOURCE: DISCOVERY_SOURCE_LAN,
            CONF_DISCOVERY_MATCH: DISCOVERY_MATCH_SPNET_MODEL_ID,
            CONF_DISCOVERY_CONFIDENCE: DISCOVERY_CONFIDENCE_VERIFIED,
        },
    )


def lan_setup_entry_data_from_discovery(
    catalog: ModelCatalog,
    discovery_info: Any,
) -> SetupEntryData:
    """Build setup data from a Home Assistant LAN discovery object."""
    response = _spnet_discovery_response_bytes(discovery_info)
    source = str(
        _discovery_value(discovery_info, CONF_HOST)
        or _discovery_value(discovery_info, "source")
        or _discovery_value(discovery_info, "host")
        or ""
    ).strip()
    return lan_setup_entry_data_from_spnet_response(
        catalog,
        response,
        source=source,
    )


def manual_setup_model(
    catalog: ModelCatalog,
    *,
    name: str,
    model_id: int | str | None = None,
) -> CatalogModel:
    """Resolve a manually selected model and optional APK variant ID."""
    name = str(name).strip()
    if not name:
        raise SetupDataError(CONF_MODEL, "required")

    resolved_model_id = _entry_model_id(model_id)
    model = catalog.resolve_model_label(name, model_id=resolved_model_id)
    if model is not None and model.is_user_facing:
        return model
    if resolved_model_id is not None and catalog.resolve_label(name) is not None:
        raise SetupDataError(CONF_MODEL_ID, "unknown_model_id")
    raise SetupDataError(CONF_MODEL, "unknown_model")


def manual_setup_entry_data(
    model: CatalogModel,
    *,
    transport: str,
    device_id: str = "",
    host: str = "",
    address: str = "",
    mesh_uuid: int | str | None = None,
    mesh_node_id: int | str | None = None,
    mesh_node_type: int | str | None = None,
    mesh_node_wiring: int | str | None = None,
) -> SetupEntryData:
    """Build validated config-entry data for the manual setup flow."""
    transport = str(transport or TRANSPORT_MANUAL).strip()
    if transport == TRANSPORT_BLE:
        return _manual_ble_setup_entry_data(model, address=address)
    if transport == TRANSPORT_LAN:
        return _lan_setup_entry_data(model, device_id=device_id, host=host)
    if transport == TRANSPORT_BLE_MESH:
        return _manual_ble_mesh_setup_entry_data(
            model,
            address=address,
            mesh_uuid=mesh_uuid,
            mesh_node_id=mesh_node_id,
            mesh_node_type=mesh_node_type,
            mesh_node_wiring=mesh_node_wiring,
        )
    if transport == TRANSPORT_MANUAL:
        return _manual_setup_entry_data(model, device_id=device_id)
    raise SetupDataError(CONF_TRANSPORT, "unsupported_transport")


def zengge_cloud_setup_entry_data(
    model: CatalogModel,
    mesh: ZenggeCloudMesh,
    *,
    address: str = "",
) -> SetupEntryData:
    """Build config-entry data from parsed MagicHue/Zengge mesh metadata."""
    if not zengge_cloud_import_supported(model):
        raise SetupDataError(CONF_TRANSPORT, "unsupported_mesh_transport")
    if mesh.mesh_uuid <= 0:
        raise SetupDataError(CONF_MESH_UUID, "required")

    unique_id = f"zng_mesh_{hex(mesh.mesh_uuid)}"
    data: dict[str, Any] = {
        CONF_MODEL: model.name,
        CONF_MODEL_ID: model.model_id,
        CONF_ADDRESS: str(address).strip(),
        CONF_DEVICE_ID: unique_id,
        CONF_MESH_UUID: mesh.mesh_uuid,
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }
    _merge_zengge_cloud_mesh_data(data, mesh)

    title = mesh.name or f"{model.friendly_name} mesh {hex(mesh.mesh_uuid)}"
    return SetupEntryData(unique_id=unique_id, title=title, data=data)


def zengge_cloud_update_entry_data(
    entry_data: Mapping[str, Any],
    mesh: ZenggeCloudMesh,
) -> dict[str, Any]:
    """Merge parsed MagicHue/Zengge mesh metadata into existing entry data."""
    model_name = str(entry_data.get(CONF_MODEL, "")).strip()
    if not model_name:
        raise SetupDataError(CONF_MODEL, "required")
    if model_name != "RG4":
        raise SetupDataError(CONF_TRANSPORT, "unsupported_mesh_transport")
    if mesh.mesh_uuid <= 0:
        raise SetupDataError(CONF_MESH_UUID, "required")

    data = dict(entry_data)
    data[CONF_MODEL] = model_name
    data[CONF_MESH_UUID] = mesh.mesh_uuid
    data[CONF_TRANSPORT] = TRANSPORT_BLE_MESH
    if not str(data.get(CONF_DEVICE_ID, "")).strip():
        data[CONF_DEVICE_ID] = f"zng_mesh_{hex(mesh.mesh_uuid)}"
    _merge_zengge_cloud_mesh_data(data, mesh)
    return data


def zengge_cloud_import_supported(model: CatalogModel) -> bool:
    """Return whether MagicHue/Zengge cloud metadata applies to this model."""
    return (
        model.family is ProtocolFamily.ZENGGE_MESH
        and TransportKind.BLE_MESH in model.transports
    )


def migrate_legacy_entry_data(
    catalog: ModelCatalog,
    entry_data: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize legacy UniLED config-entry data into the new schema."""
    transport = _legacy_transport_name(entry_data.get(CONF_TRANSPORT))
    model_name = str(entry_data.get(CONF_MODEL, "")).strip()
    if transport == TRANSPORT_BLE_MESH and not model_name:
        model_name = "RG4"
    if not model_name:
        raise SetupDataError(CONF_MODEL, "required")

    model_id = _entry_model_id(entry_data.get(CONF_MODEL_ID))
    model = catalog.resolve_model_label(model_name, model_id=model_id)
    if model is None or not model.is_user_facing:
        if model_id is not None and catalog.resolve_label(model_name) is not None:
            raise SetupDataError(CONF_MODEL_ID, "unknown_model_id")
        raise SetupDataError(CONF_MODEL, "unknown_model")

    if transport == TRANSPORT_BLE_MESH:
        return _migrate_mesh_entry_data(model, entry_data)
    if transport == TRANSPORT_LAN:
        return _migrate_lan_entry_data(model, entry_data)
    if transport == TRANSPORT_BLE:
        return _migrate_ble_entry_data(model, entry_data)
    if transport == TRANSPORT_MANUAL:
        return _migrate_manual_entry_data(model, entry_data)

    inferred = _inferred_transport(model, entry_data)
    if inferred == TRANSPORT_BLE_MESH:
        return _migrate_mesh_entry_data(model, entry_data)
    if inferred == TRANSPORT_LAN:
        return _migrate_lan_entry_data(model, entry_data)
    if inferred == TRANSPORT_BLE:
        return _migrate_ble_entry_data(model, entry_data)
    return _migrate_manual_entry_data(model, entry_data)


def reconfigure_entry_data(
    catalog: ModelCatalog,
    entry_data: Mapping[str, Any],
    *,
    device_id: Any = _UNSET,
    host: Any = _UNSET,
    address: Any = _UNSET,
    mesh_uuid: Any = _UNSET,
    mesh_node_id: Any = _UNSET,
    mesh_node_type: Any = _UNSET,
    mesh_node_wiring: Any = _UNSET,
) -> dict[str, Any]:
    """Build normalized config-entry data for a reconfigure flow."""
    working = dict(entry_data)
    old_host = _text(entry_data, CONF_HOST, "ip_address", CONF_ADDRESS)
    old_device_id = str(entry_data.get(CONF_DEVICE_ID, "")).strip()
    old_mesh_uuid = _optional_int(entry_data.get(CONF_MESH_UUID))

    _apply_reconfigure_update(working, CONF_DEVICE_ID, device_id)
    _apply_reconfigure_update(working, CONF_HOST, host)
    _apply_reconfigure_update(working, CONF_ADDRESS, address)
    _apply_reconfigure_update(working, CONF_MESH_UUID, mesh_uuid)
    _apply_reconfigure_update(working, CONF_MESH_NODE_ID, mesh_node_id)
    _apply_reconfigure_update(working, CONF_MESH_NODE_TYPE, mesh_node_type)
    _apply_reconfigure_update(working, CONF_MESH_NODE_WIRING, mesh_node_wiring)

    data = migrate_legacy_entry_data(catalog, working)
    transport = str(data.get(CONF_TRANSPORT, "")).strip()
    if transport == TRANSPORT_LAN and host is not _UNSET:
        if not old_device_id or old_device_id == old_host:
            data[CONF_DEVICE_ID] = data[CONF_HOST]
    if transport == TRANSPORT_BLE_MESH and old_mesh_uuid is not None:
        new_mesh_uuid = _optional_int(data.get(CONF_MESH_UUID))
        if old_mesh_uuid > 0 and new_mesh_uuid != old_mesh_uuid:
            raise SetupDataError(CONF_MESH_UUID, "mesh_identity_mismatch")
    return data


def _ble_mesh_setup_entry_data(
    model: CatalogModel,
    *,
    address: str,
    mesh_advert: BLEMeshAdvertisement | None,
    discovery: Mapping[str, str] | None = None,
) -> SetupEntryData:
    if mesh_advert is None:
        unique_id = _ble_mesh_unique_id(model, address=address)
        title = model.friendly_name
        data = {
            CONF_MODEL: model.name,
            CONF_MODEL_ID: model.model_id,
            CONF_ADDRESS: address,
            CONF_TRANSPORT: TRANSPORT_BLE_MESH,
        }
    else:
        unique_id = _ble_mesh_unique_id(
            model,
            address=address,
            mesh_uuid=mesh_advert.mesh_uuid,
        )
        title = f"{model.friendly_name} mesh {hex(mesh_advert.mesh_uuid)}"
        data = {
            CONF_MODEL: model.name,
            CONF_MODEL_ID: model.model_id,
            CONF_ADDRESS: address,
            CONF_DEVICE_ID: unique_id,
            CONF_MESH_UUID: mesh_advert.mesh_uuid,
            CONF_MESH_NODE_ID: mesh_advert.node_id,
            CONF_MESH_NODE_TYPE: mesh_advert.node_type,
            CONF_TRANSPORT: TRANSPORT_BLE_MESH,
        }
    if discovery:
        data.update(discovery)
    return SetupEntryData(unique_id=unique_id, title=title, data=data)


def _ble_mesh_unique_id(
    model: CatalogModel,
    *,
    address: str = "",
    mesh_uuid: int | None = None,
) -> str:
    if zengge_cloud_import_supported(model) and mesh_uuid is not None:
        return f"zng_mesh_{hex(mesh_uuid)}"
    if address:
        return f"ble_mesh:{address.casefold()}"
    if mesh_uuid is not None:
        return f"ble_mesh:{model.name.casefold()}:{hex(mesh_uuid)}"
    return f"ble_mesh:{model.name.casefold()}"


def _merge_zengge_cloud_mesh_data(
    data: dict[str, Any],
    mesh: ZenggeCloudMesh,
) -> None:
    _set_optional(data, CONF_MESH_PLACE_ID, mesh.place_id)
    _set_optional(data, CONF_MESH_PLACE_NAME, mesh.name)
    _set_optional(data, CONF_MESH_KEY, mesh.mesh_key)
    _set_optional(data, CONF_MESH_PASSWORD, mesh.mesh_password)
    _set_optional(data, CONF_MESH_LTK, mesh.mesh_ltk)
    if mesh.nodes:
        data[CONF_MESH_NODES] = [
            {
                CONF_MESH_NODE_ID: node.node_id,
                CONF_MESH_NODE_TYPE: node.node_type,
                CONF_MESH_NODE_WIRING: node.node_wiring,
                "name": node.name,
                "area": node.area,
            }
            for node in mesh.nodes
        ]
    else:
        data.pop(CONF_MESH_NODES, None)


def _set_optional(data: dict[str, Any], key: str, value: Any | None) -> None:
    if value is None:
        data.pop(key, None)
    else:
        data[key] = value


def _manual_setup_entry_data(
    model: CatalogModel,
    *,
    device_id: str,
) -> SetupEntryData:
    device_id = str(device_id).strip()
    if not device_id:
        raise SetupDataError(CONF_DEVICE_ID, "required")

    return SetupEntryData(
        unique_id=f"manual:{model.name}:{device_id.casefold()}",
        title=f"{model.friendly_name} {device_id}",
        data={
            CONF_MODEL: model.name,
            CONF_MODEL_ID: model.model_id,
            CONF_DEVICE_ID: device_id,
            CONF_TRANSPORT: TRANSPORT_MANUAL,
        },
    )


def _manual_ble_setup_entry_data(
    model: CatalogModel,
    *,
    address: str,
) -> SetupEntryData:
    if TransportKind.BLE not in model.transports:
        raise SetupDataError(CONF_TRANSPORT, "unsupported_ble_transport")

    address = _normalized_address(address)
    return SetupEntryData(
        unique_id=f"ble:{address.casefold()}",
        title=f"{model.friendly_name} {address}",
        data={
            CONF_MODEL: model.name,
            CONF_MODEL_ID: model.model_id,
            CONF_ADDRESS: address,
            CONF_TRANSPORT: TRANSPORT_BLE,
        },
    )


def _manual_ble_mesh_setup_entry_data(
    model: CatalogModel,
    *,
    address: str,
    mesh_uuid: int | str | None,
    mesh_node_id: int | str | None,
    mesh_node_type: int | str | None,
    mesh_node_wiring: int | str | None,
) -> SetupEntryData:
    if TransportKind.BLE_MESH not in model.transports:
        raise SetupDataError(CONF_TRANSPORT, "unsupported_mesh_transport")

    address = _normalized_address(address)
    mesh_uuid_int = _required_positive_int(
        mesh_uuid,
        field=CONF_MESH_UUID,
        reason="invalid_mesh_uuid",
    )
    unique_id = _ble_mesh_unique_id(
        model,
        address=address,
        mesh_uuid=mesh_uuid_int,
    )
    data: dict[str, Any] = {
        CONF_MODEL: model.name,
        CONF_MODEL_ID: model.model_id,
        CONF_ADDRESS: address,
        CONF_DEVICE_ID: unique_id,
        CONF_MESH_UUID: mesh_uuid_int,
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }
    _set_optional_int(
        data,
        CONF_MESH_NODE_ID,
        mesh_node_id,
        reason="invalid_mesh_node_id",
    )
    _set_optional_int(
        data,
        CONF_MESH_NODE_TYPE,
        mesh_node_type,
        reason="invalid_mesh_node_type",
    )
    _set_optional_int(
        data,
        CONF_MESH_NODE_WIRING,
        mesh_node_wiring,
        reason="invalid_mesh_node_wiring",
    )
    return SetupEntryData(
        unique_id=unique_id,
        title=f"{model.friendly_name} mesh {hex(mesh_uuid_int)}",
        data=data,
    )


def _lan_setup_entry_data(
    model: CatalogModel,
    *,
    device_id: str,
    host: str,
) -> SetupEntryData:
    if lan_profile_for_model(model) is None:
        raise SetupDataError(CONF_TRANSPORT, "unsupported_lan_transport")

    host = _normalized_host(host)
    device_id = str(device_id).strip() or host
    return SetupEntryData(
        unique_id=f"lan:{host.casefold()}",
        title=f"{model.friendly_name} {host}",
        data={
            CONF_MODEL: model.name,
            CONF_MODEL_ID: model.model_id,
            CONF_DEVICE_ID: device_id,
            CONF_HOST: host,
            CONF_TRANSPORT: TRANSPORT_LAN,
        },
    )


def _migrate_ble_entry_data(
    model: CatalogModel,
    entry_data: Mapping[str, Any],
) -> dict[str, Any]:
    if TransportKind.BLE not in model.transports:
        raise SetupDataError(CONF_TRANSPORT, "unsupported_ble_transport")

    address = _normalized_address(_text(entry_data, CONF_ADDRESS))
    data: dict[str, Any] = {
        CONF_MODEL: model.name,
        CONF_MODEL_ID: model.model_id,
        CONF_ADDRESS: address,
        CONF_TRANSPORT: TRANSPORT_BLE,
    }
    _copy_optional_text(data, entry_data, CONF_DEVICE_ID)
    return data


def _migrate_lan_entry_data(
    model: CatalogModel,
    entry_data: Mapping[str, Any],
) -> dict[str, Any]:
    if lan_profile_for_model(model) is None:
        raise SetupDataError(CONF_TRANSPORT, "unsupported_lan_transport")

    host = _normalized_host(
        _text(entry_data, CONF_HOST, "ip_address", CONF_ADDRESS),
    )
    device_id = str(entry_data.get(CONF_DEVICE_ID, "")).strip() or host
    return {
        CONF_MODEL: model.name,
        CONF_MODEL_ID: model.model_id,
        CONF_DEVICE_ID: device_id,
        CONF_HOST: host,
        CONF_TRANSPORT: TRANSPORT_LAN,
    }


def _migrate_mesh_entry_data(
    model: CatalogModel,
    entry_data: Mapping[str, Any],
) -> dict[str, Any]:
    if TransportKind.BLE_MESH not in model.transports:
        raise SetupDataError(CONF_TRANSPORT, "unsupported_mesh_transport")

    raw_mesh_uuid = entry_data.get(CONF_MESH_UUID)
    mesh_uuid = _optional_int(raw_mesh_uuid)
    if raw_mesh_uuid not in (None, "") and (mesh_uuid is None or mesh_uuid <= 0):
        raise SetupDataError(CONF_MESH_UUID, "invalid_mesh_uuid")
    device_id = (
        str(entry_data.get(CONF_DEVICE_ID, "")).strip()
        or str(entry_data.get("mesh_id", "")).strip()
        or _migrated_mesh_unique_id(model, entry_data, mesh_uuid)
    )
    data: dict[str, Any] = {
        CONF_MODEL: model.name,
        CONF_MODEL_ID: model.model_id,
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }
    if device_id:
        data[CONF_DEVICE_ID] = device_id
    if mesh_uuid is not None:
        data[CONF_MESH_UUID] = mesh_uuid
    _copy_optional_text(data, entry_data, CONF_ADDRESS)
    for key in (
        CONF_MESH_PLACE_ID,
        CONF_MESH_PLACE_NAME,
        CONF_MESH_KEY,
        CONF_MESH_PASSWORD,
        CONF_MESH_LTK,
    ):
        _copy_optional_text(data, entry_data, key)
    _copy_optional_value(data, entry_data, CONF_MESH_NODES)
    for key, reason in (
        (CONF_MESH_NODE_ID, "invalid_mesh_node_id"),
        (CONF_MESH_NODE_TYPE, "invalid_mesh_node_type"),
        (CONF_MESH_NODE_WIRING, "invalid_mesh_node_wiring"),
    ):
        _set_optional_int(data, key, entry_data.get(key), reason=reason)
    return data


def _migrated_mesh_unique_id(
    model: CatalogModel,
    entry_data: Mapping[str, Any],
    mesh_uuid: int | None,
) -> str:
    if mesh_uuid is None:
        return ""
    return _ble_mesh_unique_id(
        model,
        address=_text(entry_data, CONF_ADDRESS),
        mesh_uuid=mesh_uuid,
    )


def _migrate_manual_entry_data(
    model: CatalogModel,
    entry_data: Mapping[str, Any],
) -> dict[str, Any]:
    device_id = str(entry_data.get(CONF_DEVICE_ID, "")).strip()
    if not device_id:
        device_id = str(entry_data.get(CONF_ADDRESS, "")).strip()
    if not device_id:
        raise SetupDataError(CONF_DEVICE_ID, "required")
    return {
        CONF_MODEL: model.name,
        CONF_MODEL_ID: model.model_id,
        CONF_DEVICE_ID: device_id,
        CONF_TRANSPORT: TRANSPORT_MANUAL,
    }


def _legacy_transport_name(value: Any) -> str:
    transport = str(value or "").strip()
    if transport == "zng":
        return TRANSPORT_BLE_MESH
    if transport == "net":
        return TRANSPORT_LAN
    return transport


def _bluetooth_discovery_match(
    catalog: ModelCatalog,
    advertised_name: str,
) -> tuple[CatalogModel, str] | None:
    """Resolve exact or safely suffixed BLE local names to a model and match type."""
    model = catalog.resolve_label(advertised_name)
    if model is not None and model.is_user_facing:
        return (model, DISCOVERY_MATCH_EXACT_LABEL)

    folded_name = advertised_name.casefold()
    for label in sorted(catalog.user_facing_labels, key=len, reverse=True):
        if not label:
            continue
        folded_label = label.casefold()
        if not folded_name.startswith(folded_label):
            continue
        suffix = advertised_name[len(label) :]
        if suffix and suffix.startswith(_DISCOVERY_NAME_SUFFIX_SEPARATORS):
            model = catalog.resolve_label(label)
            if model is not None and model.is_user_facing:
                return (model, DISCOVERY_MATCH_SAFE_SUFFIX)
    return None


def _bluetooth_discovery_confidence(model: CatalogModel) -> str:
    """Return the config-entry confidence tier for a Bluetooth model match."""
    if model.legacy_uniled_supported or protocol_for_model(model) is not None:
        return DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
    mesh_profile = mesh_profile_for_model(model)
    if (
        mesh_profile is not None
        and mesh_profile.old_uniled_protocol_known
        and mesh_profile.core_command_protocol_known
    ):
        return DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
    return DISCOVERY_CONFIDENCE_DISCOVERED_ONLY


def _inferred_transport(model: CatalogModel, entry_data: Mapping[str, Any]) -> str:
    if entry_data.get(CONF_MESH_UUID) is not None or entry_data.get("mesh_id"):
        return TRANSPORT_BLE_MESH
    if _text(entry_data, CONF_HOST, "ip_address"):
        return TRANSPORT_LAN
    if _text(entry_data, CONF_ADDRESS) and TransportKind.BLE in model.transports:
        return TRANSPORT_BLE
    return TRANSPORT_MANUAL


def _discovery_value(source: Any, key: str) -> Any:
    """Return a value from a mapping or attribute-style discovery object."""
    if isinstance(source, Mapping):
        return source.get(key)
    return getattr(source, key, None)


def _spnet_discovery_response_bytes(discovery_info: Any) -> bytes:
    response = (
        _discovery_value(discovery_info, CONF_DISCOVERY_RESPONSE_HEX)
        or _discovery_value(discovery_info, "response")
        or _discovery_value(discovery_info, "raw")
    )
    if isinstance(response, bytes):
        return response
    if isinstance(response, (bytearray, memoryview)):
        return bytes(response)
    if isinstance(response, str):
        try:
            return bytes.fromhex(response.strip())
        except ValueError as ex:
            raise SetupDataError(CONF_MODEL, "unknown_model") from ex
    raise SetupDataError(CONF_MODEL, "unknown_model")


def _text(entry_data: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(entry_data.get(key, "")).strip()
        if value:
            return value
    return ""


def _copy_optional_text(
    data: dict[str, Any],
    source: Mapping[str, Any],
    key: str,
) -> None:
    value = str(source.get(key, "")).strip()
    if value:
        data[key] = value


def _copy_optional_value(
    data: dict[str, Any],
    source: Mapping[str, Any],
    key: str,
) -> None:
    if key in source and source[key] not in (None, ""):
        data[key] = source[key]


def _apply_reconfigure_update(
    data: dict[str, Any],
    key: str,
    value: Any,
) -> None:
    if value is not _UNSET:
        data[key] = value


def _normalized_address(address: str) -> str:
    address = str(address).strip()
    if not address:
        raise SetupDataError(CONF_ADDRESS, "required")
    if any(char.isspace() for char in address):
        raise SetupDataError(CONF_ADDRESS, "invalid_address")
    return address


def _normalized_host(host: str) -> str:
    host = str(host).strip()
    if not host:
        raise SetupDataError(CONF_HOST, "required")
    if any(char.isspace() for char in host) or "/" in host:
        raise SetupDataError(CONF_HOST, "invalid_host")
    return host


def _looks_like_mac_address(value: str) -> bool:
    parts = str(value).strip().split(":")
    if len(parts) != 6:
        return False
    for part in parts:
        if len(part) != 2:
            return False
        try:
            int(part, 16)
        except ValueError:
            return False
    return True


def _required_positive_int(
    value: int | str | None,
    *,
    field: str,
    reason: str,
) -> int:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise SetupDataError(field, "required")
    parsed = _optional_int(value)
    if parsed is None:
        raise SetupDataError(field, reason)
    if parsed <= 0:
        raise SetupDataError(field, reason)
    return parsed


def _set_optional_int(
    data: dict[str, Any],
    key: str,
    value: int | str | None,
    *,
    reason: str,
) -> None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return
    parsed = _optional_int(value)
    if parsed is None or parsed < 0:
        raise SetupDataError(key, reason)
    data[key] = parsed


def _optional_int(value: int | str | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text, 0)
    except ValueError:
        return None


def _entry_model_id(value: Any) -> int | None:
    if value in (None, ""):
        return None
    model_id = _optional_int(value)
    if model_id is None:
        raise SetupDataError(CONF_MODEL_ID, "invalid_model_id")
    return model_id
