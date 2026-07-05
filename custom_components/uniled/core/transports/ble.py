"""BLE profile facts for core protocol families."""

from __future__ import annotations

from dataclasses import dataclass

from ..catalog import CatalogModel, ProtocolFamily, TransportKind
from ..options import banlanx6xx_style_family

UUID_BASE = "0000{}-0000-1000-8000-00805f9b34fb"

APK_BLE_UUID_POOL = (
    "0000ff12-0000-1000-8000-00805f9b34fb",
    "0000ff14-0000-1000-8000-00805f9b34fb",
    "0000ff15-0000-1000-8000-00805f9b34fb",
    "0000ffe0-0000-1000-8000-00805f9b34fb",
    "0000ffe1-0000-1000-8000-00805f9b34fb",
)
APK_BLE_UUID_STRING_HINTS = (
    "0000ff12-0000-1000-8000-00805f9b34fb2",
    "0000ff14-0000-1000-8000-00805f9b34fb2",
    "0000ff15-0000-1000-8000-00805f9b34fb2",
    "0000ffe0-0000-1000-8000-00805f9b34fb2",
    "0000ffe1-0000-1000-8000-00805f9b34fb2",
    "FF122",
    "FF142",
    "FF152",
    "ffe02",
    "ffe12",
)
APK_BLE_PLUGIN_CHANNELS = (
    "com.spled.plugins/flutter_ble/main",
    "com.spled.plugins/flutter_ble/ble_characteristic_value_changed",
    "com.spled.plugins/flutter_ble/ble_connection_state_changed",
    "com.spled.plugins/flutter_ble/bluetooth_adapter_state_changed",
    "com.spled.plugins/flutter_ble/bluetooth_device_discovery_state_changed",
    "com.spled.plugins/flutter_ble/bluetooth_device_found",
)
APK_BLE_PLUGIN_METHODS = (
    "openBluetoothAdapter",
    "closeBluetoothAdapter",
    "getBluetoothAdapterState",
    "startBluetoothDevicesDiscovery",
    "stopBluetoothDevicesDiscovery",
    "getBluetoothDevices",
    "createBleConnection",
    "closeBleConnection",
    "requestMtu",
    "getBleDeviceServices",
    "getBleDeviceCharacteristics",
    "getBluetoothDeviceRssi",
    "notifyBleCharacteristicValueChange",
    "writeBleCharacteristicValue",
)
APK_BLE_PLUGIN_ARGUMENTS = (
    "deviceId",
    "serviceUuid",
    "characteristicUuid",
    "characteristicWriteType",
    "forceWaitResponse",
    "timeout",
    "value",
    "enabled",
    "services",
    "interval",
    "clearPreDiscoveredDevices",
    "aliveTime",
)
APK_BLE_PLUGIN_RESULT_FIELDS = (
    "id",
    "name",
    "rssi",
    "serviceData",
    "manufacturerData",
    "uuid",
    "supportWrite",
    "supportWriteNoResponse",
    "supportRead",
    "supportNotify",
    "supportIndicate",
)
APK_BLE_PLUGIN_CONTRACT_STRING_HINTS = (
    "serviceUuid",
    "characteristicUuid",
    "value",
    "enabled",
    "timeout",
    "characteristicWriteType",
    "forceWaitResponse",
)
APK_BLE_PROTOCOL_GAP_HINTS = (
    "APK Java plugin exposes generic BLE operations, not model-specific opcodes",
    "Flutter AOT strings expose UUID candidates but not per-family UUID binding",
    (
        "Command and notification parser support still require old-UniLED "
        "parity, native tracing, or hardware captures"
    ),
)


@dataclass(frozen=True, slots=True)
class BLEPluginContractHint:
    """One decompiled BLE plugin call-contract fact from the BanlanX APK."""

    method: str
    required_arguments: tuple[str, ...]
    default_arguments: tuple[str, ...]
    behavior: str
    error_code: str | None
    evidence: str


@dataclass(frozen=True, slots=True)
class BLEUUIDCandidate:
    """One normalized BLE UUID candidate recovered from APK native strings."""

    uuid: str
    short_name: str
    apk_string: str
    known_usage: str
    unported_binding_status: str
    evidence: str


