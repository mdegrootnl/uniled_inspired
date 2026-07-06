"""LAN profile tests."""

from __future__ import annotations

from custom_components.uniled.core import (
    EntityCategoryKind,
    PlatformKind,
    default_catalog,
    plan_for_model,
)
from custom_components.uniled.core.transports import (
    build_spnet_discovery_request,
    describe_lan_profile,
    lan_profile_for_model,
    parse_spnet_discovery_response,
    sptech_legacy_model_name_for_code,
)


def test_custom_5xx_lan_profiles_preserve_apk_network_info_limits() -> None:
    """Custom 5xx LAN profiles expose the APK network-info and MTU facts."""
    catalog = default_catalog()

    for name in ("SP547E", "SP548E"):
        model = catalog.resolve_name(name)
        assert model is not None

        profile = lan_profile_for_model(model)

        assert profile is not None
        assert profile.family.value == "banlanx_custom_5xx"
        assert profile.network_info_code == 37
        assert profile.max_data_length == 185
        assert profile.command_protocol_known is False
        assert profile.discovery_confirmed is False
        assert profile.requires_manual_host is True
        assert [
            (candidate.code, candidate.code_hex, candidate.model_name)
            for candidate in profile.sptech_legacy_model_codes
        ] == [
            (0x4E, "0x4e", "SP530E"),
            (0x56, "0x56", "SP538E"),
            (0x57, "0x57", "SP539E"),
            (0x63, "0x63", "SP548E"),
            (0x64, "0x64", "SP549E"),
            (0x69, "0x69", "SP548E"),
        ]
        assert [
            candidate.code
            for candidate in profile.sptech_legacy_configuration_codes
        ] == [
            0x06,
            0x08,
            0x81,
            0x83,
            0x85,
            0x87,
            0x8A,
            0x82,
            0x84,
            0x8D,
            0x86,
            0x88,
            0x8B,
            0x8E,
            0x89,
            0x8C,
        ]
        assert [
            (candidate.name, candidate.command_id_hex, candidate.category)
            for candidate in profile.sptech_legacy_command_ids
        ] == [
            ("STATUS_QUERY", "0x02", "read_only_query"),
            ("ONOFF_OPTIONS", "0x08", "configuration"),
            ("COEXISTENCE", "0x0a", "configuration"),
            ("ON_POWER", "0x0b", "configuration"),
            ("POWER", "0x50", "control"),
            ("BRIGHTNESS", "0x51", "control"),
            ("STATIC_COLOR", "0x52", "control"),
            ("LIGHT_MODE", "0x53", "control"),
            ("EFFECT_SPEED", "0x54", "control"),
            ("EFFECT_LENGTH", "0x55", "control"),
            ("EFFECT_DIRECTION", "0x56", "control"),
            ("EFFECT_COLOR", "0x57", "control"),
            ("EFFECT_LOOP", "0x58", "control"),
            ("AUDIO_INPUT", "0x59", "control"),
            ("AUDIO_GAIN", "0x5a", "control"),
            ("EFFECT_PLAY", "0x5d", "control"),
            ("EFFECT_CCT", "0x60", "control"),
            ("STATIC_CCT", "0x61", "control"),
            ("LIGHT_TYPE", "0x6a", "configuration"),
            ("CHIP_ORDER", "0x6b", "configuration"),
        ]
        assert [
            (candidate.chunk_type, candidate.chunk_type_hex, candidate.label)
            for candidate in profile.sptech_legacy_status_chunks
        ] == [
            (1, "0x01", "settings/firmware/light type"),
            (2, "0x02", "device mode/status/settings"),
            (3, "0x03", "extended device status/settings"),
            (4, "0x04", "timer"),
            (5, "0x05", "music strip/matrix layout"),
            (6, "0x06", "network information"),
            (7, "0x07", "fun switch"),
            (10, "0x0a", "unknown firmware/status block"),
        ]
        assert describe_lan_profile(profile) == (
            "banlanx_custom_5xx; manual_host; command_protocol_pending; "
            "network_info=37; max_data_length=185; discovery_plugins=5; "
            "network_setup_routes=1; network_setup_prompts=7; "
            "cloud_setup_prompts=2; bonsoir_nsd_methods=5; "
            "bonsoir_events=10; service_fields=7; service_normalization=5; "
            "service_type_flow=6; txt_query_flow=6; raw_socket_hints=8; "
            "discovery_status=3; discovery_gaps=4; "
            "mdns=224.0.0.251:5353; spnet=udp/6454; "
            "sptech_candidate=tcp/8587; sptech_legacy_codes=6; "
            "sptech_legacy_configs=16; sptech_legacy_commands=20; "
            "sptech_legacy_chunks=8"
        )

    assert sptech_legacy_model_name_for_code(0x63) == "SP548E"
    assert sptech_legacy_model_name_for_code(0x00) is None


