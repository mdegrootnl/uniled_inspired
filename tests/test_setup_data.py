"""Config-entry data helper tests."""

from __future__ import annotations

from types import SimpleNamespace

from custom_components.uniled.const import (
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
from custom_components.uniled.core import TransportKind, default_catalog
from custom_components.uniled.core.protocols import parse_zengge_cloud_meshes
from custom_components.uniled.setup_data import (
    SetupDataError,
    bluetooth_discovery_evidence,
    bluetooth_setup_entry_data,
    bluetooth_setup_entry_data_from_discovery,
    lan_setup_entry_data_from_discovery,
    lan_setup_entry_data_from_spnet_response,
    manual_setup_entry_data,
    manual_setup_model,
    migrate_legacy_entry_data,
    reconfigure_entry_data,
    setup_entry_compatibility_unique_ids,
    setup_entry_requires_discovery_confirmation,
    zengge_cloud_import_supported,
    zengge_cloud_setup_entry_data,
    zengge_cloud_update_entry_data,
)


def test_bluetooth_setup_entry_data_uses_exact_catalog_names() -> None:
    """Exact Bluetooth names keep the direct BLE setup path."""
    catalog = default_catalog()

    setup = bluetooth_setup_entry_data(
        catalog,
        name="SP601E",
        address="AA:BB:CC:DD:EE:FF",
    )

    assert setup.unique_id == "ble:aa:bb:cc:dd:ee:ff"
    assert setup.title == "SP601E"
    assert setup.data == {
        CONF_MODEL: "SP601E",
        CONF_MODEL_ID: 1,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        CONF_TRANSPORT: TRANSPORT_BLE,
        CONF_DISCOVERY_SOURCE: DISCOVERY_SOURCE_BLUETOOTH,
        CONF_DISCOVERY_MATCH: DISCOVERY_MATCH_EXACT_LABEL,
        CONF_DISCOVERY_CONFIDENCE: DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
    }


def test_bluetooth_setup_entry_data_resolves_suffixed_catalog_names() -> None:
    """Broad SP* discovery can resolve safe local-name suffixes."""
    catalog = default_catalog()

    setup = bluetooth_setup_entry_data(
        catalog,
        name="SP601E_AABB",
        address="AA:BB:CC:DD:EE:F0",
    )

    assert setup.unique_id == "ble:aa:bb:cc:dd:ee:f0"
    assert setup.title == "SP601E"
    assert setup.data == {
        CONF_MODEL: "SP601E",
        CONF_MODEL_ID: 1,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:F0",
        CONF_TRANSPORT: TRANSPORT_BLE,
        CONF_DISCOVERY_SOURCE: DISCOVERY_SOURCE_BLUETOOTH,
        CONF_DISCOVERY_MATCH: DISCOVERY_MATCH_SAFE_SUFFIX,
        CONF_DISCOVERY_CONFIDENCE: DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
    }


def test_bluetooth_setup_entry_data_resolves_friendly_labels() -> None:
    """Discovery can use APK friendly labels but stores canonical names."""
    catalog = default_catalog()

    setup = bluetooth_setup_entry_data(
        catalog,
        name="\u9c7c\u7f38\u706f",
        address="AA:BB:CC:DD:EE:F1",
    )

    assert setup.title == "\u9c7c\u7f38\u706f"
    assert setup.data == {
        CONF_MODEL: "FT001",
        CONF_MODEL_ID: 150,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:F1",
        CONF_TRANSPORT: TRANSPORT_BLE,
        CONF_DISCOVERY_SOURCE: DISCOVERY_SOURCE_BLUETOOTH,
        CONF_DISCOVERY_MATCH: DISCOVERY_MATCH_EXACT_LABEL,
        CONF_DISCOVERY_CONFIDENCE: DISCOVERY_CONFIDENCE_DISCOVERED_ONLY,
    }


def test_bluetooth_setup_entry_data_resolves_telink_mesh_as_rg4() -> None:
    """Generic Telink mesh advertisements create RG4 mesh entries."""
    catalog = default_catalog()

    setup = bluetooth_setup_entry_data(
        catalog,
        name="Zengge",
        address="AA:BB:CC:DD:EE:01",
        manufacturer_data={529: bytes.fromhex("11 02 00 00 00 00 00 23 00 44")},
    )

    assert setup.unique_id == "zng_mesh_0x211"
    assert setup.title == "RG4 mesh 0x211"
    assert setup.data == {
        CONF_MODEL: "RG4",
        CONF_MODEL_ID: 44034,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:01",
        CONF_DEVICE_ID: "zng_mesh_0x211",
        CONF_MESH_UUID: 0x0211,
        CONF_MESH_NODE_ID: 0x44,
        CONF_MESH_NODE_TYPE: 0x23,
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
        CONF_DISCOVERY_SOURCE: DISCOVERY_SOURCE_BLUETOOTH,
        CONF_DISCOVERY_MATCH: DISCOVERY_MATCH_TELINK_MESH,
        CONF_DISCOVERY_CONFIDENCE: DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
    }


def test_bluetooth_setup_entry_data_keeps_mesh_transport_for_exact_rg4() -> None:
    """Exact RG4 discovery still uses BLE mesh transport metadata."""
    catalog = default_catalog()

    setup = bluetooth_setup_entry_data(
        catalog,
        name="RG4",
        address="AA:BB:CC:DD:EE:02",
    )

    assert setup.unique_id == "ble_mesh:aa:bb:cc:dd:ee:02"
    assert setup.title == "RG4"
    assert setup.data == {
        CONF_MODEL: "RG4",
        CONF_MODEL_ID: 44034,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:02",
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
        CONF_DISCOVERY_SOURCE: DISCOVERY_SOURCE_BLUETOOTH,
        CONF_DISCOVERY_MATCH: DISCOVERY_MATCH_EXACT_LABEL,
        CONF_DISCOVERY_CONFIDENCE: DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
    }


def test_bluetooth_setup_entry_data_rejects_non_connectable_discovery() -> None:
    """Bluetooth discovery must be connectable because all local BLE paths write."""
    catalog = default_catalog()

    try:
        bluetooth_setup_entry_data(
            catalog,
            name="SP601E",
            address="AA:BB:CC:DD:EE:FF",
            connectable=False,
        )
    except SetupDataError as ex:
        assert ex.field == CONF_ADDRESS
        assert ex.reason == "not_connectable"
    else:
        raise AssertionError("non-connectable Bluetooth discovery should be rejected")


def test_bluetooth_setup_entry_data_rejects_lan_only_discovery() -> None:
    """Broad manifest matchers cannot create BLE entries for LAN-only models."""
    catalog = default_catalog()

    try:
        bluetooth_setup_entry_data(
            catalog,
            name="SP801E",
            address="AA:BB:CC:DD:EE:80",
            connectable=True,
        )
    except SetupDataError as ex:
        assert ex.field == CONF_TRANSPORT
        assert ex.reason == "unsupported_ble_transport"
    else:
        raise AssertionError("LAN-only Bluetooth discovery should be rejected")


def test_bluetooth_setup_entry_data_from_discovery_uses_ha_object_fields() -> None:
    """Discovery-object normalization mirrors Home Assistant Bluetooth fields."""
    catalog = default_catalog()

    setup = bluetooth_setup_entry_data_from_discovery(
        catalog,
        SimpleNamespace(
            name="",
            local_name="SP601E_AABB",
            address="AA:BB:CC:DD:EE:11",
            manufacturer_data={},
            connectable=True,
        ),
    )

    assert setup.unique_id == "ble:aa:bb:cc:dd:ee:11"
    assert setup.data[CONF_MODEL] == "SP601E"
    assert setup.data[CONF_DISCOVERY_MATCH] == DISCOVERY_MATCH_SAFE_SUFFIX
    assert (
        setup.data[CONF_DISCOVERY_CONFIDENCE]
        == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
    )


def test_bluetooth_setup_entry_data_from_discovery_accepts_mapping_shape() -> None:
    """The HA-independent helper also handles dict-like discovery fixtures."""
    catalog = default_catalog()

    setup = bluetooth_setup_entry_data_from_discovery(
        catalog,
        {
            "name": "Zengge",
            "address": "AA:BB:CC:DD:EE:12",
            "manufacturer_data": {
                529: bytes.fromhex("11 02 00 00 00 00 00 23 00 44")
            },
            "connectable": True,
        },
    )

    assert setup.unique_id == "zng_mesh_0x211"
    assert setup.data[CONF_MODEL] == "RG4"
    assert setup.data[CONF_DISCOVERY_MATCH] == DISCOVERY_MATCH_TELINK_MESH
    assert (
        setup.data[CONF_DISCOVERY_CONFIDENCE]
        == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
    )


def test_bluetooth_discovery_evidence_records_match_confidence() -> None:
    """Discovery stores whether a match is protocol-backed or catalog-only."""
    catalog = default_catalog()

    proven = bluetooth_discovery_evidence(catalog, name="SP601E")
    catalog_only = bluetooth_discovery_evidence(catalog, name="\u9c7c\u7f38\u706f")
    suffixed = bluetooth_discovery_evidence(catalog, name="SP601E_AABB")
    zengge_mesh = bluetooth_discovery_evidence(catalog, name="RG4")
    scene_mesh = bluetooth_discovery_evidence(catalog, name="SP310E")

    assert proven is not None
    assert proven.model.name == "SP601E"
    assert proven.match == DISCOVERY_MATCH_EXACT_LABEL
    assert proven.confidence == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN

    assert catalog_only is not None
    assert catalog_only.model.name == "FT001"
    assert catalog_only.match == DISCOVERY_MATCH_EXACT_LABEL
    assert catalog_only.confidence == DISCOVERY_CONFIDENCE_DISCOVERED_ONLY

    assert suffixed is not None
    assert suffixed.model.name == "SP601E"
    assert suffixed.match == DISCOVERY_MATCH_SAFE_SUFFIX
    assert suffixed.confidence == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN

    assert zengge_mesh is not None
    assert zengge_mesh.model.name == "RG4"
    assert zengge_mesh.match == DISCOVERY_MATCH_EXACT_LABEL
    assert zengge_mesh.confidence == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN

    assert scene_mesh is not None
    assert scene_mesh.model.name == "SP310E"
    assert scene_mesh.match == DISCOVERY_MATCH_EXACT_LABEL
    assert scene_mesh.confidence == DISCOVERY_CONFIDENCE_DISCOVERED_ONLY


def test_discovery_confirmation_policy_only_pauses_catalog_only_matches() -> None:
    """Protocol-backed discovery can auto-create; catalog-only matches need consent."""
    catalog = default_catalog()

    old_uniled = bluetooth_setup_entry_data(
        catalog,
        name="SP601E",
        address="AA:BB:CC:DD:EE:31",
    )
    catalog_only = bluetooth_setup_entry_data(
        catalog,
        name="SP310E",
        address="AA:BB:CC:DD:EE:32",
    )
    verified_lan = lan_setup_entry_data_from_spnet_response(
        catalog,
        bytes.fromhex(
            "53704e65740000210000000000010000105c00542024111f77075350353431450000"
        ),
        source="192.0.2.92",
    )

    assert setup_entry_requires_discovery_confirmation(old_uniled) is False
    assert setup_entry_requires_discovery_confirmation(catalog_only) is True
    assert setup_entry_requires_discovery_confirmation(verified_lan) is False


def test_bluetooth_autodiscovery_covers_old_uniled_apk_overlap() -> None:
    """Every old-UniLED/BanlanX APK overlap model resolves from BLE discovery."""
    catalog = default_catalog()
    legacy_models = tuple(
        model
        for model in catalog.user_facing_models()
        if model.legacy_uniled_supported
        and not model.home_uri.startswith("/legacy/uniled/")
    )

    assert len(legacy_models) == 49
    for index, model in enumerate(legacy_models):
        address = f"AA:BB:CC:DD:EE:{index:02X}"
        setup = bluetooth_setup_entry_data(
            catalog,
            name=f"{model.name}-AABB",
            address=address,
            connectable=True,
        )

        assert setup.unique_id == f"ble:{address.casefold()}"
        assert setup.data[CONF_MODEL] == model.name
        assert setup.data[CONF_MODEL_ID] == model.model_id
        assert setup.data[CONF_TRANSPORT] == TRANSPORT_BLE
        assert setup.data[CONF_ADDRESS] == address
        assert setup.data[CONF_DISCOVERY_SOURCE] == DISCOVERY_SOURCE_BLUETOOTH
        assert setup.data[CONF_DISCOVERY_MATCH] == DISCOVERY_MATCH_SAFE_SUFFIX
        assert (
            setup.data[CONF_DISCOVERY_CONFIDENCE]
            == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
        )


def test_bluetooth_autodiscovery_covers_legacy_only_old_uniled_models() -> None:
    """Old LED Chord/Hue models resolve as guarded legacy-only BLE entries."""
    catalog = default_catalog()

    for index, name in enumerate(("SP107E", "SP110E")):
        address = f"AA:BB:CC:DD:EF:{index:02X}"
        setup = bluetooth_setup_entry_data(
            catalog,
            name=name,
            address=address,
            connectable=True,
        )

        assert setup.unique_id == f"ble:{address.casefold()}"
        assert setup.data[CONF_MODEL] == name
        assert setup.data[CONF_ADDRESS] == address
        assert setup.data[CONF_TRANSPORT] == TRANSPORT_BLE
        assert setup.data[CONF_DISCOVERY_SOURCE] == DISCOVERY_SOURCE_BLUETOOTH
        assert setup.data[CONF_DISCOVERY_MATCH] == DISCOVERY_MATCH_EXACT_LABEL
        assert (
            setup.data[CONF_DISCOVERY_CONFIDENCE]
            == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
        )


def test_setup_data_reports_legacy_compatible_unique_ids() -> None:
    """New setup data can detect existing legacy config-entry identities."""
    catalog = default_catalog()

    ble = bluetooth_setup_entry_data(
        catalog,
        name="SP601E",
        address="AA:BB:CC:DD:EE:21",
    )
    ble_lower = bluetooth_setup_entry_data(
        catalog,
        name="SP601E",
        address="aa:bb:cc:dd:ee:22",
    )
    lan = lan_setup_entry_data_from_spnet_response(
        catalog,
        bytes.fromhex(
            "53704e65740000210000000000010000105c00542024111f77075350353431450000"
        ),
        source="192.0.2.92",
    )
    host_only_lan = manual_setup_entry_data(
        catalog.resolve_name("SP802E"),
        transport=TRANSPORT_LAN,
        host="192.0.2.55",
    )

    assert setup_entry_compatibility_unique_ids(ble) == (
        "AA:BB:CC:DD:EE:21",
        "aa:bb:cc:dd:ee:21",
    )
    assert setup_entry_compatibility_unique_ids(ble_lower) == (
        "aa:bb:cc:dd:ee:22",
    )
    assert setup_entry_compatibility_unique_ids(lan) == (
        "54:20:24:11:1F:77",
        "54:20:24:11:1f:77",
    )
    assert setup_entry_compatibility_unique_ids(host_only_lan) == ()


def test_bluetooth_setup_entry_data_requires_address() -> None:
    """Bluetooth-discovered direct BLE and mesh entries need an address."""
    catalog = default_catalog()

    cases = (
        {"name": "SP601E"},
        {"name": "RG4"},
        {
            "name": "Zengge",
            "manufacturer_data": {
                529: bytes.fromhex("11 02 00 00 00 00 00 23 00 44")
            },
        },
    )
    for kwargs in cases:
        try:
            bluetooth_setup_entry_data(catalog, **kwargs)
        except SetupDataError as ex:
            assert ex.field == CONF_ADDRESS
            assert ex.reason == "required"
        else:
            raise AssertionError(f"{kwargs!r} should require a Bluetooth address")


def test_zengge_cloud_setup_entry_data_preserves_old_uniled_mesh_identity() -> None:
    """Parsed MagicHue cloud metadata becomes RG4 mesh config-entry data."""
    catalog = default_catalog()
    model = catalog.resolve_name("RG4")
    assert model is not None
    mesh = parse_zengge_cloud_meshes(
        {
            "placeUniID": "place-1",
            "displayName": "Kitchen",
            "meshKey": "CloudMesh",
            "meshPassword": "CloudPassword",
            "meshLTK": "CloudToken",
            "deviceList": [
                {
                    "meshUUID": 0x0211,
                    "meshAddress": 0x44,
                    "deviceType": 2,
                    "wiringType": 4,
                    "displayName": "Counter Strip",
                }
            ],
        }
    )[0]

    setup = zengge_cloud_setup_entry_data(
        model,
        mesh,
        address="AA:BB:CC:DD:EE:03",
    )

    assert setup.unique_id == "zng_mesh_0x211"
    assert setup.title == "Kitchen"
    assert setup.data == {
        CONF_MODEL: "RG4",
        CONF_MODEL_ID: 44034,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:03",
        CONF_DEVICE_ID: "zng_mesh_0x211",
        CONF_MESH_UUID: 0x0211,
        CONF_MESH_PLACE_ID: "place-1",
        CONF_MESH_PLACE_NAME: "Kitchen",
        CONF_MESH_KEY: "CloudMesh",
        CONF_MESH_PASSWORD: "CloudPassword",
        CONF_MESH_LTK: "CloudToken",
        CONF_MESH_NODES: [
            {
                CONF_MESH_NODE_ID: 0x44,
                CONF_MESH_NODE_TYPE: 2,
                CONF_MESH_NODE_WIRING: 4,
                "name": "Counter Strip",
                "area": "Kitchen",
            }
        ],
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }


def test_zengge_cloud_setup_is_only_for_zengge_mesh_family() -> None:
    """BanlanX scene-mesh models must not enter MagicHue/Zengge cloud import."""
    catalog = default_catalog()
    rg4 = catalog.resolve_name("RG4")
    scene_mesh = catalog.resolve_name("SP310E")
    assert rg4 is not None
    assert scene_mesh is not None

    mesh = parse_zengge_cloud_meshes(
        {
            "placeUniID": "place-1",
            "displayName": "Kitchen",
            "meshUUID": 0x0211,
            "deviceList": [{"meshUUID": 0x0211, "meshAddress": 0x44}],
        }
    )[0]

    assert zengge_cloud_import_supported(rg4) is True
    assert zengge_cloud_import_supported(scene_mesh) is False

    try:
        zengge_cloud_setup_entry_data(scene_mesh, mesh)
    except SetupDataError as ex:
        assert ex.field == CONF_TRANSPORT
        assert ex.reason == "unsupported_mesh_transport"
    else:
        raise AssertionError("BanlanX scene mesh must not use Zengge cloud setup")


def test_zengge_cloud_update_entry_data_replaces_stale_mesh_metadata() -> None:
    """Options-flow cloud refresh keeps identity but replaces cloud-owned facts."""
    mesh = parse_zengge_cloud_meshes(
        {
            "placeUniID": "place-2",
            "displayName": "Office",
            "meshKey": "NewMesh",
            "meshPassword": "NewPassword",
            "meshLTK": "NewToken",
            "deviceList": [
                {
                    "meshUUID": 0x0211,
                    "meshAddress": 0x45,
                    "deviceType": 2,
                    "wiringType": 3,
                    "displayName": "Desk Strip",
                }
            ],
        }
    )[0]

    updated = zengge_cloud_update_entry_data(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:04",
            CONF_DEVICE_ID: "existing-device-id",
            CONF_MESH_UUID: 0x0211,
            CONF_MESH_PLACE_ID: "old-place",
            CONF_MESH_NODES: [
                {
                    CONF_MESH_NODE_ID: 0x44,
                    CONF_MESH_NODE_TYPE: 1,
                    CONF_MESH_NODE_WIRING: 1,
                    "name": "Stale",
                    "area": "Old",
                }
            ],
            CONF_TRANSPORT: TRANSPORT_BLE_MESH,
            "custom": "keep",
        },
        mesh,
    )

    assert updated[CONF_MODEL] == "RG4"
    assert updated[CONF_ADDRESS] == "AA:BB:CC:DD:EE:04"
    assert updated[CONF_DEVICE_ID] == "existing-device-id"
    assert updated["custom"] == "keep"
    assert updated[CONF_MESH_UUID] == 0x0211
    assert updated[CONF_MESH_PLACE_ID] == "place-2"
    assert updated[CONF_MESH_PLACE_NAME] == "Office"
    assert updated[CONF_MESH_KEY] == "NewMesh"
    assert updated[CONF_MESH_PASSWORD] == "NewPassword"
    assert updated[CONF_MESH_LTK] == "NewToken"
    assert updated[CONF_MESH_NODES] == [
        {
            CONF_MESH_NODE_ID: 0x45,
            CONF_MESH_NODE_TYPE: 2,
            CONF_MESH_NODE_WIRING: 3,
            "name": "Desk Strip",
            "area": "Office",
        }
    ]
    assert updated[CONF_TRANSPORT] == TRANSPORT_BLE_MESH


