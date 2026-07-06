"""Entity planner coverage tests."""

from __future__ import annotations

from custom_components.uniled.core import (
    EntityCategoryKind,
    PlatformKind,
    ProtocolFamily,
    TransportKind,
    default_catalog,
    plan_for_model,
    protocol_evidence_profile_for_model,
    select_options_for_family,
)
from custom_components.uniled.core.scene import (
    SCENE_MODE_EFFECTS,
    SCENE_MODE_ICON_COUNT,
)


def test_every_user_facing_model_has_a_safe_entity_plan() -> None:
    """Every user-facing catalog model has diagnostics and planned controls."""
    catalog = default_catalog()

    for model in catalog.user_facing_models():
        plan = plan_for_model(model)

        assert plan.features, model.name
        assert plan.has_feature("catalog_model"), model.name
        assert plan.has_feature("catalog_model_id"), model.name
        assert plan.has_feature("catalog_parent_id"), model.name
        assert plan.has_feature("catalog_connect_caps"), model.name
        assert plan.has_feature("catalog_connect_capabilities"), model.name
        assert plan.has_feature("catalog_spec_functions"), model.name
        assert plan.has_feature("catalog_spec_function_bits"), model.name
        assert plan.has_feature("catalog_color_cap"), model.name
        assert plan.has_feature("catalog_color_capabilities"), model.name
        assert plan.has_feature("catalog_feature_count"), model.name
        assert plan.has_feature("catalog_feature_keys"), model.name
        assert plan.has_feature("catalog_feature_summary"), model.name
        assert plan.has_feature("catalog_variant_count"), model.name
        assert plan.has_feature("catalog_variant_ids"), model.name
        assert plan.has_feature("protocol_family"), model.name
        assert plan.has_feature("support_level"), model.name
        assert plan.has_feature("support_disposition"), model.name
        assert plan.has_feature("support_blocker_count"), model.name
        assert plan.has_feature("support_blockers"), model.name
        assert plan.has_feature("transport"), model.name
        assert plan.has_feature("configured_transport"), model.name
        assert plan.has_feature("discovery_source"), model.name
        assert plan.has_feature("discovery_match"), model.name
        assert plan.has_feature("discovery_confidence"), model.name
        assert plan.has_feature("runtime_transport_state"), model.name
        assert plan.has_feature("last_refresh_result"), model.name

        for feature in plan.features:
            if feature.entity_category is EntityCategoryKind.DIAGNOSTIC:
                continue
            assert not feature.implemented, (model.name, feature.key)
            assert not feature.enabled_by_default, (model.name, feature.key)


def test_filtered_models_have_no_entities() -> None:
    """Filtered catalog entries are known but not exposed."""
    catalog = default_catalog()

    for model in catalog.filtered_models():
        assert plan_for_model(model).features == ()


def test_color_capable_models_get_planned_light_entities() -> None:
    """Models with color capabilities receive a planned primary light entity."""
    catalog = default_catalog()

    for model in catalog.user_facing_models():
        plan = plan_for_model(model)
        light_features = plan.features_for_platform(PlatformKind.LIGHT)

        if model.color_cap > 0:
            expected_count = {
                ProtocolFamily.BANLANX_601: 3,
                ProtocolFamily.BANLANX_60X: 5 if model.name == "SP602E" else 9,
            }.get(model.family, 1)
            assert len(light_features) == expected_count, model.name
            assert light_features[0].key == "main_light", model.name
            assert light_features[0].channel == 0, model.name
            assert light_features[0].color_modes, model.name
        else:
            assert light_features == (), model.name


def test_ble_models_get_apk_bridge_evidence_diagnostics() -> None:
    """Direct-BLE catalog models expose APK bridge evidence counts."""
    catalog = default_catalog()

    for model in catalog.user_facing_models():
        plan = plan_for_model(model)

        if TransportKind.BLE not in model.transports:
            assert not plan.has_feature("ble_profile"), model.name
            assert not plan.has_feature("ble_uuid_binding_status"), model.name
            assert not plan.has_feature("ble_known_service_uuid_count"), model.name
            assert not plan.has_feature("ble_known_service_uuids"), model.name
            assert not plan.has_feature("ble_known_write_uuid"), model.name
            assert not plan.has_feature("ble_known_notify_uuid"), model.name
            assert not plan.has_feature("ble_uuid_pool_count"), model.name
            assert not plan.has_feature("ble_apk_uuid_pool"), model.name
            assert not plan.has_feature("ble_uuid_inventory_count"), model.name
            assert not plan.has_feature("ble_unbound_uuid_candidate_count"), model.name
            assert not plan.has_feature("ble_unbound_uuid_candidates"), model.name
            assert not plan.has_feature("ble_legacy_uuid_candidate_count"), model.name
            assert not plan.has_feature("ble_legacy_uuid_candidates"), model.name
            assert not plan.has_feature("ble_scan_result_field_count"), model.name
            assert not plan.has_feature("ble_service_result_field_count"), model.name
            assert not plan.has_feature(
                "ble_characteristic_result_field_count"
            ), model.name
            assert not plan.has_feature("ble_rssi_result_field_count"), model.name
            assert not plan.has_feature("ble_mtu_result_field_count"), model.name
            assert not plan.has_feature(
                "ble_adapter_state_result_field_count"
            ), model.name
            assert not plan.has_feature(
                "ble_notification_event_field_count"
            ), model.name
            assert not plan.has_feature("ble_connection_event_field_count"), model.name
            assert not plan.has_feature(
                "ble_device_found_event_field_count"
            ), model.name
            assert not plan.has_feature("ble_descriptor_uuid_count"), model.name
            assert not plan.has_feature(
                "ble_boolean_event_channel_count"
            ), model.name
            assert not plan.has_feature("ble_plugin_event_hint_count"), model.name
            assert not plan.has_feature("ble_plugin_error_code_count"), model.name
            assert not plan.has_feature("ble_issue_advertisement_count"), model.name
            assert not plan.has_feature("ble_issue_advertisements"), model.name
            continue

        for key, unit in {
            "ble_profile": None,
            "ble_uuid_binding_status": None,
            "ble_known_service_uuid_count": "uuids",
            "ble_known_service_uuids": None,
            "ble_known_write_uuid": None,
            "ble_known_notify_uuid": None,
            "ble_uuid_pool_count": "uuids",
            "ble_apk_uuid_pool": None,
            "ble_uuid_inventory_count": "uuids",
            "ble_unbound_uuid_candidate_count": "uuids",
            "ble_unbound_uuid_candidates": None,
            "ble_legacy_uuid_candidate_count": "uuids",
            "ble_legacy_uuid_candidates": None,
            "ble_plugin_method_count": "methods",
            "ble_plugin_argument_count": "arguments",
            "ble_plugin_result_field_count": "fields",
            "ble_scan_result_field_count": "fields",
            "ble_service_result_field_count": "fields",
            "ble_characteristic_result_field_count": "fields",
            "ble_rssi_result_field_count": "fields",
            "ble_mtu_result_field_count": "fields",
            "ble_adapter_state_result_field_count": "fields",
            "ble_notification_event_field_count": "fields",
            "ble_connection_event_field_count": "fields",
            "ble_device_found_event_field_count": "fields",
            "ble_descriptor_uuid_count": "uuids",
            "ble_boolean_event_channel_count": "channels",
            "ble_plugin_event_hint_count": "hints",
            "ble_plugin_contract_hint_count": "hints",
            "ble_plugin_error_code_count": "codes",
            "ble_plugin_channel_count": "channels",
            "ble_protocol_gap_count": "gaps",
            "ble_issue_advertisement_count": "adverts",
            "ble_issue_advertisements": None,
        }.items():
            feature = plan.feature(key)
            assert feature.platform is PlatformKind.SENSOR, (model.name, key)
            assert feature.entity_category is EntityCategoryKind.DIAGNOSTIC, (
                model.name,
                key,
            )
            assert feature.implemented, (model.name, key)
            assert feature.unit == unit, (model.name, key)


