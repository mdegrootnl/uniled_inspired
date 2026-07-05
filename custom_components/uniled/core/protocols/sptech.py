"""SPTech LAN command builders and status parser."""

from __future__ import annotations

from dataclasses import dataclass

from ..options import (
    banlanx6xx_effect_attributes_for_state,
    banlanx6xx_effect_name_for_state,
    banlanx6xx_effect_type_for_mode,
    banlanx6xx_light_mode_name,
    banlanx6xx_light_type_capabilities,
    banlanx6xx_light_type_name,
)
from ..state import ChannelState, DeviceState, ParseNotificationError
from .banlanx_legacy import LegacyProtocol
from .base import byte_value, ranged_value
from .framing import DirectStatusAssembler, StatusAssembler

SPTECH_MAGIC = b"SPTECH\x00"
SPTECH_RESPONSE_HEADER_BYTES = len(SPTECH_MAGIC) + 6

_CMD_STATUS_QUERY = 0x02
_CMD_POWER = 0x50
_CMD_BRIGHTNESS = 0x51
_CMD_LIGHT_MODE = 0x53
_CMD_EFFECT_SPEED = 0x54
_CMD_EFFECT_LENGTH = 0x55
_CMD_EFFECT_DIRECTION = 0x56
_CMD_EFFECT_LOOP = 0x58
_CMD_AUDIO_INPUT = 0x59
_CMD_AUDIO_GAIN = 0x5A
_CMD_EFFECT_PLAY = 0x5D

_MODE_STATIC_WHITE = 0x02
_MODE_DYNAMIC_WHITE = 0x04
_MODE_SOUND_WHITE = 0x06
_WHITE_MODES = {_MODE_STATIC_WHITE, _MODE_DYNAMIC_WHITE, _MODE_SOUND_WHITE}
_LOOPABLE_MODES = {0x03, 0x04, 0x05, 0x06}


