"""Data coordinator for UniLED runtime state."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .core import (
    DeviceState,
    ParseNotificationError,
    ProtocolCommandError,
    TransportError,
)
from .core.protocols import ZenggeCryptoError
from .runtime import (
    UniLEDRuntime,
    apply_runtime_state,
    async_refresh_runtime_state,
    async_refresh_zengge_mesh_state,
    mark_runtime_refresh_without_session,
)

_LOGGER = logging.getLogger(__name__)
_REFRESH_TIMEOUT = 5.0


class UniLEDCoordinator(DataUpdateCoordinator[DeviceState]):
    """Coordinate UniLED runtime state for Home Assistant entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry,
        runtime: UniLEDRuntime,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=None,
            always_update=False,
        )
        self.runtime = runtime

    async def _async_update_data(self) -> DeviceState:
        """Refresh and return the current runtime state."""
        if self.runtime.session is None:
            if self.runtime.mesh_connection is not None:
                return await async_refresh_zengge_mesh_state(self.runtime)
            return mark_runtime_refresh_without_session(self.runtime)

        try:
            return await async_refresh_runtime_state(
                self.runtime,
                response_timeout=_REFRESH_TIMEOUT,
            )
        except (ProtocolCommandError, TransportError) as ex:
            self.runtime.state.available = False
            self.runtime.state.diagnostics["last_refresh_error"] = str(ex)
            raise UpdateFailed(str(ex)) from ex

        return self.runtime.state

    def apply_notification(self, data: bytes) -> DeviceState | None:
        """Assemble and parse a raw notification for protocol-backed models."""
        if self.runtime.session is not None:
            state = self.runtime.session.apply_notification(data)
            if state is None:
                return None
            apply_runtime_state(self.runtime, state)
            self.async_set_updated_data(state)
            return state

        protocol = self.runtime.protocol
        if protocol is None:
            return None
        assembler = getattr(self.runtime, "notification_assembler", None)
        if assembler is None:
            assembler = protocol.make_status_assembler()
            self.runtime.notification_assembler = assembler
        payload = assembler.feed(data)
        if payload is None:
            return None
        apply_runtime_state(self.runtime, protocol.parse_status(payload))
        self.async_set_updated_data(self.runtime.state)
        return self.runtime.state

    def apply_mesh_notification(self, data: bytes) -> DeviceState | None:
        """Decrypt and parse a raw Zengge mesh notification."""
        session = self.runtime.mesh_session
        if session is None:
            return None
        try:
            state = session.apply_encrypted_notification(data)
        except (ParseNotificationError, ProtocolCommandError, ZenggeCryptoError) as ex:
            self.runtime.state.diagnostics["last_mesh_notification_error"] = str(ex)
            return None
        if state is None:
            return None
        apply_runtime_state(self.runtime, state)
        self.async_set_updated_data(state)
        return state