APK_BLE_UUID_INVENTORY = (
    BLEUUIDCandidate(
        uuid="0000ff12-0000-1000-8000-00805f9b34fb",
        short_name="ff12",
        apk_string="0000ff12-0000-1000-8000-00805f9b34fb2",
        known_usage="unbound_candidate",
        unported_binding_status="unproven",
        evidence="BanlanX 3.3.1 Flutter libapp.so string",
    ),
    BLEUUIDCandidate(
        uuid="0000ff14-0000-1000-8000-00805f9b34fb",
        short_name="ff14",
        apk_string="0000ff14-0000-1000-8000-00805f9b34fb2",
        known_usage="unbound_candidate",
        unported_binding_status="unproven",
        evidence="BanlanX 3.3.1 Flutter libapp.so string",
    ),
    BLEUUIDCandidate(
        uuid="0000ff15-0000-1000-8000-00805f9b34fb",
        short_name="ff15",
        apk_string="0000ff15-0000-1000-8000-00805f9b34fb2",
        known_usage="unbound_candidate",
        unported_binding_status="unproven",
        evidence="BanlanX 3.3.1 Flutter libapp.so string",
    ),
    BLEUUIDCandidate(
        uuid="0000ffe0-0000-1000-8000-00805f9b34fb",
        short_name="ffe0",
        apk_string="0000ffe0-0000-1000-8000-00805f9b34fb2",
        known_usage="legacy_service_uuid",
        unported_binding_status="unproven",
        evidence="BanlanX 3.3.1 Flutter libapp.so string plus old-UniLED parity",
    ),
    BLEUUIDCandidate(
        uuid="0000ffe1-0000-1000-8000-00805f9b34fb",
        short_name="ffe1",
        apk_string="0000ffe1-0000-1000-8000-00805f9b34fb2",
        known_usage="legacy_write_notify_uuid",
        unported_binding_status="unproven",
        evidence="BanlanX 3.3.1 Flutter libapp.so string plus old-UniLED parity",
    ),
)

APK_BLE_PLUGIN_CONTRACT_HINTS = (
    BLEPluginContractHint(
        method="getBleDeviceCharacteristics",
        required_arguments=("serviceUuid",),
        default_arguments=(),
        behavior="requests characteristics for the supplied service UUID",
        error_code="10013",
        evidence="p185q2/C2229c.java validates serviceUuid before dispatch",
    ),
    BLEPluginContractHint(
        method="notifyBleCharacteristicValueChange",
        required_arguments=("serviceUuid", "characteristicUuid"),
        default_arguments=("enabled=False",),
        behavior="subscribes or unsubscribes notifications on a characteristic",
        error_code="10013",
        evidence=(
            "p185q2/C2229c.java validates serviceUuid/characteristicUuid "
            "and defaults enabled to false"
        ),
    ),
    BLEPluginContractHint(
        method="createBleConnection",
        required_arguments=(),
        default_arguments=("timeout=0",),
        behavior="creates a BLE connection through the plugin BLE manager",
        error_code=None,
        evidence="p185q2/C2229c.java defaults missing timeout to zero",
    ),
    BLEPluginContractHint(
        method="requestMtu",
        required_arguments=("value",),
        default_arguments=(),
        behavior="requests the supplied MTU value",
        error_code="10013",
        evidence="p185q2/C2229c.java validates value before requestMtu dispatch",
    ),
    BLEPluginContractHint(
        method="writeBleCharacteristicValue",
        required_arguments=("serviceUuid", "characteristicUuid", "value"),
        default_arguments=("forceWaitResponse=False",),
        behavior="writes raw bytes to the supplied characteristic",
        error_code="10013",
        evidence=(
            "p185q2/C2229c.java validates serviceUuid/characteristicUuid/value "
            "and defaults forceWaitResponse to false"
        ),
    ),
    BLEPluginContractHint(
        method="writeBleCharacteristicValue",
        required_arguments=(),
        default_arguments=("characteristicWriteType=None",),
        behavior=(
            "maps characteristicWriteType=1 to Android write type 1, any other "
            "provided value to Android write type 2, and leaves null unchanged"
        ),
        error_code=None,
        evidence="p185q2/C2229c.java maps characteristicWriteType before write",
    ),
)


@dataclass(frozen=True, slots=True)
class BLEProfile:
    """BLE service and characteristic UUIDs for one model."""

    service_uuids: tuple[str, ...]
    write_uuid: str
    notify_uuid: str | None = None

    @property
    def notification_uuid(self) -> str:
        """Return explicit notify UUID or write UUID fallback."""
        return self.notify_uuid or self.write_uuid


