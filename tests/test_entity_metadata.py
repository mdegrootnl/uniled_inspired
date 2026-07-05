"""Home Assistant entity metadata tests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from custom_components.uniled.const import (
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
from custom_components.uniled.core import (
    EntityCategoryKind,
    FeatureSpec,
    PlatformKind,
    default_catalog,
    plan_for_model,
)
from custom_components.uniled.entity_metadata import (
    device_connections,
    device_identifiers,
    entity_registry_enabled_default,
    entry_data_identity,
    entry_identity,
    feature_translation_key,
    feature_translation_placeholders,
    legacy_uniled_unique_id,
)


def test_command_feature_translation_metadata_preserves_dynamic_context() -> None:
    """Translated command names keep output, scene, and mesh-node context."""
    catalog = default_catalog()
    sp601 = catalog.resolve_name("SP601E")
    assert sp601 is not None
    sp601_plan = plan_for_model(sp601)

    output_effect = next(
        feature
        for feature in sp601_plan.features
        if feature.platform is PlatformKind.SELECT
        and feature.key == "effect"
        and feature.channel == 1
    )
    output_light = next(
        feature
        for feature in sp601_plan.features
        if feature.platform is PlatformKind.LIGHT
        and feature.implementation_hint == "legacy_uniled_output"
        and feature.channel == 1
    )
    scene = sp601_plan.feature("scene_0")

    assert feature_translation_key(output_effect) == "output_effect"
    assert feature_translation_placeholders(output_effect) == {"output": "1"}
    assert feature_translation_key(output_light) == "output_light"
    assert feature_translation_placeholders(output_light) == {"output": "1"}
    assert feature_translation_key(scene) == "scene_slot"
    assert feature_translation_placeholders(scene) == {"slot": "1"}

    mesh_effect = FeatureSpec(
        key="effect",
        platform=PlatformKind.SELECT,
        name="Node 68 effect",
        channel=0x44,
        implemented=True,
        implementation_hint="zengge_mesh_node",
    )
    mesh_speed = FeatureSpec(
        key="effect_speed",
        platform=PlatformKind.NUMBER,
        name="Node 68 effect speed",
        channel=0x44,
        entity_category=EntityCategoryKind.CONFIG,
        implemented=True,
        implementation_hint="zengge_mesh_node",
    )

    assert feature_translation_key(mesh_effect) == "mesh_node_effect"
    assert feature_translation_placeholders(mesh_effect) == {"node": "68"}
    assert feature_translation_key(mesh_speed) == "mesh_node_effect_speed"
    assert feature_translation_placeholders(mesh_speed) == {"node": "68"}


def test_entity_registry_enabled_default_reflects_planner_flag() -> None:
    """HA entity defaults use the planner's enabled-by-default decision."""
    enabled = FeatureSpec(
        key="main_light",
        platform=PlatformKind.LIGHT,
        name="Light",
        enabled_by_default=True,
    )
    disabled = FeatureSpec(
        key="scene_0",
        platform=PlatformKind.SCENE,
        name="Scene 1",
        enabled_by_default=False,
    )

    assert entity_registry_enabled_default(enabled) is True
    assert entity_registry_enabled_default(disabled) is False


def test_entry_identity_prefers_config_entry_unique_id() -> None:
    """Entity IDs use HA's stable config-entry unique ID when available."""
    entry = SimpleNamespace(
        unique_id="ble:aa:bb:cc:dd:ee:ff",
        entry_id="volatile-row-id",
        data={
            CONF_TRANSPORT: TRANSPORT_BLE,
            CONF_ADDRESS: "11:22:33:44:55:66",
        },
    )

    assert entry_identity(entry) == "ble:aa:bb:cc:dd:ee:ff"
    assert device_identifiers(entry) == {(DOMAIN, "ble:aa:bb:cc:dd:ee:ff")}