def test_zengge_cloud_update_rejects_banlanx_scene_mesh_entries() -> None:
    """Options refresh must not mix MagicHue cloud metadata into scene mesh."""
    mesh = parse_zengge_cloud_meshes(
        {
            "placeUniID": "place-1",
            "displayName": "Kitchen",
            "meshUUID": 0x0211,
            "deviceList": [{"meshUUID": 0x0211, "meshAddress": 0x44}],
        }
    )[0]

    try:
        zengge_cloud_update_entry_data(
            {
                CONF_MODEL: "SP310E",
                CONF_MODEL_ID: 176,
                CONF_TRANSPORT: TRANSPORT_BLE_MESH,
                CONF_MESH_UUID: 0x0211,
            },
            mesh,
        )
    except SetupDataError as ex:
        assert ex.field == CONF_TRANSPORT
        assert ex.reason == "unsupported_mesh_transport"
    else:
        raise AssertionError("scene mesh entries should reject Zengge cloud refresh")


def test_zengge_cloud_update_entry_data_adds_missing_device_id() -> None:
    """Old diagnostic mesh entries can gain the stable old-UniLED mesh ID."""
    mesh = parse_zengge_cloud_meshes(
        {
            "meshUUID": 0x0211,
            "deviceList": [
                {
                    "meshUUID": 0x0211,
                    "meshAddress": 0x45,
                }
            ],
        }
    )[0]

    updated = zengge_cloud_update_entry_data(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:05",
        },
        mesh,
    )

    assert updated[CONF_DEVICE_ID] == "zng_mesh_0x211"
    assert updated[CONF_TRANSPORT] == TRANSPORT_BLE_MESH


