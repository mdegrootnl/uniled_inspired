"""BLE mesh profile tests."""

from __future__ import annotations

from custom_components.uniled.core import default_catalog, plan_for_model
from custom_components.uniled.core.transports import (
    describe_mesh_profile,
    mesh_profile_for_model,
    telink_mesh_advertisement,
)
from custom_components.uniled.core.transports.mesh import (
    MESH_APP_COMMAND_ID_HINTS,
    MESH_APP_COMMAND_ID_NAMES,
    SIG_MESH_UUID_HINTS,
)


def test_rg4_mesh_profile_preserves_old_uniled_zengge_facts() -> None:
    """RG4 keeps the old UniLED Telink/Zengge mesh profile facts visible."""
    catalog = default_catalog()
    model = catalog.resolve_name("RG4")
    assert model is not None

    profile = mesh_profile_for_model(model)

    assert profile is not None
    assert profile.family.value == "zengge_mesh"
    assert profile.protocol_name == "telink_zengge"
    assert profile.package == "packages/accessories"
    assert profile.service_uuid == "00010203-0405-0607-0809-0a0b0c0d1910"
    assert profile.status_uuid == "00010203-0405-0607-0809-0a0b0c0d1911"
    assert profile.command_uuid == "00010203-0405-0607-0809-0a0b0c0d1912"
    assert profile.pair_uuid == "00010203-0405-0607-0809-0a0b0c0d1914"
    assert profile.manufacturer_id == 63517
    assert profile.telink_manufacturer_id == 529
    assert profile.default_mesh_uuid == 0x0211
    assert profile.requires_pairing is True
    assert profile.requires_cloud_mesh_credentials is True
    assert profile.old_uniled_protocol_known is True
    assert profile.core_command_protocol_known is True
    assert profile.status_uses_notifications is True
    assert len(profile.effect_names) == 20
    assert profile.command_names == (
        "status_notify",
        "state_query",
        "power",
        "brightness",
        "rgb",
        "color_temp",
        "warm_white",
        "effect",
    )
    assert profile.effect_command_fields == (
        "command=0xed",
        "payload[0]=0xff device_type",
        "payload[1]=effect",
        "payload[2]=speed",
        "payload[3]=level",
        "old-UniLED default speed=0",
        "old-UniLED default level=100",
    )
    assert profile.sig_mesh_uuid_hints == SIG_MESH_UUID_HINTS
    assert profile.app_command_id_hints == MESH_APP_COMMAND_ID_HINTS
    assert [hint.name for hint in profile.app_command_id_hints] == list(
        MESH_APP_COMMAND_ID_NAMES
    )
    assert [hint.command_id for hint in profile.app_command_id_hints] == [
        0x02,
        0x23,
        0x24,
        0x26,
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC4,
        0xC5,
        0xC7,
        0xC8,
    ]
    assert profile.control_gap_hints == (
        "Old UniLED exposed Zengge nodes as light/sensor features only",
        "Effect speed/level controls resend the current effect with the edited byte",
        (
            "Known node metadata from advertisements and MagicHue cloud "
            "import is registered"
        ),
        "Remote and non-light mesh events still need notification mapping",
    )
    assert profile.control_blockers == (
        "mesh_remote_event_parser_pending",
        "mesh_provisioning_frame_pending",
        "mesh_group_management_pending",
        "mesh_node_management_controls_pending",
    )
    assert profile.route_hints == (
        "/device/ble_mesh_rc",
        "/device/ble_mesh_rc/provisioning_guide",
    )
    assert profile.provisioning_state_hints == (
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
    assert len(profile.provisioning_hints) == 11
    assert profile.provisioning_hints[2:5] == (
        (
            "2. Provisioning automatically ends after 90 seconds. If there "
            "are still unprovisioned devices nearby, you can long press the "
            "button again to continue provisioning;"
        ),
        (
            "3. During the provisioning process, other devices cannot be "
            "controlled. You can press the provisioning button again to end "
            "provisioning."
        ),
        "If indicator light flashes rapidly, it indicates abnormal provisioning",
    )
    assert profile.provisioning_hints[-2:] == (
        "Invalid PDU(The provisioning protocol PDU is not recognized by the device.)",
        (
            "Out of Resources(The provisioning protocol cannot be continued "
            "due to insufficient resources in the device.)2"
        ),
    )
    assert profile.package_asset_count == 9
    assert len(profile.apk_asset_evidence) == 9
    assert len(profile.apk_string_evidence) == 8
    assert "packages/accessories/assets/icons/mesh_node.png" in (
        profile.apk_asset_evidence
    )
    assert profile.effect_names[:3] == (
        "Seven Color Cross Fade",
        "Red Gradual Change",
        "Green Gradual Change",
    )
    assert profile.effect_names[-1] == "Seven Color Jumping Change"


def test_rg4_mesh_profile_diagnostic_description_is_command_known() -> None:
    """RG4 diagnostics say the old Telink/Zengge command protocol is ported."""
    catalog = default_catalog()
    model = catalog.resolve_name("RG4")
    assert model is not None

    profile = mesh_profile_for_model(model)

    assert describe_mesh_profile(profile) == (
        "zengge_mesh; telink_zengge; core_protocol_known; "
        "pairing_required; old_uniled_protocol_known; "
        "service=00010203-0405-0607-0809-0a0b0c0d1910; effects=20; "
        "commands=8; effect_fields=7; sig_mesh_uuids=6; "
        "app_command_ids=12; gaps=4; blockers=4; routes=2; "
        "provisioning=11; provisioning_states=9; package_assets=9; "
        "apk_assets=9; apk_strings=8"
    )
    feature = plan_for_model(model).feature("mesh_profile")
    assert feature.implemented is True
    blocker_count = plan_for_model(model).feature("mesh_control_blocker_count")
    assert blocker_count.unit == "blockers"


def test_banlanx_scene_mesh_profile_exposes_apk_setup_facts() -> None:
    """BanlanX scene mesh exposes APK setup facts without command frames."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP310E")
    assert model is not None

    profile = mesh_profile_for_model(model)

    assert profile is not None
    assert profile.family.value == "banlanx_scene_mesh"
    assert profile.protocol_name == "banlanx_scene_mesh"
    assert profile.package == "packages/scene_ui"
    assert profile.service_uuid is None
    assert profile.old_uniled_protocol_known is False
    assert profile.core_command_protocol_known is False
    assert profile.effect_names == ()
    assert profile.sig_mesh_uuid_hints == SIG_MESH_UUID_HINTS
    assert profile.app_command_id_hints == MESH_APP_COMMAND_ID_HINTS
    assert [hint.name for hint in profile.app_command_id_hints] == list(
        MESH_APP_COMMAND_ID_NAMES
    )
    assert profile.route_hints == ("/device/scene_ui",)
    assert profile.provisioning_hints == (
        (
            "1. SP31XE series requires firmware V1.1 or above, and SP32XE "
            'series requires firmware V1.1 or above to support the "One-touch '
            'Provisioning" function;'
        ),
        (
            "2. Provisioning automatically ends after 90 seconds. If there "
            "are still unprovisioned devices nearby, you can long press the "
            "button again to continue provisioning;"
        ),
        (
            "3. During the provisioning process, other devices cannot be "
            "controlled. You can press the provisioning button again to end "
            "provisioning."
        ),
    )
    assert profile.control_gap_hints == (
        "Scene mesh uses the scene_ui APK package, not the RG4 accessories package",
        "No scene mesh provisioning frame map has been recovered",
        "No scene mesh group, node, or scene-routing command map has been recovered",
    )
    assert profile.control_blockers == (
        "scene_mesh_provisioning_frame_pending",
        "scene_mesh_group_management_pending",
        "scene_mesh_node_lifecycle_pending",
        "scene_mesh_routing_frame_pending",
    )
    assert profile.package_asset_count == 204
    assert len(profile.apk_string_evidence) == 4
    assert describe_mesh_profile(profile) == (
        "banlanx_scene_mesh; banlanx_scene_mesh; core_protocol_pending; "
        "sig_mesh_uuids=6; app_command_ids=12; gaps=3; blockers=4; "
        "routes=1; provisioning=3; package_assets=204; apk_strings=4"
    )
    assert plan_for_model(model).has_feature("mesh_profile")
    assert plan_for_model(model).feature("mesh_control_blocker_count").unit == (
        "blockers"
    )


def test_telink_mesh_advertisement_parses_old_uniled_offsets() -> None:
    """Telink manufacturer data exposes mesh UUID, node ID, and node type."""
    data = bytes.fromhex("11 02 00 00 00 00 00 23 00 44")

    advert = telink_mesh_advertisement({529: data})

    assert advert is not None
    assert advert.mesh_uuid == 0x0211
    assert advert.node_type == 0x23
    assert advert.node_id == 0x44
    assert advert.old_uniled_unique_id == "zng_mesh_0x211"


def test_telink_mesh_advertisement_rejects_missing_or_short_data() -> None:
    """Only complete Telink manufacturer records become mesh identities."""
    assert telink_mesh_advertisement({}) is None
    assert telink_mesh_advertisement({529: b"\x11\x02"}) is None


def test_non_mesh_models_do_not_claim_mesh_profiles() -> None:
    """BLE and LAN-only models do not expose BLE mesh profile facts."""
    catalog = default_catalog()

    for name in ("SP630E", "SP802E"):
        model = catalog.resolve_name(name)
        assert model is not None

        assert mesh_profile_for_model(model) is None
        assert not plan_for_model(model).has_feature("mesh_profile")
