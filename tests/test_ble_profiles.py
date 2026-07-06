"""BLE profile tests."""

from __future__ import annotations

from custom_components.uniled.core import default_catalog
from custom_components.uniled.core.transports import (
    ble_evidence_for_model,
    ble_profile_for_model,
    describe_ble_evidence_profile,
)
from custom_components.uniled.core.transports.ble import (
    APK_BLE_ADAPTER_STATE_RESULT_FIELDS,
    APK_BLE_BOOLEAN_EVENT_CHANNELS,
    APK_BLE_CHARACTERISTIC_RESULT_FIELDS,
    APK_BLE_CONNECTION_EVENT_FIELDS,
    APK_BLE_DESCRIPTOR_UUIDS,
    APK_BLE_DEVICE_FOUND_EVENT_FIELDS,
    APK_BLE_MTU_RESULT_FIELDS,
    APK_BLE_NOTIFICATION_EVENT_FIELDS,
    APK_BLE_NOTIFICATION_STRING_HINTS,
    APK_BLE_PLUGIN_CONTRACT_HINTS,
    APK_BLE_PLUGIN_CONTRACT_STRING_HINTS,
    APK_BLE_PLUGIN_ERROR_HINTS,
    APK_BLE_PLUGIN_EVENT_HINTS,
    APK_BLE_RSSI_RESULT_FIELDS,
    APK_BLE_SCAN_RESULT_FIELDS,
    APK_BLE_SERVICE_RESULT_FIELDS,
    APK_BLE_UUID_INVENTORY,
    APK_BLE_UUID_STRING_HINTS,
)


def test_legacy_ble_families_use_ffe0_ffe1_profile() -> None:
    """Old UniLED parity families use service ffe0 and write/notify ffe1."""
    catalog = default_catalog()

    for name in ("SP601E", "SP613E"):
        model = catalog.resolve_name(name)
        assert model is not None

        profile = ble_profile_for_model(model)

        assert profile is not None
        assert profile.service_uuids == ("0000ffe0-0000-1000-8000-00805f9b34fb",)
        assert profile.write_uuid == "0000ffe1-0000-1000-8000-00805f9b34fb"
        assert profile.notification_uuid == profile.write_uuid

        evidence = ble_evidence_for_model(model)

        assert evidence is not None
        assert evidence.command_profile_known is True
        assert evidence.known_service_uuids == profile.service_uuids
        assert evidence.known_write_uuid == profile.write_uuid
        assert evidence.known_notify_uuid == profile.notification_uuid


def test_banlanx_v2_profile_accepts_issue_105_e0ff_service() -> None:
    """SP611E-style v2 models accept issue-reported e0ff service fallback."""
    catalog = default_catalog()

    for name in ("SP611E", "SP616E", "SP617E", "SP620E", "SP621E"):
        model = catalog.resolve_name(name)
        assert model is not None

        profile = ble_profile_for_model(model)

        assert profile is not None
        assert profile.service_uuids == (
            "0000ffe0-0000-1000-8000-00805f9b34fb",
            "0000e0ff-0000-1000-8000-00805f9b34fb",
        )
        assert profile.write_uuid == "0000ffe1-0000-1000-8000-00805f9b34fb"
        assert profile.write_uuid_candidates == (
            "0000ffe1-0000-1000-8000-00805f9b34fb",
        )
        assert profile.notification_uuid_candidates == profile.write_uuid_candidates

        evidence = ble_evidence_for_model(model)

        assert evidence is not None
        assert evidence.command_profile_known is True
        assert evidence.known_service_uuids == profile.service_uuids
        assert evidence.known_write_uuid == profile.write_uuid


def test_banlanx_60x_profile_accepts_issue_122_ffb0_variant() -> None:
    """SP602E/SP608E accept issue-reported ffb0/ffb1 BLE variants."""
    catalog = default_catalog()

    for name in ("SP602E", "SP608E"):
        model = catalog.resolve_name(name)
        assert model is not None

        profile = ble_profile_for_model(model)

        assert profile is not None
        assert profile.service_uuids == (
            "0000ffe0-0000-1000-8000-00805f9b34fb",
            "0000ffb0-0000-1000-8000-00805f9b34fb",
        )
        assert profile.write_uuid == "0000ffe1-0000-1000-8000-00805f9b34fb"
        assert profile.fallback_write_uuids == (
            "0000ffb1-0000-1000-8000-00805f9b34fb",
        )
        assert profile.write_uuid_candidates == (
            "0000ffe1-0000-1000-8000-00805f9b34fb",
            "0000ffb1-0000-1000-8000-00805f9b34fb",
        )
        assert profile.notification_uuid_candidates == profile.write_uuid_candidates

        evidence = ble_evidence_for_model(model)

        assert evidence is not None
        assert evidence.command_profile_known is True
        assert evidence.known_service_uuids == profile.service_uuids
        assert evidence.known_write_uuid == profile.write_uuid
        assert describe_ble_evidence_profile(evidence).startswith(
            "banlanx_60x; command_profile_known; services=2; "
            "write_uuid_known"
        )


