"""LAN discovery tests."""

from __future__ import annotations

import asyncio
import errno
from dataclasses import dataclass
from enum import Enum
from typing import Any

import custom_components.uniled.lan as lan_module
from custom_components.uniled.const import (
    CONF_DEVICE_ID,
    CONF_DISCOVERY_RESPONSE_HEX,
    CONF_HOST,
    CONF_MODEL,
    CONF_MODEL_ID,
    CONF_TRANSPORT,
    DOMAIN,
    TRANSPORT_BLE,
    TRANSPORT_LAN,
)
from custom_components.uniled.lan import (
    _SPNET_DISCOVERY_TASK,
    SpNetLANDiscovery,
    _async_handle_spnet_discovery,
    _SPNetDiscoveryProtocol,
    async_discover_spnet_devices,
    async_start_spnet_discovery,
    spnet_broadcast_addresses,
    spnet_discovery_flow_data,
)


class _EntryState(Enum):
    LOADED = "loaded"
    SETUP_RETRY = "setup_retry"
    SETUP_IN_PROGRESS = "setup_in_progress"


@dataclass
class _LANEntry:
    entry_id: str
    unique_id: str | None
    data: dict[str, Any]
    state: _EntryState = _EntryState.SETUP_RETRY
    disabled_by: str | None = None
    source: str = "user"

    @property
    def title(self) -> str:
        return self.entry_id


class _LANConfigEntries:
    def __init__(self, *entries: _LANEntry) -> None:
        self.entries = entries
        self.updated: list[tuple[str, dict[str, Any]]] = []
        self.reloaded: list[str] = []
        self.discovered: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
        self.flow = self

    def async_entries(self, domain, include_ignore=True):
        assert domain == DOMAIN
        if include_ignore:
            return list(self.entries)
        return [entry for entry in self.entries if entry.source != "ignore"]

    def async_update_entry(self, entry, *, data):
        if data == entry.data:
            return False
        self.updated.append((entry.entry_id, data))
        entry.data = data
        return True

    def async_schedule_reload(self, entry_id):
        self.reloaded.append(entry_id)

    async def async_init(self, domain, *, context, data):
        self.discovered.append((domain, context, data))


class _LANHass:
    def __init__(self, *entries: _LANEntry) -> None:
        self.config_entries = _LANConfigEntries(*entries)
        self.data: dict[str, Any] = {}

    async def async_add_executor_job(self, func, *args):
        return await asyncio.to_thread(func, *args)


def _spnet_response(host, mac="54:20:24:11:1f:77", model_code=0x5C):
    mac_bytes = mac.replace(":", "") if mac else "000000000000"
    packet = bytes.fromhex(
        f"53704e6574000021000000000001000010{model_code:02x}00"
        f"{mac_bytes}075350353431450000"
    )
    return SpNetLANDiscovery(response=packet, host=host, port=6454)


def _sp541e_entry(entry_id, host, unique_id, *, device_id=None, **kwargs):
    return _LANEntry(
        entry_id,
        unique_id,
        {
            CONF_MODEL: "SP541E",
            CONF_MODEL_ID: 0x5C,
            CONF_TRANSPORT: TRANSPORT_LAN,
            CONF_HOST: host,
            CONF_DEVICE_ID: device_id or host,
            "retained": "existing config data",
        },
        **kwargs,
    )


async def _run_discovery(hass, *responses, discover_new=True):
    async def discover():
        return responses

    await _async_handle_spnet_discovery(hass, discover, discover_new=discover_new)


def test_spnet_discovery_protocol_filters_noise_and_duplicates() -> None:
    """Only recovered SPNet response packets become discovery candidates."""
    results: list[SpNetLANDiscovery] = []
    protocol = _SPNetDiscoveryProtocol(results, set())
    response = bytes.fromhex(
        "53704e65740000210000000000010000105c00542024111f77075350353431450000"
    )

    protocol.datagram_received(b"not-spnet", ("192.0.2.91", 6454))
    protocol.datagram_received(response, ("192.0.2.92", 6454))
    protocol.datagram_received(response, ("192.0.2.92", 6454))
    protocol.datagram_received(response, ("192.0.2.93", 6454))

    assert results == [
        SpNetLANDiscovery(response=response, host="192.0.2.92", port=6454),
        SpNetLANDiscovery(response=response, host="192.0.2.93", port=6454),
    ]