def test_zengge_cloud_update_entry_data_requires_existing_model() -> None:
    """Cloud refresh cannot safely update an unmodeled config entry."""
    mesh = parse_zengge_cloud_meshes(
        {
            "meshUUID": 0x0211,
            "deviceList": [
                {
                    "meshUUID": 0x0211,
                    "meshAddress": 0x45,
                }
            ],
        }
    )[0]

    try:
        zengge_cloud_update_entry_data({}, mesh)
    except SetupDataError as ex:
        assert ex.field == CONF_MODEL
        assert ex.reason == "required"
    else:
        raise AssertionError("cloud refresh should require an existing model")


def test_migrate_legacy_ble_entry_data_normalizes_transport() -> None:
    """Legacy BLE entries keep model/address and gain the new transport shape."""
    catalog = default_catalog()

    migrated = migrate_legacy_entry_data(
        catalog,
        {
            CONF_TRANSPORT: "ble",
            CONF_MODEL: "SP601E",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:10",
            CONF_DEVICE_ID: "old-id",
        },
    )

    assert migrated == {
        CONF_MODEL: "SP601E",
        CONF_MODEL_ID: 1,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:10",
        CONF_DEVICE_ID: "old-id",
        CONF_TRANSPORT: TRANSPORT_BLE,
    }


