"""Legacy BanlanX BLE command builders ported from UniLED parity behavior."""

from __future__ import annotations

from dataclasses import dataclass

from ..catalog import ProtocolFamily
from ..options import (
    banlanx6xx_effect_attributes_for_state,
    banlanx6xx_effect_name_for_state,
    banlanx6xx_effect_type_for_mode,
    banlanx6xx_light_mode_name,
    banlanx6xx_light_type_capabilities,
    banlanx6xx_light_type_has_coexistence,
    legacy_v23_model_has_audio_controls,
    legacy_v23_model_has_white_channel,
    select_option_map,
)
from ..state import ChannelState, DeviceState, ParseNotificationError
from .base import ProtocolCommandError, UnsupportedCommand, byte_value, ranged_value
from .base import rgb_value as _rgb_value
from .framing import (
    Custom5xxStatusAssembler,
    DirectStatusAssembler,
    HeaderedStatusAssembler,
    IndexedStatusAssembler,
    StatusAssembler,
)

_BANLANX2_EFFECT_WHITE = 0xBF
_BANLANX3_EFFECT_WHITE = 0xCC
_BANLANX_V23_AUTO_DYNAMIC_MODE = 0x01
_BANLANX_V23_AUTO_SOUND_MODE = 0x02
_BANLANX6XX_LOOPABLE_MODES = frozenset({0x03, 0x04, 0x05, 0x06})
_LED_CHORD_FX_DYNAMIC = 0x01
_LED_CHORD_FX_STATIC = 0xB5
_LED_CHORD_FX_STRIP = 0xBE
_LED_CHORD_FX_MATRIX = 0xDC
_LED_CHORD_LIGHT_MODE_SINGULAR = 0x00
_LED_CHORD_LIGHT_MODE_AUTO_DYNAMIC = 0x01
_LED_CHORD_LIGHT_MODE_AUTO_STRIP = 0x02
_LED_CHORD_LIGHT_MODE_AUTO_MATRIX = 0x03
_LED_CHORD_EFFECT_SPEED_MAX = 186
_LED_CHORD_SENSITIVITY_MAX = 165
_LED_CHORD_MAX_SEGMENT_COUNT = 64
_LED_CHORD_MAX_SEGMENT_PIXELS = 150
_LED_CHORD_MAX_TOTAL_PIXELS = 960
_LED_HUE_EFFECT_TYPE_AUTO = 0x00
_LED_HUE_EFFECT_TYPE_DYNAMIC = 0x01
_LED_HUE_EFFECT_TYPE_STATIC = 0x79
_LED_HUE_EFFECT_SPEED_MAX = 186
_LED_HUE_MAX_SEGMENT_PIXELS = 1024
_LED_HUE_AUTO_CYCLE_EFFECT = "Auto Cycle FX's"
_LEGACY_LED_CHIP_TYPE_MAX = 0x1A

_LED_CHORD_LIGHT_MODES = {
    _LED_CHORD_LIGHT_MODE_SINGULAR: "Single FX",
    _LED_CHORD_LIGHT_MODE_AUTO_DYNAMIC: "Cycle Dynamic FX's",
    _LED_CHORD_LIGHT_MODE_AUTO_STRIP: "Cycle Strip FX's",
    _LED_CHORD_LIGHT_MODE_AUTO_MATRIX: "Cycle Matrix FX's",
}
_LED_CHORD_EFFECTS = {
    _LED_CHORD_FX_STATIC: "Solid",
    **{
        _LED_CHORD_FX_DYNAMIC + index: f"Dynamic FX {index + 1}"
        for index in range(180)
    },
    **{
        _LED_CHORD_FX_STRIP + index: f"Sound - Strip FX {index + 1}"
        for index in range(18)
    },
    **{
        _LED_CHORD_FX_MATRIX + index: f"Sound - Matrix FX {index + 1}"
        for index in range(30)
    },
}
_LED_HUE_EFFECTS = {
    _LED_HUE_EFFECT_TYPE_STATIC: "Solid",
    **{
        _LED_HUE_EFFECT_TYPE_DYNAMIC + index: f"Pattern {index + 1}"
        for index in range(_LED_HUE_EFFECT_TYPE_STATIC - 1)
    },
}


@dataclass(frozen=True, slots=True)
class LegacyProtocol:
    """Base for stateless legacy command builders."""

    name: str

    def build_state_query(self) -> bytes:
        """Build a state query command."""
        raise UnsupportedCommand(f"{self.name} does not implement state query")

    def build_power(
        self, state: bool, *, channel: int = 0
    ) -> bytes | tuple[bytes, ...]:
        """Build a power command."""
        raise UnsupportedCommand(f"{self.name} does not implement power")

    def build_brightness(
        self,
        level: int,
        *,
        channel: int = 0,
    ) -> bytes | tuple[bytes, ...]:
        """Build a brightness command."""
        raise UnsupportedCommand(f"{self.name} does not implement brightness")

    def build_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
    ) -> tuple[bytes, ...]:
        """Build an RGB color command."""
        raise UnsupportedCommand(f"{self.name} does not implement RGB")

    def build_rgb2_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
    ) -> bytes:
        """Build a secondary/matrix RGB color command."""
        raise UnsupportedCommand(f"{self.name} does not implement RGB2")

    def build_dynamic_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
    ) -> bytes:
        """Build a dynamic-mode RGB tuning command."""
        raise UnsupportedCommand(f"{self.name} does not implement dynamic RGB")

    def build_rgbw_color(
        self,
        red: int,
        green: int,
        blue: int,
        white: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
        static: bool = True,
    ) -> tuple[bytes, ...]:
        """Build an RGBW color command sequence."""
        raise UnsupportedCommand(f"{self.name} does not implement RGBW")

    def build_rgbww_color(
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
    ) -> tuple[bytes, ...]:
        """Build an RGBWW color command sequence."""
        raise UnsupportedCommand(f"{self.name} does not implement RGBWW")

    def build_white_level(
        self,
        level: int,
        *,
        channel: int = 0,
    ) -> bytes | tuple[bytes, ...]:
        """Build a white-level command."""
        raise UnsupportedCommand(f"{self.name} does not implement white level")

    def build_white_brightness(
        self,
        level: int,
        *,
        channel: int = 0,
    ) -> bytes | tuple[bytes, ...]:
        """Build the brightness payload used while the device is already white."""
        return self.build_white_level(level, channel=channel)

    def build_cct_color(
        self,
        cold: int,
        warm: int,
        *,
        channel: int = 0,
        static: bool = True,
    ) -> bytes:
        """Build a CCT channel command."""
        raise UnsupportedCommand(f"{self.name} does not implement CCT")

    def build_effect(self, effect: int, *, channel: int = 0) -> bytes:
        """Build an effect command."""
        raise UnsupportedCommand(f"{self.name} does not implement effects")

    def build_effect_speed(self, speed: int, *, channel: int = 0) -> bytes:
        """Build an effect speed command."""
        raise UnsupportedCommand(f"{self.name} does not implement effect speed")

    def build_effect_length(self, length: int, *, channel: int = 0) -> bytes:
        """Build an effect length command."""
        raise UnsupportedCommand(f"{self.name} does not implement effect length")

    def build_effect_direction(self, state: bool, *, channel: int = 0) -> bytes:
        """Build an effect direction command."""
        raise UnsupportedCommand(f"{self.name} does not implement effect direction")

    def build_effect_loop(self, state: bool) -> bytes:
        """Build an effect loop command."""
        raise UnsupportedCommand(f"{self.name} does not implement effect loop")

    def build_scene_loop(self, state: bool) -> bytes:
        """Build a scene-loop command."""
        raise UnsupportedCommand(f"{self.name} does not implement scene loop")

    def build_audio_input(self, value: int, *, channel: int = 0) -> bytes:
        """Build an audio input command."""
        raise UnsupportedCommand(f"{self.name} does not implement audio input")

    def build_sensitivity(self, value: int, *, channel: int = 0) -> bytes:
        """Build an audio sensitivity command."""
        raise UnsupportedCommand(f"{self.name} does not implement sensitivity")

    def build_onoff_config(
        self,
        effect: int,
        speed: int,
        pixels: int,
        *,
        channel: int = 0,
    ) -> bytes:
        """Build an on/off animation configuration command."""
        raise UnsupportedCommand(f"{self.name} does not implement on/off config")

    def build_coexistence(self, state: bool, *, channel: int = 0) -> bytes:
        """Build a color/white coexistence command."""
        raise UnsupportedCommand(f"{self.name} does not implement coexistence")

    def build_on_power(self, value: int, *, channel: int = 0) -> bytes:
        """Build a power-restore behavior command."""
        raise UnsupportedCommand(f"{self.name} does not implement on-power state")

    def build_effect_play(self, state: bool, *, channel: int = 0) -> bytes:
        """Build an effect play/pause command."""
        raise UnsupportedCommand(f"{self.name} does not implement effect play")

    def build_light_type(
        self,
        light_type: int,
        chip_order: int,
        mode: int,
        effect: int,
        *,
        power: bool = False,
        refresh: bool = False,
        channel: int = 0,
    ) -> tuple[bytes, ...]:
        """Build a light-type reconfiguration command sequence."""
        raise UnsupportedCommand(f"{self.name} does not implement light type")

    def build_chip_order(self, value: int, *, channel: int = 0) -> bytes:
        """Build a chip-order command."""
        raise UnsupportedCommand(f"{self.name} does not implement chip order")

    def build_chip_type(self, value: int, *, channel: int = 0) -> bytes:
        """Build a chip-type command."""
        raise UnsupportedCommand(f"{self.name} does not implement chip type")

    def build_segment_count(
        self,
        segments: int,
        pixels: int | None = None,
        *,
        channel: int = 0,
    ) -> bytes:
        """Build a segment-count configuration command."""
        raise UnsupportedCommand(f"{self.name} does not implement segment count")

    def build_segment_pixels(
        self,
        pixels: int,
        *,
        segment_count: int | None = None,
        channel: int = 0,
    ) -> bytes:
        """Build a segment-pixel configuration command."""
        raise UnsupportedCommand(f"{self.name} does not implement segment pixels")

    def build_scene(self, scene: int, *, channel: int = 0) -> bytes:
        """Build a scene recall command."""
        raise UnsupportedCommand(f"{self.name} does not implement scenes")

    def parse_status(self, data: bytes) -> DeviceState:
        """Parse a raw status notification payload."""
        raise UnsupportedCommand(f"{self.name} does not implement status parsing")

    def make_status_assembler(self) -> StatusAssembler:
        """Create a stateful status notification assembler."""
        raise UnsupportedCommand(
            f"{self.name} does not implement notification assembly"
        )