def test_spnet_discovery_flow_data_uses_hex_response_and_host() -> None:
    """SPNet discovery candidates are serialized for config-flow handoff."""
    response = bytes.fromhex(
        "53704e65740000210000000000010000105c00542024111f77075350353431450000"
    )

    data = spnet_discovery_flow_data(
        SpNetLANDiscovery(response=response, host="192.0.2.92", port=6454)
    )

    assert data == {
        CONF_HOST: "192.0.2.92",
        CONF_DISCOVERY_RESPONSE_HEX: response.hex(),
    }


async def test_spnet_discovery_flow_init_uses_current_ha_discovery_source() -> None:
    """SPNet flow handoff uses the literal source accepted by current HA."""
    discovery = _spnet_response("192.0.2.92")
    hass = _LANHass()
    await _run_discovery(hass, discovery)

    assert hass.config_entries.discovered == [
        (
            "uniled",
            {"source": "discovery"},
            {
                CONF_HOST: "192.0.2.92",
                CONF_DISCOVERY_RESPONSE_HEX: discovery.response.hex(),
            },
        )
    ]


async def test_spnet_discovery_flow_handoff_failure_does_not_abort_scan() -> None:
    """One failed SPNet flow handoff does not drop later discovered devices."""
    calls = []

    class FakeFlow:
        async def async_init(self, domain, *, context, data):
            calls.append((domain, context, data))
            if len(calls) == 1:
                raise RuntimeError("flow failed")

    hass = _LANHass()
    hass.config_entries.flow = FakeFlow()
    await _run_discovery(
        hass,
        _spnet_response("192.0.2.92"),
        _spnet_response("192.0.2.93", "56:20:24:06:d9:d6"),
    )

    assert [call[2][CONF_HOST] for call in calls] == ["192.0.2.92", "192.0.2.93"]


async def test_spnet_discovery_moves_existing_lan_entries_by_mac() -> None:
    """Apply a verified move once without changing existing device identities."""
    raam = _sp541e_entry("raam", "192.0.2.82", "54:20:24:11:1F:77")
    midden = _sp541e_entry(
        "midden",
        "192.0.2.99",
        "legacy-id",
        device_id="56:20:24:06:D9:D6",
        state=_EntryState.LOADED,
    )
    muur = _sp541e_entry(
        "muur",
        "192.0.2.160",
        "56:20:24:06:d6:ee",
        state=_EntryState.SETUP_IN_PROGRESS,
    )
    hass = _LANHass(raam, midden, muur)
    expected = {
        "raam": {**raam.data, CONF_HOST: "192.0.2.77"},
        "midden": {**midden.data, CONF_HOST: "192.0.2.93"},
        "muur": {**muur.data, CONF_HOST: "192.0.2.154"},
    }
    raam_response = _spnet_response("192.0.2.77")
    responses = (
        raam_response,
        raam_response,
        _spnet_response("192.0.2.93", "56:20:24:06:d9:d6"),
        _spnet_response("192.0.2.154", "56:20:24:06:d6:ee"),
    )
    await _run_discovery(hass, *responses)
    await _run_discovery(hass, *responses)

    assert len(hass.config_entries.updated) == 3
    assert dict(hass.config_entries.updated) == expected
    assert sorted(hass.config_entries.reloaded) == sorted(expected)
    assert hass.config_entries.discovered == []
    assert raam.unique_id == "54:20:24:11:1F:77"
    assert midden.unique_id == "legacy-id"


async def test_spnet_discovery_skips_ambiguous_lan_moves() -> None:
    """Ignore a snapshot with duplicate claims for an address or a controller."""
    mac = "54:20:24:11:1f:77"
    hass = _LANHass(_sp541e_entry("raam", "192.0.2.82", mac))
    move = _spnet_response("192.0.2.77", mac)
    await _run_discovery(hass, move, _spnet_response("192.0.2.78", mac))
    await _run_discovery(
        hass,
        move,
        _spnet_response("192.0.2.77", "56:20:24:06:d6:ee"),
    )

    assert hass.config_entries.updated == []
    assert hass.config_entries.reloaded == []
    assert hass.config_entries.discovered == []