def test_protocol_backed_models_expose_effect_type_diagnostic() -> None:
    """Parsed effect-type state is exposed only where command protocol is known."""
    catalog = default_catalog()

    for model in catalog.user_facing_models():
        plan = plan_for_model(model)
        if protocol_evidence_profile_for_model(model) is None:
            assert not plan.has_feature("effect_type"), model.name
            continue

        feature = plan.feature("effect_type")
        assert feature.platform is PlatformKind.SENSOR
        assert feature.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert feature.implemented


def test_catalog_pixel_limits_create_diagnostics_and_config_numbers() -> None:
    """Pixel-limit metadata is exposed safely and kept planned for writes."""
    catalog = default_catalog()

    expected = {
        "SP660E": 1800,
        "SP310E": 2700,
        "SP558E": 3000,
        "SP530E": 3600,
    }

    for name, maximum in expected.items():
        model = catalog.resolve_name(name)
        assert model is not None

        pixel_count = plan_for_model(model).feature("pixel_count")
        assert pixel_count.platform is PlatformKind.NUMBER
        assert pixel_count.maximum == maximum
        assert pixel_count.unit == "px"
        assert pixel_count.implemented is False

        max_pixels = plan_for_model(model).feature("max_pixel_channels")
        assert max_pixels.platform is PlatformKind.SENSOR
        assert max_pixels.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert max_pixels.implemented is True
        assert max_pixels.unit == "px"


