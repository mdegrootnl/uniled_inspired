"""Telink/Zengge BLE mesh packet helpers ported from old UniLED."""

from __future__ import annotations

import asyncio
import colorsys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from os import urandom
from struct import pack
from typing import Protocol

from ..state import ChannelState, DeviceState, ParseNotificationError

try:
    from Crypto.Cipher import AES
except ImportError:  # pragma: no cover - exercised by dependency-free tests.
    AES = None

BlockEncryptor = Callable[[bytes, bytes], bytes]

C_GET_STATUS_SENT = 0xDA
C_GET_STATUS_RECEIVED = 0xDB
C_NOTIFICATION_RECEIVED = 0xDC
C_POWER = 0xD0
C_COLOR = 0xE2
C_EFFECT = 0xED

ZENGGE_MESH_ADDRESS_NONE = 0x00
ZENGGE_MESH_ADDRESS_BRIDGE = 0xFF
ZENGGE_DEVICE_TYPE_LIGHT_STRIP = 2
ZENGGE_DEVICE_TYPE_LIGHT_BULB = 5
ZENGGE_DEVICE_TYPE_PANEL_RGBCCT = 35
ZENGGE_WIRING_CONTROL_RGB_W = 2
ZENGGE_WIRING_CONTROL_RGB_CCT = 4
ZENGGE_WIRING_CONNECTION_RGB_CCT = 4
ZENGGE_WIRING_CONNECTION_CCT = 7
ZENGGE_STATE_MODE_RGB = 0
ZENGGE_STATE_MODE_CCT = 1
ZENGGE_STATE_MODE_DYNAMIC = 2
ZENGGE_STATUS_ONLINE = "Online"
ZENGGE_STATUS_OFFLINE = "Offline"
ZENGGE_EFFECT_SOLID = "Solid"
ZENGGE_EFFECT_UNKNOWN = "?FX?"
ZENGGE_DEFAULT_MESH_KEY = b"ZenggeMesh"
ZENGGE_DEFAULT_MESH_PASS = b"ZenggeTechnology"
ZENGGE_PAIR_SUCCESS = 0x0D
ZENGGE_PAIR_AUTH_ERROR = 0x0E
ZENGGE_COLOR_MODE_RGB = 0x60
ZENGGE_COLOR_MODE_WARMWHITE = 0x61
ZENGGE_COLOR_MODE_CCT = 0x62
ZENGGE_DIMMING_TARGET_AUTO = 0x06
ZENGGE_MIN_KELVIN = 2800
ZENGGE_MAX_KELVIN = 6500

COLOR_MODE_BRIGHTNESS = "brightness"
COLOR_MODE_COLOR_TEMP = "color_temp"
COLOR_MODE_RGB = "rgb"
COLOR_MODE_WHITE = "white"

ZENGGE_NODE_KIND_STRIP = "strip"
ZENGGE_NODE_KIND_BULB = "bulb"
ZENGGE_NODE_KIND_PANEL = "panel"
ZENGGE_NODE_KIND_LIGHT = "light"
ZENGGE_NODE_KIND_BRIDGE = "bridge"


@dataclass(frozen=True, slots=True)
class ZenggeNodeContext:
    """Known cloud or advertisement metadata for one Zengge mesh node."""

    node_id: int
    node_type: int = 0
    node_wiring: int = 0
    address: str | None = None
    rssi: int | None = None
    name: str | None = None
    area: str | None = None


@dataclass(frozen=True, slots=True)
class ZenggeNotificationBlock:
    """Decoded five-byte node status block from a Zengge notification."""

    node_id: int
    connected: int
    level: int
    mode: int
    value1: int
    value2: int
    raw: bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> ZenggeNotificationBlock:
        """Parse one old-UniLED Zengge five-byte node status block."""
        raw = bytes(data)
        if len(raw) != 5:
            raise ParseNotificationError("Zengge node block must be 5 bytes")
        return cls(
            node_id=raw[0],
            connected=raw[1],
            level=raw[2],
            mode=(raw[3] >> 6) & 0xFF,
            value1=raw[4],
            value2=raw[3] & 0x3F,
            raw=raw,
        )


class ZenggeCryptoError(RuntimeError):
    """Raised when Zengge mesh packet crypto cannot be performed."""


class ZenggeMeshTransport(Protocol):
    """Characteristic-specific byte transport needed by Zengge mesh."""

    async def write_pair(self, payload: bytes) -> bytes | None:
        """Write bytes to the pair characteristic."""

    async def read_pair(self) -> bytes:
        """Read the pair characteristic reply."""

    async def write_status(self, payload: bytes) -> bytes | None:
        """Write bytes to the status characteristic."""

    async def write_command(
        self,
        payload: bytes,
        *,
        response: bool = False,
    ) -> bytes | None:
        """Write bytes to the command characteristic."""