@dataclass(frozen=True, slots=True)
class SPTechLANProtocol(LegacyProtocol):
    """SPTech TCP protocol used by SP541E LAN controllers."""

    name: str = "sptech_lan"
    model_name: str = "SP541E"

    def build_state_query(self) -> bytes:
        """Build a read-only status query."""
        return _encode_sptech(_CMD_STATUS_QUERY, b"")

    def build_power(self, state: bool, *, channel: int = 0) -> bytes:
        """Build an on/off command."""
        return _encode_sptech(_CMD_POWER, bytes([0x01 if state else 0x00]))

    def build_brightness(self, level: int, *, channel: int = 0) -> bytes:
        """Build a mono/PWM white-channel brightness command."""
        return self.build_white_level(level, channel=channel)

    def build_white_level(self, level: int, *, channel: int = 0) -> bytes:
        """Build the SPTech white-output brightness command."""
        return _encode_sptech(
            _CMD_BRIGHTNESS,
            bytes([0x01, byte_value(level, field="white level")]),
        )

    def build_white_brightness(self, level: int, *, channel: int = 0) -> bytes:
        """Build brightness for devices already in white mode."""
        return self.build_white_level(level, channel=channel)

    def build_light_mode(self, mode: int, effect: int = 0x01) -> bytes:
        """Build a coupled light-mode/effect command."""
        return _encode_sptech(
            _CMD_LIGHT_MODE,
            bytes(
                [
                    _white_mode(mode),
                    byte_value(effect, field="effect"),
                ]
            ),
        )

    def build_effect_speed(self, speed: int, *, channel: int = 0) -> bytes:
        """Build an effect-speed command."""
        return _encode_sptech(
            _CMD_EFFECT_SPEED,
            bytes([ranged_value(speed, field="effect speed", minimum=1, maximum=10)]),
        )

    def build_effect_length(self, length: int, *, channel: int = 0) -> bytes:
        """Build an effect-length command."""
        return _encode_sptech(
            _CMD_EFFECT_LENGTH,
            bytes(
                [
                    ranged_value(
                        length,
                        field="effect length",
                        minimum=1,
                        maximum=150,
                    )
                ]
            ),
        )

    def build_effect_direction(self, state: bool, *, channel: int = 0) -> bytes:
        """Build an effect-direction command."""
        return _encode_sptech(
            _CMD_EFFECT_DIRECTION,
            bytes([0x01 if state else 0x00]),
        )

    def build_effect_loop(self, state: bool) -> bytes:
        """Build an effect-loop command."""
        return _encode_sptech(_CMD_EFFECT_LOOP, bytes([0x01 if state else 0x00]))

    def build_audio_input(self, value: int, *, channel: int = 0) -> bytes:
        """Build an audio-input command."""
        return _encode_sptech(
            _CMD_AUDIO_INPUT,
            bytes([ranged_value(value, field="audio input", minimum=0, maximum=2)]),
        )

    def build_sensitivity(self, value: int, *, channel: int = 0) -> bytes:
        """Build an audio-sensitivity command."""
        return _encode_sptech(
            _CMD_AUDIO_GAIN,
            bytes(
                [
                    ranged_value(
                        value,
                        field="audio sensitivity",
                        minimum=1,
                        maximum=16,
                    )
                ]
            ),
        )

    def build_effect_play(self, state: bool, *, channel: int = 0) -> bytes:
        """Build an effect play/pause command."""
        return _encode_sptech(_CMD_EFFECT_PLAY, bytes([0x01 if state else 0x00]))

    def parse_status(self, data: bytes) -> DeviceState:
        """Parse a full SPTech response frame or raw chunked payload."""
        payload = _response_payload(data)
        chunks = _decode_chunks(payload)

        diagnostics: dict[str, object] = {
            "protocol_family": self.name,
            "chunk_types": tuple(chunks),
        }
        firmware: str | None = None
        light_type: int | None = None
        channel = ChannelState(channel_id=0)

        chunk_1 = chunks.get(1)
        if chunk_1 is not None:
            firmware, light_type = _parse_settings_chunk(chunk_1, diagnostics)

        status_chunk = chunks.get(3)
        if status_chunk is not None:
            chunk_light_type, channel = _parse_extended_status_chunk(
                status_chunk,
                light_type=light_type,
            )
            light_type = chunk_light_type
        elif (status_chunk := chunks.get(2)) is not None:
            channel = _parse_status_chunk(status_chunk, light_type=light_type)

        if light_type is not None:
            diagnostics["light_type"] = light_type
            light_type_label = banlanx6xx_light_type_name(light_type)
            if light_type_label is not None:
                diagnostics["light_type_name"] = light_type_label

        return DeviceState(
            firmware=firmware,
            channels={0: channel},
            diagnostics=diagnostics,
            raw=bytes(data),
        )

    def make_status_assembler(self) -> StatusAssembler:
        """SPTech LAN responses arrive as complete direct frames."""
        return DirectStatusAssembler(self.name)


def _encode_sptech(command: int, data: bytes) -> bytes:
    payload = bytes(data)
    return bytes(
        [
            *SPTECH_MAGIC,
            command & 0xFF,
            0x00,
            0x00,
            0x00,
            *len(payload).to_bytes(2, "big"),
            *payload,
        ]
    )


def _white_mode(mode: int) -> int:
    mode = byte_value(mode, field="light mode")
    if mode not in _WHITE_MODES:
        raise ValueError(f"SP541E only supports white modes, got 0x{mode:02x}")
    return mode


def _response_payload(data: bytes) -> bytes:
    packet = bytes(data)
    if not packet:
        raise ParseNotificationError("sptech_lan status payload is empty")
    if not packet.startswith(SPTECH_MAGIC):
        return packet
    if len(packet) < SPTECH_RESPONSE_HEADER_BYTES:
        raise ParseNotificationError(
            "sptech_lan response header requires "
            f"{SPTECH_RESPONSE_HEADER_BYTES} bytes, got {len(packet)}"
        )
    payload_length = int.from_bytes(packet[11:13], "big")
    expected = SPTECH_RESPONSE_HEADER_BYTES + payload_length
    if len(packet) != expected:
        raise ParseNotificationError(
            f"sptech_lan response expected {expected} bytes, got {len(packet)}"
        )
    return packet[SPTECH_RESPONSE_HEADER_BYTES:]