def test_legacy_led_chord_profile_accepts_issue_111_ffb0_variant() -> None:
    """SP107E accepts issue-reported ffb0/ffb1 BLE variants."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP107E")
    assert model is not None

    profile = ble_profile_for_model(model)
    evidence = ble_evidence_for_model(model)

    assert profile is not None
    assert profile.service_uuids == (
        "0000ffe0-0000-1000-8000-00805f9b34fb",
        "0000ffb0-0000-1000-8000-00805f9b34fb",
    )
    assert profile.write_uuid == "0000ffe1-0000-1000-8000-00805f9b34fb"
    assert profile.fallback_write_uuids == (
        "0000ffb1-0000-1000-8000-00805f9b34fb",
    )
    assert profile.write_uuid_candidates == (
        "0000ffe1-0000-1000-8000-00805f9b34fb",
        "0000ffb1-0000-1000-8000-00805f9b34fb",
    )
    assert profile.notification_uuid_candidates == profile.write_uuid_candidates
    assert evidence is not None
    assert evidence.command_profile_known is True
    assert evidence.known_service_uuids == profile.service_uuids
    assert evidence.known_write_uuid == profile.write_uuid


def test_legacy_led_hue_family_keeps_old_uuid_binding() -> None:
    """Old LED Hue models keep ffe0/ffe1 binding with command parity."""
    catalog = default_catalog()

    for name in ("SP110E",):
        model = catalog.resolve_name(name)
        assert model is not None

        profile = ble_profile_for_model(model)
        evidence = ble_evidence_for_model(model)

        assert profile is not None
        assert profile.service_uuids == ("0000ffe0-0000-1000-8000-00805f9b34fb",)
        assert profile.write_uuid == "0000ffe1-0000-1000-8000-00805f9b34fb"
        assert evidence is not None
        assert evidence.command_profile_known is True
        assert evidence.known_service_uuids == profile.service_uuids
        assert evidence.known_write_uuid == profile.write_uuid


def test_banlanx_6xx_ble_profile_accepts_both_known_services() -> None:
    """SP6xx-style profiles accept e0ff and ffe0 service UUIDs."""
    catalog = default_catalog()

    for name in ("SP630E", "SP530E"):
        model = catalog.resolve_name(name)
        assert model is not None

        profile = ble_profile_for_model(model)

        assert profile is not None
        assert profile.service_uuids == (
            "0000e0ff-0000-1000-8000-00805f9b34fb",
            "0000ffe0-0000-1000-8000-00805f9b34fb",
        )
        assert profile.write_uuid == "0000ffe1-0000-1000-8000-00805f9b34fb"
        assert describe_ble_evidence_profile(ble_evidence_for_model(model)) == (
            f"{model.family.value}; command_profile_known; services=2; "
            "write_uuid_known; apk_uuid_pool=5; uuid_inventory=5; "
            "unbound_uuid_candidates=3; legacy_uuid_candidates=2; plugin_methods=14; "
            "arguments=12; result_fields=13; scan_result_fields=5; "
            "service_result_fields=2; characteristic_result_fields=6; "
            "rssi_result_fields=1; mtu_result_fields=1; adapter_state_fields=2; "
            "notification_fields=4; connection_fields=2; device_found_fields=5; "
            "descriptors=1; boolean_events=2; event_contracts=3; "
            "plugin_contracts=9; error_codes=10; channels=6; gaps=3; "
            "issue_adverts=0"
        )


def test_unported_families_do_not_claim_a_ble_profile_yet() -> None:
    """Families without command protocols are not assigned a BLE profile yet."""
    catalog = default_catalog()

    for name in ("SP660E", "SP701E", "FT001", "RG4"):
        model = catalog.resolve_name(name)
        assert model is not None

        assert ble_profile_for_model(model) is None


def test_unported_direct_ble_families_keep_apk_ble_evidence() -> None:
    """Recognized BLE families expose APK UUID/plugin facts without commands."""
    catalog = default_catalog()

    for name in ("SP660E", "SP701E", "FT001", "SP802E"):
        model = catalog.resolve_name(name)
        assert model is not None

        evidence = ble_evidence_for_model(model)

        assert evidence is not None
        assert evidence.command_profile_known is False
        assert evidence.known_service_uuids == ()
        assert evidence.known_write_uuid is None
        assert evidence.known_notify_uuid is None
        assert evidence.apk_uuid_pool == (
            "0000ff12-0000-1000-8000-00805f9b34fb",
            "0000ff14-0000-1000-8000-00805f9b34fb",
            "0000ff15-0000-1000-8000-00805f9b34fb",
            "0000ffe0-0000-1000-8000-00805f9b34fb",
            "0000ffe1-0000-1000-8000-00805f9b34fb",
        )
        assert evidence.uuid_inventory == APK_BLE_UUID_INVENTORY
        assert evidence.uuid_binding_status == (
            "binding=pending; services=0; write=pending; notify=pending; "
            "unbound_candidates=3; legacy_candidates=2"
        )
        assert [
            candidate.short_name for candidate in evidence.unbound_uuid_candidates
        ] == [
            "ff12",
            "ff14",
            "ff15",
        ]
        assert [
            candidate.short_name for candidate in evidence.legacy_uuid_candidates
        ] == [
            "ffe0",
            "ffe1",
        ]
        assert [candidate.short_name for candidate in evidence.uuid_inventory] == [
            "ff12",
            "ff14",
            "ff15",
            "ffe0",
            "ffe1",
        ]
        assert [
            candidate.known_usage for candidate in evidence.uuid_inventory
        ] == [
            "unbound_candidate",
            "unbound_candidate",
            "unbound_candidate",
            "legacy_service_uuid",
            "legacy_write_notify_uuid",
        ]
        assert all(
            candidate.unported_binding_status == "unproven"
            for candidate in evidence.uuid_inventory
        )
        assert "writeBleCharacteristicValue" in evidence.plugin_methods
        assert "notifyBleCharacteristicValueChange" in evidence.plugin_methods
        assert "openBluetoothAdapter" in evidence.plugin_methods
        assert "startBluetoothDevicesDiscovery" in evidence.plugin_methods
        assert "getBluetoothDeviceRssi" in evidence.plugin_methods
        assert "serviceUuid" in evidence.plugin_arguments
        assert "characteristicUuid" in evidence.plugin_arguments
        assert "clearPreDiscoveredDevices" in evidence.plugin_arguments
        assert "supportWriteNoResponse" in evidence.plugin_result_fields
        assert "manufacturerData" in evidence.plugin_result_fields
        assert "isPrimary" in evidence.plugin_result_fields
        assert "value" in evidence.plugin_result_fields
        assert evidence.scan_result_fields == APK_BLE_SCAN_RESULT_FIELDS
        assert evidence.service_result_fields == APK_BLE_SERVICE_RESULT_FIELDS
        assert (
            evidence.characteristic_result_fields
            == APK_BLE_CHARACTERISTIC_RESULT_FIELDS
        )
        assert evidence.rssi_result_fields == APK_BLE_RSSI_RESULT_FIELDS
        assert evidence.mtu_result_fields == APK_BLE_MTU_RESULT_FIELDS
        assert (
            evidence.adapter_state_result_fields
            == APK_BLE_ADAPTER_STATE_RESULT_FIELDS
        )
        assert evidence.notification_event_fields == APK_BLE_NOTIFICATION_EVENT_FIELDS
        assert evidence.connection_event_fields == APK_BLE_CONNECTION_EVENT_FIELDS
        assert evidence.device_found_event_fields == APK_BLE_DEVICE_FOUND_EVENT_FIELDS
        assert evidence.descriptor_uuids == APK_BLE_DESCRIPTOR_UUIDS
        assert evidence.boolean_event_channels == APK_BLE_BOOLEAN_EVENT_CHANNELS
        assert evidence.plugin_event_hints == APK_BLE_PLUGIN_EVENT_HINTS
        assert evidence.plugin_contract_hints == APK_BLE_PLUGIN_CONTRACT_HINTS
        assert evidence.plugin_error_hints == APK_BLE_PLUGIN_ERROR_HINTS
        assert evidence.issue_advertisements == ()
        assert describe_ble_evidence_profile(evidence) == (
            f"{model.family.value}; command_profile_pending; "
            "apk_uuid_pool=5; uuid_inventory=5; unbound_uuid_candidates=3; "
            "legacy_uuid_candidates=2; plugin_methods=14; arguments=12; "
            "result_fields=13; scan_result_fields=5; service_result_fields=2; "
            "characteristic_result_fields=6; rssi_result_fields=1; "
            "mtu_result_fields=1; adapter_state_fields=2; notification_fields=4; "
            "connection_fields=2; device_found_fields=5; descriptors=1; "
            "boolean_events=2; event_contracts=3; "
            "plugin_contracts=9; error_codes=10; channels=6; gaps=3; "
            "issue_adverts=0"
        )

    mesh_model = catalog.resolve_name("RG4")
    assert mesh_model is not None
    assert ble_evidence_for_model(mesh_model) is None


def test_ble_uuid_inventory_keeps_normalized_and_raw_apk_anchors() -> None:
    """Normalized UUID diagnostics stay linked to exact APK string rows."""
    assert len(APK_BLE_UUID_INVENTORY) == 5
    assert len(APK_BLE_UUID_STRING_HINTS) == 10
    assert tuple(candidate.apk_string for candidate in APK_BLE_UUID_INVENTORY) == (
        "0000ff12-0000-1000-8000-00805f9b34fb2",
        "0000ff14-0000-1000-8000-00805f9b34fb2",
        "0000ff15-0000-1000-8000-00805f9b34fb2",
        "0000ffe0-0000-1000-8000-00805f9b34fb2",
        "0000ffe1-0000-1000-8000-00805f9b34fb2",
    )
    assert tuple(candidate.uuid for candidate in APK_BLE_UUID_INVENTORY) == (
        "0000ff12-0000-1000-8000-00805f9b34fb",
        "0000ff14-0000-1000-8000-00805f9b34fb",
        "0000ff15-0000-1000-8000-00805f9b34fb",
        "0000ffe0-0000-1000-8000-00805f9b34fb",
        "0000ffe1-0000-1000-8000-00805f9b34fb",
    )


def test_ble_plugin_contract_hints_capture_decompiled_call_defaults() -> None:
    """Structured BLE bridge contracts mirror the decompiled Java plugin."""
    assert len(APK_BLE_PLUGIN_CONTRACT_HINTS) == 9
    assert APK_BLE_PLUGIN_CONTRACT_STRING_HINTS == (
        "serviceUuid",
        "characteristicUuid",
        "value",
        "enabled",
        "timeout",
        "characteristicWriteType",
        "forceWaitResponse",
    )

    notify = next(
        hint
        for hint in APK_BLE_PLUGIN_CONTRACT_HINTS
        if hint.method == "notifyBleCharacteristicValueChange"
    )
    write = next(
        hint
        for hint in APK_BLE_PLUGIN_CONTRACT_HINTS
        if hint.method == "writeBleCharacteristicValue"
        and "writes raw bytes" in hint.behavior
    )
    write_type = next(
        hint
        for hint in APK_BLE_PLUGIN_CONTRACT_HINTS
        if hint.method == "writeBleCharacteristicValue"
        and "characteristicWriteType=1" in hint.behavior
    )
    discovery = next(
        hint
        for hint in APK_BLE_PLUGIN_CONTRACT_HINTS
        if hint.method == "startBluetoothDevicesDiscovery"
    )
    stop_discovery = next(
        hint
        for hint in APK_BLE_PLUGIN_CONTRACT_HINTS
        if hint.method == "stopBluetoothDevicesDiscovery"
    )
    get_devices = next(
        hint
        for hint in APK_BLE_PLUGIN_CONTRACT_HINTS
        if hint.method == "getBluetoothDevices"
    )

    assert notify.required_arguments == ("serviceUuid", "characteristicUuid")
    assert notify.default_arguments == ("enabled=False",)
    assert notify.error_code == "10013"
    assert write.required_arguments == (
        "serviceUuid",
        "characteristicUuid",
        "value",
    )
    assert write.default_arguments == ("forceWaitResponse=False",)
    assert write.error_code == "10013"
    assert write_type.default_arguments == ("characteristicWriteType=None",)
    assert write_type.error_code is None
    assert discovery.default_arguments == (
        "interval=0",
        "clearPreDiscoveredDevices=False",
        "aliveTime=10000",
    )
    assert discovery.error_code == "10000/10001"
    assert "service UUIDs" in discovery.behavior
    assert "C2198h.java" in discovery.evidence
    assert stop_discovery.default_arguments == ()
    assert stop_discovery.error_code is None
    assert "stopScan" in stop_discovery.evidence
    assert get_devices.error_code == "10000/10001"
    assert "discovered-device maps" in get_devices.behavior
    assert all(
        hint.evidence.startswith("p")
        for hint in APK_BLE_PLUGIN_CONTRACT_HINTS
    )


def test_ble_result_fields_capture_decompiled_bridge_responses() -> None:
    """Structured result facts mirror decompiled Java plugin response maps."""
    assert APK_BLE_SCAN_RESULT_FIELDS == (
        "id",
        "name",
        "rssi",
        "serviceData",
        "manufacturerData",
    )
    assert APK_BLE_SERVICE_RESULT_FIELDS == ("uuid", "isPrimary")
    assert APK_BLE_CHARACTERISTIC_RESULT_FIELDS == (
        "uuid",
        "supportWrite",
        "supportWriteNoResponse",
        "supportRead",
        "supportNotify",
        "supportIndicate",
    )
    assert APK_BLE_RSSI_RESULT_FIELDS == ("rssi",)
    assert APK_BLE_MTU_RESULT_FIELDS == ("value",)


def test_ble_plugin_error_hints_capture_decompiled_error_codes() -> None:
    """Structured error-code facts mirror the decompiled Java plugin."""
    assert [hint.code for hint in APK_BLE_PLUGIN_ERROR_HINTS] == [
        "10000",
        "10001",
        "10002",
        "10003",
        "10004",
        "10005",
        "10006",
        "10008",
        "10012",
        "10013",
    ]
    by_code = {hint.code: hint for hint in APK_BLE_PLUGIN_ERROR_HINTS}

    assert by_code["10000"].meaning == "Bluetooth adapter is not opened/enabled"
    assert "openBluetoothAdapter" in by_code["10000"].trigger
    assert by_code["10001"].meaning == "Bluetooth adapter is unavailable"
    assert "no usable adapter" in by_code["10001"].trigger
    assert "No cached/discovered device" in by_code["10002"].meaning
    assert by_code["10003"].meaning == "BLE connection failed"
    assert "service UUID" in by_code["10004"].meaning
    assert "characteristic UUID" in by_code["10005"].meaning
    assert by_code["10006"].meaning == "Device is not connected"
    assert "Generic BLE operation failure" == by_code["10008"].meaning
    assert by_code["10012"].meaning == "BLE connection timed out"
    assert by_code["10013"].meaning == "Required method argument is missing"
    assert all(hint.evidence.startswith("p") for hint in APK_BLE_PLUGIN_ERROR_HINTS)


def test_ble_notification_contract_hints_capture_decompiled_callback() -> None:
    """Structured callback facts mirror the decompiled Java plugin."""
    assert APK_BLE_NOTIFICATION_EVENT_FIELDS == (
        "deviceId",
        "serviceUuid",
        "characteristicUuid",
        "value",
    )
    assert APK_BLE_DESCRIPTOR_UUIDS == (
        "00002902-0000-1000-8000-00805f9b34fb",
    )
    assert APK_BLE_NOTIFICATION_STRING_HINTS == (
        "com.spled.plugins/flutter_ble/ble_characteristic_value_changed",
        *APK_BLE_NOTIFICATION_EVENT_FIELDS,
    )


def test_ble_event_hints_capture_decompiled_event_payloads() -> None:
    """Structured event facts mirror decompiled Java plugin payload maps."""
    assert APK_BLE_ADAPTER_STATE_RESULT_FIELDS == (
        "available",
        "discovering",
    )
    assert APK_BLE_DEVICE_FOUND_EVENT_FIELDS == (
        "id",
        "name",
        "rssi",
        "serviceData",
        "manufacturerData",
    )
    assert APK_BLE_CONNECTION_EVENT_FIELDS == ("deviceId", "connected")
    assert APK_BLE_BOOLEAN_EVENT_CHANNELS == (
        "com.spled.plugins/flutter_ble/bluetooth_adapter_state_changed",
        "com.spled.plugins/flutter_ble/bluetooth_device_discovery_state_changed",
    )
    assert len(APK_BLE_PLUGIN_EVENT_HINTS) == 3
    by_channel = {hint.channel: hint for hint in APK_BLE_PLUGIN_EVENT_HINTS}

    assert by_channel[
        "com.spled.plugins/flutter_ble/bluetooth_device_found"
    ].fields == APK_BLE_DEVICE_FOUND_EVENT_FIELDS
    assert by_channel[
        "com.spled.plugins/flutter_ble/ble_connection_state_changed"
    ].fields == APK_BLE_CONNECTION_EVENT_FIELDS
    assert by_channel[
        "com.spled.plugins/flutter_ble/ble_characteristic_value_changed"
    ].fields == APK_BLE_NOTIFICATION_EVENT_FIELDS