async def test_periodic_spnet_discovery_updates_only_existing_entries() -> None:
    """A periodic scan can recover legacy entries without adding other devices."""
    entry = _sp541e_entry("raam", "192.0.2.82", "54:20:24:11:1f:77")
    entry.data[CONF_TRANSPORT] = "net"
    entry.data["ip_address"] = entry.data.pop(CONF_HOST)
    hass = _LANHass(entry)

    await _run_discovery(
        hass,
        _spnet_response("192.0.2.77"),
        _spnet_response("192.0.2.154", "56:20:24:06:d6:ee"),
        discover_new=False,
    )

    assert entry.data[CONF_HOST] == "192.0.2.77"
    assert hass.config_entries.reloaded == [entry.entry_id]
    assert hass.config_entries.discovered == []


async def test_spnet_discovery_does_not_infer_lan_identity() -> None:
    """Skip address changes if either side lacks a reliable matching identity."""
    mac = "54:20:24:11:1f:77"
    other_mac = "56:20:24:06:d6:ee"
    for unique_id, device_id, response in (
        (mac, None, _spnet_response("192.0.2.77", None)),
        ("lan:192.0.2.82", None, _spnet_response("192.0.2.77", mac)),
        (mac, other_mac, _spnet_response("192.0.2.77", mac)),
        (mac, other_mac, _spnet_response("192.0.2.77", other_mac)),
    ):
        entry = _sp541e_entry("raam", "192.0.2.82", unique_id, device_id=device_id)
        hass = _LANHass(entry)
        await _run_discovery(hass, response)

        assert hass.config_entries.updated == []
        assert hass.config_entries.reloaded == []
        assert entry.data[CONF_HOST] == "192.0.2.82"


async def test_spnet_discovery_respects_entry_model_transport_and_status() -> None:
    """An exact MAC alone cannot retarget an incompatible or inactive entry."""
    mac = "54:20:24:11:1f:77"
    different_model = _sp541e_entry("model", "192.0.2.82", mac)
    different_model.data.update({CONF_MODEL: "SP530E", CONF_MODEL_ID: 0x4E})
    different_transport = _sp541e_entry("transport", "192.0.2.82", mac)
    different_transport.data[CONF_TRANSPORT] = TRANSPORT_BLE
    disabled = _sp541e_entry("disabled", "192.0.2.82", mac, disabled_by="user")
    ignored = _sp541e_entry("ignored", "192.0.2.82", mac, source="ignore")

    for entry in (different_model, different_transport, disabled, ignored):
        hass = _LANHass(entry)
        await _run_discovery(hass, _spnet_response("192.0.2.77", mac))

        assert hass.config_entries.updated == []
        assert hass.config_entries.reloaded == []
        if entry is not different_transport:
            assert hass.config_entries.discovered == []
        assert entry.data[CONF_HOST] == "192.0.2.82"


async def test_spnet_discovery_task_reuses_inflight_scan_and_clears_when_done() -> None:
    """Startup SPNet discovery keeps only one in-flight task and clears it."""
    release = asyncio.Event()
    started = 0

    class FakeFlow:
        async def async_init(self, _domain, *, context, data):
            raise AssertionError("empty discovery results should not start flows")

    class FakeHass:
        def __init__(self) -> None:
            self.data = {}
            self.config_entries = type("ConfigEntries", (), {"flow": FakeFlow()})()

        def async_create_task(self, coro):
            return asyncio.create_task(coro)

    async def discovery_func():
        nonlocal started
        started += 1
        await release.wait()
        return ()

    hass = FakeHass()
    task = async_start_spnet_discovery(hass, discovery_func=discovery_func)

    assert async_start_spnet_discovery(hass, discovery_func=discovery_func) is task
    await asyncio.sleep(0)

    assert started == 1
    assert hass.data[DOMAIN][_SPNET_DISCOVERY_TASK] is task

    release.set()
    await task
    await asyncio.sleep(0)

    assert _SPNET_DISCOVERY_TASK not in hass.data[DOMAIN]


