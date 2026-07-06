"""Old UniLED parity audit tests."""

from __future__ import annotations

import json
from fnmatch import fnmatchcase
from pathlib import Path
from types import SimpleNamespace

from custom_components.uniled.const import (
    CONF_ADDRESS,
    CONF_DEVICE_ID,
    CONF_DISCOVERY_CONFIDENCE,
    CONF_DISCOVERY_MATCH,
    CONF_MESH_NODE_ID,
    CONF_MESH_NODE_TYPE,
    CONF_MESH_UUID,
    CONF_MODEL,
    CONF_MODEL_ID,
    CONF_TRANSPORT,
    DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
    DISCOVERY_MATCH_EXACT_LABEL,
    DISCOVERY_MATCH_SAFE_SUFFIX,
    DISCOVERY_MATCH_TELINK_MESH,
    TRANSPORT_BLE,
    TRANSPORT_BLE_MESH,
)
from custom_components.uniled.core import default_catalog
from custom_components.uniled.setup_data import (
    SetupDataError,
    bluetooth_setup_entry_data_from_discovery,
    migrate_legacy_entry_data,
    setup_entry_compatibility_unique_ids,
    setup_entry_requires_discovery_confirmation,
)
from scripts.audit_legacy_uniled import audit_legacy_uniled


def test_old_uniled_overlap_is_exactly_the_catalog_parity_set() -> None:
    """Old UniLED parity flags match the local old integration source files."""
    audit = audit_legacy_uniled(Path("..") / "uniled")

    assert len(audit.legacy_ble_names) == 51
    assert audit.legacy_net_names == ()
    assert len(audit.apk_overlap) == 49
    assert audit.catalog_legacy_names == audit.apk_overlap
    assert audit.legacy_only_names == ("SP107E", "SP110E")
    assert audit.catalog_legacy_only_names == audit.legacy_only_names
    assert audit.legacy_zengge_mesh_supported is True
    assert audit.missing_catalog_flags == ()
    assert audit.extra_catalog_flags == ()
    assert audit.missing_legacy_only_catalog_names == ()
    assert audit.extra_legacy_only_catalog_names == ()
    assert audit.legacy_recognized_names == ()
    assert audit.zengge_mesh_mismatches == ()
    assert audit.migration_mismatches == ()
    assert len(audit.command_surfaces) == 7
    assert audit.command_surface_mismatches == ()
    assert audit.autodiscovery_mismatches == ()
    assert audit.entity_identity_mismatches == ()
    assert "SP801E" not in audit.legacy_ble_names
    assert "SP802E" not in audit.legacy_ble_names
    assert "FT001" not in audit.legacy_ble_names
    assert "SP660E" not in audit.legacy_ble_names


def test_old_uniled_ble_names_wake_bluetooth_manifest_matchers() -> None:
    """Every old-UniLED BLE model can wake Home Assistant Bluetooth discovery."""
    audit = audit_legacy_uniled(Path("..") / "uniled")
    manifest = json.loads(
        Path("custom_components/uniled/manifest.json").read_text(encoding="utf-8")
    )
    patterns = tuple(
        matcher["local_name"]
        for matcher in manifest["bluetooth"]
        if "local_name" in matcher
    )

    assert "SP*" not in patterns
    assert [
        name
        for name in audit.legacy_ble_names
        if not any(fnmatchcase(name, pattern) for pattern in patterns)
    ] == []


def test_old_uniled_ble_names_resolve_from_exact_and_suffixed_discovery() -> None:
    """Every old-UniLED BLE name becomes a protocol-proven HA discovery entry."""
    audit = audit_legacy_uniled(Path("..") / "uniled")
    catalog = default_catalog()

    assert len(audit.legacy_ble_names) == 51
    for index, name in enumerate(audit.legacy_ble_names):
        exact_address = f"AA:BB:CC:10:{index:02X}:00"
        suffixed_address = f"AA:BB:CC:10:{index:02X}:01"
        exact = bluetooth_setup_entry_data_from_discovery(
            catalog,
            SimpleNamespace(
                name=name,
                address=exact_address,
                manufacturer_data={},
                connectable=True,
            ),
        )
        suffixed = bluetooth_setup_entry_data_from_discovery(
            catalog,
            SimpleNamespace(
                name="",
                local_name=f"{name}_AABB",
                address=suffixed_address,
                manufacturer_data={},
                connectable=True,
            ),
        )

        assert exact.data[CONF_MODEL] == name
        assert exact.data[CONF_ADDRESS] == exact_address
        assert exact.data[CONF_TRANSPORT] == TRANSPORT_BLE
        assert exact.data[CONF_DISCOVERY_MATCH] == DISCOVERY_MATCH_EXACT_LABEL
        assert (
            exact.data[CONF_DISCOVERY_CONFIDENCE]
            == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
        )
        assert setup_entry_requires_discovery_confirmation(exact) is False

        assert suffixed.data[CONF_MODEL] == name
        assert suffixed.data[CONF_ADDRESS] == suffixed_address
        assert suffixed.data[CONF_TRANSPORT] == TRANSPORT_BLE
        assert suffixed.data[CONF_DISCOVERY_MATCH] == DISCOVERY_MATCH_SAFE_SUFFIX
        assert (
            suffixed.data[CONF_DISCOVERY_CONFIDENCE]
            == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
        )
        assert setup_entry_requires_discovery_confirmation(suffixed) is False