@dataclass(slots=True)
class ZenggeMeshConnection:
    """Pair and command coordinator over a Zengge mesh transport."""

    session: ZenggeMeshSession
    transport: ZenggeMeshTransport
    _transport_lock: asyncio.Lock = field(
        default_factory=asyncio.Lock,
        init=False,
        repr=False,
    )

    async def pair(
        self,
        mesh_name: bytes = ZENGGE_DEFAULT_MESH_KEY,
        mesh_password: bytes = ZENGGE_DEFAULT_MESH_PASS,
        *,
        session_random: bytes | None = None,
    ) -> bytes:
        """Pair over the pair characteristic and store the session key."""
        payload = self.session.build_pair_request(
            mesh_name,
            mesh_password,
            session_random=session_random,
        )
        async with self._transport_lock:
            await self.transport.write_pair(payload)
            return self.session.complete_pairing(
                await self.transport.read_pair(),
                mesh_name,
                mesh_password,
            )

    async def request_status(self) -> bytes | None:
        """Kick status notifications through the status characteristic."""
        async with self._transport_lock:
            return await self.transport.write_status(
                self.session.build_status_request()
            )

    async def send_power(
        self,
        node_id: int,
        power: bool,
        *,
        delay_seconds: float = 0.0,
        gradual_seconds: float = 0.0,
        sequence: bytes | None = None,
        response: bool = False,
    ) -> bytes | None:
        """Send a node power command over the command characteristic."""
        return await self._send_command(
            self.session.build_power(
                node_id,
                power,
                delay_seconds=delay_seconds,
                gradual_seconds=gradual_seconds,
                sequence=sequence,
            ),
            response=response,
        )

    async def send_brightness(
        self,
        node_id: int,
        level: int,
        *,
        delay_seconds: float = 0.0,
        gradual_seconds: float = 0.0,
        sequence: bytes | None = None,
        response: bool = False,
    ) -> bytes | None:
        """Send a node brightness command over the command characteristic."""
        return await self._send_command(
            self.session.build_brightness(
                node_id,
                level,
                delay_seconds=delay_seconds,
                gradual_seconds=gradual_seconds,
                sequence=sequence,
            ),
            response=response,
        )

    async def send_rgb(
        self,
        node_id: int,
        red: int,
        green: int,
        blue: int,
        *,
        delay_seconds: float = 0.0,
        gradual_seconds: float = 0.0,
        sequence: bytes | None = None,
        response: bool = False,
    ) -> bytes | None:
        """Send a node RGB command over the command characteristic."""
        return await self._send_command(
            self.session.build_rgb(
                node_id,
                red,
                green,
                blue,
                delay_seconds=delay_seconds,
                gradual_seconds=gradual_seconds,
                sequence=sequence,
            ),
            response=response,
        )

    async def send_cct(
        self,
        node_id: int,
        kelvin: int,
        *,
        level: int = 255,
        delay_seconds: float = 0.0,
        gradual_seconds: float = 0.0,
        sequence: bytes | None = None,
        response: bool = False,
    ) -> bytes | None:
        """Send a node color-temperature command over the command characteristic."""
        return await self._send_command(
            self.session.build_cct(
                node_id,
                kelvin,
                level=level,
                delay_seconds=delay_seconds,
                gradual_seconds=gradual_seconds,
                sequence=sequence,
            ),
            response=response,
        )

    async def send_white(
        self,
        node_id: int,
        white: int,
        *,
        delay_seconds: float = 0.0,
        gradual_seconds: float = 0.0,
        sequence: bytes | None = None,
        response: bool = False,
    ) -> bytes | None:
        """Send a node warm-white command over the command characteristic."""
        return await self._send_command(
            self.session.build_white(
                node_id,
                white,
                delay_seconds=delay_seconds,
                gradual_seconds=gradual_seconds,
                sequence=sequence,
            ),
            response=response,
        )

    async def send_effect(
        self,
        node_id: int,
        effect: int,
        *,
        speed: int = 0,
        level: int = 100,
        sequence: bytes | None = None,
        response: bool = False,
    ) -> bytes | None:
        """Send a node dynamic-effect command over the command characteristic."""
        return await self._send_command(
            self.session.build_effect(
                node_id,
                effect,
                speed=speed,
                level=level,
                sequence=sequence,
            ),
            response=response,
        )

    def apply_notification(self, packet: bytes) -> DeviceState | None:
        """Apply an encrypted notification received from the transport."""
        return self.session.apply_encrypted_notification(packet)

    async def _send_command(
        self,
        payload: bytes,
        *,
        response: bool = False,
    ) -> bytes | None:
        async with self._transport_lock:
            return await self.transport.write_command(payload, response=response)


