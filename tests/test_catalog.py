"""Catalog coverage tests."""

from __future__ import annotations

import json
from fnmatch import fnmatchcase
from pathlib import Path

from custom_components.uniled.core import (
    COLOR_CAPABILITY_LABELS,
    SPEC_FUNCTION_BITS,
    ProtocolFamily,
    SupportLevel,
    TransportKind,
    default_catalog,
)


def test_catalog_counts() -> None:
    """The bundled catalog represents every known record and user-facing name."""
    catalog = default_catalog()

    assert len(catalog.models) == 191
    assert len(catalog.unique_names) == 153
    assert len(catalog.user_facing_names) == 152
    assert len(catalog.user_facing_labels) == 153
    assert catalog.filtered_models()[0].name == "TEST"


def test_every_user_facing_name_resolves_to_a_supported_disposition() -> None:
    """Every user-facing model has a family, transport, and support level."""
    catalog = default_catalog()

    for name in catalog.user_facing_names:
        model = catalog.resolve_name(name)

        assert model is not None, name
        assert model.support_level is not SupportLevel.FILTERED, name
        assert model.support_level in {
            SupportLevel.FULL,
            SupportLevel.LIMITED,
            SupportLevel.RECOGNIZED,
        }, name
        assert model.family not in {
            ProtocolFamily.PLACEHOLDER,
            ProtocolFamily.UNKNOWN,
        }, name
        assert model.transports, name


def test_duplicate_catalog_names_keep_deterministic_variants() -> None:
    """APK records with duplicate names keep variants behind one canonical name."""
    catalog = default_catalog()

    sp665e_variants = catalog.models_for_name("SP665E")

    assert [model.model_id for model in sp665e_variants] == [126, 260]
    assert catalog.resolve_name("SP665E") is sp665e_variants[0]
    assert sp665e_variants[0].parent_id == 121
    assert sp665e_variants[1].parent_id == 126
    assert sp665e_variants[0].spec_functions == 87
    assert sp665e_variants[1].spec_functions == 85
    assert catalog.resolve_model("SP665E", model_id=126) is sp665e_variants[0]
    assert catalog.resolve_model("SP665E", model_id=260) is sp665e_variants[1]
    assert catalog.resolve_model("SP665E", model_id=99) is None

    sp548e_variants = catalog.models_for_name("SP548E")

    assert [model.model_id for model in sp548e_variants] == [99, 105, 147, 148]
    assert catalog.resolve_name("SP548E") is sp548e_variants[0]
    assert catalog.resolve_model("SP548E", model_id=148) is sp548e_variants[3]
    assert sp548e_variants[0].features["supportGetNetInfo"] == 37
    assert {model.color_cap for model in sp548e_variants} == {1, 4}


def test_catalog_resolves_friendly_labels_without_changing_names() -> None:
    """Friendly labels can identify models while canonical names stay stable."""
    catalog = default_catalog()
    fish_label = "\u9c7c\u7f38\u706f"

    fish = catalog.resolve_name("FT001")

    assert fish is not None
    assert catalog.models_for_name(fish_label) == ()
    assert catalog.resolve_label(fish_label) is fish
    assert catalog.resolve_model_label(fish_label, model_id=150) is fish
    assert catalog.resolve_model_label(fish_label, model_id=151) is None
    assert fish_label in catalog.user_facing_labels
    assert fish_label not in catalog.user_facing_names


def test_family_resolution_for_representative_models() -> None:
    """Representative names resolve to the expected implementation families."""
    catalog = default_catalog()

    expected = {
        "SP601E": ProtocolFamily.BANLANX_601,
        "SP602E": ProtocolFamily.BANLANX_60X,
        "SP603E": ProtocolFamily.BANLANX_V3,
        "SP613E": ProtocolFamily.BANLANX_V3,
        "SP630E": ProtocolFamily.BANLANX_6XX,
        "SP530E": ProtocolFamily.BANLANX_CUSTOM_5XX,
        "SP660E": ProtocolFamily.BANLANX_SCENE_UI,
        "SP310E": ProtocolFamily.BANLANX_SCENE_MESH,
        "SP701E": ProtocolFamily.BANLANX_CAR_LIGHTS,
        "SP801E": ProtocolFamily.BANLANX_NETWORK,
        "SP802E": ProtocolFamily.BANLANX_NETWORK,
        "FT001": ProtocolFamily.FISH_TANK,
        "SP107E": ProtocolFamily.LEGACY_LED_CHORD,
        "SP110E": ProtocolFamily.LEGACY_LED_HUE,
        "RG4": ProtocolFamily.ZENGGE_MESH,
    }

    for name, family in expected.items():
        model = catalog.resolve_name(name)

        assert model is not None, name
        assert model.family is family