def test_legacy_command_controls_are_planned_with_safe_limits() -> None:
    """Ported legacy families expose planned command controls."""
    catalog = default_catalog()
    expected_lengths = {
        "SP601E": 150,
        "SP602E": 240,
        "SP611E": 150,
        "SP630E": 150,
    }

    for name, maximum in expected_lengths.items():
        model = catalog.resolve_name(name)
        assert model is not None

        effect_length = plan_for_model(model).feature("effect_length")

        assert effect_length.platform is PlatformKind.NUMBER
        assert effect_length.maximum == maximum

    sp601 = catalog.resolve_name("SP601E")
    assert sp601 is not None
    sp601_plan = plan_for_model(sp601)
    sp601_lights = sp601_plan.features_for_platform(PlatformKind.LIGHT)
    assert [feature.key for feature in sp601_lights] == [
        "main_light",
        "output_1_light",
        "output_2_light",
    ]
    assert [feature.channel for feature in sp601_lights] == [0, 1, 2]
    assert sp601_lights[1].name == "Output 1"
    assert sp601_lights[1].implementation_hint == "legacy_uniled_output"
    assert sp601_lights[1].implemented is False
    assert sp601_lights[1].enabled_by_default is False
    assert sp601_plan.feature("effect").channel == 1
    assert sp601_plan.feature("effect").name == "Output 1 effect"
    assert sp601_plan.feature("effect_direction").platform is PlatformKind.SWITCH
    assert sp601_plan.feature("effect_direction").channel == 1
    assert sp601_plan.feature("scene_loop").platform is PlatformKind.SWITCH
    assert sp601_plan.feature("scene_loop").channel == 0
    assert sp601_plan.feature("scene_loop").name == "Scene loop"
    effect_options = sp601_plan.feature("effect").options
    assert len(effect_options) == 41
    assert effect_options[:4] == (
        "Solid",
        "Rainbow",
        "Rainbow Stars",
        "Twinkle Stars",
    )
    assert effect_options[-1] == "Sound - Party"
    assert effect_options == select_options_for_family(
        ProtocolFamily.BANLANX_601,
        "effect",
    )
    assert not sp601_plan.has_feature("audio_input")
    assert sp601_plan.feature("chip_order").options == (
        "RGB",
        "RBG",
        "GRB",
        "GBR",
        "BRG",
        "BGR",
    )
    assert sp601_plan.feature("chip_order").channel == 1
    sp601_effect_channels = [
        feature.channel
        for feature in sp601_plan.features_for_platform(PlatformKind.SELECT)
        if feature.key == "effect"
    ]
    assert sp601_effect_channels == [1, 2]
    sp601_chip_channels = [
        feature.channel
        for feature in sp601_plan.features_for_platform(PlatformKind.SELECT)
        if feature.key == "chip_order"
    ]
    assert sp601_chip_channels == [1, 2]
    sp601_scenes = sp601_plan.features_for_platform(PlatformKind.SCENE)
    assert len(sp601_scenes) == 9
    assert sp601_scenes[0].key == "scene_0"
    assert sp601_scenes[0].name == "Scene 1"
    assert sp601_scenes[0].channel == 0
    assert sp601_scenes[0].implemented is False
    assert sp601_scenes[0].enabled_by_default is False
    assert sp601_scenes[-1].key == "scene_8"
    assert sp601_scenes[-1].name == "Scene 9"
    assert sp601_scenes[-1].channel == 8
    assert sp601_plan.feature("audio_sensitivity").maximum == 16
    assert sp601_plan.feature("audio_sensitivity").channel == 1

    sp602 = catalog.resolve_name("SP602E")
    assert sp602 is not None
    sp602_plan = plan_for_model(sp602)
    sp602_lights = sp602_plan.features_for_platform(PlatformKind.LIGHT)
    assert [feature.key for feature in sp602_lights] == [
        "main_light",
        "output_1_light",
        "output_2_light",
        "output_3_light",
        "output_4_light",
    ]
    assert [feature.channel for feature in sp602_lights] == list(range(5))
    assert sp602_lights[-1].name == "Output 4"
    assert sp602_lights[-1].implementation_hint == "legacy_uniled_output"
    assert not sp602_plan.has_feature("audio_input")
    assert sp602_plan.feature("audio_sensitivity").channel == 0
    sp602_effect_channels = [
        feature.channel
        for feature in sp602_plan.features_for_platform(PlatformKind.SELECT)
        if feature.key == "effect"
    ]
    assert sp602_effect_channels == [1, 2, 3, 4]
    sp602_chip_channels = [
        feature.channel
        for feature in sp602_plan.features_for_platform(PlatformKind.SELECT)
        if feature.key == "chip_order"
    ]
    assert sp602_chip_channels == [1, 2, 3, 4]
    sp602_scenes = sp602_plan.features_for_platform(PlatformKind.SCENE)
    assert len(sp602_scenes) == 9
    assert sp602_scenes[0].key == "scene_0"
    assert sp602_scenes[-1].key == "scene_8"

    sp107 = catalog.resolve_name("SP107E")
    assert sp107 is not None
    sp107_plan = plan_for_model(sp107)
    assert sp107_plan.feature("chip_type").entity_category is EntityCategoryKind.CONFIG
    assert sp107_plan.feature("chip_type").options[:3] == (
        "SM16703",
        "TM1804",
        "UCS1903",
    )
    assert sp107_plan.feature("chip_type").options[-1] == "P9412"
    assert sp107_plan.feature("segment_count").maximum == 64
    assert sp107_plan.feature("segment_pixels").maximum == 150
    assert sp107_plan.feature("segment_pixels").unit == "px"

    sp110 = catalog.resolve_name("SP110E")
    assert sp110 is not None
    sp110_plan = plan_for_model(sp110)
    assert sp110_plan.feature("chip_type").options == sp107_plan.feature(
        "chip_type"
    ).options
    assert not sp110_plan.has_feature("segment_count")
    assert sp110_plan.feature("segment_pixels").maximum == 1024
    assert sp110_plan.feature("segment_pixels").unit == "px"

    sp603 = catalog.resolve_name("SP603E")
    assert sp603 is not None
    sp603_plan = plan_for_model(sp603)
    sp603_effects = sp603_plan.feature("effect").options
    assert len(sp603_effects) == 22
    assert "Sound - Music Breath" not in sp603_effects
    assert not sp603_plan.has_feature("audio_input")
    assert not sp603_plan.has_feature("audio_sensitivity")
    assert not sp603_plan.has_feature("light_mode")
    assert sp603_plan.has_feature("effect_loop")

    sp608 = catalog.resolve_name("SP608E")
    assert sp608 is not None
    sp608_lights = plan_for_model(sp608).features_for_platform(PlatformKind.LIGHT)
    assert [feature.channel for feature in sp608_lights] == list(range(9))
    assert sp608_lights[-1].key == "output_8_light"

    sp611 = catalog.resolve_name("SP611E")
    assert sp611 is not None
    sp611_plan = plan_for_model(sp611)
    assert sp611_plan.features_for_platform(PlatformKind.SCENE) == ()
    sp611_effects = sp611_plan.feature("effect").options
    assert len(sp611_effects) == 161
    assert sp611_effects[:4] == (
        "Solid Color",
        "Rainbow",
        "Rainbow Metor",
        "Rainbow Stars",
    )
    assert "Solid White" not in sp611_effects
    assert sp611_effects[-1] == "Sound - Party"
    assert sp611_plan.feature("light_mode").options == (
        "Single FX",
        "Cycle Dynamic FX's",
        "Cycle Sound FX's",
    )
    assert not sp611_plan.has_feature("effect_loop")
    assert sp611_plan.feature("audio_input").options == (
        "Int. Mic",
        "Player",
        "Ext. Mic",
    )

    sp617 = catalog.resolve_name("SP617E")
    assert sp617 is not None
    sp617_plan = plan_for_model(sp617)
    sp617_effects = sp617_plan.feature("effect").options
    assert len(sp617_effects) == 162
    assert sp617_effects[:3] == ("Solid White", "Solid Color", "Rainbow")
    assert len(sp617_plan.feature("chip_order").options) == 24

    sp621 = catalog.resolve_name("SP621E")
    assert sp621 is not None
    sp621_plan = plan_for_model(sp621)
    sp621_effects = sp621_plan.feature("effect").options
    assert len(sp621_effects) == 143
    assert "Sound - Party" not in sp621_effects
    assert not sp621_plan.has_feature("audio_input")
    assert not sp621_plan.has_feature("audio_sensitivity")
    assert not sp621_plan.has_feature("light_mode")
    assert sp621_plan.has_feature("effect_loop")

    sp614 = catalog.resolve_name("SP614E")
    assert sp614 is not None
    sp614_plan = plan_for_model(sp614)
    assert sp614_plan.feature("effect").options[:3] == (
        "Solid White",
        "Solid Color",
        "Seven Color Gradient",
    )
    assert sp614_plan.has_feature("audio_input")
    assert sp614_plan.has_feature("audio_sensitivity")
    assert sp614_plan.has_feature("light_mode")
    assert not sp614_plan.has_feature("effect_loop")

    sp623 = catalog.resolve_name("SP623E")
    assert sp623 is not None
    sp623_plan = plan_for_model(sp623)
    assert len(sp623_plan.feature("effect").options) == 22
    assert not sp623_plan.has_feature("audio_input")
    assert not sp623_plan.has_feature("audio_sensitivity")
    assert not sp623_plan.has_feature("light_mode")
    assert sp623_plan.has_feature("effect_loop")

    sp624 = catalog.resolve_name("SP624E")
    assert sp624 is not None
    sp624_plan = plan_for_model(sp624)
    assert len(sp624_plan.feature("effect").options) == 23
    assert not sp624_plan.has_feature("audio_input")
    assert not sp624_plan.has_feature("audio_sensitivity")
    assert not sp624_plan.has_feature("light_mode")
    assert sp624_plan.has_feature("effect_loop")

    sp630 = catalog.resolve_name("SP630E")
    assert sp630 is not None
    sp630_plan = plan_for_model(sp630)
    assert sp630_plan.feature("effect").options == ()
    assert sp630_plan.feature("light_mode").options == ()
    assert len(sp630_plan.feature("light_type").options) == 14
    assert sp630_plan.feature("light_type").options[:3] == (
        "1 CH PWM - Single Color",
        "2 CH PWM - CCT",
        "3 CH PWM - RGB",
    )
    assert sp630_plan.feature("chip_order").options == ()
    assert sp630_plan.has_feature("onoff_effect")
    assert sp630_plan.has_feature("onoff_speed")
    assert sp630_plan.feature("onoff_pixels").maximum == 600
    assert sp630_plan.feature("on_power").options == (
        "Light Off",
        "Light On",
        "Last state",
    )
    assert sp630_plan.has_feature("effect_play")
    assert sp630_plan.has_feature("coexistence")

    sp548 = catalog.resolve_name("SP548E")
    assert sp548 is not None
    sp548_plan = plan_for_model(sp548)
    sp548_effects = sp548_plan.feature("effect").options
    assert not sp548_plan.has_feature("light_type")
    assert "Custom Solid - Firework" in sp548_effects
    assert "Custom Gradient - Spin" in sp548_effects
    assert "Custom Gradient" in sp548_plan.feature("light_mode").options
    assert sp548_plan.feature("chip_order").options[:3] == ("RGB", "RBG", "GRB")

    sp539 = catalog.resolve_name("SP539E")
    assert sp539 is not None
    sp539_plan = plan_for_model(sp539)
    assert not sp539_plan.has_feature("light_type")
    assert "Custom Solid - Firework" in sp539_plan.feature("effect").options
    assert "Custom Gradient - Spin" in sp539_plan.feature("effect").options
    assert "Custom Gradient" in sp539_plan.feature("light_mode").options
    assert sp539_plan.feature("chip_order").options[0] == "RGBW"

    sp631 = catalog.resolve_name("SP631E")
    assert sp631 is not None
    sp631_plan = plan_for_model(sp631)
    sp631_effects = sp631_plan.feature("effect").options
    assert len(sp631_effects) == 5
    assert sp631_effects[:2] == (
        "Static White - Solid",
        "Dynamic White - White Color Breath",
    )
    assert not sp631_plan.has_feature("light_type")
    assert sp631_plan.feature("light_mode").options == (
        "Static White",
        "Dynamic White",
        "Sound - White",
    )
    assert not sp631_plan.has_feature("chip_order")

    sp633 = catalog.resolve_name("SP633E")
    assert sp633 is not None
    sp633_effects = plan_for_model(sp633).feature("effect").options
    assert len(sp633_effects) == 19
    assert "Dynamic Color - Seven Color Jump" in sp633_effects
    assert "Sound - Color - Sound - Music Jump" in sp633_effects
    assert "Sound - Color - Sound - Party" not in sp633_effects

    sp638 = catalog.resolve_name("SP638E")
    assert sp638 is not None
    sp638_effects = plan_for_model(sp638).feature("effect").options
    assert len(sp638_effects) == 183
    assert sp638_effects[:4] == (
        "Static Color - Solid",
        "Dynamic Color - Rainbow",
        "Dynamic Color - Rainbow Metor",
        "Dynamic Color - Rainbow Comet",
    )
    assert "Sound - Color - Sound - Party" in sp638_effects
    sp638_plan = plan_for_model(sp638)
    assert sp638_plan.feature("light_mode").options == (
        "Static Color",
        "Dynamic Color",
        "Sound - Color",
        "Custom Solid",
    )
    assert sp638_plan.feature("chip_order").options == (
        "RGB",
        "RBG",
        "GRB",
        "GBR",
        "BRG",
        "BGR",
    )
    assert sp638_plan.feature("onoff_effect").options == (
        "Flow Forward",
        "Flow Backward",
        "Gradient",
        "Stars",
    )
    assert sp638_plan.feature("onoff_speed").options == ("Slow", "Medium", "Fast")
    assert sp638_plan.has_feature("effect_play")
    assert not sp638_plan.has_feature("coexistence")

    sp63be = catalog.resolve_name("SP63BE")
    assert sp63be is not None
    sp63be_effects = plan_for_model(sp63be).feature("effect").options
    assert len(sp63be_effects) == 188
    assert "Dynamic White - White Color Breath" in sp63be_effects
    assert "Sound - White - Sound - White Color Music Breath" in sp63be_effects
    assert plan_for_model(sp63be).has_feature("coexistence")

    sp637 = catalog.resolve_name("SP637E")
    assert sp637 is not None
    sp637_plan = plan_for_model(sp637)
    assert sp637_plan.feature("light_type").options == (
        "SPI - CCT1",
        "SPI - CCT2",
    )
    assert len(sp637_plan.feature("chip_order").options) == 6