@dataclass(slots=True)
class ZenggeMeshSession:
    """Stateful core session for Telink/Zengge mesh packet handling."""

    mesh_uuid: int
    address: str
    session_key: bytes | None = None
    contexts: dict[int, ZenggeNodeContext] = field(default_factory=dict)
    block_encryptor: BlockEncryptor | None = None
    pair_random: bytes | None = None
    state: DeviceState | None = None

    @property
    def paired(self) -> bool:
        """Return whether the mesh session key is available."""
        return self.session_key is not None

    def register_node(self, context: ZenggeNodeContext) -> None:
        """Register known metadata for a mesh node ID."""
        self.contexts[int(context.node_id)] = context

    def build_pair_request(
        self,
        mesh_name: bytes = ZENGGE_DEFAULT_MESH_KEY,
        mesh_password: bytes = ZENGGE_DEFAULT_MESH_PASS,
        *,
        session_random: bytes | None = None,
    ) -> bytes:
        """Build and remember a pairing request for the pair characteristic."""
        self.pair_random = (
            urandom(8) if session_random is None else bytes(session_random)
        )
        return make_pair_packet(
            mesh_name,
            mesh_password,
            self.pair_random,
            block_encryptor=self.block_encryptor,
        )

    def complete_pairing(
        self,
        response: bytes,
        mesh_name: bytes = ZENGGE_DEFAULT_MESH_KEY,
        mesh_password: bytes = ZENGGE_DEFAULT_MESH_PASS,
        *,
        session_random: bytes | None = None,
    ) -> bytes:
        """Validate a pair reply and store the derived mesh session key."""
        response = bytes(response)
        if len(response) < 9:
            raise ZenggeCryptoError("pair response must be at least 9 bytes")
        if response[0] == ZENGGE_PAIR_AUTH_ERROR:
            raise ZenggeCryptoError("Zengge mesh credentials were rejected")
        if response[0] != ZENGGE_PAIR_SUCCESS:
            raise ZenggeCryptoError(
                f"unexpected Zengge pair response 0x{response[0]:02x}"
            )

        random = session_random if session_random is not None else self.pair_random
        if random is None:
            raise ZenggeCryptoError("pair session random is not available")

        self.session_key = make_session_key(
            mesh_name,
            mesh_password,
            bytes(random),
            response[1:9],
            block_encryptor=self.block_encryptor,
        )
        return self.session_key

    def build_status_request(self) -> bytes:
        """Return the raw status-characteristic notification kick."""
        return build_status_notify_request()

    def build_state_query(
        self,
        *,
        sequence: bytes | None = None,
    ) -> bytes:
        """Build the old fallback encrypted status query packet."""
        return build_state_query_packet(
            self._require_session_key(),
            self.address,
            self.mesh_uuid,
            sequence=sequence,
            block_encryptor=self.block_encryptor,
        )

    def build_power(
        self,
        node_id: int,
        power: bool,
        *,
        delay_seconds: float = 0.0,
        gradual_seconds: float = 0.0,
        sequence: bytes | None = None,
    ) -> bytes:
        """Build an encrypted node power packet."""
        return build_power_packet(
            self._require_session_key(),
            self.address,
            node_id,
            power,
            delay_seconds=delay_seconds,
            gradual_seconds=gradual_seconds,
            sequence=sequence,
            block_encryptor=self.block_encryptor,
        )

    def build_brightness(
        self,
        node_id: int,
        level: int,
        *,
        delay_seconds: float = 0.0,
        gradual_seconds: float = 0.0,
        sequence: bytes | None = None,
    ) -> bytes:
        """Build an encrypted node brightness packet."""
        return build_brightness_packet(
            self._require_session_key(),
            self.address,
            node_id,
            level,
            delay_seconds=delay_seconds,
            gradual_seconds=gradual_seconds,
            sequence=sequence,
            block_encryptor=self.block_encryptor,
        )

    def build_rgb(
        self,
        node_id: int,
        red: int,
        green: int,
        blue: int,
        *,
        delay_seconds: float = 0.0,
        gradual_seconds: float = 0.0,
        sequence: bytes | None = None,
    ) -> bytes:
        """Build an encrypted node RGB packet."""
        return build_rgb_packet(
            self._require_session_key(),
            self.address,
            node_id,
            red,
            green,
            blue,
            delay_seconds=delay_seconds,
            gradual_seconds=gradual_seconds,
            sequence=sequence,
            block_encryptor=self.block_encryptor,
        )

    def build_cct(
        self,
        node_id: int,
        kelvin: int,
        *,
        level: int = 255,
        delay_seconds: float = 0.0,
        gradual_seconds: float = 0.0,
        sequence: bytes | None = None,
    ) -> bytes:
        """Build an encrypted node CCT packet."""
        return build_cct_packet(
            self._require_session_key(),
            self.address,
            node_id,
            kelvin,
            level=level,
            delay_seconds=delay_seconds,
            gradual_seconds=gradual_seconds,
            sequence=sequence,
            block_encryptor=self.block_encryptor,
        )

    def build_white(
        self,
        node_id: int,
        white: int,
        *,
        delay_seconds: float = 0.0,
        gradual_seconds: float = 0.0,
        sequence: bytes | None = None,
    ) -> bytes:
        """Build an encrypted node warm-white packet."""
        return build_white_packet(
            self._require_session_key(),
            self.address,
            node_id,
            white,
            delay_seconds=delay_seconds,
            gradual_seconds=gradual_seconds,
            sequence=sequence,
            block_encryptor=self.block_encryptor,
        )

    def build_effect(
        self,
        node_id: int,
        effect: int,
        *,
        speed: int = 0,
        level: int = 100,
        sequence: bytes | None = None,
    ) -> bytes:
        """Build an encrypted node effect packet."""
        return build_effect_packet(
            self._require_session_key(),
            self.address,
            node_id,
            effect,
            speed=speed,
            level=level,
            sequence=sequence,
            block_encryptor=self.block_encryptor,
        )

    def apply_decrypted_notification(self, message: bytes) -> DeviceState:
        """Parse and store a decrypted Zengge notification message."""
        self.state = parse_zengge_notification_message(
            message,
            contexts=self.contexts,
            previous=self.state,
        )
        return self.state

    def apply_encrypted_notification(self, packet: bytes) -> DeviceState | None:
        """Decrypt, parse, and store a raw 20-byte mesh notification."""
        message = decrypt_packet(
            self._require_session_key(),
            self.address,
            packet,
            block_encryptor=self.block_encryptor,
        )
        if message is None:
            return None
        return self.apply_decrypted_notification(message)

    def _require_session_key(self) -> bytes:
        if self.session_key is None:
            raise ZenggeCryptoError("Zengge mesh session is not paired")
        return self.session_key