@dataclass(frozen=True, slots=True)
class BanlanX601Protocol(LegacyProtocol):
    """SP601E command builder."""

    name: str = "banlanx_601"
    channels: int = 2

    def build_state_query(self) -> bytes:
        return bytes([0xAA, 0x2F, 0x00])

    def build_power(
        self, state: bool, *, channel: int = 0
    ) -> bytes | tuple[bytes, ...]:
        payloads = tuple(
            bytes([0xAA, 0x22, 0x02, index, _bool(state)])
            for index in self._channel_indices(channel)
        )
        return payloads[0] if len(payloads) == 1 else payloads

    def build_brightness(
        self,
        level: int,
        *,
        channel: int = 0,
    ) -> bytes | tuple[bytes, ...]:
        level = byte_value(level, field="level")
        payloads = tuple(
            bytes([0xAA, 0x25, 0x02, index, level])
            for index in self._channel_indices(channel)
        )
        return payloads[0] if len(payloads) == 1 else payloads

    def build_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
    ) -> tuple[bytes, ...]:
        red, green, blue = _rgb_value(red, green, blue)
        level = byte_value(level, field="level")
        return tuple(
            bytes(
                [
                    0xAA,
                    0x29,
                    0x05,
                    index,
                    red,
                    green,
                    blue,
                    level,
                ]
            )
            for index in self._channel_indices(channel)
        )

    def build_effect(self, effect: int, *, channel: int = 0) -> bytes:
        if int(channel) == 0:
            raise ProtocolCommandError(
                "effect commands require a physical output channel"
            )
        return bytes(
            [0xAA, 0x23, 0x02, self._physical_channel_index(channel), _effect(effect)]
        )

    def build_effect_speed(self, speed: int, *, channel: int = 0) -> bytes:
        return bytes(
            [
                0xAA,
                0x26,
                0x02,
                self._physical_channel_index(channel),
                _effect_speed(speed),
            ]
        )

    def build_effect_length(self, length: int, *, channel: int = 0) -> bytes:
        return bytes(
            [
                0xAA,
                0x27,
                0x02,
                self._physical_channel_index(channel),
                _effect_length_150(length),
            ]
        )

    def build_effect_direction(self, state: bool, *, channel: int = 0) -> bytes:
        return bytes(
            [0xAA, 0x2A, 0x02, self._physical_channel_index(channel), _bool(state)]
        )

    def build_scene_loop(self, state: bool) -> bytes:
        return bytes([0xAA, 0x30, 0x01, _bool(state)])

    def build_audio_input(self, value: int, *, channel: int = 0) -> bytes:
        return bytes(
            [0xAA, 0x28, 0x02, self._physical_channel_index(channel), _audio(value)]
        )

    def build_sensitivity(self, value: int, *, channel: int = 0) -> bytes:
        return bytes(
            [
                0xAA,
                0x2B,
                0x02,
                self._physical_channel_index(channel),
                _sensitivity(value),
            ]
        )

    def build_chip_order(self, value: int, *, channel: int = 0) -> bytes:
        return bytes(
            [
                0xAA,
                0x24,
                0x02,
                self._physical_channel_index(channel),
                byte_value(value, field="chip order"),
            ]
        )

    def build_scene(self, scene: int, *, channel: int = 0) -> bytes:
        return bytes([0xAA, 0x2E, 0x01, _scene_slot(scene)])

    def parse_status(self, data: bytes) -> DeviceState:
        """Parse a combined SP601E status payload with one or more channels."""
        state = _parse_chunked_status(
            self.name,
            data,
            channel_size=11,
            channels=self.channels,
            parser=self.parse_channel_status,
        )
        _apply_sp601_tail(state)
        return state

    def make_status_assembler(self) -> StatusAssembler:
        """Create an assembler for SP601E segmented notifications."""
        return HeaderedStatusAssembler(self.name, magic=b"\x53\x43")

    def parse_channel_status(self, data: bytes, *, channel: int = 1) -> ChannelState:
        """Parse one SP601E channel status block."""
        _require_length(self.name, data, 11)
        return ChannelState(
            channel_id=channel,
            power=data[0] != 0,
            effect=_effect_name(ProtocolFamily.BANLANX_601, data[1]),
            effect_number=data[1],
            effect_type=_legacy_effect_type(ProtocolFamily.BANLANX_601, data[1]),
            chip_order=data[2],
            brightness=data[3],
            effect_speed=data[4],
            effect_length=data[5],
            effect_direction=bool(data[6]),
            rgb=(data[7], data[8], data[9]),
            sensitivity=data[10],
        )

    def _channel_indices(self, channel: int) -> tuple[int, ...]:
        channel = int(channel)
        if channel == 0:
            return tuple(range(self.channels))
        return (self._physical_channel_index(channel),)

    def _physical_channel_index(self, channel: int) -> int:
        channel = int(channel)
        if not 1 <= channel <= self.channels:
            raise ProtocolCommandError(
                f"channel must be 1..{self.channels} for output-scoped commands"
            )
        return channel - 1


