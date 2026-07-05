"""Runtime shell tests that do not require Home Assistant."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from custom_components.uniled import _attach_runtime_transports
from custom_components.uniled.const import (
    CONF_ADDRESS,
    CONF_CLOUD_PASSWORD,
    CONF_CLOUD_USERNAME,
    CONF_DEVICE_ID,
    CONF_DISCOVERY_CONFIDENCE,
    CONF_DISCOVERY_MATCH,
    CONF_DISCOVERY_SOURCE,
    CONF_HOST,
    CONF_MESH_KEY,
    CONF_MESH_LTK,
    CONF_MESH_NODE_ID,
    CONF_MESH_NODE_TYPE,
    CONF_MESH_NODE_WIRING,
    CONF_MESH_NODES,
    CONF_MESH_PASSWORD,
    CONF_MESH_UUID,
    CONF_MODEL,
    CONF_MODEL_ID,
    CONF_TRANSPORT,
    DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
    DISCOVERY_CONFIDENCE_VERIFIED,
    DISCOVERY_MATCH_SAFE_SUFFIX,
    DISCOVERY_MATCH_SPNET_MODEL_ID,
    DISCOVERY_SOURCE_BLUETOOTH,
    DISCOVERY_SOURCE_LAN,
    TRANSPORT_BLE,
    TRANSPORT_LAN,
)
from custom_components.uniled.core import (
    BanlanX6xxProtocol,
    BanlanXCustom5xxProtocol,
    TransportError,
    TransportKind,
    default_catalog,
    protocol_for_model,
)
from custom_components.uniled.core.protocols import (
    ZenggeNodeContext,
    make_pair_packet,
    parse_zengge_notification_block,
)
from custom_components.uniled.core.scene import (
    SCENE_MODE_EFFECTS,
    SCENE_NATIVE_CODE_ANCHORS,
    SCENE_NATIVE_PERSISTENCE_EXPORTS,
)
from custom_components.uniled.core.state import ChannelState
from custom_components.uniled.core.transports.mesh import SIG_MESH_UUID_HINTS
from custom_components.uniled.runtime import (
    RuntimeSetupError,
    UniLEDRuntime,
    apply_light_command_state,
    apply_number_command_state,
    apply_runtime_state,
    apply_scene_command_state,
    apply_switch_command_state,
    async_apply_legacy_set_state_service,
    async_pair_zengge_mesh,
    async_refresh_runtime_state,
    async_refresh_zengge_mesh_state,
    build_runtime,
    cct_kelvin_from_levels,
    cct_levels_for_kelvin,
    channel_state,
    command_button_features,
    command_control_available,
    command_light_features,
    command_number_features,
    command_scene_features,
    command_select_features,
    command_switch_features,
    control_value,
    diagnostic_sensor_features,
    effect_command_value,
    implemented_sensor_keys,
    light_color_mode,
    light_mode_command_values,
    light_supported_color_modes,
    light_type_command_values,
    onoff_command_values,
    runtime_diagnostics,
    select_options,
    set_zengge_mesh_brightness,
    set_zengge_mesh_color_temp,
    set_zengge_mesh_effect,
    set_zengge_mesh_power,
    set_zengge_mesh_rgb,
    set_zengge_mesh_white,
    zengge_mesh_command_ready,
    zengge_mesh_credentials,
    zengge_mesh_effect_command_values,
    zengge_mesh_node_ids,
    zengge_mesh_panel_node_ids,
)
from custom_components.uniled.setup_data import (
    bluetooth_setup_entry_data,
    lan_setup_entry_data_from_spnet_response,
    manual_setup_entry_data,
)


@dataclass(slots=True)
class RecordingTransport:
    """Transport test double."""

    response: bytes | None = None
    sent: list[tuple[bytes, bool]] = field(default_factory=list)

    async def send(self, payload: bytes, *, response: bool = False) -> bytes | None:
        """Record one payload."""
        self.sent.append((payload, response))
        return self.response if response else None


@dataclass(slots=True)
class RecordingMeshTransport:
    """Zengge mesh transport test double."""

    pair_response: bytes = b"\x0dABCDEFGH"
    writes: list[tuple[str, bytes, bool]] = field(default_factory=list)
    closed: bool = False

    async def write_pair(self, payload: bytes) -> bytes | None:
        """Record one pair-characteristic write."""
        self.writes.append(("pair", payload, True))
        return None

    async def read_pair(self) -> bytes:
        """Return the fake pair reply."""
        return self.pair_response

    async def write_status(self, payload: bytes) -> bytes | None:
        """Record one status-characteristic write."""
        self.writes.append(("status", payload, True))
        return None

    async def write_command(
        self,
        payload: bytes,
        *,
        response: bool = False,
    ) -> bytes | None:
        """Record one command-characteristic write."""
        self.writes.append(("command", payload, response))
        return None

    async def close(self) -> None:
        """Record close."""
        self.closed = True


@dataclass(slots=True)
class ClosableTransport:
    """Transport test double with close support only."""

    closed: bool = False

    async def close(self) -> None:
        """Record close."""
        self.closed = True


@dataclass(slots=True)
class FailingCloseTransport:
    """Command transport that fails during close."""

    closed: bool = False

    async def send(self, _payload: bytes, *, response: bool = False) -> bytes | None:
        """Return no response."""
        return None

    async def close(self) -> None:
        """Fail after recording close was attempted."""
        self.closed = True
        raise RuntimeError("close failed")


def _identity_block_encryptor(key: bytes, block: bytes) -> bytes:
    return block


def _paired_rg4_runtime(
    *,
    node_id: int = 0x44,
    node_type: int = 2,
) -> tuple[UniLEDRuntime, RecordingMeshTransport]:
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_MESH_UUID: 0x0211,
            CONF_MESH_NODE_ID: node_id,
            CONF_MESH_NODE_TYPE: node_type,
        }
    )
    transport = RecordingMeshTransport()
    runtime.attach_zengge_mesh_transport(
        transport,
        block_encryptor=_identity_block_encryptor,
    )
    asyncio.run(async_pair_zengge_mesh(runtime, session_random=b"12345678"))
    return runtime, transport


def test_runtime_async_close_closes_lan_holder() -> None:
    """Runtime close reaches diagnostic LAN holders."""
    runtime = build_runtime(
        {
            CONF_MODEL: "SP801E",
            CONF_HOST: "192.0.2.10",
            CONF_TRANSPORT: TRANSPORT_LAN,
        }
    )
    transport = ClosableTransport()

    runtime.attach_lan_transport(transport, host="192.0.2.10")

    assert runtime.transport is transport
    assert runtime.lan_profile is not None

    asyncio.run(runtime.async_close())

    assert transport.closed is True
    assert runtime.transport is None
    assert runtime.lan_profile is None


def test_runtime_async_close_records_close_errors_and_clears_references() -> None:
    """Runtime close clears references even if transport close fails."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    transport = FailingCloseTransport()

    runtime.attach_transport(transport)
    runtime.coordinator = object()
    runtime.notification_assembler = object()

    assert runtime.session is not None
    assert runtime.notification_assembler is not None

    asyncio.run(runtime.async_close())

    assert transport.closed is True
    assert runtime.transport is None
    assert runtime.session is None
    assert runtime.coordinator is None
    assert runtime.notification_assembler is None
    assert runtime.state.diagnostics["last_close_error"] == "close failed"


def test_runtime_command_features_preserve_entity_default_intent() -> None:
    """Runtime-visible command features keep release-friendly registry defaults."""
    sp541e = build_runtime({CONF_MODEL: "SP541E", CONF_DEVICE_ID: "bench"})
    sp541e.attach_transport(RecordingTransport())

    sp541e_lights = command_light_features(sp541e)

    assert [(feature.key, feature.implemented) for feature in sp541e_lights] == [
        ("main_light", True)
    ]
    assert sp541e_lights[0].enabled_by_default is True

    sp601 = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    sp601.attach_transport(RecordingTransport())

    sp601_lights = command_light_features(sp601)
    sp601_scenes = command_scene_features(sp601)

    assert [(feature.key, feature.implemented) for feature in sp601_lights] == [
        ("main_light", True),
        ("output_1_light", True),
        ("output_2_light", True),
    ]
    assert sp601_lights[0].enabled_by_default is True
    assert [feature.enabled_by_default for feature in sp601_lights[1:]] == [
        False,
        False,
    ]
    assert sp601_scenes
    assert all(feature.implemented for feature in sp601_scenes)
    assert {feature.enabled_by_default for feature in sp601_scenes} == {False}


def test_runtime_resolves_model_plan_and_protocol() -> None:
    """Runtime setup resolves the catalog, plan, and protocol family."""
    runtime = build_runtime(
        {
            CONF_MODEL: "SP601E",
            CONF_DEVICE_ID: "AA:BB:CC:DD:EE:FF",
            CONF_TRANSPORT: "manual",
        }
    )

    assert runtime.model.name == "SP601E"
    assert runtime.protocol_ready is True
    assert runtime.state.model == "SP601E"
    assert runtime.state.available is False
    assert runtime.diagnostic_value("catalog_model") == "SP601E"
    assert runtime.diagnostic_value("catalog_model_id") == 1
    assert runtime.diagnostic_value("catalog_parent_id") is None
    assert runtime.diagnostic_value("catalog_connect_caps") == 1
    assert runtime.diagnostic_value("catalog_connect_capabilities") == "ble"
    assert runtime.diagnostic_value("catalog_spec_functions") == 17
    assert (
        runtime.diagnostic_value("catalog_spec_function_bits")
        == "feature_0x01, feature_0x10"
    )
    assert runtime.diagnostic_value("catalog_color_cap") == 1
    assert runtime.diagnostic_value("catalog_color_capabilities") == "rgb"
    assert runtime.diagnostic_value("catalog_feature_count") == 0
    assert runtime.diagnostic_value("catalog_feature_keys") == "none"
    assert runtime.diagnostic_value("catalog_feature_summary") == "none"
    assert runtime.diagnostic_value("catalog_variant_count") == 1
    assert runtime.diagnostic_value("catalog_variant_ids") == "1"
    assert runtime.diagnostic_value("protocol_family") == "banlanx_601"
    assert runtime.diagnostic_value("support_blocker_count") == 0
    assert runtime.diagnostic_value("support_blockers") == "none"
    assert runtime.diagnostic_value("configured_transport") == "manual"
    assert runtime.diagnostic_value("runtime_transport_state") == "diagnostic_only"
    assert runtime.diagnostic_value("last_refresh_result") is None
    assert runtime.diagnostic_value("effect_type") is None
    assert runtime.diagnostic_value("legacy_uniled_parity") is True
    assert runtime.diagnostic_value("protocol_evidence_kind") == "old_uniled_exact"
    assert "effect_type" in implemented_sensor_keys(runtime)
    runtime.state.channels[0] = ChannelState(channel_id=0, effect_type="Static")
    assert runtime.diagnostic_value("effect_type") == "Static"

    diagnostics = runtime_diagnostics(runtime)["model"]
    assert diagnostics["connect_caps"] == 1
    assert diagnostics["connect_capabilities"] == ["ble"]
    assert diagnostics["spec_functions"] == 17
    assert diagnostics["spec_function_bits"] == ["feature_0x01", "feature_0x10"]
    assert diagnostics["color_cap"] == 1
    assert diagnostics["color_capabilities"] == ["rgb"]
    assert diagnostics["feature_keys"] == []
    assert diagnostics["features"] == {}
    assert diagnostics["support_blockers"] == []


def test_runtime_exposes_discovery_provenance_diagnostics() -> None:
    """Stored discovery evidence is visible as support diagnostics."""
    catalog = default_catalog()
    ble_setup = bluetooth_setup_entry_data(
        catalog,
        name="SP601E_AABB",
        address="AA:BB:CC:DD:EE:31",
        connectable=True,
    )
    lan_setup = lan_setup_entry_data_from_spnet_response(
        catalog,
        bytes.fromhex(
            "53704e65740000210000000000010000105c00542024111f77075350353431450000"
        ),
        source="192.0.2.92",
    )

    ble_runtime = build_runtime(ble_setup.data)
    lan_runtime = build_runtime(lan_setup.data)
    manual_runtime = build_runtime(
        {
            CONF_MODEL: "SP601E",
            CONF_DEVICE_ID: "bench",
            CONF_TRANSPORT: "manual",
        }
    )

    assert (
        ble_runtime.diagnostic_value("discovery_source")
        == DISCOVERY_SOURCE_BLUETOOTH
    )
    assert (
        ble_runtime.diagnostic_value("discovery_match")
        == DISCOVERY_MATCH_SAFE_SUFFIX
    )
    assert (
        ble_runtime.diagnostic_value("discovery_confidence")
        == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
    )
    assert "discovery_source" in implemented_sensor_keys(ble_runtime)
    assert "discovery_match" in implemented_sensor_keys(ble_runtime)
    assert "discovery_confidence" in implemented_sensor_keys(ble_runtime)

    assert lan_runtime.diagnostic_value("discovery_source") == DISCOVERY_SOURCE_LAN
    assert (
        lan_runtime.diagnostic_value("discovery_match")
        == DISCOVERY_MATCH_SPNET_MODEL_ID
    )
    assert (
        lan_runtime.diagnostic_value("discovery_confidence")
        == DISCOVERY_CONFIDENCE_VERIFIED
    )

    assert manual_runtime.diagnostic_value("discovery_source") is None
    assert manual_runtime.diagnostic_value("discovery_match") is None
    assert manual_runtime.diagnostic_value("discovery_confidence") is None

    diagnostics = runtime_diagnostics(ble_runtime)
    assert diagnostics["entry"][CONF_DISCOVERY_SOURCE] == DISCOVERY_SOURCE_BLUETOOTH
    assert diagnostics["entry"][CONF_DISCOVERY_MATCH] == DISCOVERY_MATCH_SAFE_SUFFIX
    assert (
        diagnostics["entry"][CONF_DISCOVERY_CONFIDENCE]
        == DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN
    )


def test_setup_helper_attaches_normal_ble_transport_session() -> None:
    """Setup still attaches command sessions for normal BLE profiles."""
    runtime = build_runtime(
        {
            CONF_MODEL: "SP601E",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        }
    )

    kind = _attach_runtime_transports(
        None,
        dict(runtime.entry_data),
        runtime,
        notification_callback=lambda data: None,
        mesh_notification_callback=lambda data: None,
    )

    assert kind == "ble"
    assert runtime.session_ready is True
    assert runtime.lan_transport_ready is False
    assert runtime.mesh_transport_ready is False
    assert runtime.diagnostic_value("runtime_transport_state") == "command_session"
    assert runtime.transport.__class__.__name__ == "UniLEDBLETransport"


def test_setup_helper_attaches_apk_inferred_ble_command_sessions() -> None:
    """APK-inferred command families get BLE sessions, not diagnostics only."""
    cases = {
        "SP603E": {
            "light_mode": None,
            "effect_count": 22,
            "has_audio": False,
            "has_effect_loop": True,
        },
        "360PhotoB": {
            "light_mode": 0x06,
            "effect_count": 183,
            "has_audio": True,
            "has_effect_loop": True,
        },
    }

    for model_name, expected in cases.items():
        runtime = build_runtime(
            {
                CONF_MODEL: model_name,
                CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            }
        )

        kind = _attach_runtime_transports(
            None,
            dict(runtime.entry_data),
            runtime,
            notification_callback=lambda data: None,
            mesh_notification_callback=lambda data: None,
        )

        assert kind == "ble", model_name
        assert runtime.session_ready is True, model_name
        assert runtime.diagnostic_value("protocol_evidence_kind") == (
            "apk_catalog_family_inference"
        )
        assert runtime.diagnostic_value("support_disposition").endswith(
            "apk_protocol_inference"
        )
        assert [feature.key for feature in command_light_features(runtime)] == [
            "main_light"
        ]

        if expected["light_mode"] is not None:
            runtime.state.diagnostics["light_type"] = expected["light_mode"]

        select_keys = {feature.key for feature in command_select_features(runtime)}
        number_keys = {feature.key for feature in command_number_features(runtime)}
        switch_keys = {feature.key for feature in command_switch_features(runtime)}

        assert len(select_options(runtime, "effect")) == expected["effect_count"]
        assert ("audio_input" in select_keys) is expected["has_audio"]
        assert ("audio_sensitivity" in number_keys) is expected["has_audio"]
        assert ("effect_loop" in switch_keys) is expected["has_effect_loop"]

        asyncio.run(runtime.async_close())


def test_setup_helper_attaches_all_command_ready_ble_models() -> None:
    """Every command-ready BLE catalog model gets a session-backed light."""
    catalog = default_catalog()
    checked: list[str] = []

    for model in catalog.user_facing_models():
        if TransportKind.BLE not in model.transports:
            continue
        if protocol_for_model(model) is None:
            continue

        runtime = build_runtime(
            {
                CONF_MODEL: model.name,
                CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            }
        )

        kind = _attach_runtime_transports(
            None,
            dict(runtime.entry_data),
            runtime,
            notification_callback=lambda data: None,
            mesh_notification_callback=lambda data: None,
        )

        checked.append(model.name)
        assert kind == "ble", model.name
        assert runtime.session_ready is True, model.name
        assert (
            runtime.diagnostic_value("runtime_transport_state") == "command_session"
        ), model.name
        assert runtime.diagnostic_value("support_disposition").startswith(
            "limited; setup="
        ), model.name
        assert command_light_features(runtime), model.name

        asyncio.run(runtime.async_close())

    assert len(checked) == 94
    assert checked[0] == "360PhotoB"
    assert checked[-1] == "Wall Light"


def test_recognized_catalog_models_remain_diagnostic_addable() -> None:
    """Recognized-only catalog models build diagnostic-first runtimes."""
    catalog = default_catalog()
    expected_profile_keys = {
        "banlanx_car_lights": {"ble_profile", "car_light_profile"},
        "banlanx_network": {"lan_profile", "network_profile"},
        "banlanx_scene_mesh": {"mesh_profile", "scene_profile"},
        "banlanx_scene_ui": {"ble_profile", "scene_profile"},
        "fish_tank": {
            "ble_profile",
            "cloud_profile",
            "fish_tank_profile",
            "lan_profile",
        },
    }
    checked: list[str] = []
    apk_profile_checked: list[str] = []

    for model in catalog.user_facing_models():
        if model.support_level.value != "recognized":
            continue

        runtime = build_runtime(
            {
                CONF_MODEL: model.name,
                CONF_DEVICE_ID: "bench",
            }
        )
        sensor_keys = set(implemented_sensor_keys(runtime))
        disposition = runtime.diagnostic_value("support_disposition")

        checked.append(model.name)
        assert runtime.protocol_ready is False, model.name
        assert runtime.session_ready is False, model.name
        assert (
            runtime.diagnostic_value("runtime_transport_state") == "diagnostic_only"
        ), model.name
        assert "recognized; setup=" in disposition, model.name
        assert "diagnostic_only" in disposition, model.name
        assert "command_protocol_pending" in disposition, model.name
        apk_profile_checked.append(model.name)
        assert "apk_profile_ready" in disposition, model.name
        assert expected_profile_keys[model.family.value] <= sensor_keys, model.name
        assert "support_disposition" in sensor_keys, model.name
        assert command_button_features(runtime) == (), model.name
        assert command_light_features(runtime) == (), model.name
        assert command_number_features(runtime) == (), model.name
        assert command_scene_features(runtime) == (), model.name
        assert command_select_features(runtime) == (), model.name
        assert command_switch_features(runtime) == (), model.name

    assert len(checked) == 57
    assert len(apk_profile_checked) == 57
    assert apk_profile_checked[0] == "Car Lights"
    assert apk_profile_checked[-1] == "SP802E"


def test_recognized_ble_setup_entries_stay_diagnostic_without_transport() -> None:
    """Unported BLE setup entries load diagnostics without guessed BLE writes."""
    catalog = default_catalog()
    checked: list[str] = []
    uuid_pending_checked: list[str] = []

    for model in catalog.user_facing_models():
        if model.support_level.value != "recognized":
            continue
        if TransportKind.BLE not in model.transports:
            continue

        setup = manual_setup_entry_data(
            model,
            transport=TRANSPORT_BLE,
            address="AA:BB:CC:DD:EE:FF",
        )
        runtime = build_runtime(setup.data)
        kind = _attach_runtime_transports(
            None,
            dict(runtime.entry_data),
            runtime,
            notification_callback=lambda data: None,
            mesh_notification_callback=lambda data: None,
        )

        checked.append(model.name)
        assert kind is None, model.name
        assert runtime.protocol_ready is False, model.name
        assert runtime.session_ready is False, model.name
        assert runtime.diagnostic_value("configured_transport") == TRANSPORT_BLE
        assert (
            runtime.diagnostic_value("runtime_transport_state") == "diagnostic_only"
        ), model.name
        assert runtime.diagnostic_value("support_level") == "recognized"
        disposition = runtime.diagnostic_value("support_disposition")
        uuid_pending_checked.append(model.name)
        assert "ble_uuid_binding_pending" in disposition, model.name
        assert command_button_features(runtime) == (), model.name
        assert command_light_features(runtime) == (), model.name
        assert command_number_features(runtime) == (), model.name
        assert command_select_features(runtime) == (), model.name
        assert command_switch_features(runtime) == (), model.name

    assert len(checked) == 30
    assert len(uuid_pending_checked) == 30
    assert uuid_pending_checked[0] == "Car Lights"
    assert uuid_pending_checked[-1] == "SP802E"


def test_setup_helper_attaches_zengge_mesh_without_command_session() -> None:
    """RG4 setup gets a mesh transport holder without command entities."""
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_MESH_UUID: 0x0211,
            CONF_MESH_NODE_ID: 0x11,
            CONF_MESH_NODE_TYPE: 2,
        }
    )

    kind = _attach_runtime_transports(
        None,
        dict(runtime.entry_data),
        runtime,
        notification_callback=lambda data: None,
        mesh_notification_callback=lambda data: None,
    )

    assert kind == "ble_mesh"
    assert runtime.session_ready is False
    assert runtime.lan_transport_ready is False
    assert runtime.mesh_transport_ready is True
    assert runtime.diagnostic_value("runtime_transport_state") == "mesh_transport"
    assert runtime.transport.__class__.__name__ == "UniLEDZenggeMeshTransport"
    assert command_light_features(runtime) == ()
    assert {feature.key for feature in command_button_features(runtime)} == {
        "refresh"
    }
    assert command_number_features(runtime) == ()
    assert command_scene_features(runtime) == ()
    assert command_select_features(runtime) == ()
    assert command_switch_features(runtime) == ()


def test_setup_helper_attaches_lan_transport_holder_without_command_session() -> None:
    """LAN setup stores the host transport while command entities stay closed."""
    runtime = build_runtime(
        {
            CONF_MODEL: "SP802E",
            CONF_HOST: "192.168.1.50",
            CONF_TRANSPORT: TRANSPORT_LAN,
        }
    )

    kind = _attach_runtime_transports(
        None,
        dict(runtime.entry_data),
        runtime,
        notification_callback=lambda data: None,
        mesh_notification_callback=lambda data: None,
    )

    assert kind == "lan"
    assert runtime.protocol_ready is False
    assert runtime.session_ready is False
    assert runtime.lan_transport_ready is True
    assert runtime.mesh_transport_ready is False
    assert runtime.diagnostic_value("runtime_transport_state") == "lan_transport_holder"
    assert runtime.transport.__class__.__name__ == "UniLEDLANTransport"
    assert runtime.state.diagnostics["lan_transport_ready"] is True
    assert runtime.state.diagnostics["lan_manual_host_configured"] is True
    assert command_button_features(runtime) == ()
    assert command_light_features(runtime) == ()

    diagnostics = runtime_diagnostics(runtime)

    assert diagnostics["runtime"]["lan_transport_ready"] is True
    assert diagnostics["runtime"]["transport_attached"] is True
    assert (
        diagnostics["runtime"]["runtime_transport_state"] == "lan_transport_holder"
    )

    try:
        asyncio.run(runtime.transport.send(b"\x00"))
    except TransportError as ex:
        assert "LAN command protocol is not mapped" in str(ex)
    else:
        raise AssertionError("LAN transport should refuse guessed command payloads")

    transport = runtime.transport
    asyncio.run(runtime.async_close())

    assert transport.closed is True
    assert runtime.lan_transport_ready is False


def test_setup_helper_attaches_sp541e_lan_command_session() -> None:
    """SP541E LAN uses the verified SPNet/SPTech command path."""
    runtime = build_runtime(
        {
            CONF_MODEL: "SP541E",
            CONF_HOST: "192.0.2.92",
            CONF_TRANSPORT: TRANSPORT_LAN,
        }
    )

    kind = _attach_runtime_transports(
        None,
        dict(runtime.entry_data),
        runtime,
        notification_callback=lambda data: None,
        mesh_notification_callback=lambda data: None,
    )

    assert kind == "lan"
    assert runtime.protocol_ready is True
    assert runtime.session_ready is True
    assert runtime.lan_transport_ready is True
    assert runtime.mesh_transport_ready is False
    assert runtime.diagnostic_value("runtime_transport_state") == "command_session"
    assert runtime.diagnostic_value("lan_host_setup_mode") == "discovery_ready"
    assert runtime.diagnostic_value("lan_profile").startswith(
        "banlanx_custom_5xx; discovery_ready; command_protocol_known"
    )
    assert runtime.transport.__class__.__name__ == "UniLEDLANTransport"
    assert runtime.protocol.__class__.__name__ == "SPTechLANProtocol"
    assert runtime.state.diagnostics["lan_transport_ready"] is True
    assert runtime.state.diagnostics["lan_protocol"] == "sptech"

    transport = runtime.transport
    asyncio.run(runtime.async_close())

    assert transport.closed is True
    assert runtime.lan_transport_ready is False


def test_setup_helper_attaches_lan_transport_for_all_lan_family_shapes() -> None:
    """LAN-only, BLE+LAN, optional-cloud, and protocol-backed LAN shapes work."""
    cases = {
        "SP801E": ("banlanx_network", False),
        "SP802E": ("banlanx_network", False),
        "FT001": ("fish_tank", False),
        "SP547E": ("banlanx_custom_5xx", True),
    }

    for model_name, (family, protocol_ready) in cases.items():
        runtime = build_runtime(
            {
                CONF_MODEL: model_name,
                CONF_HOST: "192.0.2.56",
                CONF_TRANSPORT: TRANSPORT_LAN,
            }
        )

        kind = _attach_runtime_transports(
            None,
            dict(runtime.entry_data),
            runtime,
            notification_callback=lambda data: None,
            mesh_notification_callback=lambda data: None,
        )

        assert kind == "lan", model_name
        assert runtime.model.family.value == family
        assert runtime.protocol_ready is protocol_ready
        assert runtime.session_ready is False
        assert runtime.lan_transport_ready is True
        assert runtime.mesh_transport_ready is False
        assert (
            runtime.diagnostic_value("runtime_transport_state")
            == "lan_transport_holder"
        )
        assert runtime.lan_profile is not None
        assert runtime.lan_profile.requires_manual_host is True
        assert runtime.state.diagnostics["lan_transport_ready"] is True
        assert runtime.state.diagnostics["lan_manual_host_configured"] is True
        assert command_button_features(runtime) == ()
        assert command_light_features(runtime) == ()
        assert command_number_features(runtime) == ()
        assert command_select_features(runtime) == ()
        assert command_switch_features(runtime) == ()

        asyncio.run(runtime.async_close())
        assert runtime.lan_transport_ready is False


def test_runtime_resolves_custom_5xx_as_6xx_style_protocol() -> None:
    """Custom 5xx models are protocol-backed with SP6xx-style controls."""
    runtime = build_runtime({CONF_MODEL: "SP530E", CONF_DEVICE_ID: "bench"})

    assert runtime.protocol_ready is True
    assert runtime.diagnostic_value("protocol_family") == "banlanx_custom_5xx"
    assert runtime.diagnostic_value("support_level") == "limited"

    runtime.attach_transport(RecordingTransport())
    runtime.state.diagnostics["light_type"] = 0x86

    assert "main_light" in {feature.key for feature in command_light_features(runtime)}
    assert "effect" in {feature.key for feature in command_select_features(runtime)}
    assert "onoff_pixels" in {
        feature.key for feature in command_number_features(runtime)
    }
    assert "coexistence" in {
        feature.key for feature in command_switch_features(runtime)
    }
    assert effect_command_value(runtime, "Dynamic Color - Rainbow") == (0x03, 0x01)


def test_runtime_rejects_missing_unknown_or_filtered_models() -> None:
    """Runtime setup fails visibly for unsafe model choices."""
    cases = (
        ({}, CONF_MODEL, "required"),
        ({CONF_MODEL: "NOPE"}, CONF_MODEL, "unknown_model"),
        ({CONF_MODEL: "TEST"}, CONF_MODEL, "unknown_model"),
    )
    for data, expected_field, reason in cases:
        try:
            build_runtime(data)
        except RuntimeSetupError as ex:
            assert ex.field == expected_field
            assert ex.reason == reason
        else:
            raise AssertionError(f"{data} should not build a runtime")


def test_implemented_sensor_keys_are_catalog_diagnostics() -> None:
    """Only implemented diagnostic sensors are exposed by the first platform."""
    runtime = build_runtime({CONF_MODEL: "SP530E", CONF_DEVICE_ID: "kitchen"})

    keys = implemented_sensor_keys(runtime)

    assert "catalog_model" in keys
    assert "catalog_model_id" in keys
    assert "catalog_parent_id" in keys
    assert "catalog_connect_caps" in keys
    assert "catalog_connect_capabilities" in keys
    assert "catalog_spec_functions" in keys
    assert "catalog_spec_function_bits" in keys
    assert "catalog_color_cap" in keys
    assert "catalog_color_capabilities" in keys
    assert "catalog_feature_count" in keys
    assert "catalog_feature_keys" in keys
    assert "catalog_feature_summary" in keys
    assert "catalog_variant_count" in keys
    assert "catalog_variant_ids" in keys
    assert "protocol_family" in keys
    assert "support_level" in keys
    assert "support_disposition" in keys
    assert "support_blocker_count" in keys
    assert "support_blockers" in keys
    assert "transport" in keys
    assert "configured_transport" in keys
    assert "runtime_transport_state" in keys
    assert "last_refresh_result" in keys
    assert "protocol_evidence_profile" in keys
    assert "protocol_evidence_kind" in keys
    assert "protocol_evidence_hint_count" in keys
    assert "ble_profile" in keys
    assert "ble_uuid_binding_status" in keys
    assert "ble_known_service_uuid_count" in keys
    assert "ble_uuid_pool_count" in keys
    assert "ble_unbound_uuid_candidate_count" in keys
    assert "ble_legacy_uuid_candidate_count" in keys
    assert "ble_plugin_method_count" in keys
    assert "ble_plugin_argument_count" in keys
    assert "ble_plugin_result_field_count" in keys
    assert "ble_plugin_contract_hint_count" in keys
    assert "ble_plugin_channel_count" in keys
    assert "ble_protocol_gap_count" in keys
    assert "custom_effect_slot" in keys
    assert "main_light" not in keys


def test_catalog_feature_metadata_is_exposed_for_selected_model() -> None:
    """Selected runtime diagnostics expose APK extra-feature metadata."""
    runtime = build_runtime({CONF_MODEL: "SP530E", CONF_DEVICE_ID: "kitchen"})
    diagnostics = runtime_diagnostics(runtime)["model"]

    assert runtime.diagnostic_value("catalog_feature_count") == 5
    assert runtime.diagnostic_value("catalog_feature_keys") == (
        "customFeature, maxPixelChannels, musicFeature, otherFeature, settingFeature"
    )
    assert runtime.diagnostic_value("catalog_feature_summary") == (
        "customFeature=1; maxPixelChannels=3600; musicFeature=3; "
        "otherFeature=1; settingFeature=1"
    )
    assert runtime.diagnostic_value("catalog_variant_ids") == "78"
    assert diagnostics["feature_keys"] == [
        "customFeature",
        "maxPixelChannels",
        "musicFeature",
        "otherFeature",
        "settingFeature",
    ]
    assert diagnostics["features"] == {
        "customFeature": 1,
        "maxPixelChannels": 3600,
        "musicFeature": 3,
        "otherFeature": 1,
        "settingFeature": 1,
    }


def test_support_disposition_summarizes_each_integration_shape() -> None:
    """Runtime support diagnostics make every support state explicit."""
    cases = {
        "SP601E": (
            "limited; setup=ble; command_protocol_ready; state_refresh_ready; "
            "old_uniled_parity"
        ),
        "SP530E": (
            "limited; setup=ble,lan; command_protocol_ready; "
            "state_refresh_ready; sp6xx_style_ble_commands; "
            "lan_frame_pending; cloud_optional; account_token_schema_pending; "
            "request_signing_headers_pending; region_reauth_contract_pending; "
            "raw_command_json_envelope_pending; "
            "device_bind_ownership_lifecycle_pending"
        ),
        "SP541E": (
            "limited; setup=ble,lan; command_protocol_ready; "
            "state_refresh_ready; sp6xx_style_ble_commands; "
            "lan_frame_ready; cloud_optional; account_token_schema_pending; "
            "request_signing_headers_pending; region_reauth_contract_pending; "
            "raw_command_json_envelope_pending; "
            "device_bind_ownership_lifecycle_pending"
        ),
        "SP603E": (
            "limited; setup=ble; command_protocol_ready; state_refresh_ready; "
            "apk_protocol_inference"
        ),
        "RG4": (
            "limited; setup=ble_mesh; zengge_mesh_limited; pair_required; "
            "node_commands_guarded; panel_status_sensors; "
            "mesh_remote_event_parser_pending; mesh_provisioning_frame_pending; "
            "mesh_group_management_pending; mesh_node_management_controls_pending"
        ),
        "SP660E": (
            "recognized; setup=ble; diagnostic_only; "
            "command_protocol_pending; apk_profile_ready; "
            "ble_uuid_binding_pending; scene_command_envelope_pending; "
            "scene_status_parser_pending; scene_lfx_frame_pending; "
            "scene_timer_frame_pending; scene_favorite_frame_pending; "
            "scene_diy_frame_pending; scene_white_brightness_parser_pending"
        ),
        "SP310E": (
            "recognized; setup=ble_mesh; diagnostic_only; "
            "command_protocol_pending; apk_profile_ready; mesh_frame_pending; "
            "scene_command_envelope_pending; scene_status_parser_pending; "
            "scene_lfx_frame_pending; scene_timer_frame_pending; "
            "scene_favorite_frame_pending; scene_diy_frame_pending; "
            "scene_white_brightness_parser_pending; "
            "firmware_v1_1_required; provisioning_frame_pending; "
            "scene_mesh_routing_pending"
        ),
        "SP701E": (
            "recognized; setup=ble; diagnostic_only; "
            "command_protocol_pending; apk_profile_ready; "
            "ble_uuid_binding_pending; car_light_ble_opcode_pending; "
            "car_light_status_parser_pending; car_light_zone_command_pending; "
            "car_light_trigger_packet_pending; "
            "car_light_subdevice_binding_pending; car_light_password_flow_pending"
        ),
        "SP801E": (
            "recognized; setup=lan; diagnostic_only; "
            "command_protocol_pending; apk_profile_ready; lan_frame_pending; "
            "network_discovery_pending; network_socket_frame_pending; "
            "network_dns_sd_service_pending; network_artnet_config_pending; "
            "network_playlist_packet_pending; network_dxf_import_pending; "
            "network_panel_layout_pending"
        ),
        "SP802E": (
            "recognized; setup=ble,lan; diagnostic_only; "
            "command_protocol_pending; apk_profile_ready; "
            "ble_uuid_binding_pending; lan_frame_pending; "
            "network_discovery_pending; network_socket_frame_pending; "
            "network_dns_sd_service_pending; network_lfx_packet_pending; "
            "network_lfx_status_parser_pending; network_panel_layout_pending; "
            "network_matrix_music_pending"
        ),
        "FT001": (
            "recognized; setup=ble,lan; diagnostic_only; "
            "command_protocol_pending; apk_profile_ready; "
            "ble_uuid_binding_pending; lan_frame_pending; "
            "fish_tank_ble_opcode_pending; fish_tank_status_parser_pending; "
            "fish_tank_lan_refresh_pending; fish_tank_timer_frame_pending; "
            "fish_tank_favorite_frame_pending; fish_tank_effect_packet_pending; "
            "fish_tank_brightness_parser_pending; cloud_optional; "
            "account_token_schema_pending; request_signing_headers_pending; "
            "region_reauth_contract_pending; raw_command_json_envelope_pending; "
            "device_bind_ownership_lifecycle_pending"
        ),
    }

    for model_name, expected in cases.items():
        runtime = build_runtime({CONF_MODEL: model_name, CONF_DEVICE_ID: "bench"})
        expected_blockers = tuple(
            token
            for token in expected.split("; ")
            if token.endswith("_pending")
            or token.endswith("_required")
            or token.startswith("accessory_dependency=")
        )
        expected_blocker_text = (
            "none" if not expected_blockers else ", ".join(expected_blockers)
        )

        assert runtime.diagnostic_value("support_disposition") == expected
        assert runtime.diagnostic_value("support_blocker_count") == len(
            expected_blockers
        )
        assert runtime.diagnostic_value("support_blockers") == expected_blocker_text
        assert runtime_diagnostics(runtime)["model"]["support_disposition"] == expected
        assert runtime_diagnostics(runtime)["model"]["support_blockers"] == list(
            expected_blockers
        )