def test_entry_identity_derives_setup_unique_ids_from_entry_data() -> None:
    """Entries without a HA unique_id still get stable setup-derived IDs."""
    cases = (
        (
            {CONF_TRANSPORT: TRANSPORT_BLE, CONF_ADDRESS: "AA:BB:CC:DD:EE:07"},
            "ble:aa:bb:cc:dd:ee:07",
        ),
        (
            {CONF_TRANSPORT: TRANSPORT_LAN, CONF_HOST: "LED-Kitchen.local"},
            "lan:led-kitchen.local",
        ),
        (
            {
                CONF_TRANSPORT: TRANSPORT_LAN,
                CONF_HOST: "192.0.2.92",
                CONF_DEVICE_ID: "54:20:24:11:1F:77",
            },
            "54:20:24:11:1f:77",
        ),
        (
            {
                CONF_TRANSPORT: TRANSPORT_MANUAL,
                CONF_MODEL: "SP601E",
                CONF_DEVICE_ID: "Bench Controller",
            },
            "manual:SP601E:bench controller",
        ),
        (
            {CONF_TRANSPORT: TRANSPORT_BLE_MESH, CONF_MESH_UUID: "0x211"},
            "zng_mesh_0x211",
        ),
        (
            {
                CONF_TRANSPORT: TRANSPORT_BLE_MESH,
                CONF_MODEL: "SP310E",
                CONF_ADDRESS: "AA:BB:CC:DD:EE:08",
                CONF_MESH_UUID: "0x211",
            },
            "ble_mesh:aa:bb:cc:dd:ee:08",
        ),
        (
            {
                CONF_TRANSPORT: TRANSPORT_BLE_MESH,
                CONF_MODEL: "SP310E",
                CONF_MESH_UUID: "0x211",
            },
            "ble_mesh:sp310e:0x211",
        ),
    )

    for data, expected in cases:
        entry = SimpleNamespace(unique_id=None, entry_id="volatile-row-id", data=data)

        assert entry_data_identity(data) == expected
        assert entry_identity(entry) == expected
        assert device_identifiers(entry) == {(DOMAIN, expected)}


def test_device_connections_expose_proven_physical_addresses() -> None:
    """Device registry connections use proven Bluetooth and LAN MAC addresses."""
    ble = SimpleNamespace(
        unique_id=None,
        entry_id="ble-row",
        data={CONF_TRANSPORT: TRANSPORT_BLE, CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
    )
    mesh = SimpleNamespace(
        unique_id=None,
        entry_id="mesh-row",
        data={
            CONF_TRANSPORT: TRANSPORT_BLE_MESH,
            CONF_ADDRESS: "AA:BB:CC:DD:EE:02",
            CONF_DEVICE_ID: "zng_mesh_0x211",
        },
    )
    lan = SimpleNamespace(
        unique_id=None,
        entry_id="lan-row",
        data={CONF_TRANSPORT: TRANSPORT_LAN, CONF_HOST: "192.0.2.55"},
    )
    spnet = SimpleNamespace(
        unique_id=None,
        entry_id="spnet-row",
        data={
            CONF_TRANSPORT: TRANSPORT_LAN,
            CONF_HOST: "192.0.2.92",
            CONF_DEVICE_ID: "54:20:24:11:1F:77",
        },
    )
    migrated_spnet = SimpleNamespace(
        unique_id="56:20:24:06:d6:ee",
        entry_id="migrated-spnet-row",
        data={
            CONF_TRANSPORT: TRANSPORT_LAN,
            CONF_HOST: "192.168.0.160",
            CONF_DEVICE_ID: "192.168.0.160",
        },
    )

    assert device_connections(ble) == {("bluetooth", "AA:BB:CC:DD:EE:FF")}
    assert device_connections(mesh) == {("bluetooth", "AA:BB:CC:DD:EE:02")}
    assert device_connections(lan) == set()
    assert device_connections(spnet) == {("mac", "54:20:24:11:1F:77")}
    assert device_connections(migrated_spnet) == {("mac", "56:20:24:06:d6:ee")}


def test_sp541e_lan_entities_reuse_legacy_uniled_unique_ids() -> None:
    """Migrated house-light controls keep the old UniLED registry identity."""
    entry = SimpleNamespace(
        unique_id="54:20:24:11:1f:77",
        entry_id="entry-id",
        data={CONF_MODEL: "SP541E", CONF_TRANSPORT: TRANSPORT_LAN},
    )

    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(key="main_light", platform=PlatformKind.LIGHT, name="Light"),
    ) == "_54:20:24:11:1f:77_strip"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="audio_sensitivity",
            platform=PlatformKind.NUMBER,
            name="Audio sensitivity",
        ),
    ) == "_54:20:24:11:1f:77_sensitivity"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="effect_speed",
            platform=PlatformKind.NUMBER,
            name="Effect speed",
        ),
    ) == "_54:20:24:11:1f:77_effect_speed"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="audio_input",
            platform=PlatformKind.SELECT,
            name="Audio input",
        ),
    ) == "_54:20:24:11:1f:77_audio_input"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="light_mode",
            platform=PlatformKind.SELECT,
            name="Light mode",
        ),
    ) == "_54:20:24:11:1f:77_light_mode"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="effect_type",
            platform=PlatformKind.SENSOR,
            name="Effect type",
            entity_category=EntityCategoryKind.DIAGNOSTIC,
        ),
    ) == "_54:20:24:11:1f:77_effect_type"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="effect_direction",
            platform=PlatformKind.SWITCH,
            name="Direction",
        ),
    ) == "_54:20:24:11:1f:77_effect_direction"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="effect_loop",
            platform=PlatformKind.SWITCH,
            name="Effect loop",
        ),
    ) == "_54:20:24:11:1f:77_effect_loop"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="effect_play",
            platform=PlatformKind.SWITCH,
            name="Effect play",
        ),
    ) == "_54:20:24:11:1f:77_effect_play"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(key="effect", platform=PlatformKind.SELECT, name="Effect"),
    ) is None