def test_migrate_legacy_network_entry_data_maps_to_lan() -> None:
    """Legacy net entries become manual-host LAN entries."""
    catalog = default_catalog()

    migrated = migrate_legacy_entry_data(
        catalog,
        {
            CONF_TRANSPORT: "net",
            CONF_MODEL: "SP802E",
            CONF_ADDRESS: "192.168.1.77",
        },
    )

    assert migrated == {
        CONF_MODEL: "SP802E",
        CONF_MODEL_ID: 158,
        CONF_DEVICE_ID: "192.168.1.77",
        CONF_HOST: "192.168.1.77",
        CONF_TRANSPORT: TRANSPORT_LAN,
    }


def test_migrate_legacy_zengge_entry_data_preserves_mesh_identity() -> None:
    """Legacy Zengge entries preserve old mesh IDs without cloud credentials."""
    catalog = default_catalog()

    migrated = migrate_legacy_entry_data(
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

    assert migrated == {
        CONF_MODEL: "RG4",
        CONF_MODEL_ID: 44034,
        CONF_DEVICE_ID: "zng_mesh_0x211",
        CONF_MESH_UUID: 0x0211,
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }


def test_migrate_current_rg4_discovery_entry_allows_missing_mesh_uuid() -> None:
    """Current exact-name RG4 entries can still migrate before mesh metadata."""
    catalog = default_catalog()

    migrated = migrate_legacy_entry_data(
        catalog,
        {
            CONF_TRANSPORT: TRANSPORT_BLE_MESH,
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:11",
        },
    )

    assert migrated == {
        CONF_MODEL: "RG4",
        CONF_MODEL_ID: 44034,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:11",
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }


def test_migrate_scene_mesh_entry_derives_address_identity() -> None:
    """Scene-mesh migrations keep local BLE-mesh identity separate from Zengge."""
    catalog = default_catalog()

    migrated = migrate_legacy_entry_data(
        catalog,
        {
            CONF_TRANSPORT: TRANSPORT_BLE_MESH,
            CONF_MODEL: "SP310E",
            CONF_MODEL_ID: 176,
            CONF_ADDRESS: "AA:BB:CC:DD:EE:12",
            CONF_MESH_UUID: "0x211",
        },
    )

    assert migrated == {
        CONF_MODEL: "SP310E",
        CONF_MODEL_ID: 176,
        CONF_DEVICE_ID: "ble_mesh:aa:bb:cc:dd:ee:12",
        CONF_MESH_UUID: 0x0211,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:12",
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }


def test_migrate_entry_data_preserves_duplicate_model_id_variant() -> None:
    """Duplicate-name entries keep their stored APK variant identity."""
    catalog = default_catalog()

    migrated = migrate_legacy_entry_data(
        catalog,
        {
            CONF_TRANSPORT: TRANSPORT_MANUAL,
            CONF_MODEL: "SP665E",
            CONF_MODEL_ID: 260,
            CONF_DEVICE_ID: "scene",
        },
    )

    assert migrated == {
        CONF_MODEL: "SP665E",
        CONF_MODEL_ID: 260,
        CONF_DEVICE_ID: "scene",
        CONF_TRANSPORT: TRANSPORT_MANUAL,
    }


def test_migrate_legacy_entry_data_rejects_unsafe_shapes() -> None:
    """Migration fails visibly when required legacy facts are missing."""
    catalog = default_catalog()

    cases = (
        ({CONF_TRANSPORT: "ble", CONF_MODEL: "SP601E"}, CONF_ADDRESS, "required"),
        (
            {CONF_TRANSPORT: "net", CONF_MODEL: "SP630E", CONF_ADDRESS: "host"},
            CONF_TRANSPORT,
            "unsupported_lan_transport",
        ),
        (
            {CONF_TRANSPORT: "zng", CONF_MESH_UUID: "bad"},
            CONF_MESH_UUID,
            "invalid_mesh_uuid",
        ),
        (
            {
                CONF_TRANSPORT: "ble",
                CONF_MODEL: "SP601E",
                CONF_MODEL_ID: "bad",
                CONF_ADDRESS: "AA:BB:CC:DD:EE:12",
            },
            CONF_MODEL_ID,
            "invalid_model_id",
        ),
        (
            {
                CONF_TRANSPORT: "ble",
                CONF_MODEL: "SP601E",
                CONF_MODEL_ID: 260,
                CONF_ADDRESS: "AA:BB:CC:DD:EE:12",
            },
            CONF_MODEL_ID,
            "unknown_model_id",
        ),
        ({CONF_TRANSPORT: "manual", CONF_MODEL: "Nope"}, CONF_MODEL, "unknown_model"),
    )
    for entry_data, field, reason in cases:
        try:
            migrate_legacy_entry_data(catalog, entry_data)
        except SetupDataError as ex:
            assert ex.field == field
            assert ex.reason == reason
        else:
            raise AssertionError(f"{entry_data!r} should not migrate")


def test_reconfigure_ble_entry_data_updates_address() -> None:
    """BLE reconfigure can repair a stale stored Bluetooth address."""
    catalog = default_catalog()

    updated = reconfigure_entry_data(
        catalog,
        {
            CONF_TRANSPORT: TRANSPORT_BLE,
            CONF_MODEL: "SP601E",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:20",
            CONF_DEVICE_ID: "old-id",
        },
        address="AA:BB:CC:DD:EE:21",
    )

    assert updated == {
        CONF_MODEL: "SP601E",
        CONF_MODEL_ID: 1,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:21",
        CONF_DEVICE_ID: "old-id",
        CONF_TRANSPORT: TRANSPORT_BLE,
    }


def test_reconfigure_lan_entry_data_updates_default_device_id() -> None:
    """LAN host changes keep custom IDs but update host-derived IDs."""
    catalog = default_catalog()

    updated = reconfigure_entry_data(
        catalog,
        {
            CONF_TRANSPORT: TRANSPORT_LAN,
            CONF_MODEL: "SP802E",
            CONF_HOST: "192.168.1.70",
            CONF_DEVICE_ID: "192.168.1.70",
        },
        host="192.168.1.71",
    )
    custom = reconfigure_entry_data(
        catalog,
        {
            CONF_TRANSPORT: TRANSPORT_LAN,
            CONF_MODEL: "SP802E",
            CONF_HOST: "192.168.1.70",
            CONF_DEVICE_ID: "Kitchen pixels",
        },
        host="192.168.1.72",
    )

    assert updated == {
        CONF_MODEL: "SP802E",
        CONF_MODEL_ID: 158,
        CONF_DEVICE_ID: "192.168.1.71",
        CONF_HOST: "192.168.1.71",
        CONF_TRANSPORT: TRANSPORT_LAN,
    }
    assert custom[CONF_DEVICE_ID] == "Kitchen pixels"
    assert custom[CONF_HOST] == "192.168.1.72"


def test_reconfigure_legacy_network_entry_data_accepts_new_host() -> None:
    """Reconfigure can normalize an old net entry while repairing the host."""
    catalog = default_catalog()

    updated = reconfigure_entry_data(
        catalog,
        {
            CONF_TRANSPORT: "net",
            CONF_MODEL: "SP802E",
            CONF_ADDRESS: "192.168.1.73",
        },
        host="led-office.local",
    )

    assert updated == {
        CONF_MODEL: "SP802E",
        CONF_MODEL_ID: 158,
        CONF_DEVICE_ID: "led-office.local",
        CONF_HOST: "led-office.local",
        CONF_TRANSPORT: TRANSPORT_LAN,
    }


def test_reconfigure_mesh_entry_data_preserves_credentials() -> None:
    """Mesh reconfigure updates local facts without dropping cloud metadata."""
    catalog = default_catalog()

    updated = reconfigure_entry_data(
        catalog,
        {
            CONF_TRANSPORT: TRANSPORT_BLE_MESH,
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:30",
            CONF_DEVICE_ID: "zng_mesh_0x211",
            CONF_MESH_UUID: 0x0211,
            CONF_MESH_KEY: "CloudMesh",
            CONF_MESH_PASSWORD: "CloudPassword",
            CONF_MESH_LTK: "CloudToken",
            CONF_MESH_NODES: [
                {
                    CONF_MESH_NODE_ID: 0x44,
                    CONF_MESH_NODE_TYPE: 1,
                    CONF_MESH_NODE_WIRING: 2,
                    "name": "Counter",
                }
            ],
        },
        address="AA:BB:CC:DD:EE:31",
        mesh_node_id="0x44",
        mesh_node_type="0x02",
        mesh_node_wiring="4",
    )

    assert updated[CONF_ADDRESS] == "AA:BB:CC:DD:EE:31"
    assert updated[CONF_MESH_UUID] == 0x0211
    assert updated[CONF_MESH_KEY] == "CloudMesh"
    assert updated[CONF_MESH_PASSWORD] == "CloudPassword"
    assert updated[CONF_MESH_LTK] == "CloudToken"
    assert updated[CONF_MESH_NODES] == [
        {
            CONF_MESH_NODE_ID: 0x44,
            CONF_MESH_NODE_TYPE: 1,
            CONF_MESH_NODE_WIRING: 2,
            "name": "Counter",
        }
    ]
    assert updated[CONF_MESH_NODE_ID] == 0x44
    assert updated[CONF_MESH_NODE_TYPE] == 2
    assert updated[CONF_MESH_NODE_WIRING] == 4


def test_reconfigure_entry_data_rejects_unsafe_updates() -> None:
    """Reconfigure fails visibly for invalid or cross-identity updates."""
    catalog = default_catalog()

    cases = (
        (
            {
                CONF_TRANSPORT: TRANSPORT_BLE,
                CONF_MODEL: "SP601E",
                CONF_ADDRESS: "AA:BB",
            },
            {CONF_ADDRESS: "AA BB"},
            CONF_ADDRESS,
            "invalid_address",
        ),
        (
            {
                CONF_TRANSPORT: TRANSPORT_LAN,
                CONF_MODEL: "SP802E",
                CONF_HOST: "192.168.1.74",
            },
            {CONF_HOST: "http://device.local"},
            CONF_HOST,
            "invalid_host",
        ),
        (
            {
                CONF_TRANSPORT: TRANSPORT_BLE_MESH,
                CONF_MODEL: "RG4",
                CONF_MESH_UUID: 0x0211,
            },
            {CONF_MESH_UUID: "0x212"},
            CONF_MESH_UUID,
            "mesh_identity_mismatch",
        ),
        (
            {
                CONF_TRANSPORT: TRANSPORT_BLE_MESH,
                CONF_MODEL: "RG4",
                CONF_MESH_UUID: 0x0211,
            },
            {CONF_MESH_NODE_ID: "bad"},
            CONF_MESH_NODE_ID,
            "invalid_mesh_node_id",
        ),
    )
    for entry_data, updates, field, reason in cases:
        try:
            reconfigure_entry_data(catalog, entry_data, **updates)
        except SetupDataError as ex:
            assert ex.field == field
            assert ex.reason == reason
        else:
            raise AssertionError(f"{updates!r} should not reconfigure")


def test_bluetooth_setup_entry_data_rejects_unknown_discovery() -> None:
    """Unknown Bluetooth names without mesh evidence are rejected."""
    catalog = default_catalog()

    for name in ("Unknown", "SP601EX"):
        try:
            bluetooth_setup_entry_data(catalog, name=name)
        except SetupDataError as ex:
            assert ex.field == CONF_MODEL
            assert ex.reason == "unknown_model"
        else:
            raise AssertionError(f"{name!r} Bluetooth discovery should abort")


def test_manual_setup_model_resolves_duplicate_variant_id() -> None:
    """Manual setup can target an exact APK row behind a duplicate name."""
    catalog = default_catalog()

    default_model = manual_setup_model(catalog, name="SP665E")
    variant = manual_setup_model(catalog, name="SP665E", model_id="0x104")
    setup = manual_setup_entry_data(
        variant,
        transport=TRANSPORT_MANUAL,
        device_id="Scene Controller",
    )

    assert default_model.model_id == 126
    assert variant.model_id == 260
    assert variant.parent_id == 126
    assert setup.data == {
        CONF_MODEL: "SP665E",
        CONF_MODEL_ID: 260,
        CONF_DEVICE_ID: "Scene Controller",
        CONF_TRANSPORT: TRANSPORT_MANUAL,
    }


def test_manual_setup_model_accepts_friendly_label() -> None:
    """Manual/migrated inputs can resolve labels and store canonical names."""
    catalog = default_catalog()

    model = manual_setup_model(catalog, name="\u9c7c\u7f38\u706f")
    setup = manual_setup_entry_data(
        model,
        transport=TRANSPORT_MANUAL,
        device_id="tank",
    )

    assert model.name == "FT001"
    assert setup.data == {
        CONF_MODEL: "FT001",
        CONF_MODEL_ID: 150,
        CONF_DEVICE_ID: "tank",
        CONF_TRANSPORT: TRANSPORT_MANUAL,
    }


def test_manual_setup_model_rejects_unknown_variant_id() -> None:
    """Manual setup errors point at model_id when the name exists but ID differs."""
    catalog = default_catalog()

    cases = (
        ("SP665E", "bad", CONF_MODEL_ID, "invalid_model_id"),
        ("SP665E", 99, CONF_MODEL_ID, "unknown_model_id"),
        ("Nope", 260, CONF_MODEL, "unknown_model"),
    )
    for name, model_id, field, reason in cases:
        try:
            manual_setup_model(catalog, name=name, model_id=model_id)
        except SetupDataError as ex:
            assert ex.field == field
            assert ex.reason == reason
        else:
            raise AssertionError(f"{name!r}/{model_id!r} should not resolve")


def test_manual_setup_entry_data_keeps_existing_diagnostic_path() -> None:
    """Manual setup keeps the current stable identifier behavior."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP601E")
    assert model is not None

    setup = manual_setup_entry_data(
        model,
        transport=TRANSPORT_MANUAL,
        device_id="Bench Controller",
    )

    assert setup.unique_id == "manual:SP601E:bench controller"
    assert setup.title == "SP601E Bench Controller"
    assert setup.data == {
        CONF_MODEL: "SP601E",
        CONF_MODEL_ID: 1,
        CONF_DEVICE_ID: "Bench Controller",
        CONF_TRANSPORT: TRANSPORT_MANUAL,
    }


def test_manual_ble_setup_entry_data_uses_address_identity() -> None:
    """Manual BLE setup can create a stable entry when discovery misses."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP601E")
    assert model is not None

    setup = manual_setup_entry_data(
        model,
        transport=TRANSPORT_BLE,
        address="AA:BB:CC:DD:EE:07",
    )

    assert setup.unique_id == "ble:aa:bb:cc:dd:ee:07"
    assert setup.title == "SP601E AA:BB:CC:DD:EE:07"
    assert setup.data == {
        CONF_MODEL: "SP601E",
        CONF_MODEL_ID: 1,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:07",
        CONF_TRANSPORT: TRANSPORT_BLE,
    }


