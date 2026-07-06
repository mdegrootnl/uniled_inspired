"""Protocol session for command dispatch and notification parsing."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field

from .protocols import CommandKind, ProtocolCommandError
from .protocols.banlanx_legacy import LegacyProtocol
from .protocols.framing import StatusAssembler
from .state import DeviceState, ParseNotificationError
from .transports import CommandTransport

CommandBuilder = Callable[[], bytes | tuple[bytes, ...]]


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Result of dispatching one high-level command."""

    kind: CommandKind
    payloads: tuple[bytes, ...]
    responses: tuple[bytes | None, ...]


@dataclass(slots=True)
class DeviceSession:
    """Stateful protocol session independent from Home Assistant."""

    protocol: LegacyProtocol
    transport: CommandTransport
    assembler: StatusAssembler | None = None
    state: DeviceState | None = None
    _notification_event: asyncio.Event = field(
        default_factory=asyncio.Event,
        init=False,
        repr=False,
    )
    _dispatch_lock: asyncio.Lock = field(
        default_factory=asyncio.Lock,
        init=False,
        repr=False,
    )

    async def request_state(self) -> CommandResult:
        """Send a state query command."""
        return await self._dispatch(
            CommandKind.STATE_QUERY,
            self.protocol.build_state_query,
            response=True,
        )

    async def refresh_state(
        self, *, response_timeout: float = 5.0
    ) -> DeviceState | None:
        """Request and return current state from response bytes or notification."""
        async with self._dispatch_lock:
            self._notification_event.clear()
            result = await self._dispatch_unlocked(
                CommandKind.STATE_QUERY,
                self.protocol.build_state_query,
                response=True,
            )
            for response in result.responses:
                if response is None:
                    continue
                if state := self.apply_response(response):
                    return state

            if response_timeout <= 0:
                return self.state if self._notification_event.is_set() else None

            try:
                await asyncio.wait_for(
                    self._notification_event.wait(),
                    response_timeout,
                )
            except TimeoutError:
                return None
            return self.state

    async def set_power(self, state: bool, *, channel: int = 0) -> CommandResult:
        """Send a power command."""
        return await self._dispatch(
            CommandKind.POWER,
            lambda: self.protocol.build_power(state, channel=channel),
        )

    async def set_brightness(
        self,
        level: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a brightness command."""
        return await self._dispatch(
            CommandKind.BRIGHTNESS,
            lambda: self.protocol.build_brightness(level, channel=channel),
        )

    async def set_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
    ) -> CommandResult:
        """Send an RGB color command."""
        return await self._dispatch(
            CommandKind.RGB_COLOR,
            lambda: self.protocol.build_rgb_color(
                red,
                green,
                blue,
                channel=channel,
                level=level,
            ),
        )

    async def set_rgb2_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a secondary/matrix RGB color command."""
        return await self._dispatch(
            CommandKind.RGB2_COLOR,
            lambda: self.protocol.build_rgb2_color(
                red,
                green,
                blue,
                channel=channel,
            ),
        )

    async def set_dynamic_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a dynamic-mode RGB tuning command."""
        return await self._dispatch(
            CommandKind.DYNAMIC_RGB_COLOR,
            lambda: self.protocol.build_dynamic_rgb_color(
                red,
                green,
                blue,
                channel=channel,
            ),
        )

    async def set_rgbw_color(
        self,
        red: int,
        green: int,
        blue: int,
        white: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
        static: bool = True,
    ) -> CommandResult:
        """Send an RGBW color command sequence."""
        return await self._dispatch(
            CommandKind.RGBW_COLOR,
            lambda: self.protocol.build_rgbw_color(
                red,
                green,
                blue,
                white,
                channel=channel,
                level=level,
                static=static,
            ),
        )

    async def set_rgbww_color(
        self,
        red: int,
        green: int,
        blue: int,
        cold: int,
        warm: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
        static: bool = True,
    ) -> CommandResult:
        """Send an RGBWW color command sequence."""
        return await self._dispatch(
            CommandKind.RGBWW_COLOR,
            lambda: self.protocol.build_rgbww_color(
                red,
                green,
                blue,
                cold,
                warm,
                channel=channel,
                level=level,
                static=static,
            ),
        )

    async def set_white_level(
        self,
        level: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a white-level command."""
        return await self._dispatch(
            CommandKind.WHITE_LEVEL,
            lambda: self.protocol.build_white_level(level, channel=channel),
        )

    async def set_white_brightness(
        self,
        level: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a white brightness payload for devices already in white mode."""
        return await self._dispatch(
            CommandKind.WHITE_LEVEL,
            lambda: self.protocol.build_white_brightness(level, channel=channel),
        )

    async def set_cct_color(
        self,
        cold: int,
        warm: int,
        *,
        channel: int = 0,
        static: bool = True,
    ) -> CommandResult:
        """Send a CCT color command."""
        return await self._dispatch(
            CommandKind.CCT_COLOR,
            lambda: self.protocol.build_cct_color(
                cold,
                warm,
                channel=channel,
                static=static,
            ),
        )

    async def set_effect(self, effect: int, *, channel: int = 0) -> CommandResult:
        """Send an effect command."""
        return await self._dispatch(
            CommandKind.EFFECT,
            lambda: self.protocol.build_effect(effect, channel=channel),
        )

    async def set_light_mode(
        self,
        mode: int,
        effect: int | None = None,
    ) -> CommandResult:
        """Send a light-mode command for protocols that support it."""
        builder = getattr(self.protocol, "build_light_mode", None)
        if builder is None:
            raise ProtocolCommandError(
                f"{self.protocol.name} does not implement light mode"
            )
        return await self._dispatch(
            CommandKind.LIGHT_MODE,
            lambda: builder(mode) if effect is None else builder(mode, effect),
        )

    async def set_effect_speed(
        self,
        speed: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send an effect-speed command."""
        return await self._dispatch(
            CommandKind.EFFECT_SPEED,
            lambda: self.protocol.build_effect_speed(speed, channel=channel),
        )

    async def set_effect_length(
        self,
        length: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send an effect-length command."""
        return await self._dispatch(
            CommandKind.EFFECT_LENGTH,
            lambda: self.protocol.build_effect_length(length, channel=channel),
        )

    async def set_effect_direction(
        self,
        state: bool,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send an effect-direction command."""
        return await self._dispatch(
            CommandKind.EFFECT_DIRECTION,
            lambda: self.protocol.build_effect_direction(state, channel=channel),
        )

    async def set_effect_loop(self, state: bool) -> CommandResult:
        """Send an effect-loop command."""
        return await self._dispatch(
            CommandKind.EFFECT_LOOP,
            lambda: self.protocol.build_effect_loop(state),
        )

    async def set_scene_loop(self, state: bool) -> CommandResult:
        """Send a scene-loop command."""
        return await self._dispatch(
            CommandKind.SCENE_LOOP,
            lambda: self.protocol.build_scene_loop(state),
        )

    async def set_audio_input(
        self,
        value: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send an audio-input command."""
        return await self._dispatch(
            CommandKind.AUDIO_INPUT,
            lambda: self.protocol.build_audio_input(value, channel=channel),
        )

    async def set_sensitivity(
        self,
        value: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send an audio-sensitivity command."""
        return await self._dispatch(
            CommandKind.SENSITIVITY,
            lambda: self.protocol.build_sensitivity(value, channel=channel),
        )

    async def set_onoff_config(
        self,
        effect: int,
        speed: int,
        pixels: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send an on/off animation configuration command."""
        return await self._dispatch(
            CommandKind.ONOFF_CONFIG,
            lambda: self.protocol.build_onoff_config(
                effect,
                speed,
                pixels,
                channel=channel,
            ),
        )

    async def set_coexistence(
        self,
        state: bool,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a color/white coexistence command."""
        return await self._dispatch(
            CommandKind.COEXISTENCE,
            lambda: self.protocol.build_coexistence(state, channel=channel),
        )

    async def set_on_power(
        self,
        value: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a power-restore behavior command."""
        return await self._dispatch(
            CommandKind.ON_POWER,
            lambda: self.protocol.build_on_power(value, channel=channel),
        )

    async def set_effect_play(
        self,
        state: bool,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send an effect play/pause command."""
        return await self._dispatch(
            CommandKind.EFFECT_PLAY,
            lambda: self.protocol.build_effect_play(state, channel=channel),
        )

    async def set_light_type(
        self,
        light_type: int,
        chip_order: int,
        mode: int,
        effect: int,
        *,
        power: bool = False,
        refresh: bool = False,
        channel: int = 0,
    ) -> CommandResult:
        """Send a light-type reconfiguration command sequence."""
        return await self._dispatch(
            CommandKind.LIGHT_TYPE,
            lambda: self.protocol.build_light_type(
                light_type,
                chip_order,
                mode,
                effect,
                power=power,
                refresh=refresh,
                channel=channel,
            ),
        )

    async def set_chip_order(
        self,
        value: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a chip-order command."""
        return await self._dispatch(
            CommandKind.CHIP_ORDER,
            lambda: self.protocol.build_chip_order(value, channel=channel),
        )

    async def set_chip_type(
        self,
        value: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a chip-type command."""
        return await self._dispatch(
            CommandKind.CHIP_TYPE,
            lambda: self.protocol.build_chip_type(value, channel=channel),
        )

    async def set_segment_count(
        self,
        segments: int,
        pixels: int | None = None,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a segment-count configuration command."""
        if pixels is None:
            pixels = _state_diagnostic_int(self.state, "segment_pixels")
        return await self._dispatch(
            CommandKind.SEGMENT_COUNT,
            lambda: self.protocol.build_segment_count(
                segments,
                pixels,
                channel=channel,
            ),
        )

    async def set_segment_pixels(
        self,
        pixels: int,
        *,
        segment_count: int | None = None,
        channel: int = 0,
    ) -> CommandResult:
        """Send a segment-pixel configuration command."""
        if (
            segment_count is None
            and self.state is not None
            and isinstance(self.state.diagnostics.get("segment_count"), int)
        ):
            segment_count = _state_diagnostic_int(self.state, "segment_count")
        return await self._dispatch(
            CommandKind.SEGMENT_PIXELS,
            lambda: self.protocol.build_segment_pixels(
                pixels,
                segment_count=segment_count,
                channel=channel,
            ),
        )

    async def set_scene(
        self,
        scene: int,
        *,
        channel: int = 0,
    ) -> CommandResult:
        """Send a scene recall command."""
        return await self._dispatch(
            CommandKind.SCENE,
            lambda: self.protocol.build_scene(scene, channel=channel),
        )

    def apply_notification(self, data: bytes) -> DeviceState | None:
        """Assemble and parse one raw notification."""
        if self.assembler is None:
            self.assembler = self.protocol.make_status_assembler()
        payload = self.assembler.feed(data)
        if payload is None:
            return None
        self.state = self.protocol.parse_status(payload)
        self._notification_event.set()
        return self.state

    def apply_response(self, data: bytes) -> DeviceState | None:
        """Parse direct response bytes as notification or raw protocol status."""
        try:
            if state := self.apply_notification(data):
                return state
        except (ParseNotificationError, ProtocolCommandError, ValueError):
            pass

        try:
            self.state = self.protocol.parse_status(data)
        except (ParseNotificationError, ProtocolCommandError, ValueError):
            return None
        self._notification_event.set()
        return self.state

    async def _dispatch(
        self,
        kind: CommandKind,
        builder: CommandBuilder,
        *,
        response: bool = False,
    ) -> CommandResult:
        async with self._dispatch_lock:
            return await self._dispatch_unlocked(kind, builder, response=response)

    async def _dispatch_unlocked(
        self,
        kind: CommandKind,
        builder: CommandBuilder,
        *,
        response: bool = False,
    ) -> CommandResult:
        payloads = _as_payloads(builder())
        responses = []
        for payload in payloads:
            responses.append(await self.transport.send(payload, response=response))
        return CommandResult(
            kind=kind,
            payloads=payloads,
            responses=tuple(responses),
        )


def _as_payloads(payload: bytes | tuple[bytes, ...]) -> tuple[bytes, ...]:
    if isinstance(payload, bytes):
        return (payload,)
    return tuple(payload)


def _state_diagnostic_int(state: DeviceState | None, key: str) -> int:
    if state is None:
        raise ProtocolCommandError(f"{key} is required before this command")
    value = state.diagnostics.get(key)
    if not isinstance(value, int):
        raise ProtocolCommandError(f"{key} is required before this command")
    return value