@dataclass(frozen=True, slots=True)
class BLEEvidenceProfile:
    """BLE facts recovered from APK strings and ported command profiles."""

    family: ProtocolFamily
    command_profile_known: bool
    known_service_uuids: tuple[str, ...]
    known_write_uuid: str | None
    known_notify_uuid: str | None
    apk_uuid_pool: tuple[str, ...] = APK_BLE_UUID_POOL
    uuid_inventory: tuple[BLEUUIDCandidate, ...] = APK_BLE_UUID_INVENTORY
    plugin_channels: tuple[str, ...] = APK_BLE_PLUGIN_CHANNELS
    plugin_methods: tuple[str, ...] = APK_BLE_PLUGIN_METHODS
    plugin_arguments: tuple[str, ...] = APK_BLE_PLUGIN_ARGUMENTS
    plugin_result_fields: tuple[str, ...] = APK_BLE_PLUGIN_RESULT_FIELDS
    plugin_contract_hints: tuple[
        BLEPluginContractHint, ...
    ] = APK_BLE_PLUGIN_CONTRACT_HINTS
    protocol_gap_hints: tuple[str, ...] = APK_BLE_PROTOCOL_GAP_HINTS

    @property
    def unbound_uuid_candidates(self) -> tuple[BLEUUIDCandidate, ...]:
        """Return APK UUID candidates without a proven family binding."""
        return tuple(
            candidate
            for candidate in self.uuid_inventory
            if candidate.known_usage == "unbound_candidate"
        )

    @property
    def legacy_uuid_candidates(self) -> tuple[BLEUUIDCandidate, ...]:
        """Return APK UUID candidates already backed by old-UniLED parity."""
        return tuple(
            candidate
            for candidate in self.uuid_inventory
            if candidate.known_usage.startswith("legacy_")
        )

    @property
    def uuid_binding_status(self) -> str:
        """Return a compact status for proven versus pending UUID bindings."""
        binding = "known" if self.command_profile_known else "pending"
        write = "known" if self.known_write_uuid is not None else "pending"
        notify = "known" if self.known_notify_uuid is not None else "pending"
        return (
            f"binding={binding}; services={len(self.known_service_uuids)}; "
            f"write={write}; notify={notify}; "
            f"unbound_candidates={len(self.unbound_uuid_candidates)}; "
            f"legacy_candidates={len(self.legacy_uuid_candidates)}"
        )


def ble_profile_for_model(model: CatalogModel) -> BLEProfile | None:
    """Return the known BLE profile for a catalog model."""
    if model.family in {
        ProtocolFamily.BANLANX_601,
        ProtocolFamily.BANLANX_60X,
        ProtocolFamily.BANLANX_V2,
        ProtocolFamily.BANLANX_V3,
        ProtocolFamily.LEGACY_LED_CHORD,
        ProtocolFamily.LEGACY_LED_HUE,
    }:
        return BLEProfile(
            service_uuids=(_uuid16("ffe0"),),
            write_uuid=_uuid16("ffe1"),
        )

    if banlanx6xx_style_family(model.family):
        return BLEProfile(
            service_uuids=(_uuid16("e0ff"), _uuid16("ffe0")),
            write_uuid=_uuid16("ffe1"),
        )

    return None


def ble_evidence_for_model(model: CatalogModel) -> BLEEvidenceProfile | None:
    """Return APK/ported BLE evidence for direct-BLE-capable models."""
    if TransportKind.BLE not in model.transports:
        return None

    profile = ble_profile_for_model(model)
    return BLEEvidenceProfile(
        family=model.family,
        command_profile_known=profile is not None,
        known_service_uuids=() if profile is None else profile.service_uuids,
        known_write_uuid=None if profile is None else profile.write_uuid,
        known_notify_uuid=None if profile is None else profile.notification_uuid,
    )


def describe_ble_evidence_profile(profile: BLEEvidenceProfile | None) -> str | None:
    """Return a compact diagnostic string for a BLE evidence profile."""
    if profile is None:
        return None

    parts = [
        profile.family.value,
        "command_profile_known"
        if profile.command_profile_known
        else "command_profile_pending",
    ]
    if profile.known_service_uuids:
        parts.append(f"services={len(profile.known_service_uuids)}")
    if profile.known_write_uuid is not None:
        parts.append("write_uuid_known")
    parts.append(f"apk_uuid_pool={len(profile.apk_uuid_pool)}")
    parts.append(f"uuid_inventory={len(profile.uuid_inventory)}")
    parts.append(f"unbound_uuid_candidates={len(profile.unbound_uuid_candidates)}")
    parts.append(f"legacy_uuid_candidates={len(profile.legacy_uuid_candidates)}")
    parts.append(f"plugin_methods={len(profile.plugin_methods)}")
    parts.append(f"arguments={len(profile.plugin_arguments)}")
    parts.append(f"result_fields={len(profile.plugin_result_fields)}")
    parts.append(f"plugin_contracts={len(profile.plugin_contract_hints)}")
    parts.append(f"channels={len(profile.plugin_channels)}")
    parts.append(f"gaps={len(profile.protocol_gap_hints)}")
    return "; ".join(parts)


def _uuid16(part: str) -> str:
    return UUID_BASE.format(part.lower())
