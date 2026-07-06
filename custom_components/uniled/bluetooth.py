"""Home Assistant Bluetooth transport for UniLED."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .const import DOMAIN
from .core import DeviceState, TransportError
from .core.transports import BLEMeshProfile, BLEProfile

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
else:
    HomeAssistant = Any

_LOGGER = logging.getLogger(__name__)


class UniLEDBLETransport:
    """BLE byte transport backed by Home Assistant Bluetooth."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        address: str,
        name: str,
        profile: BLEProfile,
        notification_callback: Callable[[bytes], DeviceState | None],
    ) -> None:
        """Initialize the BLE transport."""
        self._hass = hass
        self._address = address
        self._name = name
        self._profile = profile
        self._notification_callback = notification_callback
        self._client: Any | None = None
        self._connected = False
        self._write_characteristic: Any | None = None
        self._notification_characteristic: Any | None = None

    async def connect(self) -> None:
        """Connect and subscribe to notifications."""
        from bleak_retry_connector import establish_connection
        from habluetooth import BleakClientWithServiceCache
        from homeassistant.components import bluetooth as ha_bluetooth

        ble_device = ha_bluetooth.async_ble_device_from_address(
            self._hass,
            self._address,
            connectable=True,
        )
        if ble_device is None:
            raise TransportError(f"No reachable BLE device for {self._address}")

        client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            self._name,
            self._address,
        )
        self._client = client
        self._notification_characteristic = self._resolve_characteristic(
            self._profile.notification_uuid_candidates,
            "notify",
        )
        await client.start_notify(
            self._notification_characteristic,
            self._handle_notification,
        )
        self._connected = True
        _LOGGER.debug("%s connected over BLE", self._name)

    async def close(self) -> None:
        """Disconnect the BLE client."""
        if self._client is None:
            self._connected = False
            return
        try:
            if self._connected:
                notify_characteristic = (
                    self._notification_characteristic
                    or self._profile.notification_uuid
                )
                await self._client.stop_notify(notify_characteristic)
        finally:
            await self._client.disconnect()
            self._client = None
            self._connected = False
            self._write_characteristic = None
            self._notification_characteristic = None

    async def send(self, payload: bytes, *, response: bool = False) -> bytes | None:
        """Send one payload to the BLE write characteristic."""
        if self._client is None or not self._connected:
            await self.connect()
        if self._client is None:
            raise TransportError(f"{self._name} BLE client is not connected")

        if self._write_characteristic is None:
            self._write_characteristic = self._resolve_characteristic(
                self._profile.write_uuid_candidates,
                "write",
            )
        await self._client.write_gatt_char(
            self._write_characteristic,
            payload,
            response=_write_response_mode(self._write_characteristic, response),
        )
        return None

    def _handle_notification(self, _sender: Any, data: bytearray) -> None:
        """Forward a BLE notification into the protocol session."""
        self._notification_callback(bytes(data))

    def _resolve_characteristic(
        self,
        uuids: str | tuple[str, ...],
        purpose: str,
    ) -> Any:
        """Return a service-scoped GATT characteristic when services are known."""
        if self._client is None:
            raise TransportError(f"{self._name} BLE client is not connected")
        candidates = (uuids,) if isinstance(uuids, str) else uuids
        services = getattr(self._client, "services", None)
        if services is None:
            return candidates[0]

        for service_uuid in self._profile.service_uuids:
            service = _service_by_uuid(services, service_uuid)
            if service is None:
                continue
            for uuid in candidates:
                characteristic = _characteristic_by_uuid(service, uuid)
                if characteristic is not None:
                    return characteristic

        if self._profile.service_uuids:
            service_list = ", ".join(self._profile.service_uuids)
            uuid_list = ", ".join(candidates)
            raise TransportError(
                f"{self._name} does not expose {purpose} characteristic "
                f"{uuid_list} under expected service(s): {service_list}"
            )

        for uuid in candidates:
            characteristic = _characteristic_from_collection(services, uuid)
            if characteristic is not None:
                return characteristic
        return candidates[0]