@dataclass(frozen=True, slots=True)
class BanlanX60xProtocol(LegacyProtocol):
    """SP602E/SP608E command builder."""

    name: str = "banlanx_60x"
    channels: int = 8
    triggers: int = 4

    def build_state_query(self) -> bytes:
        return bytes([0x88, 0x8F, 0x00])

    def build_power(self, state: bool, *, channel: int = 0) -> bytes:
        return bytes([0x88, 0x82, 0x02, self._channel_mask(channel), _bool(state)])

    def build_brightness(self, level: int, *, channel: int = 0) -> bytes:
        return bytes(
            [
                0x88,
                0x85,
                0x02,
                self._channel_mask(channel),
                byte_value(level, field="level"),
            ]
        )

    def build_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
    ) -> tuple[bytes, ...]:
        red, green, blue = _rgb_value(red, green, blue)
        return (
            bytes(
                [
                    0x88,
                    0x89,
                    0x05,
                    self._channel_mask(channel),
                    red,
                    green,
                    blue,
                    byte_value(level, field="level"),
                ]
            ),
        )

    def build_effect(self, effect: int, *, channel: int = 0) -> bytes:
        if int(channel) == 0:
            raise ProtocolCommandError(
                "effect commands require a physical output channel"
            )
        return bytes([0x88, 0x83, 0x02, self._channel_mask(channel), _effect(effect)])

    def build_effect_speed(self, speed: int, *, channel: int = 0) -> bytes:
        return bytes(
            [
                0x88,
                0x86,
                0x02,
                self._physical_channel_mask(channel),
                _effect_speed(speed),
            ]
        )

    def build_effect_length(self, length: int, *, channel: int = 0) -> bytes:
        length = ranged_value(
            length, field="effect length", minimum=1, maximum=240
        ).to_bytes(2, "big")
        return bytes(
            [
                0x88,
                0x87,
                0x03,
                self._physical_channel_mask(channel),
                length[0],
                length[1],
            ]
        )

    def build_effect_direction(self, state: bool, *, channel: int = 0) -> bytes:
        return bytes(
            [0x88, 0x8A, 0x02, self._physical_channel_mask(channel), _bool(state)]
        )

    def build_scene_loop(self, state: bool) -> bytes:
        return bytes([0x88, 0x90, 0x01, _bool(state)])

    def build_audio_input(self, value: int, *, channel: int = 0) -> bytes:
        return bytes([0x88, 0x88, 0x02, self._channel_mask(channel), _audio(value)])

    def build_sensitivity(self, value: int, *, channel: int = 0) -> bytes:
        return bytes(
            [0x88, 0x8B, 0x02, self._channel_mask(channel), _sensitivity(value)]
        )

    def build_chip_order(self, value: int, *, channel: int = 0) -> bytes:
        return bytes(
            [
                0x88,
                0x84,
                0x02,
                self._physical_channel_mask(channel),
                byte_value(value, field="chip order"),
            ]
        )

    def build_scene(self, scene: int, *, channel: int = 0) -> bytes:
        return bytes([0x88, 0x8E, 0x01, _scene_slot(scene)])

    def parse_status(self, data: bytes) -> DeviceState:
        """Parse a combined SP602E/SP608E status payload."""
        state = _parse_chunked_status(
            self.name,
            data,
            channel_size=11,
            channels=self.channels,
            parser=self.parse_channel_status,
        )
        _apply_sp60x_tail(state, triggers=self.triggers)
        return state

    def make_status_assembler(self) -> StatusAssembler:
        """Create an assembler for SP602E/SP608E segmented notifications."""
        return HeaderedStatusAssembler(self.name, magic=b"\x36\x38")

    def parse_channel_status(self, data: bytes, *, channel: int = 1) -> ChannelState:
        """Parse one SP602E/SP608E channel status block."""
        _require_length(self.name, data, 11)
        return ChannelState(
            channel_id=channel,
            power=data[0] != 0,
            effect=_effect_name(ProtocolFamily.BANLANX_60X, data[1]),
            effect_number=data[1],
            effect_type=_legacy_effect_type(ProtocolFamily.BANLANX_60X, data[1]),
            chip_order=data[2],
            brightness=data[3],
            effect_speed=data[4],
            effect_length=int.from_bytes(data[5:7], "big"),
            effect_direction=bool(data[7]),
            rgb=(data[8], data[9], data[10]),
        )

    def _channel_mask(self, channel: int) -> int:
        channel = int(channel)
        if channel == 0:
            return 0xFF
        if not 1 <= channel <= self.channels:
            raise ProtocolCommandError(f"channel must be 0..{self.channels}")
        return 1 << (channel - 1)

    def _physical_channel_mask(self, channel: int) -> int:
        channel = int(channel)
        if not 1 <= channel <= self.channels:
            raise ProtocolCommandError(
                f"channel must be 1..{self.channels} for output-scoped commands"
            )
        return 1 << (channel - 1)


@dataclass(frozen=True, slots=True)
class BanlanX2Protocol(LegacyProtocol):
    """SP611E/SP616E/SP617E/SP620E/SP621E command builder."""

    name: str = "banlanx_v2"
    model_name: str | None = None
    color_cap: int | None = None
    spec_functions: int | None = None

    def build_state_query(self) -> bytes:
        return bytes([0xA0, 0x70, 0x00])

    def build_power(self, state: bool, *, channel: int = 0) -> bytes:
        return bytes([0xA0, 0x62, 0x01, _bool(state)])

    def build_brightness(self, level: int, *, channel: int = 0) -> bytes:
        return bytes([0xA0, 0x66, 0x01, byte_value(level, field="level")])

    def build_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
    ) -> tuple[bytes, ...]:
        red, green, blue = _rgb_value(red, green, blue)
        return (
            bytes(
                [
                    0xA0,
                    0x69,
                    0x04,
                    red,
                    green,
                    blue,
                    byte_value(level, field="level"),
                ]
            ),
    )

    def build_effect(self, effect: int, *, channel: int = 0) -> bytes:
        return bytes(
            [0xA0, 0x63, 0x01, self._supported_select_value("effect", effect)]
        )

    def build_rgbw_color(
        self,
        red: int,
        green: int,
        blue: int,
        white: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
        static: bool = True,
    ) -> tuple[bytes, ...]:
        if not self._has_white_channel():
            raise ProtocolCommandError(
                f"{self.model_name or self.name} does not support white level"
            )
        return (
            *self.build_rgb_color(
                red,
                green,
                blue,
                channel=channel,
                level=level,
            ),
            bytes([0xA0, 0x76, 0x02, byte_value(white, field="white"), 0x00]),
        )

    def build_white_level(self, level: int, *, channel: int = 0) -> tuple[bytes, ...]:
        if not self._has_white_channel():
            raise ProtocolCommandError(
                f"{self.model_name or self.name} does not support white level"
            )
        return (
            self.build_effect(_BANLANX2_EFFECT_WHITE, channel=channel),
            self.build_white_brightness(level, channel=channel),
        )

    def build_white_brightness(self, level: int, *, channel: int = 0) -> bytes:
        if not self._has_white_channel():
            raise ProtocolCommandError(
                f"{self.model_name or self.name} does not support white level"
            )
        return bytes([0xA0, 0x76, 0x02, byte_value(level, field="white"), 0x00])

    def build_light_mode(self, mode: int) -> bytes:
        return bytes([0xA0, 0x6A, 0x01, self._light_mode_value(mode)])

    def build_effect_speed(self, speed: int, *, channel: int = 0) -> bytes:
        return bytes([0xA0, 0x67, 0x01, _effect_speed(speed)])

    def build_effect_length(self, length: int, *, channel: int = 0) -> bytes:
        return bytes([0xA0, 0x68, 0x01, _effect_length_150(length)])

    def build_effect_loop(self, state: bool) -> bytes:
        return self.build_light_mode(0x01 if state else 0x00)

    def build_audio_input(self, value: int, *, channel: int = 0) -> bytes:
        return bytes(
            [
                0xA0,
                0x6C,
                0x01,
                self._supported_select_value("audio_input", value),
            ]
        )

    def build_sensitivity(self, value: int, *, channel: int = 0) -> bytes:
        if not self._has_audio_controls():
            raise ProtocolCommandError(
                f"{self.model_name or self.name} does not support sensitivity"
            )
        return bytes([0xA0, 0x6B, 0x01, _sensitivity(value)])

    def build_chip_order(self, value: int, *, channel: int = 0) -> bytes:
        return bytes(
            [
                0xA0,
                0x64,
                0x01,
                self._supported_select_value("chip_order", value),
            ]
        )

    def parse_status(self, data: bytes) -> DeviceState:
        """Parse an SP611E/SP616E/SP617E/SP620E/SP621E status payload."""
        _require_length(self.name, data, 12)
        has_white = self._has_white_channel()
        mode = data[1]
        effect = data[2]
        effect_type = _legacy_effect_type(
            ProtocolFamily.BANLANX_V2,
            effect,
            color_cap=self.color_cap,
            model_name=self.model_name,
            spec_functions=self.spec_functions,
        )
        if mode == _BANLANX_V23_AUTO_DYNAMIC_MODE:
            effect_type = "Dynamic"
        elif mode == _BANLANX_V23_AUTO_SOUND_MODE:
            effect_type = "Sound"
        white_level = data[-2] if has_white else None
        timer_header, timer_count, timer_records = _banlanx2_timer_metadata(data)
        brightness = (
            None
            if effect_type == "Sound"
            else
            white_level
            if effect == _BANLANX2_EFFECT_WHITE and white_level is not None
            else data[4]
        )
        is_dynamic_state = mode == _BANLANX_V23_AUTO_DYNAMIC_MODE or (
            mode == 0 and effect_type == "Dynamic"
        )
        extra = {
            "timer_header": timer_header,
            "timer_count": timer_count,
            "timer_records": timer_records,
            "color_level": data[4],
            "white_level": white_level,
        }
        if brightness is None:
            extra["color_mode"] = "onoff"
        channel = ChannelState(
            channel_id=0,
            power=data[0] == 1,
            light_mode_number=data[1],
            effect_loop=bool(data[1]) if data[1] in (0, 1) else None,
            effect=_effect_name(
                ProtocolFamily.BANLANX_V2,
                effect,
                color_cap=self.color_cap,
                model_name=self.model_name,
                spec_functions=self.spec_functions,
            ),
            effect_number=effect,
            effect_type=effect_type,
            chip_order=data[3],
            brightness=brightness,
            effect_speed=data[5] if is_dynamic_state else None,
            effect_length=data[6] if is_dynamic_state else None,
            rgb=(data[7], data[8], data[9]),
            audio_input=data[10] if self._has_audio_controls() else None,
            sensitivity=data[11] if self._has_audio_controls() else None,
            cold_white=white_level,
            warm_white=data[-1] if has_white else None,
            extra=extra,
        )
        diagnostics = {
            "protocol_family": self.name,
            "timer_header": timer_header,
            "timer_count": timer_count,
            "timer_record_count": len(timer_records),
            "timer_records": timer_records,
        }
        if self.model_name is not None:
            diagnostics.update(
                {
                    "protocol_model": self.model_name,
                    "audio_controls": self._has_audio_controls(),
                    "white_channel": self._has_white_channel(),
                }
            )
        return DeviceState(
            channels={0: channel},
            diagnostics=diagnostics,
            raw=bytes(data),
        )

    def make_status_assembler(self) -> StatusAssembler:
        """Create an assembler for BanlanX v2 segmented notifications."""
        return HeaderedStatusAssembler(self.name, magic=b"\x53\x43")

    def _has_audio_controls(self) -> bool:
        return legacy_v23_model_has_audio_controls(
            ProtocolFamily.BANLANX_V2,
            model_name=self.model_name,
            spec_functions=self.spec_functions,
        )

    def _has_white_channel(self) -> bool:
        return legacy_v23_model_has_white_channel(
            ProtocolFamily.BANLANX_V2,
            color_cap=self.color_cap,
            model_name=self.model_name,
        )

    def _light_mode_value(self, mode: int) -> int:
        mode = ranged_value(mode, field="light mode", minimum=0, maximum=2)
        if mode == 2 and not self._has_audio_controls():
            raise ProtocolCommandError(
                f"{self.model_name or self.name} does not support sound cycle mode"
            )
        return mode

    def _supported_select_value(self, key: str, value: int) -> int:
        return _supported_select_value(
            ProtocolFamily.BANLANX_V2,
            key,
            value,
            color_cap=self.color_cap,
            model_name=self.model_name,
            spec_functions=self.spec_functions,
        )