def zengge_crypto_available() -> bool:
    """Return whether the runtime has the pycryptodome AES provider."""
    return AES is not None


def zengge_node_kind(node_type: int) -> str:
    """Return the old-UniLED node role label for a Zengge device type."""
    node_type = int(node_type)
    if node_type == ZENGGE_DEVICE_TYPE_LIGHT_STRIP:
        return ZENGGE_NODE_KIND_STRIP
    if node_type == ZENGGE_DEVICE_TYPE_LIGHT_BULB:
        return ZENGGE_NODE_KIND_BULB
    if node_type == ZENGGE_DEVICE_TYPE_PANEL_RGBCCT:
        return ZENGGE_NODE_KIND_PANEL
    return ZENGGE_NODE_KIND_LIGHT


def encrypt_block(
    key: bytes,
    value: bytes,
    *,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Encrypt one block using the reversed Telink/Zengge AES convention."""
    key = bytes(key)
    if not key:
        raise ZenggeCryptoError("mesh key is required")
    if len(key) != 16:
        raise ZenggeCryptoError("mesh key must be 16 bytes")

    block = bytes(value).ljust(16, b"\x00")
    encrypted = _encrypt_reversed_block(
        bytes(reversed(key)),
        bytes(reversed(block)),
        block_encryptor=block_encryptor,
    )
    return bytes(reversed(encrypted))


def make_checksum(
    key: bytes,
    nonce: bytes,
    payload: bytes,
    *,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build the Telink/Zengge packet checksum block."""
    base = (bytes(nonce) + bytes([len(payload)])).ljust(16, b"\x00")
    check = encrypt_block(key, base, block_encryptor=block_encryptor)

    for offset in range(0, len(payload), 16):
        check_payload = bytes(payload[offset : offset + 16]).ljust(16, b"\x00")
        check = _xor_bytes(check, check_payload)
        check = encrypt_block(key, check, block_encryptor=block_encryptor)

    return check


def crypt_payload(
    key: bytes,
    nonce: bytes,
    payload: bytes,
    *,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Encrypt or decrypt a Telink/Zengge payload."""
    base = bytearray(b"\x00" + bytes(nonce))
    base = base.ljust(16, b"\x00")
    result = bytearray()

    for offset in range(0, len(payload), 16):
        encrypted_base = encrypt_block(key, base, block_encryptor=block_encryptor)
        result.extend(_xor_bytes(encrypted_base, payload[offset : offset + 16]))
        base[0] += 1

    return bytes(result)


def make_command_packet(
    key: bytes,
    address: str,
    dest_id: int,
    command: int,
    data: bytes = b"",
    *,
    sequence: bytes | None = None,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build an encrypted Telink/Zengge mesh command packet."""
    data = bytes(data)
    if len(data) > 10:
        raise ZenggeCryptoError("mesh command data must be 10 bytes or less")
    sequence = urandom(3) if sequence is None else bytes(sequence)
    if len(sequence) != 3:
        raise ZenggeCryptoError("mesh command sequence must be 3 bytes")

    address_bytes = _address_bytes(address)
    nonce = bytes(reversed(address_bytes))[0:4] + b"\x01" + sequence
    payload = (
        int(dest_id).to_bytes(2, byteorder="little")
        + bytes([int(command) & 0xFF])
        + b"\x11\x02"
        + data
    ).ljust(15, b"\x00")

    check = make_checksum(key, nonce, payload, block_encryptor=block_encryptor)
    encrypted_payload = crypt_payload(
        key,
        nonce,
        payload,
        block_encryptor=block_encryptor,
    )
    return sequence + check[:2] + encrypted_payload


def make_control_payload(
    opcode: int,
    value1: int,
    value2: int = 0,
    value3: int = 0,
    *,
    delay_seconds: float = 0.0,
    gradual_seconds: float = 0.0,
    device_type: int = 0xFF,
) -> bytes:
    """Build the old UniLED nine-byte Zengge control payload."""
    delay = int(round(delay_seconds * 10.0)) & 0xFFFF
    gradual = int(round(gradual_seconds * 10.0)) & 0xFFFF
    return pack(
        "<BBBBBHH",
        _byte(device_type, "device_type"),
        _byte(opcode, "opcode"),
        _byte(value1, "value1"),
        _byte(value2, "value2"),
        _byte(value3, "value3"),
        delay,
        gradual,
    )


def build_status_notify_request() -> bytes:
    """Return the raw status-notification kick used by old UniLED."""
    return b"\x01"


def build_state_query_packet(
    key: bytes,
    address: str,
    mesh_uuid: int,
    *,
    sequence: bytes | None = None,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build the old fallback status query packet."""
    return make_command_packet(
        key,
        address,
        mesh_uuid,
        C_GET_STATUS_SENT,
        sequence=sequence,
        block_encryptor=block_encryptor,
    )


def build_power_packet(
    key: bytes,
    address: str,
    node_id: int,
    power: bool,
    *,
    delay_seconds: float = 0.0,
    gradual_seconds: float = 0.0,
    sequence: bytes | None = None,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build an old-UniLED Zengge on/off packet for one mesh node."""
    payload = make_control_payload(
        0x01,
        0xFF if power else 0x00,
        delay_seconds=delay_seconds,
        gradual_seconds=gradual_seconds,
    )
    return make_command_packet(
        key,
        address,
        node_id,
        C_POWER,
        payload,
        sequence=sequence,
        block_encryptor=block_encryptor,
    )


def build_brightness_packet(
    key: bytes,
    address: str,
    node_id: int,
    level: int,
    *,
    delay_seconds: float = 0.0,
    gradual_seconds: float = 0.0,
    sequence: bytes | None = None,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build an old-UniLED Zengge brightness packet for one mesh node."""
    payload = make_control_payload(
        0x02,
        _percentage(level, 255, field="level"),
        ZENGGE_DIMMING_TARGET_AUTO,
        delay_seconds=delay_seconds,
        gradual_seconds=gradual_seconds,
    )
    return make_command_packet(
        key,
        address,
        node_id,
        C_POWER,
        payload,
        sequence=sequence,
        block_encryptor=block_encryptor,
    )


def build_rgb_packet(
    key: bytes,
    address: str,
    node_id: int,
    red: int,
    green: int,
    blue: int,
    *,
    delay_seconds: float = 0.0,
    gradual_seconds: float = 0.0,
    sequence: bytes | None = None,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build an old-UniLED Zengge RGB color packet."""
    payload = make_control_payload(
        ZENGGE_COLOR_MODE_RGB,
        _byte(red, "red"),
        _byte(green, "green"),
        _byte(blue, "blue"),
        delay_seconds=delay_seconds,
        gradual_seconds=gradual_seconds,
    )
    return make_command_packet(
        key,
        address,
        node_id,
        C_COLOR,
        payload,
        sequence=sequence,
        block_encryptor=block_encryptor,
    )


def build_cct_packet(
    key: bytes,
    address: str,
    node_id: int,
    kelvin: int,
    *,
    level: int = 255,
    delay_seconds: float = 0.0,
    gradual_seconds: float = 0.0,
    sequence: bytes | None = None,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build an old-UniLED Zengge CCT color packet."""
    payload = make_control_payload(
        ZENGGE_COLOR_MODE_CCT,
        kelvin_to_cct_percentage(kelvin),
        _percentage(level, 255, field="level"),
        delay_seconds=delay_seconds,
        gradual_seconds=gradual_seconds,
    )
    return make_command_packet(
        key,
        address,
        node_id,
        C_COLOR,
        payload,
        sequence=sequence,
        block_encryptor=block_encryptor,
    )


def build_white_packet(
    key: bytes,
    address: str,
    node_id: int,
    white: int,
    *,
    delay_seconds: float = 0.0,
    gradual_seconds: float = 0.0,
    sequence: bytes | None = None,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build an old-UniLED Zengge warm-white packet."""
    payload = make_control_payload(
        ZENGGE_COLOR_MODE_WARMWHITE,
        _byte(white, "white"),
        delay_seconds=delay_seconds,
        gradual_seconds=gradual_seconds,
    )
    return make_command_packet(
        key,
        address,
        node_id,
        C_COLOR,
        payload,
        sequence=sequence,
        block_encryptor=block_encryptor,
    )


def build_effect_packet(
    key: bytes,
    address: str,
    node_id: int,
    effect: int,
    *,
    speed: int = 0,
    level: int = 100,
    sequence: bytes | None = None,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build an old-UniLED Zengge effect packet."""
    data = bytes(
        (
            0xFF,
            _byte(effect, "effect"),
            _byte(speed, "speed"),
            _byte(level, "level"),
        )
    )
    return make_command_packet(
        key,
        address,
        node_id,
        C_EFFECT,
        data,
        sequence=sequence,
        block_encryptor=block_encryptor,
    )


def kelvin_to_cct_percentage(kelvin: int) -> int:
    """Convert Kelvin to the old Zengge CCT percentage byte."""
    kelvin = int(kelvin)
    if not ZENGGE_MIN_KELVIN <= kelvin <= ZENGGE_MAX_KELVIN:
        raise ZenggeCryptoError(
            f"kelvin must be between {ZENGGE_MIN_KELVIN} and {ZENGGE_MAX_KELVIN}"
        )
    return round(((kelvin - ZENGGE_MIN_KELVIN) * 100) / _kelvin_range()) & 0xFF


def cct_percentage_to_kelvin(percent: int) -> int:
    """Convert an old Zengge CCT percentage byte into Kelvin."""
    percent = _byte(percent, "percent")
    return ZENGGE_MIN_KELVIN + round((percent * _kelvin_range()) / 100.0)


def decode_zengge_hsv_rgb(hue: int, saturation: int, value: float = 1.0) -> tuple[
    int,
    int,
    int,
]:
    """Decode old-UniLED Zengge HSV bytes into an RGB tuple."""
    hue = _byte(hue, "hue")
    saturation = _byte(saturation, "saturation")
    if not 0.0 <= float(value) <= 1.0:
        raise ZenggeCryptoError("value must be between 0.0 and 1.0")
    return tuple(
        round(part * 255)
        for part in colorsys.hsv_to_rgb(hue / 255, saturation / 63, value)
    )


def parse_zengge_notification_block(
    data: bytes,
    *,
    context: ZenggeNodeContext | None = None,
    previous: ChannelState | None = None,
) -> ChannelState | None:
    """Parse one old-UniLED Zengge five-byte status block."""
    block = ZenggeNotificationBlock.from_bytes(data)
    if block.node_id == ZENGGE_MESH_ADDRESS_NONE:
        return None
    if block.node_id == ZENGGE_MESH_ADDRESS_BRIDGE:
        return ChannelState(
            channel_id=block.node_id,
            extra={
                "node_id": block.node_id,
                "node_kind": ZENGGE_NODE_KIND_BRIDGE,
                "raw": block.raw.hex(),
            },
        )

    context = context or ZenggeNodeContext(node_id=block.node_id)
    connected = block.connected & 0xFF
    power = block.level != 0 if connected != 0 else None
    brightness = _byte_percentage(block.level)
    status = ZENGGE_STATUS_ONLINE if connected else ZENGGE_STATUS_OFFLINE
    supported_modes = _zengge_supported_color_modes(context)
    previous_brightness = (
        previous.brightness
        if previous is not None and previous.brightness is not None
        else 255
    )

    channel = ChannelState(
        channel_id=block.node_id,
        power=power,
        brightness=brightness if power else previous_brightness,
        effect=ZENGGE_EFFECT_SOLID,
        light_mode=_zengge_light_mode_name(block.mode),
        light_mode_number=block.mode,
        extra={
            "node_id": block.node_id,
            "node_kind": zengge_node_kind(context.node_type),
            "node_type": context.node_type,
            "node_wiring": context.node_wiring,
            "node_address": context.address,
            "node_rssi": context.rssi,
            "node_name": context.name,
            "node_area": context.area,
            "status": status,
            "connected": connected,
            "value1": block.value1,
            "value2": block.value2,
            "supported_color_modes": supported_modes,
            "color_mode": COLOR_MODE_BRIGHTNESS,
            "raw": block.raw.hex(),
        },
    )

    if context.node_type == ZENGGE_DEVICE_TYPE_PANEL_RGBCCT:
        channel.power = None
        channel.brightness = None
        channel.effect = None
        channel.extra["node_kind"] = ZENGGE_NODE_KIND_PANEL
        return channel

    if COLOR_MODE_RGB in supported_modes:
        channel.rgb = _previous_rgb(previous)
    if COLOR_MODE_WHITE in supported_modes:
        channel.warm_white = _previous_warm_white(previous)
    if COLOR_MODE_COLOR_TEMP in supported_modes:
        channel.color_temp_kelvin = _previous_color_temp(previous)
        channel.extra["min_color_temp_kelvin"] = ZENGGE_MIN_KELVIN
        channel.extra["max_color_temp_kelvin"] = ZENGGE_MAX_KELVIN

    if power:
        if block.mode == ZENGGE_STATE_MODE_RGB:
            channel.rgb = decode_zengge_hsv_rgb(block.value1, block.value2)
            channel.extra["color_mode"] = COLOR_MODE_RGB
            channel.extra["color_level"] = brightness
        elif block.mode == ZENGGE_STATE_MODE_CCT:
            if context.node_wiring in (
                ZENGGE_WIRING_CONNECTION_CCT,
                ZENGGE_WIRING_CONNECTION_RGB_CCT,
            ):
                channel.color_temp_kelvin = cct_percentage_to_kelvin(block.value1)
                channel.extra["color_mode"] = COLOR_MODE_COLOR_TEMP
            else:
                channel.warm_white = channel.brightness
                channel.extra["color_mode"] = COLOR_MODE_BRIGHTNESS
        elif block.mode == ZENGGE_STATE_MODE_DYNAMIC:
            channel.effect = ZENGGE_EFFECT_UNKNOWN
            channel.effect_type = "dynamic"

    return channel


def parse_zengge_notification_message(
    message: bytes,
    *,
    contexts: Mapping[int, ZenggeNodeContext] | None = None,
    previous: DeviceState | None = None,
) -> DeviceState:
    """Parse a decrypted 20-byte old-UniLED Zengge notification message."""
    raw = bytes(message)
    if len(raw) < 20:
        raise ParseNotificationError("Zengge notification message must be 20 bytes")

    command = raw[7]
    if command != C_NOTIFICATION_RECEIVED:
        raise ParseNotificationError(
            f"unsupported Zengge notification command 0x{command:02x}"
        )

    contexts = contexts or {}
    channels: dict[int, ChannelState] = {}
    for block in (raw[10:15], raw[15:20]):
        node_id = block[0]
        channel = parse_zengge_notification_block(
            block,
            context=contexts.get(node_id),
            previous=previous.channel(node_id) if previous is not None else None,
        )
        if channel is not None:
            channels[channel.channel_id] = channel

    return DeviceState(
        available=True,
        channels=channels,
        diagnostics={
            "mesh_command": command,
            "mesh_uuid": int.from_bytes(raw[3:5], byteorder="little"),
            "response_node_id": raw[8],
            "packet_type": raw[9],
            "notification_blocks": len(channels),
        },
        raw=raw,
    )


def decrypt_packet(
    key: bytes,
    address: str,
    packet: bytes,
    *,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes | None:
    """Decrypt and validate a 20-byte Telink/Zengge notification packet."""
    packet = bytes(packet)
    if len(packet) != 20:
        raise ZenggeCryptoError("mesh notification packet must be 20 bytes")

    address_bytes = _address_bytes(address)
    nonce = bytes(reversed(address_bytes))[0:3] + packet[:5]
    payload = crypt_payload(
        key,
        nonce,
        packet[7:],
        block_encryptor=block_encryptor,
    )
    check = make_checksum(key, nonce, payload, block_encryptor=block_encryptor)
    if check[:2] != packet[5:7]:
        return None
    return packet[:7] + payload


def make_pair_packet(
    mesh_name: bytes,
    mesh_password: bytes,
    session_random: bytes,
    *,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build the Telink/Zengge pairing packet."""
    session_random = bytes(session_random)
    if len(session_random) != 8:
        raise ZenggeCryptoError("session random must be 8 bytes")

    name_pass = _mesh_name_password_xor(mesh_name, mesh_password)
    encrypted = encrypt_block(
        session_random.ljust(16, b"\x00"),
        name_pass,
        block_encryptor=block_encryptor,
    )
    return b"\x0c" + session_random + encrypted[:8]


def make_session_key(
    mesh_name: bytes,
    mesh_password: bytes,
    session_random: bytes,
    response_random: bytes,
    *,
    block_encryptor: BlockEncryptor | None = None,
) -> bytes:
    """Build the Telink/Zengge session key from pairing randoms."""
    session_random = bytes(session_random)
    response_random = bytes(response_random)
    if len(session_random) != 8 or len(response_random) != 8:
        raise ZenggeCryptoError("pairing randoms must be 8 bytes each")

    name_pass = _mesh_name_password_xor(mesh_name, mesh_password)
    return encrypt_block(
        name_pass,
        session_random + response_random,
        block_encryptor=block_encryptor,
    )


def crc16(data: bytes) -> int:
    """Return the old UniLED Telink CRC16 value."""
    poly = (0x0000, 0xA001)
    crc = 0xFFFF
    for value in bytes(data):
        for _ in range(8):
            index = (crc ^ value) & 0x01
            crc = (crc >> 1) ^ poly[index]
            value >>= 1
    return crc


def _byte_percentage(percent: int) -> int:
    return round((_byte(percent, "percent") * 255) / 100.0) & 0xFF


def _previous_rgb(previous: ChannelState | None) -> tuple[int, int, int]:
    if previous is not None and previous.rgb is not None:
        return previous.rgb
    return (0xFF, 0xFF, 0xFF)


def _previous_warm_white(previous: ChannelState | None) -> int:
    if previous is not None and previous.warm_white is not None:
        return previous.warm_white
    return 0xFF


def _previous_color_temp(previous: ChannelState | None) -> int:
    if previous is not None and previous.color_temp_kelvin is not None:
        return previous.color_temp_kelvin
    return ZENGGE_MAX_KELVIN


def _zengge_supported_color_modes(context: ZenggeNodeContext) -> tuple[str, ...]:
    if context.node_type == ZENGGE_DEVICE_TYPE_PANEL_RGBCCT:
        return ()
    if context.node_wiring == ZENGGE_WIRING_CONTROL_RGB_CCT:
        return (COLOR_MODE_RGB, COLOR_MODE_COLOR_TEMP)
    if context.node_wiring == ZENGGE_WIRING_CONTROL_RGB_W:
        return (COLOR_MODE_RGB, COLOR_MODE_WHITE)
    return (COLOR_MODE_BRIGHTNESS,)


def _zengge_light_mode_name(mode: int) -> str:
    if mode == ZENGGE_STATE_MODE_RGB:
        return COLOR_MODE_RGB
    if mode == ZENGGE_STATE_MODE_CCT:
        return COLOR_MODE_COLOR_TEMP
    if mode == ZENGGE_STATE_MODE_DYNAMIC:
        return "dynamic"
    return "other"


def _mesh_name_password_xor(mesh_name: bytes, mesh_password: bytes) -> bytes:
    name = bytes(mesh_name).ljust(16, b"\x00")
    password = bytes(mesh_password).ljust(16, b"\x00")
    return _xor_bytes(name, password)


def _encrypt_reversed_block(
    reversed_key: bytes,
    reversed_block: bytes,
    *,
    block_encryptor: BlockEncryptor | None,
) -> bytes:
    if block_encryptor is not None:
        encrypted = bytes(block_encryptor(reversed_key, reversed_block))
    else:
        if AES is None:
            raise ZenggeCryptoError("pycryptodome is required for Zengge mesh AES")
        encrypted = AES.new(reversed_key, AES.MODE_ECB).encrypt(reversed_block)
    if len(encrypted) != 16:
        raise ZenggeCryptoError("block encryptor must return 16 bytes")
    return encrypted


def _address_bytes(address: str) -> bytes:
    try:
        value = bytes.fromhex(str(address).replace(":", ""))
    except ValueError as ex:
        raise ZenggeCryptoError("mesh address must be a hex MAC address") from ex
    if len(value) != 6:
        raise ZenggeCryptoError("mesh address must contain 6 bytes")
    return value


def _byte(value: int, field: str) -> int:
    value = int(value)
    if not 0 <= value <= 0xFF:
        raise ZenggeCryptoError(f"{field} must be between 0 and 255")
    return value


def _percentage(value: int, whole: int, *, field: str) -> int:
    value = int(value)
    if not 0 <= value <= whole:
        raise ZenggeCryptoError(f"{field} must be between 0 and {whole}")
    return round((100 * value) / whole) & 0xFF


def _kelvin_range() -> int:
    return ZENGGE_MAX_KELVIN - ZENGGE_MIN_KELVIN


def _xor_bytes(left: bytes, right: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(bytes(left), bytes(right), strict=False))