def test_old_uniled_ble_autodiscovery_reports_legacy_duplicate_ids() -> None:
    """Every old BLE discovery setup can block raw-address old-UniLED entries."""
    audit = audit_legacy_uniled(Path("..") / "uniled")
    catalog = default_catalog()

    assert len(audit.legacy_ble_names) == 51
    for index, name in enumerate(audit.legacy_ble_names):
        address = f"AA:BB:CC:12:{index:02X}:00"
        setup = bluetooth_setup_entry_data_from_discovery(
            catalog,
            SimpleNamespace(
                name=name,
                address=address,
                manufacturer_data={},
                connectable=True,
            ),
        )

        assert setup.unique_id == f"ble:{address.casefold()}"
        assert setup_entry_compatibility_unique_ids(setup) == (
            address,
            address.casefold(),
        )


def test_old_uniled_ble_entries_migrate_catalog_wide() -> None:
    """Every old direct-BLE shape becomes a normalized UniLED Next BLE entry."""
    audit = audit_legacy_uniled(Path("..") / "uniled")
    catalog = default_catalog()

    assert len(audit.legacy_ble_names) == 51
    for index, name in enumerate(audit.legacy_ble_names):
        address = f"AA:BB:CC:13:{index:02X}:00"
        model = catalog.resolve_name(name)
        explicit = migrate_legacy_entry_data(
            catalog,
            {CONF_TRANSPORT: "ble", CONF_MODEL: name, CONF_ADDRESS: address},
        )
        inferred = migrate_legacy_entry_data(
            catalog,
            {CONF_MODEL: name, CONF_ADDRESS: address},
        )

        assert model is not None
        expected = {
            CONF_MODEL: name,
            CONF_MODEL_ID: model.model_id,
            CONF_ADDRESS: address,
            CONF_TRANSPORT: TRANSPORT_BLE,
        }
        assert explicit == expected
        assert inferred == expected


def test_old_uniled_zengge_entries_migrate_without_credentials() -> None:
    """Old Zengge entries preserve mesh identity and drop cloud credentials."""
    catalog = default_catalog()

    expected = {
        CONF_MODEL: "RG4",
        CONF_MODEL_ID: 44034,
        CONF_DEVICE_ID: "zng_mesh_0x211",
        CONF_MESH_UUID: 0x0211,
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }
    with_cloud = migrate_legacy_entry_data(
        catalog,
        {
            CONF_TRANSPORT: "zng",
            "mesh_id": "zng_mesh_0x211",
            CONF_MESH_UUID: "0x211",
            "username": "old@example.com",
            "password": "do-not-store",
            "country": "US",
        },
    )
    without_mesh_id = migrate_legacy_entry_data(
        catalog,
        {
            CONF_TRANSPORT: "zng",
            CONF_MESH_UUID: "0x211",
        },
    )

    assert with_cloud == expected
    assert without_mesh_id == expected


