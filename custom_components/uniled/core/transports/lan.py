"""LAN profile facts derived from the BanlanX APK catalog and plugins."""

from __future__ import annotations

from dataclasses import dataclass

from ..catalog import CatalogModel, ProtocolFamily, TransportKind

APK_NETWORK_INFO_METHODS = (
    "wifiBroadcast",
    "wifiGatewayAddress",
    "wifiState",
    "wifiIPAddress",
    "wifiIPv6Address",
    "wifiName",
    "wifiBSSID",
    "wifiSubmask",
)

APK_DISCOVERY_HINTS = (
    "network_info_plus",
    "multicast_lock",
    "bonsoir",
    "android_nsd",
    "raw_datagram_socket",
)

APK_DISCOVERY_CHANNELS = (
    "dev.fluttercommunity.plus/network_info",
    "com.spled.plugins/multicast_lock",
    "bonsoir",
)

APK_NETWORK_SETUP_ROUTE_HINTS = ("/device/universal/network/config",)

MODULE_HOME_PACKAGE = "packages/module_home"
MODULE_HOME_PACKAGE_ASSET_COUNT = 115

SP801E_NETWORK_SETUP_GUIDE_ASSETS = (
    f"{MODULE_HOME_PACKAGE}/assets/images/net_config_guide/sp801e_init.png",
    f"{MODULE_HOME_PACKAGE}/assets/images/net_config_guide/sp801e_ble.png",
    f"{MODULE_HOME_PACKAGE}/assets/images/net_config_guide/sp801e_ap.png",
)

APK_NETWORK_SETUP_PROMPTS = (
    "Configure device network",
    "Device network status",
    "Please connect your phone to an available network first",
    (
        'Press the device\'s "AP/STA" button more than 5 seconds until the '
        "green indicator light flashes, than the device enters the network "
        "configuration state (via Bluetooth)."
    ),
    (
        'Short press the device\'s "AP/STA" button, when the blue indicator '
        "light on, than the device enters the network configuration state "
        "(via AP).2"
    ),
    "The device has not been connected to a network yet",
    "Unavailable network, some features will be limited.",
)

APK_NETWORK_CLOUD_SETUP_PROMPTS = (
    (
        "The controller is not bound to your account. To enable cloud or voice "
        "assistant control, please reconfigure the device to the network"
    ),
    (
        "You are not signed in. After setup, the device can only be controlled "
        "within the local network and not via cloud access or voice assistant"
    ),
)

APK_MULTICAST_LOCK_METHODS = (
    "acquire_multicast_lock",
    "release_multicast_lock",
    "held_multicast_lock",
)

APK_BONSOIR_METHODS = (
    "broadcast.initialize",
    "broadcast.start",
    "broadcast.stop",
    "discovery.initialize",
    "discovery.start",
    "discovery.stop",
)

APK_BONSOIR_ARGUMENTS = (
    "service.name",
    "service.type",
    "service.port",
    "service.host",
    "service.attributes",
)

APK_BONSOIR_NSD_METHODS = (
    "NsdManager.discoverServices",
    "NsdManager.resolveService",
    "NsdManager.registerService",
    "NsdManager.stopServiceDiscovery",
    "NsdManager.unregisterService",
)

