"""Notification frame assembly helpers for protocol parsers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..state import ParseNotificationError


class StatusAssembler(Protocol):
    """Stateful collector for status notification packets."""

    def feed(self, data: bytes) -> bytes | None:
        """Feed one notification and return a full payload when complete."""

    def reset(self) -> None:
        """Discard any buffered partial payload."""


@dataclass(slots=True)
class HeaderedStatusAssembler:
    """Assemble packets with a two-byte family marker and five-byte header."""

    family: str
    magic: bytes
    _packet_number: int | None = field(default=None, init=False)
    _message_length: int | None = field(default=None, init=False)
    _buffer: bytearray = field(default_factory=bytearray, init=False)

    def feed(self, data: bytes) -> bytes | None:
        """Feed one SP601/SP60x/BanlanX2 notification packet."""
        packet = bytes(data)
        if len(packet) < 5:
            self._fail(f"expected at least 5 bytes, got {len(packet)}")
        if packet[:2] != self.magic:
            self._fail(
                "expected header "
                f"{self.magic.hex()}, got {packet[:2].hex()}"
            )

        packet_number = packet[2]
        message_length = packet[3]
        payload_length = packet[4]
        payload = packet[5:]
        self._check_payload_size(payload, payload_length)

        if packet_number == 1:
            self.reset()
            return self._start(packet_number, message_length, payload)

        return self._append(packet_number, message_length, payload)

    def reset(self) -> None:
        """Discard buffered partial payload."""
        self._packet_number = None
        self._message_length = None
        self._buffer.clear()

    def _start(
        self, packet_number: int, message_length: int, payload: bytes
    ) -> bytes | None:
        if len(payload) > message_length:
            self._fail(
                f"payload length {len(payload)} exceeds message length "
                f"{message_length}"
            )
        if len(payload) == message_length:
            return payload
        self._packet_number = packet_number
        self._message_length = message_length
        self._buffer.extend(payload)
        return None

    def _append(
        self, packet_number: int, message_length: int, payload: bytes
    ) -> bytes | None:
        if self._packet_number is None or self._message_length is None:
            self._fail("continuation packet without an initial packet")
        if packet_number != self._packet_number + 1:
            self._fail(
                f"expected packet {self._packet_number + 1}, got {packet_number}"
            )
        if message_length != self._message_length:
            self._fail(
                f"expected message length {self._message_length}, "
                f"got {message_length}"
            )

        self._buffer.extend(payload)
        if len(self._buffer) > self._message_length:
            self._fail(
                f"assembled payload length {len(self._buffer)} exceeds "
                f"message length {self._message_length}"
            )
        if len(self._buffer) < self._message_length:
            self._packet_number = packet_number
            return None

        result = bytes(self._buffer)
        self.reset()
        return result

    def _check_payload_size(self, payload: bytes, expected: int) -> None:
        if len(payload) != expected:
            self._fail(f"expected payload length {expected}, got {len(payload)}")

    def _fail(self, message: str) -> None:
        self.reset()
        raise ParseNotificationError(f"{self.family} notification: {message}")


@dataclass(slots=True)
class IndexedStatusAssembler:
    """Assemble BanlanX3 packets with short first/continuation headers."""

    family: str
    _packet_number: int | None = field(default=None, init=False)
    _message_length: int | None = field(default=None, init=False)
    _buffer: bytearray = field(default_factory=bytearray, init=False)

    def feed(self, data: bytes) -> bytes | None:
        """Feed one BanlanX3 notification packet."""
        packet = bytes(data)
        if len(packet) < 2:
            self._fail(f"expected at least 2 bytes, got {len(packet)}")

        packet_number = packet[0]
        if packet_number == 1:
            if len(packet) < 3:
                self._fail("initial packet is missing message lengths")
            message_length = packet[1]
            payload = packet[3:]
            self._check_payload_size(payload, packet[2])
            self.reset()
            return self._start(packet_number, message_length, payload)

        payload = packet[2:]
        self._check_payload_size(payload, packet[1])
        return self._append(packet_number, payload)

    def reset(self) -> None:
        """Discard buffered partial payload."""
        self._packet_number = None
        self._message_length = None
        self._buffer.clear()

    def _start(
        self, packet_number: int, message_length: int, payload: bytes
    ) -> bytes | None:
        if len(payload) > message_length:
            self._fail(
                f"payload length {len(payload)} exceeds message length "
                f"{message_length}"
            )
        if len(payload) == message_length:
            return payload
        self._packet_number = packet_number
        self._message_length = message_length
        self._buffer.extend(payload)
        return None

    def _append(self, packet_number: int, payload: bytes) -> bytes | None:
        if self._packet_number is None or self._message_length is None:
            self._fail("continuation packet without an initial packet")
        if packet_number != self._packet_number + 1:
            self._fail(
                f"expected packet {self._packet_number + 1}, got {packet_number}"
            )

        self._buffer.extend(payload)
        if len(self._buffer) > self._message_length:
            self._fail(
                f"assembled payload length {len(self._buffer)} exceeds "
                f"message length {self._message_length}"
            )
        if len(self._buffer) < self._message_length:
            self._packet_number = packet_number
            return None

        result = bytes(self._buffer)
        self.reset()
        return result

    def _check_payload_size(self, payload: bytes, expected: int) -> None:
        if len(payload) != expected:
            self._fail(f"expected payload length {expected}, got {len(payload)}")

    def _fail(self, message: str) -> None:
        self.reset()
        raise ParseNotificationError(f"{self.family} notification: {message}")


@dataclass(slots=True)
class DirectStatusAssembler:
    """Pass through complete notifications that are not segmented."""

    family: str

    def feed(self, data: bytes) -> bytes:
        """Return one complete status packet."""
        return bytes(data)

    def reset(self) -> None:
        """Direct packets have no buffered state."""