def test_sp541e_lan_profile_preserves_live_spnet_evidence() -> None:
    """SP541E LAN diagnostics expose recovered SPNet and SPTECH anchors."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP541E")
    assert model is not None

    profile = lan_profile_for_model(model)

    assert profile is not None
    assert profile.family.value == "banlanx_custom_5xx"
    assert profile.network_info_code is None
    assert profile.max_data_length == 185
    assert profile.command_protocol_known is True
    assert profile.discovery_confirmed is True
    assert profile.requires_manual_host is False
    assert profile.spnet_discovery_known is True
    assert profile.spnet_udp_port == 6454
    assert profile.spnet_discovery_request.hex() == (
        "53704e65740000200000000002e0"
    )
    assert profile.spnet_response_prefix.hex() == (
        "53704e6574000021000000000001"
    )
    assert profile.spnet_evidence == (
        (
            "BanlanX 3.3.1 arm64 libapp.so UDP constants include SpNet, "
            "wifiBroadcast, and discovery payload bytes 02e0"
        ),
        "Official BanlanX app opens UDP/6454 while listing nearby SP541E devices",
        (
            "Live SP541E network page reports Wi-Fi (Infra) connected and "
            "cloud available"
        ),
        (
            "Live Home Assistant host SPNet discovery returned source host, "
            "model byte 0x5c, network MAC, and SP541E name"
        ),
    )
    assert profile.sptech_tcp_port == 8587
    assert profile.sptech_magic == b"SPTECH\x00"
    assert profile.sptech_status_query.hex() == "53505445434800020000000000"
    assert profile.sptech_response_header_bytes == 13
    assert profile.sptech_candidate_evidence == (
        "Live SP541E hosts expose TCP/8587",
        (
            "Legacy/adapted UniLED evidence proves SPTECH framing; direct "
            "read-only probes can return zero bytes while another controller "
            "session owns the socket"
        ),
    )
    assert len(profile.sptech_legacy_model_codes) == 6
    assert len(profile.sptech_legacy_configuration_codes) == 16
    assert len(profile.sptech_legacy_command_ids) == 20
    assert len(profile.sptech_legacy_status_chunks) == 8
    assert profile.sptech_legacy_model_code_evidence == (
        (
            "Old UniLED dev_v3 and 3.0.10-beta.11 map SP530E to "
            "SPTech LAN code 0x4e"
        ),
        (
            "Old UniLED dev_v3 and 3.0.10-beta.11 map "
            "SP538E/SP548E/SP539E/SP549E to SPTech LAN model codes"
        ),
        (
            "The old mapping proves recognition/configuration hints only; "
            "non-SP541E LAN writes remain disabled until response frames are "
            "proven"
        ),
    )
    assert describe_lan_profile(profile) == (
        "banlanx_custom_5xx; discovery_ready; command_protocol_known; "
        "max_data_length=185; discovery_plugins=5; network_setup_routes=1; "
        "network_setup_prompts=7; cloud_setup_prompts=2; "
        "bonsoir_nsd_methods=5; bonsoir_events=10; service_fields=7; "
        "service_normalization=5; service_type_flow=6; txt_query_flow=6; "
        "raw_socket_hints=8; discovery_status=3; discovery_gaps=4; "
        "mdns=224.0.0.251:5353; spnet=udp/6454; "
        "sptech_candidate=tcp/8587; sptech_legacy_codes=6; "
        "sptech_legacy_configs=16; sptech_legacy_commands=20; "
        "sptech_legacy_chunks=8"
    )


def test_spnet_discovery_request_and_response_parser() -> None:
    """The SPNet discovery parser accepts only the recovered response prefix."""
    assert build_spnet_discovery_request().hex() == (
        "53704e65740000200000000002e0"
    )

    live_responses = (
        (
            "192.168.0.82",
            "53704e65740000210000000000010000105c00542024111f77075350353431450000",
            "54:20:24:11:1F:77",
        ),
        (
            "192.168.0.160",
            "53704e65740000210000000000010000105c0056202406d6ee075350353431450000",
            "56:20:24:06:D6:EE",
        ),
        (
            "192.168.0.99",
            "53704e65740000210000000000010000105c0056202406d9d6075350353431450000",
            "56:20:24:06:D9:D6",
        ),
    )
    for source, response_hex, mac_address in live_responses:
        response = bytes.fromhex(response_hex)
        parsed = parse_spnet_discovery_response(response, source=source)

        assert parsed is not None
        assert parsed.source == source
        assert parsed.raw == response
        assert parsed.payload.startswith(bytes.fromhex("0000105c00"))
        assert parsed.model_id == 0x5C
        assert parsed.mac_address == mac_address
        assert parsed.device_name == "SP541E"
    assert parse_spnet_discovery_response(b"not-spnet") is None


def test_network_family_lan_profiles_remain_protocol_pending() -> None:
    """SP801E/SP802E are LAN-capable but not command-protocol backed yet."""
    catalog = default_catalog()

    sp802 = catalog.resolve_name("SP802E")
    assert sp802 is not None
    sp802_profile = lan_profile_for_model(sp802)

    assert sp802_profile is not None
    assert sp802_profile.family.value == "banlanx_network"
    assert sp802_profile.network_info_code == 9
    assert sp802_profile.max_data_length is None
    assert sp802_profile.command_protocol_known is False
    assert sp802_profile.requires_manual_host is True
    assert sp802_profile.network_setup_guide_assets == ()
    assert sp802_profile.sptech_legacy_model_codes == ()
    assert sp802_profile.sptech_legacy_configuration_codes == ()
    assert sp802_profile.sptech_legacy_command_ids == ()
    assert sp802_profile.sptech_legacy_status_chunks == ()

    sp801 = catalog.resolve_name("SP801E")
    assert sp801 is not None
    sp801_profile = lan_profile_for_model(sp801)

    assert sp801_profile is not None
    assert sp801_profile.family.value == "banlanx_network"
    assert sp801_profile.network_info_code is None
    assert sp801_profile.max_data_length is None
    assert sp801_profile.network_setup_guide_assets == (
        "packages/module_home/assets/images/net_config_guide/sp801e_init.png",
        "packages/module_home/assets/images/net_config_guide/sp801e_ble.png",
        "packages/module_home/assets/images/net_config_guide/sp801e_ap.png",
    )
    assert sp801_profile.sptech_legacy_model_codes == ()
    assert sp801_profile.sptech_legacy_configuration_codes == ()
    assert sp801_profile.sptech_legacy_command_ids == ()
    assert sp801_profile.sptech_legacy_status_chunks == ()
    assert describe_lan_profile(sp801_profile) == (
        "banlanx_network; manual_host; command_protocol_pending; "
        "discovery_plugins=5; network_setup_routes=1; "
        "network_setup_guides=3; network_setup_prompts=7; "
        "cloud_setup_prompts=2; bonsoir_nsd_methods=5; "
        "bonsoir_events=10; service_fields=7; service_normalization=5; "
        "service_type_flow=6; txt_query_flow=6; raw_socket_hints=8; "
        "discovery_status=3; discovery_gaps=4; mdns=224.0.0.251:5353"
    )


def test_lan_profiles_track_apk_host_network_methods() -> None:
    """The profile records host network facts the APK asks Android for."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP802E")
    assert model is not None

    profile = lan_profile_for_model(model)

    assert profile is not None
    assert profile.host_network_methods == (
        "wifiBroadcast",
        "wifiGatewayAddress",
        "wifiState",
        "wifiIPAddress",
        "wifiIPv6Address",
        "wifiName",
        "wifiBSSID",
        "wifiSubmask",
    )
    assert profile.apk_discovery_hints == (
        "network_info_plus",
        "multicast_lock",
        "bonsoir",
        "android_nsd",
        "raw_datagram_socket",
    )
    assert profile.apk_discovery_channels == (
        "dev.fluttercommunity.plus/network_info",
        "com.spled.plugins/multicast_lock",
        "bonsoir",
    )
    assert profile.network_setup_route_hints == (
        "/device/universal/network/config",
    )
    assert profile.network_setup_prompts == (
        "Configure device network",
        "Device network status",
        "Please connect your phone to an available network first",
        (
            'Press the device\'s "AP/STA" button more than 5 seconds until '
            "the green indicator light flashes, than the device enters the "
            "network configuration state (via Bluetooth)."
        ),
        (
            'Short press the device\'s "AP/STA" button, when the blue '
            "indicator light on, than the device enters the network "
            "configuration state (via AP).2"
        ),
        "The device has not been connected to a network yet",
        "Unavailable network, some features will be limited.",
    )
    assert profile.network_cloud_setup_prompts == (
        (
            "The controller is not bound to your account. To enable cloud or "
            "voice assistant control, please reconfigure the device to the "
            "network"
        ),
        (
            "You are not signed in. After setup, the device can only be "
            "controlled within the local network and not via cloud access or "
            "voice assistant"
        ),
    )
    assert profile.multicast_lock_methods == (
        "acquire_multicast_lock",
        "release_multicast_lock",
        "held_multicast_lock",
    )
    assert profile.bonsoir_methods == (
        "broadcast.initialize",
        "broadcast.start",
        "broadcast.stop",
        "discovery.initialize",
        "discovery.start",
        "discovery.stop",
    )
    assert profile.bonsoir_arguments == (
        "service.name",
        "service.type",
        "service.port",
        "service.host",
        "service.attributes",
    )
    assert profile.bonsoir_nsd_methods == (
        "NsdManager.discoverServices",
        "NsdManager.resolveService",
        "NsdManager.registerService",
        "NsdManager.stopServiceDiscovery",
        "NsdManager.unregisterService",
    )
    assert profile.bonsoir_discovery_events == (
        "discoveryStarted",
        "discoveryServiceFound",
        "discoveryServiceResolved",
        "discoveryServiceResolveFailed",
        "discoveryServiceLost",
        "discoveryStopped",
        "discoveryUndiscoveredServiceResolveFailed",
        "discoveryTxtResolved",
        "discoveryTxtResolveFailed",
        "discoveryError",
    )
    assert profile.bonsoir_service_event_fields == (
        "id",
        "service",
        "service.name",
        "service.type",
        "service.port",
        "service.host",
        "service.attributes",
    )
    assert profile.bonsoir_service_normalization_hints == (
        (
            "Trailing-dot Android NSD service types are trimmed before "
            "lookup/emission"
        ),
        "Resolved host values are emitted as getHostAddress() strings when present",
        "NSD TXT byte values are decoded as UTF-8 strings",
        "Null TXT values are normalized to empty strings",
        "Android NSD resolveService calls are serialized through a plugin queue",
    )
    assert profile.bonsoir_service_type_flow_hints == (
        "discovery.initialize stores the Dart session type as the NSD service type",
        "discovery.start passes that service type to NsdManager.discoverServices",
        (
            "discovery.resolveService rebuilds NsdServiceInfo from service "
            "name and type"
        ),
        "broadcast.initialize stores service.type for NSD registration",
        (
            "broadcast.start sets service.type, port, host, and TXT attributes "
            "before registerService"
        ),
        (
            "onServiceFound normalizes trailing-dot service types and extracts "
            "TXT attributes"
        ),
    )
    assert profile.bonsoir_txt_query_flow_hints == (
        "discoveryServiceFound schedules a secondary mDNS TXT query for the service",
        "TXT query name is encoded as service.name, service.type, and local",
        "TXT query uses DNS record type 16",
        (
            "TXT query class is 32769, matching IN plus the mDNS "
            "unicast-response bit"
        ),
        "TXT query retries using local port 5353 after an ephemeral-port timeout",
        "TXT parser updates service attributes and emits lost/found events on change",
    )
    assert profile.discovery_gap_hints == (
        (
            "Decompiled Bonsoir plugin shows service type is supplied by "
            "Dart, but the concrete BanlanX DNS-SD service type was not "
            "recovered"
        ),
        (
            "Blutter/static string searches found multicast/raw datagram "
            "anchors but no concrete _tcp/_udp DNS-SD service type"
        ),
        "No model-specific TXT attribute schema or discovery response was recovered",
        (
            "RawDatagramSocket and DatagramSocket evidence is generic plumbing, "
            "not a command frame"
        ),
    )
    assert profile.raw_socket_hints == (
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
    )
    assert profile.discovery_status_hints == (
        "delay stop discovery>>>>>>>",
        "reported data:",
        "unresolved discovery response from",
    )
    assert profile.mdns_multicast_group == "224.0.0.251"
    assert profile.mdns_port == 5353
    assert profile.mdns_ttl == 255
    assert profile.mdns_txt_query_timeout_ms == 2000
    assert profile.mdns_txt_record_type == 16
    assert profile.mdns_txt_query_class == 32769
    assert profile.udp_socket_timeout_ms == 8000
    assert profile.udp_receive_buffer_bytes == 2000
    assert profile.mdns_txt_buffer_bytes == 1024