def test_legacy_uniled_parity_profile_exposes_ported_old_command_surface() -> None:
    """Diagnostics make the old-UniLED parity boundary explicit."""
    cases = {
        "SP601E": (
            "banlanx_601; old_uniled=custom_components/uniled/lib/ble/"
            "banlanx_601.py; commands=13; parsers=4; stubbed=1; gaps=1"
        ),
        "SP602E": (
            "banlanx_60x; old_uniled=custom_components/uniled/lib/ble/"
            "banlanx_60x.py; commands=13; parsers=4; stubbed=1; gaps=1"
        ),
        "SP611E": (
            "banlanx_v2; old_uniled=custom_components/uniled/lib/ble/"
            "banlanx2.py; commands=14; parsers=4; stubbed=0; gaps=0"
        ),
        "SP614E": (
            "banlanx_v3; old_uniled=custom_components/uniled/lib/ble/"
            "banlanx3.py; commands=12; parsers=4; stubbed=0; gaps=0"
        ),
        "SP630E": (
            "banlanx_6xx; old_uniled=custom_components/uniled/lib/ble/"
            "banlanx_6xx.py; commands=22; parsers=6; stubbed=0; gaps=0"
        ),
        "SP107E": (
            "legacy_led_chord; old_uniled=custom_components/uniled/lib/ble/"
            "led_chord.py; commands=11; parsers=4; stubbed=4; gaps=1"
        ),
        "SP110E": (
            "legacy_led_hue; old_uniled=custom_components/uniled/lib/ble/"
            "led_hue.py; commands=10; parsers=4; stubbed=2; gaps=1"
        ),
    }

    for model_name, expected in cases.items():
        runtime = build_runtime({CONF_MODEL: model_name, CONF_DEVICE_ID: "bench"})
        profile = runtime_diagnostics(runtime)["model"][
            "legacy_uniled_parity_profile"
        ]

        assert runtime.diagnostic_value("legacy_uniled_parity_profile") == expected
        assert profile is not None
        assert profile["family"] == runtime.model.family.value
        assert len(profile["command_builders"]) == runtime.diagnostic_value(
            "legacy_uniled_command_count"
        )
        assert len(profile["status_parser_hints"]) == runtime.diagnostic_value(
            "legacy_uniled_status_parser_count"
        )
        assert len(profile["stubbed_builders"]) == runtime.diagnostic_value(
            "legacy_uniled_stubbed_command_count"
        )
        assert len(profile["gap_hints"]) == runtime.diagnostic_value(
            "legacy_uniled_parity_gap_count"
        )
        assert "state_query" in profile["command_builders"]
        assert "power" in profile["command_builders"]

    sp601 = runtime_diagnostics(
        build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    )["model"]["legacy_uniled_parity_profile"]
    assert sp601["stubbed_builders"] == ["scene_save"]
    assert "empty old-UniLED stub" in sp601["gap_hints"][0]

    custom = build_runtime({CONF_MODEL: "SP530E", CONF_DEVICE_ID: "bench"})
    assert custom.diagnostic_value("legacy_uniled_parity_profile") is None
    assert custom.diagnostic_value("legacy_uniled_command_count") is None
    assert runtime_diagnostics(custom)["model"]["legacy_uniled_parity_profile"] is None


def test_protocol_evidence_profile_explains_command_backed_models() -> None:
    """Diagnostics distinguish exact parity from APK family inference."""
    cases = {
        "SP601E": "old_uniled_exact",
        "SP107E": "old_uniled_exact",
        "SP110E": "old_uniled_exact",
        "SP530E": "sp6xx_style_ble_commands",
        "SP603E": "apk_catalog_family_inference",
    }

    for model_name, expected_kind in cases.items():
        runtime = build_runtime({CONF_MODEL: model_name, CONF_DEVICE_ID: "bench"})
        diagnostics = runtime_diagnostics(runtime)["model"][
            "protocol_evidence_profile"
        ]

        assert runtime.diagnostic_value("protocol_evidence_kind") == expected_kind
        assert runtime.diagnostic_value("protocol_evidence_profile").startswith(
            f"{runtime.model.family.value}; evidence={expected_kind}; "
        )
        assert diagnostics is not None
        assert diagnostics["kind"] == expected_kind
        assert diagnostics["family"] == runtime.model.family.value
        assert diagnostics["basis"]
        assert len(diagnostics["evidence_hints"]) == runtime.diagnostic_value(
            "protocol_evidence_hint_count"
        )
        assert any("model_id=" in hint for hint in diagnostics["evidence_hints"])

    recognized = build_runtime({CONF_MODEL: "SP660E", CONF_DEVICE_ID: "bench"})
    assert recognized.diagnostic_value("protocol_evidence_profile") is None
    assert runtime_diagnostics(recognized)["model"]["protocol_evidence_profile"] is None


def test_sp6xx_custom_effect_slot_diagnostic_reads_old_uniled_status_byte() -> None:
    """SP6xx/custom 5xx expose parsed DIY/custom slot status as diagnostics."""
    runtime = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})

    assert runtime.diagnostic_value("custom_effect_slot") is None

    channel_state(runtime).extra["diy_mode"] = 7

    assert runtime.diagnostic_value("custom_effect_slot") == 7
    assert "custom_effect_slot" in implemented_sensor_keys(runtime)

    legacy_runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})

    assert legacy_runtime.diagnostic_value("custom_effect_slot") is None


def test_sp630e_surface_profile_runtime_diagnostics() -> None:
    """SP6xx and custom 5xx expose APK /sp630e surface evidence."""
    runtime = build_runtime({CONF_MODEL: "SP530E", CONF_DEVICE_ID: "bench"})

    assert runtime.diagnostic_value("sp630e_profile") == (
        "banlanx_custom_5xx; package=packages/sp630e; surfaces=23; "
        "routes=16; favorite_limits=4; timer_limit=5; music_assets=19; "
        "network_hints=12; remote_hints=7; motor_hints=6; methods=8; "
        "data=8; native_lfx=27; gaps=7; package_assets=217; "
        "legacy_ble_protocol_known"
    )
    assert runtime.diagnostic_value("sp630e_route_count") == 16
    assert runtime.diagnostic_value("sp630e_control_surface_count") == 23
    assert runtime.diagnostic_value("sp630e_favorite_limit_hint_count") == 4
    assert runtime.diagnostic_value("sp630e_timer_limit") == 5
    assert runtime.diagnostic_value("sp630e_timer_hint_count") == 4
    assert runtime.diagnostic_value("sp630e_music_asset_count") == 19
    assert runtime.diagnostic_value("sp630e_network_hint_count") == 12
    assert runtime.diagnostic_value("sp630e_remote_hint_count") == 7
    assert runtime.diagnostic_value("sp630e_motor_hint_count") == 6
    assert runtime.diagnostic_value("sp630e_app_method_count") == 8
    assert runtime.diagnostic_value("sp630e_data_model_hint_count") == 8
    assert runtime.diagnostic_value("sp630e_native_lfx_hint_count") == 27
    assert runtime.diagnostic_value("sp630e_protocol_gap_count") == 7
    assert runtime.diagnostic_value("sp630e_apk_asset_evidence_count") == 46
    assert runtime.diagnostic_value("sp630e_apk_package_asset_count") == 217
    assert runtime.diagnostic_value("sp630e_apk_string_evidence_count") == 10
    assert "sp630e_profile" in implemented_sensor_keys(runtime)
    assert "sp630e_timer_limit" in implemented_sensor_keys(runtime)
    assert "sp630e_native_lfx_hint_count" in implemented_sensor_keys(runtime)

    diagnostics = runtime_diagnostics(runtime)["model"]["sp630e_profile"]
    assert diagnostics["package"] == "packages/sp630e"
    assert diagnostics["package_asset_count"] == 217
    assert diagnostics["timer_limit"] == 5
    assert "/sp630e/diy/fav" in diagnostics["route_hints"]
    assert "You can only add up to 5 timers!" in diagnostics["timer_hints"]
    assert (
        "There may be some deviations in timing, and once the device is "
        "powered off, all timers will be deleted."
    ) in diagnostics["timer_hints"]
    assert "favoriteLightingEffectIds" in diagnostics["data_model_hints"]
    assert "liblfx.so" in diagnostics["native_lfx_hints"]
    assert "Music_VuMeter" in diagnostics["native_lfx_hints"]
    assert any("remote" in hint for hint in diagnostics["remote_hints"])
    assert any("not proven" in gap for gap in diagnostics["protocol_gap_hints"])
    assert any("liblfx.so" in gap for gap in diagnostics["protocol_gap_hints"])

    sp630 = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})
    assert sp630.diagnostic_value("sp630e_profile").startswith(
        "banlanx_6xx; package=packages/sp630e;"
    )

    legacy = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    assert legacy.diagnostic_value("sp630e_profile") is None


def test_banlanx3_diy_diagnostics_read_old_uniled_status_metadata() -> None:
    """BanlanX3 exposes parsed DIY effect metadata as diagnostics only."""
    runtime = build_runtime({CONF_MODEL: "SP614E", CONF_DEVICE_ID: "bench"})

    assert runtime.diagnostic_value("diy_effect_type") is None
    assert runtime.diagnostic_value("diy_color_count") is None

    channel_state(runtime).extra.update(
        {
            "diy_effect_type": 0xAA,
            "diy_color_count": 0x03,
        }
    )

    assert runtime.diagnostic_value("diy_effect_type") == 0xAA
    assert runtime.diagnostic_value("diy_color_count") == 0x03
    assert "diy_effect_type" in implemented_sensor_keys(runtime)
    assert "diy_color_count" in implemented_sensor_keys(runtime)

    v2_runtime = build_runtime({CONF_MODEL: "SP617E", CONF_DEVICE_ID: "bench"})
    channel_state(v2_runtime).extra.update(
        {
            "diy_effect_type": 0xAA,
            "diy_color_count": 0x03,
        }
    )

    assert v2_runtime.diagnostic_value("diy_effect_type") is None
    assert v2_runtime.diagnostic_value("diy_color_count") is None


def test_runtime_diagnostics_hex_encodes_binary_parser_records() -> None:
    """Home Assistant diagnostics serialize raw parser bytes safely."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    assert runtime.protocol is not None
    ch1 = bytes([1, 0x02, 0x03, 100, 5, 6, 1, 10, 20, 30, 0x10])
    ch2 = bytes([0, 0x03, 0x04, 200, 7, 8, 0, 40, 50, 60, 0x09])
    timer = bytes.fromhex("01 02 03 04 05 06 07")

    state = runtime.protocol.parse_status(
        ch1 + ch2 + bytes([1]) + timer + bytes([1])
    )
    apply_runtime_state(runtime, state)

    diagnostics = runtime_diagnostics(runtime)

    assert diagnostics["diagnostics"]["trailing_bytes"] == "010102030405060701"
    assert diagnostics["diagnostics"]["timer_records"] == ["01020304050607"]
    assert diagnostics["diagnostics"]["scene_loop"] is True


def test_banlanx2_timer_count_diagnostic_reads_old_uniled_status_tail() -> None:
    """BanlanX2 timer status remains diagnostic-only."""
    runtime = build_runtime({CONF_MODEL: "SP621E", CONF_DEVICE_ID: "bench"})
    assert runtime.protocol is not None
    timer = bytes.fromhex("00 01 6a 00 93 a8 01")
    data = bytes.fromhex(
        "01 00 0e 02 61 0a 1e ff 00 00 01 10 "
        "09 04 0b 14 1a 32 37 50 53 73 01"
    ) + timer

    assert runtime.diagnostic_value("timer_count") is None

    apply_runtime_state(runtime, runtime.protocol.parse_status(data))
    diagnostics = runtime_diagnostics(runtime)

    assert runtime.diagnostic_value("timer_count") == 1
    assert "timer_count" in implemented_sensor_keys(runtime)
    assert diagnostics["diagnostics"]["timer_header"] == "09040b141a3237505373"
    assert diagnostics["diagnostics"]["timer_records"] == ["00016a0093a801"]


def test_command_light_features_require_attached_session() -> None:
    """Command lights are exposed only after a command session exists."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})

    assert command_light_features(runtime) == ()

    runtime.attach_transport(RecordingTransport())
    features = command_light_features(runtime)

    assert [feature.key for feature in features] == [
        "main_light",
        "output_1_light",
        "output_2_light",
    ]
    assert [feature.channel for feature in features] == [0, 1, 2]

    runtime = build_runtime({CONF_MODEL: "SP602E", CONF_DEVICE_ID: "bench"})
    assert command_light_features(runtime) == ()

    runtime.attach_transport(RecordingTransport())
    features = command_light_features(runtime)

    assert len(features) == 5
    assert [feature.channel for feature in features] == list(range(5))
    assert features[0].key == "main_light"
    assert features[-1].key == "output_4_light"

    runtime = build_runtime({CONF_MODEL: "SP608E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    features = command_light_features(runtime)

    assert len(features) == 9
    assert [feature.channel for feature in features] == list(range(9))
    assert features[-1].key == "output_8_light"


def test_command_scene_features_require_attached_legacy_session() -> None:
    """Old-UniLED scene recall scenes are exposed only after a command session."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})

    assert command_scene_features(runtime) == ()

    runtime.attach_transport(RecordingTransport())
    features = command_scene_features(runtime)

    assert len(features) == 9
    assert features[0].key == "scene_0"
    assert features[0].name == "Scene 1"
    assert features[0].channel == 0
    assert features[0].enabled_by_default is False
    assert features[0].implementation_hint == "legacy_uniled"
    assert features[-1].key == "scene_8"
    assert features[-1].name == "Scene 9"
    assert features[-1].channel == 8

    scene_runtime = build_runtime({CONF_MODEL: "SP660E", CONF_DEVICE_ID: "bench"})
    assert command_scene_features(scene_runtime) == ()


def test_command_button_features_require_refresh_transport() -> None:
    """Refresh buttons are exposed only after a refresh transport is attached."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})

    assert command_button_features(runtime) == ()

    runtime.attach_transport(RecordingTransport())
    features = command_button_features(runtime)

    assert len(features) == 1
    assert features[0].key == "refresh"
    assert features[0].platform.value == "button"
    assert features[0].implemented is True

    network = build_runtime({CONF_MODEL: "SP802E", CONF_DEVICE_ID: "panel"})

    assert command_button_features(network) == ()


def test_apply_light_command_state_updates_normalized_channel() -> None:
    """Successful light commands update normalized runtime state."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    channel = apply_light_command_state(
        runtime,
        power=True,
        brightness=128,
        rgb=(1, 2, 3),
    )

    assert runtime.state.available is True
    assert channel.channel_id == 0
    assert channel.power is True
    assert channel.brightness == 128
    assert channel.rgb == (1, 2, 3)
    assert runtime.state.channels[1].power is True
    assert runtime.state.channels[1].brightness == 128
    assert runtime.state.channels[1].rgb == (1, 2, 3)
    assert runtime.state.channels[2].power is True
    assert runtime.state.channels[2].brightness == 128
    assert runtime.state.channels[2].rgb == (1, 2, 3)

    apply_light_command_state(runtime, power=False)

    assert runtime.state.channels[0].power is False
    assert runtime.state.channels[1].power is False
    assert runtime.state.channels[2].power is False

    output = apply_light_command_state(
        runtime,
        channel=1,
        power=True,
        brightness=64,
        rgb=(9, 8, 7),
    )

    assert output.channel_id == 1
    assert runtime.state.channels[1].power is True
    assert runtime.state.channels[1].brightness == 64
    assert runtime.state.channels[1].rgb == (9, 8, 7)


def test_legacy_set_state_service_uses_direct_session_commands() -> None:
    """The old light service shim sends through the runtime command session."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)

    changed = asyncio.run(
        async_apply_legacy_set_state_service(
            runtime,
            {
                "power": True,
                "rgb_color": (1, 2, 3),
                "brightness": 128,
                "effect_speed": 6,
                "effect_length": 7,
                "effect_direction": "off",
            },
            channel=1,
        )
    )

    state = channel_state(runtime, 1)
    assert changed is True
    assert state.power is True
    assert state.brightness == 128
    assert state.rgb == (1, 2, 3)
    assert state.effect_speed == 6
    assert state.effect_length == 7
    assert state.effect_direction is False
    assert len(transport.sent) == 5


def test_legacy_set_state_service_fans_out_sp601_aggregate_light_only() -> None:
    """Aggregate SP601E service calls do not leak output-scoped controls."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)

    changed = asyncio.run(
        async_apply_legacy_set_state_service(
            runtime,
            {
                "rgb_color": (1, 2, 3),
                "brightness": 128,
                "effect_speed": 6,
                "effect_length": 7,
                "effect_direction": "off",
                "sensitivity": 8,
            },
        )
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("aa 29 05 00 01 02 03 80"), False),
        (bytes.fromhex("aa 29 05 01 01 02 03 80"), False),
    ]
    assert channel_state(runtime).brightness == 128
    assert channel_state(runtime).rgb == (1, 2, 3)
    assert channel_state(runtime, 1).brightness == 128
    assert channel_state(runtime, 1).rgb == (1, 2, 3)
    assert channel_state(runtime, 2).brightness == 128
    assert channel_state(runtime, 2).rgb == (1, 2, 3)
    assert control_value(runtime, "effect_speed") is None
    assert control_value(runtime, "effect_direction") is None


def test_legacy_set_state_service_power_off_suppresses_followups() -> None:
    """Power-off service calls match old UniLED's off-first behavior."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)

    changed = asyncio.run(
        async_apply_legacy_set_state_service(
            runtime,
            {"power": False, "brightness": 128, "rgb_color": (4, 5, 6)},
        )
    )

    state = channel_state(runtime)
    assert changed is True
    assert state.power is False
    assert state.brightness is None
    assert state.rgb is None
    assert runtime.state.channels[1].power is False
    assert runtime.state.channels[2].power is False
    assert transport.sent == [
        (bytes.fromhex("aa 22 02 00 00"), False),
        (bytes.fromhex("aa 22 02 01 00"), False),
    ]


def test_legacy_set_state_service_skips_sp6xx_sound_brightness() -> None:
    """SP6xx sound modes keep old UniLED's no-brightness-packet behavior."""
    for model_name, light_type in {"SP638E": 0x06, "SP530E": 0x86}.items():
        runtime = build_runtime({CONF_MODEL: model_name, CONF_DEVICE_ID: "bench"})
        transport = RecordingTransport()
        runtime.attach_transport(transport)
        runtime.state.diagnostics["light_type"] = light_type

        for mode in (0x05, 0x06):
            channel = channel_state(runtime)
            channel.light_mode_number = mode
            channel.brightness = 32
            transport.sent.clear()

            changed = asyncio.run(
                async_apply_legacy_set_state_service(runtime, {"brightness": 128})
            )

            assert changed is False
            assert transport.sent == []
            assert channel_state(runtime).brightness == 0xFF

        channel_state(runtime).light_mode_number = 0x01
        transport.sent.clear()

        changed = asyncio.run(
            async_apply_legacy_set_state_service(runtime, {"brightness": 128})
        )

        assert changed is True
        assert transport.sent == [
            (bytes.fromhex("53 51 00 01 00 02 00 80"), False)
        ]
        assert channel_state(runtime).brightness == 128


def test_legacy_set_state_service_routes_sp6xx_white_mode_brightness() -> None:
    """SP6xx white/CCT modes use the old UniLED 0x51 white selector."""
    runtime = build_runtime({CONF_MODEL: "SP639E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    runtime.state.diagnostics["light_type"] = 0x08
    state = channel_state(runtime)
    state.light_mode_number = 0x02

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"brightness": 128})
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("53 51 00 01 00 02 01 80"), False)
    ]
    assert state.brightness == 128
    assert state.extra["white_level"] == 128

    state.light_mode_number = 0x06
    state.brightness = 32
    state.extra.clear()
    transport.sent.clear()

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"brightness": 64})
    )

    assert changed is False
    assert transport.sent == []
    assert state.brightness == 0xFF
    assert "white_level" not in state.extra


def test_legacy_set_state_service_keeps_sp6xx_dynamic_rgb_brightness_free() -> None:
    """SP6xx non-static RGB tuning does not append a brightness frame."""
    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    state = channel_state(runtime)
    state.light_mode_number = 0x01
    state.brightness = 32

    changed = asyncio.run(
        async_apply_legacy_set_state_service(
            runtime,
            {"rgb_color": (1, 2, 3), "brightness": 128},
        )
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("53 52 00 01 00 04 01 02 03 80"), False),
    ]
    assert state.rgb == (1, 2, 3)
    assert state.brightness == 128

    for mode in (0x03, 0x05):
        state.light_mode_number = mode
        state.brightness = 32
        transport.sent.clear()

        changed = asyncio.run(
            async_apply_legacy_set_state_service(
                runtime,
                {"rgb_color": (4, 5, 6), "brightness": 64},
            )
        )

        assert changed is True
        assert transport.sent == [
            (bytes.fromhex("53 57 00 01 00 03 04 05 06"), False),
        ]
        assert state.rgb == (4, 5, 6)
        assert state.brightness == 32


def test_legacy_set_state_service_switches_v23_rgb_to_solid() -> None:
    """BanlanX2/BanlanX3 RGB writes switch non-colorable effects to solid."""
    runtime = build_runtime({CONF_MODEL: "SP617E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    state = channel_state(runtime)
    state.effect_number = 0xBF

    changed = asyncio.run(
        async_apply_legacy_set_state_service(
            runtime,
            {"rgb_color": (1, 2, 3), "brightness": 128},
        )
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("a0 63 01 be"), False),
        (bytes.fromhex("a0 69 04 01 02 03 80"), False),
    ]
    assert state.effect_number == 0xBE
    assert state.effect == "Solid Color"
    assert state.effect_type == "Static"
    assert state.rgb == (1, 2, 3)
    assert state.brightness == 128

    runtime = build_runtime({CONF_MODEL: "SP614E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    state = channel_state(runtime)
    state.effect_number = 0x01

    changed = asyncio.run(
        async_apply_legacy_set_state_service(
            runtime,
            {"rgb_color": (4, 5, 6), "brightness": 64},
        )
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("15 01 63"), False),
        (bytes.fromhex("13 04 04 05 06 40"), False),
    ]
    assert state.effect_number == 0x63
    assert state.effect == "Solid Color"
    assert state.effect_type == "Static"
    assert state.rgb == (4, 5, 6)
    assert state.brightness == 64

    state.effect_number = 0x20
    transport.sent.clear()

    changed = asyncio.run(
        async_apply_legacy_set_state_service(
            runtime,
            {"rgb_color": (7, 8, 9), "brightness": 32},
        )
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("13 04 07 08 09 20"), False),
    ]
    assert state.effect_number == 0x20
    assert state.rgb == (7, 8, 9)
    assert state.brightness == 32


def test_legacy_set_state_service_preserves_existing_color_level() -> None:
    """RGB color writes reuse old UniLED's current color-level byte."""
    runtime = build_runtime({CONF_MODEL: "SP617E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    state = channel_state(runtime)
    state.effect_number = 0xBE
    state.brightness = 0x99
    state.extra["color_level"] = 0x44

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"rgb_color": (1, 2, 3)})
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("a0 69 04 01 02 03 44"), False),
    ]
    assert state.rgb == (1, 2, 3)
    assert state.brightness == 0x99

    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    state = channel_state(runtime)
    state.light_mode_number = 0x01
    state.brightness = 0x55

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"rgb_color": (4, 5, 6)})
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("53 52 00 01 00 04 04 05 06 55"), False),
    ]
    assert state.rgb == (4, 5, 6)
    assert state.brightness == 0x55

    runtime = build_runtime({CONF_MODEL: "SP639E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    state = channel_state(runtime)
    state.light_mode_number = 0x01
    state.brightness = 0x33

    changed = asyncio.run(
        async_apply_legacy_set_state_service(
            runtime,
            {"rgbw_color": (7, 8, 9, 10)},
        )
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("53 52 00 01 00 04 07 08 09 33"), False),
        (bytes.fromhex("53 51 00 01 00 02 01 0a"), False),
    ]
    assert state.rgbw == (7, 8, 9, 10)
    assert state.brightness == 0x33


def test_legacy_set_state_service_routes_banlanx_v23_white_brightness() -> None:
    """BanlanX2/3 brightness in solid white uses old-UniLED white-level bytes."""
    runtime = build_runtime({CONF_MODEL: "SP617E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    state = channel_state(runtime)
    state.effect_number = 0xBF

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"brightness": 0x44})
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("a0 76 02 44 00"), False),
    ]
    assert state.effect_number == 0xBF
    assert state.effect == "Solid White"
    assert state.effect_type == "Static"
    assert state.brightness == 0x44
    assert state.extra["white_level"] == 0x44

    runtime = build_runtime({CONF_MODEL: "SP624E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    state = channel_state(runtime)
    state.effect_number = 0x63

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"white": 0x55})
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("15 01 cc"), False),
        (bytes.fromhex("21 02 55 ff"), False),
    ]
    assert state.effect_number == 0xCC
    assert state.effect == "Solid White"
    assert state.effect_type == "Static"
    assert state.brightness == 0x55
    assert state.extra["white_level"] == 0x55


def test_legacy_set_state_service_mirrors_banlanx_v23_white_effect_state() -> None:
    """Selecting Solid White mirrors old-UniLED's white brightness side effect."""
    runtime = build_runtime({CONF_MODEL: "SP617E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    state = channel_state(runtime)
    state.brightness = 0x22
    state.extra["white_level"] = 0x66

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"effect": "Solid White"})
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("a0 63 01 bf"), False),
    ]
    assert light_color_mode(runtime) == "white"
    assert state.effect_number == 0xBF
    assert state.effect == "Solid White"
    assert state.effect_type == "Static"
    assert state.brightness == 0x66
    assert state.extra["white_level"] == 0x66

    runtime = build_runtime({CONF_MODEL: "SP624E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    state = channel_state(runtime)

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"effect": "Solid White"})
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("15 01 cc"), False),
    ]
    assert light_color_mode(runtime) == "white"
    assert state.effect_number == 0xCC
    assert state.brightness == 0xFF
    assert state.extra["white_level"] == 0xFF


def test_legacy_set_state_service_switches_sp6xx_white_mode() -> None:
    """SP6xx white requests enter a white mode before writing white level."""
    runtime = build_runtime({CONF_MODEL: "SP639E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    runtime.state.diagnostics["light_type"] = 0x08
    state = channel_state(runtime)
    state.light_mode_number = 0x01
    state.effect_number = 0x01

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"white": 0x40})
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("53 53 00 01 00 02 02 01"), False),
        (bytes.fromhex("53 51 00 01 00 02 01 40"), False),
    ]
    assert state.light_mode_number == 0x02
    assert state.effect_number == 0x01
    assert state.effect_type == "Static"
    assert state.brightness == 0x40
    assert state.extra["white_level"] == 0x40


def test_legacy_set_state_service_switches_sp6xx_sound_white_without_level() -> None:
    """SP6xx sound white mode changes do not append ignored 0x51 level writes."""
    runtime = build_runtime({CONF_MODEL: "SP639E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    runtime.state.diagnostics["light_type"] = 0x08
    state = channel_state(runtime)
    state.light_mode_number = 0x05
    state.effect_number = 0x12

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"white": 0x40})
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("53 53 00 01 00 02 06 01"), False),
    ]
    assert state.light_mode_number == 0x06
    assert state.effect_number == 0x01
    assert state.effect_type == "Sound"
    assert state.brightness == 0xFF
    assert "white_level" not in state.extra


def test_legacy_set_state_service_requires_command_path() -> None:
    """Diagnostic-only models do not become controllable through the old service."""
    runtime = build_runtime({CONF_MODEL: "SP802E", CONF_DEVICE_ID: "panel"})

    changed = asyncio.run(
        async_apply_legacy_set_state_service(runtime, {"brightness": 128})
    )

    assert changed is False
    assert runtime.state.channels == {}