def test_direct_ble_entities_reuse_old_uniled_raw_address_unique_ids() -> None:
    """Migrated old-UniLED BLE entries keep single-channel entity IDs."""
    entry = SimpleNamespace(
        unique_id="AA:BB:CC:DD:EE:10",
        entry_id="entry-id",
        data={CONF_MODEL: "SP611E", CONF_TRANSPORT: TRANSPORT_BLE},
    )
    new_identity_entry = SimpleNamespace(
        unique_id="ble:aa:bb:cc:dd:ee:10",
        entry_id="entry-id",
        data={
            CONF_MODEL: "SP611E",
            CONF_TRANSPORT: TRANSPORT_BLE,
            CONF_ADDRESS: "AA:BB:CC:DD:EE:10",
        },
    )

    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(key="main_light", platform=PlatformKind.LIGHT, name="Light"),
    ) == "_AA:BB:CC:DD:EE:10_strip"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(key="effect", platform=PlatformKind.SELECT, name="Effect"),
    ) == "_AA:BB:CC:DD:EE:10_effect"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="audio_sensitivity",
            platform=PlatformKind.NUMBER,
            name="Audio sensitivity",
        ),
    ) == "_AA:BB:CC:DD:EE:10_sensitivity"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="effect_type",
            platform=PlatformKind.SENSOR,
            name="Effect type",
            entity_category=EntityCategoryKind.DIAGNOSTIC,
        ),
    ) == "_AA:BB:CC:DD:EE:10_effect_type"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(key="refresh", platform=PlatformKind.BUTTON, name="Refresh"),
    ) is None
    assert legacy_uniled_unique_id(
        new_identity_entry,
        FeatureSpec(key="main_light", platform=PlatformKind.LIGHT, name="Light"),
    ) is None


def test_direct_ble_output_entities_reuse_old_uniled_channel_unique_ids() -> None:
    """Old SP601/SP60x output entities used master/channel identity segments."""
    entry = SimpleNamespace(
        unique_id="AA:BB:CC:DD:EE:20",
        entry_id="entry-id",
        data={CONF_MODEL: "SP601E", CONF_TRANSPORT: TRANSPORT_BLE},
    )

    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(key="main_light", platform=PlatformKind.LIGHT, name="Light"),
    ) == "_AA:BB:CC:DD:EE:20_master_strip"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="output_1_light",
            platform=PlatformKind.LIGHT,
            name="Output 1",
            channel=1,
            implementation_hint="legacy_uniled_output",
        ),
    ) == "_AA:BB:CC:DD:EE:20_channel_1_strip"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="effect_speed",
            platform=PlatformKind.NUMBER,
            name="Output 1 effect speed",
            channel=1,
        ),
    ) == "_AA:BB:CC:DD:EE:20_channel_1_effect_speed"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="scene_loop",
            platform=PlatformKind.SWITCH,
            name="Scene loop",
        ),
    ) == "_AA:BB:CC:DD:EE:20_master_scene_loop"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="scene_0",
            platform=PlatformKind.SCENE,
            name="Scene 1",
            implementation_hint="legacy_uniled",
        ),
    ) == "_AA:BB:CC:DD:EE:20_master_scene_0"