def test_ble_only_models_do_not_claim_lan_profiles() -> None:
    """BLE-only models do not expose LAN profile facts."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP630E")
    assert model is not None

    assert lan_profile_for_model(model) is None
    assert describe_lan_profile(None) is None
    assert not plan_for_model(model).has_feature("lan_profile")


def test_lan_capable_models_get_lan_profile_diagnostics() -> None:
    """Every LAN-capable setup path exposes the profile as diagnostics."""
    catalog = default_catalog()

    for name in ("SP547E", "SP801E", "SP802E", "FT001"):
        model = catalog.resolve_name(name)
        assert model is not None

        feature = plan_for_model(model).feature("lan_profile")

        assert feature.implemented is True
        assert feature.key == "lan_profile"
        host_mode = plan_for_model(model).feature("lan_host_setup_mode")
        assert host_mode.platform is PlatformKind.SENSOR
        assert host_mode.entity_category is EntityCategoryKind.DIAGNOSTIC
        assert host_mode.implemented is True
        assert host_mode.unit is None

        for key, unit in {
            "lan_host_network_method_count": "methods",
            "lan_discovery_plugin_count": "plugins",
            "lan_discovery_channel_count": "channels",
            "lan_network_setup_route_count": "routes",
            "lan_network_setup_prompt_count": "prompts",
            "lan_network_cloud_setup_prompt_count": "prompts",
            "lan_multicast_lock_method_count": "methods",
            "lan_bonsoir_method_count": "methods",
            "lan_bonsoir_argument_count": "arguments",
            "lan_bonsoir_nsd_method_count": "methods",
            "lan_bonsoir_discovery_event_count": "events",
            "lan_bonsoir_service_event_field_count": "fields",
            "lan_bonsoir_service_normalization_hint_count": "hints",
            "lan_bonsoir_service_type_flow_hint_count": "hints",
            "lan_bonsoir_txt_query_flow_hint_count": "hints",
            "lan_discovery_gap_count": "gaps",
            "lan_raw_socket_hint_count": "hints",
            "lan_discovery_status_hint_count": "hints",
            "lan_udp_socket_timeout_ms": "ms",
            "lan_udp_receive_buffer_bytes": "bytes",
            "lan_mdns_txt_query_timeout_ms": "ms",
            "lan_mdns_txt_record_type": None,
            "lan_mdns_txt_query_class": None,
            "lan_mdns_txt_buffer_bytes": "bytes",
        }.items():
            diagnostic = plan_for_model(model).feature(key)
            assert diagnostic.platform is PlatformKind.SENSOR, (name, key)
            assert diagnostic.entity_category is EntityCategoryKind.DIAGNOSTIC, (
                name,
                key,
            )
            assert diagnostic.implemented, (name, key)
            assert diagnostic.unit == unit, (name, key)

    custom = catalog.resolve_name("SP547E")
    assert custom is not None
    custom_plan = plan_for_model(custom)
    assert (
        custom_plan.feature("lan_sptech_legacy_model_code_count").unit
        == "codes"
    )
    assert (
        custom_plan.feature("lan_sptech_legacy_configuration_code_count").unit
        == "codes"
    )
    assert (
        custom_plan.feature("lan_sptech_legacy_command_id_count").unit
        == "commands"
    )
    assert (
        custom_plan.feature("lan_sptech_legacy_status_chunk_count").unit
        == "chunks"
    )
    network = catalog.resolve_name("SP802E")
    assert network is not None
    assert not plan_for_model(network).has_feature(
        "lan_sptech_legacy_model_code_count"
    )


def test_sp801e_gets_network_setup_guide_asset_diagnostic() -> None:
    """SP801E exposes the APK setup-guide image count as a diagnostic."""
    catalog = default_catalog()
    sp801 = catalog.resolve_name("SP801E")
    sp802 = catalog.resolve_name("SP802E")
    assert sp801 is not None
    assert sp802 is not None

    guide = plan_for_model(sp801).feature("lan_network_setup_guide_asset_count")

    assert guide.platform is PlatformKind.SENSOR
    assert guide.entity_category is EntityCategoryKind.DIAGNOSTIC
    assert guide.implemented is True
    assert guide.unit == "assets"
    assert not plan_for_model(sp802).has_feature(
        "lan_network_setup_guide_asset_count"
    )