def _decode_chunks(payload: bytes) -> dict[int, bytes]:
    if not payload:
        raise ParseNotificationError("sptech_lan response payload is empty")
    length_fields = payload[0]
    if length_fields not in {0, 1}:
        raise ParseNotificationError(
            f"sptech_lan unsupported chunk length field marker {length_fields}"
        )
    size_width = length_fields + 1
    offset = 1
    chunks: dict[int, bytes] = {}
    while offset < len(payload):
        chunk_type = payload[offset]
        offset += 1
        if offset + size_width > len(payload):
            raise ParseNotificationError("sptech_lan truncated chunk size")
        chunk_size = int.from_bytes(payload[offset : offset + size_width], "big")
        offset += size_width
        end = offset + chunk_size
        if end > len(payload):
            raise ParseNotificationError(
                f"sptech_lan chunk {chunk_type} requires {chunk_size} bytes"
            )
        chunks[chunk_type] = payload[offset:end]
        offset = end
    return chunks


def _parse_settings_chunk(
    data: bytes,
    diagnostics: dict[str, object],
) -> tuple[str | None, int | None]:
    _require_length("settings", data, 17)
    firmware = data[2:10].decode("utf-8", errors="replace").strip("\x00 ")
    light_type = data[10]
    diagnostics.update(
        {
            "settings_unknown": (data[0], data[1]),
            "onoff_effect": data[11],
            "onoff_speed": data[12],
            "onoff_pixels": int.from_bytes(data[13:15], "big"),
            "coexistence": data[15],
            "on_power": data[16],
        }
    )
    return firmware or None, light_type


def _parse_extended_status_chunk(
    data: bytes,
    *,
    light_type: int | None,
) -> tuple[int | None, ChannelState]:
    _require_length("extended status", data, 26)
    chunk_light_type = data[1]
    return chunk_light_type, _parse_status_chunk(data[2:], light_type=chunk_light_type)


def _parse_status_chunk(data: bytes, *, light_type: int | None) -> ChannelState:
    _require_length("status", data, 24)
    power = data[1] > 0
    mode = data[4]
    effect = data[5]
    level_color = data[7]
    level_white = data[8]
    static_rgb = (data[9], data[10], data[11])
    static_white = (data[12], data[13])
    speed = data[14]
    length = data[15]
    direction = data[16]
    gain = data[17]
    audio = data[18]
    effect_rgb = (data[19], data[20], data[21])
    effect_white = (data[22], data[23])

    capabilities = set(banlanx6xx_light_type_capabilities(light_type))
    is_white = mode in _WHITE_MODES
    is_sound = mode == _MODE_SOUND_WHITE
    brightness = 0xFF if is_sound else level_white if is_white else level_color
    effect_attributes = banlanx6xx_effect_attributes_for_state(
        light_type,
        mode,
        effect,
    )
    cold_white = warm_white = None
    if "cct" in capabilities:
        cold_white, warm_white = (
            effect_white if mode in {_MODE_DYNAMIC_WHITE, _MODE_SOUND_WHITE}
            else static_white
        )

    return ChannelState(
        channel_id=0,
        power=power,
        brightness=brightness,
        rgb=effect_rgb if mode == 0x03 else static_rgb if mode == 0x01 else None,
        effect=banlanx6xx_effect_name_for_state(light_type, mode, effect),
        effect_number=effect,
        effect_type=banlanx6xx_effect_type_for_mode(mode),
        effect_speed=speed
        if effect_attributes is not None and effect_attributes.speedable
        else None,
        effect_length=length
        if effect_attributes is not None and effect_attributes.sizeable
        else None,
        effect_direction=bool(direction)
        if effect_attributes is not None and effect_attributes.directional
        else None,
        effect_loop=bool(data[2]) if mode in _LOOPABLE_MODES else None,
        light_mode=banlanx6xx_light_mode_name(mode),
        light_mode_number=mode,
        audio_input=audio if power and is_sound else None,
        sensitivity=gain if power and is_sound else None,
        cold_white=cold_white,
        warm_white=warm_white,
        extra={
            "play": bool(data[6])
            if effect_attributes is not None and effect_attributes.pausable
            else None,
            "color_level": level_color,
            "white_level": level_white,
            "static_white": static_white,
            "effect_white": effect_white,
        },
    )


def _require_length(label: str, data: bytes, minimum: int) -> None:
    if len(data) < minimum:
        raise ParseNotificationError(
            f"sptech_lan {label} chunk requires at least {minimum} bytes, "
            f"got {len(data)}"
        )