@dataclass(frozen=True, slots=True)
class BanlanX3Protocol(LegacyProtocol):
    """SP613E/SP614E/SP623E/SP624E command builder."""

    name: str = "banlanx_v3"
    model_name: str | None = None
    color_cap: int | None = None
    spec_functions: int | None = None

    def build_state_query(self) -> bytes:
        return bytes([0x1D, 0x00])

    def build_power(self, state: bool, *, channel: int = 0) -> bytes:
        return bytes([0x0F, 0x01, _bool(state)])

    def build_brightness(self, level: int, *, channel: int = 0) -> bytes:
        return bytes([0x12, 0x01, byte_value(level, field="level")])

    def build_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
    ) -> tuple[bytes, ...]:
        red, green, blue = _rgb_value(red, green, blue)
        return (
            bytes(
                [
                    0x13,
                    0x04,
                    red,
                    green,
                    blue,
                    byte_value(level, field="level"),
                ]
            ),
        )

    def build_effect(self, effect: int, *, channel: int = 0) -> bytes:
        return bytes([0x15, 0x01, self._supported_select_value("effect", effect)])

    def build_white_level(self, level: int, *, channel: int = 0) -> tuple[bytes, ...]:
        if not self._has_white_channel():
            raise ProtocolCommandError(
                f"{self.model_name or self.name} does not support white level"
            )
        return (
            self.build_effect(_BANLANX3_EFFECT_WHITE, channel=channel),
            self.build_white_brightness(level, channel=channel),
        )

    def build_white_brightness(self, level: int, *, channel: int = 0) -> bytes:
        if not self._has_white_channel():
            raise ProtocolCommandError(
                f"{self.model_name or self.name} does not support white level"
            )
        return bytes([0x21, 0x02, byte_value(level, field="white"), 0xFF])

    def build_light_mode(self, mode: int) -> bytes:
        return bytes([0x16, 0x01, self._light_mode_value(mode)])

    def build_effect_speed(self, speed: int, *, channel: int = 0) -> bytes:
        return bytes([0x14, 0x01, _effect_speed(speed)])

    def build_effect_loop(self, state: bool) -> bytes:
        return self.build_light_mode(0x01 if state else 0x00)

    def build_audio_input(self, value: int, *, channel: int = 0) -> bytes:
        return bytes(
            [0x19, 0x01, self._supported_select_value("audio_input", value)]
        )

    def build_sensitivity(self, value: int, *, channel: int = 0) -> bytes:
        if not self._has_audio_controls():
            raise ProtocolCommandError(
                f"{self.model_name or self.name} does not support sensitivity"
            )
        return bytes([0x17, 0x01, _sensitivity(value)])

    def build_chip_order(self, value: int, *, channel: int = 0) -> bytes:
        return bytes(
            [self._supported_select_value("chip_order", value), 0x00, 0x00, 0x3C]
        )

    def parse_status(self, data: bytes) -> DeviceState:
        """Parse an SP603E/SP613E/SP614E/SP623E/SP624E status payload."""
        _require_length(self.name, data, 10)
        has_white = self._has_white_channel()
        mode = data[5]
        effect = data[4]
        effect_type = _legacy_effect_type(
            ProtocolFamily.BANLANX_V3,
            effect,
            color_cap=self.color_cap,
            model_name=self.model_name,
            spec_functions=self.spec_functions,
        )
        if mode == _BANLANX_V23_AUTO_DYNAMIC_MODE:
            effect_type = "Dynamic"
        elif mode == _BANLANX_V23_AUTO_SOUND_MODE:
            effect_type = "Sound"
        white_level = data[-2] if has_white else None
        brightness = (
            None
            if effect_type == "Sound"
            else
            white_level
            if effect == _BANLANX3_EFFECT_WHITE and white_level is not None
            else data[1]
        )
        is_dynamic_state = mode == _BANLANX_V23_AUTO_DYNAMIC_MODE or (
            mode == 0 and effect_type == "Dynamic"
        )
        extra = {
            "diy_effect_type": data[10] if len(data) > 10 else None,
            "diy_color_count": data[11] if len(data) > 11 else None,
            "color_level": data[1],
            "white_level": white_level,
        }
        if brightness is None:
            extra["color_mode"] = "onoff"
        channel = ChannelState(
            channel_id=0,
            power=data[0] == 1,
            brightness=brightness,
            effect_speed=data[2] if is_dynamic_state else None,
            chip_order=data[3],
            effect=_effect_name(
                ProtocolFamily.BANLANX_V3,
                effect,
                color_cap=self.color_cap,
                model_name=self.model_name,
                spec_functions=self.spec_functions,
            ),
            effect_number=effect,
            effect_type=effect_type,
            light_mode_number=mode,
            effect_loop=bool(mode) if mode in (0, 1) else None,
            rgb=(data[6], data[7], data[8]),
            sensitivity=data[9] if self._has_audio_controls() else None,
            audio_input=data[-3]
            if self._has_audio_controls() and len(data) >= 3
            else None,
            cold_white=white_level,
            warm_white=data[-1] if has_white else None,
            extra=extra,
        )
        diagnostics = {"protocol_family": self.name}
        if self.model_name is not None:
            diagnostics.update(
                {
                    "protocol_model": self.model_name,
                    "audio_controls": self._has_audio_controls(),
                    "white_channel": self._has_white_channel(),
                }
            )
        return DeviceState(
            channels={0: channel},
            diagnostics=diagnostics,
            raw=bytes(data),
        )

    def make_status_assembler(self) -> StatusAssembler:
        """Create an assembler for BanlanX v3 segmented notifications."""
        return IndexedStatusAssembler(self.name)

    def _has_audio_controls(self) -> bool:
        return legacy_v23_model_has_audio_controls(
            ProtocolFamily.BANLANX_V3,
            model_name=self.model_name,
            spec_functions=self.spec_functions,
        )

    def _has_white_channel(self) -> bool:
        return legacy_v23_model_has_white_channel(
            ProtocolFamily.BANLANX_V3,
            color_cap=self.color_cap,
            model_name=self.model_name,
        )

    def _light_mode_value(self, mode: int) -> int:
        mode = ranged_value(mode, field="light mode", minimum=0, maximum=2)
        if mode == 2 and not self._has_audio_controls():
            raise ProtocolCommandError(
                f"{self.model_name or self.name} does not support sound cycle mode"
            )
        return mode

    def _supported_select_value(self, key: str, value: int) -> int:
        return _supported_select_value(
            ProtocolFamily.BANLANX_V3,
            key,
            value,
            color_cap=self.color_cap,
            model_name=self.model_name,
            spec_functions=self.spec_functions,
        )


