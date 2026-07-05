"""Bluetooth transport tests that do not require Home Assistant."""

from __future__ import annotations

import asyncio
from typing import Any

from custom_components.uniled.bluetooth import (
    UniLEDBLETransport,
    UniLEDZenggeMeshTransport,
)
from custom_components.uniled.core import DeviceState, ProtocolFamily, TransportError
from custom_components.uniled.core.transports import BLEMeshProfile, BLEProfile


class FakeBleakClient:
    """Small fake for characteristic-level BLE transport tests."""

    def __init__(self, pair_response: bytes = b"\x0dABCDEFGH") -> None:
        self.pair_response = pair_response
        self.writes: list[tuple[Any, bytes, bool]] = []
        self.started: list[Any] = []
        self.stopped: list[Any] = []
        self.disconnected = False
        self.services: FakeServices | None = None

    async def write_gatt_char(
        self,
        uuid: Any,
        payload: bytes,
        response: bool = False,
    ) -> None:
        """Record a characteristic write."""
        self.writes.append((uuid, payload, response))

    async def read_gatt_char(self, uuid: Any) -> bytes:
        """Return the fake pair reply."""
        assert uuid == "pair"
        return self.pair_response

    async def start_notify(self, uuid: Any, callback) -> None:
        """Record notification startup."""
        self.started.append(uuid)
        self.callback = callback

    async def stop_notify(self, uuid: Any) -> None:
        """Record notification shutdown."""
        self.stopped.append(uuid)

    async def disconnect(self) -> None:
        """Record disconnect."""
        self.disconnected = True


class FakeCharacteristic:
    """Tiny characteristic object with a UUID."""

    def __init__(
        self,
        uuid: str,
        label: str,
        *,
        properties: list[str] | int | None = None,
    ) -> None:
        self.uuid = uuid
        self.label = label
        self.properties = () if properties is None else properties


class FakeService:
    """Tiny service object with UUID-scoped characteristic lookup."""

    def __init__(self, uuid: str, characteristics: list[FakeCharacteristic]) -> None:
        self.uuid = uuid
        self.characteristics = characteristics

    def get_characteristic(self, uuid: str) -> FakeCharacteristic | None:
        """Return a matching characteristic from this service."""
        for characteristic in self.characteristics:
            if characteristic.uuid.casefold() == uuid.casefold():
                return characteristic
        return None


class FakeServices:
    """Tiny service collection with Bleak-like helpers."""

    def __init__(self, services: list[FakeService]) -> None:
        self._services = services

    def __iter__(self):
        return iter(self._services)

    def get_service(self, uuid: str) -> FakeService | None:
        """Return a matching service."""
        for service in self._services:
            if service.uuid.casefold() == uuid.casefold():
                return service
        return None


def _profile() -> BLEMeshProfile:
    return BLEMeshProfile(
        family=ProtocolFamily.ZENGGE_MESH,
        protocol_name="telink_zengge",
        status_uuid="status",
        command_uuid="command",
        pair_uuid="pair",
    )


def test_direct_ble_transport_resolves_write_characteristic_by_service() -> None:
    """Direct BLE writes are scoped to the expected service UUID."""
    wrong = FakeCharacteristic("char-write", "wrong-service")
    expected = FakeCharacteristic("char-write", "expected-service")
    fake = FakeBleakClient()
    fake.services = FakeServices(
        [
            FakeService("other-service", [wrong]),
            FakeService("service-primary", [expected]),
        ]
    )
    transport = UniLEDBLETransport(
        None,
        address="AA:BB:CC:DD:EE:FF",
        name="SP601E",
        profile=BLEProfile(
            service_uuids=("service-primary",),
            write_uuid="char-write",
        ),
        notification_callback=lambda data: DeviceState(raw=data),
    )
    transport._client = fake
    transport._connected = True

    asyncio.run(transport.send(b"payload", response=True))

    assert fake.writes == [(expected, b"payload", True)]


