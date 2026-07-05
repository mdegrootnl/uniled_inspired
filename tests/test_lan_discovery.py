"""LAN discovery tests."""

from __future__ import annotations

import asyncio

import custom_components.uniled.lan as lan_module
from custom_components.uniled.const import (
    CONF_DISCOVERY_RESPONSE_HEX,
    CONF_HOST,
    DOMAIN,
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
    response = bytes.fromhex(
        "53704e65740000210000000000010000105c00542024111f77075350353431450000"
    )
    calls = []

    class FakeFlow:
        async def async_init(self, domain, *, context, data):
            calls.append((domain, context, data))

    class FakeHass:
        config_entries = type("ConfigEntries", (), {"flow": FakeFlow()})()

    async def discovery_func():
        return [SpNetLANDiscovery(response=response, host="192.0.2.92", port=6454)]

    await _async_handle_spnet_discovery(FakeHass(), discovery_func)

    assert calls == [
        (
            "uniled",
            {"source": "discovery"},
            {
                CONF_HOST: "192.0.2.92",
                CONF_DISCOVERY_RESPONSE_HEX: response.hex(),
            },
        )
    ]


async def test_spnet_discovery_flow_handoff_failure_does_not_abort_scan() -> None:
    """One failed SPNet flow handoff does not drop later discovered devices."""
    response = bytes.fromhex(
        "53704e65740000210000000000010000105c00542024111f77075350353431450000"
    )
    calls = []

    class FakeFlow:
        async def async_init(self, domain, *, context, data):
            calls.append((domain, context, data))
            if len(calls) == 1:
                raise RuntimeError("flow failed")

    class FakeHass:
        config_entries = type("ConfigEntries", (), {"flow": FakeFlow()})()

    async def discovery_func():
        return [
            SpNetLANDiscovery(response=response, host="192.0.2.92", port=6454),
            SpNetLANDiscovery(response=response, host="192.0.2.93", port=6454),
        ]

    await _async_handle_spnet_discovery(FakeHass(), discovery_func)

    assert [call[2][CONF_HOST] for call in calls] == ["192.0.2.92", "192.0.2.93"]


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
            assert local_addr == ("0.0.0.0", 0)
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