def test_network_information_metadata_creates_diagnostic_sensors() -> None:
    """Models with network-info support expose a diagnostic sensor in the plan."""
    catalog = default_catalog()

    for name in {"SP802E", "SP547E", "SP548E"}:
        model = catalog.resolve_name(name)
        assert model is not None

        network_info = plan_for_model(model).feature("network_info")
        assert network_info.platform is PlatformKind.SENSOR
        assert network_info.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert network_info.implemented


def test_sp6xx_style_models_expose_custom_effect_slot_diagnostic() -> None:
    """Old-UniLED SP6xx custom/DIY slot status is diagnostic-only for now."""
    catalog = default_catalog()

    for name in {"SP630E", "SP530E"}:
        model = catalog.resolve_name(name)
        assert model is not None

        custom_slot = plan_for_model(model).feature("custom_effect_slot")

        assert custom_slot.platform is PlatformKind.SENSOR
        assert custom_slot.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert custom_slot.implemented

    sp601 = catalog.resolve_name("SP601E")
    assert sp601 is not None
    assert not plan_for_model(sp601).has_feature("custom_effect_slot")


def test_sp630e_surface_profile_creates_apk_diagnostics() -> None:
    """The APK /sp630e surface is tracked for SP6xx and custom 5xx models."""
    catalog = default_catalog()

    expected_surfaces = (
        "Power",
        "Brightness",
        "Static color",
        "Dynamic effects",
        "Sound effects",
        "DIY solid effects",
        "DIY gradient effects",
        "Favorite effects",
        "Favorite effect loop",
        "Timers",
        "Light type",
        "Color order",
        "Color correction",
        "Music matrix layout",
        "Music strip layout",
        "Audio source",
        "Sensitivity",
        "Network configuration",
        "Remote status",
        "Motor mode",
        "Power-on behavior",
        "Firmware/version",
        "Device rename",
    )
    expected_units = {
        "sp630e_route_count": "routes",
        "sp630e_control_surface_count": "surfaces",
        "sp630e_favorite_limit_hint_count": "hints",
        "sp630e_timer_limit": "slots",
        "sp630e_timer_hint_count": "hints",
        "sp630e_music_asset_count": "assets",
        "sp630e_network_hint_count": "hints",
        "sp630e_remote_hint_count": "hints",
        "sp630e_motor_hint_count": "hints",
        "sp630e_app_method_count": "methods",
        "sp630e_app_command_id_count": "ids",
        "sp630e_data_model_hint_count": "hints",
        "sp630e_native_lfx_hint_count": "hints",
        "sp630e_native_export_detail_count": "anchors",
        "sp630e_catalog_hint_count": "hints",
        "sp630e_protocol_gap_count": "gaps",
        "sp630e_apk_asset_evidence_count": "assets",
        "sp630e_apk_package_asset_count": "assets",
        "sp630e_apk_string_evidence_count": "strings",
    }

    for name in {"SP630E", "SP530E"}:
        model = catalog.resolve_name(name)
        assert model is not None
        plan = plan_for_model(model)

        assert plan.feature("sp630e_profile").implemented
        for key, unit in expected_units.items():
            diagnostic = plan.feature(key)
            assert diagnostic.platform is PlatformKind.SENSOR
            assert diagnostic.entity_category is EntityCategoryKind.DIAGNOSTIC
            assert diagnostic.implemented
            assert diagnostic.unit == unit

        surface = plan.feature("sp630e_control_surface")
        assert surface.options == expected_surfaces
        assert surface.implemented is False
        assert surface.enabled_by_default is False

    sp601 = catalog.resolve_name("SP601E")
    assert sp601 is not None
    assert not plan_for_model(sp601).has_feature("sp630e_profile")


def test_rg4_mesh_accessory_profile_creates_apk_diagnostics() -> None:
    """RG4 exposes APK accessories/provisioning evidence as diagnostics only."""
    catalog = default_catalog()
    rg4 = catalog.resolve_name("RG4")
    assert rg4 is not None
    plan = plan_for_model(rg4)

    expected_states = (
        "provisioningStart",
        "provisioningInvite",
        "provisioningPublicKey",
        "provisioningData",
        "provisioningConfirmation",
        "provisioningRandom",
        "provisioningInputComplete",
        "provisioningComplete",
        "provisioningFailed",
    )

    assert plan.feature("mesh_profile").implemented
    for key, unit in {
        "mesh_route_count": "routes",
        "mesh_provisioning_hint_count": "hints",
        "mesh_provisioning_state_count": "states",
        "mesh_sig_mesh_uuid_hint_count": "uuids",
        "mesh_app_command_id_count": "ids",
        "mesh_control_blocker_count": "blockers",
        "mesh_apk_asset_evidence_count": "assets",
        "mesh_apk_package_asset_count": "assets",
        "mesh_apk_string_evidence_count": "strings",
        "mesh_known_node_count": "nodes",
        "mesh_command_node_count": "nodes",
        "mesh_strip_node_count": "nodes",
        "mesh_bulb_node_count": "nodes",
        "mesh_panel_node_count": "nodes",
        "mesh_bridge_seen": None,
    }.items():
        diagnostic = plan.feature(key)
        assert diagnostic.platform is PlatformKind.SENSOR
        assert diagnostic.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert diagnostic.implemented
        assert diagnostic.unit == unit

    state = plan.feature("mesh_provisioning_state")
    assert state.options == expected_states
    assert state.implemented is False
    assert state.enabled_by_default is False

    scene_mesh = catalog.resolve_name("SP310E")
    assert scene_mesh is not None
    scene_plan = plan_for_model(scene_mesh)
    assert scene_plan.has_feature("mesh_profile")
    assert scene_plan.feature("mesh_route_count").unit == "routes"
    assert scene_plan.feature("mesh_provisioning_hint_count").unit == "hints"
    assert scene_plan.feature("mesh_sig_mesh_uuid_hint_count").unit == "uuids"
    assert scene_plan.feature("mesh_app_command_id_count").unit == "ids"
    assert scene_plan.feature("mesh_control_blocker_count").unit == "blockers"
    assert scene_plan.feature("mesh_apk_package_asset_count").unit == "assets"
    assert scene_plan.feature("mesh_apk_string_evidence_count").unit == "strings"
    assert not scene_plan.has_feature("mesh_known_node_count")
    assert not scene_plan.has_feature("mesh_provisioning_state")


