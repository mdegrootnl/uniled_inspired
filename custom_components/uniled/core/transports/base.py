"""Core transport protocols."""

from __future__ import annotations

from typing import Protocol


class TransportError(RuntimeError):
    """Raised when a transport cannot move bytes."""


class CommandTransport(Protocol):
    """Minimal async byte transport needed by protocol sessions."""

    async def send(self, payload: bytes, *, response: bool = False) -> bytes | None:
        """Send one protocol payload and optionally return a response."""
