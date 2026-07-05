"""Support matrix generator coverage."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_support_matrix import (
    matrix_summary,
    render_json,
    render_markdown,
    support_blocker_counts,
    support_matrix_rows,
)


def test_support_matrix_covers_every_user_facing_catalog_model() -> None:
    rows = support_matrix_rows()
    summary = matrix_summary(rows)

    assert len(rows) == 152
    assert summary["catalog_records"] == 191
    assert summary["unique_names"] == 153
    assert summary["user_facing_records"] == 190
    assert summary["user_facing_models"] == 152
    assert summary["filtered_records"] == 1
    assert summary["record_families"]["banlanx_scene_ui"] == 25
    assert summary["record_families"]["banlanx_6xx"] == 56
    assert summary["families"]["banlanx_scene_ui"] == 24
    assert summary["families"]["banlanx_6xx"] == 38
    assert summary["support_levels"] == {
        "limited": 95,
        "recognized": 57,
    }
    assert summary["transports"] == {
        "ble": 124,
        "ble_mesh": 27,
        "cloud_optional": 39,
        "lan": 41,
    }
    assert summary["legacy_uniled_models"] == 52
    assert summary["protocol_ready_models"] == 94
    assert summary["support_blockers"] == support_blocker_counts(rows)


def test_support_matrix_summarizes_open_protocol_blockers() -> None:
    rows = support_matrix_rows()
    rows_by_name = {row.name: row for row in rows}
    blockers = support_blocker_counts(rows)

    assert blockers["command_protocol_pending"] == 57
    assert blockers["scene_command_envelope_pending"] == 50
    assert blockers["scene_status_parser_pending"] == 50
    assert blockers["scene_white_brightness_parser_pending"] == 50
    assert blockers["lan_frame_pending"] == 40
    assert blockers["account_token_schema_pending"] == 39
    assert blockers["raw_command_json_envelope_pending"] == 39
    assert blockers["ble_uuid_binding_pending"] == 30
    assert blockers["firmware_v1_1_required"] == 26
    assert blockers["scene_mesh_routing_pending"] == 26
    assert blockers["car_light_ble_opcode_pending"] == 4
    assert blockers["network_discovery_pending"] == 2
    assert blockers["fish_tank_ble_opcode_pending"] == 1
    assert blockers["accessory_dependency=SP702E"] == 1
    assert "legacy_only_command_port_pending" not in blockers
    assert "legacy_only_status_parser_pending" not in blockers

    sp601 = rows_by_name["SP601E"]
    assert sp601.support_blockers == ()
    assert sp601.support_blocker_count == 0

    ft001 = rows_by_name["FT001"]
    assert ft001.support_blocker_count == len(ft001.support_blockers)
    assert "fish_tank_ble_opcode_pending" in ft001.support_blockers
    assert "cloud_optional" not in ft001.support_blockers
    assert all(
        blocker.endswith("_pending")
        or blocker.endswith("_required")
        or blocker.startswith("accessory_dependency=")
        for blocker in ft001.support_blockers
    )

    rg4 = rows_by_name["RG4"]
    assert rg4.support_blocker_count == len(rg4.support_blockers)
    assert "pair_required" in rg4.support_blockers


def test_support_matrix_marks_representative_evidence_paths() -> None:
    rows = {row.name: row for row in support_matrix_rows()}

    sp601 = rows["SP601E"]
    assert sp601.support_level == "limited"
    assert sp601.protocol_ready is True
    assert sp601.support_blockers == ()
    assert sp601.support_blocker_count == 0
    assert sp601.evidence_profiles == (
        "command_protocol",
        "legacy_uniled",
        "ble_apk",
    )

    sp530 = rows["SP530E"]
    assert sp530.evidence_profiles == (
        "command_protocol",
        "sp6xx_style_ble_commands",
        "ble_apk",
        "lan_apk",
        "cloud_apk",
        "sp630e_apk",
    )
    assert "cloud_optional" in sp530.support_disposition
    assert "account_token_schema_pending" in sp530.support_disposition
    assert "request_signing_headers_pending" in sp530.support_disposition
    assert "raw_command_json_envelope_pending" in sp530.support_disposition

    sp541 = rows["SP541E"]
    assert sp541.evidence_profiles == (
        "command_protocol",
        "sp6xx_style_ble_commands",
        "ble_apk",
        "lan_apk",
        "sptech_lan",
        "cloud_apk",
        "sp630e_apk",
    )
    assert "lan_frame_ready" in sp541.support_disposition
    assert "lan_frame_pending" not in sp541.support_blockers

    sp603 = rows["SP603E"]
    assert sp603.evidence_profiles == (
        "command_protocol",
        "apk_catalog_family_inference",
        "ble_apk",
    )
    assert "apk_protocol_inference" in sp603.support_disposition

    sp660 = rows["SP660E"]
    assert sp660.support_level == "recognized"
    assert sp660.protocol_ready is False
    assert sp660.support_blocker_count == len(sp660.support_blockers)
    assert "scene_command_envelope_pending" in sp660.support_blockers
    assert "scene_white_brightness_parser_pending" in sp660.support_blockers
    assert sp660.evidence_profiles == ("ble_apk", "scene_apk")
    assert "diagnostic_only" in sp660.support_disposition
    assert "scene_command_envelope_pending" in sp660.support_disposition
    assert "scene_lfx_frame_pending" in sp660.support_disposition
    assert "scene_white_brightness_parser_pending" in sp660.support_disposition

    sp107 = rows["SP107E"]
    assert sp107.support_level == "limited"
    assert sp107.protocol_ready is True
    assert sp107.legacy_uniled is True
    assert sp107.evidence_profiles == (
        "command_protocol",
        "legacy_uniled",
        "legacy_uniled_only",
    )
    assert sp107.support_blockers == ()
    assert "old_uniled_parity" in sp107.support_disposition

    sp110 = rows["SP110E"]
    assert sp110.family == "legacy_led_hue"
    assert sp110.support_level == "limited"
    assert sp110.protocol_ready is True
    assert sp110.evidence_profiles == (
        "command_protocol",
        "legacy_uniled",
        "legacy_uniled_only",
    )

    sp310 = rows["SP310E"]
    assert sp310.evidence_profiles == ("mesh_apk", "scene_apk")
    assert "scene_status_parser_pending" in sp310.support_disposition
    assert "scene_timer_frame_pending" in sp310.support_disposition
    assert "scene_diy_frame_pending" in sp310.support_disposition
    assert "firmware_v1_1_required" in sp310.support_disposition
    assert "provisioning_frame_pending" in sp310.support_disposition
    assert "scene_mesh_routing_pending" in sp310.support_disposition

    sp701 = rows["SP701E"]
    assert "car_light_ble_opcode_pending" in sp701.support_disposition
    assert "car_light_subdevice_binding_pending" in sp701.support_disposition
    assert "car_light_password_flow_pending" in sp701.support_disposition

    spmic = rows["SP-MIC"]
    assert "car_light_sp_mic_event_pending" in spmic.support_disposition
    assert "accessory_dependency=SP702E" in spmic.support_disposition

    sp801 = rows["SP801E"]
    assert sp801.evidence_profiles == ("lan_apk", "network_apk")
    assert sp801.support_blocker_count == len(sp801.support_blockers)
    assert "lan_frame_pending" in sp801.support_blockers
    assert "network_panel_layout_pending" in sp801.support_blockers
    assert "lan_frame_pending" in sp801.support_disposition
    assert "network_artnet_config_pending" in sp801.support_disposition
    assert "network_playlist_packet_pending" in sp801.support_disposition
    assert "network_panel_layout_pending" in sp801.support_disposition

    sp802 = rows["SP802E"]
    assert "network_lfx_packet_pending" in sp802.support_disposition
    assert "network_lfx_status_parser_pending" in sp802.support_disposition
    assert "network_matrix_music_pending" in sp802.support_disposition

    ft001 = rows["FT001"]
    assert ft001.support_blocker_count == len(ft001.support_blockers)
    assert "fish_tank_brightness_parser_pending" in ft001.support_blockers
    assert "cloud_optional" not in ft001.support_blockers
    assert "fish_tank_ble_opcode_pending" in ft001.support_disposition
    assert "fish_tank_timer_frame_pending" in ft001.support_disposition
    assert "fish_tank_favorite_frame_pending" in ft001.support_disposition
    assert "fish_tank_brightness_parser_pending" in ft001.support_disposition
    assert "cloud_optional" in ft001.support_disposition
    assert "account_token_schema_pending" in ft001.support_disposition
    assert "region_reauth_contract_pending" in ft001.support_disposition
    assert "device_bind_ownership_lifecycle_pending" in ft001.support_disposition

    rg4 = rows["RG4"]
    assert rg4.support_level == "limited"
    assert rg4.protocol_ready is False
    assert rg4.legacy_uniled is True
    assert rg4.support_blocker_count == len(rg4.support_blockers)
    assert "pair_required" in rg4.support_blockers
    assert "mesh_node_management_controls_pending" in rg4.support_blockers
    assert rg4.evidence_profiles == (
        "zengge_mesh_core",
        "legacy_uniled",
        "mesh_apk",
    )
    assert "node_commands_guarded" in rg4.support_disposition
    assert (
        "mesh_effect_speed_level_controls_pending"
        not in rg4.support_disposition
    )
    assert "mesh_remote_event_parser_pending" in rg4.support_disposition
    assert "mesh_provisioning_frame_pending" in rg4.support_disposition
    assert "mesh_node_management_controls_pending" in rg4.support_disposition


def test_support_matrix_distinguishes_old_uniled_mesh_from_empty_legacy_net() -> None:
    rows = {row.name: row for row in support_matrix_rows()}

    rg4 = rows["RG4"]
    assert rg4.legacy_uniled is True
    assert "legacy_uniled" in rg4.evidence_profiles
    assert "node_commands_guarded" in rg4.support_disposition

    sp801 = rows["SP801E"]
    assert sp801.legacy_uniled is False
    assert "legacy_uniled" not in sp801.evidence_profiles
    assert "network_socket_frame_pending" in sp801.support_disposition


def test_support_matrix_renderers_include_machine_and_human_outputs() -> None:
    rows = support_matrix_rows()
    data = json.loads(render_json(rows))
    markdown = render_markdown(rows)

    assert data["summary"]["user_facing_models"] == 152
    assert data["summary"]["user_facing_records"] == 190
    assert data["summary"]["support_blockers"]["command_protocol_pending"] == 57
    assert data["summary"]["support_blockers"]["scene_lfx_frame_pending"] == 50
    ft001 = next(row for row in data["rows"] if row["name"] == "FT001")
    assert ft001["support_blocker_count"] == len(ft001["support_blockers"])
    assert "fish_tank_ble_opcode_pending" in ft001["support_blockers"]
    sp601 = next(row for row in data["rows"] if row["name"] == "SP601E")
    assert sp601["support_blockers"] == []
    assert sp601["support_blocker_count"] == 0
    assert "# UniLED Next Support Matrix" in markdown
    assert "legacy-only old UniLED rows" in markdown
    assert "- Catalog records: 191" in markdown
    assert "- Catalog record families: " in markdown
    assert "- Canonical user-facing models: 152" in markdown
    assert "- Old UniLED parity/evidence candidates: 52" in markdown
    assert "## Open Support Blockers" in markdown
    assert "| command_protocol_pending | 57 |" in markdown
    assert "| scene_command_envelope_pending | 50 |" in markdown
    assert "## Model Matrix" in markdown
    assert "| Open blockers | Blocker count | Disposition |" in markdown
    assert (
        "| SP801E | 157 | banlanx_network | recognized | lan | no | "
        "lan_apk, network_apk | command_protocol_pending, "
        "lan_frame_pending"
    ) in markdown


def test_support_matrix_document_is_generated_from_current_catalog() -> None:
    expected = render_markdown(support_matrix_rows())
    actual = Path("docs/SUPPORT_MATRIX.md").read_text(encoding="utf-8")

    assert actual == expected