async def test_spnet_discovery_task_clears_failed_scan() -> None:
    """Failed startup SPNet discovery tasks do not leave stale task handles."""

    class FakeHass:
        def __init__(self) -> None:
            self.data = {}

        def async_create_task(self, coro):
            return asyncio.create_task(coro)

    async def discovery_func():
        raise RuntimeError("scan failed")

    hass = FakeHass()
    task = async_start_spnet_discovery(hass, discovery_func=discovery_func)

    try:
        await task
    except RuntimeError as ex:
        assert str(ex) == "scan failed"
    else:
        raise AssertionError("failed discovery task should preserve its exception")
    await asyncio.sleep(0)

    assert _SPNET_DISCOVERY_TASK not in hass.data[DOMAIN]


async def test_spnet_discovery_resolves_local_addresses_in_executor() -> None:
    """Async SPNet discovery does not probe local addresses in the event loop."""
    executor_calls = []
    sent = []
    closed = []

    def fail_if_called_directly():
        raise AssertionError("local address probing must run in an executor")

    class FakeHass:
        async def async_add_executor_job(self, func):
            executor_calls.append(func)
            return ("192.168.7.42",)

    class FakeTransport:
        def sendto(self, payload, address):
            sent.append((payload, address))

        def close(self):
            closed.append(True)

    class FakeLoop:
        async def create_datagram_endpoint(
            self,
            factory,
            *,
            local_addr,
            allow_broadcast,
        ):
            assert local_addr == ("0.0.0.0", 6454)
            assert allow_broadcast is True
            assert isinstance(factory(), lan_module._SPNetDiscoveryProtocol)
            return FakeTransport(), object()

    original_local_addresses = lan_module._local_ipv4_addresses
    original_get_running_loop = lan_module.asyncio.get_running_loop
    try:
        lan_module._local_ipv4_addresses = fail_if_called_directly
        lan_module.asyncio.get_running_loop = lambda: FakeLoop()
        results = await async_discover_spnet_devices(hass=FakeHass(), scan_window=0)
    finally:
        lan_module._local_ipv4_addresses = original_local_addresses
        lan_module.asyncio.get_running_loop = original_get_running_loop

    assert results == ()
    assert executor_calls == [fail_if_called_directly]
    assert [address for _, address in sent] == [
        ("255.255.255.255", 6454),
        ("192.168.7.255", 6454),
    ]
    assert closed == [True]


async def test_spnet_discovery_falls_back_when_source_port_is_busy() -> None:
    """Retain discovery on hosts that already have a listener on UDP 6454."""
    bound_addresses = []
    sent_to = []

    class FakeTransport:
        def sendto(self, payload, address):
            sent_to.append(address)

        def close(self):
            pass

    class FakeLoop:
        async def create_datagram_endpoint(
            self, factory, *, local_addr, allow_broadcast
        ):
            bound_addresses.append(local_addr)
            assert allow_broadcast
            if local_addr[1] == 6454:
                raise OSError(errno.EADDRINUSE, "address in use")
            return FakeTransport(), factory()

    original_get_running_loop = lan_module.asyncio.get_running_loop
    try:
        lan_module.asyncio.get_running_loop = lambda: FakeLoop()
        await async_discover_spnet_devices(
            scan_window=0, broadcast_addresses=("192.0.2.255",)
        )
    finally:
        lan_module.asyncio.get_running_loop = original_get_running_loop

    assert bound_addresses == [("0.0.0.0", 6454), ("0.0.0.0", 0)]
    assert sent_to == [("192.0.2.255", 6454)]


def test_spnet_broadcast_addresses_include_private_24_broadcasts() -> None:
    """SPNet discovery includes directed broadcasts derived from local IPs."""
    assert spnet_broadcast_addresses(
        (
            "192.168.0.42",
            "10.2.3.4",
            "127.0.0.1",
            "not-an-ip",
        )
    ) == (
        "255.255.255.255",
        "192.168.0.255",
        "10.2.3.255",
    )