def test_legacy_timer_models_expose_timer_count_diagnostic() -> None:
    """Old-UniLED timer-count bytes are diagnostic-only for legacy BLE."""
    catalog = default_catalog()

    for name in {"SP601E", "SP602E", "SP611E"}:
        model = catalog.resolve_name(name)
        assert model is not None

        timer_count = plan_for_model(model).feature("timer_count")

        assert timer_count.platform is PlatformKind.SENSOR
        assert timer_count.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert timer_count.implemented

    sp613 = catalog.resolve_name("SP613E")
    assert sp613 is not None
    assert not plan_for_model(sp613).has_feature("timer_count")


def test_banlanx3_models_expose_diy_status_diagnostics() -> None:
    """Old-UniLED BanlanX3 DIY status metadata is diagnostic-only for now."""
    catalog = default_catalog()

    sp614 = catalog.resolve_name("SP614E")
    assert sp614 is not None
    sp614_plan = plan_for_model(sp614)

    for key in ("diy_effect_type", "diy_color_count"):
        feature = sp614_plan.feature(key)

        assert feature.platform is PlatformKind.SENSOR
        assert feature.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert feature.implemented

    sp617 = catalog.resolve_name("SP617E")
    assert sp617 is not None
    sp617_plan = plan_for_model(sp617)

    assert not sp617_plan.has_feature("diy_effect_type")
    assert not sp617_plan.has_feature("diy_color_count")


def test_refresh_button_is_limited_to_refresh_capable_families() -> None:
    """Refresh buttons are planned only where a runtime refresh path exists."""
    catalog = default_catalog()

    for name in {"SP601E", "SP630E", "SP530E", "RG4"}:
        model = catalog.resolve_name(name)
        assert model is not None
        refresh = plan_for_model(model).feature("refresh")

        assert refresh.platform is PlatformKind.BUTTON
        assert refresh.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert refresh.implemented

    for name in {"SP801E", "FT001", "SP701E", "SP660E"}:
        model = catalog.resolve_name(name)
        assert model is not None
        assert not plan_for_model(model).has_feature("refresh")


def test_network_family_uses_apk_profile_evidence() -> None:
    """SP801E/SP802E plans expose APK profile surfaces without commands."""
    catalog = default_catalog()

    sp801 = catalog.resolve_name("SP801E")
    assert sp801 is not None
    sp801_plan = plan_for_model(sp801)

    profile = sp801_plan.feature("network_profile")
    assert profile.platform is PlatformKind.SENSOR
    assert profile.entity_category is EntityCategoryKind.DIAGNOSTIC
    assert profile.implemented
    for key, unit in {
        "network_surface_count": "surfaces",
        "network_content_mode_count": "modes",
        "network_artnet_field_count": "fields",
        "network_port_field_count": "fields",
        "network_playlist_action_count": "actions",
        "network_matrix_music_control_count": "controls",
        "network_lfx_effect_count": "effects",
        "network_lfx_gif_count": "previews",
        "network_route_count": "routes",
        "network_regular_lfx_effect_asset_count": "assets",
        "network_lfx_gif_asset_count": "assets",
        "network_app_method_count": "methods",
        "network_app_command_id_count": "ids",
        "network_workflow_hint_count": "workflows",
        "network_raw_string_hint_count": "strings",
        "network_import_constraint_count": "constraints",
        "network_catalog_hint_count": "hints",
        "network_transport_hint_count": "hints",
        "network_native_library_hint_count": "hints",
        "network_native_frame_hint_count": "hints",
        "network_native_lfx_param_hint_count": "hints",
        "network_native_effect_generator_hint_count": "generators",
        "network_native_matrix_mode_hint_count": "hints",
        "network_native_pixel_helper_hint_count": "helpers",
        "network_native_export_hint_count": "hints",
        "network_native_export_detail_count": "anchors",
        "network_protocol_gap_count": "gaps",
        "network_command_blocker_count": "blockers",
        "network_apk_asset_evidence_count": "assets",
        "network_apk_package_asset_count": "assets",
        "network_apk_string_evidence_count": "strings",
    }.items():
        diagnostic = sp801_plan.feature(key)
        assert diagnostic.platform is PlatformKind.SENSOR
        assert diagnostic.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert diagnostic.implemented
        assert diagnostic.unit == unit
    assert sp801_plan.feature("network_surface").options == (
        "Art-Net settings",
        "Port configuration",
        "LED layout",
        "Scene list",
        "Playlist",
        "Color correction",
        "Brightness",
        "Speed",
        "Graffiti canvas",
        "DXF import",
        "Firmware update",
    )
    assert sp801_plan.feature("network_content_mode").options == (
        "Regular effect",
        "Image",
        "GIF",
        "Graffiti",
        "Music",
        "Text",
        "Video",
    )
    assert sp801_plan.feature("network_artnet_field").options == (
        "portActions",
        "portUniverseCounts",
        "protocolVersion",
        "startUniverse",
    )
    assert sp801_plan.feature("network_port_field").options == (
        "channel_index",
        "sp_channel_group",
        "portDriverType",
        "portId",
        "portNo",
        "port_id",
    )
    assert sp801_plan.feature("network_playlist_action").options == (
        "getPlaylistList",
        "addPlaylist",
        "updatePlaylist",
        "removePlaylist",
    )
    assert not sp801_plan.has_feature("network_matrix_music_control")
    assert not sp801_plan.has_feature("network_lfx_effect")
    assert sp801_plan.feature("identify").implemented is False

    sp802 = catalog.resolve_name("SP802E")
    assert sp802 is not None
    sp802_plan = plan_for_model(sp802)

    assert sp802_plan.feature("network_surface").options == (
        "LFX effects",
        "Material library",
        "Favorites",
        "GIF LFX",
        "Image LFX",
        "Text LFX",
        "Graffiti LFX",
        "Rhythm LFX",
        "Animation LFX",
        "LED panel layout",
        "DIY gradient",
        "Color editing",
    )
    assert sp802_plan.feature("network_content_mode").options == (
        "Regular LFX",
        "Animation LFX",
        "GIF LFX",
        "Graffiti LFX",
        "Image LFX",
        "Text LFX",
        "Rhythm LFX",
    )
    assert sp802_plan.feature("network_matrix_music_control").options == (
        "setMatrixMusicMode",
        "setMatrixMusicDotColor",
        "setMatrixMusicColColor",
        "setMatrixMusicColColorType",
        "setMatrixMusicColGradientColor",
    )
    assert not sp802_plan.has_feature("network_artnet_field")
    assert not sp802_plan.has_feature("network_port_field")
    assert not sp802_plan.has_feature("network_playlist_action")
    assert sp802_plan.feature("network_lfx_effect").options == (
        "Black hole",
        "Bursts",
        "Circle fade",
        "Diagonal fade",
        "Diamond fade",
        "GEQ",
        "Hiphotic",
        "Horizontal DNA",
        "Horizontal fade",
        "Hyper fade",
        "Matrix",
        "Metaballs",
        "Palette",
        "Party",
        "Plasmaball",
        "Soap",
        "Squared swirl",
        "Static",
        "Vertical DNA",
        "Waverly",
    )
    assert sp802_plan.feature("network_lfx_effect").implemented is False
    assert sp802_plan.feature("identify").enabled_by_default is False