def test_apply_scene_command_state_records_last_scene() -> None:
    """Successful scene recall records the last 0-based legacy scene slot."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    apply_scene_command_state(runtime, 8)

    assert runtime.state.diagnostics["scene"] == 8
    assert runtime.state.diagnostics["scene_channel"] == 0
    assert runtime.state.available is True


def test_sp6xx_light_color_modes_follow_light_type_and_coexistence() -> None:
    """SP6xx light color modes are derived from parsed light type state."""
    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    runtime.state.diagnostics["light_type"] = 0x06

    assert light_supported_color_modes(runtime) == ("rgb",)
    assert light_color_mode(runtime) == "rgb"

    runtime = build_runtime({CONF_MODEL: "SP639E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    runtime.state.diagnostics.update({"light_type": 0x08, "coexistence": 1})
    apply_light_command_state(runtime, rgbw=(1, 2, 3, 4), brightness=128)

    assert light_supported_color_modes(runtime) == ("rgbw",)
    assert light_color_mode(runtime) == "rgbw"

    runtime.state.diagnostics["coexistence"] = 0

    assert light_supported_color_modes(runtime) == ("rgb", "white")

    runtime = build_runtime({CONF_MODEL: "SP63AE", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    runtime.state.diagnostics.update({"light_type": 0x0B, "coexistence": 1})
    apply_light_command_state(runtime, rgbww=(1, 2, 3, 4, 5), brightness=128)

    assert light_supported_color_modes(runtime) == ("rgbww",)
    assert light_color_mode(runtime) == "rgbww"

    runtime.state.diagnostics["coexistence"] = 0
    runtime.state.channels[0].light_mode_number = 0x02

    assert light_supported_color_modes(runtime) == ("rgb", "color_temp")
    assert light_color_mode(runtime) == "color_temp"

    runtime = build_runtime({CONF_MODEL: "SP631E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    runtime.state.diagnostics["light_type"] = 0x01

    assert light_supported_color_modes(runtime) == ("brightness",)
    assert light_color_mode(runtime) == "brightness"


def test_banlanx_v23_light_color_modes_follow_rgbw_profile() -> None:
    """V2/V3 RGBW models expose legacy RGB plus white modes."""
    runtime = build_runtime({CONF_MODEL: "SP617E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    assert light_supported_color_modes(runtime) == ("rgb", "white")
    assert light_color_mode(runtime) == "rgb"

    state = apply_light_command_state(runtime, brightness=0x44, white=0x44)

    assert light_color_mode(runtime) == "white"
    assert state.effect == "Solid White"
    assert state.effect_number == 0xBF
    assert state.effect_type == "Static"
    assert state.extra["white_level"] == 0x44

    runtime = build_runtime({CONF_MODEL: "SP624E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    apply_light_command_state(runtime, brightness=0x55, white=0x55)

    assert light_supported_color_modes(runtime) == ("rgb", "white")
    assert light_color_mode(runtime) == "white"
    assert runtime.state.channels[0].effect_number == 0xCC

    runtime = build_runtime({CONF_MODEL: "SP621E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    assert light_supported_color_modes(runtime) == ("rgb",)
    assert light_color_mode(runtime) == "rgb"


def test_banlanx_v23_sound_status_is_onoff_until_color_write() -> None:
    """Parsed V2/V3 sound states follow old-UniLED on/off-only color mode."""
    runtime = build_runtime({CONF_MODEL: "SP611E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()
    runtime.attach_transport(transport)
    status = bytes.fromhex(
        "01 00 da 02 61 0a 1e ff 00 00 01 10 "
        "09 04 0b 14 1a 32 37 50 53 73 00"
    )

    apply_runtime_state(runtime, runtime.protocol.parse_status(status))
    state = channel_state(runtime)

    assert light_supported_color_modes(runtime) == ("onoff",)
    assert light_color_mode(runtime) == "onoff"
    assert state.brightness is None
    assert state.extra["color_level"] == 0x61

    changed = asyncio.run(
        async_apply_legacy_set_state_service(
            runtime,
            {"rgb_color": (4, 5, 6), "brightness": 0x40},
        )
    )

    assert changed is True
    assert transport.sent == [
        (bytes.fromhex("a0 63 01 be"), False),
        (bytes.fromhex("a0 69 04 04 05 06 40"), False),
    ]
    assert light_supported_color_modes(runtime) == ("rgb",)
    assert light_color_mode(runtime) == "rgb"
    assert "color_mode" not in state.extra
    assert state.brightness == 0x40


def test_sp6xx_cct_conversion_and_light_command_state() -> None:
    """Runtime converts Kelvin/CCT levels and stores richer light state."""
    runtime = build_runtime({CONF_MODEL: "SP637E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    cold, warm = cct_levels_for_kelvin(4600, level=200)

    assert (cold, warm) == (100, 100)
    assert cct_kelvin_from_levels(cold, warm) == 4600

    state = apply_light_command_state(
        runtime,
        brightness=200,
        color_temp_kelvin=4600,
        cct=(cold, warm),
    )

    assert state.brightness == 200
    assert state.color_temp_kelvin == 4600
    assert state.cold_white == 100
    assert state.warm_white == 100


def test_command_number_features_require_attached_session() -> None:
    """Command numbers are exposed only after a command session exists."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})

    assert command_number_features(runtime) == ()

    runtime.attach_transport(RecordingTransport())
    features = command_number_features(runtime)
    channels_by_key = {
        key: [feature.channel for feature in features if feature.key == key]
        for key in {feature.key for feature in features}
    }

    assert channels_by_key["effect_speed"] == [1, 2]
    assert channels_by_key["effect_length"] == [1, 2]
    assert channels_by_key["audio_sensitivity"] == [1, 2]
    assert "pixel_count" not in channels_by_key

    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    keys = {feature.key for feature in command_number_features(runtime)}

    assert "onoff_pixels" in keys

    runtime = build_runtime({CONF_MODEL: "SP621E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    keys = {feature.key for feature in command_number_features(runtime)}

    assert "audio_sensitivity" not in keys


def test_command_select_features_require_attached_session() -> None:
    """Command selects are exposed only after a command session exists."""
    runtime = build_runtime({CONF_MODEL: "SP611E", CONF_DEVICE_ID: "bench"})

    assert command_select_features(runtime) == ()

    runtime.attach_transport(RecordingTransport())
    keys = {feature.key for feature in command_select_features(runtime)}

    assert keys == {"audio_input", "chip_order", "effect", "light_mode"}
    assert "effect_loop" not in {
        feature.key for feature in command_switch_features(runtime)
    }

    runtime = build_runtime({CONF_MODEL: "SP621E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    keys = {feature.key for feature in command_select_features(runtime)}

    assert keys == {"chip_order", "effect"}
    assert select_options(runtime, "audio_input") == ()
    assert select_options(runtime, "light_mode") == ()
    assert "effect_loop" in {
        feature.key for feature in command_switch_features(runtime)
    }

    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    features = command_select_features(runtime)
    channels_by_key = {
        key: [feature.channel for feature in features if feature.key == key]
        for key in {feature.key for feature in features}
    }

    assert channels_by_key == {"chip_order": [1, 2], "effect": [1, 2]}
    assert select_options(runtime, "effect") == ()
    assert select_options(runtime, "chip_order") == ()
    assert len(select_options(runtime, "effect", channel=1)) == 41
    assert len(select_options(runtime, "chip_order", channel=1)) == 6

    runtime = build_runtime({CONF_MODEL: "SP602E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    features = command_select_features(runtime)
    channels_by_key = {
        key: [feature.channel for feature in features if feature.key == key]
        for key in {feature.key for feature in features}
    }

    assert channels_by_key == {
        "chip_order": [1, 2, 3, 4],
        "effect": [1, 2, 3, 4],
    }
    assert select_options(runtime, "effect") == ()
    assert select_options(runtime, "chip_order") == ()
    assert len(select_options(runtime, "effect", channel=4)) == 41

    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    keys = {feature.key for feature in command_select_features(runtime)}

    assert keys == {
        "audio_input",
        "chip_order",
        "effect",
        "light_mode",
        "on_power",
        "onoff_effect",
        "onoff_speed",
    }

    runtime = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    keys = {feature.key for feature in command_select_features(runtime)}

    assert keys == {
        "audio_input",
        "chip_order",
        "effect",
        "light_mode",
        "light_type",
        "on_power",
        "onoff_effect",
        "onoff_speed",
    }
    assert select_options(runtime, "effect") == ()
    assert select_options(runtime, "chip_order") == ()
    assert select_options(runtime, "light_mode") == ()
    assert len(select_options(runtime, "light_type")) == 14

    runtime = build_runtime({CONF_MODEL: "360PhotoB", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    keys = {feature.key for feature in command_select_features(runtime)}

    assert keys == {
        "audio_input",
        "chip_order",
        "effect",
        "light_mode",
        "light_type",
        "on_power",
        "onoff_effect",
        "onoff_speed",
    }
    assert select_options(runtime, "effect") == ()


def test_command_switch_features_require_attached_session() -> None:
    """Command switches are exposed only after a command session exists."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})

    assert command_switch_features(runtime) == ()

    runtime.attach_transport(RecordingTransport())
    features = command_switch_features(runtime)
    channels_by_key = {
        key: [feature.channel for feature in features if feature.key == key]
        for key in {feature.key for feature in features}
    }

    assert channels_by_key == {"effect_direction": [1, 2], "scene_loop": [0]}

    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    keys = {feature.key for feature in command_switch_features(runtime)}

    assert keys == {"effect_direction", "effect_loop", "effect_play"}

    runtime = build_runtime({CONF_MODEL: "SP634E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    keys = {feature.key for feature in command_switch_features(runtime)}

    assert keys == {
        "coexistence",
        "effect_direction",
        "effect_loop",
        "effect_play",
    }


def test_sp6xx_effect_attribute_command_availability_follows_status() -> None:
    """SP6xx command entities are unavailable when current effect lacks flags."""
    from tests.test_state_parsers import _banlanx_6xx_status_packet

    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})

    assert not command_control_available(runtime, "effect_speed")

    runtime.attach_transport(RecordingTransport())
    protocol = BanlanX6xxProtocol()

    pausable_packet = bytearray(_banlanx_6xx_status_packet())
    pausable_packet[19] = 0x06
    pausable_packet[32] = 0x03
    pausable_packet[33] = 0x01
    apply_runtime_state(runtime, protocol.parse_status(bytes(pausable_packet)))

    assert command_control_available(runtime, "effect_speed")
    assert command_control_available(runtime, "effect_length")
    assert command_control_available(runtime, "effect_direction")
    assert command_control_available(runtime, "effect_loop")
    assert command_control_available(runtime, "effect_play")

    non_pausable_packet = bytearray(pausable_packet)
    non_pausable_packet[33] = 0x02
    apply_runtime_state(runtime, protocol.parse_status(bytes(non_pausable_packet)))

    assert command_control_available(runtime, "effect_speed")
    assert command_control_available(runtime, "effect_length")
    assert command_control_available(runtime, "effect_direction")
    assert command_control_available(runtime, "effect_loop")
    assert not command_control_available(runtime, "effect_play")

    static_packet = bytearray(pausable_packet)
    static_packet[32] = 0x01
    static_packet[33] = 0x01
    apply_runtime_state(runtime, protocol.parse_status(bytes(static_packet)))

    assert not command_control_available(runtime, "effect_speed")
    assert not command_control_available(runtime, "effect_length")
    assert not command_control_available(runtime, "effect_direction")
    assert not command_control_available(runtime, "effect_loop")
    assert not command_control_available(runtime, "effect_play")

    v2_runtime = build_runtime({CONF_MODEL: "SP611E", CONF_DEVICE_ID: "bench"})
    v2_runtime.attach_transport(RecordingTransport())

    assert command_control_available(v2_runtime, "effect_speed")


def test_sp6xx_audio_command_availability_follows_sound_status() -> None:
    """SP6xx audio controls are available only for powered sound states."""
    from tests.test_state_parsers import _banlanx_6xx_status_packet

    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})

    assert not command_control_available(runtime, "audio_input")
    assert not command_control_available(runtime, "audio_sensitivity")

    runtime.attach_transport(RecordingTransport())
    protocol = BanlanX6xxProtocol()

    static_packet = bytearray(_banlanx_6xx_status_packet())
    static_packet[32] = 0x01
    static_packet[33] = 0x01
    apply_runtime_state(runtime, protocol.parse_status(bytes(static_packet)))

    assert control_value(runtime, "audio_input") is None
    assert control_value(runtime, "audio_sensitivity") is None
    assert not command_control_available(runtime, "audio_input")
    assert not command_control_available(runtime, "audio_sensitivity")

    sound_packet = bytearray(_banlanx_6xx_status_packet())
    sound_packet[32] = 0x05
    sound_packet[33] = 0x01
    apply_runtime_state(runtime, protocol.parse_status(bytes(sound_packet)))

    assert control_value(runtime, "audio_input") == "Ext. Mic"
    assert control_value(runtime, "audio_sensitivity") == 16
    assert command_control_available(runtime, "audio_input")
    assert command_control_available(runtime, "audio_sensitivity")

    sound_packet[29] = 0
    apply_runtime_state(runtime, protocol.parse_status(bytes(sound_packet)))

    assert control_value(runtime, "audio_input") is None
    assert control_value(runtime, "audio_sensitivity") is None
    assert not command_control_available(runtime, "audio_input")
    assert not command_control_available(runtime, "audio_sensitivity")

    v2_runtime = build_runtime({CONF_MODEL: "SP611E", CONF_DEVICE_ID: "bench"})
    v2_runtime.attach_transport(RecordingTransport())

    assert command_control_available(v2_runtime, "audio_input")
    assert command_control_available(v2_runtime, "audio_sensitivity")


def test_sp6xx_dynamic_select_availability_waits_for_light_type_status() -> None:
    """Dynamic SP6xx-style selects stay unavailable until options are known."""
    from tests.test_state_parsers import _banlanx_6xx_status_packet

    for model_name, protocol in (
        ("SP630E", BanlanX6xxProtocol()),
        ("SP530E", BanlanXCustom5xxProtocol()),
    ):
        runtime = build_runtime({CONF_MODEL: model_name, CONF_DEVICE_ID: "bench"})
        runtime.attach_transport(RecordingTransport())

        keys = {feature.key for feature in command_select_features(runtime)}

        assert {"chip_order", "effect", "light_mode", "light_type"} <= keys
        assert select_options(runtime, "effect") == ()
        assert select_options(runtime, "chip_order") == ()
        assert select_options(runtime, "light_mode") == ()
        assert command_control_available(runtime, "light_type")
        assert not command_control_available(runtime, "effect")
        assert not command_control_available(runtime, "chip_order")
        assert not command_control_available(runtime, "light_mode")

        apply_runtime_state(
            runtime,
            protocol.parse_status(_banlanx_6xx_status_packet()),
        )

        assert select_options(runtime, "effect")
        assert select_options(runtime, "chip_order")
        assert select_options(runtime, "light_mode")
        assert command_control_available(runtime, "effect")
        assert command_control_available(runtime, "chip_order")
        assert command_control_available(runtime, "light_mode")

    fixed_runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    fixed_runtime.attach_transport(RecordingTransport())

    assert command_control_available(fixed_runtime, "effect")
    assert command_control_available(fixed_runtime, "chip_order")
    assert command_control_available(fixed_runtime, "light_mode")


def test_sp6xx_effect_parameter_state_clears_after_select_changes() -> None:
    """Optimistic SP6xx select state clears parameters unsupported by new effect."""
    from custom_components.uniled.runtime import apply_select_command_state
    from tests.test_state_parsers import _banlanx_6xx_status_packet

    protocol = BanlanX6xxProtocol()

    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    pausable_packet = bytearray(_banlanx_6xx_status_packet())
    pausable_packet[19] = 0x06
    pausable_packet[32] = 0x03
    pausable_packet[33] = 0x01
    apply_runtime_state(runtime, protocol.parse_status(bytes(pausable_packet)))

    apply_select_command_state(runtime, "effect", "Dynamic Color - Rainbow Metor")

    state = channel_state(runtime)
    assert state.effect_speed == 5
    assert state.effect_length == 6
    assert state.effect_direction is True
    assert state.effect_loop is True
    assert state.extra["play"] is None
    assert not command_control_available(runtime, "effect_play")

    apply_select_command_state(runtime, "effect", "Static Color - Solid")

    assert state.effect_speed is None
    assert state.effect_length is None
    assert state.effect_direction is None
    assert state.effect_loop is None
    assert state.extra["play"] is None

    mode_runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    mode_runtime.attach_transport(RecordingTransport())
    apply_runtime_state(mode_runtime, protocol.parse_status(bytes(pausable_packet)))

    apply_select_command_state(mode_runtime, "light_mode", "Static Color")

    mode_state = channel_state(mode_runtime)
    assert mode_state.effect == "Static Color - Solid"
    assert mode_state.effect_speed is None
    assert mode_state.effect_length is None
    assert mode_state.effect_direction is None
    assert mode_state.effect_loop is None
    assert mode_state.extra["play"] is None

    type_runtime = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})
    type_runtime.attach_transport(RecordingTransport())
    apply_runtime_state(type_runtime, protocol.parse_status(bytes(pausable_packet)))

    apply_select_command_state(type_runtime, "light_type", "SPI - CCT1")

    type_state = channel_state(type_runtime)
    assert type_state.light_mode == "Static White"
    assert type_state.effect == "Static White - Solid"
    assert type_state.effect_speed is None
    assert type_state.effect_length is None
    assert type_state.effect_direction is None
    assert type_state.effect_loop is None
    assert type_state.extra["play"] is None


def test_apply_number_and_switch_command_state_updates_channel() -> None:
    """Successful command controls update normalized runtime state."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    apply_number_command_state(runtime, "effect_speed", 7, channel=1)
    apply_number_command_state(runtime, "effect_length", 120, channel=1)
    apply_number_command_state(runtime, "audio_sensitivity", 8, channel=1)
    apply_switch_command_state(runtime, "effect_direction", True, channel=1)
    apply_switch_command_state(runtime, "scene_loop", False)

    assert control_value(runtime, "effect_speed") is None
    assert control_value(runtime, "effect_speed", channel=1) == 7
    assert control_value(runtime, "effect_length", channel=1) == 120
    assert control_value(runtime, "audio_sensitivity", channel=1) == 8
    assert control_value(runtime, "effect_direction", channel=1) is True
    assert control_value(runtime, "scene_loop") is False
    assert runtime.state.diagnostics["scene_loop"] is False


def test_apply_sp6xx_advanced_command_state_updates_runtime() -> None:
    """SP6xx advanced command controls use parsed diagnostics as state."""
    from custom_components.uniled.runtime import (
        apply_select_command_state,
        channel_state,
        select_command_value,
    )

    runtime = build_runtime({CONF_MODEL: "SP634E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    runtime.state.diagnostics.update(
        {
            "light_type": 0x07,
            "onoff_effect": 1,
            "onoff_speed": 2,
            "onoff_pixels": 300,
            "coexistence": 1,
            "on_power": 2,
        }
    )
    channel_state(runtime).extra["play"] = True

    assert control_value(runtime, "onoff_effect") == "Flow Forward"
    assert control_value(runtime, "onoff_speed") == "Medium"
    assert control_value(runtime, "onoff_pixels") == 300
    assert control_value(runtime, "on_power") == "Last state"
    assert control_value(runtime, "coexistence") is True
    assert control_value(runtime, "effect_play") is True
    assert onoff_command_values(runtime, effect=3) == (3, 2, 300)

    assert select_command_value(runtime, "onoff_effect", "Stars") == 4
    assert select_command_value(runtime, "on_power", "Light Off") == 0

    apply_select_command_state(runtime, "onoff_effect", "Stars")
    apply_select_command_state(runtime, "onoff_speed", "Fast")
    apply_select_command_state(runtime, "on_power", "Light Off")
    apply_number_command_state(runtime, "onoff_pixels", 75)
    apply_switch_command_state(runtime, "effect_play", False)
    apply_switch_command_state(runtime, "coexistence", False)

    assert control_value(runtime, "onoff_effect") == "Stars"
    assert control_value(runtime, "onoff_speed") == "Fast"
    assert control_value(runtime, "on_power") == "Light Off"
    assert control_value(runtime, "onoff_pixels") == 75
    assert control_value(runtime, "effect_play") is False
    assert control_value(runtime, "coexistence") is False
    assert onoff_command_values(runtime) == (4, 3, 75)

    runtime.state.diagnostics["light_type"] = 0x06

    assert control_value(runtime, "coexistence") is None


def test_sp6xx_light_mode_select_uses_light_type_default_effects() -> None:
    """SP6xx light-mode commands choose an effect valid for the target mode."""
    from custom_components.uniled.runtime import (
        apply_select_command_state,
        channel_state,
        select_command_value,
    )

    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    channel = channel_state(runtime)

    assert select_options(runtime, "light_mode") == (
        "Static Color",
        "Dynamic Color",
        "Sound - Color",
        "Custom",
    )
    assert select_command_value(runtime, "light_mode", "Static Color") == 0x01

    channel.effect_number = 0x05

    assert light_mode_command_values(runtime, 0x03) == (0x03, 0x05)
    assert light_mode_command_values(runtime, 0x01) == (0x01, 0x01)

    apply_select_command_state(runtime, "light_mode", "Dynamic Color")

    assert control_value(runtime, "light_mode") == "Dynamic Color"
    assert control_value(runtime, "effect") == "Dynamic Color - Rainbow Wave"
    assert channel.light_mode_number == 0x03
    assert channel.effect_number == 0x05
    assert channel.effect_type == "Dynamic"

    apply_select_command_state(runtime, "light_mode", "Static Color")

    assert control_value(runtime, "light_mode") == "Static Color"
    assert control_value(runtime, "effect") == "Static Color - Solid"
    assert channel.light_mode_number == 0x01
    assert channel.effect_number == 0x01
    assert channel.effect_type == "Static"


def test_sp6xx_dynamic_light_mode_select_waits_for_light_type() -> None:
    """Dynamic SP6xx-style models expose mode options only after light type."""
    from custom_components.uniled.runtime import (
        apply_select_command_state,
        channel_state,
        select_command_value,
    )

    runtime = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    assert select_options(runtime, "light_mode") == ()
    assert light_mode_command_values(runtime, 0x03) is None
    try:
        select_command_value(runtime, "light_mode", "Dynamic Color")
    except ValueError:
        pass
    else:
        raise AssertionError("SP630E should wait for parsed light type")

    runtime.state.diagnostics["light_type"] = 0x86
    channel_state(runtime).effect_number = 0x05

    assert select_options(runtime, "light_mode") == (
        "Static Color",
        "Dynamic Color",
        "Sound - Color",
        "Custom",
    )
    assert light_mode_command_values(runtime, 0x03) == (0x03, 0x05)

    apply_select_command_state(runtime, "light_mode", "Static Color")

    assert control_value(runtime, "light_mode") == "Static Color"
    assert control_value(runtime, "effect") == "Static Color - Solid"
    assert channel_state(runtime).effect_number == 0x01


def test_apply_sp6xx_light_type_and_chip_order_state_updates_runtime() -> None:
    """SP6xx light-type/chip-order selects use light-type-aware options."""
    from custom_components.uniled.runtime import (
        apply_select_command_state,
        channel_state,
        select_command_value,
    )

    runtime = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())
    channel = channel_state(runtime)
    channel.power = True
    channel.chip_order = 2
    channel.light_mode_number = 0x04
    channel.effect_number = 0x02
    runtime.state.diagnostics["light_type"] = 0x84

    assert control_value(runtime, "light_type") == "SPI - CCT1"
    assert select_options(runtime, "chip_order") == (
        "CWX",
        "CXW",
        "WCX",
        "WXC",
        "XCW",
        "XWC",
    )
    assert control_value(runtime, "chip_order") == "WCX"
    assert select_command_value(runtime, "light_type", "SPI - RGB") == 0x86
    assert select_command_value(runtime, "chip_order", "XWC") == 5

    command = light_type_command_values(runtime, 0x86)

    assert command.light_type == 0x86
    assert command.chip_order == 0
    assert command.mode == 0x01
    assert command.effect == 0x01
    assert command.power is True
    assert command.refresh is True

    apply_select_command_state(runtime, "light_type", "SPI - RGB")

    assert runtime.state.diagnostics["light_type"] == 0x86
    assert control_value(runtime, "light_type") == "SPI - RGB"
    assert select_options(runtime, "chip_order") == (
        "RGB",
        "RBG",
        "GRB",
        "GBR",
        "BRG",
        "BGR",
    )
    assert control_value(runtime, "chip_order") == "RGB"
    assert control_value(runtime, "effect") == "Static Color - Solid"
    assert channel.power is False

    apply_select_command_state(runtime, "chip_order", "GRB")

    assert control_value(runtime, "chip_order") == "GRB"
    assert channel.chip_order == 2


def test_apply_select_command_state_uses_legacy_option_maps() -> None:
    """Successful select commands update state through legacy option maps."""
    from custom_components.uniled.runtime import (
        apply_select_command_state,
        select_command_value,
    )

    runtime = build_runtime({CONF_MODEL: "SP611E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    assert select_command_value(runtime, "audio_input", "Ext. Mic") == 2
    assert select_command_value(runtime, "light_mode", "Cycle Sound FX's") == 2
    assert select_command_value(runtime, "effect", "Sound - Party") == 0xDA

    apply_select_command_state(runtime, "audio_input", "Ext. Mic")
    apply_select_command_state(runtime, "light_mode", "Cycle Sound FX's")
    apply_select_command_state(runtime, "effect", "Sound - Party")

    assert control_value(runtime, "audio_input") == "Ext. Mic"
    assert control_value(runtime, "light_mode") == "Cycle Sound FX's"
    assert control_value(runtime, "effect") == "Sound - Party"
    assert runtime.state.channels[0].effect_number == 0xDA
    assert runtime.state.channels[0].effect_type == "Sound"
    assert runtime.state.channels[0].effect_loop is True

    runtime = build_runtime({CONF_MODEL: "SP617E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    assert select_command_value(runtime, "effect", "Solid White") == 0xBF

    runtime = build_runtime({CONF_MODEL: "SP603E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    assert select_options(runtime, "audio_input") == ()
    assert select_options(runtime, "light_mode") == ()
    assert "Sound - Music Breath" not in select_options(runtime, "effect")
    try:
        select_command_value(runtime, "effect", "Sound - Music Breath")
    except ValueError:
        pass
    else:
        raise AssertionError("SP603E should not expose sound effects")

    runtime = build_runtime({CONF_MODEL: "SP621E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    assert select_options(runtime, "audio_input") == ()
    assert select_options(runtime, "light_mode") == ()
    try:
        select_command_value(runtime, "audio_input", "Ext. Mic")
    except ValueError:
        pass
    else:
        raise AssertionError("SP621E should not expose audio input")

    try:
        select_command_value(runtime, "light_mode", "Cycle Sound FX's")
    except ValueError:
        pass
    else:
        raise AssertionError("SP621E should not expose light mode")

    try:
        select_command_value(runtime, "effect", "Sound - Party")
    except ValueError:
        pass
    else:
        raise AssertionError("SP621E should not expose sound effects")

    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    assert select_options(runtime, "effect") == ()
    try:
        select_command_value(runtime, "effect", "Chasing")
    except ValueError:
        pass
    else:
        raise AssertionError("SP601E aggregate should not expose effects")
    assert select_options(runtime, "chip_order") == ()
    try:
        select_command_value(runtime, "chip_order", "GRB")
    except ValueError:
        pass
    else:
        raise AssertionError("SP601E aggregate should not expose chip order")
    assert select_command_value(runtime, "effect", "Chasing", channel=1) == 8
    assert select_command_value(runtime, "chip_order", "GRB", channel=1) == 2

    apply_select_command_state(runtime, "effect", "Chasing", channel=1)
    apply_select_command_state(runtime, "chip_order", "GRB", channel=1)

    assert control_value(runtime, "effect") is None
    assert control_value(runtime, "effect", channel=1) == "Chasing"
    assert control_value(runtime, "chip_order") is None
    assert control_value(runtime, "chip_order", channel=1) == "GRB"
    assert runtime.state.channels[1].effect_number == 8
    assert runtime.state.channels[1].effect_type == "Dynamic"
    assert runtime.state.channels[1].chip_order == 2

    runtime = build_runtime({CONF_MODEL: "SP638E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    assert select_command_value(runtime, "effect", "Dynamic Color - Rainbow") == 0x0301
    assert effect_command_value(runtime, "Dynamic Color - Rainbow") == (0x03, 0x01)

    apply_select_command_state(runtime, "effect", "Sound - Color - Sound - Party")

    assert control_value(runtime, "effect") == "Sound - Color - Sound - Party"
    assert runtime.state.channels[0].light_mode == "Sound - Color"
    assert runtime.state.channels[0].light_mode_number == 0x05
    assert runtime.state.channels[0].effect_number == 0x12
    assert runtime.state.channels[0].effect_type == "Sound"

    runtime = build_runtime({CONF_MODEL: "SP633E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    try:
        select_command_value(runtime, "effect", "Sound - Color - Sound - Party")
    except ValueError:
        pass
    else:
        raise AssertionError("PWM RGB SP6xx models should not expose SPI sound effects")

    runtime = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    try:
        select_command_value(runtime, "effect", "Dynamic Color - Rainbow")
    except ValueError:
        pass
    else:
        raise AssertionError("SP630E should wait for parsed light type")

    runtime.state.diagnostics["light_type"] = 0x06

    assert len(select_options(runtime, "effect")) == 183
    assert select_command_value(runtime, "effect", "Dynamic Color - Rainbow") == 0x0301
    assert effect_command_value(runtime, "Dynamic Color - Rainbow") == (0x03, 0x01)

    apply_select_command_state(runtime, "effect", "Dynamic Color - Rainbow Metor")

    assert control_value(runtime, "effect") == "Dynamic Color - Rainbow Metor"
    assert runtime.state.channels[0].light_mode == "Dynamic Color"
    assert runtime.state.channels[0].light_mode_number == 0x03
    assert runtime.state.channels[0].effect_number == 0x02


def test_async_refresh_runtime_state_queries_and_adopts_response() -> None:
    """Runtime refresh sends a state query and adopts parsed metadata."""
    response = bytes.fromhex(
        "01 02 00 ff 0a 1e 01 ff 00 00 10"
        "00 01 02 ff 0a 1e 00 00 ff 00 10"
    )
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport(response=response)
    runtime.attach_transport(transport)

    state = asyncio.run(async_refresh_runtime_state(runtime, response_timeout=0))

    assert state is runtime.state
    assert state.available is True
    assert state.model == "SP601E"
    assert state.channels[1].brightness == 255
    assert state.diagnostics["last_refresh_result"] == "ok"
    assert state.diagnostics["session_ready"] is True
    assert transport.sent == [(bytes.fromhex("aa 2f 00"), True)]


def test_async_refresh_runtime_state_marks_unavailable_without_response() -> None:
    """Runtime refresh records no-response state without losing diagnostics."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    runtime.attach_transport(RecordingTransport())

    state = asyncio.run(async_refresh_runtime_state(runtime, response_timeout=0))

    assert state is runtime.state
    assert state.available is False
    assert state.diagnostics["last_refresh_result"] == "no_response"
    assert state.diagnostics["session_ready"] is True


def test_async_refresh_runtime_state_records_missing_session() -> None:
    """Runtime refresh records diagnostic-only entries without a session."""
    runtime = build_runtime({CONF_MODEL: "SP802E", CONF_DEVICE_ID: "bench"})

    state = asyncio.run(async_refresh_runtime_state(runtime, response_timeout=0))

    assert state is runtime.state
    assert state.available is False
    assert state.diagnostics["last_refresh_result"] == "no_session"
    assert runtime.diagnostic_value("last_refresh_result") == "no_session"
    assert "last_refresh_result" in implemented_sensor_keys(runtime)


def test_runtime_diagnostics_redacts_entry_identifiers() -> None:
    """Diagnostics preserve model facts while redacting local identifiers."""
    runtime = build_runtime(
        {
            CONF_MODEL: "SP802E",
            CONF_DEVICE_ID: "living-room",
            CONF_HOST: "192.168.1.50",
            CONF_TRANSPORT: TRANSPORT_LAN,
        }
    )

    diagnostics = runtime_diagnostics(runtime)

    assert diagnostics["entry"][CONF_MODEL] == "SP802E"
    assert diagnostics["entry"][CONF_DEVICE_ID] == "**REDACTED**"
    assert diagnostics["entry"][CONF_HOST] == "**REDACTED**"
    assert diagnostics["model"]["family"] == "banlanx_network"
    assert diagnostics["runtime"]["protocol_ready"] is False
    assert diagnostics["model"]["lan_profile"] == {
        "family": "banlanx_network",
        "network_info_code": 9,
        "max_data_length": None,
        "command_protocol_known": False,
        "discovery_confirmed": False,
        "requires_manual_host": True,
        "host_network_methods": [
            "wifiBroadcast",
            "wifiGatewayAddress",
            "wifiState",
            "wifiIPAddress",
            "wifiIPv6Address",
            "wifiName",
            "wifiBSSID",
            "wifiSubmask",
        ],
        "apk_discovery_hints": [
            "network_info_plus",
            "multicast_lock",
            "bonsoir",
            "android_nsd",
            "raw_datagram_socket",
        ],
        "apk_discovery_channels": [
            "dev.fluttercommunity.plus/network_info",
            "com.spled.plugins/multicast_lock",
            "bonsoir",
        ],
        "network_setup_route_hints": [
            "/device/universal/network/config",
        ],
        "network_setup_prompts": [
            "Configure device network",
            "Device network status",
            "Please connect your phone to an available network first",
            (
                'Press the device\'s "AP/STA" button more than 5 seconds '
                "until the green indicator light flashes, than the device "
                "enters the network configuration state (via Bluetooth)."
            ),
            (
                'Short press the device\'s "AP/STA" button, when the blue '
                "indicator light on, than the device enters the network "
                "configuration state (via AP).2"
            ),
            "The device has not been connected to a network yet",
            "Unavailable network, some features will be limited.",
        ],
        "network_cloud_setup_prompts": [
            (
                "The controller is not bound to your account. To enable cloud "
                "or voice assistant control, please reconfigure the device to "
                "the network"
            ),
            (
                "You are not signed in. After setup, the device can only be "
                "controlled within the local network and not via cloud access "
                "or voice assistant"
            ),
        ],
        "multicast_lock_methods": [
            "acquire_multicast_lock",
            "release_multicast_lock",
            "held_multicast_lock",
        ],
        "bonsoir_methods": [
            "broadcast.initialize",
            "broadcast.start",
            "broadcast.stop",
            "discovery.initialize",
            "discovery.start",
            "discovery.stop",
        ],
        "bonsoir_arguments": [
            "service.name",
            "service.type",
            "service.port",
            "service.host",
            "service.attributes",
        ],
        "bonsoir_nsd_methods": [
            "NsdManager.discoverServices",
            "NsdManager.resolveService",
            "NsdManager.registerService",
            "NsdManager.stopServiceDiscovery",
            "NsdManager.unregisterService",
        ],
        "bonsoir_service_type_flow_hints": [
            (
                "discovery.initialize stores the Dart session type as the NSD "
                "service type"
            ),
            (
                "discovery.start passes that service type to "
                "NsdManager.discoverServices"
            ),
            (
                "discovery.resolveService rebuilds NsdServiceInfo from service "
                "name and type"
            ),
            "broadcast.initialize stores service.type for NSD registration",
            (
                "broadcast.start sets service.type, port, host, and TXT "
                "attributes before registerService"
            ),
            (
                "onServiceFound normalizes trailing-dot service types and "
                "extracts TXT attributes"
            ),
        ],
        "bonsoir_txt_query_flow_hints": [
            (
                "discoveryServiceFound schedules a secondary mDNS TXT query "
                "for the service"
            ),
            "TXT query name is encoded as service.name, service.type, and local",
            "TXT query uses DNS record type 16",
            (
                "TXT query class is 32769, matching IN plus the mDNS "
                "unicast-response bit"
            ),
            "TXT query retries using local port 5353 after an ephemeral-port timeout",
            (
                "TXT parser updates service attributes and emits lost/found "
                "events on change"
            ),
        ],
        "discovery_gap_hints": [
            (
                "Decompiled Bonsoir plugin shows service type is supplied by "
                "Dart, but the concrete BanlanX DNS-SD service type was not "
                "recovered"
            ),
            (
                "No model-specific TXT attribute schema or discovery response "
                "was recovered"
            ),
            (
                "RawDatagramSocket and DatagramSocket evidence is generic "
                "plumbing, not a command frame"
            ),
        ],
        "raw_socket_hints": [
            "RawDatagramSocket:onDone",
            "RawDatagramSocket:onError ->",
            "Socket_AvailableDatagram",
            "_makeDatagram@16069316",
            (
                "Address family not supported by protocol family, "
                "sourceAddress.type must be 2"
            ),
            "Reading from a closed socket2",
            "Writing to a closed socket",
            "socket bind error ->",
        ],
        "discovery_status_hints": [
            "delay stop discovery>>>>>>>",
            "reported data:",
            "unresolved discovery response from",
        ],
        "mdns_multicast_group": "224.0.0.251",
        "mdns_port": 5353,
        "mdns_ttl": 255,
        "mdns_txt_query_timeout_ms": 2000,
        "mdns_txt_record_type": 16,
        "mdns_txt_query_class": 32769,
        "udp_socket_timeout_ms": 8000,
        "udp_receive_buffer_bytes": 2000,
        "mdns_txt_buffer_bytes": 1024,
    }

    assert any(
        feature["key"] == "network_info" and feature["implemented"] is True
        for feature in diagnostics["entity_plan"]
    )
    assert runtime.diagnostic_value("lan_profile") == (
        "banlanx_network; manual_host; command_protocol_pending; "
        "network_info=9; discovery_plugins=5; network_setup_routes=1; "
        "network_setup_prompts=7; cloud_setup_prompts=2; "
        "bonsoir_nsd_methods=5; service_type_flow=6; txt_query_flow=6; "
        "raw_socket_hints=8; "
        "discovery_status=3; discovery_gaps=3; mdns=224.0.0.251:5353"
    )
    assert runtime.diagnostic_value("lan_host_network_method_count") == 8
    assert runtime.diagnostic_value("lan_host_setup_mode") == "manual_host"
    assert runtime.diagnostic_value("lan_discovery_plugin_count") == 5
    assert runtime.diagnostic_value("lan_discovery_channel_count") == 3
    assert runtime.diagnostic_value("lan_network_setup_route_count") == 1
    assert runtime.diagnostic_value("lan_network_setup_prompt_count") == 7
    assert runtime.diagnostic_value("lan_network_cloud_setup_prompt_count") == 2
    assert runtime.diagnostic_value("lan_multicast_lock_method_count") == 3
    assert runtime.diagnostic_value("lan_bonsoir_method_count") == 6
    assert runtime.diagnostic_value("lan_bonsoir_argument_count") == 5
    assert runtime.diagnostic_value("lan_bonsoir_nsd_method_count") == 5
    assert (
        runtime.diagnostic_value("lan_bonsoir_service_type_flow_hint_count")
        == 6
    )
    assert runtime.diagnostic_value("lan_bonsoir_txt_query_flow_hint_count") == 6
    assert runtime.diagnostic_value("lan_discovery_gap_count") == 3
    assert runtime.diagnostic_value("lan_raw_socket_hint_count") == 8
    assert runtime.diagnostic_value("lan_discovery_status_hint_count") == 3
    assert runtime.diagnostic_value("lan_udp_socket_timeout_ms") == 8000
    assert runtime.diagnostic_value("lan_udp_receive_buffer_bytes") == 2000
    assert runtime.diagnostic_value("lan_mdns_txt_query_timeout_ms") == 2000
    assert runtime.diagnostic_value("lan_mdns_txt_record_type") == 16
    assert runtime.diagnostic_value("lan_mdns_txt_query_class") == 32769
    assert runtime.diagnostic_value("lan_mdns_txt_buffer_bytes") == 1024
    assert "lan_host_network_method_count" in implemented_sensor_keys(runtime)
    assert "lan_host_setup_mode" in implemented_sensor_keys(runtime)
    assert "lan_discovery_plugin_count" in implemented_sensor_keys(runtime)
    assert "lan_discovery_channel_count" in implemented_sensor_keys(runtime)
    assert "lan_network_setup_route_count" in implemented_sensor_keys(runtime)
    assert "lan_network_setup_prompt_count" in implemented_sensor_keys(runtime)
    assert (
        "lan_network_cloud_setup_prompt_count"
        in implemented_sensor_keys(runtime)
    )
    assert "lan_multicast_lock_method_count" in implemented_sensor_keys(runtime)
    assert "lan_bonsoir_method_count" in implemented_sensor_keys(runtime)
    assert "lan_bonsoir_argument_count" in implemented_sensor_keys(runtime)
    assert "lan_bonsoir_nsd_method_count" in implemented_sensor_keys(runtime)
    assert (
        "lan_bonsoir_service_type_flow_hint_count"
        in implemented_sensor_keys(runtime)
    )
    assert "lan_bonsoir_txt_query_flow_hint_count" in implemented_sensor_keys(
        runtime
    )
    assert "lan_discovery_gap_count" in implemented_sensor_keys(runtime)
    assert "lan_raw_socket_hint_count" in implemented_sensor_keys(runtime)
    assert "lan_discovery_status_hint_count" in implemented_sensor_keys(runtime)
    assert "lan_udp_socket_timeout_ms" in implemented_sensor_keys(runtime)
    assert "lan_udp_receive_buffer_bytes" in implemented_sensor_keys(runtime)
    assert "lan_mdns_txt_query_timeout_ms" in implemented_sensor_keys(runtime)
    assert "lan_mdns_txt_record_type" in implemented_sensor_keys(runtime)
    assert "lan_mdns_txt_query_class" in implemented_sensor_keys(runtime)
    assert "lan_mdns_txt_buffer_bytes" in implemented_sensor_keys(runtime)
    assert (
        runtime.diagnostic_value("network_info")
        == "supportGetNetInfo=9; command_protocol_pending"
    )

    runtime.state.diagnostics["network_info"] = "ssid=lab; ip=192.0.2.10"

    assert runtime.diagnostic_value("network_info") == "ssid=lab; ip=192.0.2.10"


def test_runtime_diagnostics_redacts_cloud_credentials() -> None:
    """Diagnostics redact transient cloud credentials if they are present."""
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_DEVICE_ID: "bench",
            CONF_CLOUD_USERNAME: "user@example.test",
            CONF_CLOUD_PASSWORD: "SecretPassword",
        }
    )

    diagnostics = runtime_diagnostics(runtime)

    assert diagnostics["entry"][CONF_CLOUD_USERNAME] == "**REDACTED**"
    assert diagnostics["entry"][CONF_CLOUD_PASSWORD] == "**REDACTED**"

    ble_only = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})

    assert ble_only.diagnostic_value("lan_profile") is None
    assert ble_only.diagnostic_value("lan_discovery_plugin_count") is None
    assert ble_only.diagnostic_value("lan_network_setup_prompt_count") is None
    assert ble_only.diagnostic_value("lan_raw_socket_hint_count") is None
    assert ble_only.diagnostic_value("lan_discovery_status_hint_count") is None
    assert (
        ble_only.diagnostic_value("lan_bonsoir_txt_query_flow_hint_count")
        is None
    )
    assert ble_only.diagnostic_value("lan_mdns_txt_query_timeout_ms") is None
    assert ble_only.diagnostic_value("lan_mdns_txt_record_type") is None
    assert ble_only.diagnostic_value("lan_mdns_txt_query_class") is None
    assert "lan_discovery_plugin_count" not in implemented_sensor_keys(ble_only)
    assert "lan_network_setup_prompt_count" not in implemented_sensor_keys(ble_only)
    assert "lan_raw_socket_hint_count" not in implemented_sensor_keys(ble_only)
    assert "lan_discovery_status_hint_count" not in implemented_sensor_keys(ble_only)
    assert "lan_bonsoir_txt_query_flow_hint_count" not in implemented_sensor_keys(
        ble_only
    )


def test_runtime_sp801e_network_setup_guide_diagnostic() -> None:
    """SP801E exposes APK setup-guide assets without unlocking LAN commands."""
    runtime = build_runtime(
        {
            CONF_MODEL: "SP801E",
            CONF_HOST: "192.168.1.80",
            CONF_TRANSPORT: TRANSPORT_LAN,
        }
    )
    diagnostics = runtime_diagnostics(runtime)

    assert runtime.diagnostic_value("lan_network_setup_guide_asset_count") == 3
    assert "lan_network_setup_guide_asset_count" in implemented_sensor_keys(runtime)
    assert diagnostics["model"]["lan_profile"]["network_setup_guide_assets"] == [
        "packages/module_home/assets/images/net_config_guide/sp801e_init.png",
        "packages/module_home/assets/images/net_config_guide/sp801e_ble.png",
        "packages/module_home/assets/images/net_config_guide/sp801e_ap.png",
    ]
    assert runtime.protocol is None


def test_runtime_diagnostics_exposes_duplicate_catalog_variants() -> None:
    """Diagnostics preserve APK records hidden behind duplicate display names."""
    runtime = build_runtime({CONF_MODEL: "SP665E", CONF_DEVICE_ID: "scene"})

    diagnostics = runtime_diagnostics(runtime)
    variants = diagnostics["model"]["catalog_variants"]

    assert runtime.model.model_id == 126
    assert runtime.diagnostic_value("catalog_model_id") == 126
    assert runtime.diagnostic_value("catalog_parent_id") == 121
    assert runtime.diagnostic_value("catalog_variant_count") == 2
    assert runtime.diagnostic_value("catalog_variant_ids") == "126, 260"
    assert [variant["id"] for variant in variants] == [126, 260]
    assert [variant["parent_id"] for variant in variants] == [121, 126]
    assert [variant["spec_functions"] for variant in variants] == [87, 85]
    assert [variant["spec_function_bits"] for variant in variants] == [
        [
            "feature_0x01",
            "audio_controls",
            "feature_0x04",
            "feature_0x10",
            "feature_0x40",
        ],
        ["feature_0x01", "feature_0x04", "feature_0x10", "feature_0x40"],
    ]
    assert [variant["color_capabilities"] for variant in variants] == [
        ["addressable_rgb"],
        ["addressable_rgb"],
    ]
    assert [variant["feature_keys"] for variant in variants] == [
        ["features", "maxPixelChannels"],
        ["features", "maxPixelChannels"],
    ]
    assert [variant["canonical"] for variant in variants] == [True, False]
    assert [variant["selected"] for variant in variants] == [True, False]
    assert all(variant["name"] == "SP665E" for variant in variants)
    assert all(variant["family"] == "banlanx_scene_ui" for variant in variants)
    assert variants[0]["features"] == {
        "features": 1,
        "maxPixelChannels": 1800,
    }
    assert variants[1]["features"] == {
        "features": 1,
        "maxPixelChannels": 1800,
    }


def test_runtime_can_select_duplicate_catalog_variant_by_model_id() -> None:
    """Stored APK model IDs select the exact row hidden behind duplicate names."""
    runtime = build_runtime(
        {CONF_MODEL: "SP665E", CONF_MODEL_ID: 260, CONF_DEVICE_ID: "scene"}
    )

    diagnostics = runtime_diagnostics(runtime)
    variants = diagnostics["model"]["catalog_variants"]

    assert runtime.model.model_id == 260
    assert runtime.model.parent_id == 126
    assert runtime.model.spec_functions == 85
    assert runtime.diagnostic_value("catalog_model_id") == 260
    assert runtime.diagnostic_value("catalog_parent_id") == 126
    assert [variant["id"] for variant in variants] == [126, 260]
    assert [variant["canonical"] for variant in variants] == [True, False]
    assert [variant["selected"] for variant in variants] == [False, True]


def test_runtime_accepts_friendly_label_and_stores_canonical_model() -> None:
    """Older entry data with a friendly label still resolves to one APK row."""
    runtime = build_runtime(
        {CONF_MODEL: "\u9c7c\u7f38\u706f", CONF_DEVICE_ID: "tank"}
    )

    assert runtime.model.name == "FT001"
    assert runtime.model.model_id == 150
    assert runtime.state.model == "FT001"
    assert runtime.diagnostic_value("catalog_model_id") == 150


def test_runtime_rejects_mismatched_duplicate_model_id() -> None:
    """A stored model ID must match the stored display name."""
    cases = (
        (
            {CONF_MODEL: "SP665E", CONF_MODEL_ID: 99, CONF_DEVICE_ID: "scene"},
            "unknown_model_id",
        ),
        (
            {
                CONF_MODEL: "SP665E",
                CONF_MODEL_ID: "not-an-int",
                CONF_DEVICE_ID: "scene",
            },
            "invalid_model_id",
        ),
    )
    for data, reason in cases:
        try:
            build_runtime(data)
        except RuntimeSetupError as ex:
            assert ex.field == CONF_MODEL_ID
            assert ex.reason == reason
        else:
            raise AssertionError("mismatched or invalid model IDs must not fallback")


def test_network_info_diagnostic_uses_catalog_code_until_query_supported() -> None:
    """Network-info sensors expose APK/catalog query codes before live reads."""
    runtime = build_runtime({CONF_MODEL: "SP547E", CONF_DEVICE_ID: "bench"})

    assert (
        runtime.diagnostic_value("network_info")
        == "supportGetNetInfo=37; command_protocol_pending"
    )

    no_network_info = build_runtime({CONF_MODEL: "SP801E", CONF_DEVICE_ID: "panel"})

    assert no_network_info.diagnostic_value("network_info") is None


def test_max_pixel_channels_diagnostic_uses_catalog_limit() -> None:
    """Pixel-channel limits are diagnostic facts until write frames are proven."""
    runtime = build_runtime({CONF_MODEL: "SP660E", CONF_DEVICE_ID: "scene"})

    assert runtime.diagnostic_value("max_pixel_channels") == 1800
    assert "max_pixel_channels" in implemented_sensor_keys(runtime)

    custom = build_runtime({CONF_MODEL: "SP530E", CONF_DEVICE_ID: "strip"})

    assert custom.diagnostic_value("max_pixel_channels") == 3600
    assert "max_pixel_channels" in implemented_sensor_keys(custom)

    no_limit = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "legacy"})

    assert no_limit.diagnostic_value("max_pixel_channels") is None
    assert "max_pixel_channels" not in implemented_sensor_keys(no_limit)


def test_runtime_diagnostics_exposes_ble_evidence_profiles() -> None:
    """Direct-BLE diagnostics distinguish proven profiles from APK evidence."""
    runtime = build_runtime({CONF_MODEL: "SP660E", CONF_DEVICE_ID: "scene"})

    profile = runtime_diagnostics(runtime)["model"]["ble_profile"]

    assert profile["family"] == "banlanx_scene_ui"
    assert profile["command_profile_known"] is False
    assert profile["known_service_uuids"] == []
    assert profile["known_write_uuid"] is None
    assert profile["known_notify_uuid"] is None
    assert profile["uuid_binding_status"] == (
        "binding=pending; services=0; write=pending; notify=pending; "
        "unbound_candidates=3; legacy_candidates=2"
    )
    assert profile["apk_uuid_pool"] == [
        "0000ff12-0000-1000-8000-00805f9b34fb",
        "0000ff14-0000-1000-8000-00805f9b34fb",
        "0000ff15-0000-1000-8000-00805f9b34fb",
        "0000ffe0-0000-1000-8000-00805f9b34fb",
        "0000ffe1-0000-1000-8000-00805f9b34fb",
    ]
    assert profile["uuid_inventory"] == [
        {
            "uuid": "0000ff12-0000-1000-8000-00805f9b34fb",
            "short_name": "ff12",
            "apk_string": "0000ff12-0000-1000-8000-00805f9b34fb2",
            "known_usage": "unbound_candidate",
            "unported_binding_status": "unproven",
            "evidence": "BanlanX 3.3.1 Flutter libapp.so string",
        },
        {
            "uuid": "0000ff14-0000-1000-8000-00805f9b34fb",
            "short_name": "ff14",
            "apk_string": "0000ff14-0000-1000-8000-00805f9b34fb2",
            "known_usage": "unbound_candidate",
            "unported_binding_status": "unproven",
            "evidence": "BanlanX 3.3.1 Flutter libapp.so string",
        },
        {
            "uuid": "0000ff15-0000-1000-8000-00805f9b34fb",
            "short_name": "ff15",
            "apk_string": "0000ff15-0000-1000-8000-00805f9b34fb2",
            "known_usage": "unbound_candidate",
            "unported_binding_status": "unproven",
            "evidence": "BanlanX 3.3.1 Flutter libapp.so string",
        },
        {
            "uuid": "0000ffe0-0000-1000-8000-00805f9b34fb",
            "short_name": "ffe0",
            "apk_string": "0000ffe0-0000-1000-8000-00805f9b34fb2",
            "known_usage": "legacy_service_uuid",
            "unported_binding_status": "unproven",
            "evidence": (
                "BanlanX 3.3.1 Flutter libapp.so string plus old-UniLED parity"
            ),
        },
        {
            "uuid": "0000ffe1-0000-1000-8000-00805f9b34fb",
            "short_name": "ffe1",
            "apk_string": "0000ffe1-0000-1000-8000-00805f9b34fb2",
            "known_usage": "legacy_write_notify_uuid",
            "unported_binding_status": "unproven",
            "evidence": (
                "BanlanX 3.3.1 Flutter libapp.so string plus old-UniLED parity"
            ),
        },
    ]
    assert profile["unbound_uuid_candidates"] == ["ff12", "ff14", "ff15"]
    assert profile["legacy_uuid_candidates"] == ["ffe0", "ffe1"]
    assert profile["plugin_channels"] == [
        "com.spled.plugins/flutter_ble/main",
        "com.spled.plugins/flutter_ble/ble_characteristic_value_changed",
        "com.spled.plugins/flutter_ble/ble_connection_state_changed",
        "com.spled.plugins/flutter_ble/bluetooth_adapter_state_changed",
        "com.spled.plugins/flutter_ble/bluetooth_device_discovery_state_changed",
        "com.spled.plugins/flutter_ble/bluetooth_device_found",
    ]
    assert profile["plugin_methods"] == [
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
    ]
    assert "serviceUuid" in profile["plugin_arguments"]
    assert "characteristicUuid" in profile["plugin_arguments"]
    assert "services" in profile["plugin_arguments"]
    assert "clearPreDiscoveredDevices" in profile["plugin_arguments"]
    assert profile["plugin_result_fields"] == [
        "id",
        "name",
        "rssi",
        "serviceData",
        "manufacturerData",
        "uuid",
        "supportWrite",
        "supportWriteNoResponse",
        "supportRead",
        "supportNotify",
        "supportIndicate",
    ]
    assert len(profile["plugin_contract_hints"]) == 6
    assert profile["plugin_contract_hints"][0] == {
        "method": "getBleDeviceCharacteristics",
        "required_arguments": ["serviceUuid"],
        "default_arguments": [],
        "behavior": "requests characteristics for the supplied service UUID",
        "error_code": "10013",
        "evidence": "p185q2/C2229c.java validates serviceUuid before dispatch",
    }
    assert profile["plugin_contract_hints"][1]["method"] == (
        "notifyBleCharacteristicValueChange"
    )
    assert profile["plugin_contract_hints"][1]["default_arguments"] == [
        "enabled=False"
    ]
    assert profile["plugin_contract_hints"][4]["required_arguments"] == [
        "serviceUuid",
        "characteristicUuid",
        "value",
    ]
    assert profile["plugin_contract_hints"][5]["default_arguments"] == [
        "characteristicWriteType=None"
    ]
    assert len(profile["protocol_gap_hints"]) == 3
    assert runtime.diagnostic_value("ble_profile") == (
        "banlanx_scene_ui; command_profile_pending; apk_uuid_pool=5; "
        "uuid_inventory=5; unbound_uuid_candidates=3; legacy_uuid_candidates=2; "
        "plugin_methods=14; arguments=12; result_fields=11; plugin_contracts=6; "
        "channels=6; gaps=3"
    )
    assert runtime.diagnostic_value("ble_uuid_binding_status") == (
        "binding=pending; services=0; write=pending; notify=pending; "
        "unbound_candidates=3; legacy_candidates=2"
    )
    assert "ble_profile" in implemented_sensor_keys(runtime)
    assert "ble_uuid_binding_status" in implemented_sensor_keys(runtime)
    assert runtime.diagnostic_value("ble_known_service_uuid_count") == 0
    assert runtime.diagnostic_value("ble_uuid_pool_count") == 5
    assert runtime.diagnostic_value("ble_uuid_inventory_count") == 5
    assert runtime.diagnostic_value("ble_unbound_uuid_candidate_count") == 3
    assert runtime.diagnostic_value("ble_legacy_uuid_candidate_count") == 2
    assert runtime.diagnostic_value("ble_plugin_method_count") == 14
    assert runtime.diagnostic_value("ble_plugin_argument_count") == 12
    assert runtime.diagnostic_value("ble_plugin_result_field_count") == 11
    assert runtime.diagnostic_value("ble_plugin_contract_hint_count") == 6
    assert runtime.diagnostic_value("ble_plugin_channel_count") == 6
    assert runtime.diagnostic_value("ble_protocol_gap_count") == 3
    assert "ble_uuid_pool_count" in implemented_sensor_keys(runtime)
    assert "ble_uuid_inventory_count" in implemented_sensor_keys(runtime)
    assert "ble_known_service_uuid_count" in implemented_sensor_keys(runtime)
    assert "ble_unbound_uuid_candidate_count" in implemented_sensor_keys(runtime)
    assert "ble_legacy_uuid_candidate_count" in implemented_sensor_keys(runtime)
    assert "ble_plugin_method_count" in implemented_sensor_keys(runtime)
    assert "ble_plugin_argument_count" in implemented_sensor_keys(runtime)
    assert "ble_plugin_result_field_count" in implemented_sensor_keys(runtime)
    assert "ble_plugin_contract_hint_count" in implemented_sensor_keys(runtime)
    assert "ble_plugin_channel_count" in implemented_sensor_keys(runtime)
    assert "ble_protocol_gap_count" in implemented_sensor_keys(runtime)

    known = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "strip"})
    known_profile = runtime_diagnostics(known)["model"]["ble_profile"]

    assert known_profile["command_profile_known"] is True
    assert known_profile["known_service_uuids"] == [
        "0000ffe0-0000-1000-8000-00805f9b34fb"
    ]
    assert known_profile["known_write_uuid"] == (
        "0000ffe1-0000-1000-8000-00805f9b34fb"
    )
    assert known_profile["uuid_binding_status"] == (
        "binding=known; services=1; write=known; notify=known; "
        "unbound_candidates=3; legacy_candidates=2"
    )
    assert known.diagnostic_value("ble_profile") == (
        "banlanx_601; command_profile_known; services=1; "
        "write_uuid_known; apk_uuid_pool=5; uuid_inventory=5; "
        "unbound_uuid_candidates=3; legacy_uuid_candidates=2; "
        "plugin_methods=14; arguments=12; result_fields=11; plugin_contracts=6; "
        "channels=6; gaps=3"
    )
    assert known.diagnostic_value("ble_uuid_binding_status") == (
        "binding=known; services=1; write=known; notify=known; "
        "unbound_candidates=3; legacy_candidates=2"
    )
    assert known.diagnostic_value("ble_known_service_uuid_count") == 1
    assert known.diagnostic_value("ble_uuid_pool_count") == 5
    assert known.diagnostic_value("ble_uuid_inventory_count") == 5
    assert known.diagnostic_value("ble_unbound_uuid_candidate_count") == 3
    assert known.diagnostic_value("ble_legacy_uuid_candidate_count") == 2
    assert known.diagnostic_value("ble_plugin_method_count") == 14
    assert known.diagnostic_value("ble_plugin_argument_count") == 12
    assert known.diagnostic_value("ble_plugin_result_field_count") == 11
    assert known.diagnostic_value("ble_plugin_contract_hint_count") == 6
    assert known.diagnostic_value("ble_plugin_channel_count") == 6
    assert known.diagnostic_value("ble_protocol_gap_count") == 3

    mesh = build_runtime({CONF_MODEL: "RG4", CONF_DEVICE_ID: "mesh"})

    assert runtime_diagnostics(mesh)["model"]["ble_profile"] is None
    assert mesh.diagnostic_value("ble_profile") is None
    assert mesh.diagnostic_value("ble_uuid_binding_status") is None
    assert mesh.diagnostic_value("ble_known_service_uuid_count") is None
    assert mesh.diagnostic_value("ble_uuid_pool_count") is None
    assert mesh.diagnostic_value("ble_uuid_inventory_count") is None
    assert mesh.diagnostic_value("ble_unbound_uuid_candidate_count") is None
    assert mesh.diagnostic_value("ble_legacy_uuid_candidate_count") is None
    assert "ble_uuid_binding_status" not in implemented_sensor_keys(mesh)
    assert "ble_known_service_uuid_count" not in implemented_sensor_keys(mesh)
    assert "ble_uuid_pool_count" not in implemented_sensor_keys(mesh)
    assert "ble_uuid_inventory_count" not in implemented_sensor_keys(mesh)
    assert "ble_unbound_uuid_candidate_count" not in implemented_sensor_keys(mesh)
    assert "ble_legacy_uuid_candidate_count" not in implemented_sensor_keys(mesh)


def test_runtime_diagnostics_exposes_banlanx_cloud_profile() -> None:
    """Diagnostics expose APK cloud/API facts without enabling cloud commands."""
    runtime = build_runtime({CONF_MODEL: "FT001", CONF_DEVICE_ID: "tank"})

    cloud = runtime_diagnostics(runtime)["model"]["cloud_profile"]

    assert cloud["provider"] == "banlanx_cloud"
    assert cloud["model_name"] == "FT001"
    assert cloud["command_protocol_known"] is False
    assert cloud["base_urls"] == [
        "https://app.ledhue.com/spiot2",
        "https://app.ledhue.com/spiot/banlanx2",
        "https://app.ledhue.com/spiot/els/v1",
        "https://app.ledhue.com/spiot/app-link/alexa",
    ]
    assert "/home/device/auth" in cloud["auth_endpoints"]
    assert "/auth/refresh-token" in cloud["account_auth_endpoints"]
    assert "/auth/signIn2" in cloud["account_auth_endpoints"]
    assert "/user/sign-out" in cloud["account_auth_endpoints"]
    assert "/home/device/add" in cloud["device_endpoints"]
    assert "/user/device/post/raw" in cloud["device_endpoints"]
    assert "/user/device/connection/cloud/check" in cloud["device_endpoints"]
    assert cloud["root_device_endpoints"] == [
        "/configureDevice",
        "/device/check-update2",
    ]
    assert cloud["home_device_endpoints"] == [
        "/home/device/add",
        "/home/device/fw_new_version",
        "/home/device/ota",
        "/home/device/reset",
    ]
    assert cloud["btmesh_endpoints"] == [
        "/user/btmesh/get",
        "/user/btmesh/update",
    ]
    assert cloud["local_device_endpoints"] == [
        "/user/local-device/add",
        "/user/local-device/add/batch2",
    ]
    assert cloud["raw_command_endpoints"] == ["/user/device/post/raw"]
    assert "/user/device/post/raw" in cloud["user_device_endpoints"]
    assert "/banlanx/user/alexa/link" in cloud["voice_assistant_endpoints"]
    assert len(cloud["endpoint_inventory"]) == 52
    assert cloud["endpoint_groups"] == [
        "account_auth",
        "device_auth",
        "root_device",
        "home_device",
        "btmesh",
        "user_device",
        "local_device",
        "content",
        "voice_assistant",
    ]
    endpoint_by_path = {
        endpoint["path"]: endpoint for endpoint in cloud["endpoint_inventory"]
    }
    assert endpoint_by_path["/auth/sign-in"] == {
        "group": "account_auth",
        "path": "/auth/sign-in",
        "method": "unknown",
        "auth": "unproven",
        "base_url": "unresolved",
        "command_related": False,
        "evidence": "BanlanX 3.3.1 Flutter libapp.so string",
    }
    assert endpoint_by_path["/user/device/post/raw"] == {
        "group": "user_device",
        "path": "/user/device/post/raw",
        "method": "unknown",
        "auth": "unproven",
        "base_url": "unresolved",
        "command_related": True,
        "evidence": "BanlanX 3.3.1 Flutter libapp.so string",
    }
    assert endpoint_by_path[
        "https://app.ledhue.com/spiot/app-link/alexa"
    ]["group"] == "voice_assistant"
    inventory_paths = [endpoint["path"] for endpoint in cloud["endpoint_inventory"]]
    assert cloud["command_related_endpoint_paths"] == ["/user/device/post/raw"]
    assert cloud["unresolved_base_url_endpoint_paths"] == inventory_paths
    assert cloud["unproven_auth_endpoint_paths"] == inventory_paths
    assert "https://document.ledhue.com/banlanx/about/privacy" in cloud[
        "document_urls"
    ]
    assert (
        "https://document.ledhue.com/banlanx/faq/version/8/zh2"
        in cloud["document_urls"]
    )
    assert "user:token" in cloud["auth_token_hints"]
    assert "user:refresh_token" in cloud["auth_token_hints"]
    assert "refreshToken2" in cloud["auth_token_hints"]
    assert cloud["device_identity_hints"] == [
        "deviceCode",
        "deviceUdids =",
        "device_id = ?",
        "device_key",
        "device_model2",
        "device_name",
        "device_to_group_mapping",
        "device_udid",
        "device_udids2",
        "mobile_device_identifier",
    ]
    assert cloud["http_header_hints"] == [
        "Authorization",
        "Bearer",
        "S-AccessKey",
        "S-AppVer",
        "S-AppVerName2",
        "S-SysCode",
        "S-SysName",
        "S-System",
        "S-Timestamp",
        "content-type:",
        "application/json",
    ]
    assert cloud["signature_hints"] == [
        "buildSignature",
        ", buildSignature:",
        ", nonce =",
        "encrypt nonce =",
        "decrypt nonce =",
    ]
    assert len(cloud["request_contract_hints"]) == 26
    assert cloud["token_contract_hint_strings"] == cloud["auth_token_hints"]
    assert cloud["header_contract_hint_strings"] == cloud["http_header_hints"]
    assert cloud["signature_contract_hint_strings"] == cloud["signature_hints"]
    contract_by_string = {
        hint["apk_string"]: hint for hint in cloud["request_contract_hints"]
    }
    assert contract_by_string["user:token"] == {
        "category": "token_or_auth_storage",
        "apk_string": "user:token",
        "unported_binding_status": "unproven",
        "blocker": "account_token_schema_pending",
        "evidence": "BanlanX 3.3.1 Flutter libapp.so string",
    }
    assert contract_by_string["S-AccessKey"] == {
        "category": "http_header",
        "apk_string": "S-AccessKey",
        "unported_binding_status": "unproven",
        "blocker": "request_signing_headers_pending",
        "evidence": "BanlanX 3.3.1 Flutter libapp.so string",
    }
    assert contract_by_string["buildSignature"] == {
        "category": "signature_or_nonce",
        "apk_string": "buildSignature",
        "unported_binding_status": "unproven",
        "blocker": "request_signing_headers_pending",
        "evidence": "BanlanX 3.3.1 Flutter libapp.so string",
    }
    assert cloud["command_blockers"] == [
        "account_token_schema_pending",
        "request_signing_headers_pending",
        "region_reauth_contract_pending",
        "raw_command_json_envelope_pending",
        "device_bind_ownership_lifecycle_pending",
    ]
    assert "connectCaps=7" in cloud["catalog_hints"]
    assert any("post/raw" in hint for hint in cloud["protocol_gap_hints"])
    assert runtime.diagnostic_value("cloud_profile") == (
        "banlanx_cloud; bases=4; auth=6; account_auth=11; devices=20; "
        "inventory=52; endpoint_groups=9; command_related=1; "
        "unresolved_bases=52; unproven_auth=52; "
        "home_devices=4; user_devices=10; local_devices=2; "
        "btmesh=2; root_devices=2; raw_commands=1; content=9; voice=6; docs=6; "
        "tokens=10; device_identity=10; headers=11; signatures=5; "
        "request_contracts=26; token_contracts=10; header_contracts=11; "
        "signature_contracts=5; "
        "transport=4; gaps=5; blockers=5; "
        "command_protocol_pending; catalog=5"
    )
    for key, expected in {
        "cloud_base_url_count": 4,
        "cloud_endpoint_count": 52,
        "cloud_endpoint_inventory_count": 52,
        "cloud_endpoint_group_count": 9,
        "cloud_command_related_endpoint_count": 1,
        "cloud_unresolved_base_url_endpoint_count": 52,
        "cloud_unproven_auth_endpoint_count": 52,
        "cloud_auth_endpoint_count": 6,
        "cloud_account_auth_endpoint_count": 11,
        "cloud_device_endpoint_count": 20,
        "cloud_home_device_endpoint_count": 4,
        "cloud_user_device_endpoint_count": 10,
        "cloud_local_device_endpoint_count": 2,
        "cloud_btmesh_endpoint_count": 2,
        "cloud_root_device_endpoint_count": 2,
        "cloud_raw_command_endpoint_count": 1,
        "cloud_content_endpoint_count": 9,
        "cloud_voice_endpoint_count": 6,
        "cloud_document_url_count": 6,
        "cloud_auth_token_hint_count": 10,
        "cloud_device_identity_hint_count": 10,
        "cloud_http_header_hint_count": 11,
        "cloud_signature_hint_count": 5,
        "cloud_request_contract_hint_count": 26,
        "cloud_token_contract_hint_count": 10,
        "cloud_header_contract_hint_count": 11,
        "cloud_signature_contract_hint_count": 5,
        "cloud_transport_hint_count": 4,
        "cloud_protocol_gap_count": 5,
        "cloud_command_blocker_count": 5,
    }.items():
        assert runtime.diagnostic_value(key) == expected
    assert runtime.diagnostic_value("cloud_raw_command_endpoint") == (
        "/user/device/post/raw"
    )
    sensor_keys = implemented_sensor_keys(runtime)
    for key in {
        "cloud_profile",
        "cloud_base_url_count",
        "cloud_endpoint_count",
        "cloud_endpoint_inventory_count",
        "cloud_endpoint_group_count",
        "cloud_command_related_endpoint_count",
        "cloud_unresolved_base_url_endpoint_count",
        "cloud_unproven_auth_endpoint_count",
        "cloud_auth_endpoint_count",
        "cloud_account_auth_endpoint_count",
        "cloud_device_endpoint_count",
        "cloud_home_device_endpoint_count",
        "cloud_user_device_endpoint_count",
        "cloud_local_device_endpoint_count",
        "cloud_btmesh_endpoint_count",
        "cloud_root_device_endpoint_count",
        "cloud_raw_command_endpoint_count",
        "cloud_content_endpoint_count",
        "cloud_voice_endpoint_count",
        "cloud_document_url_count",
        "cloud_auth_token_hint_count",
        "cloud_device_identity_hint_count",
        "cloud_http_header_hint_count",
        "cloud_signature_hint_count",
        "cloud_request_contract_hint_count",
        "cloud_token_contract_hint_count",
        "cloud_header_contract_hint_count",
        "cloud_signature_contract_hint_count",
        "cloud_transport_hint_count",
        "cloud_protocol_gap_count",
        "cloud_command_blocker_count",
        "cloud_raw_command_endpoint",
    }:
        assert key in sensor_keys

    ble_only = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})

    assert runtime_diagnostics(ble_only)["model"]["cloud_profile"] is None
    assert ble_only.diagnostic_value("cloud_profile") is None
    assert ble_only.diagnostic_value("cloud_endpoint_count") is None
    assert ble_only.diagnostic_value("cloud_endpoint_inventory_count") is None
    assert ble_only.diagnostic_value("cloud_endpoint_group_count") is None
    assert ble_only.diagnostic_value("cloud_command_related_endpoint_count") is None
    assert (
        ble_only.diagnostic_value("cloud_unresolved_base_url_endpoint_count")
        is None
    )
    assert ble_only.diagnostic_value("cloud_unproven_auth_endpoint_count") is None
    assert ble_only.diagnostic_value("cloud_account_auth_endpoint_count") is None
    assert ble_only.diagnostic_value("cloud_user_device_endpoint_count") is None
    assert ble_only.diagnostic_value("cloud_device_identity_hint_count") is None
    assert ble_only.diagnostic_value("cloud_http_header_hint_count") is None
    assert ble_only.diagnostic_value("cloud_signature_hint_count") is None
    assert ble_only.diagnostic_value("cloud_request_contract_hint_count") is None
    assert ble_only.diagnostic_value("cloud_token_contract_hint_count") is None
    assert ble_only.diagnostic_value("cloud_header_contract_hint_count") is None
    assert ble_only.diagnostic_value("cloud_signature_contract_hint_count") is None
    assert ble_only.diagnostic_value("cloud_protocol_gap_count") is None
    assert ble_only.diagnostic_value("cloud_command_blocker_count") is None
    assert ble_only.diagnostic_value("cloud_raw_command_endpoint") is None


def test_runtime_diagnostics_exposes_network_profiles() -> None:
    """Diagnostics expose APK network-controller package and editor facts."""
    runtime = build_runtime({CONF_MODEL: "SP802E", CONF_DEVICE_ID: "panel"})

    diagnostics = runtime_diagnostics(runtime)
    regular_lfx_effects = [
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
    ]
    regular_lfx_effect_assets = [
        "packages/sp802e/assets/icons/ic_lfx_black_hole.png",
        "packages/sp802e/assets/icons/ic_lfx_bursts.png",
        "packages/sp802e/assets/icons/ic_lfx_circle_fade.png",
        "packages/sp802e/assets/icons/ic_lfx_diagonal_fade.png",
        "packages/sp802e/assets/icons/ic_lfx_diamond_fade.png",
        "packages/sp802e/assets/icons/ic_lfx_geq.png",
        "packages/sp802e/assets/icons/ic_lfx_hiphotic.png",
        "packages/sp802e/assets/icons/ic_lfx_horiz_dna.png",
        "packages/sp802e/assets/icons/ic_lfx_horiz_fade.png",
        "packages/sp802e/assets/icons/ic_lfx_hyper_fade.png",
        "packages/sp802e/assets/icons/ic_lfx_matrix.png",
        "packages/sp802e/assets/icons/ic_lfx_metaballs.png",
        "packages/sp802e/assets/icons/ic_lfx_palette.png",
        "packages/sp802e/assets/icons/ic_lfx_party.png",
        "packages/sp802e/assets/icons/ic_lfx_plasmaball.png",
        "packages/sp802e/assets/icons/ic_lfx_soap.png",
        "packages/sp802e/assets/icons/ic_lfx_squaredswirl.png",
        "packages/sp802e/assets/icons/ic_lfx_static.png",
        "packages/sp802e/assets/icons/ic_lfx_vert_dna.png",
        "packages/sp802e/assets/icons/ic_lfx_waverly.png",
    ]

    assert diagnostics["model"]["network_profile"] == {
        "family": "banlanx_network",
        "package": "packages/sp802e",
        "route_hints": [
            "/sp802e",
            "/sp802e/settings",
            "/sp802e/edit_led_layout",
        ],
        "control_surfaces": [
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
        ],
        "content_modes": [
            "Regular LFX",
            "Animation LFX",
            "GIF LFX",
            "Graffiti LFX",
            "Image LFX",
            "Text LFX",
            "Rhythm LFX",
        ],
        "artnet_fields": [],
        "port_fields": [],
        "playlist_actions": [],
        "matrix_music_controls": [
            "setMatrixMusicMode",
            "setMatrixMusicDotColor",
            "setMatrixMusicColColor",
            "setMatrixMusicColColorType",
            "setMatrixMusicColGradientColor",
        ],
        "supports_artnet": False,
        "supports_lfx": True,
        "panel_layout_supported": True,
        "regular_lfx_effects": regular_lfx_effects,
        "regular_lfx_effect_assets": regular_lfx_effect_assets,
        "lfx_gif_count": 30,
        "lfx_gif_assets": [
            "packages/sp802e/assets/gifs/200.gif",
            "packages/sp802e/assets/gifs/207.gif",
            "packages/sp802e/assets/gifs/215_3.gif",
            "packages/sp802e/assets/gifs/223.gif",
            "packages/sp802e/assets/gifs/235_2.gif",
            "packages/sp802e/assets/gifs/256_2.gif",
            "packages/sp802e/assets/gifs/264.gif",
            "packages/sp802e/assets/gifs/266.gif",
            "packages/sp802e/assets/gifs/268.gif",
            "packages/sp802e/assets/gifs/269.gif",
            "packages/sp802e/assets/gifs/272.gif",
            "packages/sp802e/assets/gifs/292_3.gif",
            "packages/sp802e/assets/gifs/302.gif",
            "packages/sp802e/assets/gifs/314.gif",
            "packages/sp802e/assets/gifs/334.gif",
            "packages/sp802e/assets/gifs/360.gif",
            "packages/sp802e/assets/gifs/361.gif",
            "packages/sp802e/assets/gifs/361_2.gif",
            "packages/sp802e/assets/gifs/362.gif",
            "packages/sp802e/assets/gifs/365.gif",
            "packages/sp802e/assets/gifs/376.gif",
            "packages/sp802e/assets/gifs/418_2.gif",
            "packages/sp802e/assets/gifs/427_2.gif",
            "packages/sp802e/assets/gifs/453_3.gif",
            "packages/sp802e/assets/gifs/466.gif",
            "packages/sp802e/assets/gifs/474.gif",
            "packages/sp802e/assets/gifs/485_2.gif",
            "packages/sp802e/assets/gifs/cs_1.gif",
            "packages/sp802e/assets/gifs/cs_2.gif",
            "packages/sp802e/assets/gifs/cs_3.gif",
        ],
        "app_method_hints": [
            "setLedPanelLayout",
            "setLfxMode",
            "setLfxSpeed",
            "setLfxPixelCount",
            "setLfxLoopMode",
            "setLfxColor",
            "setLfxColorTemp",
            "setLfxGradient",
            "setLfxDir",
            "setOnOffLfx",
            "setBrightness",
            "setSensitivity",
            "setSoundSource",
            "setMatrixMusicMode",
            "setMatrixMusicDotColor",
            "setMatrixMusicColColor",
            "setMatrixMusicColColorType",
            "setMatrixMusicColGradientColor",
        ],
        "workflow_hints": [
            "SP802E reuses the shared /device/lfx creation routes",
            (
                "Matrix music setters expose dot, column, color-type, and "
                "gradient color controls"
            ),
            (
                "libwled_lfx.so exposes matrix layout and 2D WLED-style "
                "effect generator symbols"
            ),
            (
                "LFX favorite and material assets are present alongside 30 "
                "GIF previews"
            ),
        ],
        "raw_string_hints": [
            "lfxDurationInLoop: ",
            "lfxLoopMode: ",
            "lfxMode-",
            "lfxParams",
            "lfx_color_sets",
            "lfx_colors",
            "lfx_gradients",
            "lfx_mode_id",
            "lfx_mode_type",
            "gif_lfx_frames",
            "led_matrix_info",
            "matrixType = ",
            "wifiState",
            "wifiStrength2",
            "supportGetNetInfo",
        ],
        "import_constraints": [
            "LED panel size must stay within canvas bounds",
            (
                "Recommended canvas size should match the total size of the "
                "LED panels"
            ),
        ],
        "catalog_hints": [
            "model_id=158",
            "parent_id=none",
            "connectCaps=3",
            "specFunctions=70",
            "colorCap=1",
            "transports=ble,lan",
            "supportGetNetInfo=9",
        ],
        "transport_hints": [
            "connectCaps=3 maps to BLE plus LAN in the catalog",
            "supportGetNetInfo=9 is present on SP802E",
            (
                "The APK exposes Bonsoir/Android NSD, "
                "com.spled.plugins/multicast_lock, mDNS 224.0.0.251:5353, "
                "and raw datagram sockets, but no SP802E socket frame"
            ),
            (
                "SP802E may need BLE for setup or network-info flow and LAN "
                "for local content control"
            ),
        ],
        "protocol_gap_hints": [
            "No old-UniLED SP801E/SP802E command implementation was found",
            (
                "No confirmed LAN discovery response or local socket frame "
                "has been mapped"
            ),
            (
                "No concrete DNS-SD service type was recovered from the APK "
                "string surfaces"
            ),
            "No Art-Net configuration payload encoding has been mapped",
            "No SP802E BLE/LAN LFX command or status parser has been mapped",
            (
                "No playlist, scene-list, DXF import, or panel-layout "
                "packet flow is known"
            ),
        ],
        "command_blockers": [
            "network_discovery_pending",
            "network_socket_frame_pending",
            "network_dns_sd_service_pending",
            "network_lfx_packet_pending",
            "network_lfx_status_parser_pending",
            "network_panel_layout_pending",
            "network_matrix_music_pending",
        ],
        "native_library_hints": [
            "libwled_lfx.so",
            "setup_matrix_layout",
            "switch_lfx_mode",
            "set_effect_params",
            "recover_effect_param",
            "updateMusicDat",
            "initRegularLfxGenerator",
            "render_frame",
            "get_frame_data",
            "mode_2Dmatrix",
            "mode_2Dmusicsoap",
            "mode_2Dmusicsquaredswirl",
            "setPixelColorXY",
            "getPixelColorXY",
            "setLineColorXY",
            "wled_DrawCircle",
        ],
        "native_frame_hints": [
            "render_frame",
            "get_frame_data",
            "setPixelColorXY",
            "getPixelColorXY",
            "setLineColorXY",
            "addPixelColorXY",
            "fadePixelColorXY",
            "sysMatrixW",
            "sysMatrixH",
        ],
        "native_lfx_param_hints": [
            "switch_lfx_mode",
            "set_effect_params",
            "recover_effect_param",
            "effect_prj",
            "Create_effectsTables",
            "EFFECT_GENERATOR_CONSTRUCTORS",
            "Dyneffect_num",
            "Rhyeffect_num",
        ],
        "native_effect_generator_hints": [
            "create_circle_fade_effect_generator",
            "create_diamond_fade_effect_generator",
            "create_horiz_fade_effect_generator",
            "create_horiz_sym_fade_effect_generator",
            "create_hyper_fade_effect_generator",
            "create_main_diagonally_fade_effect_generator",
            "create_plasma_fade_effect_generator",
            "create_regular_fade_effect_generator",
            "create_secondary_diagonally_fade_effect_generator",
            "create_vert_fade_effect_generator",
            "create_vert_sym_fade_effect_generator",
        ],
        "native_matrix_mode_hints": [
            "setup_matrix_layout",
            "mode_2Dmatrix",
            "mode_2Dmusicsoap",
            "mode_2Dmusicsquaredswirl",
            "sysMatrixW",
            "sysMatrixH",
            "staRGBIC",
            "RGBCW",
        ],
        "native_pixel_helper_hints": [
            "render_frame",
            "get_frame_data",
            "setPixelColorXY",
            "getPixelColorXY",
            "setLineColorXY",
            "addPixelColorXY",
            "fadePixelColorXY",
            "fillGradientRGB",
            "wled_DrawCircle",
        ],
        "native_export_hints": [
            "libwled_lfx.so ELF .dynsym exports 186 named symbols",
            (
                "High-signal export scan found 35 "
                "matrix/effect/LFX/generator-related symbols"
            ),
            (
                "The recovered RGBCW native string is not exported in "
                ".dynsym"
            ),
            (
                "Exported setup and mode helpers include setup_matrix_layout, "
                "switch_lfx_mode, initRegularLfxGenerator, set_effect_params, "
                "and recover_effect_param"
            ),
            "Detailed dynsym scan places set_effect_params at 0x0000a4dd (26 bytes)",
            (
                "Exported matrix/frame helpers include setPixelColorXY, "
                "getPixelColorXY, setLineColorXY, render_frame, "
                "get_frame_data, sysMatrixW, and sysMatrixH"
            ),
            (
                "Exported regular-effect generator names include "
                "create_horiz_fade_effect_generator, "
                "create_circle_fade_effect_generator, "
                "create_diamond_fade_effect_generator, and "
                "create_plasma_fade_effect_generator"
            ),
            (
                "Exported symbols still do not expose SP802E BLE/LAN command "
                "envelopes, local socket frames, or status parser offsets"
            ),
        ],
        "command_protocol_known": False,
        "package_asset_count": 81,
        "apk_asset_evidence": [
            "packages/sp802e/assets/icons/ic_lfx.png",
            "packages/sp802e/assets/icons/ic_gif_lfx.png",
            "packages/sp802e/assets/icons/ic_graffiti_lfx.png",
            "packages/sp802e/assets/icons/ic_image_lfx.png",
            "packages/sp802e/assets/icons/ic_text_lfx.png",
            "packages/sp802e/assets/icons/ic_rhythm_lfx.png",
            "packages/sp802e/assets/icons/ic_animation_lfx.png",
            "packages/sp802e/assets/icons/ic_material.png",
            "packages/sp802e/assets/icons/ic_favorite_lfx.png",
            "packages/sp802e/assets/images/setup_led_panel_layout.png",
            "packages/sp802e/assets/images/device_banner.png",
            "packages/sp802e/assets/images/scene_background.png",
            "packages/sp802e/assets/images/tooltip_slide_horiz.png",
            "packages/sp802e/assets/gifs/200.gif",
            "packages/sp802e/assets/gifs/207.gif",
            "packages/sp802e/assets/gifs/215_3.gif",
            "packages/sp802e/assets/gifs/223.gif",
            "packages/sp802e/assets/gifs/235_2.gif",
            "packages/sp802e/assets/gifs/256_2.gif",
            "packages/sp802e/assets/gifs/264.gif",
            "packages/sp802e/assets/gifs/266.gif",
            "packages/sp802e/assets/gifs/268.gif",
            "packages/sp802e/assets/gifs/269.gif",
            "packages/sp802e/assets/gifs/272.gif",
            "packages/sp802e/assets/gifs/292_3.gif",
            "packages/sp802e/assets/gifs/302.gif",
            "packages/sp802e/assets/gifs/314.gif",
            "packages/sp802e/assets/gifs/334.gif",
            "packages/sp802e/assets/gifs/360.gif",
            "packages/sp802e/assets/gifs/361.gif",
            "packages/sp802e/assets/gifs/361_2.gif",
            "packages/sp802e/assets/gifs/362.gif",
            "packages/sp802e/assets/gifs/365.gif",
            "packages/sp802e/assets/gifs/376.gif",
            "packages/sp802e/assets/gifs/418_2.gif",
            "packages/sp802e/assets/gifs/427_2.gif",
            "packages/sp802e/assets/gifs/453_3.gif",
            "packages/sp802e/assets/gifs/466.gif",
            "packages/sp802e/assets/gifs/474.gif",
            "packages/sp802e/assets/gifs/485_2.gif",
            "packages/sp802e/assets/gifs/cs_1.gif",
            "packages/sp802e/assets/gifs/cs_2.gif",
            "packages/sp802e/assets/gifs/cs_3.gif",
        ],
        "apk_string_evidence": [
            (
                "Native route strings expose /sp802e, "
                "/sp802e/settings, and /sp802e/edit_led_layout"
            ),
            (
                "Native strings expose LFX setter names including "
                "setLfxMode, setLfxSpeed, and setLedPanelLayout"
            ),
            "Native library exports expose libwled_lfx.so matrix/LFX symbols",
            (
                "Native library strings expose SP802E LFX parameter and "
                "mode-switch helpers"
            ),
            (
                "Native library strings expose SP802E regular LFX effect "
                "generator anchors"
            ),
            (
                "Native library strings expose SP802E matrix layout and "
                "music-mode anchors"
            ),
            "Native library strings expose SP802E pixel/frame helper anchors",
            (
                "ELF .dynsym export inspection confirms SP802E matrix/effect "
                "helpers but no BLE or LAN packet envelope"
            ),
            (
                "Native strings expose LFX state labels, gif_lfx_frames, "
                "led_matrix_info, and Wi-Fi state labels"
            ),
            (
                "Assets expose LFX modes for regular, animation, GIF, "
                "graffiti, image, text, and rhythm content"
            ),
            "Assets expose 20 regular LFX effect icons for SP802E",
            "The asset manifest exposes 30 packages/sp802e/assets/gifs previews",
        ],
    }
    assert runtime.diagnostic_value("network_profile") == (
        "banlanx_network; package=packages/sp802e; "
        "surfaces=12; modes=7; lfx_gifs=30; lfx_effects=20; "
        "matrix_music_controls=5; panel_layout; methods=18; native_hints=16; "
        "native_frames=9; native_lfx_params=8; native_effect_generators=11; "
        "native_matrix_modes=8; native_pixel_helpers=9; native_exports=8; "
        "workflows=4; raw_strings=15; constraints=2; catalog=7; transport=4; "
        "gaps=6; blockers=7; package_assets=81; command_protocol_pending; "
        "routes=3"
    )
    assert runtime.diagnostic_value("network_surface_count") == 12
    assert runtime.diagnostic_value("network_content_mode_count") == 7
    assert runtime.diagnostic_value("network_artnet_field_count") == 0
    assert runtime.diagnostic_value("network_port_field_count") == 0
    assert runtime.diagnostic_value("network_playlist_action_count") == 0
    assert runtime.diagnostic_value("network_matrix_music_control_count") == 5
    assert runtime.diagnostic_value("network_lfx_effect_count") == 20
    assert runtime.diagnostic_value("network_lfx_gif_count") == 30
    assert runtime.diagnostic_value("network_route_count") == 3
    assert runtime.diagnostic_value("network_regular_lfx_effect_asset_count") == 20
    assert runtime.diagnostic_value("network_lfx_gif_asset_count") == 30
    assert runtime.diagnostic_value("network_app_method_count") == 18
    assert runtime.diagnostic_value("network_workflow_hint_count") == 4
    assert runtime.diagnostic_value("network_raw_string_hint_count") == 15
    assert runtime.diagnostic_value("network_import_constraint_count") == 2
    assert runtime.diagnostic_value("network_catalog_hint_count") == 7
    assert runtime.diagnostic_value("network_transport_hint_count") == 4
    assert runtime.diagnostic_value("network_native_library_hint_count") == 16
    assert runtime.diagnostic_value("network_native_frame_hint_count") == 9
    assert runtime.diagnostic_value("network_native_lfx_param_hint_count") == 8
    assert (
        runtime.diagnostic_value("network_native_effect_generator_hint_count")
        == 11
    )
    assert runtime.diagnostic_value("network_native_matrix_mode_hint_count") == 8
    assert runtime.diagnostic_value("network_native_pixel_helper_hint_count") == 9
    assert runtime.diagnostic_value("network_native_export_hint_count") == 8
    assert runtime.diagnostic_value("network_protocol_gap_count") == 6
    assert runtime.diagnostic_value("network_command_blocker_count") == 7
    assert runtime.diagnostic_value("network_apk_asset_evidence_count") == 43
    assert runtime.diagnostic_value("network_apk_package_asset_count") == 81
    assert runtime.diagnostic_value("network_apk_string_evidence_count") == 12
    assert "network_profile" in implemented_sensor_keys(runtime)
    assert "network_surface_count" in implemented_sensor_keys(runtime)
    assert "network_content_mode_count" in implemented_sensor_keys(runtime)
    assert "network_artnet_field_count" in implemented_sensor_keys(runtime)
    assert "network_port_field_count" in implemented_sensor_keys(runtime)
    assert "network_playlist_action_count" in implemented_sensor_keys(runtime)
    assert "network_matrix_music_control_count" in implemented_sensor_keys(runtime)
    assert "network_lfx_effect_count" in implemented_sensor_keys(runtime)
    assert "network_lfx_gif_count" in implemented_sensor_keys(runtime)
    assert "network_route_count" in implemented_sensor_keys(runtime)
    assert "network_regular_lfx_effect_asset_count" in implemented_sensor_keys(
        runtime
    )
    assert "network_lfx_gif_asset_count" in implemented_sensor_keys(runtime)
    assert "network_app_method_count" in implemented_sensor_keys(runtime)
    assert "network_workflow_hint_count" in implemented_sensor_keys(runtime)
    assert "network_raw_string_hint_count" in implemented_sensor_keys(runtime)
    assert "network_import_constraint_count" in implemented_sensor_keys(runtime)
    assert "network_catalog_hint_count" in implemented_sensor_keys(runtime)
    assert "network_transport_hint_count" in implemented_sensor_keys(runtime)
    assert "network_native_library_hint_count" in implemented_sensor_keys(runtime)
    assert "network_native_frame_hint_count" in implemented_sensor_keys(runtime)
    assert "network_native_lfx_param_hint_count" in implemented_sensor_keys(runtime)
    assert "network_native_effect_generator_hint_count" in implemented_sensor_keys(
        runtime
    )
    assert "network_native_matrix_mode_hint_count" in implemented_sensor_keys(runtime)
    assert "network_native_pixel_helper_hint_count" in implemented_sensor_keys(
        runtime
    )
    assert "network_native_export_hint_count" in implemented_sensor_keys(runtime)
    assert "network_protocol_gap_count" in implemented_sensor_keys(runtime)
    assert "network_command_blocker_count" in implemented_sensor_keys(runtime)
    assert "network_apk_asset_evidence_count" in implemented_sensor_keys(runtime)
    assert "network_apk_package_asset_count" in implemented_sensor_keys(runtime)
    assert "network_apk_string_evidence_count" in implemented_sensor_keys(runtime)

    sp801 = build_runtime({CONF_MODEL: "SP801E", CONF_DEVICE_ID: "artnet"})

    assert sp801.diagnostic_value("network_profile") == (
        "banlanx_network; package=packages/module_sp801e; "
        "surfaces=11; modes=7; artnet; artnet_fields=4; port_fields=6; "
        "playlist_actions=4; panel_layout; methods=7; workflows=4; "
        "raw_strings=16; constraints=4; catalog=6; "
        "transport=3; gaps=6; blockers=7; package_assets=143; "
        "command_protocol_pending; routes=1"
    )
    assert sp801.diagnostic_value("network_surface_count") == 11
    assert sp801.diagnostic_value("network_content_mode_count") == 7
    assert sp801.diagnostic_value("network_artnet_field_count") == 4
    assert sp801.diagnostic_value("network_port_field_count") == 6
    assert sp801.diagnostic_value("network_playlist_action_count") == 4
    assert sp801.diagnostic_value("network_matrix_music_control_count") == 0
    assert sp801.diagnostic_value("network_lfx_effect_count") == 0
    assert sp801.diagnostic_value("network_lfx_gif_count") == 0
    assert sp801.diagnostic_value("network_route_count") == 1
    assert sp801.diagnostic_value("network_regular_lfx_effect_asset_count") == 0
    assert sp801.diagnostic_value("network_lfx_gif_asset_count") == 0
    assert sp801.diagnostic_value("network_app_method_count") == 7
    assert sp801.diagnostic_value("network_workflow_hint_count") == 4
    assert sp801.diagnostic_value("network_raw_string_hint_count") == 16
    assert sp801.diagnostic_value("network_import_constraint_count") == 4
    assert sp801.diagnostic_value("network_catalog_hint_count") == 6
    assert sp801.diagnostic_value("network_transport_hint_count") == 3
    assert sp801.diagnostic_value("network_native_library_hint_count") == 0
    assert sp801.diagnostic_value("network_native_frame_hint_count") == 0
    assert sp801.diagnostic_value("network_native_lfx_param_hint_count") == 0
    assert (
        sp801.diagnostic_value("network_native_effect_generator_hint_count") == 0
    )
    assert sp801.diagnostic_value("network_native_matrix_mode_hint_count") == 0
    assert sp801.diagnostic_value("network_native_pixel_helper_hint_count") == 0
    assert sp801.diagnostic_value("network_native_export_hint_count") == 0
    assert sp801.diagnostic_value("network_protocol_gap_count") == 6
    assert sp801.diagnostic_value("network_command_blocker_count") == 7
    assert sp801.diagnostic_value("network_apk_asset_evidence_count") == 21
    assert sp801.diagnostic_value("network_apk_package_asset_count") == 143
    assert sp801.diagnostic_value("network_apk_string_evidence_count") == 8
    sp801_profile = runtime_diagnostics(sp801)["model"]["network_profile"]
    assert sp801_profile["supports_artnet"] is True
    assert sp801_profile["supports_lfx"] is False
    assert sp801_profile["package_asset_count"] == 143
    assert sp801_profile["route_hints"] == ["/sp801e"]
    assert sp801_profile["artnet_fields"] == [
        "portActions",
        "portUniverseCounts",
        "protocolVersion",
        "startUniverse",
    ]
    assert sp801_profile["port_fields"] == [
        "channel_index",
        "sp_channel_group",
        "portDriverType",
        "portId",
        "portNo",
        "port_id",
    ]
    assert sp801_profile["playlist_actions"] == [
        "getPlaylistList",
        "addPlaylist",
        "updatePlaylist",
        "removePlaylist",
    ]
    assert sp801_profile["matrix_music_controls"] == []
    assert sp801_profile["native_lfx_param_hints"] == []
    assert sp801_profile["native_effect_generator_hints"] == []
    assert sp801_profile["native_matrix_mode_hints"] == []
    assert sp801_profile["native_pixel_helper_hints"] == []
    assert sp801_profile["app_method_hints"] == [
        "getNetworkInfo",
        "getArtNetConfig",
        "setArtNetConfig",
        "getPlaylistList",
        "addPlaylist",
        "updatePlaylist",
        "removePlaylist",
    ]
    assert sp801_profile["raw_string_hints"] == [
        "portActions: [",
        "portUniverseCounts: [",
        "protocolVersion: ",
        "startUniverse: ",
        (
            "CREATE TABLE channel (id INTEGER PRIMARY KEY, "
            "device_id INTEGER, channel_index INTEGER, name TEXT)"
        ),
        (
            "CREATE TABLE sp_channel_group (id INTEGER PRIMARY KEY, "
            "device_id INTEGER, group_id INTEGER, name TEXT, channels INTEGER)"
        ),
        "channel_index",
        "device_id = ? AND channel_index = ?",
        "peripheral_group_id = ? AND channel_id = ?",
        "portDriverType",
        "portId",
        "portNo",
        "port_id",
        "music/playlist",
        "scene_playlist_action_bar",
        "scene_playlist_action_bar_empty",
    ]
    assert sp801_profile["catalog_hints"] == [
        "model_id=157",
        "parent_id=none",
        "connectCaps=2",
        "specFunctions=68",
        "colorCap=1",
        "transports=lan",
    ]
    assert sp801_profile["command_blockers"] == [
        "network_discovery_pending",
        "network_socket_frame_pending",
        "network_dns_sd_service_pending",
        "network_artnet_config_pending",
        "network_playlist_packet_pending",
        "network_dxf_import_pending",
        "network_panel_layout_pending",
    ]
    assert sp801_profile["import_constraints"] == [
        (
            "Art-Net V4 control is expected to be handled by external "
            "Art-Net lighting software"
        ),
        "DXF imports are limited to no more than 4 ports",
        "DXF imports are limited to no more than 1024 LEDs per port",
        (
            "LED screen pixel count cannot exceed 1024 in the visible layout "
            "strings"
        ),
    ]

    non_network = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})
    assert non_network.diagnostic_value("network_app_method_count") is None
    assert non_network.diagnostic_value("network_artnet_field_count") is None
    assert non_network.diagnostic_value("network_command_blocker_count") is None
    assert "network_app_method_count" not in implemented_sensor_keys(non_network)
    assert "network_artnet_field_count" not in implemented_sensor_keys(non_network)
    assert "network_command_blocker_count" not in implemented_sensor_keys(
        non_network
    )


def test_runtime_diagnostics_exposes_mesh_profile_for_rg4() -> None:
    """Diagnostics expose old-UniLED mesh facts and ported command status."""
    runtime = build_runtime({CONF_MODEL: "RG4", CONF_DEVICE_ID: "remote"})

    diagnostics = runtime_diagnostics(runtime)

    assert diagnostics["model"]["support_level"] == "limited"
    assert runtime.diagnostic_value("support_level") == "limited"
    assert diagnostics["model"]["mesh_profile"] == {
        "family": "zengge_mesh",
        "protocol_name": "telink_zengge",
        "package": "packages/accessories",
        "service_uuid": "00010203-0405-0607-0809-0a0b0c0d1910",
        "status_uuid": "00010203-0405-0607-0809-0a0b0c0d1911",
        "command_uuid": "00010203-0405-0607-0809-0a0b0c0d1912",
        "pair_uuid": "00010203-0405-0607-0809-0a0b0c0d1914",
        "manufacturer_id": 63517,
        "telink_manufacturer_id": 529,
        "default_mesh_uuid": 529,
        "requires_pairing": True,
        "requires_cloud_mesh_credentials": True,
        "old_uniled_protocol_known": True,
        "core_command_protocol_known": True,
        "status_uses_notifications": True,
        "effect_count": 20,
        "command_names": [
            "status_notify",
            "state_query",
            "power",
            "brightness",
            "rgb",
            "color_temp",
            "warm_white",
            "effect",
        ],
        "effect_command_fields": [
            "command=0xed",
            "payload[0]=0xff device_type",
            "payload[1]=effect",
            "payload[2]=speed",
            "payload[3]=level",
            "old-UniLED default speed=0",
            "old-UniLED default level=100",
        ],
        "sig_mesh_uuid_hints": list(SIG_MESH_UUID_HINTS),
        "control_gap_hints": [
            "Old UniLED exposed Zengge nodes as light/sensor features only",
            (
                "Effect speed/level controls resend the current effect with "
                "the edited byte"
            ),
            (
                "Known node metadata from advertisements and MagicHue cloud "
                "import is registered"
            ),
            (
                "Remote and non-light mesh events still need notification mapping"
            ),
        ],
        "control_blockers": [
            "mesh_remote_event_parser_pending",
            "mesh_provisioning_frame_pending",
            "mesh_group_management_pending",
            "mesh_node_management_controls_pending",
        ],
        "route_hints": [
            "/device/ble_mesh_rc",
            "/device/ble_mesh_rc/provisioning_guide",
        ],
        "provisioning_hints": [
            "One-touch provisioning and remote control of zones",
            (
                "Long press the Provisioning button until the indicator light "
                "flashes twice quickly"
            ),
            (
                "2. Provisioning automatically ends after 90 seconds. If "
                "there are still unprovisioned devices nearby, you can long "
                "press the button again to continue provisioning;"
            ),
            (
                "3. During the provisioning process, other devices cannot be "
                "controlled. You can press the provisioning button again to "
                "end provisioning."
            ),
            "If indicator light flashes rapidly, it indicates abnormal provisioning",
            "Indicator breathing means provisioning is in progress",
            "Indicator off means provisioning is complete",
            "Found 1 provisioned device",
            "assigned provisioner unicast address:",
            (
                "Invalid PDU(The provisioning protocol PDU is not "
                "recognized by the device.)"
            ),
            (
                "Out of Resources(The provisioning protocol cannot be "
                "continued due to insufficient resources in the device.)2"
            ),
        ],
        "provisioning_state_hints": [
            "provisioningStart",
            "provisioningInvite",
            "provisioningPublicKey",
            "provisioningData",
            "provisioningConfirmation",
            "provisioningRandom",
            "provisioningInputComplete",
            "provisioningComplete",
            "provisioningFailed",
        ],
        "package_asset_count": 9,
        "apk_asset_evidence": [
            "packages/accessories/assets/icons/ble_mesh_provisioning.png",
            "packages/accessories/assets/icons/mesh_group.png",
            "packages/accessories/assets/icons/mesh_node.png",
            "packages/accessories/assets/images/fast_provisioning_guide_1.png",
            "packages/accessories/assets/images/fast_provisioning_guide_2.png",
            "packages/accessories/assets/images/fast_provisioning_guide_3.png",
            "packages/accessories/assets/images/rg4_reconnect_guide.png",
            "packages/accessories/assets/images/rg4_screen_head_bg.png",
            "packages/accessories/assets/images/rg4_zones_bg.png",
        ],
        "apk_string_evidence": [
            "Catalog records route RG4 to /device/ble_mesh_rc",
            "Native routes expose /device/ble_mesh_rc/provisioning_guide",
            "Native strings expose provisioner_uuid",
            "Native strings expose provisioningCapabilities",
            "Native strings expose one-touch provisioning and zone remote wording",
            "Native strings expose 90-second fast provisioning timeout text",
            "Native strings expose mesh provisioning state callback names",
            (
                "Native strings expose provisioning error labels for Invalid "
                "PDU and Out of Resources"
            ),
        ],
    }
    assert runtime.diagnostic_value("mesh_profile") == (
        "zengge_mesh; telink_zengge; core_protocol_known; "
        "pairing_required; old_uniled_protocol_known; "
        "service=00010203-0405-0607-0809-0a0b0c0d1910; effects=20; "
        "commands=8; effect_fields=7; sig_mesh_uuids=6; gaps=4; "
        "blockers=4; routes=2; provisioning=11; provisioning_states=9; "
        "package_assets=9; apk_assets=9; apk_strings=8"
    )
    assert runtime.diagnostic_value("mesh_route_count") == 2
    assert runtime.diagnostic_value("mesh_provisioning_hint_count") == 11
    assert runtime.diagnostic_value("mesh_provisioning_state_count") == 9
    assert runtime.diagnostic_value("mesh_sig_mesh_uuid_hint_count") == 6
    assert runtime.diagnostic_value("mesh_control_blocker_count") == 4
    assert runtime.diagnostic_value("mesh_apk_asset_evidence_count") == 9
    assert runtime.diagnostic_value("mesh_apk_package_asset_count") == 9
    assert runtime.diagnostic_value("mesh_apk_string_evidence_count") == 8
    assert runtime.diagnostic_value("mesh_role") == (
        "zengge_mesh; transport_pending; unpaired; nodes=0; "
        "command_nodes=0; strip_nodes=0; bulb_nodes=0; "
        "panel_nodes=0; bridge_seen=False"
    )
    assert runtime.diagnostic_value("mesh_known_node_count") == 0
    assert runtime.diagnostic_value("mesh_command_node_count") == 0
    assert runtime.diagnostic_value("mesh_strip_node_count") == 0
    assert runtime.diagnostic_value("mesh_bulb_node_count") == 0
    assert runtime.diagnostic_value("mesh_panel_node_count") == 0
    assert runtime.diagnostic_value("mesh_bridge_seen") is False
    assert "mesh_role" in implemented_sensor_keys(runtime)
    assert "mesh_known_node_count" in implemented_sensor_keys(runtime)
    assert "mesh_command_node_count" in implemented_sensor_keys(runtime)
    assert "mesh_strip_node_count" in implemented_sensor_keys(runtime)
    assert "mesh_bulb_node_count" in implemented_sensor_keys(runtime)
    assert "mesh_panel_node_count" in implemented_sensor_keys(runtime)
    assert "mesh_bridge_seen" in implemented_sensor_keys(runtime)
    assert "mesh_provisioning_state_count" in implemented_sensor_keys(runtime)
    assert "mesh_sig_mesh_uuid_hint_count" in implemented_sensor_keys(runtime)
    assert "mesh_control_blocker_count" in implemented_sensor_keys(runtime)


def test_runtime_diagnostics_exposes_scene_profiles() -> None:
    """Diagnostics expose APK scene UI package facts for BLE and mesh models."""
    runtime = build_runtime({CONF_MODEL: "SP660E", CONF_DEVICE_ID: "scene"})

    diagnostics = runtime_diagnostics(runtime)

    assert diagnostics["model"]["family"] == "banlanx_scene_ui"
    assert diagnostics["model"]["scene_profile"] == {
        "family": "banlanx_scene_ui",
        "package": "packages/scene_ui",
        "presets": [
            "Christmas",
            "Dynamic bar",
            "Eaves",
            "Esports 181",
            "Living room",
        ],
        "control_surfaces": [
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
        ],
        "route_hints": [
            "/device/scene_ui",
            "/device/scene_ui/settings",
            "/device/scene_ui/settings/color",
            "/device/scene_ui/settings/more",
            "/device/scene_ui/settings/rename",
        ],
        "lfx_route_hints": [
            "/device/lfx/regular",
            "/device/lfx/rhythm",
            "/device/lfx/animation",
            "/device/lfx/gif",
            "/device/lfx/graffiti2",
            "/device/lfx/image",
            "/device/lfx/text",
            "/device/scene/image/get",
        ],
        "timer_route_hints": [
            "/device/universal/timers",
            "/device/universal/timer/config",
        ],
        "mode_icon_count": 80,
        "mode_effects": list(SCENE_MODE_EFFECTS),
        "mode_icon_samples": [
            "ic_mode_bouncing_ball",
            "ic_mode_breath",
            "ic_mode_comet",
            "ic_mode_fire",
            "ic_mode_rainbow",
            "ic_mode_static",
            "ic_mode_white_breathe",
            "ic_mode_white_flowing_water",
        ],
        "app_method_hints": [
            "getFrameInfoHandler",
            "getFrameLenHandler",
            "getPWMFrameInfoHandler",
            "setBrightness",
            "setLfxMode",
            "setLfxSpeed",
            "setLfxPixelCount",
            "setLfxLoopMode",
            "setLfxColor",
            "setLfxColorTemp",
            "setLfxGradient",
            "setLfxDir",
            "setOnOffLfx",
            "setSensitivity",
            "setSoundSource",
            "setSolidColor",
            "setSolidColorTemp",
            "setWhiteLightCoexistWithRGB",
            "setLedPanelLayout",
        ],
        "storage_hints": [
            "scene_ui:scene_light_info",
            "scene_ui:effect_multi_colors",
            "addRecScene",
            "getRecSceneList",
            "removeRecScene",
            "saveDiyLfx",
            "saveFavoriteEffectList",
            "updateFavoriteLfxList",
            "resetLfx",
        ],
        "recent_actions": [
            "addRecScene",
            "getRecSceneList",
            "removeRecScene",
        ],
        "favorite_actions": [
            "saveFavoriteEffectList",
            "updateFavoriteLfxList",
        ],
        "timer_actions": [
            "saveTimingTask",
            "removeTimingTask",
        ],
        "diy_actions": [
            "saveDiyLfx",
            "resetLfx",
        ],
        "white_brightness_anchors": [
            "raw-brightness-",
            "whiteBrightness",
            "white_brightness",
            "setWhiteLightCoexistWithRGB",
        ],
        "raw_string_hints": [
            "recScene",
            "removeTimingTask",
            "saveTimingTask",
            "timing_task",
            "favoriteLightingEffectIds",
            "favoriteLightingEffectLoopEnabled",
            "raw-brightness-",
            "whiteBrightness",
            "white_brightness",
            "SP31XE series requires firmware V1.1",
            "SP32XE series requires firmware V1.1",
            "One-touch Provisioning",
        ],
        "lfx_data_model_hints": [
            "Lfx(",
            "LfxColorProps.",
            "LfxColorSet{fx: ",
            "LfxDirection.",
            "LfxExternParams(",
            "LfxLoopMode.2",
            "DiyLfx(modeId: ",
            "DiyGradientLfx(modeId: ",
            "DiyLfxSegment{pixelCount: ",
            "CreativeLfxModeType.2",
            "TriggerLfxMode.",
            "WLedLfx",
            "wrappedLfx",
        ],
        "lfx_frame_field_hints": [
            "opCode = ",
            "opCode: ",
            "checksum",
            "lfxParams",
            "lfxMode-",
            "lfx_mode_id",
            "lfx_mode_type",
            "lfx_colors",
            "lfx_color_sets",
            "lfx_gradients",
            "gif_lfx_frames",
            "favLfxModeIds: [",
            "diyGradientLfx: ",
            "lfxDurationInLoop: ",
            "lfxLoopMode: ",
            "lfx: ",
        ],
        "native_handler_hints": [
            "API_IC_Param_Get_Handler",
            "API_IC_Scene_Set_Handler",
            "API_IC_OnOff_Set_Handler",
            "API_IC_Inrt_Set_Handler",
            "API_IC_Inrt_Reset_Handler",
            "API_IC_Channel_Set_Handler",
            "API_IC_Bright_Set_Handler",
            "API_IC_Speed_Set_Handler",
            "API_IC_Loop_Set_Handler",
            "API_IC_Sta_Clr_Set_Handler",
            "API_IC_Clr_Set_Handler",
            "API_IC_Clr_Temper_Set_Handler",
            "API_IC_Pixel_Len_Set_Handler",
            "API_IC_Direction_Set_Handler",
            "API_IC_Diy_Clr_Set_Handler",
            "API_IC_OnOff_Anim_Set_Handler",
            "API_IC_WRGB_Coexist_Set_Handler",
            "API_IC_All_Reset_Handler",
            "API_IC_Pause_Set_Handler",
            "API_IC_Clr_Paletter_Set_Handler",
            "API_PWM_Param_Get_Handler",
            "API_PWM_Scene_Set_Handler",
            "API_PWM_OnOff_Set_Handler",
            "API_PWM_Inrt_Set_Handler",
            "API_PWM_Inrt_Reset_Handler",
            "API_PWM_Channel_Set_Handler",
            "API_PWM_Bright_Set_Handler",
            "API_PWM_Speed_Set_Handler",
            "API_PWM_Loop_Set_Handler",
            "API_PWM_Sta_Clr_Set_Handler",
            "API_PWM_Clr_Set_Handler",
            "API_PWM_Clr_Temper_Set_Handler",
            "API_PWM_Diy_Clr_Set_Handler",
            "API_PWM_OnOff_Anim_Set_Handler",
            "API_PWM_WRGB_Coexist_Set_Handler",
            "API_PWM_All_Reset_Handler",
            "_IC_Scene_Loop_Handler",
            "_PWM_Scene_Loop_Handler",
        ],
        "native_paired_api_capabilities": [
            "param_get",
            "scene_set",
            "on_off_set",
            "inrt_set",
            "inrt_reset",
            "channel_set",
            "bright_set",
            "speed_set",
            "loop_set",
            "sta_clr_set",
            "clr_set",
            "clr_temper_set",
            "diy_clr_set",
            "on_off_anim_set",
            "wrgb_coexist_set",
            "all_reset",
        ],
        "native_ic_only_api_capabilities": [
            "pixel_len_set",
            "direction_set",
            "pause_set",
            "clr_paletter_set",
        ],
        "native_loop_handlers": [
            "_IC_Scene_Loop_Handler",
            "_PWM_Scene_Loop_Handler",
        ],
        "native_library_hints": [
            "libscene_lfx.so",
            "DiyEffect",
            "DiyGradEffect",
            "Music_VuMeter",
            "pwmDiyGradient",
            "pwmOnOffAnimation",
            "fillGradientRGB",
            "setPixelColor",
            "hal_App_Opcode_Handler",
            "Coexist_Map",
            "SetCoexistColor",
            "_IC_Favor_Recover_Handler",
            "_IC_Favor_Record_Handler",
            "_IC_Routine_Recover_Handler",
            "_IC_Routine_Record_Handler",
            "_IC_System_Recover_Handler",
            "_IC_LED_Type_Para_Handler",
            "_IC_Para_Default_Handler",
            "_PWM_Favor_Recover_Handler",
            "_PWM_Favor_Record_Handler",
            "_PWM_Routine_Recover_Handler",
            "_PWM_Routine_Record_Handler",
            "_PWM_System_Recover_Handler",
            "_PWM_LED_Type_Para_Handler",
            "_PWM_Para_Default_Handler",
        ],
        "native_frame_hints": [
            "createFrameHandler",
            "getFrameInfoHandler",
            "getFrameLenHandler",
            "getPWMFrameInfoHandler",
            "getCurrFrameIntv",
            "getCurrFrameIntvHandler",
            "getChanNumHandler",
        ],
        "native_opcode_hints": [
            "hal_App_Opcode_Handler",
            "hal_pwmCtrl_Handler_R1",
            "hal_pwmCtrl_Handler_G1",
            "hal_pwmCtrl_Handler_B1",
            "hal_pwmCtrl_Handler_CW1",
            "hal_pwmCtrl_Handler_WW1",
            "hal_WpwmCtrl_Handler_CW1",
            "hal_WpwmCtrl_Handler_WW1",
            "hal_rgbToBus_Handler_01",
        ],
        "native_state_hints": [
            "getStaDat",
            "syncBriChangeHandler",
            "getBitState",
            "setBitlOn",
            "setBitlOff",
        ],
        "native_state_exports": [
            "getStaDat@0x0001119d/256",
            "syncBriChangeHandler@0x0001118d/16",
            "getBitState@0x0000fbe9/16",
            "setBitlOn@0x0000fbb9/24",
            "setBitlOff@0x0000fbd1/24",
        ],
        "native_color_order_hints": [
            "CRGBW",
            "CWRGB",
            "HAVE_RGB",
            "ONLY_PWM",
            "ONLY_PWM_W",
            "ONLY_RGB",
            "RGBCW",
            "RGBWC",
            "WCRGB",
            "WRGBC",
        ],
        "native_pwm_table_hints": [
            "IC_PWM_WDYN_TAB",
            "IC_PWM_WRHY_TAB",
            "IC_PWM_WSTA_TAB",
            "PWM_DIY_TAB",
            "PWM_DYN_TAB",
            "PWM_INRT_TAB",
            "PWM_RHY_TAB",
            "PWM_STA_TAB",
            "PWM_WDYN_TAB",
            "PWM_WRHY_TAB",
            "PWM_WSTA_TAB",
        ],
        "native_music_effect_hints": [
            "Music_Blink",
            "Music_Eject",
            "Music_Firework",
            "Music_Force",
            "Music_Hits",
            "Music_Spectrum",
            "Music_SymbolColors",
            "Music_VuMeter",
            "pwmDiyBreath",
            "pwmDiyGradient",
            "pwmDiyJumpColor",
            "pwmDiyStrobe",
            "pwmDynBreath",
            "pwmDynGradient",
            "pwmDynHeartBeat",
            "pwmDynJumpColor",
            "pwmDynStrobe",
            "pwmRhyBeat",
            "pwmRhyJumpColor",
            "pwmStaMode",
            "pwmOnOffAnimation",
        ],
        "native_pwm_driver_hints": [
            "Anim_Calibrate_PWM_Handle",
            "Anim_Echo_PWM_Handler",
            "Anim_FacTest_PWM_Handler",
            "IC_DriveRGB",
            "PWM_DriveRGB",
            "PWM_DriveW",
            "WpickClrPWM",
            "Wpwm_Ctl_s",
            "WsetPWM",
            "WsetPwmBuf",
            "hal_Wpwm_led_Init",
            "pickClrPWM",
            "pwm_Ctl_s",
            "pwm_buffer",
            "setCCTBri",
            "setPWM",
            "setPwmBuf",
        ],
        "native_animation_exports": [
            "Anim_Calibrate_IC_Handle@0x0000f83d/96",
            "Anim_Calibrate_PWM_Handle@0x00014255/44",
            "Anim_Echo_IC_Handler@0x0000fa6d/332",
            "Anim_Echo_PWM_Handler@0x0001437d/212",
            "Anim_FacTest_IC_Handler@0x0000f89d/464",
            "Anim_FacTest_PWM_Handler@0x00014281/252",
            "API_IC_OnOff_Anim_Set_Handler@0x000152c9/28",
            "API_PWM_OnOff_Anim_Set_Handler@0x00016011/28",
            "pwmOnOffAnimation@0x000133c5/128",
            "WOnOffAnimation@0x0000f2e5/104",
        ],
        "native_drive_exports": [
            "IC_DriveRGB@0x00006904/7",
            "IC_DriveW@0x0000690b/7",
            "LED_DRIVE_TYPE@0x000196e4/4",
            "PWM_DriveRGB@0x00006912/4",
            "PWM_DriveW@0x00006916/7",
        ],
        "native_persistence_handlers": [
            "_IC_Favor_Recover_Handler",
            "_IC_Favor_Record_Handler",
            "_IC_Routine_Recover_Handler",
            "_IC_Routine_Record_Handler",
            "_IC_System_Recover_Handler",
            "_IC_LED_Type_Para_Handler",
            "_IC_Para_Default_Handler",
            "_PWM_Favor_Recover_Handler",
            "_PWM_Favor_Record_Handler",
            "_PWM_Routine_Recover_Handler",
            "_PWM_Routine_Record_Handler",
            "_PWM_System_Recover_Handler",
            "_PWM_LED_Type_Para_Handler",
            "_PWM_Para_Default_Handler",
        ],
        "native_persistence_exports": [
            {
                "capability": export.capability,
                "driver": export.driver,
                "symbol": export.symbol,
                "value": export.value,
                "size": export.size,
            }
            for export in SCENE_NATIVE_PERSISTENCE_EXPORTS
        ],
        "native_persistence_capabilities": [
            "favor_recover",
            "favor_record",
            "routine_recover",
            "routine_record",
            "system_recover",
            "led_type_para",
            "para_default",
        ],
        "native_export_hints": [
            "libscene_lfx.so ELF .dynsym exports 378 named symbols",
            (
                "High-signal export scan found 76 handler/frame/opcode/"
                "LFX-related symbols"
            ),
            (
                "Exported frame helpers include createFrameHandler, "
                "getFrameInfoHandler, getFrameLenHandler, "
                "getPWMFrameInfoHandler, and getCurrFrameIntvHandler"
            ),
            (
                "Exported routing helper hal_App_Opcode_Handler confirms "
                "native opcode dispatch exists inside the scene LFX library"
            ),
            (
                "Detailed dynsym scan places hal_App_Opcode_Handler at "
                "0x000130a9 (128 bytes)"
            ),
            (
                "Largest exported scene handlers include "
                "API_IC_All_Reset_Handler at 0x00014ec9 (864 bytes), "
                "API_PWM_All_Reset_Handler at 0x00015e05 (524 bytes), and "
                "_IC_Para_Default_Handler at 0x000148a5 (488 bytes)"
            ),
            (
                "Scene write anchors include API_IC_Scene_Set_Handler at "
                "0x00014a91 (292 bytes) and API_PWM_Scene_Set_Handler at "
                "0x00015ab9 (200 bytes)"
            ),
            (
                "Exported state helpers include getStaDat, "
                "syncBriChangeHandler, getBitState, setBitlOn, and setBitlOff"
            ),
            (
                "Exported animation/self-test anchors include IC/PWM "
                "calibrate, echo, factory-test, and on/off animation handlers"
            ),
            (
                "Exported drive-type anchors include IC_DriveRGB, IC_DriveW, "
                "LED_DRIVE_TYPE, PWM_DriveRGB, and PWM_DriveW"
            ),
            (
                "Exported persistence anchors include IC/PWM favor, routine, "
                "system-recover, LED-type parameter, and parameter-default handlers"
            ),
            (
                "Exported symbols still do not expose BLE UUID binding, "
                "command envelope bytes, or notification parser offsets"
            ),
        ],
        "native_code_anchors": [
            {
                "name": name,
                "value": value,
                "size": size,
                "sha256": sha256,
                "first16": first16,
                "last16": last16,
            }
            for name, value, size, sha256, first16, last16
            in SCENE_NATIVE_CODE_ANCHORS
        ],
        "setup_requirements": [
            (
                "SP31XE and SP32XE require firmware V1.1+ for one-touch "
                "provisioning"
            ),
        ],
        "catalog_hints": [
            "model_id=121",
            "parent_id=none",
            "connectCaps=1",
            "specFunctions=87",
            "colorCap=4",
            "transports=ble",
            "maxPixelChannels=1800",
            "featureFlags=1",
        ],
        "transport_hints": [
            "Scene UI records with connectCaps=1 map to direct BLE",
            "Scene mesh records with connectCaps=8 map to BLE mesh",
            "Both scene families share home_uri=/device/scene_ui",
        ],
        "protocol_gap_hints": [
            "No old-UniLED scene UI or scene mesh implementation was found",
            "No confirmed scene BLE command opcode table was recovered",
            "No scene notification/status parser has been mapped",
            (
                "No saved-scene, timer, favorite, or DIY LFX packet layout "
                "is known"
            ),
            (
                "No SP31x/SP32x BLE-mesh routing or provisioning frame map "
                "is known"
            ),
        ],
        "command_blockers": [
            "scene_command_envelope_pending",
            "scene_status_parser_pending",
            "scene_lfx_frame_pending",
            "scene_timer_frame_pending",
            "scene_favorite_frame_pending",
            "scene_diy_frame_pending",
            "scene_white_brightness_parser_pending",
        ],
        "command_protocol_known": False,
        "package_asset_count": 204,
        "apk_asset_evidence": [
            "packages/scene_ui/assets/animations/inner_mic.json",
            "packages/scene_ui/assets/animations/mobile_mic.json",
            "packages/scene_ui/assets/animations/light_off.json",
            "packages/scene_ui/assets/images/scenes/christmas/thumb.png",
            "packages/scene_ui/assets/images/scenes/dynamic_bar/dynamic_light.png",
            "packages/scene_ui/assets/images/scenes/eaves/thumb.png",
            "packages/scene_ui/assets/images/scenes/esports_181/thumb.png",
            "packages/scene_ui/assets/images/scenes/living_room/thumb.png",
            "packages/scene_ui/assets/images/img_fav_empty.png",
            "packages/scene_ui/assets/images/img_timer_empty.png",
            "packages/scene_ui/assets/images/img_setting_color.png",
            "packages/scene_ui/assets/icons/ic_white_brightness.png",
            "packages/scene_ui/assets/icons/ic_setting_scene.png",
            "packages/scene_ui/assets/icons/ic_setting_timer.png",
            "packages/scene_ui/assets/icons/ic_setting_pixel_count.png",
            "packages/scene_ui/assets/icons/ic_opr_inner_mic.png",
            "packages/scene_ui/assets/icons/ic_opr_phone_mic.png",
            "packages/scene_ui/assets/icons/ic_opr_music.png",
            "packages/scene_ui/assets/icons/ic_effect_loop.png",
            "packages/scene_ui/assets/icons/ic_effect_play.png",
            "packages/scene_ui/assets/icons/ic_opr_direction_forward.png",
        ],
        "apk_string_evidence": [
            "Scene models use the /device/scene_ui home URI in the APK catalog",
            "Native strings expose scene_ui settings, color, more, and rename routes",
            (
                "Native strings expose LFX creation routes for regular, "
                "rhythm, animation, GIF, graffiti, image, and text modes"
            ),
            (
                "Native strings expose scene LFX methods including "
                "setLfxMode, setLfxSpeed, setLfxPixelCount, and setLedPanelLayout"
            ),
            (
                "Native strings expose recent-scene and favorite-effect methods "
                "including addRecScene, getRecSceneList, and saveFavoriteEffectList"
            ),
            (
                "Native strings expose timing task and white-brightness labels, "
                "but no packet schema"
            ),
            "Native routes expose the shared universal timer list/config pages",
            (
                "Native strings expose SP31XE/SP32XE firmware V1.1+ "
                "one-touch provisioning text"
            ),
            (
                "Native library exports expose libscene_lfx.so IC/PWM "
                "API handler names"
            ),
            (
                "Native library strings expose frame, opcode, and state "
                "helper anchors"
            ),
            (
                "Native library strings expose color-order and LED-type "
                "capability anchors"
            ),
            (
                "Native library strings expose PWM static, dynamic, rhythm, "
                "and DIY tables"
            ),
            (
                "Native library strings expose scene music, rhythm, and LFX "
                "effect routines"
            ),
            (
                "Native library strings expose PWM driver, buffer, and write "
                "helpers"
            ),
            (
                "Native library exports expose animation calibrate, echo, "
                "factory-test, and on/off animation handlers"
            ),
            (
                "Native library exports expose IC/PWM RGB/W drive-type "
                "objects and LED_DRIVE_TYPE"
            ),
            (
                "Native library strings expose favor/routine/system record "
                "and recover handlers"
            ),
            (
                "Native strings expose scene LFX DTO/model anchors including "
                "Lfx, DiyLfx, DiyGradientLfx, TriggerLfxMode, WLedLfx, and "
                "wrappedLfx"
            ),
            (
                "Native strings expose app-side LFX frame field labels "
                "including opCode, checksum, lfxParams, lfxMode, lfx colors, "
                "GIF frames, favorite mode IDs, loop duration, and loop mode"
            ),
            (
                "ELF .dynsym export inspection confirms frame, state, and "
                "opcode-dispatch helpers but no BLE packet envelope"
            ),
            (
                "ELF .dynsym export inspection groups 16 paired IC/PWM API "
                "handlers, 4 IC-only API handlers, 2 loop handlers, and 5 "
                "state helpers"
            ),
            "The asset manifest exposes 80 packages/scene_ui ic_mode_* mode icons",
        ],
    }
    assert runtime.diagnostic_value("scene_profile") == (
        "banlanx_scene_ui; package=packages/scene_ui; "
        "presets=5; surfaces=14; mode_icons=80; mode_effects=80; "
        "lfx_routes=8; timer_routes=2; methods=19; storage=9; "
        "recent_actions=3; "
        "favorite_actions=2; timer_actions=2; diy_actions=2; "
        "white_brightness=4; raw_strings=12; lfx_data=13; "
        "lfx_frame_fields=16; native_handlers=38; "
        "native_paired_api=16; native_ic_only_api=4; "
        "native_loop_handlers=2; native_hints=25; native_frames=7; "
        "native_opcode=9; native_state=5; native_state_exports=5; "
        "native_color_order=10; native_pwm_tables=11; "
        "native_music_effects=21; native_pwm_drivers=17; "
        "native_animation_exports=10; native_drive_exports=5; "
        "native_persistence=14; native_persistence_exports=14; "
        "native_persistence_capabilities=7; native_exports=12; "
        "native_code_anchors=7; "
        "setup=1; catalog=8; transport=3; "
        "gaps=5; blockers=7; package_assets=204; "
        "command_protocol_pending; routes=5"
    )
    assert runtime.diagnostic_value("scene_preset_count") == 5
    assert runtime.diagnostic_value("scene_control_surface_count") == 14
    assert runtime.diagnostic_value("scene_route_count") == 5
    assert runtime.diagnostic_value("scene_mode_icon_count") == 80
    assert runtime.diagnostic_value("scene_mode_effect_count") == 80
    assert runtime.diagnostic_value("scene_mode_icon_sample_count") == 8
    assert runtime.diagnostic_value("scene_lfx_route_count") == 8
    assert runtime.diagnostic_value("scene_timer_route_count") == 2
    assert runtime.diagnostic_value("scene_app_method_count") == 19
    assert runtime.diagnostic_value("scene_storage_hint_count") == 9
    assert runtime.diagnostic_value("scene_recent_action_count") == 3
    assert runtime.diagnostic_value("scene_favorite_action_count") == 2
    assert runtime.diagnostic_value("scene_timer_action_count") == 2
    assert runtime.diagnostic_value("scene_diy_action_count") == 2
    assert runtime.diagnostic_value("scene_white_brightness_anchor_count") == 4
    assert runtime.diagnostic_value("scene_raw_string_hint_count") == 12
    assert runtime.diagnostic_value("scene_lfx_data_model_hint_count") == 13
    assert runtime.diagnostic_value("scene_lfx_frame_field_hint_count") == 16
    assert runtime.diagnostic_value("scene_native_handler_count") == 38
    assert runtime.diagnostic_value("scene_native_paired_api_count") == 16
    assert runtime.diagnostic_value("scene_native_ic_only_api_count") == 4
    assert runtime.diagnostic_value("scene_native_loop_handler_count") == 2
    assert runtime.diagnostic_value("scene_native_library_hint_count") == 25
    assert runtime.diagnostic_value("scene_native_frame_hint_count") == 7
    assert runtime.diagnostic_value("scene_native_opcode_hint_count") == 9
    assert runtime.diagnostic_value("scene_native_state_hint_count") == 5
    assert runtime.diagnostic_value("scene_native_state_export_count") == 5
    assert runtime.diagnostic_value("scene_native_color_order_hint_count") == 10
    assert runtime.diagnostic_value("scene_native_pwm_table_hint_count") == 11
    assert runtime.diagnostic_value("scene_native_music_effect_hint_count") == 21
    assert runtime.diagnostic_value("scene_native_pwm_driver_hint_count") == 17
    assert runtime.diagnostic_value("scene_native_animation_export_count") == 10
    assert runtime.diagnostic_value("scene_native_drive_export_count") == 5
    assert runtime.diagnostic_value("scene_native_persistence_handler_count") == 14
    assert runtime.diagnostic_value("scene_native_persistence_export_count") == 14
    assert runtime.diagnostic_value("scene_native_persistence_capability_count") == 7
    assert runtime.diagnostic_value("scene_native_export_hint_count") == 12
    assert runtime.diagnostic_value("scene_native_code_anchor_count") == 7
    assert runtime.diagnostic_value("scene_setup_requirement_count") == 1
    assert runtime.diagnostic_value("scene_catalog_hint_count") == 8
    assert runtime.diagnostic_value("scene_transport_hint_count") == 3
    assert runtime.diagnostic_value("scene_protocol_gap_count") == 5
    assert runtime.diagnostic_value("scene_command_blocker_count") == 7
    assert runtime.diagnostic_value("scene_apk_asset_evidence_count") == 21
    assert runtime.diagnostic_value("scene_apk_package_asset_count") == 204
    assert runtime.diagnostic_value("scene_apk_string_evidence_count") == 22
    assert "scene_profile" in implemented_sensor_keys(runtime)
    assert "scene_preset_count" in implemented_sensor_keys(runtime)
    assert "scene_control_surface_count" in implemented_sensor_keys(runtime)
    assert "scene_route_count" in implemented_sensor_keys(runtime)
    assert "scene_mode_icon_count" in implemented_sensor_keys(runtime)
    assert "scene_mode_effect_count" in implemented_sensor_keys(runtime)
    assert "scene_mode_icon_sample_count" in implemented_sensor_keys(runtime)
    assert "scene_lfx_route_count" in implemented_sensor_keys(runtime)
    assert "scene_timer_route_count" in implemented_sensor_keys(runtime)
    assert "scene_app_method_count" in implemented_sensor_keys(runtime)
    assert "scene_storage_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_recent_action_count" in implemented_sensor_keys(runtime)
    assert "scene_favorite_action_count" in implemented_sensor_keys(runtime)
    assert "scene_timer_action_count" in implemented_sensor_keys(runtime)
    assert "scene_diy_action_count" in implemented_sensor_keys(runtime)
    assert "scene_white_brightness_anchor_count" in implemented_sensor_keys(runtime)
    assert "scene_raw_string_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_lfx_data_model_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_lfx_frame_field_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_native_handler_count" in implemented_sensor_keys(runtime)
    assert "scene_native_paired_api_count" in implemented_sensor_keys(runtime)
    assert "scene_native_ic_only_api_count" in implemented_sensor_keys(runtime)
    assert "scene_native_loop_handler_count" in implemented_sensor_keys(runtime)
    assert "scene_native_library_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_native_frame_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_native_opcode_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_native_state_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_native_state_export_count" in implemented_sensor_keys(runtime)
    assert "scene_native_color_order_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_native_pwm_table_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_native_music_effect_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_native_pwm_driver_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_native_animation_export_count" in implemented_sensor_keys(runtime)
    assert "scene_native_drive_export_count" in implemented_sensor_keys(runtime)
    assert "scene_native_persistence_handler_count" in implemented_sensor_keys(
        runtime
    )
    assert "scene_native_persistence_export_count" in implemented_sensor_keys(
        runtime
    )
    assert "scene_native_persistence_capability_count" in implemented_sensor_keys(
        runtime
    )
    assert "scene_native_export_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_native_code_anchor_count" in implemented_sensor_keys(runtime)
    assert "scene_setup_requirement_count" in implemented_sensor_keys(runtime)
    assert "scene_catalog_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_transport_hint_count" in implemented_sensor_keys(runtime)
    assert "scene_protocol_gap_count" in implemented_sensor_keys(runtime)
    assert "scene_command_blocker_count" in implemented_sensor_keys(runtime)
    assert "scene_apk_asset_evidence_count" in implemented_sensor_keys(runtime)
    assert "scene_apk_package_asset_count" in implemented_sensor_keys(runtime)
    assert "scene_apk_string_evidence_count" in implemented_sensor_keys(runtime)

    mesh_runtime = build_runtime({CONF_MODEL: "SP310E", CONF_DEVICE_ID: "mesh"})

    assert mesh_runtime.diagnostic_value("scene_profile").startswith(
        "banlanx_scene_mesh; package=packages/scene_ui; "
    )
    assert mesh_runtime.diagnostic_value("scene_control_surface_count") == 14
    assert mesh_runtime.diagnostic_value("scene_route_count") == 5
    assert mesh_runtime.diagnostic_value("scene_mode_icon_count") == 80
    assert mesh_runtime.diagnostic_value("scene_mode_effect_count") == 80
    assert mesh_runtime.diagnostic_value("scene_recent_action_count") == 3
    assert mesh_runtime.diagnostic_value("scene_timer_route_count") == 2
    assert mesh_runtime.diagnostic_value("scene_favorite_action_count") == 2
    assert mesh_runtime.diagnostic_value("scene_timer_action_count") == 2
    assert mesh_runtime.diagnostic_value("scene_lfx_data_model_hint_count") == 13
    assert mesh_runtime.diagnostic_value("scene_lfx_frame_field_hint_count") == 16
    assert mesh_runtime.diagnostic_value("scene_native_handler_count") == 38
    assert mesh_runtime.diagnostic_value("scene_native_paired_api_count") == 16
    assert mesh_runtime.diagnostic_value("scene_native_ic_only_api_count") == 4
    assert mesh_runtime.diagnostic_value("scene_native_loop_handler_count") == 2
    assert mesh_runtime.diagnostic_value("scene_native_frame_hint_count") == 7
    assert mesh_runtime.diagnostic_value("scene_native_opcode_hint_count") == 9
    assert mesh_runtime.diagnostic_value("scene_native_state_hint_count") == 5
    assert mesh_runtime.diagnostic_value("scene_native_state_export_count") == 5
    assert mesh_runtime.diagnostic_value("scene_native_color_order_hint_count") == 10
    assert mesh_runtime.diagnostic_value("scene_native_pwm_table_hint_count") == 11
    assert mesh_runtime.diagnostic_value("scene_native_music_effect_hint_count") == 21
    assert mesh_runtime.diagnostic_value("scene_native_pwm_driver_hint_count") == 17
    assert mesh_runtime.diagnostic_value("scene_native_animation_export_count") == 10
    assert mesh_runtime.diagnostic_value("scene_native_drive_export_count") == 5
    assert (
        mesh_runtime.diagnostic_value("scene_native_persistence_handler_count")
        == 14
    )
    assert (
        mesh_runtime.diagnostic_value("scene_native_persistence_export_count")
        == 14
    )
    assert (
        mesh_runtime.diagnostic_value("scene_native_persistence_capability_count")
        == 7
    )
    assert mesh_runtime.diagnostic_value("scene_native_code_anchor_count") == 7
    assert mesh_runtime.diagnostic_value("scene_setup_requirement_count") == 1
    assert mesh_runtime.diagnostic_value("scene_catalog_hint_count") == 8
    assert mesh_runtime.diagnostic_value("scene_protocol_gap_count") == 5
    assert mesh_runtime.diagnostic_value("scene_command_blocker_count") == 7
    assert mesh_runtime.diagnostic_value("scene_apk_asset_evidence_count") == 21
    assert mesh_runtime.diagnostic_value("scene_apk_package_asset_count") == 204
    assert mesh_runtime.diagnostic_value("scene_apk_string_evidence_count") == 22
    assert mesh_runtime.diagnostic_value("mesh_profile") == (
        "banlanx_scene_mesh; banlanx_scene_mesh; core_protocol_pending; "
        "sig_mesh_uuids=6; gaps=3; blockers=4; routes=1; provisioning=3; "
        "package_assets=204; apk_strings=4"
    )
    assert mesh_runtime.diagnostic_value("mesh_route_count") == 1
    assert mesh_runtime.diagnostic_value("mesh_provisioning_hint_count") == 3
    assert mesh_runtime.diagnostic_value("mesh_provisioning_state_count") is None
    assert mesh_runtime.diagnostic_value("mesh_sig_mesh_uuid_hint_count") == 6
    assert mesh_runtime.diagnostic_value("mesh_control_blocker_count") == 4
    assert mesh_runtime.diagnostic_value("mesh_apk_package_asset_count") == 204
    assert mesh_runtime.diagnostic_value("mesh_apk_string_evidence_count") == 4
    mesh_transport_profile = runtime_diagnostics(mesh_runtime)["model"][
        "mesh_profile"
    ]
    assert mesh_transport_profile["sig_mesh_uuid_hints"] == list(
        SIG_MESH_UUID_HINTS
    )
    assert mesh_transport_profile["control_blockers"] == [
        "scene_mesh_provisioning_frame_pending",
        "scene_mesh_group_management_pending",
        "scene_mesh_node_lifecycle_pending",
        "scene_mesh_routing_frame_pending",
    ]
    mesh_profile = runtime_diagnostics(mesh_runtime)["model"]["scene_profile"]
    assert mesh_profile["package_asset_count"] == 204
    assert mesh_profile["command_blockers"] == [
        "scene_command_envelope_pending",
        "scene_status_parser_pending",
        "scene_lfx_frame_pending",
        "scene_timer_frame_pending",
        "scene_favorite_frame_pending",
        "scene_diy_frame_pending",
        "scene_white_brightness_parser_pending",
    ]
    assert mesh_profile["catalog_hints"] == [
        "model_id=176",
        "parent_id=none",
        "connectCaps=8",
        "specFunctions=71",
        "colorCap=8",
        "transports=ble_mesh",
        "maxPixelChannels=2700",
        "featureFlags=0",
    ]

    non_scene = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})
    assert non_scene.diagnostic_value("scene_native_handler_count") is None
    assert non_scene.diagnostic_value("scene_native_paired_api_count") is None
    assert non_scene.diagnostic_value("scene_native_ic_only_api_count") is None
    assert non_scene.diagnostic_value("scene_native_loop_handler_count") is None
    assert non_scene.diagnostic_value("scene_native_frame_hint_count") is None
    assert non_scene.diagnostic_value("scene_native_opcode_hint_count") is None
    assert non_scene.diagnostic_value("scene_native_state_hint_count") is None
    assert non_scene.diagnostic_value("scene_native_state_export_count") is None
    assert non_scene.diagnostic_value("scene_native_color_order_hint_count") is None
    assert non_scene.diagnostic_value("scene_native_pwm_table_hint_count") is None
    assert non_scene.diagnostic_value("scene_native_music_effect_hint_count") is None
    assert non_scene.diagnostic_value("scene_native_pwm_driver_hint_count") is None
    assert non_scene.diagnostic_value("scene_native_animation_export_count") is None
    assert non_scene.diagnostic_value("scene_native_drive_export_count") is None
    assert non_scene.diagnostic_value("scene_native_persistence_export_count") is None
    assert (
        non_scene.diagnostic_value("scene_native_persistence_capability_count")
        is None
    )
    assert non_scene.diagnostic_value("scene_native_code_anchor_count") is None
    assert non_scene.diagnostic_value("scene_recent_action_count") is None
    assert non_scene.diagnostic_value("scene_lfx_data_model_hint_count") is None
    assert non_scene.diagnostic_value("scene_lfx_frame_field_hint_count") is None
    assert non_scene.diagnostic_value("scene_command_blocker_count") is None
    assert "scene_native_handler_count" not in implemented_sensor_keys(non_scene)
    assert "scene_native_paired_api_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_ic_only_api_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_loop_handler_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_frame_hint_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_lfx_data_model_hint_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_lfx_frame_field_hint_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_state_export_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_color_order_hint_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_pwm_table_hint_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_music_effect_hint_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_pwm_driver_hint_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_animation_export_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_drive_export_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_persistence_export_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_persistence_capability_count" not in implemented_sensor_keys(
        non_scene
    )
    assert "scene_native_code_anchor_count" not in implemented_sensor_keys(non_scene)
    assert "scene_recent_action_count" not in implemented_sensor_keys(non_scene)
    assert "scene_command_blocker_count" not in implemented_sensor_keys(non_scene)


def test_runtime_diagnostics_exposes_car_light_profile() -> None:
    """Diagnostics expose APK car-light zones, triggers, and accessory roles."""
    runtime = build_runtime({CONF_MODEL: "SP701E", CONF_DEVICE_ID: "car"})

    diagnostics = runtime_diagnostics(runtime)

    assert diagnostics["model"]["family"] == "banlanx_car_lights"
    assert diagnostics["model"]["car_light_accessory_role"] == (
        "interior_controller"
    )
    assert diagnostics["model"]["car_light_model_role"] == {
        "role": "interior_controller",
        "setup_stage": "interior_before_chassis",
        "setup_order": 1,
        "required_controller_model": None,
        "parent_group_model_id": 65537,
    }
    assert diagnostics["model"]["car_light_profile"] == {
        "family": "banlanx_car_lights",
        "package": "packages/car_lights",
        "zones": [
            "Car lights",
            "Chassis lights",
            "Console lights",
            "Door lights",
            "Footsocket lights",
            "Storage lights",
            "Welcome lights",
            "Wheel lights",
        ],
        "triggers": [
            "Brake light",
            "Brake light blink",
            "Brake light blink new",
            "Fade car light",
            "Flow car light",
            "Left turn signal flow",
            "Right turn signal flow",
            "Turn signal blink",
            "Turn signal blink new",
        ],
        "control_surfaces": [
            "Setup",
            "Zone selection",
            "Trigger settings",
            "Color correction",
            "Subdevices management",
            "Device password",
            "Password reset",
            "Settings",
        ],
        "accessory_assets": [
            "ic_subdevice_manager_outlined",
            "ic_master_slave_sycned",
            "ic_pwd_edit_outlined",
            "reset_device_pwd",
        ],
        "animation_assets": [
            "packages/car_lights/assets/animations/brake_light.zip",
            "packages/car_lights/assets/animations/brake_light_blink.zip",
            "packages/car_lights/assets/animations/brake_light_blink_new.zip",
            "packages/car_lights/assets/animations/fade_car_light.zip",
            "packages/car_lights/assets/animations/flow_car_light.zip",
            "packages/car_lights/assets/animations/left_turn_signal_light_flow.zip",
            "packages/car_lights/assets/animations/reset_device_pwd.zip",
            "packages/car_lights/assets/animations/right_turn_signal_light_flow.zip",
            "packages/car_lights/assets/animations/turn_signal_light_blink.zip",
            "packages/car_lights/assets/animations/turn_signal_light_blink_new.zip",
        ],
        "trigger_image_assets": [
            "packages/car_lights/assets/images/astern.png",
            "packages/car_lights/assets/images/brake.png",
            "packages/car_lights/assets/images/left_turn_signal.png",
            "packages/car_lights/assets/images/right_turn_signal.png",
        ],
        "zone_image_assets": [
            "packages/car_lights/assets/images/car_areas.png",
            "packages/car_lights/assets/images/car_argb.png",
            "packages/car_lights/assets/images/car_chassic.png",
            "packages/car_lights/assets/images/car_console.png",
            "packages/car_lights/assets/images/car_door.png",
            "packages/car_lights/assets/images/car_footsocket.png",
            "packages/car_lights/assets/images/car_lights_banner.png",
            "packages/car_lights/assets/images/car_rgb.png",
            "packages/car_lights/assets/images/car_storage.png",
            "packages/car_lights/assets/images/car_wheel.png",
            "packages/car_lights/assets/images/chassis_lights.png",
            "packages/car_lights/assets/images/new_car.png",
            "packages/car_lights/assets/images/whole_car.png",
        ],
        "subdevice_hints": [
            "subdevice",
            "subdeviceAddr = ",
            "include_added_subdevices",
            "exclude_slave_devices",
            (
                "Removing the master device will reset all sub-devices. "
                "Please proceed with caution!"
            ),
            (
                "The subdevice configuration is not yet complete. Are you "
                "sure you want to exit?"
            ),
            "Unable to add the subdevice",
            (
                "Secondary devices will chain-react to turn off lights when "
                "Primary loses power."
            ),
        ],
        "subdevice_filters": [
            "include_added_subdevices",
            "exclude_slave_devices",
        ],
        "password_hints": [
            "Device password",
            "Set your password",
            "Setup password successfully",
            "Turn on password",
            "Turn off password",
            "Wait for the device password reset...",
            "The password reset timed out. Please try again!",
            '_xxx"(the password is 12345678), and return to "BanlanX".',
        ],
        "password_flow_states": [
            "Set your password",
            "Setup password successfully",
            "Turn on password",
            "Turn off password",
            "Wait for the device password reset...",
            "The password reset timed out. Please try again!",
        ],
        "password_entry_hints": [
            "Enter your password",
            "Enter new password",
            "Enter new password again",
            "New password2",
            "Repeat password",
            "Show password",
            "Forget password?",
            "Forgot password?",
        ],
        "password_policy_hints": [
            "Change password",
            "Change password successfully2",
            "Inconsistent new password input!",
            (
                "When you turn off your password, you won't be able to "
                "prevent other users from connecting and controlling your "
                "device."
            ),
            (
                "The password can consist of numbers, letters or symbols "
                "(_ - ! @ # $ & * ~). "
            ),
            (
                "Enter your new password. The password can consist of "
                "numbers, letters or symbols (_ - ! @ # $ & * ~)."
            ),
        ],
        "password_reset_hints": [
            (
                "Press and hold the power button for 3 seconds until the "
                "indicator switches from blinking to steady on to reset the "
                "password."
            ),
            "When enabled: 5 power cycles reset the device.",
            "Remove and reset device.",
            "Reset password successfully",
        ],
        "trigger_storage_hints": [
            (
                "CREATE TABLE sp_trigger (id INTEGER PRIMARY KEY, "
                "device_id INTEGER, trigger_index INTEGER, name TEXT)"
            ),
            "sp_trigger",
            "trigger_id",
            "trigger_index",
            "triggers",
            (
                "Set the lighting effect when the corresponding trigger "
                "signal is received"
            ),
            "Rename trigger",
        ],
        "trigger_actions": [
            (
                "Set the lighting effect when the corresponding trigger "
                "signal is received"
            ),
            "Rename trigger",
        ],
        "route_hints": [
            "/car_lights",
            "/car_lights/new",
            "/car_lights/setup",
            "/car_lights/settings/chassic_lights_trigger",
            "/car_lights/settings/color_correction",
            "/car_lights/settings/subdevices_management",
            "/car_lights/settings2",
        ],
        "setup_requirements": [
            (
                'The "Wireless MIC" can only be used as an accessory to the '
                '"Chassis Lamp Controller (SP702E)". '
            ),
            'Please add a "Chassis Lamp Controller (SP702E)" first.',
            (
                "It is not supported to add the interiorl lights when only "
                "the chassis light is available. After removing the chassis "
                "light, add the interiorl light (SP701E) and then add the "
                "chassis light (SP702E)."
            ),
            (
                'requires "Microphone" permission to trigger the LED '
                "controller's lighting effects in real-time by capturing "
                "surrounding sounds."
            ),
            (
                "Secondary devices will chain-react to turn off lights when "
                "Primary loses power."
            ),
        ],
        "setup_flow_hints": [
            'To retain the current device as primary controller, select "Ignore"',
            (
                "If you are unsure about the installation area of the LED "
                "controller, observe which area in the car has LED strips "
                "displaying a fast-flashing white light effect. Please select "
                "the corresponding area in the diagram below."
            ),
        ],
        "setup_key_hints": [
            "isPrimary",
            "subUni",
            " channel is ",
            '" as the primary controller.',
            (
                'Click the "Exit" button below to return to the device '
                'discovery page and connect the device installed in "'
            ),
        ],
        "model_role": {
            "role": "interior_controller",
            "setup_stage": "interior_before_chassis",
            "setup_order": 1,
            "required_controller_model": None,
            "parent_group_model_id": 65537,
        },
        "model_role_hints": [
            "Car Lights model_id=65537 family group",
            "SP701E parent_id=65537 interior_controller",
            "SP702E parent_id=65537 chassis_controller",
            "SP-MIC parent_id=65537 wireless_microphone_accessory",
            "SP-MIC required_controller=SP702E",
            "SP701E setup_order=1 before SP702E",
            "SP702E setup_order=2 after SP701E when both are present",
            "Native setup flow exposes isPrimary and subUni keys",
        ],
        "model_setup_dependency": {
            "model_name": "SP701E",
            "relationship": "precedes_chassis_when_both_present",
            "related_model": "SP702E",
            "setup_order": 1,
            "required": False,
            "enforcement_status": "diagnostic_only",
            "evidence": "SP701E setup_order=1 before SP702E",
        },
        "setup_dependencies": [
            {
                "model_name": "Car Lights",
                "relationship": "parent_group",
                "related_model": None,
                "setup_order": None,
                "required": False,
                "enforcement_status": "catalog_group_only",
                "evidence": "Car Lights model_id=65537 family group",
            },
            {
                "model_name": "SP701E",
                "relationship": "precedes_chassis_when_both_present",
                "related_model": "SP702E",
                "setup_order": 1,
                "required": False,
                "enforcement_status": "diagnostic_only",
                "evidence": "SP701E setup_order=1 before SP702E",
            },
            {
                "model_name": "SP702E",
                "relationship": "follows_interior_when_both_present",
                "related_model": "SP701E",
                "setup_order": 2,
                "required": False,
                "enforcement_status": "diagnostic_only",
                "evidence": "SP702E setup_order=2 after SP701E when both are present",
            },
            {
                "model_name": "SP-MIC",
                "relationship": "requires_chassis_controller",
                "related_model": "SP702E",
                "setup_order": None,
                "required": True,
                "enforcement_status": "diagnostic_only",
                "evidence": "SP-MIC required_controller=SP702E",
            },
        ],
        "required_setup_dependencies": [
            {
                "model_name": "SP-MIC",
                "relationship": "requires_chassis_controller",
                "related_model": "SP702E",
                "setup_order": None,
                "required": True,
                "enforcement_status": "diagnostic_only",
                "evidence": "SP-MIC required_controller=SP702E",
            },
        ],
        "ordered_setup_dependencies": [
            {
                "model_name": "SP701E",
                "relationship": "precedes_chassis_when_both_present",
                "related_model": "SP702E",
                "setup_order": 1,
                "required": False,
                "enforcement_status": "diagnostic_only",
                "evidence": "SP701E setup_order=1 before SP702E",
            },
            {
                "model_name": "SP702E",
                "relationship": "follows_interior_when_both_present",
                "related_model": "SP701E",
                "setup_order": 2,
                "required": False,
                "enforcement_status": "diagnostic_only",
                "evidence": "SP702E setup_order=2 after SP701E when both are present",
            },
        ],
        "catalog_hints": [
            "model_id=257",
            "parent_id=65537",
            "connectCaps=1",
            "specFunctions=2",
            "colorCap=4",
            "transports=ble",
        ],
        "transport_hints": [
            "connectCaps=1 maps to BLE-only for all car-light catalog records",
            "All car-light records share home_uri=/car_lights",
            "SP701E and SP702E are child models of the Car Lights parent group",
            (
                "SP-MIC is a BLE accessory child model without color/spec "
                "function flags"
            ),
        ],
        "protocol_gap_hints": [
            "No old-UniLED car-light implementation was found",
            "No confirmed car-light BLE command opcode table was recovered",
            "No car-light notification/status parser has been mapped",
            (
                "No subdevice binding, password flow, or SP-MIC event "
                "packet flow is known"
            ),
        ],
        "command_blockers": [
            "car_light_ble_opcode_pending",
            "car_light_status_parser_pending",
            "car_light_zone_command_pending",
            "car_light_trigger_packet_pending",
            "car_light_subdevice_binding_pending",
            "car_light_password_flow_pending",
        ],
        "command_protocol_known": False,
        "package_asset_count": 58,
        "apk_asset_evidence": [
            "packages/car_lights/assets/animations/brake_light.zip",
            "packages/car_lights/assets/animations/brake_light_blink.zip",
            "packages/car_lights/assets/animations/brake_light_blink_new.zip",
            "packages/car_lights/assets/animations/fade_car_light.zip",
            "packages/car_lights/assets/animations/flow_car_light.zip",
            "packages/car_lights/assets/animations/left_turn_signal_light_flow.zip",
            "packages/car_lights/assets/animations/reset_device_pwd.zip",
            "packages/car_lights/assets/animations/right_turn_signal_light_flow.zip",
            "packages/car_lights/assets/animations/turn_signal_light_blink.zip",
            "packages/car_lights/assets/animations/turn_signal_light_blink_new.zip",
            "packages/car_lights/assets/icons/ic_car_lights.png",
            "packages/car_lights/assets/icons/ic_car_lights_outlined.png",
            "packages/car_lights/assets/icons/ic_car_trigger_outlined.png",
            "packages/car_lights/assets/icons/ic_chassis_lights.png",
            "packages/car_lights/assets/icons/ic_chassis_lights_outlined.png",
            "packages/car_lights/assets/icons/ic_color_correction_outlined.png",
            "packages/car_lights/assets/icons/ic_console_lights.png",
            "packages/car_lights/assets/icons/ic_console_lights_outlined.png",
            "packages/car_lights/assets/icons/ic_door_lights.png",
            "packages/car_lights/assets/icons/ic_door_lights_outlined.png",
            "packages/car_lights/assets/icons/ic_footsocket_lights.png",
            "packages/car_lights/assets/icons/ic_footsocket_lights_outlined.png",
            "packages/car_lights/assets/icons/ic_master_slave_sycned.png",
            "packages/car_lights/assets/icons/ic_pwd_edit_outlined.png",
            "packages/car_lights/assets/icons/ic_storage_lights.png",
            "packages/car_lights/assets/icons/ic_storage_lights_outlined.png",
            "packages/car_lights/assets/icons/ic_subdevice_manager_outlined.png",
            "packages/car_lights/assets/icons/ic_welcome_lights.png",
            "packages/car_lights/assets/icons/ic_wheel_lights.png",
            "packages/car_lights/assets/icons/ic_wheel_lights_outlined.png",
            "packages/car_lights/assets/images/astern.png",
            "packages/car_lights/assets/images/brake.png",
            "packages/car_lights/assets/images/left_turn_signal.png",
            "packages/car_lights/assets/images/right_turn_signal.png",
            "packages/car_lights/assets/images/car_areas.png",
            "packages/car_lights/assets/images/car_argb.png",
            "packages/car_lights/assets/images/car_chassic.png",
            "packages/car_lights/assets/images/car_console.png",
            "packages/car_lights/assets/images/car_door.png",
            "packages/car_lights/assets/images/car_footsocket.png",
            "packages/car_lights/assets/images/car_lights_banner.png",
            "packages/car_lights/assets/images/car_rgb.png",
            "packages/car_lights/assets/images/car_storage.png",
            "packages/car_lights/assets/images/car_wheel.png",
            "packages/car_lights/assets/images/chassis_lights.png",
            "packages/car_lights/assets/images/new_car.png",
            "packages/car_lights/assets/images/whole_car.png",
        ],
        "apk_string_evidence": [
            "SP701E appears in native strings as the interior-light controller",
            "SP702E appears in native strings as the chassis-light controller",
            "SP-MIC appears in native strings as a wireless microphone accessory",
            "Wireless MIC setup requires a Chassis Lamp Controller (SP702E)",
            (
                "Interior lights must be added before chassis lights when "
                "both are present"
            ),
            (
                "Native strings expose sp_trigger storage, trigger_id, "
                "and trigger_index"
            ),
            (
                "Native strings expose subdeviceAddr plus include/exclude "
                "slave-device filters"
            ),
            "Native strings expose device password setup/reset states",
            "Native strings expose password entry, change, and policy labels",
            (
                "Native strings expose button-hold and power-cycle password "
                "reset guidance"
            ),
            "Native strings expose primary-controller retain/Ignore setup flow",
            (
                "Native strings expose fast-flashing white install-area "
                "identification flow"
            ),
            "Native strings expose secondary-device power-loss behavior",
        ],
    }
    assert runtime.diagnostic_value("car_light_profile") == (
        "banlanx_car_lights; package=packages/car_lights; "
        "zones=8; triggers=9; surfaces=8; animations=10; "
        "trigger_images=4; zone_images=13; subdevices=8; "
        "subdevice_filters=2; passwords=8; password_flows=6; "
        "password_entries=8; password_policies=6; password_resets=4; "
        "trigger_storage=7; trigger_actions=2; requirements=5; "
        "required_controller=none; setup_stage=interior_before_chassis; "
        "setup_flows=2; setup_keys=5; role_hints=8; setup_dependencies=4; "
        "required_dependencies=1; ordered_models=2; "
        "model_dependency=precedes_chassis_when_both_present; "
        "catalog=6; gaps=4; "
        "blockers=6; package_assets=58; command_protocol_pending; routes=7"
    )
    assert runtime.diagnostic_value("accessory_role") == "interior_controller"
    assert runtime.diagnostic_value("car_light_required_controller") == "none"
    assert runtime.diagnostic_value("car_light_setup_stage") == (
        "interior_before_chassis"
    )
    assert runtime.diagnostic_value("car_light_setup_order") == 1
    assert runtime.diagnostic_value("car_light_setup_dependency") == (
        "precedes_chassis_when_both_present"
    )
    assert runtime.diagnostic_value("car_light_setup_dependency_count") == 4
    assert runtime.diagnostic_value("car_light_required_setup_dependency_count") == 1
    assert runtime.diagnostic_value("car_light_ordered_setup_model_count") == 2
    assert runtime.diagnostic_value("car_light_zone_count") == 8
    assert runtime.diagnostic_value("car_light_trigger_count") == 9
    assert runtime.diagnostic_value("car_light_control_surface_count") == 8
    assert runtime.diagnostic_value("car_light_accessory_asset_count") == 4
    assert runtime.diagnostic_value("car_light_animation_asset_count") == 10
    assert runtime.diagnostic_value("car_light_trigger_image_asset_count") == 4
    assert runtime.diagnostic_value("car_light_zone_image_asset_count") == 13
    assert runtime.diagnostic_value("car_light_subdevice_hint_count") == 8
    assert runtime.diagnostic_value("car_light_subdevice_filter_count") == 2
    assert runtime.diagnostic_value("car_light_password_hint_count") == 8
    assert runtime.diagnostic_value("car_light_password_flow_state_count") == 6
    assert runtime.diagnostic_value("car_light_password_entry_hint_count") == 8
    assert runtime.diagnostic_value("car_light_password_policy_hint_count") == 6
    assert runtime.diagnostic_value("car_light_password_reset_hint_count") == 4
    assert runtime.diagnostic_value("car_light_trigger_storage_hint_count") == 7
    assert runtime.diagnostic_value("car_light_trigger_action_count") == 2
    assert runtime.diagnostic_value("car_light_route_count") == 7
    assert runtime.diagnostic_value("car_light_setup_requirement_count") == 5
    assert runtime.diagnostic_value("car_light_setup_flow_hint_count") == 2
    assert runtime.diagnostic_value("car_light_setup_key_hint_count") == 5
    assert runtime.diagnostic_value("car_light_model_role_hint_count") == 8
    assert runtime.diagnostic_value("car_light_protocol_gap_count") == 4
    assert runtime.diagnostic_value("car_light_command_blocker_count") == 6
    assert runtime.diagnostic_value("car_light_apk_asset_evidence_count") == 47
    assert runtime.diagnostic_value("car_light_apk_package_asset_count") == 58
    assert runtime.diagnostic_value("car_light_apk_string_evidence_count") == 13
    assert "car_light_profile" in implemented_sensor_keys(runtime)
    assert "accessory_role" in implemented_sensor_keys(runtime)
    assert "car_light_required_controller" in implemented_sensor_keys(runtime)
    assert "car_light_setup_stage" in implemented_sensor_keys(runtime)
    assert "car_light_setup_order" in implemented_sensor_keys(runtime)
    assert "car_light_setup_dependency" in implemented_sensor_keys(runtime)
    assert "car_light_setup_dependency_count" in implemented_sensor_keys(runtime)
    assert "car_light_required_setup_dependency_count" in implemented_sensor_keys(
        runtime
    )
    assert "car_light_ordered_setup_model_count" in implemented_sensor_keys(runtime)
    assert "car_light_zone_count" in implemented_sensor_keys(runtime)
    assert "car_light_trigger_count" in implemented_sensor_keys(runtime)
    assert "car_light_control_surface_count" in implemented_sensor_keys(runtime)
    assert "car_light_accessory_asset_count" in implemented_sensor_keys(runtime)
    assert "car_light_animation_asset_count" in implemented_sensor_keys(runtime)
    assert "car_light_trigger_image_asset_count" in implemented_sensor_keys(
        runtime
    )
    assert "car_light_zone_image_asset_count" in implemented_sensor_keys(runtime)
    assert "car_light_subdevice_hint_count" in implemented_sensor_keys(runtime)
    assert "car_light_subdevice_filter_count" in implemented_sensor_keys(runtime)
    assert "car_light_password_hint_count" in implemented_sensor_keys(runtime)
    assert "car_light_password_flow_state_count" in implemented_sensor_keys(runtime)
    assert "car_light_password_entry_hint_count" in implemented_sensor_keys(runtime)
    assert "car_light_password_policy_hint_count" in implemented_sensor_keys(runtime)
    assert "car_light_password_reset_hint_count" in implemented_sensor_keys(runtime)
    assert "car_light_trigger_storage_hint_count" in implemented_sensor_keys(runtime)
    assert "car_light_trigger_action_count" in implemented_sensor_keys(runtime)
    assert "car_light_route_count" in implemented_sensor_keys(runtime)
    assert "car_light_setup_requirement_count" in implemented_sensor_keys(runtime)
    assert "car_light_setup_flow_hint_count" in implemented_sensor_keys(runtime)
    assert "car_light_setup_key_hint_count" in implemented_sensor_keys(runtime)
    assert "car_light_model_role_hint_count" in implemented_sensor_keys(runtime)
    assert "car_light_protocol_gap_count" in implemented_sensor_keys(runtime)
    assert "car_light_command_blocker_count" in implemented_sensor_keys(runtime)
    assert "car_light_apk_asset_evidence_count" in implemented_sensor_keys(runtime)
    assert "car_light_apk_package_asset_count" in implemented_sensor_keys(
        runtime
    )
    assert "car_light_apk_string_evidence_count" in implemented_sensor_keys(runtime)

    mic = build_runtime({CONF_MODEL: "SP-MIC", CONF_DEVICE_ID: "mic"})
    mic_diagnostics = runtime_diagnostics(mic)

    assert mic.diagnostic_value("accessory_role") == (
        "wireless_microphone_accessory"
    )
    assert mic.diagnostic_value("car_light_required_controller") == "SP702E"
    assert mic.diagnostic_value("car_light_setup_stage") == "accessory_after_sp702e"
    assert mic.diagnostic_value("car_light_setup_order") == "none"
    assert mic.diagnostic_value("car_light_setup_dependency") == (
        "requires_chassis_controller"
    )
    assert mic_diagnostics["model"]["car_light_model_role"] == {
        "role": "wireless_microphone_accessory",
        "setup_stage": "accessory_after_sp702e",
        "setup_order": None,
        "required_controller_model": "SP702E",
        "parent_group_model_id": 65537,
    }
    assert mic_diagnostics["model"]["car_light_required_controller"] == "SP702E"
    assert mic_diagnostics["model"]["car_light_profile"][
        "required_controller_model"
    ] == "SP702E"
    assert mic_diagnostics["model"]["car_light_profile"][
        "model_setup_dependency"
    ] == {
        "model_name": "SP-MIC",
        "relationship": "requires_chassis_controller",
        "related_model": "SP702E",
        "setup_order": None,
        "required": True,
        "enforcement_status": "diagnostic_only",
        "evidence": "SP-MIC required_controller=SP702E",
    }
    assert mic.diagnostic_value("car_light_command_blocker_count") == 7
    assert "car_light_sp_mic_event_pending" in mic_diagnostics["model"][
        "support_disposition"
    ]
    assert "car_light_sp_mic_event_pending" in mic_diagnostics["model"][
        "car_light_profile"
    ]["command_blockers"]
    assert "accessory_dependency=SP702E" in mic_diagnostics["model"][
        "support_disposition"
    ]

    non_car = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})
    assert non_car.diagnostic_value("car_light_route_count") is None
    assert non_car.diagnostic_value("car_light_required_controller") is None
    assert non_car.diagnostic_value("car_light_setup_stage") is None
    assert non_car.diagnostic_value("car_light_setup_order") is None
    assert non_car.diagnostic_value("car_light_setup_dependency") is None
    assert non_car.diagnostic_value("car_light_setup_dependency_count") is None
    assert (
        non_car.diagnostic_value("car_light_required_setup_dependency_count")
        is None
    )
    assert non_car.diagnostic_value("car_light_ordered_setup_model_count") is None
    assert non_car.diagnostic_value("car_light_control_surface_count") is None
    assert non_car.diagnostic_value("car_light_animation_asset_count") is None
    assert non_car.diagnostic_value("car_light_password_entry_hint_count") is None
    assert non_car.diagnostic_value("car_light_password_policy_hint_count") is None
    assert non_car.diagnostic_value("car_light_password_reset_hint_count") is None
    assert non_car.diagnostic_value("car_light_subdevice_filter_count") is None
    assert non_car.diagnostic_value("car_light_setup_flow_hint_count") is None
    assert non_car.diagnostic_value("car_light_setup_key_hint_count") is None
    assert non_car.diagnostic_value("car_light_model_role_hint_count") is None
    assert non_car.diagnostic_value("car_light_command_blocker_count") is None
    assert "car_light_route_count" not in implemented_sensor_keys(non_car)
    assert "car_light_setup_dependency" not in implemented_sensor_keys(non_car)
    assert "car_light_setup_dependency_count" not in implemented_sensor_keys(non_car)
    assert "car_light_required_setup_dependency_count" not in implemented_sensor_keys(
        non_car
    )
    assert "car_light_ordered_setup_model_count" not in implemented_sensor_keys(
        non_car
    )
    assert "car_light_control_surface_count" not in implemented_sensor_keys(non_car)
    assert "car_light_animation_asset_count" not in implemented_sensor_keys(non_car)
    assert "car_light_password_entry_hint_count" not in implemented_sensor_keys(
        non_car
    )
    assert "car_light_password_policy_hint_count" not in implemented_sensor_keys(
        non_car
    )
    assert "car_light_password_reset_hint_count" not in implemented_sensor_keys(
        non_car
    )
    assert "car_light_subdevice_filter_count" not in implemented_sensor_keys(non_car)
    assert "car_light_setup_flow_hint_count" not in implemented_sensor_keys(non_car)
    assert "car_light_setup_key_hint_count" not in implemented_sensor_keys(non_car)
    assert "car_light_model_role_hint_count" not in implemented_sensor_keys(non_car)
    assert "car_light_command_blocker_count" not in implemented_sensor_keys(non_car)


def test_runtime_diagnostics_exposes_fish_tank_profile() -> None:
    """Diagnostics expose APK FT001 package routes and profile surfaces."""
    runtime = build_runtime({CONF_MODEL: "FT001", CONF_DEVICE_ID: "tank"})

    diagnostics = runtime_diagnostics(runtime)

    assert diagnostics["model"]["family"] == "fish_tank"
    assert diagnostics["runtime"]["protocol_ready"] is False
    assert diagnostics["model"]["fish_tank_profile"] == {
        "family": "fish_tank",
        "package": "packages/fish_tank_lights",
        "light_channels": ["First light", "Second light"],
        "control_surfaces": [
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
        ],
        "route_hints": [
            "/device/fish_tank_lights",
            "/device/fish_tank_lights/settings",
            "/device/fish_tank_lights/settings/rename",
            "/device/fish_tank_lights/settings/timer_list2",
            "/device/fish_tank_lights/settings/timer_list/timer_config",
            "/device/fish_tank_lights/favorite/favorite_edit",
        ],
        "effect_hints": [
            "Windmill",
            "springwater",
        ],
        "effect_string_hints": [
            "Windmill",
            "springwater",
            "waterdrop",
            "Flowing Water",
            "Spring Water2",
            "Stromend Water",
        ],
        "icon_assets": [
            "packages/fish_tank_lights/assets/icons/ic_add_timer.png",
            "packages/fish_tank_lights/assets/icons/ic_checked.png",
            "packages/fish_tank_lights/assets/icons/ic_close.png",
            "packages/fish_tank_lights/assets/icons/ic_light_first.png",
            "packages/fish_tank_lights/assets/icons/ic_light_second.png",
            "packages/fish_tank_lights/assets/icons/ic_color_correct.png",
            "packages/fish_tank_lights/assets/icons/ic_color_palette.png",
            "packages/fish_tank_lights/assets/icons/ic_delete.png",
            "packages/fish_tank_lights/assets/icons/ic_edit.png",
            "packages/fish_tank_lights/assets/icons/ic_heart.png",
            "packages/fish_tank_lights/assets/icons/ic_lightness.png",
            "packages/fish_tank_lights/assets/icons/ic_speed.png",
            "packages/fish_tank_lights/assets/icons/ic_timer.png",
            "packages/fish_tank_lights/assets/icons/ic_network_config.png",
            "packages/fish_tank_lights/assets/icons/ic_pencil.png",
            "packages/fish_tank_lights/assets/icons/ic_pencil_color.png",
            "packages/fish_tank_lights/assets/icons/ic_reset.png",
            "packages/fish_tank_lights/assets/icons/ic_select_all.png",
            "packages/fish_tank_lights/assets/icons/ic_settings.png",
            "packages/fish_tank_lights/assets/icons/ic_unchecked.png",
            "packages/fish_tank_lights/assets/icons/ic_unselect_all.png",
            "packages/fish_tank_lights/assets/icons/ic_version.png",
            "packages/fish_tank_lights/assets/icons/ic_windmill.png",
        ],
        "image_assets": [
            "packages/fish_tank_lights/assets/images/img_background.png",
            "packages/fish_tank_lights/assets/images/img_color_palette.png",
            "packages/fish_tank_lights/assets/images/img_fav_empty.png",
            "packages/fish_tank_lights/assets/images/img_fish_tank.png",
            "packages/fish_tank_lights/assets/images/img_timer_empty.png",
            "packages/fish_tank_lights/assets/images/img_timer_tip.png",
            "packages/fish_tank_lights/assets/images/img_windmill.png",
        ],
        "channel_assets": [
            "packages/fish_tank_lights/assets/icons/ic_light_first.png",
            "packages/fish_tank_lights/assets/icons/ic_light_second.png",
        ],
        "timer_assets": [
            "packages/fish_tank_lights/assets/icons/ic_add_timer.png",
            "packages/fish_tank_lights/assets/icons/ic_timer.png",
            "packages/fish_tank_lights/assets/images/img_timer_empty.png",
            "packages/fish_tank_lights/assets/images/img_timer_tip.png",
        ],
        "favorite_assets": [
            "packages/fish_tank_lights/assets/icons/ic_heart.png",
            "packages/fish_tank_lights/assets/images/img_fav_empty.png",
        ],
        "effect_assets": [
            "packages/fish_tank_lights/assets/icons/ic_windmill.png",
            "packages/fish_tank_lights/assets/images/img_windmill.png",
        ],
        "workflow_hints": [
            "First/second light channel selection",
            "Color palette editing",
            "Color correction",
            "Windmill effect",
            "Timer add/edit/delete/select workflow",
            "Favorite effect edit/empty state",
            "Device settings and rename",
            "Network configuration",
        ],
        "favorite_slots": [
            "Favorite 1",
            "Favorite 2",
            "Favorite 3",
            "Favorite 4",
        ],
        "favorite_action_hints": [
            "FavoriteStore0",
            "FavoriteStore1",
            "FavoriteStore2",
            "FavoriteStore3",
            "FavoriteRecall0",
            "FavoriteRecall1",
            "FavoriteRecall2",
            "FavoriteRecall3",
            "FavoriteClear0",
            "FavoriteClear1",
            "FavoriteClear2",
            "FavoriteClear3",
        ],
        "favorite_store_hints": [
            "FavoriteStore0",
            "FavoriteStore1",
            "FavoriteStore2",
            "FavoriteStore3",
        ],
        "favorite_recall_hints": [
            "FavoriteRecall0",
            "FavoriteRecall1",
            "FavoriteRecall2",
            "FavoriteRecall3",
        ],
        "favorite_clear_hints": [
            "FavoriteClear0",
            "FavoriteClear1",
            "FavoriteClear2",
            "FavoriteClear3",
        ],
        "favorite_actions": [
            "Store favorite",
            "Recall favorite",
            "Clear favorite",
        ],
        "favorite_loop_hints": [
            "favoriteLightingEffectLoopEnabled",
            "favoriteLfx",
            "NextFavoriteChannel",
            "Loop all favorite effects",
            "Stop looping the favorite effects",
        ],
        "favorite_loop_actions": [
            "Loop all favorite effects",
            "Stop looping the favorite effects",
        ],
        "firmware_prompt_hints": [
            "FishTankLights:fw_prompted_",
        ],
        "timer_limit": 5,
        "timer_slots": [
            "Timer 1",
            "Timer 2",
            "Timer 3",
            "Timer 4",
            "Timer 5",
        ],
        "timer_hints": [
            "idxTimerTaskCount",
            "Flutter | D -> idxTimerTaskCount = ",
            "newTimerId",
            "Timer interface not supported.",
            "removeTimingTask",
            "saveTimingTask",
            "timing_task",
            "You can only add up to 5 timers!",
        ],
        "timer_string_hints": [
            "idxTimerTaskCount",
            "Flutter | D -> idxTimerTaskCount = ",
            "newTimerId",
            "newTimerId: 2",
            "timerConfig",
            "Timer interface not supported.",
            "You can only add up to 5 timers!",
            "removeTimingTask",
            "saveTimingTask",
            "timing_task",
        ],
        "timer_actions": [
            "Save timer",
            "Remove timer",
        ],
        "catalog_hints": [
            "model_id=150",
            "connectCaps=7",
            "specFunctions=145",
            "colorCap=1",
            "transports=ble,lan,cloud_optional",
        ],
        "app_method_hints": [
            "getNetworkInfo",
            "setBrightness",
            "setLfxColor",
            "setLfxColorTemp",
            "setLfxSpeed",
            "setSolidColor",
            "setSolidColorTemp",
            "saveFavoriteEffectList",
            "updateFavoriteLfxList",
        ],
        "data_model_hints": [
            "FavoriteLightingEffectApiService",
            "FavEffectNameEntity",
            "FavoriteEffectName",
            "FavoriteStore0-3",
            "FavoriteRecall0-3",
            "FavoriteClear0-3",
            "favoriteLightingEffectIds",
            "favoriteLightingEffectLoopEnabled",
        ],
        "favorite_service_hints": [
            "FavoriteLightingEffectApiService",
        ],
        "favorite_storage_hints": [
            "FavEffectNameEntity",
            "FavoriteEffectName",
            "favoriteLightingEffectIds",
            "favoriteLightingEffectLoopEnabled",
            "favoriteLfx",
        ],
        "timer_storage_hints": [
            "idxTimerTaskCount",
            "newTimerId",
            "timerConfig",
            "timing_task",
        ],
        "brightness_state_hints": [
            "raw-brightness-",
            "whiteBrightness",
            "white_brightness",
        ],
        "raw_string_hints": [
            "newTimerId: 2",
            "timerConfig",
            "raw-brightness-",
            ", whiteBrightness: ",
            "whiteBrightness",
            "white_brightness",
            "white_brightness INTEGER",
            "Windmill",
            "springwater",
            "waterdrop",
            "Flowing Water",
            "Spring Water2",
            "Stromend Water",
            "favoriteLightingEffectLoopEnabled",
            "favoriteLfx",
            "NextFavoriteChannel",
            "Loop all favorite effects",
            "Stop looping the favorite effects",
            "FishTankLights:fw_prompted_",
        ],
        "brightness_string_hints": [
            "raw-brightness-",
            ", whiteBrightness: ",
            "whiteBrightness",
            "white_brightness",
            "white_brightness INTEGER",
        ],
        "transport_hints": [
            "connectCaps=7 maps to BLE, LAN, and optional cloud in the catalog",
            (
                "Native UUID pool includes ffe0/ffe1 and ff12/ff14/ff15 "
                "but no FT001 binding"
            ),
            "LAN discovery/control packet shape remains unconfirmed",
        ],
        "protocol_gap_hints": [
            "No old-UniLED FT001 implementation was found",
            "No FT001-specific BLE opcode table was recovered",
            "No FT001 notification/status parser shape was recovered",
            "No FT001 LAN endpoint or refresh packet was recovered",
            "FT001 has no supportGetNetInfo catalog extra in APK 3.3.1",
        ],
        "command_blockers": [
            "fish_tank_ble_opcode_pending",
            "fish_tank_status_parser_pending",
            "fish_tank_lan_refresh_pending",
            "fish_tank_timer_frame_pending",
            "fish_tank_favorite_frame_pending",
            "fish_tank_effect_packet_pending",
            "fish_tank_brightness_parser_pending",
        ],
        "command_protocol_known": False,
        "package_asset_count": 30,
        "apk_asset_evidence": [
            "packages/fish_tank_lights/assets/icons/ic_add_timer.png",
            "packages/fish_tank_lights/assets/icons/ic_checked.png",
            "packages/fish_tank_lights/assets/icons/ic_close.png",
            "packages/fish_tank_lights/assets/icons/ic_light_first.png",
            "packages/fish_tank_lights/assets/icons/ic_light_second.png",
            "packages/fish_tank_lights/assets/icons/ic_color_correct.png",
            "packages/fish_tank_lights/assets/icons/ic_color_palette.png",
            "packages/fish_tank_lights/assets/icons/ic_delete.png",
            "packages/fish_tank_lights/assets/icons/ic_edit.png",
            "packages/fish_tank_lights/assets/icons/ic_heart.png",
            "packages/fish_tank_lights/assets/icons/ic_lightness.png",
            "packages/fish_tank_lights/assets/icons/ic_speed.png",
            "packages/fish_tank_lights/assets/icons/ic_timer.png",
            "packages/fish_tank_lights/assets/icons/ic_network_config.png",
            "packages/fish_tank_lights/assets/icons/ic_pencil.png",
            "packages/fish_tank_lights/assets/icons/ic_pencil_color.png",
            "packages/fish_tank_lights/assets/icons/ic_reset.png",
            "packages/fish_tank_lights/assets/icons/ic_select_all.png",
            "packages/fish_tank_lights/assets/icons/ic_settings.png",
            "packages/fish_tank_lights/assets/icons/ic_unchecked.png",
            "packages/fish_tank_lights/assets/icons/ic_unselect_all.png",
            "packages/fish_tank_lights/assets/icons/ic_version.png",
            "packages/fish_tank_lights/assets/icons/ic_windmill.png",
            "packages/fish_tank_lights/assets/images/img_background.png",
            "packages/fish_tank_lights/assets/images/img_color_palette.png",
            "packages/fish_tank_lights/assets/images/img_fav_empty.png",
            "packages/fish_tank_lights/assets/images/img_fish_tank.png",
            "packages/fish_tank_lights/assets/images/img_timer_empty.png",
            "packages/fish_tank_lights/assets/images/img_timer_tip.png",
            "packages/fish_tank_lights/assets/images/img_windmill.png",
        ],
        "apk_string_evidence": [
            "FT001 catalog home_uri is /device/fish_tank_lights",
            "FT001 catalog flags are connectCaps=7, specFunctions=145, colorCap=1",
            (
                "Native routes expose settings, rename, timer_list2, "
                "timer_config, and favorite_edit"
            ),
            (
                "Native strings/assets include Windmill; native string table "
                "also includes springwater"
            ),
            (
                "Native string table includes waterdrop, Flowing Water, "
                "Spring Water2, and Stromend Water labels"
            ),
            (
                "Native strings include favorite effect service/storage names "
                "and save/update methods"
            ),
            "Native strings expose FavoriteStore/Recall/Clear slots 0-3",
            "Native strings expose favorite-loop actions and NextFavoriteChannel",
            "Native strings expose FishTankLights:fw_prompted_ firmware prompt storage",
            (
                "Native timer strings include idxTimerTaskCount, newTimerId, "
                "and exact 5-timer limit text"
            ),
            (
                "Native string table includes raw brightness and "
                "white-brightness state labels"
            ),
        ],
    }
    assert runtime.diagnostic_value("fish_tank_profile") == (
        "fish_tank; package=packages/fish_tank_lights; "
        "channels=2; surfaces=10; effects=2; effect_strings=6; "
        "icons=23; images=7; "
        "channel_assets=2; timer_assets=4; favorite_assets=2; "
        "effect_assets=2; workflows=8; favorites=4; "
        "favorite_actions=12; favorite_store=4; favorite_recall=4; "
        "favorite_clear=4; favorite_action_types=3; "
        "favorite_loop_hints=5; favorite_loop_actions=2; "
        "firmware_prompts=1; "
        "timer_limit=5; timers=5; timer_strings=10; timer_actions=2; "
        "methods=9; data=8; favorite_services=1; favorite_storage=5; "
        "timer_storage=4; brightness_state=3; raw_strings=19; "
        "brightness_strings=5; gaps=5; blockers=7; package_assets=30; "
        "command_protocol_pending; routes=6"
    )
    assert runtime.diagnostic_value("fish_tank_favorite_slot_count") == 4
    assert runtime.diagnostic_value("fish_tank_timer_limit") == 5
    assert runtime.diagnostic_value("fish_tank_light_channel_count") == 2
    assert runtime.diagnostic_value("fish_tank_control_surface_count") == 10
    assert runtime.diagnostic_value("fish_tank_route_count") == 6
    assert runtime.diagnostic_value("fish_tank_effect_hint_count") == 2
    assert runtime.diagnostic_value("fish_tank_effect_string_hint_count") == 6
    assert runtime.diagnostic_value("fish_tank_icon_asset_count") == 23
    assert runtime.diagnostic_value("fish_tank_image_asset_count") == 7
    assert runtime.diagnostic_value("fish_tank_channel_asset_count") == 2
    assert runtime.diagnostic_value("fish_tank_timer_asset_count") == 4
    assert runtime.diagnostic_value("fish_tank_favorite_asset_count") == 2
    assert runtime.diagnostic_value("fish_tank_effect_asset_count") == 2
    assert runtime.diagnostic_value("fish_tank_workflow_hint_count") == 8
    assert runtime.diagnostic_value("fish_tank_favorite_action_count") == 12
    assert runtime.diagnostic_value("fish_tank_favorite_store_hint_count") == 4
    assert runtime.diagnostic_value("fish_tank_favorite_recall_hint_count") == 4
    assert runtime.diagnostic_value("fish_tank_favorite_clear_hint_count") == 4
    assert runtime.diagnostic_value("fish_tank_favorite_action_type_count") == 3
    assert runtime.diagnostic_value("fish_tank_favorite_loop_hint_count") == 5
    assert runtime.diagnostic_value("fish_tank_favorite_loop_action_count") == 2
    assert runtime.diagnostic_value("fish_tank_firmware_prompt_hint_count") == 1
    assert runtime.diagnostic_value("fish_tank_timer_slot_count") == 5
    assert runtime.diagnostic_value("fish_tank_timer_action_count") == 2
    assert runtime.diagnostic_value("fish_tank_timer_hint_count") == 8
    assert runtime.diagnostic_value("fish_tank_timer_string_hint_count") == 10
    assert runtime.diagnostic_value("fish_tank_app_method_count") == 9
    assert runtime.diagnostic_value("fish_tank_data_model_hint_count") == 8
    assert runtime.diagnostic_value("fish_tank_favorite_service_hint_count") == 1
    assert runtime.diagnostic_value("fish_tank_favorite_storage_hint_count") == 5
    assert runtime.diagnostic_value("fish_tank_timer_storage_hint_count") == 4
    assert runtime.diagnostic_value("fish_tank_brightness_state_hint_count") == 3
    assert runtime.diagnostic_value("fish_tank_raw_string_hint_count") == 19
    assert runtime.diagnostic_value("fish_tank_brightness_string_hint_count") == 5
    assert runtime.diagnostic_value("fish_tank_protocol_gap_count") == 5
    assert runtime.diagnostic_value("fish_tank_command_blocker_count") == 7
    assert runtime.diagnostic_value("fish_tank_apk_asset_evidence_count") == 30
    assert runtime.diagnostic_value("fish_tank_apk_package_asset_count") == 30
    assert runtime.diagnostic_value("fish_tank_apk_string_evidence_count") == 11
    assert "fish_tank_profile" in implemented_sensor_keys(runtime)
    assert "fish_tank_favorite_slot_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_timer_limit" in implemented_sensor_keys(runtime)
    assert "fish_tank_light_channel_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_control_surface_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_route_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_effect_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_effect_string_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_icon_asset_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_image_asset_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_channel_asset_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_timer_asset_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_favorite_asset_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_effect_asset_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_workflow_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_favorite_action_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_favorite_store_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_favorite_recall_hint_count" in implemented_sensor_keys(
        runtime
    )
    assert "fish_tank_favorite_clear_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_favorite_action_type_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_favorite_loop_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_favorite_loop_action_count" in implemented_sensor_keys(
        runtime
    )
    assert "fish_tank_firmware_prompt_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_timer_slot_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_timer_action_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_timer_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_timer_string_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_app_method_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_data_model_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_favorite_service_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_favorite_storage_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_timer_storage_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_brightness_state_hint_count" in implemented_sensor_keys(
        runtime
    )
    assert "fish_tank_raw_string_hint_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_brightness_string_hint_count" in implemented_sensor_keys(
        runtime
    )
    assert "fish_tank_protocol_gap_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_command_blocker_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_apk_asset_evidence_count" in implemented_sensor_keys(runtime)
    assert "fish_tank_apk_package_asset_count" in implemented_sensor_keys(
        runtime
    )
    assert "fish_tank_apk_string_evidence_count" in implemented_sensor_keys(runtime)

    non_fish = build_runtime({CONF_MODEL: "SP630E", CONF_DEVICE_ID: "bench"})
    assert non_fish.diagnostic_value("fish_tank_route_count") is None
    assert non_fish.diagnostic_value("fish_tank_icon_asset_count") is None
    assert non_fish.diagnostic_value("fish_tank_effect_string_hint_count") is None
    assert non_fish.diagnostic_value("fish_tank_favorite_loop_hint_count") is None
    assert non_fish.diagnostic_value("fish_tank_firmware_prompt_hint_count") is None
    assert non_fish.diagnostic_value("fish_tank_favorite_storage_hint_count") is None
    assert non_fish.diagnostic_value("fish_tank_timer_storage_hint_count") is None
    assert non_fish.diagnostic_value("fish_tank_brightness_state_hint_count") is None
    assert non_fish.diagnostic_value("fish_tank_timer_string_hint_count") is None
    assert non_fish.diagnostic_value("fish_tank_brightness_string_hint_count") is None
    assert non_fish.diagnostic_value("fish_tank_command_blocker_count") is None
    assert "fish_tank_route_count" not in implemented_sensor_keys(non_fish)
    assert "fish_tank_icon_asset_count" not in implemented_sensor_keys(non_fish)
    assert "fish_tank_effect_string_hint_count" not in implemented_sensor_keys(
        non_fish
    )
    assert "fish_tank_favorite_loop_hint_count" not in implemented_sensor_keys(
        non_fish
    )
    assert "fish_tank_favorite_storage_hint_count" not in implemented_sensor_keys(
        non_fish
    )
    assert "fish_tank_timer_storage_hint_count" not in implemented_sensor_keys(
        non_fish
    )
    assert "fish_tank_brightness_state_hint_count" not in implemented_sensor_keys(
        non_fish
    )
    assert "fish_tank_firmware_prompt_hint_count" not in implemented_sensor_keys(
        non_fish
    )
    assert "fish_tank_timer_string_hint_count" not in implemented_sensor_keys(
        non_fish
    )
    assert "fish_tank_brightness_string_hint_count" not in implemented_sensor_keys(
        non_fish
    )
    assert "fish_tank_command_blocker_count" not in implemented_sensor_keys(non_fish)


def test_runtime_can_attach_zengge_mesh_without_command_entities() -> None:
    """RG4 can hold a mesh connection while normal command gates stay closed."""
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_MESH_UUID: 0x0211,
            CONF_MESH_NODE_ID: 0x11,
            CONF_MESH_NODE_TYPE: 2,
        }
    )
    transport = RecordingMeshTransport()

    connection = runtime.attach_zengge_mesh_transport(
        transport,
        block_encryptor=_identity_block_encryptor,
    )

    assert runtime.session is None
    assert runtime.session_ready is False
    assert runtime.mesh_connection is connection
    assert runtime.mesh_transport_ready is True
    assert runtime.mesh_session_paired is False
    assert command_light_features(runtime) == ()
    assert command_number_features(runtime) == ()
    assert not command_control_available(runtime, "effect_speed", channel=0x11)
    assert not command_control_available(runtime, "effect_level", channel=0x11)
    assert command_select_features(runtime) == ()
    assert command_switch_features(runtime) == ()
    assert runtime.mesh_session.contexts[0x11].node_type == 2

    key = asyncio.run(connection.pair(session_random=b"12345678"))
    diagnostics = runtime_diagnostics(runtime)

    assert key == bytes.fromhex(
        "31 32 33 34 35 36 37 38 41 42 43 44 45 46 47 48"
    )
    assert runtime.mesh_session_paired is True
    assert diagnostics["runtime"]["session_ready"] is False
    assert diagnostics["runtime"]["mesh_transport_ready"] is True
    assert diagnostics["runtime"]["mesh_session_paired"] is True
    numbers = command_number_features(runtime)
    assert [(number.key, number.channel) for number in numbers] == [
        ("effect_speed", 0x11),
        ("effect_level", 0x11),
    ]

    asyncio.run(runtime.async_close())

    assert transport.closed is True
    assert runtime.mesh_session is None
    assert runtime.mesh_connection is None


def test_zengge_mesh_credentials_are_redacted_and_used_for_pairing() -> None:
    """Custom mesh credentials flow into pairing without leaking diagnostics."""
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_MESH_KEY: "MeshName",
            CONF_MESH_PASSWORD: "MeshPassword",
        }
    )
    transport = RecordingMeshTransport()
    runtime.attach_zengge_mesh_transport(
        transport,
        block_encryptor=_identity_block_encryptor,
    )

    assert zengge_mesh_credentials(runtime) == (b"MeshName", b"MeshPassword")

    session_key = asyncio.run(
        async_pair_zengge_mesh(runtime, session_random=b"12345678")
    )
    diagnostics = runtime_diagnostics(runtime)

    assert session_key == bytes.fromhex(
        "31 32 33 34 35 36 37 38 41 42 43 44 45 46 47 48"
    )
    assert transport.writes[0] == (
        "pair",
        make_pair_packet(
            b"MeshName",
            b"MeshPassword",
            b"12345678",
            block_encryptor=_identity_block_encryptor,
        ),
        True,
    )
    assert diagnostics["entry"][CONF_MESH_KEY] == "**REDACTED**"
    assert diagnostics["entry"][CONF_MESH_PASSWORD] == "**REDACTED**"
    assert diagnostics["runtime"]["mesh_session_paired"] is True


def test_zengge_mesh_credentials_default_to_old_uniled_values() -> None:
    """Missing mesh credentials use the old UniLED default Zengge pair values."""
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        }
    )

    assert zengge_mesh_credentials(runtime) == (
        b"ZenggeMesh",
        b"ZenggeTechnology",
    )


def test_zengge_mesh_light_features_appear_after_pairing() -> None:
    """Known paired mesh nodes become runtime light features."""
    runtime, _transport = _paired_rg4_runtime()

    features = command_light_features(runtime)

    assert len(features) == 1
    assert runtime.diagnostic_value("mesh_role") == (
        "zengge_mesh; transport_ready; paired; nodes=1; "
        "command_nodes=1; strip_nodes=1; bulb_nodes=0; "
        "panel_nodes=0; bridge_seen=False"
    )
    assert runtime.diagnostic_value("mesh_known_node_count") == 1
    assert runtime.diagnostic_value("mesh_command_node_count") == 1
    assert runtime.diagnostic_value("mesh_strip_node_count") == 1
    assert runtime.diagnostic_value("mesh_bulb_node_count") == 0
    assert runtime.diagnostic_value("mesh_panel_node_count") == 0
    assert runtime.diagnostic_value("mesh_bridge_seen") is False
    assert features[0].key == "mesh_light_44"
    assert features[0].channel == 0x44
    assert features[0].name == "Strip 68"
    assert features[0].implemented is True
    assert features[0].implementation_hint == "zengge_mesh_node"
    assert features[0].color_modes == ("brightness",)
    numbers = command_number_features(runtime)
    assert [(number.key, number.channel) for number in numbers] == [
        ("effect_speed", 0x44),
        ("effect_level", 0x44),
    ]
    assert [number.name for number in numbers] == [
        "Strip 68 effect speed",
        "Strip 68 effect level",
    ]
    assert [number.minimum for number in numbers] == [0, 0]
    assert [number.maximum for number in numbers] == [100, 100]
    assert command_control_available(runtime, "effect_speed", channel=0x44)
    assert command_control_available(runtime, "effect_level", channel=0x44)
    selects = command_select_features(runtime)
    assert len(selects) == 1
    assert selects[0].key == "effect"
    assert selects[0].channel == 0x44
    assert selects[0].name == "Strip 68 effect"
    assert selects[0].implemented is True
    assert selects[0].implementation_hint == "zengge_mesh_node"
    assert selects[0].options[:3] == (
        "Seven Color Cross Fade",
        "Red Gradual Change",
        "Green Gradual Change",
    )
    assert command_switch_features(runtime) == ()
    assert select_options(runtime, "effect", channel=0x44)[:3] == (
        "Seven Color Cross Fade",
        "Red Gradual Change",
        "Green Gradual Change",
    )
    assert (
        effect_command_value(runtime, "Seven Color Jumping Change")
        == 0x14
    )


def test_zengge_mesh_bulb_node_type_uses_old_uniled_role_name() -> None:
    """Old-UniLED Zengge device type 5 is a command-capable bulb node."""
    runtime, _transport = _paired_rg4_runtime(node_id=0x45, node_type=5)

    features = command_light_features(runtime)

    assert zengge_mesh_node_ids(runtime) == (0x45,)
    assert runtime.diagnostic_value("mesh_strip_node_count") == 0
    assert runtime.diagnostic_value("mesh_bulb_node_count") == 1
    assert runtime.diagnostic_value("mesh_role") == (
        "zengge_mesh; transport_ready; paired; nodes=1; "
        "command_nodes=1; strip_nodes=0; bulb_nodes=1; "
        "panel_nodes=0; bridge_seen=False"
    )
    assert features[0].name == "Bulb 69"
    assert command_select_features(runtime)[0].name == "Bulb 69 effect"


def test_zengge_mesh_light_modes_follow_node_wiring_and_status() -> None:
    """Mesh light color modes use old-UniLED node wiring semantics."""
    runtime, _transport = _paired_rg4_runtime()
    assert runtime.mesh_session is not None
    runtime.mesh_session.register_node(
        ZenggeNodeContext(
            node_id=0x44,
            node_type=2,
            node_wiring=4,
            name="Strip",
        )
    )

    assert light_supported_color_modes(runtime, channel=0x44) == (
        "rgb",
        "color_temp",
    )
    assert command_light_features(runtime)[0].name == "Strip"

    state = channel_state(runtime, 0x44)
    state.extra["color_mode"] = "color_temp"
    assert light_color_mode(runtime, channel=0x44) == "color_temp"

    state.extra["supported_color_modes"] = ("rgb", "white")
    state.extra["color_mode"] = "white"
    state.warm_white = 64

    assert light_supported_color_modes(runtime, channel=0x44) == (
        "rgb",
        "white",
    )
    assert light_color_mode(runtime, channel=0x44) == "white"


def test_zengge_mesh_runtime_uses_cloud_node_metadata() -> None:
    """Cloud metadata supplies mesh credentials, names, wiring, and redaction."""
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_MESH_UUID: 0x0211,
            CONF_MESH_KEY: "CloudMesh",
            CONF_MESH_PASSWORD: "CloudPassword",
            CONF_MESH_LTK: "CloudToken",
            CONF_MESH_NODES: [
                {
                    CONF_MESH_NODE_ID: "0x44",
                    CONF_MESH_NODE_TYPE: "2",
                    CONF_MESH_NODE_WIRING: "4",
                    "name": "Counter Strip",
                    "area": "Kitchen",
                }
            ],
        }
    )
    transport = RecordingMeshTransport()
    runtime.attach_zengge_mesh_transport(
        transport,
        block_encryptor=_identity_block_encryptor,
    )

    assert runtime.mesh_session is not None
    context = runtime.mesh_session.contexts[0x44]
    assert context.node_type == 2
    assert context.node_wiring == 4
    assert context.name == "Counter Strip"
    assert context.area == "Kitchen"
    assert zengge_mesh_node_ids(runtime) == (0x44,)

    asyncio.run(async_pair_zengge_mesh(runtime, session_random=b"12345678"))

    features = command_light_features(runtime)
    diagnostics = runtime_diagnostics(runtime)

    assert features[0].name == "Counter Strip"
    assert features[0].color_modes == ("rgb", "color_temp")
    assert command_select_features(runtime)[0].name == "Counter Strip effect"
    assert transport.writes[0] == (
        "pair",
        make_pair_packet(
            b"CloudMesh",
            b"CloudPassword",
            b"12345678",
            block_encryptor=_identity_block_encryptor,
        ),
        True,
    )
    assert diagnostics["entry"][CONF_MESH_KEY] == "**REDACTED**"
    assert diagnostics["entry"][CONF_MESH_PASSWORD] == "**REDACTED**"
    assert diagnostics["entry"][CONF_MESH_LTK] == "**REDACTED**"


def test_zengge_mesh_runtime_commands_target_known_node() -> None:
    """Runtime node commands use old-UniLED packets without normal entities."""
    runtime, transport = _paired_rg4_runtime()

    assert runtime.session_ready is False
    assert zengge_mesh_node_ids(runtime) == (0x44,)
    assert zengge_mesh_command_ready(runtime) is True
    assert zengge_mesh_command_ready(runtime, 0x44) is True

    power = asyncio.run(
        set_zengge_mesh_power(
            runtime,
            0x44,
            True,
            sequence=bytes.fromhex("07 08 09"),
            response=True,
        )
    )
    brightness = asyncio.run(
        set_zengge_mesh_brightness(
            runtime,
            0x44,
            128,
            sequence=bytes.fromhex("0d 0e 0f"),
        )
    )
    rgb = asyncio.run(
        set_zengge_mesh_rgb(
            runtime,
            0x44,
            1,
            2,
            3,
            sequence=bytes.fromhex("10 11 12"),
        )
    )

    assert power is None
    assert brightness is None
    assert rgb is None
    assert transport.writes[-3:] == [
        (
            "command",
            bytes.fromhex(
                "07 08 09 bb ee 44 ff 3e cc ce fe 06 f7 09 "
                "00 00 00 00 00 00"
            ),
            True,
        ),
        (
            "command",
            bytes.fromhex(
                "0d 0e 0f bb ee 44 ff 3e cc ce fe 0f 3c 09 "
                "00 00 00 00 00 00"
            ),
            False,
        ),
        (
            "command",
            bytes.fromhex(
                "10 11 12 bb ee 44 ff 0c cc ce fe 70 10 10 03 "
                "00 00 00 00 00"
            ),
            False,
        ),
    ]

    channel = runtime.state.channel(0x44)
    assert channel is not None
    assert channel.power is True
    assert channel.brightness == 128
    assert channel.rgb == (1, 2, 3)
    assert channel.extra["node_id"] == 0x44
    assert runtime.state.available is True
    assert runtime.state.diagnostics["last_mesh_command"] == "rgb"
    assert runtime.state.diagnostics["last_mesh_command_node_id"] == 0x44
    assert command_light_features(runtime)[0].key == "mesh_light_44"


def test_zengge_mesh_runtime_commands_preserve_gradual_transition() -> None:
    """Runtime mesh helpers pass HA-style transitions into Zengge gradual bytes."""
    runtime, transport = _paired_rg4_runtime()

    asyncio.run(
        set_zengge_mesh_brightness(
            runtime,
            0x44,
            128,
            gradual_seconds=2.5,
            sequence=bytes.fromhex("0d 0e 0f"),
        )
    )

    assert transport.writes[-1] == (
        "command",
        bytes.fromhex(
            "0d 0e 0f bb ee 44 ff 3e cc ce fe 0f 3c 09 "
            "00 00 00 19 00 00"
        ),
        False,
    )
    assert channel_state(runtime, 0x44).brightness == 128


def test_legacy_set_state_service_uses_guarded_zengge_mesh_commands() -> None:
    """The compatibility service can target a paired known Zengge mesh node."""
    runtime, transport = _paired_rg4_runtime()

    changed = asyncio.run(
        async_apply_legacy_set_state_service(
            runtime,
            {
                "power": True,
                "rgb_color": (10, 20, 30),
                "brightness": 90,
                "transition": 2.5,
            },
            channel=0x44,
        )
    )

    state = channel_state(runtime, 0x44)
    assert changed is True
    assert state.power is True
    assert state.brightness == 90
    assert state.rgb == (10, 20, 30)
    assert [write[0] for write in transport.writes[-3:]] == [
        "command",
        "command",
        "command",
    ]
    assert transport.writes[-1][1][-3:] == bytes.fromhex("19 00 00")
    assert runtime.state.diagnostics["last_mesh_command"] == "brightness"
    assert runtime.state.diagnostics["last_mesh_command_node_id"] == 0x44


def test_zengge_mesh_runtime_color_and_effect_commands() -> None:
    """Runtime exposes every currently ported Zengge packet builder."""
    runtime, transport = _paired_rg4_runtime()

    asyncio.run(
        set_zengge_mesh_color_temp(
            runtime,
            0x44,
            4600,
            level=128,
            sequence=bytes.fromhex("13 14 15"),
        )
    )
    asyncio.run(
        set_zengge_mesh_white(
            runtime,
            0x44,
            64,
            sequence=bytes.fromhex("01 02 03"),
        )
    )
    asyncio.run(
        set_zengge_mesh_effect(
            runtime,
            0x44,
            0x14,
            speed=9,
            level=80,
            sequence=bytes.fromhex("04 05 06"),
        )
    )

    assert transport.writes[-3:] == [
        (
            "command",
            bytes.fromhex(
                "13 14 15 bb ee 44 ff 0c cc ce fe 71 25 27 "
                "00 00 00 00 00 00"
            ),
            False,
        ),
        (
            "command",
            bytes.fromhex(
                "01 02 03 bb ee 44 ff 0c cc ce fe 60 42 03 "
                "00 00 00 00 00 00"
            ),
            False,
        ),
        (
            "command",
            bytes.fromhex(
                "04 05 06 bb ee 44 ff 03 cc ce fe 10 0c 56 "
                "00 00 00 00 00 00"
            ),
            False,
        ),
    ]

    channel = runtime.state.channel(0x44)
    assert channel is not None
    assert channel.color_temp_kelvin == 4600
    assert channel.warm_white == 64
    assert channel.brightness == 80
    assert channel.effect_number == 0x14
    assert channel.effect == "Seven Color Jumping Change"
    assert channel.effect_type == "dynamic"
    assert channel.effect_speed == 9
    assert channel.extra["effect_level"] == 80
    assert control_value(runtime, "effect_level", channel=0x44) == 80
    assert runtime.state.diagnostics["last_mesh_command"] == "effect"


def test_zengge_mesh_effect_number_values_preserve_current_effect() -> None:
    """Partial mesh speed/level edits reuse the current effect packet values."""
    runtime, transport = _paired_rg4_runtime()

    asyncio.run(
        set_zengge_mesh_effect(
            runtime,
            0x44,
            0x14,
            speed=9,
            level=80,
            sequence=bytes.fromhex("04 05 06"),
        )
    )

    assert zengge_mesh_effect_command_values(runtime, 0x44, speed=12) == (
        0x14,
        12,
        80,
    )
    assert zengge_mesh_effect_command_values(runtime, 0x44, level=45) == (
        0x14,
        9,
        45,
    )

    effect, speed, level = zengge_mesh_effect_command_values(
        runtime,
        0x44,
        speed=12,
    )
    asyncio.run(
        set_zengge_mesh_effect(
            runtime,
            0x44,
            effect,
            speed=speed,
            level=level,
            sequence=bytes.fromhex("07 08 09"),
        )
    )

    assert transport.writes[-1] == (
        "command",
        bytes.fromhex(
            "07 08 09 bb ee 44 ff 03 cc ce fe 13 04 59 "
            "00 00 00 00 00 00"
        ),
        False,
    )
    assert control_value(runtime, "effect_speed", channel=0x44) == 12
    assert control_value(runtime, "effect_level", channel=0x44) == 80


def test_zengge_mesh_runtime_commands_require_known_paired_node() -> None:
    """Runtime refuses unsafe mesh command targets before transport writes."""
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_MESH_UUID: 0x0211,
            CONF_MESH_NODE_ID: 0x44,
            CONF_MESH_NODE_TYPE: 2,
        }
    )
    transport = RecordingMeshTransport()
    runtime.attach_zengge_mesh_transport(
        transport,
        block_encryptor=_identity_block_encryptor,
    )

    assert zengge_mesh_node_ids(runtime) == (0x44,)
    assert zengge_mesh_command_ready(runtime) is False
    assert zengge_mesh_command_ready(runtime, 0x44) is False

    try:
        asyncio.run(set_zengge_mesh_power(runtime, 0x44, True))
    except RuntimeSetupError as ex:
        assert "not paired" in str(ex)
    else:
        raise AssertionError("unpaired mesh commands should fail")

    asyncio.run(async_pair_zengge_mesh(runtime, session_random=b"12345678"))

    try:
        asyncio.run(set_zengge_mesh_power(runtime, 0x45, True))
    except RuntimeSetupError as ex:
        assert "not known" in str(ex)
    else:
        raise AssertionError("unknown mesh nodes should fail")

    assert zengge_mesh_command_ready(runtime, 0x45) is False
    assert [write[0] for write in transport.writes] == ["pair"]


def test_zengge_mesh_runtime_excludes_non_light_nodes() -> None:
    """Bridge and panel nodes stay out of command-capable mesh targets."""
    runtime, _transport = _paired_rg4_runtime(node_id=0x20, node_type=35)

    assert zengge_mesh_node_ids(runtime) == ()
    assert zengge_mesh_panel_node_ids(runtime) == (0x20,)
    assert zengge_mesh_command_ready(runtime) is False
    assert zengge_mesh_command_ready(runtime, 0x20) is False

    runtime.state.channels[0xFF] = ChannelState(
        channel_id=0xFF,
        extra={"node_kind": "bridge"},
    )
    assert zengge_mesh_node_ids(runtime) == ()
    assert runtime.diagnostic_value("mesh_role") == (
        "zengge_mesh; transport_ready; paired; nodes=2; "
        "command_nodes=0; strip_nodes=0; bulb_nodes=0; "
        "panel_nodes=1; bridge_seen=True"
    )
    assert runtime.diagnostic_value("mesh_known_node_count") == 2
    assert runtime.diagnostic_value("mesh_command_node_count") == 0
    assert runtime.diagnostic_value("mesh_strip_node_count") == 0
    assert runtime.diagnostic_value("mesh_bulb_node_count") == 0
    assert runtime.diagnostic_value("mesh_panel_node_count") == 1
    assert runtime.diagnostic_value("mesh_bridge_seen") is True

    try:
        asyncio.run(set_zengge_mesh_power(runtime, 0x20, True))
    except RuntimeSetupError as ex:
        assert "not known" in str(ex)
    else:
        raise AssertionError("panel nodes should not accept light commands")


def test_zengge_mesh_panel_nodes_create_status_sensors() -> None:
    """Old-UniLED Zengge panel nodes are exposed as diagnostics, not lights."""
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_MESH_UUID: 0x0211,
            CONF_MESH_NODES: [
                {
                    CONF_MESH_NODE_ID: "0x20",
                    CONF_MESH_NODE_TYPE: "35",
                    "name": "Wall Panel",
                },
                {
                    CONF_MESH_NODE_ID: "0x44",
                    CONF_MESH_NODE_TYPE: "2",
                    CONF_MESH_NODE_WIRING: "4",
                    "name": "Counter Strip",
                },
            ],
        }
    )
    transport = RecordingMeshTransport()
    runtime.attach_zengge_mesh_transport(
        transport,
        block_encryptor=_identity_block_encryptor,
    )

    assert zengge_mesh_node_ids(runtime) == (0x44,)
    assert zengge_mesh_panel_node_ids(runtime) == (0x20,)
    assert "mesh_panel_20_status" in implemented_sensor_keys(runtime)
    assert runtime.diagnostic_value("mesh_panel_20_status") is None

    features = diagnostic_sensor_features(runtime)
    panel = next(
        feature for feature in features if feature.key == "mesh_panel_20_status"
    )
    assert panel.platform.value == "sensor"
    assert panel.channel == 0x20
    assert panel.name == "Wall Panel status"
    assert panel.implemented is True
    assert panel.implementation_hint == "zengge_mesh_panel"
    assert "mesh_light_20" not in {
        feature.key for feature in command_light_features(runtime)
    }

    parsed = parse_zengge_notification_block(
        bytes((0x20, 0x01, 100, 0x00, 0x00)),
        context=ZenggeNodeContext(node_id=0x20, node_type=35, name="Wall Panel"),
    )
    assert parsed is not None
    runtime.state.channels[0x20] = parsed
    assert runtime.diagnostic_value("mesh_panel_20_status") == "Online"

    parsed = parse_zengge_notification_block(
        bytes((0x20, 0x00, 0, 0x00, 0x00)),
        context=ZenggeNodeContext(node_id=0x20, node_type=35, name="Wall Panel"),
    )
    assert parsed is not None
    runtime.state.channels[0x20] = parsed
    assert runtime.diagnostic_value("mesh_panel_20_status") == "Offline"


def test_zengge_mesh_refresh_pairs_and_requests_status() -> None:
    """Diagnostic mesh refresh pairs and kicks old UniLED status notifications."""
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        }
    )
    transport = RecordingMeshTransport()
    runtime.attach_zengge_mesh_transport(
        transport,
        block_encryptor=_identity_block_encryptor,
    )

    state = asyncio.run(
        async_refresh_zengge_mesh_state(runtime, session_random=b"12345678")
    )

    assert state is runtime.state
    assert state.available is True
    assert runtime.session_ready is False
    assert runtime.mesh_session_paired is True
    assert state.diagnostics["last_mesh_pair_result"] == "ok"
    assert state.diagnostics["last_mesh_status_request"] == "ok"
    assert transport.writes[0][0] == "pair"
    assert transport.writes[1] == ("status", b"\x01", True)
    assert command_light_features(runtime) == ()


def test_zengge_mesh_refresh_records_pair_failures_without_raising() -> None:
    """Pair failures remain diagnostics and keep RG4 command entities hidden."""
    runtime = build_runtime(
        {
            CONF_MODEL: "RG4",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
        }
    )
    transport = RecordingMeshTransport(pair_response=b"\x0eABCDEFGH")
    runtime.attach_zengge_mesh_transport(
        transport,
        block_encryptor=_identity_block_encryptor,
    )

    state = asyncio.run(
        async_refresh_zengge_mesh_state(runtime, session_random=b"12345678")
    )

    assert state is runtime.state
    assert state.available is False
    assert runtime.mesh_session_paired is False
    assert state.diagnostics["last_mesh_pair_result"] == "failed"
    assert "rejected" in state.diagnostics["last_mesh_pair_error"]
    assert "last_mesh_status_request" not in state.diagnostics
    assert command_light_features(runtime) == ()
    assert command_select_features(runtime) == ()


def test_runtime_rejects_zengge_mesh_attachment_without_ble_address() -> None:
    """Zengge packet crypto needs the node MAC address for nonces."""
    runtime = build_runtime({CONF_MODEL: "RG4", CONF_DEVICE_ID: "mesh"})

    try:
        runtime.attach_zengge_mesh_transport(RecordingMeshTransport())
    except RuntimeSetupError as ex:
        assert "BLE address" in str(ex)
    else:
        raise AssertionError("Zengge mesh attachment should require an address")