def test_manual_ble_setup_entry_data_rejects_non_ble_models() -> None:
    """Manual BLE setup follows catalog transport support."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP801E")
    assert model is not None

    try:
        manual_setup_entry_data(
            model,
            transport=TRANSPORT_BLE,
            address="AA:BB:CC:DD:EE:08",
        )
    except SetupDataError as ex:
        assert ex.field == CONF_TRANSPORT
        assert ex.reason == "unsupported_ble_transport"
    else:
        raise AssertionError("LAN-only models should not allow BLE setup")


def test_manual_ble_mesh_setup_entry_data_uses_old_uniled_mesh_identity() -> None:
    """Manual RG4 setup can create a command-ready local mesh entry."""
    catalog = default_catalog()
    model = catalog.resolve_name("RG4")
    assert model is not None

    setup = manual_setup_entry_data(
        model,
        transport=TRANSPORT_BLE_MESH,
        address="AA:BB:CC:DD:EE:06",
        mesh_uuid="0x211",
        mesh_node_id="0x44",
        mesh_node_type="0x02",
        mesh_node_wiring="4",
    )

    assert setup.unique_id == "zng_mesh_0x211"
    assert setup.title == "RG4 mesh 0x211"
    assert setup.data == {
        CONF_MODEL: "RG4",
        CONF_MODEL_ID: 44034,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:06",
        CONF_DEVICE_ID: "zng_mesh_0x211",
        CONF_MESH_UUID: 0x0211,
        CONF_MESH_NODE_ID: 0x44,
        CONF_MESH_NODE_TYPE: 2,
        CONF_MESH_NODE_WIRING: 4,
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }


def test_manual_ble_mesh_setup_entry_data_uses_scene_mesh_address_identity() -> None:
    """Manual BanlanX scene-mesh setup must not look like old Zengge mesh."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP310E")
    assert model is not None

    setup = manual_setup_entry_data(
        model,
        transport=TRANSPORT_BLE_MESH,
        address="AA:BB:CC:DD:EE:0B",
        mesh_uuid="0x211",
    )

    assert setup.unique_id == "ble_mesh:aa:bb:cc:dd:ee:0b"
    assert setup.title == "SP310E mesh 0x211"
    assert setup.data == {
        CONF_MODEL: "SP310E",
        CONF_MODEL_ID: 176,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:0B",
        CONF_DEVICE_ID: "ble_mesh:aa:bb:cc:dd:ee:0b",
        CONF_MESH_UUID: 0x0211,
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }


def test_manual_ble_mesh_setup_entry_data_allows_cloud_only_nodes() -> None:
    """Manual RG4 setup can defer node details to MagicHue cloud import."""
    catalog = default_catalog()
    model = catalog.resolve_name("RG4")
    assert model is not None

    setup = manual_setup_entry_data(
        model,
        transport=TRANSPORT_BLE_MESH,
        address="AA:BB:CC:DD:EE:07",
        mesh_uuid=0x0211,
    )

    assert setup.unique_id == "zng_mesh_0x211"
    assert setup.data == {
        CONF_MODEL: "RG4",
        CONF_MODEL_ID: 44034,
        CONF_ADDRESS: "AA:BB:CC:DD:EE:07",
        CONF_DEVICE_ID: "zng_mesh_0x211",
        CONF_MESH_UUID: 0x0211,
        CONF_TRANSPORT: TRANSPORT_BLE_MESH,
    }


def test_manual_ble_mesh_setup_entry_data_rejects_invalid_identity() -> None:
    """Manual mesh setup requires a reachable address and mesh UUID."""
    catalog = default_catalog()
    model = catalog.resolve_name("RG4")
    assert model is not None

    cases = (
        ({CONF_ADDRESS: "", CONF_MESH_UUID: "0x211"}, CONF_ADDRESS, "required"),
        (
            {CONF_ADDRESS: "AA:BB CC", CONF_MESH_UUID: "0x211"},
            CONF_ADDRESS,
            "invalid_address",
        ),
        ({CONF_ADDRESS: "AA:BB", CONF_MESH_UUID: ""}, CONF_MESH_UUID, "required"),
        (
            {CONF_ADDRESS: "AA:BB", CONF_MESH_UUID: "nope"},
            CONF_MESH_UUID,
            "invalid_mesh_uuid",
        ),
        (
            {CONF_ADDRESS: "AA:BB", CONF_MESH_UUID: "0"},
            CONF_MESH_UUID,
            "invalid_mesh_uuid",
        ),
        (
            {
                CONF_ADDRESS: "AA:BB",
                CONF_MESH_UUID: "0x211",
                CONF_MESH_NODE_ID: "nope",
            },
            CONF_MESH_NODE_ID,
            "invalid_mesh_node_id",
        ),
    )
    for data, field, reason in cases:
        try:
            manual_setup_entry_data(
                model,
                transport=TRANSPORT_BLE_MESH,
                address=str(data.get(CONF_ADDRESS, "")),
                mesh_uuid=data.get(CONF_MESH_UUID),
                mesh_node_id=data.get(CONF_MESH_NODE_ID),
            )
        except SetupDataError as ex:
            assert ex.field == field
            assert ex.reason == reason
        else:
            raise AssertionError(f"{data!r} should not be accepted")