def test_scene_families_get_scene_plans() -> None:
    """Scene UI families produce both scene selection and saved-scene plans."""
    catalog = default_catalog()
    expected_presets = (
        "Christmas",
        "Dynamic bar",
        "Eaves",
        "Esports 181",
        "Living room",
    )
    expected_surfaces = (
        "Scene selection",
        "Favorites",
        "Timers",
        "Pixel count",
        "Color settings",
        "White brightness",
        "DIY gradient",
        "DIY solid",
        "Music input",
        "Inner microphone",
        "Phone microphone",
        "PC mode",
        "Speed",
        "Sensitivity",
    )

    for name in {"SP660E", "SP310E", "DynamicBar"}:
        model = catalog.resolve_name(name)
        assert model is not None
        plan = plan_for_model(model)

        assert model.family in {
            ProtocolFamily.BANLANX_SCENE_UI,
            ProtocolFamily.BANLANX_SCENE_MESH,
        }
        profile = plan.feature("scene_profile")
        assert profile.platform is PlatformKind.SENSOR
        assert profile.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert profile.implemented

        for key, unit in {
            "scene_preset_count": "presets",
            "scene_control_surface_count": "surfaces",
            "scene_route_count": "routes",
            "scene_mode_icon_count": "icons",
            "scene_mode_effect_count": "effects",
            "scene_mode_icon_sample_count": "samples",
            "scene_lfx_route_count": "routes",
            "scene_timer_route_count": "routes",
            "scene_app_method_count": "methods",
            "scene_app_command_id_count": "ids",
            "scene_storage_hint_count": "hints",
            "scene_recent_action_count": "actions",
            "scene_favorite_action_count": "actions",
            "scene_timer_action_count": "actions",
            "scene_diy_action_count": "actions",
            "scene_white_brightness_anchor_count": "anchors",
            "scene_raw_string_hint_count": "strings",
            "scene_lfx_data_model_hint_count": "hints",
            "scene_lfx_frame_field_hint_count": "fields",
            "scene_native_handler_count": "handlers",
            "scene_native_paired_api_count": "capabilities",
            "scene_native_ic_only_api_count": "capabilities",
            "scene_native_loop_handler_count": "handlers",
            "scene_native_library_hint_count": "hints",
            "scene_native_frame_hint_count": "helpers",
            "scene_native_opcode_hint_count": "helpers",
            "scene_native_state_hint_count": "helpers",
            "scene_native_state_export_count": "helpers",
            "scene_native_color_order_hint_count": "hints",
            "scene_native_pwm_table_hint_count": "tables",
            "scene_native_music_effect_hint_count": "effects",
            "scene_native_pwm_driver_hint_count": "helpers",
            "scene_native_animation_export_count": "exports",
            "scene_native_drive_export_count": "exports",
            "scene_native_persistence_handler_count": "handlers",
            "scene_native_persistence_export_count": "exports",
            "scene_native_persistence_capability_count": "capabilities",
            "scene_native_export_hint_count": "hints",
            "scene_native_code_anchor_count": "anchors",
            "scene_setup_requirement_count": "requirements",
            "scene_catalog_hint_count": "hints",
            "scene_transport_hint_count": "hints",
            "scene_protocol_gap_count": "gaps",
            "scene_command_blocker_count": "blockers",
            "scene_apk_asset_evidence_count": "assets",
            "scene_apk_package_asset_count": "assets",
            "scene_apk_string_evidence_count": "strings",
        }.items():
            diagnostic = plan.feature(key)
            assert diagnostic.platform is PlatformKind.SENSOR
            assert diagnostic.entity_category is EntityCategoryKind.DIAGNOSTIC
            assert diagnostic.implemented
            assert diagnostic.unit == unit

        assert plan.has_feature("scene_slot")
        preset = plan.feature("scene_preset")
        assert preset.options == expected_presets
        assert preset.implemented is False
        assert preset.enabled_by_default is False

        mode_effect = plan.feature("scene_mode_effect")
        assert len(mode_effect.options) == SCENE_MODE_ICON_COUNT
        assert mode_effect.options == SCENE_MODE_EFFECTS
        assert mode_effect.options[:3] == (
            "Bouncing Ball",
            "Breath",
            "Color Twinkles",
        )
        assert mode_effect.options[-3:] == (
            "White Static",
            "White Strobe",
            "White Wave",
        )
        assert mode_effect.implemented is False
        assert mode_effect.enabled_by_default is False

        surface = plan.feature("scene_surface")
        assert surface.options == expected_surfaces
        assert surface.implemented is False
        assert surface.enabled_by_default is False

        recent_action = plan.feature("scene_recent_action")
        assert recent_action.options == (
            "addRecScene",
            "getRecSceneList",
            "removeRecScene",
        )
        assert recent_action.implemented is False
        assert recent_action.enabled_by_default is False

        favorite_action = plan.feature("scene_favorite_action")
        assert favorite_action.options == (
            "saveFavoriteEffectList",
            "updateFavoriteLfxList",
        )
        assert favorite_action.implemented is False
        assert favorite_action.enabled_by_default is False

        timer_action = plan.feature("scene_timer_action")
        assert timer_action.options == ("saveTimingTask", "removeTimingTask")
        assert timer_action.implemented is False
        assert timer_action.enabled_by_default is False

        diy_action = plan.feature("scene_diy_action")
        assert diy_action.options == ("saveDiyLfx", "resetLfx")
        assert diy_action.implemented is False
        assert diy_action.enabled_by_default is False

        white_brightness = plan.feature("scene_white_brightness_anchor")
        assert white_brightness.options == (
            "raw-brightness-",
            "whiteBrightness",
            "white_brightness",
            "setWhiteLightCoexistWithRGB",
        )
        assert white_brightness.implemented is False
        assert white_brightness.enabled_by_default is False
        assert plan.has_feature("saved_scene")


