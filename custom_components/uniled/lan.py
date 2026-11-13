"""Home Assistant LAN transports for UniLED."""

from __future__ import annotations

import asyncio
import contextlib
import ipaddress
import logging
import re
import socket
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .const import (
    CONF_DEVICE_ID,
    CONF_DISCOVERY_RESPONSE_HEX,
    CONF_HOST,
    CONF_MODEL,
    CONF_MODEL_ID,
    CONF_TRANSPORT,
    DOMAIN,
    TRANSPORT_LAN,
)
from .core import ModelCatalog, TransportError, default_catalog
from .core.protocols import SPTECH_MAGIC, SPTECH_RESPONSE_HEADER_BYTES
from .core.transports import (
    LANProfile,
    build_spnet_discovery_request,
    parse_spnet_discovery_response,
)
from .core.transports.lan import SPNET_DISCOVERY_PORT
from .setup_data import (
    SetupDataError,
    lan_setup_entry_data_from_spnet_response,
    migrate_legacy_entry_data,
)

_LOGGER = logging.getLogger(__name__)
_DEFAULT_TIMEOUT = 5.0
_ERROR_BACKOFF = 0.3
_SPNET_DISCOVERY_TASK = "spnet_discovery_task"
_SPNET_DISCOVERY_TIMEOUT = 2.0
_SPNET_BROADCAST_ADDRESSES = ("255.255.255.255",)
_RELOADABLE_DISCOVERY_STATES = {"loaded", "setup_retry", "setup_in_progress"}
_MAC_PATTERN = re.compile(
    r"(?:[0-9a-f]{12}|[0-9a-f]{2}([:-])(?:[0-9a-f]{2}\1){4}[0-9a-f]{2})"
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
else:
    HomeAssistant = Any


@dataclass(frozen=True, slots=True)
class SpNetLANDiscovery:
    """One verified SPNet LAN discovery response."""

    response: bytes
    host: str
    port: int


DiscoveryFunction = Callable[[], Awaitable[tuple[SpNetLANDiscovery, ...]]]


class UniLEDLANTransport:
    """Async TCP transport for SPTech-backed LAN UniLED entries."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        host: str,
        name: str,
        profile: LANProfile,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the LAN transport."""
        self._hass = hass
        self.host = host
        self.name = name
        self.profile = profile
        self.port = profile.sptech_tcp_port
        self.timeout = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self.closed = False

    async def close(self) -> None:
        """Close the active TCP connection."""
        self.closed = True
        await self._close_stream()

    @property
    def supports_sptech(self) -> bool:
        """Return whether this LAN profile has a mapped SPTech command path."""
        return (
            self.profile.command_protocol_known
            and self.port is not None
            and self.profile.sptech_magic == SPTECH_MAGIC
        )

    async def send(self, payload: bytes, *, response: bool = False) -> bytes | None:
        """Send one SPTech LAN payload and optionally return its response frame."""
        if not self.supports_sptech or self.port is None:
            raise TransportError(
                f"{self.name} LAN command protocol is not mapped; "
                "refusing to send guessed payloads"
            )
        if not payload.startswith(SPTECH_MAGIC):
            raise TransportError(f"{self.name} refused non-SPTech LAN payload")

        async with self._lock:
            last_error: Exception | None = None
            for attempt in range(2):
                try:
                    await self._connect_if_needed()
                    assert self._writer is not None
                    self._writer.write(payload)
                    await asyncio.wait_for(
                        self._writer.drain(),
                        timeout=self.timeout,
                    )
                    _LOGGER.debug(
                        "%s => %s (%d)",
                        self.name,
                        payload.hex(),
                        len(payload),
                    )
                    if not response:
                        return None
                    return await self._read_sptech_response()
                except (OSError, TimeoutError, asyncio.IncompleteReadError) as ex:
                    last_error = ex
                    await self._close_stream()
                    if attempt == 0:
                        await asyncio.sleep(_ERROR_BACKOFF)

            raise TransportError(f"{self.name} LAN communication failed: {last_error}")

    async def _connect_if_needed(self) -> None:
        if self._writer is not None and not self._writer.is_closing():
            return
        if self.port is None:
            raise TransportError(f"{self.name} has no LAN TCP port")
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
        except (OSError, TimeoutError) as ex:
            raise TransportError(
                f"{self.name} could not connect to {self.host}:{self.port}: {ex}"
            ) from ex
        _LOGGER.debug("%s connected to %s:%s", self.name, self.host, self.port)

    async def _read_sptech_response(self) -> bytes:
        reader = self._reader
        if reader is None:
            raise TransportError(f"{self.name} has no LAN reader")
        header = await asyncio.wait_for(
            reader.readexactly(SPTECH_RESPONSE_HEADER_BYTES),
            timeout=self.timeout,
        )
        if not header.startswith(SPTECH_MAGIC):
            raise TransportError(
                f"{self.name} invalid SPTech response header: {header.hex()}"
            )
        payload_length = int.from_bytes(header[11:13], "big")
        payload = b""
        if payload_length:
            payload = await asyncio.wait_for(
                reader.readexactly(payload_length),
                timeout=self.timeout,
            )
        response = header + payload
        _LOGGER.debug(
            "%s <= %s (%d)",
            self.name,
            response.hex(),
            len(response),
        )
        return response

    async def _close_stream(self) -> None:
        writer = self._writer
        self._reader = None
        self._writer = None
        if writer is None:
            return
        writer.close()
        with contextlib.suppress(OSError, TimeoutError):
            await asyncio.wait_for(writer.wait_closed(), timeout=1.0)
        _LOGGER.debug("%s LAN socket closed", self.name)


def lan_device_name(model_name: str, host: str) -> str:
    """Return a stable name for LAN logs and diagnostics."""
    return f"{DOMAIN}:{model_name}:{host}"


def async_start_spnet_discovery(
    hass: HomeAssistant,
    *,
    discovery_func: DiscoveryFunction | None = None,
    discover_new: bool = True,
) -> asyncio.Task[Any]:
    """Start one background SPNet LAN discovery pass."""
    data = hass.data.setdefault(DOMAIN, {})
    task = data.get(_SPNET_DISCOVERY_TASK)
    if task is not None and not task.done():
        return task

    if discovery_func is None:

        async def default_discovery_func() -> tuple[SpNetLANDiscovery, ...]:
            return await async_discover_spnet_devices(hass=hass)

        discovery_func = default_discovery_func

    task = hass.async_create_task(
        _async_handle_spnet_discovery(hass, discovery_func, discover_new=discover_new)
    )
    data[_SPNET_DISCOVERY_TASK] = task
    task.add_done_callback(lambda done: _spnet_discovery_done(hass, done))
    return task


async def async_discover_spnet_devices(
    *,
    hass: HomeAssistant | None = None,
    scan_window: float = _SPNET_DISCOVERY_TIMEOUT,
    broadcast_addresses: tuple[str, ...] | None = None,
) -> tuple[SpNetLANDiscovery, ...]:
    """Broadcast the SPNet discovery packet and collect verified responses."""
    loop = asyncio.get_running_loop()
    results: list[SpNetLANDiscovery] = []
    seen: set[tuple[str, bytes]] = set()
    protocol = _SPNetDiscoveryProtocol(results, seen)
    # Some controllers send replies to the fixed SPNet port.
    for source_port in (SPNET_DISCOVERY_PORT, 0):
        try:
            transport, _ = await loop.create_datagram_endpoint(
                lambda: protocol,
                local_addr=("0.0.0.0", source_port),
                allow_broadcast=True,
            )
            break
        except OSError as ex:
            _LOGGER.debug("SPNet discovery could not bind port %s: %s", source_port, ex)
    else:
        return ()

    try:
        request = build_spnet_discovery_request()
        if broadcast_addresses is None:
            local_addresses = await _async_local_ipv4_addresses(hass)
            broadcast_addresses = spnet_broadcast_addresses(local_addresses)
        for address in broadcast_addresses:
            try:
                transport.sendto(request, (address, SPNET_DISCOVERY_PORT))
            except OSError as ex:
                _LOGGER.debug(
                    "SPNet LAN discovery broadcast to %s failed: %s",
                    address,
                    ex,
                )
        await asyncio.sleep(scan_window)
    finally:
        transport.close()
    return tuple(results)


def spnet_discovery_flow_data(discovery: SpNetLANDiscovery) -> dict[str, str]:
    """Return config-flow discovery data for one SPNet response."""
    return {
        CONF_HOST: discovery.host,
        CONF_DISCOVERY_RESPONSE_HEX: discovery.response.hex(),
    }


def spnet_broadcast_addresses(
    local_addresses: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    """Return conservative broadcast targets for SPNet discovery."""
    addresses = list(_SPNET_BROADCAST_ADDRESSES)
    for local_address in local_addresses or _local_ipv4_addresses():
        try:
            address = ipaddress.ip_address(str(local_address).strip())
        except ValueError:
            continue
        if address.version != 4 or not (
            address.is_private or address.is_link_local
        ):
            continue
        if address.is_loopback or address.is_unspecified or address.is_multicast:
            continue
        broadcast = str(
            ipaddress.ip_network(f"{address}/24", strict=False).broadcast_address
        )
        if broadcast not in addresses:
            addresses.append(broadcast)
    return tuple(addresses)


async def _async_handle_spnet_discovery(
    hass: HomeAssistant,
    discovery_func: DiscoveryFunction,
    *,
    discover_new: bool = True,
) -> None:
    # Collect the entire scan before trusting an address, in case two replies disagree.
    observations: list[tuple[SpNetLANDiscovery, str | None]] = []
    devices_by_mac: dict[str, set[tuple[str, int | None]]] = defaultdict(set)
    macs_by_host: dict[str, set[str]] = defaultdict(set)
    for discovery in await discovery_func():
        parsed = parse_spnet_discovery_response(
            discovery.response, source=discovery.host
        )
        if parsed is None:
            continue
        mac = _lan_mac(parsed.mac_address)
        observations.append((discovery, mac))
        if mac is not None:
            devices_by_mac[mac].add((discovery.host, parsed.model_id))
            macs_by_host[discovery.host].add(mac)

    if not observations:
        return

    catalog = await hass.async_add_executor_job(default_catalog)
    entries_by_mac: dict[str, list[tuple[ConfigEntry, set[str]]]] = defaultdict(list)
    for entry in hass.config_entries.async_entries(DOMAIN):
        if (
            entry.data.get(CONF_TRANSPORT) not in {TRANSPORT_LAN, "net"}
            and entry.source != "ignore"
        ):
            continue
        identities = {
            mac
            for value in (entry.unique_id, entry.data.get(CONF_DEVICE_ID))
            if (mac := _lan_mac(value)) is not None
        }
        for mac in identities:
            entries_by_mac[mac].append((entry, identities))

    new_devices: list[SpNetLANDiscovery] = []
    seen: set[tuple[str, str | None]] = set()
    for discovery, mac in observations:
        host = discovery.host
        if (host, mac) in seen:
            continue
        seen.add((host, mac))
        if mac is None:
            if discover_new and host not in macs_by_host:
                new_devices.append(discovery)
            continue
        if len(devices_by_mac[mac]) != 1 or len(macs_by_host[host]) != 1:
            _LOGGER.debug("Skipping ambiguous SPNet discovery for %s at %s", mac, host)
            continue

        matching_entries = entries_by_mac.get(mac, [])
        if not matching_entries:
            if discover_new:
                new_devices.append(discovery)
            continue
        if len(matching_entries) != 1:
            continue
        entry, identities = matching_entries[0]
        if (
            len(identities) != 1
            or entry.disabled_by is not None
            or entry.source == "ignore"
        ):
            continue

        _async_update_discovered_host(hass, catalog, entry, discovery)

    for discovery in new_devices:
        try:
            await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "discovery"},
                data=spnet_discovery_flow_data(discovery),
            )
        except Exception:  # noqa: BLE001
            _LOGGER.exception(
                "SPNet LAN discovery flow handoff failed for %s",
                discovery.host,
            )


