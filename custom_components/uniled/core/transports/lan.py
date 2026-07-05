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
    return "; ".join(parts)


def build_spnet_discovery_request() -> bytes:
    """Return the SPNet UDP discovery request recovered from BanlanX."""
    return SPNET_DISCOVERY_REQUEST


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