def test_car_light_family_uses_apk_profile_evidence() -> None:
    """Car-light plans expose APK zones/triggers without enabling commands."""
    catalog = default_catalog()
    expected_zones = (
        "Car lights",
        "Chassis lights",
        "Console lights",
        "Door lights",
        "Footsocket lights",
        "Storage lights",
        "Welcome lights",
        "Wheel lights",
    )
    expected_triggers = (
        "Brake light",
        "Brake light blink",
        "Brake light blink new",
        "Fade car light",
        "Flow car light",
        "Left turn signal flow",
        "Right turn signal flow",
        "Turn signal blink",
        "Turn signal blink new",
    )
    expected_surfaces = (
        "Setup",
        "Zone selection",
        "Trigger settings",
        "Color correction",
        "Subdevices management",
        "Device password",
        "Password reset",
        "Settings",
    )

    for name in {"Car Lights", "SP701E", "SP702E", "SP-MIC"}:
        model = catalog.resolve_name(name)
        assert model is not None

        plan = plan_for_model(model)

        profile = plan.feature("car_light_profile")
        assert profile.platform is PlatformKind.SENSOR
        assert profile.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert profile.implemented

        role = plan.feature("accessory_role")
        assert role.platform is PlatformKind.SENSOR
        assert role.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert role.implemented

        required_controller = plan.feature("car_light_required_controller")
        assert required_controller.platform is PlatformKind.SENSOR
        assert required_controller.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert required_controller.implemented

        setup_stage = plan.feature("car_light_setup_stage")
        assert setup_stage.platform is PlatformKind.SENSOR
        assert setup_stage.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert setup_stage.implemented

        setup_order = plan.feature("car_light_setup_order")
        assert setup_order.platform is PlatformKind.SENSOR
        assert setup_order.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert setup_order.implemented

        setup_dependency = plan.feature("car_light_setup_dependency")
        assert setup_dependency.platform is PlatformKind.SENSOR
        assert setup_dependency.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert setup_dependency.implemented

        zone_count = plan.feature("car_light_zone_count")
        assert zone_count.platform is PlatformKind.SENSOR
        assert zone_count.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert zone_count.implemented
        assert zone_count.unit == "zones"

        trigger_count = plan.feature("car_light_trigger_count")
        assert trigger_count.platform is PlatformKind.SENSOR
        assert trigger_count.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert trigger_count.implemented
        assert trigger_count.unit == "triggers"

        for key, unit in {
            "car_light_accessory_asset_count": "assets",
            "car_light_animation_asset_count": "assets",
            "car_light_trigger_image_asset_count": "assets",
            "car_light_zone_image_asset_count": "assets",
            "car_light_control_surface_count": "surfaces",
            "car_light_subdevice_hint_count": "hints",
            "car_light_subdevice_filter_count": "filters",
            "car_light_password_hint_count": "hints",
            "car_light_password_flow_state_count": "states",
            "car_light_password_entry_hint_count": "hints",
            "car_light_password_policy_hint_count": "hints",
            "car_light_password_reset_hint_count": "hints",
            "car_light_trigger_storage_hint_count": "hints",
            "car_light_trigger_action_count": "actions",
            "car_light_route_count": "routes",
            "car_light_setup_requirement_count": "requirements",
            "car_light_setup_flow_hint_count": "hints",
            "car_light_setup_key_hint_count": "hints",
            "car_light_app_command_id_count": "ids",
            "car_light_setup_dependency_count": "dependencies",
            "car_light_required_setup_dependency_count": "dependencies",
            "car_light_ordered_setup_model_count": "models",
            "car_light_model_role_hint_count": "hints",
            "car_light_protocol_gap_count": "gaps",
            "car_light_command_blocker_count": "blockers",
            "car_light_apk_asset_evidence_count": "assets",
            "car_light_apk_package_asset_count": "assets",
            "car_light_apk_string_evidence_count": "strings",
        }.items():
            diagnostic = plan.feature(key)
            assert diagnostic.platform is PlatformKind.SENSOR
            assert diagnostic.entity_category is EntityCategoryKind.DIAGNOSTIC
            assert diagnostic.implemented
            assert diagnostic.unit == unit

        zone = plan.feature("car_light_zone")
        assert zone.options == expected_zones
        assert zone.implemented is False
        assert zone.enabled_by_default is False

        trigger = plan.feature("car_light_trigger")
        assert trigger.options == expected_triggers
        assert trigger.implemented is False
        assert trigger.enabled_by_default is False

        surface = plan.feature("car_light_control_surface")
        assert surface.options == expected_surfaces
        assert surface.implemented is False
        assert surface.enabled_by_default is False

        subdevice_filter = plan.feature("car_light_subdevice_filter")
        assert subdevice_filter.options == (
            "include_added_subdevices",
            "exclude_slave_devices",
        )
        assert subdevice_filter.implemented is False
        assert subdevice_filter.enabled_by_default is False

        password_flow_state = plan.feature("car_light_password_flow_state")
        assert password_flow_state.options == (
            "Set your password",
            "Setup password successfully",
            "Turn on password",
            "Turn off password",
            "Wait for the device password reset...",
            "The password reset timed out. Please try again!",
        )
        assert password_flow_state.implemented is False
        assert password_flow_state.enabled_by_default is False

        trigger_action = plan.feature("car_light_trigger_action")
        assert trigger_action.options == (
            "Set the lighting effect when the corresponding trigger signal is received",
            "Rename trigger",
        )
        assert trigger_action.implemented is False
        assert trigger_action.enabled_by_default is False


def test_fish_tank_family_uses_apk_profile_evidence() -> None:
    """FT001 plans expose APK profile surfaces without enabling commands."""
    catalog = default_catalog()
    model = catalog.resolve_name("FT001")
    assert model is not None

    plan = plan_for_model(model)

    profile = plan.feature("fish_tank_profile")
    assert profile.platform is PlatformKind.SENSOR
    assert profile.entity_category is EntityCategoryKind.DIAGNOSTIC
    assert profile.implemented

    favorite_count = plan.feature("fish_tank_favorite_slot_count")
    assert favorite_count.platform is PlatformKind.SENSOR
    assert favorite_count.entity_category is EntityCategoryKind.DIAGNOSTIC
    assert favorite_count.implemented
    assert favorite_count.unit == "slots"

    timer_limit = plan.feature("fish_tank_timer_limit")
    assert timer_limit.platform is PlatformKind.SENSOR
    assert timer_limit.entity_category is EntityCategoryKind.DIAGNOSTIC
    assert timer_limit.implemented
    assert timer_limit.unit == "slots"

    for key, unit in {
        "fish_tank_light_channel_count": "channels",
        "fish_tank_control_surface_count": "surfaces",
        "fish_tank_route_count": "routes",
        "fish_tank_effect_hint_count": "effects",
        "fish_tank_effect_string_hint_count": "strings",
        "fish_tank_icon_asset_count": "assets",
        "fish_tank_image_asset_count": "assets",
        "fish_tank_channel_asset_count": "assets",
        "fish_tank_timer_asset_count": "assets",
        "fish_tank_favorite_asset_count": "assets",
        "fish_tank_effect_asset_count": "assets",
        "fish_tank_workflow_hint_count": "workflows",
        "fish_tank_favorite_action_count": "actions",
        "fish_tank_favorite_store_hint_count": "hints",
        "fish_tank_favorite_recall_hint_count": "hints",
        "fish_tank_favorite_clear_hint_count": "hints",
        "fish_tank_favorite_action_type_count": "actions",
        "fish_tank_favorite_loop_hint_count": "hints",
        "fish_tank_favorite_loop_action_count": "actions",
        "fish_tank_firmware_prompt_hint_count": "hints",
        "fish_tank_timer_slot_count": "slots",
        "fish_tank_timer_action_count": "actions",
        "fish_tank_timer_hint_count": "hints",
        "fish_tank_timer_string_hint_count": "strings",
        "fish_tank_app_method_count": "methods",
        "fish_tank_app_command_id_count": "ids",
        "fish_tank_data_model_hint_count": "hints",
        "fish_tank_raw_string_hint_count": "strings",
        "fish_tank_brightness_string_hint_count": "strings",
        "fish_tank_protocol_gap_count": "gaps",
        "fish_tank_command_blocker_count": "blockers",
        "fish_tank_apk_asset_evidence_count": "assets",
        "fish_tank_apk_package_asset_count": "assets",
        "fish_tank_apk_string_evidence_count": "strings",
    }.items():
        diagnostic = plan.feature(key)
        assert diagnostic.platform is PlatformKind.SENSOR
        assert diagnostic.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert diagnostic.implemented
        assert diagnostic.unit == unit

    channel = plan.feature("fish_tank_light_channel")
    assert channel.options == ("First light", "Second light")
    assert channel.implemented is False
    assert channel.enabled_by_default is False

    surface = plan.feature("fish_tank_control_surface")
    assert surface.options == (
        "Color palette",
        "Color correction",
        "Brightness",
        "Speed",
        "Windmill",
        "Timer",
        "Favorite effects",
        "Settings",
        "Device rename",
        "Network configuration",
    )
    assert surface.implemented is False
    assert surface.enabled_by_default is False

    effect = plan.feature("fish_tank_effect")
    assert effect.options == ("Windmill", "springwater")
    assert effect.implemented is False
    assert effect.enabled_by_default is False

    favorite = plan.feature("fish_tank_favorite_slot")
    assert favorite.options == ("Favorite 1", "Favorite 2", "Favorite 3", "Favorite 4")
    assert favorite.implemented is False
    assert favorite.enabled_by_default is False

    favorite_action = plan.feature("fish_tank_favorite_action")
    assert favorite_action.options == (
        "Store favorite",
        "Recall favorite",
        "Clear favorite",
    )
    assert favorite_action.implemented is False
    assert favorite_action.enabled_by_default is False

    favorite_loop_action = plan.feature("fish_tank_favorite_loop_action")
    assert favorite_loop_action.options == (
        "Loop all favorite effects",
        "Stop looping the favorite effects",
    )
    assert favorite_loop_action.implemented is False
    assert favorite_loop_action.enabled_by_default is False

    timer = plan.feature("fish_tank_timer_slot")
    assert timer.options == ("Timer 1", "Timer 2", "Timer 3", "Timer 4", "Timer 5")
    assert timer.implemented is False
    assert timer.enabled_by_default is False

    timer_action = plan.feature("fish_tank_timer_action")
    assert timer_action.options == ("Save timer", "Remove timer")
    assert timer_action.implemented is False
    assert timer_action.enabled_by_default is False