def test_direct_ble_transport_fails_before_ambiguous_write() -> None:
    """Missing expected service/characteristic pairs fail before writing."""
    fake = FakeBleakClient()
    fake.services = FakeServices(
        [FakeService("other-service", [FakeCharacteristic("char-write", "wrong")])]
    )
    transport = UniLEDBLETransport(
        None,
        address="AA:BB:CC:DD:EE:FF",
        name="SP601E",
        profile=BLEProfile(
            service_uuids=("service-primary",),
            write_uuid="char-write",
        ),
        notification_callback=lambda data: DeviceState(raw=data),
    )
    transport._client = fake
    transport._connected = True

    try:
        asyncio.run(transport.send(b"payload"))
    except TransportError as ex:
        assert "write characteristic" in str(ex)
        assert "service-primary" in str(ex)
    else:
        raise AssertionError("missing direct BLE characteristic should fail")
    assert fake.writes == []


def test_direct_ble_transport_matches_apk_write_type_fallback() -> None:
    """Direct BLE write response behavior follows characteristic properties."""
    write_with_response = FakeCharacteristic(
        "char-write",
        "write-with-response",
        properties=["write"],
    )
    write_without_response = FakeCharacteristic(
        "char-write",
        "write-without-response",
        properties=["write-without-response"],
    )

    for characteristic, expected_response in (
        (write_with_response, True),
        (write_without_response, False),
        (FakeCharacteristic("char-write", "android-mask", properties=0x08), True),
        (FakeCharacteristic("char-write", "android-mask", properties=0x04), False),
    ):
        fake = FakeBleakClient()
        fake.services = FakeServices([FakeService("service-primary", [characteristic])])
        transport = UniLEDBLETransport(
            None,
            address="AA:BB:CC:DD:EE:FF",
            name="SP601E",
            profile=BLEProfile(
                service_uuids=("service-primary",),
                write_uuid="char-write",
            ),
            notification_callback=lambda data: DeviceState(raw=data),
        )
        transport._client = fake
        transport._connected = True

        asyncio.run(transport.send(b"payload"))

        assert fake.writes == [(characteristic, b"payload", expected_response)]


def test_zengge_ble_mesh_transport_routes_characteristic_writes() -> None:
    """Zengge mesh transport writes to pair, status, and command UUIDs."""
    seen: list[bytes] = []
    transport = UniLEDZenggeMeshTransport(
        None,
        address="AA:BB:CC:DD:EE:FF",
        name="RG4",
        profile=_profile(),
        notification_callback=lambda data: seen.append(data) or None,
        pair_read_delay=0,
    )
    fake = FakeBleakClient()
    transport._client = fake
    transport._connected = True

    asyncio.run(transport.write_pair(b"pair payload"))
    pair_response = asyncio.run(transport.read_pair())
    asyncio.run(transport.write_status(b"\x01"))
    asyncio.run(transport.write_command(b"command payload", response=True))
    transport._handle_notification(None, bytearray(b"notification"))
    asyncio.run(transport.close())

    assert pair_response == b"\x0dABCDEFGH"
    assert fake.writes == [
        ("pair", b"pair payload", True),
        ("status", b"\x01", True),
        ("command", b"command payload", True),
    ]
    assert seen == [b"notification"]
    assert fake.stopped == ["status"]
    assert fake.disconnected is True


def test_zengge_ble_mesh_transport_requires_characteristic_uuids() -> None:
    """Incomplete mesh profiles fail before writing unknown characteristics."""
    transport = UniLEDZenggeMeshTransport(
        None,
        address="AA:BB:CC:DD:EE:FF",
        name="RG4",
        profile=BLEMeshProfile(
            family=ProtocolFamily.ZENGGE_MESH,
            protocol_name="telink_zengge",
        ),
        notification_callback=lambda data: DeviceState(raw=data),
        pair_read_delay=0,
    )
    transport._client = FakeBleakClient()
    transport._connected = True

    try:
        asyncio.run(transport.write_command(b"payload"))
    except TransportError as ex:
        assert "command characteristic" in str(ex)
    else:
        raise AssertionError("missing Zengge command UUID should fail")
