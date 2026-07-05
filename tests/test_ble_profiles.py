"""BLE profile tests."""

from __future__ import annotations

from custom_components.uniled.core import default_catalog
from custom_components.uniled.core.transports import (
    ble_evidence_for_model,
    ble_profile_for_model,
    describe_ble_evidence_profile,
)
from custom_components.uniled.core.transports.ble import (
    APK_BLE_PLUGIN_CONTRACT_HINTS,
    APK_BLE_PLUGIN_CONTRACT_STRING_HINTS,
    APK_BLE_UUID_INVENTORY,
    APK_BLE_UUID_STRING_HINTS,
)


def test_legacy_ble_families_use_ffe0_ffe1_profile() -> None:
    """Old UniLED parity families use service ffe0 and write/notify ffe1."""
    catalog = default_catalog()

    for name in ("SP601E", "SP602E", "SP611E", "SP613E"):
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


def test_legacy_only_ble_families_keep_old_uuid_binding() -> None:
    """Old LED Chord/Hue models keep ffe0/ffe1 binding with command parity."""
    catalog = default_catalog()

    for name in ("SP107E", "SP110E"):
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
            "arguments=12; result_fields=11; plugin_contracts=6; "
            "channels=6; gaps=3"
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
        assert evidence.plugin_contract_hints == APK_BLE_PLUGIN_CONTRACT_HINTS
        assert describe_ble_evidence_profile(evidence) == (
            f"{model.family.value}; command_profile_pending; "
            "apk_uuid_pool=5; uuid_inventory=5; unbound_uuid_candidates=3; "
            "legacy_uuid_candidates=2; plugin_methods=14; arguments=12; "
            "result_fields=11; plugin_contracts=6; channels=6; gaps=3"
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
    assert len(APK_BLE_PLUGIN_CONTRACT_HINTS) == 6
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
    assert all("C2229c.java" in hint.evidence for hint in APK_BLE_PLUGIN_CONTRACT_HINTS)