def test_cloud_optional_models_get_cloud_profile_diagnostics() -> None:
    """Optional-cloud catalog models expose profile facts without commands."""
    catalog = default_catalog()
    cloud_models = [
        model
        for model in catalog.user_facing_models()
        if TransportKind.CLOUD_OPTIONAL in model.transports
    ]

    assert len(cloud_models) == 39

    for model in cloud_models:
        plan = plan_for_model(model)
        profile = plan.feature("cloud_profile")

        assert profile.platform is PlatformKind.SENSOR
        assert profile.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert profile.implemented
        for key, unit in {
            "cloud_base_url_count": "hosts",
            "cloud_endpoint_count": "endpoints",
            "cloud_endpoint_inventory_count": "endpoints",
            "cloud_endpoint_group_count": "groups",
            "cloud_command_related_endpoint_count": "endpoints",
            "cloud_unresolved_base_url_endpoint_count": "endpoints",
            "cloud_unproven_auth_endpoint_count": "endpoints",
            "cloud_auth_endpoint_count": "endpoints",
            "cloud_account_auth_endpoint_count": "endpoints",
            "cloud_device_endpoint_count": "endpoints",
            "cloud_home_device_endpoint_count": "endpoints",
            "cloud_user_device_endpoint_count": "endpoints",
            "cloud_local_device_endpoint_count": "endpoints",
            "cloud_btmesh_endpoint_count": "endpoints",
            "cloud_root_device_endpoint_count": "endpoints",
            "cloud_raw_command_endpoint_count": "endpoints",
            "cloud_content_endpoint_count": "endpoints",
            "cloud_voice_endpoint_count": "endpoints",
            "cloud_document_url_count": "urls",
            "cloud_auth_token_hint_count": "hints",
            "cloud_device_identity_hint_count": "hints",
            "cloud_http_header_hint_count": "hints",
            "cloud_signature_hint_count": "hints",
            "cloud_request_contract_hint_count": "hints",
            "cloud_token_contract_hint_count": "hints",
            "cloud_header_contract_hint_count": "hints",
            "cloud_signature_contract_hint_count": "hints",
            "cloud_transport_hint_count": "hints",
            "cloud_protocol_gap_count": "gaps",
            "cloud_command_blocker_count": "blockers",
            "cloud_raw_command_endpoint": None,
        }.items():
            diagnostic = plan.feature(key)
            assert diagnostic.platform is PlatformKind.SENSOR
            assert diagnostic.entity_category is EntityCategoryKind.DIAGNOSTIC
            assert diagnostic.implemented
            assert diagnostic.unit == unit

    model = catalog.resolve_name("SP630E")
    assert model is not None
    assert not plan_for_model(model).has_feature("cloud_profile")


def test_legacy_uniled_parity_models_are_marked_in_plans() -> None:
    """Old UniLED parity candidates are visible to tests and diagnostics."""
    catalog = default_catalog()

    for name in {"SP601E", "SP630E", "SP65CE"}:
        model = catalog.resolve_name(name)
        assert model is not None
        plan = plan_for_model(model)

        parity = plan.feature("legacy_uniled_parity")
        assert parity.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert parity.implementation_hint == "legacy_uniled"
        for key, unit in {
            "legacy_uniled_parity_profile": None,
            "legacy_uniled_command_count": "commands",
            "legacy_uniled_status_parser_count": "parsers",
            "legacy_uniled_stubbed_command_count": "stubs",
            "legacy_uniled_parity_gap_count": "gaps",
        }.items():
            diagnostic = plan.feature(key)
            assert diagnostic.entity_category is EntityCategoryKind.DIAGNOSTIC
            assert diagnostic.implementation_hint == "legacy_uniled"
            assert diagnostic.unit == unit
        assert plan.feature("main_light").implementation_hint == "legacy_uniled"

    model = catalog.resolve_name("SP530E")
    assert model is not None
    assert not plan_for_model(model).has_feature("legacy_uniled_parity")
    assert not plan_for_model(model).has_feature("legacy_uniled_parity_profile")


def test_protocol_evidence_models_are_marked_in_plans() -> None:
    """Command-backed models expose the evidence tier behind the protocol."""
    catalog = default_catalog()

    for name in {"SP601E", "SP530E", "SP603E"}:
        model = catalog.resolve_name(name)
        assert model is not None
        plan = plan_for_model(model)

        for key, unit in {
            "protocol_evidence_profile": None,
            "protocol_evidence_kind": None,
            "protocol_evidence_hint_count": "hints",
        }.items():
            diagnostic = plan.feature(key)
            assert diagnostic.platform is PlatformKind.SENSOR
            assert diagnostic.entity_category is EntityCategoryKind.DIAGNOSTIC
            assert diagnostic.implemented
            assert diagnostic.implementation_hint == "protocol_evidence"
            assert diagnostic.unit == unit

    model = catalog.resolve_name("SP660E")
    assert model is not None
    assert not plan_for_model(model).has_feature("protocol_evidence_profile")