@dataclass(frozen=True, slots=True)
class BanlanX6xxProtocol(LegacyProtocol):
    """SP630E/SP63x/SP64x/SP65x command builder."""

    name: str = "banlanx_6xx"
    model_name: str | None = None

    def build_state_query(self) -> bytes:
        return _encode_6xx(0x02, bytes([0x01]))

    def build_power(self, state: bool, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x50, bytes([_bool(state)]))

    def build_brightness(self, level: int, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x51, bytes([0x00, byte_value(level, field="level")]))

    def build_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
    ) -> tuple[bytes, ...]:
        red, green, blue = _rgb_value(red, green, blue)
        return (
            _encode_6xx(
                0x52,
                bytes([red, green, blue, byte_value(level, field="level")]),
            ),
        )

    def build_light_mode(self, mode: int, effect: int) -> bytes:
        return _encode_6xx(
            0x53,
            bytes(
                [
                    byte_value(mode, field="light mode"),
                    byte_value(effect, field="effect"),
                ]
            ),
        )

    def build_dynamic_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
    ) -> bytes:
        red, green, blue = _rgb_value(red, green, blue)
        return _encode_6xx(0x57, bytes([red, green, blue]))

    def build_rgbw_color(
        self,
        red: int,
        green: int,
        blue: int,
        white: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
        static: bool = True,
    ) -> tuple[bytes, ...]:
        red_command = (
            self.build_rgb_color(
                red,
                green,
                blue,
                channel=channel,
                level=level,
            )[0]
            if static
            else self.build_dynamic_rgb_color(red, green, blue, channel=channel)
        )
        return (
            red_command,
            self.build_white_level(white, channel=channel),
        )

    def build_rgbww_color(
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
    ) -> tuple[bytes, ...]:
        red_command = (
            self.build_rgb_color(
                red,
                green,
                blue,
                channel=channel,
                level=level,
            )[0]
            if static
            else self.build_dynamic_rgb_color(red, green, blue, channel=channel)
        )
        return (
            red_command,
            self.build_cct_color(cold, warm, channel=channel, static=static),
        )

    def build_white_level(self, level: int, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x51, bytes([0x01, byte_value(level, field="white")]))

    def build_cct_color(
        self,
        cold: int,
        warm: int,
        *,
        channel: int = 0,
        static: bool = True,
    ) -> bytes:
        command = 0x61 if static else 0x60
        return _encode_6xx(
            command,
            bytes(
                [
                    byte_value(cold, field="cold white"),
                    byte_value(warm, field="warm white"),
                ]
            ),
        )

    def build_effect_speed(self, speed: int, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x54, bytes([_effect_speed(speed)]))

    def build_effect_length(self, length: int, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x55, bytes([_effect_length_150(length)]))

    def build_effect_direction(self, state: bool, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x56, bytes([_bool(state)]))

    def build_effect_loop(self, state: bool) -> bytes:
        return _encode_6xx(0x58, bytes([_bool(state)]))

    def build_audio_input(self, value: int, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x59, bytes([_audio(value)]))

    def build_sensitivity(self, value: int, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x5A, bytes([_sensitivity(value)]))

    def build_onoff_config(
        self,
        effect: int,
        speed: int,
        pixels: int,
        *,
        channel: int = 0,
    ) -> bytes:
        effect = ranged_value(
            effect,
            field="on/off effect",
            minimum=1,
            maximum=4,
        )
        speed = ranged_value(speed, field="on/off speed", minimum=1, maximum=3)
        pixels = ranged_value(
            pixels,
            field="on/off pixels",
            minimum=1,
            maximum=600,
        )
        return _encode_6xx(
            0x08,
            bytes([0x01, effect, speed, *pixels.to_bytes(2, "big")]),
        )

    def build_coexistence(self, state: bool, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x0A, bytes([_bool(state)]))

    def build_on_power(self, value: int, *, channel: int = 0) -> bytes:
        return _encode_6xx(
            0x0B,
            bytes(
                [
                    ranged_value(
                        value,
                        field="on power",
                        minimum=0,
                        maximum=2,
                    )
                ]
            ),
        )

    def build_effect_play(self, state: bool, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x5D, bytes([_bool(state)]))

    def build_light_type(
        self,
        light_type: int,
        chip_order: int,
        mode: int,
        effect: int,
        *,
        power: bool = False,
        refresh: bool = False,
        channel: int = 0,
    ) -> tuple[bytes, ...]:
        light_type = ranged_value(
            light_type,
            field="light type",
            minimum=1,
            maximum=0x8E,
        )
        payloads: list[bytes] = []
        if power:
            payloads.append(self.build_power(False, channel=channel))
        payloads.extend(
            [
                _encode_6xx(0x6A, bytes([0x01, light_type & 0x7F])),
                self.build_chip_order(chip_order, channel=channel),
                self.build_light_mode(mode, effect),
            ]
        )
        if refresh:
            payloads.append(self.build_state_query())
        return tuple(payloads)

    def build_chip_order(self, value: int, *, channel: int = 0) -> bytes:
        return _encode_6xx(0x6B, bytes([byte_value(value, field="chip order")]))

    def parse_status(self, data: bytes) -> DeviceState:
        """Parse an SP63x/SP64x/SP65x unencrypted status packet."""
        packet = self.decode_packet(data)
        _require_length(self.name, packet, 53)
        if packet[1] != 0x02:
            raise ParseNotificationError(
                f"{self.name} expected status packet 0x02, got 0x{packet[1]:02x}"
            )

        firmware = packet[11:18].decode("utf-8", errors="replace").strip("\x00")
        light_type = packet[19]
        mode = packet[32]
        effect = packet[33]
        color_level = packet[35]
        white_level = packet[36]
        static_rgb = (packet[37], packet[38], packet[39])
        live_rgb = (packet[47], packet[48], packet[49])
        cold_white = packet[40]
        warm_white = packet[41]
        dynamic_cold = packet[50]
        dynamic_warm = packet[51]
        capabilities = set(banlanx6xx_light_type_capabilities(light_type))
        coexistence = (
            packet[24] != 0 and banlanx6xx_light_type_has_coexistence(light_type)
        )
        is_white_mode = mode in {0x02, 0x04, 0x06}
        is_static_mode = mode in {0x01, 0x02}
        is_live_color_mode = mode in {0x03, 0x05}
        is_sound_mode = mode in {0x05, 0x06}
        power = packet[29] > 0
        audio_input = packet[46] if power and is_sound_mode else None
        effect_attributes = banlanx6xx_effect_attributes_for_state(
            light_type,
            mode,
            effect,
            model_name=self.model_name,
        )
        brightness = (
            0xFF
            if is_sound_mode
            else white_level
            if is_white_mode
            else color_level
        )
        rgb = live_rgb if is_live_color_mode else static_rgb
        rgbw = None
        rgbww = None
        color_temp_kelvin = None

        if is_static_mode and "hue" in capabilities and "cct" in capabilities:
            if coexistence:
                rgbww = (*rgb, cold_white, warm_white)
            elif is_white_mode or "hue" not in capabilities:
                color_temp_kelvin = _kelvin_from_cold_warm(cold_white, warm_white)
        elif is_static_mode and "hue" in capabilities and "white" in capabilities:
            if coexistence:
                rgbw = (*rgb, white_level)
        elif is_white_mode and "cct" in capabilities:
            cold_white = dynamic_cold if not is_static_mode else cold_white
            warm_white = dynamic_warm if not is_static_mode else warm_white
            color_temp_kelvin = _kelvin_from_cold_warm(cold_white, warm_white)

        channel = ChannelState(
            channel_id=0,
            power=power,
            brightness=brightness,
            rgb=rgb,
            rgbw=rgbw,
            rgbww=rgbww,
            color_temp_kelvin=color_temp_kelvin,
            effect=banlanx6xx_effect_name_for_state(
                light_type,
                mode,
                effect,
                model_name=self.model_name,
            ),
            effect_type=banlanx6xx_effect_type_for_mode(mode),
            light_mode_number=mode,
            light_mode=banlanx6xx_light_mode_name(mode),
            effect_number=effect,
            effect_loop=bool(packet[30])
            if mode in _BANLANX6XX_LOOPABLE_MODES
            else None,
            effect_speed=packet[42]
            if effect_attributes is not None and effect_attributes.speedable
            else None,
            effect_length=packet[43]
            if effect_attributes is not None and effect_attributes.sizeable
            else None,
            effect_direction=bool(packet[44])
            if effect_attributes is not None and effect_attributes.directional
            else None,
            audio_input=audio_input,
            sensitivity=packet[45] if audio_input is not None else None,
            chip_order=packet[31],
            cold_white=cold_white if "cct" in capabilities else None,
            warm_white=warm_white if "cct" in capabilities else None,
            extra={
                "play": bool(packet[34])
                if effect_attributes is not None and effect_attributes.pausable
                else None,
                "color_level": color_level,
                "white_level": white_level,
                "diy_mode": packet[52],
            },
        )
        diagnostics = {
            "protocol_family": self.name,
            "light_type": light_type,
            "onoff_effect": packet[20],
            "onoff_speed": packet[21],
            "onoff_pixels": int.from_bytes(packet[22:24], "big"),
            "coexistence": packet[24],
            "on_power": packet[25],
            "debug_extra": (packet[8], packet[10], packet[26], packet[28]),
        }
        return DeviceState(
            firmware=firmware or None,
            channels={0: channel},
            diagnostics=diagnostics,
            raw=bytes(packet),
        )

    def make_status_assembler(self) -> StatusAssembler:
        """Create an assembler for SP6xx complete status packets."""
        return DirectStatusAssembler(self.name)

    def decode_packet(self, data: bytes) -> bytes:
        """Validate and return an unencrypted SP6xx packet."""
        _require_length(self.name, data, 6)
        if data[0] != 0x53:
            raise ParseNotificationError(
                f"{self.name} expected packet header 0x53, got 0x{data[0]:02x}"
            )
        if data[2] != 0x00:
            raise ParseNotificationError(
                f"{self.name} encoded status packets are not supported yet"
            )
        message_length = data[5]
        expected_length = 6 + message_length
        if len(data) != expected_length:
            raise ParseNotificationError(
                f"{self.name} expected {expected_length} bytes, got {len(data)}"
            )
        return bytes(data)