def test_zengge_mesh_node_entities_reuse_old_uniled_unique_ids() -> None:
    """Old RG4 mesh node entities used decimal node identity segments."""
    entry = SimpleNamespace(
        unique_id="zng_mesh_0x211",
        entry_id="entry-id",
        data={CONF_MODEL: "RG4", CONF_TRANSPORT: TRANSPORT_BLE_MESH},
    )
    scene_mesh = SimpleNamespace(
        unique_id="ble_mesh:aa:bb:cc:dd:ee:30",
        entry_id="entry-id",
        data={CONF_MODEL: "SP310E", CONF_TRANSPORT: TRANSPORT_BLE_MESH},
    )

    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="mesh_light_44",
            platform=PlatformKind.LIGHT,
            name="Counter Strip",
            channel=0x44,
            implementation_hint="zengge_mesh_node",
        ),
    ) == "_zng_mesh_0x211_node_68"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="mesh_panel_20_status",
            platform=PlatformKind.SENSOR,
            name="Wall Panel status",
            channel=0x20,
            entity_category=EntityCategoryKind.DIAGNOSTIC,
            implementation_hint="zengge_mesh_panel",
        ),
    ) == "_zng_mesh_0x211_node_32"
    assert legacy_uniled_unique_id(
        entry,
        FeatureSpec(
            key="effect_speed",
            platform=PlatformKind.NUMBER,
            name="Node 68 effect speed",
            channel=0x44,
            implementation_hint="zengge_mesh_node",
        ),
    ) is None
    assert legacy_uniled_unique_id(
        scene_mesh,
        FeatureSpec(
            key="mesh_light_44",
            platform=PlatformKind.LIGHT,
            name="Counter Strip",
            channel=0x44,
            implementation_hint="zengge_mesh_node",
        ),
    ) is None


def test_command_feature_translation_keys_have_english_names() -> None:
    """Every command translation key emitted by the helper exists in en.json."""
    translations = json.loads(
        Path("custom_components/uniled/translations/en.json").read_text()
    )
    entities = translations["entity"]

    samples = (
        FeatureSpec(
            key="refresh",
            platform=PlatformKind.BUTTON,
            name="Refresh",
            entity_category=EntityCategoryKind.DIAGNOSTIC,
        ),
        FeatureSpec(key="main_light", platform=PlatformKind.LIGHT, name="Light"),
        FeatureSpec(
            key="output_1_light",
            platform=PlatformKind.LIGHT,
            name="Output 1",
            channel=1,
            implementation_hint="legacy_uniled_output",
        ),
        FeatureSpec(
            key="mesh_light_44",
            platform=PlatformKind.LIGHT,
            name="Node 68",
            channel=0x44,
            implementation_hint="zengge_mesh_node",
        ),
        FeatureSpec(key="effect_speed", platform=PlatformKind.NUMBER, name="Speed"),
        FeatureSpec(
            key="effect_length",
            platform=PlatformKind.NUMBER,
            name="Output 1 length",
            channel=1,
        ),
        FeatureSpec(key="effect", platform=PlatformKind.SELECT, name="Effect"),
        FeatureSpec(
            key="chip_order",
            platform=PlatformKind.SELECT,
            name="Output 1 chip order",
            channel=1,
            entity_category=EntityCategoryKind.CONFIG,
        ),
        FeatureSpec(
            key="effect_direction",
            platform=PlatformKind.SWITCH,
            name="Output 1 direction",
            channel=1,
        ),
        FeatureSpec(key="scene_0", platform=PlatformKind.SCENE, name="Scene 1"),
    )

    for feature in samples:
        key = feature_translation_key(feature)
        if key is None:
            continue
        platform = feature.platform.value
        assert entities[platform][key]["name"], (platform, key)


def test_all_implemented_diagnostic_sensors_have_english_names() -> None:
    """Diagnostic sensors are real entities, including recognized-only models."""
    translations = json.loads(
        Path("custom_components/uniled/translations/en.json").read_text()
    )
    sensor_entities = translations["entity"]["sensor"]

    for model in default_catalog().user_facing_models():
        for feature in plan_for_model(model).features:
            if feature.platform is not PlatformKind.SENSOR or not feature.implemented:
                continue
            key = feature_translation_key(feature)
            assert key is not None, (model.name, feature.key)
            assert sensor_entities[key]["name"], (model.name, feature.key, key)

    panel = FeatureSpec(
        key="mesh_panel_20_status",
        platform=PlatformKind.SENSOR,
        name="Wall Panel status",
        channel=0x20,
        entity_category=EntityCategoryKind.DIAGNOSTIC,
        implemented=True,
        implementation_hint="zengge_mesh_panel",
    )

    assert feature_translation_key(panel) == "mesh_panel_status"
    assert feature_translation_placeholders(panel) == {"node": "32"}
    assert sensor_entities["mesh_panel_status"]["name"] == "Panel node {node} status"