def test_manual_ble_mesh_setup_rejects_models_without_mesh_capability() -> None:
    """Only mesh-capable models can use manual BLE mesh setup."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP601E")
    assert model is not None

    try:
        manual_setup_entry_data(
            model,
            transport=TRANSPORT_BLE_MESH,
            address="AA:BB:CC:DD:EE:08",
            mesh_uuid="0x211",
        )
    except SetupDataError as ex:
        assert ex.field == CONF_TRANSPORT
        assert ex.reason == "unsupported_mesh_transport"
    else:
        raise AssertionError("non-mesh models should reject BLE mesh setup")


def test_lan_setup_entry_data_uses_host_as_stable_identifier() -> None:
    """LAN-capable models can be configured by manual host/IP."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP802E")
    assert model is not None

    setup = manual_setup_entry_data(
        model,
        transport=TRANSPORT_LAN,
        host="192.168.1.50",
    )

    assert setup.unique_id == "lan:192.168.1.50"
    assert setup.title == "SP802E 192.168.1.50"
    assert setup.data == {
        CONF_MODEL: "SP802E",
        CONF_MODEL_ID: 158,
        CONF_DEVICE_ID: "192.168.1.50",
        CONF_HOST: "192.168.1.50",
        CONF_TRANSPORT: TRANSPORT_LAN,
    }