@dataclass(frozen=True, slots=True)
class BanlanXCustom5xxProtocol(BanlanX6xxProtocol):
    """SP52x/SP53x/SP54x command builder using the SP6xx wire format."""

    name: str = "banlanx_custom_5xx"

    def parse_status(self, data: bytes) -> DeviceState:
        """Parse SP6xx-style or SPTech-chunked custom 5xx status payloads."""
        packet = bytes(data)
        if packet and packet[0] in {0x00, 0x01}:
            from .sptech import SPTechLANProtocol

            return SPTechLANProtocol(
                name=self.name,
                model_name=self.model_name or "SP530E",
            ).parse_status(packet)
        return BanlanX6xxProtocol.parse_status(self, packet)

    def make_status_assembler(self) -> StatusAssembler:
        """Create an assembler for direct and fragmented custom 5xx status."""
        return Custom5xxStatusAssembler(self.name)


@dataclass(frozen=True, slots=True)
class LegacyLEDChordProtocol(LegacyProtocol):
    """SP107E LED Chord command builder and parser."""

    name: str = "legacy_led_chord"

    def build_state_query(self) -> bytes:
        return bytes([0x00, 0x00, 0x00, 0x02])

    def build_power(self, state: bool, *, channel: int = 0) -> bytes:
        return bytes([0x00, 0x00, 0x00, 0xAA if state else 0xBB])

    def build_brightness(self, level: int, *, channel: int = 0) -> bytes:
        return bytes([byte_value(level, field="level"), 0x00, 0x00, 0x0A])

    def build_white_level(self, level: int, *, channel: int = 0) -> bytes:
        return bytes([byte_value(level, field="white level"), 0x00, 0x00, 0x0B])

    def build_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
    ) -> tuple[bytes, ...]:
        red, green, blue = _rgb_value(red, green, blue)
        return (bytes([red, green, blue, 0x0C]),)

    def build_rgb2_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
    ) -> bytes:
        red, green, blue = _rgb_value(red, green, blue)
        return bytes([red, green, blue, 0x10])

    def build_rgbw_color(
        self,
        red: int,
        green: int,
        blue: int,
        white: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
        static: bool = True,
    ) -> tuple[bytes, ...]:
        red, green, blue = _rgb_value(red, green, blue)
        white = byte_value(white, field="white")
        return (
            bytes([red, green, blue, 0x0C]),
            bytes([white, 0x00, 0x00, 0x0B]),
        )

    def build_effect(self, effect: int, *, channel: int = 0) -> bytes:
        if int(effect) not in _LED_CHORD_EFFECTS:
            raise ProtocolCommandError(f"effect must be a known {self.name} value")
        return bytes([int(effect) & 0xFF, 0x00, 0x00, 0x08])

    def build_light_mode(self, mode: int, effect: int | None = None) -> bytes:
        mode = int(mode)
        if mode == _LED_CHORD_LIGHT_MODE_AUTO_DYNAMIC:
            return bytes([0x01, 0x00, 0x00, 0x0D])
        if mode == _LED_CHORD_LIGHT_MODE_AUTO_STRIP:
            return bytes([0x01, 0x00, 0x00, 0x0F])
        if mode == _LED_CHORD_LIGHT_MODE_AUTO_MATRIX:
            return bytes([0x01, 0x00, 0x00, 0x12])
        if mode == _LED_CHORD_LIGHT_MODE_SINGULAR:
            return self.build_effect(
                _LED_CHORD_FX_STATIC if effect is None else effect
            )
        raise ProtocolCommandError(f"light mode must be a known {self.name} value")

    def build_effect_speed(self, speed: int, *, channel: int = 0) -> bytes:
        speed = ranged_value(
            speed,
            field="effect speed",
            minimum=1,
            maximum=_LED_CHORD_EFFECT_SPEED_MAX,
        )
        return bytes([speed, 0x00, 0x00, 0x09])

    def build_sensitivity(self, value: int, *, channel: int = 0) -> bytes:
        value = ranged_value(
            value,
            field="sensitivity",
            minimum=1,
            maximum=_LED_CHORD_SENSITIVITY_MAX,
        )
        return bytes([value, 0x00, 0x00, 0x13])

    def build_chip_order(self, value: int, *, channel: int = 0) -> bytes:
        return bytes([byte_value(value, field="chip order"), 0x00, 0x00, 0x04])

    def build_chip_type(self, value: int, *, channel: int = 0) -> bytes:
        return bytes([_legacy_led_chip_type(value), 0x00, 0x00, 0x05])

    def build_segment_count(
        self,
        segments: int,
        pixels: int | None = None,
        *,
        channel: int = 0,
    ) -> bytes:
        if pixels is None:
            raise ProtocolCommandError(
                "segment pixels are required for stateless LED Chord commands"
            )
        segment_count = ranged_value(
            segments,
            field="segment count",
            minimum=1,
            maximum=_LED_CHORD_MAX_SEGMENT_COUNT,
        )
        segment_pixels = ranged_value(
            pixels,
            field="segment pixels",
            minimum=1,
            maximum=_LED_CHORD_MAX_SEGMENT_PIXELS,
        )
        if segment_count * segment_pixels > _LED_CHORD_MAX_TOTAL_PIXELS:
            raise ProtocolCommandError(
                "segment count times segment pixels must be 960 or less"
            )
        return bytes([segment_count, segment_pixels, 0x00, 0x06])

    def build_segment_pixels(
        self,
        pixels: int,
        *,
        segment_count: int | None = None,
        channel: int = 0,
    ) -> bytes:
        if segment_count is None:
            raise ProtocolCommandError(
                "segment count is required for stateless LED Chord commands"
            )
        return self.build_segment_count(segment_count, pixels, channel=channel)

    def parse_status(self, data: bytes) -> DeviceState:
        packet = bytes(data)
        _require_exact_length(self.name, packet, 26)
        effect = packet[5]
        chip_type = packet[2]
        rgb = (packet[13], packet[14], packet[15])
        white = packet[11] if chip_type in {0x03, 0x04, 0x05, 0x09, 0x0C} else None
        effect_type = "Unknown"
        light_mode_number = _LED_CHORD_LIGHT_MODE_SINGULAR
        light_mode = _LED_CHORD_LIGHT_MODES[light_mode_number]
        sensitivity = None
        effect_speed = None
        rgb2 = None

        if effect == _LED_CHORD_FX_STATIC:
            effect_type = "Static"
        elif effect < _LED_CHORD_FX_STATIC:
            effect_type = "Dynamic"
            effect_speed = packet[9]
            if packet[6]:
                light_mode_number = _LED_CHORD_LIGHT_MODE_AUTO_DYNAMIC
        else:
            sensitivity = packet[25]
            if _LED_CHORD_FX_STRIP <= effect < _LED_CHORD_FX_MATRIX:
                rgb = (packet[16], packet[17], packet[18])
                effect_type = "Sound - Strip FX"
                if packet[7]:
                    light_mode_number = _LED_CHORD_LIGHT_MODE_AUTO_STRIP
            elif effect >= _LED_CHORD_FX_MATRIX:
                rgb = (packet[22], packet[23], packet[24])
                rgb2 = (packet[19], packet[20], packet[21])
                effect_type = "Sound - Matrix FX"
                if packet[8]:
                    light_mode_number = _LED_CHORD_LIGHT_MODE_AUTO_MATRIX
            light_mode = _LED_CHORD_LIGHT_MODES[light_mode_number]

        light_mode = _LED_CHORD_LIGHT_MODES[light_mode_number]
        channel = ChannelState(
            channel_id=0,
            power=packet[0] == 1,
            brightness=packet[10],
            rgb=rgb if white is None else None,
            rgbw=rgb + (white,) if white is not None else None,
            effect=_LED_CHORD_EFFECTS.get(effect, "Unknown"),
            effect_number=effect,
            effect_type=effect_type,
            effect_speed=effect_speed,
            light_mode=light_mode,
            light_mode_number=light_mode_number,
            sensitivity=sensitivity,
            chip_order=packet[1],
            extra={
                "chip_type": chip_type,
                "segment_count": packet[3],
                "segment_pixels": packet[4],
                "total_pixels": packet[3] * packet[4],
                "white_level": white,
                "rgb2": rgb2,
                "unknown_12": packet[12],
            },
        )
        return DeviceState(
            channels={0: channel},
            diagnostics={
                "protocol_family": self.name,
                "chip_type": chip_type,
                "segment_count": packet[3],
                "segment_pixels": packet[4],
                "total_pixels": packet[3] * packet[4],
            },
            raw=packet,
        )

    def make_status_assembler(self) -> StatusAssembler:
        return LEDChordStatusAssembler(self.name)