APK_BONSOIR_DISCOVERY_EVENTS = (
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

APK_BONSOIR_SERVICE_EVENT_FIELDS = (
    "id",
    "service",
    "service.name",
    "service.type",
    "service.port",
    "service.host",
    "service.attributes",
)

APK_BONSOIR_SERVICE_NORMALIZATION_HINTS = (
    "Trailing-dot Android NSD service types are trimmed before lookup/emission",
    "Resolved host values are emitted as getHostAddress() strings when present",
    "NSD TXT byte values are decoded as UTF-8 strings",
    "Null TXT values are normalized to empty strings",
    "Android NSD resolveService calls are serialized through a plugin queue",
)

APK_BONSOIR_SERVICE_TYPE_FLOW_HINTS = (
    "discovery.initialize stores the Dart session type as the NSD service type",
    "discovery.start passes that service type to NsdManager.discoverServices",
    (
        "discovery.resolveService rebuilds NsdServiceInfo from service name "
        "and type"
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

APK_BONSOIR_TXT_QUERY_FLOW_HINTS = (
    "discoveryServiceFound schedules a secondary mDNS TXT query for the service",
    "TXT query name is encoded as service.name, service.type, and local",
    "TXT query uses DNS record type 16",
    "TXT query class is 32769, matching IN plus the mDNS unicast-response bit",
    "TXT query retries using local port 5353 after an ephemeral-port timeout",
    "TXT parser updates service attributes and emits lost/found events on change",
)

APK_DISCOVERY_GAP_HINTS = (
    (
        "Decompiled Bonsoir plugin shows service type is supplied by Dart, "
        "but the concrete BanlanX DNS-SD service type was not recovered"
    ),
    (
        "Blutter/static string searches found multicast/raw datagram anchors "
        "but no concrete _tcp/_udp DNS-SD service type"
    ),
    "No model-specific TXT attribute schema or discovery response was recovered",
    (
        "RawDatagramSocket and DatagramSocket evidence is generic plumbing, "
        "not a command frame"
    ),
)

APK_MDNS_MULTICAST_GROUP = "224.0.0.251"
APK_MDNS_PORT = 5353
APK_MDNS_TTL = 255
APK_MDNS_TXT_QUERY_TIMEOUT_MS = 2000
APK_MDNS_TXT_RECORD_TYPE = 16
APK_MDNS_TXT_QUERY_CLASS = 32769
APK_UDP_SOCKET_TIMEOUT_MS = 8000
APK_UDP_RECEIVE_BUFFER_BYTES = 2000
APK_MDNS_TXT_BUFFER_BYTES = 1024

APK_RAW_SOCKET_HINTS = (
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

APK_DISCOVERY_STATUS_HINTS = (
    "delay stop discovery>>>>>>>",
    "reported data:",
    "unresolved discovery response from",
)

SPNET_DISCOVERY_PORT = 6454
SPNET_DISCOVERY_REQUEST = bytes.fromhex("53704e65740000200000000002e0")
SPNET_DISCOVERY_RESPONSE_PREFIX = bytes.fromhex(
    "53704e6574000021000000000001"
)
SPNET_DISCOVERY_EVIDENCE = (
    (
        "BanlanX 3.3.1 arm64 libapp.so UDP constants include SpNet, "
        "wifiBroadcast, and discovery payload bytes 02e0"
    ),
    "Official BanlanX app opens UDP/6454 while listing nearby SP541E devices",
    "Live SP541E network page reports Wi-Fi (Infra) connected and cloud available",
    (
        "Live Home Assistant host SPNet discovery returned source host, "
        "model byte 0x5c, network MAC, and SP541E name"
    ),
)

SPTECH_TCP_PORT = 8587
SPTECH_MAGIC = b"SPTECH\x00"
SPTECH_STATUS_QUERY = bytes.fromhex("53505445434800020000000000")
SPTECH_RESPONSE_HEADER_BYTES = 13
SPTECH_CANDIDATE_EVIDENCE = (
    "Live SP541E hosts expose TCP/8587",
    (
        "Legacy/adapted UniLED evidence proves SPTECH framing; direct "
        "read-only probes can return zero bytes while another controller "
        "session owns the socket"
    ),
)


@dataclass(frozen=True, slots=True)
class SPTechLegacyModelCode:
    """Old-UniLED SPTech LAN model-code alias."""

    code: int
    model_name: str
    source: str

    @property
    def code_hex(self) -> str:
        """Return the model code as a compact hex string."""
        return f"0x{self.code:02x}"


@dataclass(frozen=True, slots=True)
class SPTechLegacyConfigurationCode:
    """Old-UniLED SPTech LAN configuration-code hint."""

    code: int
    label: str
    model_names: tuple[str, ...]
    source: str

    @property
    def code_hex(self) -> str:
        """Return the configuration code as a compact hex string."""
        return f"0x{self.code:02x}"


@dataclass(frozen=True, slots=True)
class SPTechLegacyCommandId:
    """Old-UniLED SPTech LAN command ID hint."""

    name: str
    command_id: int
    category: str
    source: str

    @property
    def command_id_hex(self) -> str:
        """Return the command ID as a compact hex string."""
        return f"0x{self.command_id:02x}"


@dataclass(frozen=True, slots=True)
class SPTechLegacyStatusChunkHint:
    """Old-UniLED SPTech LAN status chunk decoder hint."""

    chunk_type: int
    label: str
    source: str

    @property
    def chunk_type_hex(self) -> str:
        """Return the chunk type as a compact hex string."""
        return f"0x{self.chunk_type:02x}"


SPTECH_LEGACY_SOURCE = (
    "monty68/uniled origin/dev_v3 and 3.0.10-beta.11 "
    "custom_components/uniled/lib/net/sp53x_54xe.py"
)
SPTECH_LEGACY_PROTOCOL_SOURCE = (
    "monty68/uniled origin/dev_v3 and 3.0.10-beta.11 "
    "custom_components/uniled/lib/sptech_model.py"
)

SPTECH_LEGACY_MODEL_CODES = (
    SPTechLegacyModelCode(0x4E, "SP530E", SPTECH_LEGACY_SOURCE),
    SPTechLegacyModelCode(0x56, "SP538E", SPTECH_LEGACY_SOURCE),
    SPTechLegacyModelCode(0x57, "SP539E", SPTECH_LEGACY_SOURCE),
    SPTechLegacyModelCode(0x63, "SP548E", SPTECH_LEGACY_SOURCE),
    SPTechLegacyModelCode(0x64, "SP549E", SPTECH_LEGACY_SOURCE),
    SPTechLegacyModelCode(0x69, "SP548E", SPTECH_LEGACY_SOURCE),
)

SPTECH_LEGACY_CONFIGURATION_CODES = (
    SPTechLegacyConfigurationCode(
        0x06, "SPI - RGB", ("SP538E", "SP548E"), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x08, "SPI - RGBW", ("SP539E", "SP549E"), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x81, "PWM Mono", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x83, "PWM CCT", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x85, "PWM RGB", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x87, "PWM RGBW", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x8A, "PWM RGBCCT", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x82, "SPI - Mono", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x84, "SPI - CCT (1)", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x8D, "SPI - CCT (2)", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x86, "SPI - RGB", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x88, "SPI - RGBW", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x8B, "SPI - RGBCCT (1)", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x8E, "SPI - RGBCCT (2)", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x89, "SPI - RGB + 1 CH PWM", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
    SPTechLegacyConfigurationCode(
        0x8C, "SPI - RGB + 2 CH PWM", ("SP530E",), SPTECH_LEGACY_SOURCE
    ),
)

SPTECH_LEGACY_MODEL_CODE_EVIDENCE = (
    "Old UniLED dev_v3 and 3.0.10-beta.11 map SP530E to SPTech LAN code 0x4e",
    (
        "Old UniLED dev_v3 and 3.0.10-beta.11 map "
        "SP538E/SP548E/SP539E/SP549E to SPTech LAN model codes"
    ),
    (
        "The old mapping proves recognition/configuration hints only; "
        "non-SP541E LAN writes remain disabled until response frames are proven"
    ),
)

SPTECH_LEGACY_COMMAND_IDS = (
    SPTechLegacyCommandId(
        "STATUS_QUERY", 0x02, "read_only_query", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "ONOFF_OPTIONS", 0x08, "configuration", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "COEXISTENCE", 0x0A, "configuration", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "ON_POWER", 0x0B, "configuration", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "POWER", 0x50, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "BRIGHTNESS", 0x51, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "STATIC_COLOR", 0x52, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "LIGHT_MODE", 0x53, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "EFFECT_SPEED", 0x54, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "EFFECT_LENGTH", 0x55, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "EFFECT_DIRECTION", 0x56, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "EFFECT_COLOR", 0x57, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "EFFECT_LOOP", 0x58, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "AUDIO_INPUT", 0x59, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "AUDIO_GAIN", 0x5A, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "EFFECT_PLAY", 0x5D, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "EFFECT_CCT", 0x60, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "STATIC_CCT", 0x61, "control", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "LIGHT_TYPE", 0x6A, "configuration", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyCommandId(
        "CHIP_ORDER", 0x6B, "configuration", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
)

SPTECH_LEGACY_STATUS_CHUNKS = (
    SPTechLegacyStatusChunkHint(
        1, "settings/firmware/light type", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyStatusChunkHint(
        2, "device mode/status/settings", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyStatusChunkHint(
        3, "extended device status/settings", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyStatusChunkHint(4, "timer", SPTECH_LEGACY_PROTOCOL_SOURCE),
    SPTechLegacyStatusChunkHint(
        5, "music strip/matrix layout", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyStatusChunkHint(
        6, "network information", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
    SPTechLegacyStatusChunkHint(7, "fun switch", SPTECH_LEGACY_PROTOCOL_SOURCE),
    SPTechLegacyStatusChunkHint(
        10, "unknown firmware/status block", SPTECH_LEGACY_PROTOCOL_SOURCE
    ),
)

SPTECH_LEGACY_PROTOCOL_EVIDENCE = (
    (
        "Old UniLED SPTechModel encodes NET frames as SPTECH\\0, command ID, "
        "key byte, two reserved bytes, two-byte payload length, and payload"
    ),
    (
        "Old UniLED SPTechModel decodes chunked status payloads for settings, "
        "mode/status, timers, music layout, network info, and fun switch data"
    ),
    (
        "These command IDs and chunk labels are diagnostics only until each "
        "model's LAN response and write behavior is proven"
    ),
)


@dataclass(frozen=True, slots=True)
class SpNetDiscoveryResponse:
    """Parsed SPNet UDP discovery response."""

    raw: bytes
    payload: bytes
    model_id: int | None
    mac_address: str | None = None
    device_name: str | None = None
    source: str | None = None


@dataclass(frozen=True, slots=True)
class LANProfile:
    """Known LAN-side facts for one catalog model."""

    family: ProtocolFamily
    network_info_code: int | None
    max_data_length: int | None
    command_protocol_known: bool = False
    discovery_confirmed: bool = False
    host_network_methods: tuple[str, ...] = APK_NETWORK_INFO_METHODS
    apk_discovery_hints: tuple[str, ...] = APK_DISCOVERY_HINTS
    apk_discovery_channels: tuple[str, ...] = APK_DISCOVERY_CHANNELS
    network_setup_route_hints: tuple[str, ...] = APK_NETWORK_SETUP_ROUTE_HINTS
    network_setup_guide_assets: tuple[str, ...] = ()
    network_setup_prompts: tuple[str, ...] = APK_NETWORK_SETUP_PROMPTS
    network_cloud_setup_prompts: tuple[str, ...] = (
        APK_NETWORK_CLOUD_SETUP_PROMPTS
    )
    multicast_lock_methods: tuple[str, ...] = APK_MULTICAST_LOCK_METHODS
    bonsoir_methods: tuple[str, ...] = APK_BONSOIR_METHODS
    bonsoir_arguments: tuple[str, ...] = APK_BONSOIR_ARGUMENTS
    bonsoir_nsd_methods: tuple[str, ...] = APK_BONSOIR_NSD_METHODS
    bonsoir_discovery_events: tuple[
        str, ...
    ] = APK_BONSOIR_DISCOVERY_EVENTS
    bonsoir_service_event_fields: tuple[
        str, ...
    ] = APK_BONSOIR_SERVICE_EVENT_FIELDS
    bonsoir_service_normalization_hints: tuple[
        str, ...
    ] = APK_BONSOIR_SERVICE_NORMALIZATION_HINTS
    bonsoir_service_type_flow_hints: tuple[
        str, ...
    ] = APK_BONSOIR_SERVICE_TYPE_FLOW_HINTS
    bonsoir_txt_query_flow_hints: tuple[
        str, ...
    ] = APK_BONSOIR_TXT_QUERY_FLOW_HINTS
    discovery_gap_hints: tuple[str, ...] = APK_DISCOVERY_GAP_HINTS
    raw_socket_hints: tuple[str, ...] = APK_RAW_SOCKET_HINTS
    discovery_status_hints: tuple[str, ...] = APK_DISCOVERY_STATUS_HINTS
    mdns_multicast_group: str = APK_MDNS_MULTICAST_GROUP
    mdns_port: int = APK_MDNS_PORT
    mdns_ttl: int = APK_MDNS_TTL
    mdns_txt_query_timeout_ms: int = APK_MDNS_TXT_QUERY_TIMEOUT_MS
    mdns_txt_record_type: int = APK_MDNS_TXT_RECORD_TYPE
    mdns_txt_query_class: int = APK_MDNS_TXT_QUERY_CLASS
    udp_socket_timeout_ms: int = APK_UDP_SOCKET_TIMEOUT_MS
    udp_receive_buffer_bytes: int = APK_UDP_RECEIVE_BUFFER_BYTES
    mdns_txt_buffer_bytes: int = APK_MDNS_TXT_BUFFER_BYTES
    spnet_discovery_known: bool = False
    spnet_udp_port: int | None = None
    spnet_discovery_request: bytes = b""
    spnet_response_prefix: bytes = b""
    spnet_evidence: tuple[str, ...] = ()
    sptech_tcp_port: int | None = None
    sptech_magic: bytes = b""
    sptech_status_query: bytes = b""
    sptech_response_header_bytes: int | None = None
    sptech_candidate_evidence: tuple[str, ...] = ()
    sptech_legacy_model_codes: tuple[SPTechLegacyModelCode, ...] = ()
    sptech_legacy_configuration_codes: tuple[
        SPTechLegacyConfigurationCode, ...
    ] = ()
    sptech_legacy_model_code_evidence: tuple[str, ...] = ()
    sptech_legacy_command_ids: tuple[SPTechLegacyCommandId, ...] = ()
    sptech_legacy_status_chunks: tuple[SPTechLegacyStatusChunkHint, ...] = ()
    sptech_legacy_protocol_evidence: tuple[str, ...] = ()

    @property
    def requires_manual_host(self) -> bool:
        """Return whether setup should ask for a host/IP for now."""
        return not self.discovery_confirmed


def lan_profile_for_model(model: CatalogModel) -> LANProfile | None:
    """Return APK/catalog LAN facts for a model, if it has LAN capability."""
    if TransportKind.LAN not in model.transports:
        return None

    network_info_code = _optional_int(model.features.get("supportGetNetInfo"))
    max_data_length = _optional_int(model.features.get("maxDataLength"))
    setup_guide_assets = (
        SP801E_NETWORK_SETUP_GUIDE_ASSETS if model.name == "SP801E" else ()
    )
    spnet_kwargs = {}
    if model.family is ProtocolFamily.BANLANX_CUSTOM_5XX:
        spnet_kwargs = {
            "spnet_discovery_known": True,
            "spnet_udp_port": SPNET_DISCOVERY_PORT,
            "spnet_discovery_request": SPNET_DISCOVERY_REQUEST,
            "spnet_response_prefix": SPNET_DISCOVERY_RESPONSE_PREFIX,
            "spnet_evidence": SPNET_DISCOVERY_EVIDENCE,
            "sptech_tcp_port": SPTECH_TCP_PORT,
            "sptech_magic": SPTECH_MAGIC,
            "sptech_status_query": SPTECH_STATUS_QUERY,
            "sptech_response_header_bytes": SPTECH_RESPONSE_HEADER_BYTES,
            "sptech_candidate_evidence": SPTECH_CANDIDATE_EVIDENCE,
            "sptech_legacy_model_codes": SPTECH_LEGACY_MODEL_CODES,
            "sptech_legacy_configuration_codes": (
                SPTECH_LEGACY_CONFIGURATION_CODES
            ),
            "sptech_legacy_model_code_evidence": (
                SPTECH_LEGACY_MODEL_CODE_EVIDENCE
            ),
            "sptech_legacy_command_ids": SPTECH_LEGACY_COMMAND_IDS,
            "sptech_legacy_status_chunks": SPTECH_LEGACY_STATUS_CHUNKS,
            "sptech_legacy_protocol_evidence": (
                SPTECH_LEGACY_PROTOCOL_EVIDENCE
            ),
        }
    is_verified_sp541e = model.name == "SP541E"

    return LANProfile(
        family=model.family,
        network_info_code=network_info_code,
        max_data_length=max_data_length,
        command_protocol_known=is_verified_sp541e,
        discovery_confirmed=is_verified_sp541e,
        network_setup_guide_assets=setup_guide_assets,
        **spnet_kwargs,
    )


def describe_lan_profile(profile: LANProfile | None) -> str | None:
    """Return a compact diagnostic string for a LAN profile."""
    if profile is None:
        return None

    parts = [
        profile.family.value,
        "manual_host" if profile.requires_manual_host else "discovery_ready",
        "command_protocol_known"
        if profile.command_protocol_known
        else "command_protocol_pending",
    ]
    if profile.network_info_code is not None:
        parts.append(f"network_info={profile.network_info_code}")
    if profile.max_data_length is not None:
        parts.append(f"max_data_length={profile.max_data_length}")
    parts.append(f"discovery_plugins={len(profile.apk_discovery_hints)}")
    parts.append(
        f"network_setup_routes={len(profile.network_setup_route_hints)}"
    )
    if profile.network_setup_guide_assets:
        parts.append(
            f"network_setup_guides={len(profile.network_setup_guide_assets)}"
    )
    parts.append(f"network_setup_prompts={len(profile.network_setup_prompts)}")
    parts.append(
        f"cloud_setup_prompts={len(profile.network_cloud_setup_prompts)}"
    )
    parts.append(f"bonsoir_nsd_methods={len(profile.bonsoir_nsd_methods)}")
    parts.append(f"bonsoir_events={len(profile.bonsoir_discovery_events)}")
    parts.append(
        f"service_fields={len(profile.bonsoir_service_event_fields)}"
    )
    parts.append(
        "service_normalization="
        f"{len(profile.bonsoir_service_normalization_hints)}"
    )
    parts.append(
        "service_type_flow="
        f"{len(profile.bonsoir_service_type_flow_hints)}"
    )
    parts.append(
        f"txt_query_flow={len(profile.bonsoir_txt_query_flow_hints)}"
    )
    parts.append(f"raw_socket_hints={len(profile.raw_socket_hints)}")
    parts.append(f"discovery_status={len(profile.discovery_status_hints)}")
    parts.append(f"discovery_gaps={len(profile.discovery_gap_hints)}")
    parts.append(f"mdns={profile.mdns_multicast_group}:{profile.mdns_port}")
    if profile.spnet_discovery_known and profile.spnet_udp_port is not None:
        parts.append(f"spnet=udp/{profile.spnet_udp_port}")
    if profile.sptech_tcp_port is not None:
        parts.append(f"sptech_candidate=tcp/{profile.sptech_tcp_port}")
    if profile.sptech_legacy_model_codes:
        parts.append(
            f"sptech_legacy_codes={len(profile.sptech_legacy_model_codes)}"
        )
    if profile.sptech_legacy_configuration_codes:
        parts.append(
            "sptech_legacy_configs="
            f"{len(profile.sptech_legacy_configuration_codes)}"
        )
    if profile.sptech_legacy_command_ids:
        parts.append(
            f"sptech_legacy_commands={len(profile.sptech_legacy_command_ids)}"
        )
    if profile.sptech_legacy_status_chunks:
        parts.append(
            f"sptech_legacy_chunks={len(profile.sptech_legacy_status_chunks)}"
        )
    return "; ".join(parts)


def build_spnet_discovery_request() -> bytes:
    """Return the SPNet UDP discovery request recovered from BanlanX."""
    return SPNET_DISCOVERY_REQUEST


def sptech_legacy_model_name_for_code(code: int) -> str | None:
    """Return an old-UniLED SPTech model name for a LAN model code."""
    for candidate in SPTECH_LEGACY_MODEL_CODES:
        if candidate.code == code:
            return candidate.model_name
    return None


def parse_spnet_discovery_response(
    data: bytes, *, source: str | None = None
) -> SpNetDiscoveryResponse | None:
    """Parse a SPNet discovery response, returning None for unrelated packets."""
    packet = bytes(data)
    if not packet.startswith(SPNET_DISCOVERY_RESPONSE_PREFIX):
        return None

    payload = packet[len(SPNET_DISCOVERY_RESPONSE_PREFIX) :]
    model_id = _spnet_model_id(payload)
    return SpNetDiscoveryResponse(
        raw=packet,
        payload=payload,
        model_id=model_id,
        mac_address=_spnet_mac_address(payload),
        device_name=_spnet_device_name(payload),
        source=source,
    )


def _spnet_model_id(payload: bytes) -> int | None:
    if len(payload) >= 4 and payload[3]:
        return payload[3]
    if payload and payload[0]:
        return payload[0]
    return None


def _spnet_mac_address(payload: bytes) -> str | None:
    if len(payload) < 11:
        return None
    mac = payload[5:11]
    if not any(mac):
        return None
    return ":".join(f"{part:02X}" for part in mac)


def _spnet_device_name(payload: bytes) -> str | None:
    if len(payload) < 13:
        return None
    name_length = payload[11]
    if name_length <= 0:
        return None
    raw_name = payload[12 : 12 + name_length].rstrip(b"\x00")
    if not raw_name:
        return None
    try:
        return raw_name.decode("ascii").strip() or None
    except UnicodeDecodeError:
        return None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