def test_lan_setup_entry_data_preserves_optional_device_id() -> None:
    """A LAN entry may keep a better local identifier when known."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP547E")
    assert model is not None

    setup = manual_setup_entry_data(
        model,
        transport=TRANSPORT_LAN,
        device_id="Kitchen pixels",
        host="led-kitchen.local",
    )

    assert setup.unique_id == "lan:led-kitchen.local"
    assert setup.data[CONF_DEVICE_ID] == "Kitchen pixels"
    assert setup.data[CONF_HOST] == "led-kitchen.local"


def test_lan_setup_entry_data_from_spnet_response_creates_verified_sp541e() -> None:
    """A proven SPNet response can create a verified SP541E LAN entry."""
    catalog = default_catalog()

    setup = lan_setup_entry_data_from_spnet_response(
        catalog,
        bytes.fromhex(
            "53704e65740000210000000000010000105c00542024111f77075350353431450000"
        ),
        source="192.0.2.92",
    )

    assert setup.unique_id == "54:20:24:11:1f:77"
    assert setup.title == "SP541E 192.0.2.92"
    assert setup.data == {
        CONF_MODEL: "SP541E",
        CONF_MODEL_ID: 92,
        CONF_DEVICE_ID: "54:20:24:11:1F:77",
        CONF_HOST: "192.0.2.92",
        CONF_TRANSPORT: TRANSPORT_LAN,
        CONF_DISCOVERY_SOURCE: DISCOVERY_SOURCE_LAN,
        CONF_DISCOVERY_MATCH: DISCOVERY_MATCH_SPNET_MODEL_ID,
        CONF_DISCOVERY_CONFIDENCE: DISCOVERY_CONFIDENCE_VERIFIED,
    }


def test_lan_setup_entry_data_from_discovery_accepts_flow_shape() -> None:
    """Home Assistant LAN discovery data reuses the verified SPNet path."""
    catalog = default_catalog()

    setup = lan_setup_entry_data_from_discovery(
        catalog,
        {
            CONF_HOST: "192.0.2.92",
            CONF_DISCOVERY_RESPONSE_HEX: (
                "53704e65740000210000000000010000105c00542024111f77075350353431450000"
            ),
        },
    )

    assert setup.unique_id == "54:20:24:11:1f:77"
    assert setup.data[CONF_MODEL] == "SP541E"
    assert setup.data[CONF_MODEL_ID] == 92
    assert setup.data[CONF_DEVICE_ID] == "54:20:24:11:1F:77"
    assert setup.data[CONF_HOST] == "192.0.2.92"
    assert setup.data[CONF_TRANSPORT] == TRANSPORT_LAN
    assert setup.data[CONF_DISCOVERY_SOURCE] == DISCOVERY_SOURCE_LAN
    assert setup.data[CONF_DISCOVERY_MATCH] == DISCOVERY_MATCH_SPNET_MODEL_ID
    assert (
        setup.data[CONF_DISCOVERY_CONFIDENCE]
        == DISCOVERY_CONFIDENCE_VERIFIED
    )


def test_lan_setup_entry_data_from_discovery_accepts_raw_response_attr() -> None:
    """Attribute-style LAN discovery objects can carry raw response bytes."""
    catalog = default_catalog()

    setup = lan_setup_entry_data_from_discovery(
        catalog,
        SimpleNamespace(
            source="192.0.2.93",
            response=bytes.fromhex(
                "53704e65740000210000000000010000105c00562024111f88075350353431450000"
            ),
        ),
    )

    assert setup.unique_id == "56:20:24:11:1f:88"
    assert setup.data[CONF_MODEL] == "SP541E"
    assert setup.data[CONF_DEVICE_ID] == "56:20:24:11:1F:88"


def test_lan_setup_entry_data_from_spnet_response_rejects_unsafe_shapes() -> None:
    """SPNet setup only accepts the verified SP541E model-byte path."""
    catalog = default_catalog()

    cases = (
        (b"not-spnet", "192.0.2.93", CONF_MODEL, "unknown_model"),
        (
            bytes.fromhex("53704e6574000021000000000001"),
            "192.0.2.93",
            CONF_MODEL_ID,
            "unknown_model_id",
        ),
        (
            bytes.fromhex("53704e657400002100000000000100"),
            "192.0.2.93",
            CONF_MODEL_ID,
            "unknown_model_id",
        ),
        (
            bytes.fromhex("53704e657400002100000000000196"),
            "192.0.2.93",
            CONF_TRANSPORT,
            "unsupported_lan_transport",
        ),
        (
            bytes.fromhex(
                "53704e65740000210000000000010000105c00542024111f77075350353431450000"
            ),
            "",
            CONF_HOST,
            "required",
        ),
    )
    for response, source, field, reason in cases:
        try:
            lan_setup_entry_data_from_spnet_response(
                catalog,
                response,
                source=source,
            )
        except SetupDataError as ex:
            assert ex.field == field
            assert ex.reason == reason
        else:
            raise AssertionError(f"{response.hex()} should not create LAN setup data")


def test_lan_setup_rejects_models_without_lan_capability() -> None:
    """BLE-only models cannot be configured as LAN devices."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP630E")
    assert model is not None

    try:
        manual_setup_entry_data(
            model,
            transport=TRANSPORT_LAN,
            host="192.168.1.51",
        )
    except SetupDataError as ex:
        assert ex.field == CONF_TRANSPORT
        assert ex.reason == "unsupported_lan_transport"
    else:
        raise AssertionError("BLE-only models should reject LAN setup")


def test_lan_setup_requires_a_plain_host() -> None:
    """LAN setup validates the host before creating entry data."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP802E")
    assert model is not None

    for host, reason in (("", "required"), ("http://device.local", "invalid_host")):
        try:
            manual_setup_entry_data(model, transport=TRANSPORT_LAN, host=host)
        except SetupDataError as ex:
            assert ex.field == CONF_HOST
            assert ex.reason == reason
        else:
            raise AssertionError(f"{host!r} should not be accepted")


def test_manual_setup_rejects_unknown_transport() -> None:
    """Only the explicitly implemented setup transports are accepted."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP601E")
    assert model is not None

    try:
        manual_setup_entry_data(model, transport="cloud")
    except SetupDataError as ex:
        assert ex.field == CONF_TRANSPORT
        assert ex.reason == "unsupported_transport"
    else:
        raise AssertionError("unknown setup transports should fail visibly")


def test_every_user_facing_model_has_advertised_manual_setup_routes() -> None:
    """Every APK catalog model can create setup data for its local transports."""
    catalog = default_catalog()
    route_counts = {
        TRANSPORT_BLE: 0,
        TRANSPORT_BLE_MESH: 0,
        TRANSPORT_LAN: 0,
        "cloud_optional": 0,
    }

    for model in catalog.user_facing_models():
        if TransportKind.BLE in model.transports:
            setup = manual_setup_entry_data(
                model,
                transport=TRANSPORT_BLE,
                address="AA:BB:CC:DD:EE:09",
            )
            assert setup.data[CONF_MODEL] == model.name
            assert setup.data[CONF_MODEL_ID] == model.model_id
            assert setup.data[CONF_TRANSPORT] == TRANSPORT_BLE
            assert setup.data[CONF_ADDRESS] == "AA:BB:CC:DD:EE:09"
            route_counts[TRANSPORT_BLE] += 1

        if TransportKind.BLE_MESH in model.transports:
            setup = manual_setup_entry_data(
                model,
                transport=TRANSPORT_BLE_MESH,
                address="AA:BB:CC:DD:EE:0A",
                mesh_uuid="0x211",
            )
            assert setup.data[CONF_MODEL] == model.name
            assert setup.data[CONF_MODEL_ID] == model.model_id
            assert setup.data[CONF_TRANSPORT] == TRANSPORT_BLE_MESH
            assert setup.data[CONF_ADDRESS] == "AA:BB:CC:DD:EE:0A"
            assert setup.data[CONF_MESH_UUID] == 0x0211
            route_counts[TRANSPORT_BLE_MESH] += 1

        if TransportKind.LAN in model.transports:
            setup = manual_setup_entry_data(
                model,
                transport=TRANSPORT_LAN,
                host="192.0.2.55",
            )
            assert setup.data[CONF_MODEL] == model.name
            assert setup.data[CONF_MODEL_ID] == model.model_id
            assert setup.data[CONF_TRANSPORT] == TRANSPORT_LAN
            assert setup.data[CONF_HOST] == "192.0.2.55"
            assert setup.unique_id == "lan:192.0.2.55"
            route_counts[TRANSPORT_LAN] += 1

        if TransportKind.CLOUD_OPTIONAL in model.transports:
            route_counts["cloud_optional"] += 1

    assert route_counts == {
        TRANSPORT_BLE: 124,
        TRANSPORT_BLE_MESH: 27,
        TRANSPORT_LAN: 41,
        "cloud_optional": 39,
    }
