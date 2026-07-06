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
APK_BLE_SCAN_RESULT_FIELDS = (
    "id",
    "name",
    "rssi",
    "serviceData",
    "manufacturerData",
)
APK_BLE_SERVICE_RESULT_FIELDS = (
    "uuid",
    "isPrimary",
)
APK_BLE_CHARACTERISTIC_RESULT_FIELDS = (
    "uuid",
    "supportWrite",
    "supportWriteNoResponse",
    "supportRead",
    "supportNotify",
    "supportIndicate",
)
APK_BLE_RSSI_RESULT_FIELDS = (
    "rssi",
)
APK_BLE_MTU_RESULT_FIELDS = (
    "value",
)
APK_BLE_PLUGIN_RESULT_FIELDS = (
    *APK_BLE_SCAN_RESULT_FIELDS,
    *APK_BLE_SERVICE_RESULT_FIELDS,
    *APK_BLE_CHARACTERISTIC_RESULT_FIELDS[1:],
    *APK_BLE_MTU_RESULT_FIELDS,
)
APK_BLE_ADAPTER_STATE_RESULT_FIELDS = (
    "available",
    "discovering",
)
APK_BLE_NOTIFICATION_EVENT_FIELDS = (
    "deviceId",
    "serviceUuid",
    "characteristicUuid",
    "value",
)
APK_BLE_CONNECTION_EVENT_FIELDS = (
    "deviceId",
    "connected",
)
APK_BLE_DEVICE_FOUND_EVENT_FIELDS = (
    "id",
    "name",
    "rssi",
    "serviceData",
    "manufacturerData",
)
APK_BLE_DESCRIPTOR_UUIDS = (
    "00002902-0000-1000-8000-00805f9b34fb",
)
APK_BLE_BOOLEAN_EVENT_CHANNELS = (
    "com.spled.plugins/flutter_ble/bluetooth_adapter_state_changed",
    "com.spled.plugins/flutter_ble/bluetooth_device_discovery_state_changed",
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
APK_BLE_NOTIFICATION_STRING_HINTS = (
    "com.spled.plugins/flutter_ble/ble_characteristic_value_changed",
    "deviceId",
    "serviceUuid",
    "characteristicUuid",
    "value",
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
class BLEPluginErrorHint:
    """One decompiled BLE plugin error-code fact from the BanlanX APK."""

    code: str
    meaning: str
    trigger: str
    evidence: str


@dataclass(frozen=True, slots=True)
class BLEPluginEventHint:
    """One decompiled BLE plugin event-payload fact from the BanlanX APK."""

    channel: str
    fields: tuple[str, ...]
    behavior: str
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


@dataclass(frozen=True, slots=True)
class BLEIssueAdvertisement:
    """One old-UniLED issue advertisement shape pinned as discovery evidence."""

    issue: str
    model_name: str
    manufacturer_id: int
    manufacturer_payload_hex: str
    service_uuid: str
    evidence: str
    model_id: int | None = None


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
OLD_UNILED_ISSUE_ADVERTISEMENTS = (
    BLEIssueAdvertisement(
        issue="#45",
        model_name="SP63AE",
        manufacturer_id=20563,
        manufacturer_payload_hex="29 10 32 00 00 00 1a a6",
        service_uuid=UUID_BASE.format("e0ff"),
        evidence="SP63AE old-UniLED issue #45 advertisement log",
    ),
    BLEIssueAdvertisement(
        issue="#57",
        model_name="SP617E",
        manufacturer_id=20563,
        manufacturer_payload_hex="17 11 41 00 00 00 26 19",
        service_uuid=UUID_BASE.format("e0ff"),
        evidence="SP617E old-UniLED issue #57 advertisement log",
    ),
    BLEIssueAdvertisement(
        issue="#60",
        model_name="SP621E",
        manufacturer_id=20563,
        manufacturer_payload_hex="0d 00 ff 23 06 03 21 f3",
        service_uuid=UUID_BASE.format("e0ff"),
        evidence="SP621E old-UniLED issue #60 advertisement log",
    ),
    BLEIssueAdvertisement(
        issue="#78",
        model_name="SP642E",
        manufacturer_id=20563,
        manufacturer_payload_hex="4a 10 35 00 00 00 15 f5",
        service_uuid=UUID_BASE.format("e0ff"),
        evidence="SP642E old-UniLED issue #78 advertisement log",
    ),
    BLEIssueAdvertisement(
        issue="#69",
        model_name="SP110E",
        manufacturer_id=65535,
        manufacturer_payload_hex="10 00 0c 91",
        service_uuid=UUID_BASE.format("ffe0"),
        evidence="SP110E old-UniLED issue #69 advertisement log",
    ),
    BLEIssueAdvertisement(
        issue="#105",
        model_name="SP611E",
        manufacturer_id=20563,
        manufacturer_payload_hex="10 00 21 06 28 00 4e 44",
        service_uuid=UUID_BASE.format("e0ff"),
        evidence="SP611E old-UniLED issue #105 advertisement log",
    ),
    BLEIssueAdvertisement(
        issue="#111",
        model_name="SP107E",
        manufacturer_id=21301,
        manufacturer_payload_hex="1a 05 98 9e",
        service_uuid=UUID_BASE.format("ffb0"),
        evidence="SP107E old-UniLED issue #111 advertisement log",
    ),
    BLEIssueAdvertisement(
        issue="#120",
        model_name="SP538E",
        manufacturer_id=20563,
        manufacturer_payload_hex="56 f0 90 e5 b1 34 d0 9e",
        service_uuid=UUID_BASE.format("ffe1"),
        evidence="SP538E old-UniLED issue #120 advertisement log",
        model_id=0x56,
    ),
    BLEIssueAdvertisement(
        issue="#120",
        model_name="SP548E",
        manufacturer_id=20563,
        manufacturer_payload_hex="63 f0 bc 17 d6 be 0d bc",
        service_uuid=UUID_BASE.format("ffe1"),
        evidence="SP548E old-UniLED issue #120 advertisement log",
        model_id=0x63,
    ),
    BLEIssueAdvertisement(
        issue="#122",
        model_name="SP608E",
        manufacturer_id=20563,
        manufacturer_payload_hex="05 01 fc 58 fa a7 9a ee",
        service_uuid=UUID_BASE.format("ffb0"),
        evidence="SP608E old-UniLED issue #122 advertisement log",
    ),
    BLEIssueAdvertisement(
        issue="#132",
        model_name="SP542E",
        manufacturer_id=20563,
        manufacturer_payload_hex="5d 10 54 20 24 00 27 16",
        service_uuid=UUID_BASE.format("ffe0"),
        evidence="SP542E old-UniLED issue #132 advertisement log",
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
    BLEPluginContractHint(
        method="startBluetoothDevicesDiscovery",
        required_arguments=(),
        default_arguments=(
            "interval=0",
            "clearPreDiscoveredDevices=False",
            "aliveTime=10000",
        ),
        behavior=(
            "starts Android BLE scanning, optionally filters by service UUIDs, "
            "clears or refreshes cached discoveries, and uses report delay "
            "only when interval is positive and batching is supported"
        ),
        error_code="10000/10001",
        evidence=(
            "p185q2/C2233g.java applies discovery defaults and "
            "p180p2/C2198h.java builds scan filters/report delay"
        ),
    ),
    BLEPluginContractHint(
        method="stopBluetoothDevicesDiscovery",
        required_arguments=(),
        default_arguments=(),
        behavior="sets discovery state false and stops the Android BLE scanner",
        error_code=None,
        evidence="p185q2/C2233g.java dispatches C2199i stopScan and returns null",
    ),
    BLEPluginContractHint(
        method="getBluetoothDevices",
        required_arguments=(),
        default_arguments=(),
        behavior="returns the cached discovered-device maps from the BLE manager",
        error_code="10000/10001",
        evidence="p185q2/C2233g.java serializes discovered devices with C2252k.m4201a",
    ),
)

APK_BLE_PLUGIN_ERROR_HINTS = (
    BLEPluginErrorHint(
        code="10000",
        meaning="Bluetooth adapter is not opened/enabled",
        trigger="BLE operations are attempted before openBluetoothAdapter succeeds",
        evidence=(
            "p180p2/C2200j.java, p185q2/C2229c.java, and "
            "p185q2/C2233g.java raise 10000 before BLE dispatch"
        ),
    ),
    BLEPluginErrorHint(
        code="10001",
        meaning="Bluetooth adapter is unavailable",
        trigger="Android BluetoothManager returns no usable adapter",
        evidence="p189r2/C2242a.java default constructor raises 10001",
    ),
    BLEPluginErrorHint(
        code="10002",
        meaning="No cached/discovered device exists for the supplied deviceId",
        trigger="device lookup misses connected and discovered device maps",
        evidence="p189r2/C2242a.java device-id constructor raises 10002",
    ),
    BLEPluginErrorHint(
        code="10003",
        meaning="BLE connection failed",
        trigger="connection callback reports a non-timeout failure status",
        evidence="p185q2/RunnableC2231e.java maps connection failures to 10003",
    ),
    BLEPluginErrorHint(
        code="10004",
        meaning="Requested service UUID was not found on the device",
        trigger="BluetoothGatt.getService returns null",
        evidence="p189r2/C2249h.java raises 10004 for missing service UUIDs",
    ),
    BLEPluginErrorHint(
        code="10005",
        meaning="Requested characteristic UUID was not found on the service",
        trigger="BluetoothGattService.getCharacteristic returns null",
        evidence="p189r2/C2249h.java raises 10005 for missing characteristics",
    ),
    BLEPluginErrorHint(
        code="10006",
        meaning="Device is not connected",
        trigger="service/characteristic operation is attempted without a live GATT",
        evidence="p189r2/C2249h.java raises 10006 when the GATT is not connected",
    ),
    BLEPluginErrorHint(
        code="10008",
        meaning="Generic BLE operation failure",
        trigger=(
            "scan failures, notification-enable failures, adapter-disable "
            "failures, or unknown async exceptions"
        ),
        evidence=(
            "p180p2/C2197g.java, p189r2/C2246e.java, "
            "p185q2/C2229c.java, and p096X0/RunnableC0845g.java emit 10008"
        ),
    ),
    BLEPluginErrorHint(
        code="10012",
        meaning="BLE connection timed out",
        trigger="connection status callback reports timeout sentinel -2",
        evidence="p185q2/RunnableC2231e.java maps timeout status -2 to 10012",
    ),
    BLEPluginErrorHint(
        code="10013",
        meaning="Required method argument is missing",
        trigger="deviceId, serviceUuid, characteristicUuid, or value is null",
        evidence="p185q2/C2229c.java validates required arguments with 10013",
    ),
)

APK_BLE_PLUGIN_EVENT_HINTS = (
    BLEPluginEventHint(
        channel="com.spled.plugins/flutter_ble/bluetooth_device_found",
        fields=APK_BLE_DEVICE_FOUND_EVENT_FIELDS,
        behavior=(
            "emits discovered BLE devices with address, display name, RSSI, "
            "service data, and manufacturer data"
        ),
        evidence="p189r2/C2252k.java builds the bluetooth_device_found map",
    ),
    BLEPluginEventHint(
        channel="com.spled.plugins/flutter_ble/ble_connection_state_changed",
        fields=APK_BLE_CONNECTION_EVENT_FIELDS,
        behavior="emits a device address and boolean connection state",
        evidence="p180p2/C2196f.java posts deviceId/connected",
    ),
    BLEPluginEventHint(
        channel="com.spled.plugins/flutter_ble/ble_characteristic_value_changed",
        fields=APK_BLE_NOTIFICATION_EVENT_FIELDS,
        behavior=(
            "emits characteristic notifications with device, service, "
            "characteristic, and raw value bytes"
        ),
        evidence="p189r2/C2243b.java posts characteristic notification values",
    ),
)


@dataclass(frozen=True, slots=True)
class BLEProfile:
    """BLE service and characteristic UUIDs for one model."""

    service_uuids: tuple[str, ...]
    write_uuid: str
    notify_uuid: str | None = None
    fallback_write_uuids: tuple[str, ...] = ()
    fallback_notify_uuids: tuple[str, ...] = ()

    @property
    def notification_uuid(self) -> str:
        """Return explicit notify UUID or write UUID fallback."""
        return self.notify_uuid or self.write_uuid

    @property
    def write_uuid_candidates(self) -> tuple[str, ...]:
        """Return preferred write UUID followed by issue-backed fallbacks."""
        return (self.write_uuid, *self.fallback_write_uuids)

    @property
    def notification_uuid_candidates(self) -> tuple[str, ...]:
        """Return preferred notify UUID followed by issue-backed fallbacks."""
        fallback_notify = (
            self.fallback_notify_uuids
            if self.notify_uuid is not None
            else self.fallback_write_uuids
        )
        return (self.notification_uuid, *fallback_notify)


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
    scan_result_fields: tuple[str, ...] = APK_BLE_SCAN_RESULT_FIELDS
    service_result_fields: tuple[str, ...] = APK_BLE_SERVICE_RESULT_FIELDS
    characteristic_result_fields: tuple[
        str, ...
    ] = APK_BLE_CHARACTERISTIC_RESULT_FIELDS
    rssi_result_fields: tuple[str, ...] = APK_BLE_RSSI_RESULT_FIELDS
    mtu_result_fields: tuple[str, ...] = APK_BLE_MTU_RESULT_FIELDS
    adapter_state_result_fields: tuple[
        str, ...
    ] = APK_BLE_ADAPTER_STATE_RESULT_FIELDS
    notification_event_fields: tuple[str, ...] = APK_BLE_NOTIFICATION_EVENT_FIELDS
    connection_event_fields: tuple[str, ...] = APK_BLE_CONNECTION_EVENT_FIELDS
    device_found_event_fields: tuple[str, ...] = APK_BLE_DEVICE_FOUND_EVENT_FIELDS
    descriptor_uuids: tuple[str, ...] = APK_BLE_DESCRIPTOR_UUIDS
    boolean_event_channels: tuple[str, ...] = APK_BLE_BOOLEAN_EVENT_CHANNELS
    plugin_event_hints: tuple[BLEPluginEventHint, ...] = APK_BLE_PLUGIN_EVENT_HINTS
    plugin_contract_hints: tuple[
        BLEPluginContractHint, ...
    ] = APK_BLE_PLUGIN_CONTRACT_HINTS
    plugin_error_hints: tuple[BLEPluginErrorHint, ...] = APK_BLE_PLUGIN_ERROR_HINTS
    protocol_gap_hints: tuple[str, ...] = APK_BLE_PROTOCOL_GAP_HINTS
    issue_advertisements: tuple[BLEIssueAdvertisement, ...] = ()

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
    if model.family is ProtocolFamily.BANLANX_60X:
        return BLEProfile(
            service_uuids=(_uuid16("ffe0"), _uuid16("ffb0")),
            write_uuid=_uuid16("ffe1"),
            fallback_write_uuids=(_uuid16("ffb1"),),
        )

    if model.family is ProtocolFamily.LEGACY_LED_CHORD:
        return BLEProfile(
            service_uuids=(_uuid16("ffe0"), _uuid16("ffb0")),
            write_uuid=_uuid16("ffe1"),
            fallback_write_uuids=(_uuid16("ffb1"),),
        )

    if model.family in {
        ProtocolFamily.BANLANX_601,
        ProtocolFamily.BANLANX_V3,
        ProtocolFamily.LEGACY_LED_HUE,
    }:
        return BLEProfile(
            service_uuids=(_uuid16("ffe0"),),
            write_uuid=_uuid16("ffe1"),
        )

    if model.family is ProtocolFamily.BANLANX_V2:
        return BLEProfile(
            service_uuids=(_uuid16("ffe0"), _uuid16("e0ff")),
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
        issue_advertisements=_issue_advertisements_for_model(model),
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
    parts.append(f"scan_result_fields={len(profile.scan_result_fields)}")
    parts.append(f"service_result_fields={len(profile.service_result_fields)}")
    parts.append(
        f"characteristic_result_fields={len(profile.characteristic_result_fields)}"
    )
    parts.append(f"rssi_result_fields={len(profile.rssi_result_fields)}")
    parts.append(f"mtu_result_fields={len(profile.mtu_result_fields)}")
    parts.append(f"adapter_state_fields={len(profile.adapter_state_result_fields)}")
    parts.append(f"notification_fields={len(profile.notification_event_fields)}")
    parts.append(f"connection_fields={len(profile.connection_event_fields)}")
    parts.append(f"device_found_fields={len(profile.device_found_event_fields)}")
    parts.append(f"descriptors={len(profile.descriptor_uuids)}")
    parts.append(f"boolean_events={len(profile.boolean_event_channels)}")
    parts.append(f"event_contracts={len(profile.plugin_event_hints)}")
    parts.append(f"plugin_contracts={len(profile.plugin_contract_hints)}")
    parts.append(f"error_codes={len(profile.plugin_error_hints)}")
    parts.append(f"channels={len(profile.plugin_channels)}")
    parts.append(f"gaps={len(profile.protocol_gap_hints)}")
    parts.append(f"issue_adverts={len(profile.issue_advertisements)}")
    return "; ".join(parts)


def _uuid16(part: str) -> str:
    return UUID_BASE.format(part.lower())


def _issue_advertisements_for_model(
    model: CatalogModel,
) -> tuple[BLEIssueAdvertisement, ...]:
    """Return old issue advertisement fixtures that match a catalog model."""
    return tuple(
        advertisement
        for advertisement in OLD_UNILED_ISSUE_ADVERTISEMENTS
        if advertisement.model_name == model.name
        and (
            advertisement.model_id is None
            or advertisement.model_id == model.model_id
        )
    )