@dataclass(frozen=True, slots=True)
class LegacyLEDHueProtocol(LegacyProtocol):
    """SP110E LED Hue command builder and parser."""

    name: str = "legacy_led_hue"

    def build_state_query(self) -> bytes:
        return bytes([0x00, 0x00, 0x00, 0x10])

    def build_power(self, state: bool, *, channel: int = 0) -> bytes:
        return bytes([0x00, 0x00, 0x00, 0xAA if state else 0xAB])

    def build_brightness(self, level: int, *, channel: int = 0) -> bytes:
        return bytes([byte_value(level, field="level"), 0x00, 0x00, 0x2A])

    def build_white_level(self, level: int, *, channel: int = 0) -> bytes:
        return bytes([byte_value(level, field="white level"), 0x00, 0x00, 0x69])

    def build_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
    ) -> tuple[bytes, ...]:
        red, green, blue = _rgb_value(red, green, blue)
        return (bytes([red, green, blue, 0x1E]),)

    def build_rgbw_color(
        self,
        red: int,
        green: int,
        blue: int,
        white: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
        static: bool = True,
    ) -> tuple[bytes, ...]:
        red, green, blue = _rgb_value(red, green, blue)
        white = byte_value(white, field="white")
        return (
            bytes([red, green, blue, 0x1E]),
            bytes([white, 0x00, 0x00, 0x69]),
        )

    def build_effect(self, effect: int, *, channel: int = 0) -> bytes:
        if int(effect) not in _LED_HUE_EFFECTS:
            raise ProtocolCommandError(f"effect must be a known {self.name} value")
        return bytes([int(effect) & 0xFF, 0x00, 0x00, 0x2C])

    def build_effect_loop(self, state: bool) -> bytes:
        if state:
            return bytes([0x00, 0x00, 0x00, 0x06])
        return self.build_effect(_LED_HUE_EFFECT_TYPE_STATIC)

    def build_effect_speed(self, speed: int, *, channel: int = 0) -> bytes:
        speed = ranged_value(
            speed,
            field="effect speed",
            minimum=1,
            maximum=_LED_HUE_EFFECT_SPEED_MAX,
        )
        return bytes([speed, 0x00, 0x00, 0x03])

    def build_chip_order(self, value: int, *, channel: int = 0) -> bytes:
        return bytes([byte_value(value, field="chip order"), 0x00, 0x00, 0x3C])

    def build_chip_type(self, value: int, *, channel: int = 0) -> bytes:
        return bytes([_legacy_led_chip_type(value), 0x00, 0x00, 0x1C])

    def build_segment_pixels(
        self,
        pixels: int,
        *,
        segment_count: int | None = None,
        channel: int = 0,
    ) -> bytes:
        value = ranged_value(
            pixels,
            field="segment pixels",
            minimum=1,
            maximum=_LED_HUE_MAX_SEGMENT_PIXELS,
        ).to_bytes(2, "big")
        return bytes([value[0], value[1], 0x00, 0x2D])

    def parse_status(self, data: bytes) -> DeviceState:
        packet = bytes(data)
        if len(packet) == 13:
            packet = packet[1:]
        _require_exact_length(self.name, packet, 12)
        power = packet[0]
        effect = packet[1]
        speed = packet[2]
        level = packet[3]
        chip_type = packet[4]
        chip_order = packet[5]
        pixels = int.from_bytes(packet[6:8], "big")
        rgb = (packet[8], packet[9], packet[10])
        is_rgbw = chip_type in {0x03, 0x04, 0x05, 0x09, 0x0C}

        effect_type = "Static"
        effect_speed = None
        effect_name = _LED_HUE_EFFECTS.get(effect, "Unknown")
        if effect == _LED_HUE_EFFECT_TYPE_AUTO or effect != _LED_HUE_EFFECT_TYPE_STATIC:
            effect_type = "Dynamic"
            effect_speed = speed
            if effect == _LED_HUE_EFFECT_TYPE_AUTO:
                effect_name = _LED_HUE_AUTO_CYCLE_EFFECT

        channel = ChannelState(
            channel_id=0,
            power=power != 0x00,
            brightness=level,
            rgb=None if is_rgbw else rgb,
            rgbw=rgb + (packet[11],) if is_rgbw else None,
            effect=effect_name,
            effect_number=effect,
            effect_type=effect_type,
            effect_speed=effect_speed,
            effect_loop=effect == _LED_HUE_EFFECT_TYPE_AUTO,
            chip_order=chip_order,
            extra={
                "chip_type": chip_type,
                "segment_pixels": pixels,
                "white_level": packet[11] if is_rgbw else None,
            },
        )
        return DeviceState(
            channels={0: channel},
            diagnostics={
                "protocol_family": self.name,
                "chip_type": chip_type,
                "segment_pixels": pixels,
            },
            raw=bytes(data),
        )

    def make_status_assembler(self) -> StatusAssembler:
        return DirectStatusAssembler(self.name)


@dataclass(slots=True)
class LEDChordStatusAssembler:
    """Assemble SP107E's two 15-byte LED Chord status notifications."""

    family: str
    _first: bytes | None = None

    def feed(self, data: bytes) -> bytes | None:
        packet = bytes(data)
        if len(packet) != 15:
            self._fail(f"expected 15 bytes, got {len(packet)}")
        if packet[:2] == b"\x00\x01":
            self._first = packet[2:]
            return None
        if packet[:2] != b"\x00\x02":
            self._fail(f"expected packet 1 or 2, got {packet[:2].hex()}")
        if self._first is None:
            self._fail("continuation packet without an initial packet")
        result = self._first + packet[2:]
        self.reset()
        return result

    def reset(self) -> None:
        self._first = None

    def _fail(self, message: str) -> None:
        self.reset()
        raise ParseNotificationError(f"{self.family} notification: {message}")