def test_transport_resolution_for_representative_models() -> None:
    """Representative names resolve to expected transport families."""
    catalog = default_catalog()

    expected = {
        "SP601E": (TransportKind.BLE,),
        "SP530E": (
            TransportKind.BLE,
            TransportKind.LAN,
            TransportKind.CLOUD_OPTIONAL,
        ),
        "SP310E": (TransportKind.BLE_MESH,),
        "SP701E": (TransportKind.BLE,),
        "SP801E": (TransportKind.LAN,),
        "SP802E": (TransportKind.BLE, TransportKind.LAN),
        "SP107E": (TransportKind.BLE,),
        "SP110E": (TransportKind.BLE,),
        "FT001": (
            TransportKind.BLE,
            TransportKind.LAN,
            TransportKind.CLOUD_OPTIONAL,
        ),
        "RG4": (TransportKind.BLE_MESH,),
    }

    for name, transports in expected.items():
        model = catalog.resolve_name(name)

        assert model is not None, name
        assert model.transports == transports


def test_connect_caps_decode_to_catalog_transports() -> None:
    """The APK connectCaps bitmask decodes to the generated transport labels."""
    catalog = default_catalog()

    expected = {
        "SP601E": ("ble",),
        "SP530E": ("ble", "lan", "cloud_optional"),
        "SP310E": ("ble_mesh",),
        "SP801E": ("lan",),
        "SP802E": ("ble", "lan"),
    }

    for name, capabilities in expected.items():
        model = catalog.resolve_name(name)

        assert model is not None, name
        assert model.connect_capabilities == capabilities

    for model in catalog.user_facing_models():
        assert model.connect_capabilities == tuple(
            transport.value for transport in model.transports
        ), model.name

    test_model = catalog.filtered_models()[0]
    assert test_model.name == "TEST"
    assert test_model.connect_capabilities == ("ble", "cloud_optional")


def test_catalog_spec_and_color_cap_decoders_cover_apk_values() -> None:
    """Decoded specFunctions/colorCap labels preserve every observed APK value."""
    catalog = default_catalog()

    expected = {
        "SP601E": {
            "spec": ("feature_0x01", "feature_0x10"),
            "color": ("rgb",),
        },
        "SP611E": {
            "spec": (
                "feature_0x01",
                "audio_controls",
                "feature_0x04",
                "feature_0x10",
                "feature_0x40",
            ),
            "color": ("rgb",),
        },
        "SP614E": {
            "spec": (
                "feature_0x01",
                "audio_controls",
                "feature_0x04",
                "feature_0x08",
                "feature_0x10",
                "feature_0x40",
            ),
            "color": ("rgb",),
        },
        "SP630E": {
            "spec": (
                "feature_0x01",
                "audio_controls",
                "feature_0x04",
                "feature_0x10",
                "feature_0x40",
            ),
            "color": ("addressable_rgb",),
        },
        "FT001": {
            "spec": ("feature_0x01", "feature_0x10", "feature_0x80"),
            "color": ("rgb",),
        },
    }

    for name, values in expected.items():
        model = catalog.resolve_name(name)

        assert model is not None, name
        assert model.spec_function_bits == values["spec"]
        assert model.color_capabilities == values["color"]

    bit_by_label = {label: bit for bit, label in SPEC_FUNCTION_BITS}
    for model in catalog.models:
        decoded = 0
        for label in model.spec_function_bits:
            decoded |= bit_by_label[label]
        assert decoded == model.spec_functions, model.name
        assert model.color_cap in COLOR_CAPABILITY_LABELS, model.name


def test_catalog_feature_keys_cover_current_apk_extra_metadata() -> None:
    """Current APK extra-feature metadata is preserved as stable sorted keys."""
    catalog = default_catalog()
    feature_keys = {
        key
        for model in catalog.models
        for key in model.feature_keys
    }

    assert feature_keys == {
        "customFeature",
        "features",
        "maxDataLength",
        "maxPixelChannels",
        "musicFeature",
        "otherFeature",
        "settingFeature",
        "supportGetNetInfo",
    }
    assert catalog.resolve_name("SP601E").feature_keys == ()
    assert catalog.resolve_name("SP530E").feature_keys == (
        "customFeature",
        "maxPixelChannels",
        "musicFeature",
        "otherFeature",
        "settingFeature",
    )
    assert catalog.resolve_name("SP548E").feature_keys == (
        "customFeature",
        "maxDataLength",
        "maxPixelChannels",
        "otherFeature",
        "supportGetNetInfo",
    )
    assert catalog.resolve_name("SP660E").feature_keys == (
        "features",
        "maxPixelChannels",
    )