def _async_update_discovered_host(
    hass: HomeAssistant,
    catalog: ModelCatalog,
    entry: ConfigEntry,
    discovery: SpNetLANDiscovery,
) -> None:
    host = discovery.host
    try:
        configured = migrate_legacy_entry_data(catalog, entry.data)
        old_host = configured[CONF_HOST]
        if host == old_host:
            return
        # Keep manually configured DNS names and update numeric IPv4 hosts.
        ipaddress.IPv4Address(old_host)
        ipaddress.IPv4Address(host)
        setup = lan_setup_entry_data_from_spnet_response(
            catalog, discovery.response, source=host
        )
    except (ipaddress.AddressValueError, SetupDataError):
        return
    if (
        configured[CONF_MODEL] != setup.data[CONF_MODEL]
        or configured[CONF_MODEL_ID] != setup.data[CONF_MODEL_ID]
    ):
        return
    if not hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_HOST: host}
    ):
        return
    _LOGGER.info("Updated %s LAN address from %s to %s", entry.title, old_host, host)
    if entry.state.value in _RELOADABLE_DISCOVERY_STATES:
        hass.config_entries.async_schedule_reload(entry.entry_id)


def _lan_mac(value: object) -> str | None:
    """Normalize a LAN controller MAC from SPNet or a stored entry ID."""
    if not isinstance(value, str):
        return None
    value = value.strip().lower().removeprefix("lan:")
    if not _MAC_PATTERN.fullmatch(value):
        return None
    mac = value.replace(":", "").replace("-", "")
    if mac == "000000000000" or int(mac[:2], 16) & 1:
        return None
    return mac