class UniLEDZenggeMeshTransport:
    """Characteristic-specific BLE transport for Telink/Zengge mesh."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        address: str,
        name: str,
        profile: BLEMeshProfile,
        notification_callback: Callable[[bytes], DeviceState | None],
        pair_read_delay: float = 0.3,
    ) -> None:
        """Initialize the Zengge BLE mesh transport."""
        self._hass = hass
        self._address = address
        self._name = name
        self._profile = profile
        self._notification_callback = notification_callback
        self._pair_read_delay = pair_read_delay
        self._client: Any | None = None
        self._connected = False

    async def connect(self) -> None:
        """Connect and subscribe to mesh status notifications."""
        from bleak_retry_connector import establish_connection
        from habluetooth import BleakClientWithServiceCache
        from homeassistant.components import bluetooth as ha_bluetooth

        status_uuid = self._require_uuid(self._profile.status_uuid, "status")
        ble_device = ha_bluetooth.async_ble_device_from_address(
            self._hass,
            self._address,
            connectable=True,
        )
        if ble_device is None:
            raise TransportError(f"No reachable BLE mesh node for {self._address}")

        client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            self._name,
            self._address,
        )
        self._client = client
        await client.start_notify(status_uuid, self._handle_notification)
        self._connected = True
        _LOGGER.debug("%s connected over Zengge BLE mesh", self._name)

    async def close(self) -> None:
        """Disconnect the BLE mesh client."""
        if self._client is None:
            self._connected = False
            return
        try:
            if self._connected and self._profile.status_uuid is not None:
                await self._client.stop_notify(self._profile.status_uuid)
        finally:
            await self._client.disconnect()
            self._client = None
            self._connected = False

    async def write_pair(self, payload: bytes) -> bytes | None:
        """Write bytes to the Zengge pair characteristic."""
        client = await self._ensure_connected()
        await client.write_gatt_char(
            self._require_uuid(self._profile.pair_uuid, "pair"),
            payload,
            response=True,
        )
        return None

    async def read_pair(self) -> bytes:
        """Read the Zengge pair characteristic reply."""
        client = await self._ensure_connected()
        if self._pair_read_delay > 0:
            await asyncio.sleep(self._pair_read_delay)
        return bytes(
            await client.read_gatt_char(
                self._require_uuid(self._profile.pair_uuid, "pair")
            )
        )

    async def write_status(self, payload: bytes) -> bytes | None:
        """Write bytes to the Zengge status characteristic."""
        client = await self._ensure_connected()
        await client.write_gatt_char(
            self._require_uuid(self._profile.status_uuid, "status"),
            payload,
            response=True,
        )
        return None

    async def write_command(
        self,
        payload: bytes,
        *,
        response: bool = False,
    ) -> bytes | None:
        """Write bytes to the Zengge command characteristic."""
        client = await self._ensure_connected()
        await client.write_gatt_char(
            self._require_uuid(self._profile.command_uuid, "command"),
            payload,
            response=response,
        )
        return None

    def _handle_notification(self, _sender: Any, data: bytearray) -> None:
        """Forward encrypted mesh notifications into the mesh session."""
        self._notification_callback(bytes(data))

    async def _ensure_connected(self) -> Any:
        if self._client is None or not self._connected:
            await self.connect()
        if self._client is None:
            raise TransportError(f"{self._name} BLE mesh client is not connected")
        return self._client

    def _require_uuid(self, uuid: str | None, purpose: str) -> str:
        if uuid is None:
            raise TransportError(f"{self._name} missing {purpose} characteristic UUID")
        return uuid


def ble_device_name(model_name: str, address: str) -> str:
    """Return a stable name for BLE connection logs."""
    return f"{DOMAIN}:{model_name}:{address}"


def _service_by_uuid(services: Any, uuid: str) -> Any | None:
    get_service = getattr(services, "get_service", None)
    if callable(get_service):
        service = get_service(uuid)
        if service is not None:
            return service

    for service in _iter_services(services):
        if _uuid_matches(getattr(service, "uuid", None), uuid):
            return service
    return None


def _characteristic_by_uuid(service: Any, uuid: str) -> Any | None:
    get_characteristic = getattr(service, "get_characteristic", None)
    if callable(get_characteristic):
        characteristic = get_characteristic(uuid)
        if characteristic is not None:
            return characteristic

    for characteristic in _iter_characteristics(service):
        if _uuid_matches(getattr(characteristic, "uuid", None), uuid):
            return characteristic
    return None


def _characteristic_from_collection(services: Any, uuid: str) -> Any | None:
    get_characteristic = getattr(services, "get_characteristic", None)
    if callable(get_characteristic):
        characteristic = get_characteristic(uuid)
        if characteristic is not None:
            return characteristic

    for service in _iter_services(services):
        if characteristic := _characteristic_by_uuid(service, uuid):
            return characteristic
    return None


def _write_response_mode(characteristic: Any, requested_response: bool) -> bool:
    """Return the BLE write response flag matching APK bridge behavior."""
    if requested_response:
        return True

    properties = getattr(characteristic, "properties", None)
    if properties is None:
        return False

    if isinstance(properties, int):
        supports_write_without_response = bool(properties & 0x04)
        supports_write = bool(properties & 0x08)
        return supports_write and not supports_write_without_response

    if isinstance(properties, str):
        property_names = {properties.casefold()}
    else:
        try:
            property_names = {str(item).casefold() for item in properties}
        except TypeError:
            return False

    if {
        "write-without-response",
        "write_without_response",
        "write no response",
    } & property_names:
        return False
    return bool({"write", "write-with-response", "write_response"} & property_names)


def _iter_services(services: Any) -> tuple[Any, ...]:
    values = getattr(services, "values", None)
    if callable(values):
        return tuple(values())
    try:
        return tuple(services)
    except TypeError:
        return ()


def _iter_characteristics(service: Any) -> tuple[Any, ...]:
    characteristics = getattr(service, "characteristics", ())
    values = getattr(characteristics, "values", None)
    if callable(values):
        return tuple(values())
    try:
        return tuple(characteristics)
    except TypeError:
        return ()


def _uuid_matches(actual: Any, expected: str) -> bool:
    return str(actual).casefold() == expected.casefold()