def _bool(state: bool) -> int:
    return 0x01 if state else 0x00


def _legacy_led_chip_type(value: int) -> int:
    return ranged_value(
        value,
        field="chip type",
        minimum=0,
        maximum=_LEGACY_LED_CHIP_TYPE_MAX,
    )


def _banlanx2_timer_metadata(
    data: bytes,
) -> tuple[bytes | None, int | None, tuple[bytes, ...]]:
    """Return old-UniLED BanlanX2 timer metadata without decoding records."""
    if len(data) <= 22:
        return None, None, ()
    timer_count = data[22]
    return (
        bytes(data[12:22]),
        timer_count,
        _tail_records(data, offset=23, count=timer_count, size=7),
    )


def _kelvin_from_cold_warm(cold: int, warm: int) -> int | None:
    total = int(cold) + int(warm)
    if total <= 0:
        return None
    return round(2700 + (int(cold) / total) * (6500 - 2700))


def _effect(value: int) -> int:
    return byte_value(value, field="effect")


def _effect_speed(value: int) -> int:
    return ranged_value(value, field="effect speed", minimum=1, maximum=10)


def _effect_length_150(value: int) -> int:
    return ranged_value(value, field="effect length", minimum=1, maximum=150)


def _effect_length_240(value: int) -> int:
    return ranged_value(value, field="effect length", minimum=1, maximum=240)


def _scene_slot(value: int) -> int:
    return ranged_value(value, field="scene", minimum=0, maximum=8)


def _audio(value: int) -> int:
    return ranged_value(value, field="audio input", minimum=0, maximum=2)


def _sensitivity(value: int) -> int:
    return ranged_value(value, field="sensitivity", minimum=1, maximum=16)


def _supported_select_value(
    family: ProtocolFamily,
    key: str,
    value: int,
    *,
    color_cap: int | None,
    model_name: str | None,
    spec_functions: int | None,
) -> int:
    field = key.replace("_", " ")
    raw_value = byte_value(value, field=field)
    option_map = select_option_map(
        family,
        key,
        color_cap=color_cap,
        model_name=model_name,
        spec_functions=spec_functions,
    )
    if option_map is None or option_map.option_for_value(raw_value) is None:
        model = model_name or family.value
        raise ProtocolCommandError(f"{model} does not support {field} {raw_value}")
    return raw_value


def _effect_name(
    family: ProtocolFamily,
    value: int,
    *,
    color_cap: int | None = None,
    model_name: str | None = None,
    spec_functions: int | None = None,
) -> str | None:
    option_map = select_option_map(
        family,
        "effect",
        color_cap=color_cap,
        model_name=model_name,
        spec_functions=spec_functions,
    )
    return None if option_map is None else option_map.option_for_value(value)


def _legacy_effect_type(
    family: ProtocolFamily,
    value: int,
    *,
    color_cap: int | None = None,
    model_name: str | None = None,
    spec_functions: int | None = None,
) -> str | None:
    if family in {ProtocolFamily.BANLANX_601, ProtocolFamily.BANLANX_60X}:
        if value == 0x19:
            return "Static"
        if value >= 0x65:
            return "Sound"
        return "Dynamic"
    if family is ProtocolFamily.BANLANX_V2:
        if (
            _effect_name(
                family,
                value,
                color_cap=color_cap,
                model_name=model_name,
                spec_functions=spec_functions,
            )
            is None
        ):
            return None
        if value in {0xBE, 0xBF}:
            return "Static"
        if value >= 0xC9:
            return "Sound"
        return "Dynamic"
    if family is ProtocolFamily.BANLANX_V3:
        if (
            _effect_name(
                family,
                value,
                color_cap=color_cap,
                model_name=model_name,
                spec_functions=spec_functions,
            )
            is None
        ):
            return None
        if value in {0x63, 0xCC}:
            return "Static"
        if 0x65 <= value < 0xCC:
            return "Sound"
        return "Dynamic"
    if value == 0:
        return "Static"
    return "Dynamic"


def _encode_6xx(command: int, data: bytes) -> bytes:
    length = len(data) & 0xFF
    return bytes([0x53, command & 0xFF, 0x00, 0x01, 0x00, length, *data])


def _parse_chunked_status(
    family: str,
    data: bytes,
    *,
    channel_size: int,
    channels: int,
    parser,
) -> DeviceState:
    _require_length(family, data, channel_size)
    channel_count = min(channels, len(data) // channel_size)
    if channel_count < 1:
        raise ParseNotificationError(f"{family} status contains no channel data")

    parsed = {
        channel_id: parser(
            data[(channel_id - 1) * channel_size : channel_id * channel_size],
            channel=channel_id,
        )
        for channel_id in range(1, channel_count + 1)
    }
    if channel_count > 1:
        parsed[0] = _master_from_channels(parsed)

    return DeviceState(
        channels=parsed,
        diagnostics={
            "protocol_family": family,
            "channel_count": channel_count,
            "trailing_bytes": bytes(data[channel_count * channel_size :]),
        },
        raw=bytes(data),
    )


def _master_from_channels(channels: dict[int, ChannelState]) -> ChannelState:
    brightness_values = [
        channel.brightness
        for channel_id, channel in channels.items()
        if channel_id != 0 and channel.brightness is not None
    ]
    brightness = (
        int(sum(brightness_values) / len(brightness_values))
        if brightness_values
        else None
    )
    return ChannelState(
        channel_id=0,
        power=any(
            channel.power is True
            for channel_id, channel in channels.items()
            if channel_id != 0
        ),
        brightness=brightness,
        extra={"source": "aggregate"},
    )


def _apply_sp601_tail(state: DeviceState) -> None:
    """Apply old-UniLED SP601E tail fields after channel blocks."""
    tail = state.diagnostics.get("trailing_bytes")
    if not isinstance(tail, bytes) or not tail:
        return

    timer_count = tail[0]
    state.diagnostics["timer_count"] = timer_count
    timer_records = _tail_records(tail, offset=1, count=timer_count, size=7)
    state.diagnostics["timer_record_count"] = len(timer_records)
    state.diagnostics["timer_records"] = timer_records
    offset = 1 + timer_count * 7
    if len(tail) <= offset:
        return

    master = state.channels.setdefault(0, ChannelState(channel_id=0))
    master.effect_loop = bool(tail[offset])
    state.diagnostics["scene_loop"] = master.effect_loop


def _apply_sp60x_tail(state: DeviceState, *, triggers: int) -> None:
    """Apply old-UniLED SP60x tail fields after channel blocks."""
    tail = state.diagnostics.get("trailing_bytes")
    if not isinstance(tail, bytes) or not tail:
        return

    master = state.channels.setdefault(0, ChannelState(channel_id=0))
    gain = tail[0]
    state.diagnostics["tail_sensitivity"] = gain
    if master.power is True:
        master.sensitivity = gain

    offset = 1
    if len(tail) <= offset:
        return

    timer_count = tail[offset]
    state.diagnostics["timer_count"] = timer_count
    offset += 1
    timer_records = _tail_records(tail, offset=offset, count=timer_count, size=7)
    state.diagnostics["timer_record_count"] = len(timer_records)
    state.diagnostics["timer_records"] = timer_records
    offset += timer_count * 7
    trigger_bytes = int(triggers) * 13
    trigger_records = _tail_records(tail, offset=offset, count=triggers, size=13)
    state.diagnostics["trigger_record_count"] = len(trigger_records)
    state.diagnostics["trigger_records"] = trigger_records
    if len(tail) < offset + trigger_bytes:
        return

    offset += trigger_bytes
    if len(tail) <= offset:
        return

    master.effect_loop = bool(tail[offset])
    state.diagnostics["scene_loop"] = master.effect_loop


def _tail_records(
    tail: bytes,
    *,
    offset: int,
    count: int,
    size: int,
) -> tuple[bytes, ...]:
    """Return complete fixed-size records from an old-UniLED status tail."""
    records: list[bytes] = []
    for index in range(int(count)):
        start = offset + index * size
        end = start + size
        if len(tail) < end:
            break
        records.append(bytes(tail[start:end]))
    return tuple(records)


def _require_length(family: str, data: bytes, minimum: int) -> None:
    if len(data) < minimum:
        raise ParseNotificationError(
            f"{family} status requires at least {minimum} bytes, got {len(data)}"
        )


def _require_exact_length(family: str, data: bytes, expected: int) -> None:
    if len(data) != expected:
        raise ParseNotificationError(
            f"{family} status requires {expected} bytes, got {len(data)}"
        )