def _spnet_discovery_done(
    hass: HomeAssistant,
    task: asyncio.Task[Any],
) -> None:
    data = hass.data.get(DOMAIN, {})
    if data.get(_SPNET_DISCOVERY_TASK) is task:
        data.pop(_SPNET_DISCOVERY_TASK, None)
    try:
        task.result()
    except asyncio.CancelledError:
        return
    except Exception:  # noqa: BLE001
        _LOGGER.exception("SPNet LAN discovery failed")


class _SPNetDiscoveryProtocol(asyncio.DatagramProtocol):
    """Collect only packets matching the recovered SPNet response prefix."""

    def __init__(
        self,
        results: list[SpNetLANDiscovery],
        seen: set[tuple[str, bytes]],
    ) -> None:
        self.results = results
        self.seen = seen

    def datagram_received(self, data: bytes, addr: tuple[Any, ...]) -> None:
        host = str(addr[0]).strip() if addr else ""
        if not host:
            return
        packet = bytes(data)
        if parse_spnet_discovery_response(packet, source=host) is None:
            return
        key = (host.casefold(), packet)
        if key in self.seen:
            return
        self.seen.add(key)
        port = int(addr[1]) if len(addr) > 1 else 0
        self.results.append(
            SpNetLANDiscovery(response=packet, host=host, port=port)
        )


async def _async_local_ipv4_addresses(
    hass: HomeAssistant | None,
) -> tuple[str, ...]:
    """Return local IPv4 addresses without blocking the event loop."""
    if hass is not None and hasattr(hass, "async_add_executor_job"):
        return await hass.async_add_executor_job(_local_ipv4_addresses)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _local_ipv4_addresses)


def _local_ipv4_addresses() -> tuple[str, ...]:
    addresses: list[str] = []
    hostname = socket.gethostname()
    with contextlib.suppress(OSError):
        for family, _, _, _, sockaddr in socket.getaddrinfo(
            hostname,
            None,
            family=socket.AF_INET,
            type=socket.SOCK_DGRAM,
        ):
            if family == socket.AF_INET and sockaddr:
                address = str(sockaddr[0])
                if address not in addresses:
                    addresses.append(address)

    with contextlib.suppress(OSError):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            address = str(sock.getsockname()[0])
            if address not in addresses:
                addresses.append(address)
        finally:
            sock.close()
    return tuple(addresses)