def test_old_uniled_zengge_mesh_discovery_resolves_without_confirmation() -> None:
    """Old RG4/Zengge discovery paths become protocol-proven mesh entries."""
    catalog = default_catalog()

    exact = bluetooth_setup_entry_data_from_discovery(
        catalog,
        SimpleNamespace(
            name="RG4",
            address="AA:BB:CC:21:00:00",
            manufacturer_data={},
            connectable=True,
        ),
    )
    telink = bluetooth_setup_entry_data_from_discovery(
        catalog,
        SimpleNamespace(
            name="Zengge",
            local_name="",
            address="AA:BB:CC:21:00:01",
            manufacturer_data={
                529: bytes.fromhex("11 02 00 00 00 00 00 23 00 44")
            },
            connectable=True,
        ),
    )

    assert exact.unique_id == "ble_mesh:aa:bb:cc:21:00:00"
    assert exact.data[CONF_MODEL] == "RG4"
    assert exact.data[CONF_ADDRESS] == "AA:BB:CC:21:00:00"
    assert exact.data[CONF_TRANSPORT] == TRANSPORT_BLE_MESH
    assert exact.data[CONF_DISCOVERY_MATCH] == DISCOVERY_MATCH_EXACT_LABEL
    assert (
        exact.data[CONF_DISCOVERY_CONFIDENCE]
        == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
    )
    assert setup_entry_requires_discovery_confirmation(exact) is False

    assert telink.unique_id == "zng_mesh_0x211"
    assert telink.data[CONF_MODEL] == "RG4"
    assert telink.data[CONF_ADDRESS] == "AA:BB:CC:21:00:01"
    assert telink.data[CONF_DEVICE_ID] == "zng_mesh_0x211"
    assert telink.data[CONF_MESH_UUID] == 0x0211
    assert telink.data[CONF_MESH_NODE_ID] == 0x44
    assert telink.data[CONF_MESH_NODE_TYPE] == 0x23
    assert telink.data[CONF_TRANSPORT] == TRANSPORT_BLE_MESH
    assert telink.data[CONF_DISCOVERY_MATCH] == DISCOVERY_MATCH_TELINK_MESH
    assert (
        telink.data[CONF_DISCOVERY_CONFIDENCE]
        == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
    )
    assert setup_entry_requires_discovery_confirmation(telink) is False


def test_old_uniled_near_miss_ble_names_do_not_create_entries() -> None:
    """Unsafe no-separator suffixes must not resolve from broad SP matchers."""
    audit = audit_legacy_uniled(Path("..") / "uniled")
    catalog = default_catalog()

    assert len(audit.legacy_ble_names) == 51
    for index, name in enumerate(audit.legacy_ble_names):
        try:
            bluetooth_setup_entry_data_from_discovery(
                catalog,
                SimpleNamespace(
                    name=f"{name}X",
                    address=f"AA:BB:CC:11:{index:02X}:00",
                    manufacturer_data={},
                    connectable=True,
                ),
            )
        except SetupDataError as ex:
            assert ex.field == CONF_MODEL
            assert ex.reason == "unknown_model"
        else:
            raise AssertionError(f"{name}X should not resolve as a safe suffix")


def test_old_uniled_command_surfaces_match_ported_parity_profiles() -> None:
    """Old UniLED non-stub command builders are covered by parity profiles."""
    audit = audit_legacy_uniled(Path("..") / "uniled")
    surfaces = {
        surface.source_module: surface
        for surface in audit.command_surfaces
    }

    sp601 = surfaces["custom_components/uniled/lib/ble/banlanx_601.py"]
    assert len(sp601.old_command_builders) == 14
    assert "scene_save" in sp601.old_command_builders
    assert sp601.stubbed_builders == ("scene_save",)
    assert sp601.missing_builders == ()

    sp60x = surfaces["custom_components/uniled/lib/ble/banlanx_60x.py"]
    assert "scene_save" in sp60x.old_command_builders
    assert sp60x.stubbed_builders == ("scene_save",)
    assert sp60x.missing_builders == ()

    sp6xx = surfaces["custom_components/uniled/lib/ble/banlanx_6xx.py"]
    assert len(sp6xx.old_command_builders) == 21
    assert "light_mode" in sp6xx.old_command_builders
    assert "effect" not in sp6xx.old_command_builders
    assert "onoff_config" in sp6xx.old_command_builders
    assert sp6xx.stubbed_builders == ()
    assert sp6xx.missing_builders == ()

    chord = surfaces["custom_components/uniled/lib/ble/led_chord.py"]
    assert "rgb2_color" in chord.old_command_builders
    assert chord.stubbed_builders == ()
    assert chord.missing_builders == ()

    hue = surfaces["custom_components/uniled/lib/ble/led_hue.py"]
    assert "effect_loop" in hue.old_command_builders
    assert hue.stubbed_builders == ()
    assert hue.missing_builders == ()

    assert all(
        not surface.missing_builders
        for surface in audit.command_surfaces
    )