def test_protocol_backed_families_are_limited_support() -> None:
    """Families with command, parser, BLE-profile, and entity tests are limited."""
    catalog = default_catalog()
    limited_families = {
        ProtocolFamily.BANLANX_601,
        ProtocolFamily.BANLANX_60X,
        ProtocolFamily.BANLANX_V2,
        ProtocolFamily.BANLANX_V3,
        ProtocolFamily.BANLANX_6XX,
        ProtocolFamily.BANLANX_CUSTOM_5XX,
        ProtocolFamily.LEGACY_LED_CHORD,
        ProtocolFamily.LEGACY_LED_HUE,
        ProtocolFamily.ZENGGE_MESH,
    }

    limited_models = [
        model
        for model in catalog.user_facing_models()
        if model.family in limited_families
    ]

    assert len(limited_models) == 95
    assert {model.support_level for model in limited_models} == {
        SupportLevel.LIMITED
    }
    assert catalog.resolve_name("SP530E").support_level is SupportLevel.LIMITED
    assert catalog.resolve_name("RG4").support_level is SupportLevel.LIMITED
    assert catalog.resolve_name("SP660E").support_level is SupportLevel.RECOGNIZED


def test_legacy_uniled_parity_candidates_are_tracked() -> None:
    """Models already present in the old integration are marked for parity."""
    catalog = default_catalog()
    legacy_names = {
        model.name
        for model in catalog.user_facing_models()
        if model.legacy_uniled_supported
    }

    assert len(legacy_names) == 51
    assert "SP601E" in legacy_names
    assert "SP65CE" in legacy_names
    assert "SP107E" in legacy_names
    assert "SP110E" in legacy_names
    assert "SP530E" not in legacy_names
    assert "SP801E" not in legacy_names


def test_legacy_only_sp_led_models_are_separate_catalog_source() -> None:
    """Old LED Chord/Hue modules are cataloged outside the BanlanX APK source."""
    catalog = default_catalog()

    expected = {
        "SP107E": (0x107E, ProtocolFamily.LEGACY_LED_CHORD),
        "SP110E": (0x110E, ProtocolFamily.LEGACY_LED_HUE),
    }
    for name, (model_id, family) in expected.items():
        model = catalog.resolve_name(name)

        assert model is not None
        assert model.model_id == model_id
        assert model.family is family
        assert model.home_uri.startswith("/legacy/uniled/")
        assert model.support_level is SupportLevel.LIMITED
        assert model.legacy_uniled_supported is True


def test_manifest_contains_telink_mesh_bluetooth_matcher() -> None:
    """Generic Telink/Zengge mesh advertisements can trigger config flow."""
    manifest = json.loads(
        Path("custom_components/uniled/manifest.json").read_text(encoding="utf-8")
    )

    assert {
        "connectable": True,
        "manufacturer_id": 529,
        "service_uuid": "00010203-0405-0607-0809-0a0b0c0d1910",
    } in manifest["bluetooth"]


def test_manifest_bluetooth_matchers_are_connectable() -> None:
    """Every current Bluetooth setup path needs an outgoing BLE connection."""
    manifest = json.loads(
        Path("custom_components/uniled/manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["bluetooth"]
    assert [
        matcher
        for matcher in manifest["bluetooth"]
        if matcher.get("connectable") is not True
    ] == []


def test_manifest_local_name_matchers_cover_ble_catalog_names() -> None:
    """Bluetooth discovery matchers cover every user-facing BLE catalog name."""
    catalog = default_catalog()
    manifest = json.loads(
        Path("custom_components/uniled/manifest.json").read_text(encoding="utf-8")
    )
    patterns = tuple(
        matcher["local_name"]
        for matcher in manifest["bluetooth"]
        if "local_name" in matcher
    )
    ble_names = tuple(
        model.name
        for model in catalog.user_facing_models()
        if TransportKind.BLE in model.transports
        or TransportKind.BLE_MESH in model.transports
    )

    assert len(ble_names) == 151
    assert "SP*" not in patterns
    assert "SP1*" in patterns
    for legacy_name in ("SP107E", "SP110E"):
        assert legacy_name in ble_names
        assert any(fnmatchcase(legacy_name, pattern) for pattern in patterns)
    assert [
        name
        for name in ble_names
        if not any(fnmatchcase(name, pattern) for pattern in patterns)
    ] == []


def test_manifest_declares_zengge_mesh_crypto_dependency() -> None:
    """RG4/Zengge mesh packet crypto needs pycryptodome AES."""
    manifest = json.loads(
        Path("custom_components/uniled/manifest.json").read_text(encoding="utf-8")
    )

    assert "pycryptodome>=3.17" in manifest["requirements"]


def test_manifest_does_not_reference_original_uniled_repository() -> None:
    """UniLED Next should not advertise the detached original project."""
    manifest_text = Path("custom_components/uniled/manifest.json").read_text(
        encoding="utf-8"
    )

    assert "monty68/uniled" not in manifest_text
