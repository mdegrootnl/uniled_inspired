"""SPTech LAN command builders and status parser."""

from __future__ import annotations

from dataclasses import dataclass

from ..options import (
    banlanx6xx_chip_order_values_for_light_type,
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
from .base import rgb_value as _rgb_value
from .framing import DirectStatusAssembler, StatusAssembler

SPTECH_MAGIC = b"SPTECH\x00"
SPTECH_RESPONSE_HEADER_BYTES = len(SPTECH_MAGIC) + 6

_CMD_STATUS_QUERY = 0x02
_CMD_ONOFF_OPTIONS = 0x08
_CMD_COEXISTENCE = 0x0A
_CMD_ON_POWER = 0x0B
_CMD_POWER = 0x50
_CMD_BRIGHTNESS = 0x51
_CMD_STATIC_COLOR = 0x52
_CMD_LIGHT_MODE = 0x53
_CMD_EFFECT_SPEED = 0x54
_CMD_EFFECT_LENGTH = 0x55
_CMD_EFFECT_DIRECTION = 0x56
_CMD_EFFECT_COLOR = 0x57
_CMD_EFFECT_LOOP = 0x58
_CMD_AUDIO_INPUT = 0x59
_CMD_AUDIO_GAIN = 0x5A
_CMD_EFFECT_PLAY = 0x5D
_CMD_EFFECT_CCT = 0x60
_CMD_STATIC_CCT = 0x61
_CMD_LIGHT_TYPE = 0x6A
_CMD_CHIP_ORDER = 0x6B

_MODE_STATIC_WHITE = 0x02
_MODE_DYNAMIC_WHITE = 0x04
_MODE_SOUND_WHITE = 0x06
_WHITE_MODES = {_MODE_STATIC_WHITE, _MODE_DYNAMIC_WHITE, _MODE_SOUND_WHITE}
_LOOPABLE_MODES = {0x03, 0x04, 0x05, 0x06}
_HANDLED_STATUS_CHUNK_TYPES = frozenset({1, 2, 3, 4, 5, 6, 7})
_UNKNOWN_CHUNK_HEX_LIMIT = 96
_UNKNOWN_CHUNK_ASCII_MIN_RUN = 3


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

    def build_rgb_color(
        self,
        red: int,
        green: int,
        blue: int,
        *,
        channel: int = 0,
        level: int = 0xFF,
    ) -> tuple[bytes, ...]:
        """Build the old-UniLED SPTech static RGB command."""
        red, green, blue = _rgb_value(red, green, blue)
        return (
            _encode_sptech(
                _CMD_STATIC_COLOR,
                bytes([red, green, blue, byte_value(level, field="level")]),
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
        """Build the old-UniLED SPTech dynamic/sound RGB tuning command."""
        red, green, blue = _rgb_value(red, green, blue)
        return _encode_sptech(_CMD_EFFECT_COLOR, bytes([red, green, blue]))

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
        """Build an old-UniLED SPTech RGBW command sequence."""
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
        """Build an old-UniLED SPTech RGBCCT command sequence."""
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

    def build_cct_color(
        self,
        cold: int,
        warm: int,
        *,
        channel: int = 0,
        static: bool = True,
    ) -> bytes:
        """Build the old-UniLED SPTech static/dynamic CCT command."""
        command = _CMD_STATIC_CCT if static else _CMD_EFFECT_CCT
        return _encode_sptech(
            command,
            bytes(
                [
                    byte_value(cold, field="cold white"),
                    byte_value(warm, field="warm white"),
                ]
            ),
        )

    def build_light_mode(self, mode: int, effect: int = 0x01) -> bytes:
        """Build a coupled light-mode/effect command."""
        return _encode_sptech(
            _CMD_LIGHT_MODE,
            bytes(
                [
                    byte_value(mode, field="light mode"),
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

    def build_onoff_config(
        self,
        effect: int,
        speed: int,
        pixels: int,
        *,
        channel: int = 0,
    ) -> bytes:
        """Build the old-UniLED SPTech on/off animation config command."""
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
        return _encode_sptech(
            _CMD_ONOFF_OPTIONS,
            bytes([0x01, effect, speed, *pixels.to_bytes(2, "big")]),
        )

    def build_coexistence(self, state: bool, *, channel: int = 0) -> bytes:
        """Build the old-UniLED SPTech coexistence command."""
        return _encode_sptech(_CMD_COEXISTENCE, bytes([0x01 if state else 0x00]))

    def build_on_power(self, value: int, *, channel: int = 0) -> bytes:
        """Build the old-UniLED SPTech power-restore command."""
        return _encode_sptech(
            _CMD_ON_POWER,
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
        """Build the old-UniLED SPTech light-type reconfiguration sequence."""
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
                _encode_sptech(_CMD_LIGHT_TYPE, bytes([0x01, light_type & 0x7F])),
                self.build_chip_order(chip_order, channel=channel),
                self.build_light_mode(mode, effect),
            ]
        )
        if refresh:
            payloads.append(self.build_state_query())
        return tuple(payloads)

    def build_chip_order(self, value: int, *, channel: int = 0) -> bytes:
        """Build an SPI chip-order command recovered from old UniLED."""
        return _encode_sptech(
            _CMD_CHIP_ORDER,
            bytes([ranged_value(value, field="chip order", minimum=0, maximum=23)]),
        )

    def parse_status(self, data: bytes) -> DeviceState:
        """Parse a full SPTech response frame or raw chunked payload."""
        payload = _response_payload(data)
        chunks, chunk_types = _decode_chunks(payload)

        diagnostics: dict[str, object] = {
            "protocol_family": self.name,
            "chunk_types": chunk_types,
        }
        firmware: str | None = None
        light_type: int | None = None
        channel = ChannelState(channel_id=0)

        chunk_1 = _last_chunk(chunks, 1)
        if chunk_1 is not None:
            firmware, light_type = _parse_settings_chunk(chunk_1, diagnostics)

        status_chunk = _last_chunk(chunks, 3)
        if status_chunk is not None:
            chunk_light_type, channel = _parse_extended_status_chunk(
                status_chunk,
                light_type=light_type,
                model_name=self.model_name,
                diagnostics=diagnostics,
            )
            light_type = chunk_light_type
        elif (status_chunk := _last_chunk(chunks, 2)) is not None:
            channel = _parse_status_chunk(
                status_chunk,
                light_type=light_type,
                model_name=self.model_name,
            )
            _parse_status_tail(status_chunk[24:], diagnostics, include_gradient=False)

        timer_chunks = chunks.get(4, ())
        if timer_chunks:
            _parse_timer_chunks(timer_chunks, diagnostics)

        effect_layout_chunk = _last_chunk(chunks, 5)
        if effect_layout_chunk is not None:
            _parse_effect_layout_chunk(effect_layout_chunk, diagnostics)

        network_chunk = _last_chunk(chunks, 6)
        if network_chunk is not None:
            _parse_network_info_chunk(network_chunk, diagnostics)

        fun_switch_chunk = _last_chunk(chunks, 7)
        if fun_switch_chunk is not None:
            _parse_fun_switch_chunk(fun_switch_chunk, diagnostics)

        _parse_unknown_chunks(
            chunks,
            diagnostics,
            handled_types=_HANDLED_STATUS_CHUNK_TYPES,
        )

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


def _decode_chunks(
    payload: bytes,
) -> tuple[dict[int, tuple[bytes, ...]], tuple[int, ...]]:
    if not payload:
        raise ParseNotificationError("sptech_lan response payload is empty")
    length_fields = payload[0]
    if length_fields not in {0, 1}:
        raise ParseNotificationError(
            f"sptech_lan unsupported chunk length field marker {length_fields}"
        )
    size_width = length_fields + 1
    offset = 1
    chunks: dict[int, list[bytes]] = {}
    chunk_types: list[int] = []
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
        chunk_types.append(chunk_type)
        chunks.setdefault(chunk_type, []).append(payload[offset:end])
        offset = end
    return {
        chunk_type: tuple(chunk_payloads)
        for chunk_type, chunk_payloads in chunks.items()
    }, tuple(chunk_types)


def _last_chunk(
    chunks: dict[int, tuple[bytes, ...]],
    chunk_type: int,
) -> bytes | None:
    chunk_payloads = chunks.get(chunk_type)
    if not chunk_payloads:
        return None
    return chunk_payloads[-1]


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
    model_name: str | None,
    diagnostics: dict[str, object],
) -> tuple[int | None, ChannelState]:
    _require_length("extended status", data, 26)
    chunk_light_type = data[1]
    _parse_status_tail(data[26:], diagnostics, include_gradient=True)
    return chunk_light_type, _parse_status_chunk(
        data[2:],
        light_type=chunk_light_type,
        model_name=model_name,
    )


def _parse_status_chunk(
    data: bytes,
    *,
    light_type: int | None,
    model_name: str | None,
) -> ChannelState:
    _require_length("status", data, 24)
    power = data[1] > 0
    chip_order = data[3]
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
        model_name=model_name,
    )
    chip_order_values = banlanx6xx_chip_order_values_for_light_type(light_type)
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
        effect=banlanx6xx_effect_name_for_state(
            light_type,
            mode,
            effect,
            model_name=model_name,
        ),
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
        chip_order=chip_order
        if chip_order_values is not None and chip_order in chip_order_values
        else None,
        cold_white=cold_white,
        warm_white=warm_white,
        extra={
            "play": bool(data[6])
            if effect_attributes is not None and effect_attributes.pausable
            else None,
            "color_level": level_color,
            "white_level": level_white,
            "chip_order_raw": chip_order,
            "static_white": static_white,
            "effect_white": effect_white,
        },
    )


def _parse_network_info_chunk(
    data: bytes,
    diagnostics: dict[str, object],
) -> None:
    """Parse old-UniLED SPTech chunk 6 network-info strings."""
    if len(data) < 2:
        diagnostics["network_info_parse_error"] = "truncated_string_count"
        return

    string_count = int.from_bytes(data[0:2], "big")
    offset = 2
    strings: list[str] = []
    for _ in range(string_count):
        if offset >= len(data):
            diagnostics["network_info_parse_error"] = "truncated_string_length"
            break
        string_length = data[offset]
        offset += 1
        end = offset + string_length
        if end > len(data):
            diagnostics["network_info_parse_error"] = "truncated_string"
            break
        raw = data[offset:end]
        offset = end
        strings.append(raw.decode("utf-8", errors="replace"))

    if strings:
        diagnostics["network_info_strings"] = tuple(strings)
    if len(strings) >= 1 and strings[0]:
        diagnostics["network_wifi_ssid"] = strings[0]
    if len(strings) >= 2 and strings[1]:
        diagnostics["network_ip_address"] = strings[1]
    if len(strings) >= 2 and (strings[0] or strings[1]):
        diagnostics["network_info"] = f"ssid={strings[0]}; ip={strings[1]}"
    if offset < len(data):
        diagnostics["network_info_tail"] = data[offset:].hex()


def _parse_status_tail(
    data: bytes,
    diagnostics: dict[str, object],
    *,
    include_gradient: bool,
) -> None:
    """Parse old-UniLED SPTech DIY slot metadata after status bytes."""
    if not data:
        return

    offset = _parse_diy_slots(
        data,
        diagnostics,
        prefix="sptech_diy_solid",
        value_key="pixels",
    )
    if not include_gradient:
        if offset < len(data):
            diagnostics["sptech_diy_solid_tail"] = data[offset:].hex()
        return

    if offset >= len(data):
        diagnostics["sptech_diy_gradient_parse_error"] = "missing_header"
        return
    gradient_offset = _parse_diy_slots(
        data[offset:],
        diagnostics,
        prefix="sptech_diy_gradient",
        value_key="level",
    )
    tail_offset = offset + gradient_offset
    if tail_offset < len(data):
        diagnostics["sptech_diy_gradient_tail"] = data[tail_offset:].hex()


def _parse_diy_slots(
    data: bytes,
    diagnostics: dict[str, object],
    *,
    prefix: str,
    value_key: str,
) -> int:
    if len(data) < 2:
        diagnostics[f"{prefix}_parse_error"] = "truncated_header"
        return len(data)

    mode = data[0]
    slot_count = data[1]
    offset = 2
    slots: list[dict[str, object]] = []
    for slot_index in range(slot_count):
        if offset + 4 > len(data):
            diagnostics[f"{prefix}_parse_error"] = f"truncated_slot_{slot_index}"
            break
        slot = data[offset : offset + 4]
        offset += 4
        slots.append(
            {
                value_key: slot[0],
                "rgb": (slot[1], slot[2], slot[3]),
            }
        )

    diagnostics[f"{prefix}_mode"] = mode
    diagnostics[f"{prefix}_slot_count"] = slot_count
    diagnostics[f"{prefix}_slots"] = tuple(slots)
    return offset


def _parse_timer_chunks(
    timer_chunks: tuple[bytes, ...],
    diagnostics: dict[str, object],
) -> None:
    """Parse old-UniLED SPTech chunk 4 timer records."""
    records: list[dict[str, object]] = []
    errors: list[str] = []
    for index, data in enumerate(timer_chunks):
        if not data:
            continue
        if len(data) < 7:
            errors.append(f"chunk_{index}_truncated")
            continue

        record: dict[str, object] = {
            "id": data[0],
            "enabled": bool(data[1]),
            "power": bool(data[2]),
            "days": data[3],
            "meridiem": data[4],
            "time": int.from_bytes(data[5:7], "big"),
        }
        if len(data) > 7:
            record["tail"] = data[7:].hex()
        records.append(record)

    diagnostics["sptech_timer_count"] = len(records)
    diagnostics["sptech_timer_records"] = tuple(records)
    if errors:
        diagnostics["sptech_timer_parse_errors"] = tuple(errors)


def _parse_effect_layout_chunk(
    data: bytes,
    diagnostics: dict[str, object],
) -> None:
    """Parse old-UniLED SPTech chunk 5 music/effect layout metadata."""
    if len(data) < 5:
        diagnostics["sptech_effect_layout_parse_error"] = "truncated_header"
        return

    diagnostics.update(
        {
            "sptech_effect_layout_unknown": data[0],
            "sptech_effect_layout": data[1],
            "sptech_matrix_width": data[2],
            "sptech_matrix_height": data[3],
            "sptech_matrix_layout": data[4],
        }
    )

    offset = 5
    if offset >= len(data):
        diagnostics["sptech_effect_layout_parse_error"] = (
            "missing_strip_mode_count"
        )
        return

    strip_mode_count = data[offset]
    offset += 1
    strip_modes: list[dict[str, object]] = []
    parse_error: str | None = None
    for strip_mode in range(strip_mode_count):
        if offset >= len(data):
            parse_error = "truncated_strip_mode"
            break
        segment_count = data[offset]
        offset += 1
        segments: list[dict[str, object]] = []
        for segment_index in range(segment_count):
            if offset + 9 > len(data):
                parse_error = f"truncated_strip_segment_{strip_mode}_{segment_index}"
                break
            segment = data[offset : offset + 9]
            offset += 9
            segments.append(
                {
                    "segment": segment[0],
                    "pixels": int.from_bytes(segment[1:3], "big"),
                    "direction": segment[3],
                    "effect": segment[4],
                    "frequency": segment[5],
                    "rgb": (segment[6], segment[7], segment[8]),
                }
            )
        strip_modes.append(
            {
                "mode": strip_mode,
                "segment_count": segment_count,
                "segments": tuple(segments),
            }
        )
        if parse_error is not None:
            break

    diagnostics["sptech_sound_strip_mode_count"] = strip_mode_count
    diagnostics["sptech_sound_strip_modes"] = tuple(strip_modes)
    if parse_error is not None:
        diagnostics["sptech_effect_layout_parse_error"] = parse_error
        return

    if offset >= len(data):
        diagnostics["sptech_effect_layout_parse_error"] = (
            "missing_matrix_mode_count"
        )
        return

    matrix_mode_count = data[offset]
    offset += 1
    matrix_modes: list[str] = []
    for matrix_mode in range(matrix_mode_count):
        if offset + 28 > len(data):
            diagnostics["sptech_effect_layout_parse_error"] = (
                f"truncated_matrix_mode_{matrix_mode}"
            )
            break
        matrix_modes.append(data[offset : offset + 28].hex())
        offset += 28

    diagnostics["sptech_sound_matrix_mode_count"] = matrix_mode_count
    diagnostics["sptech_sound_matrix_modes"] = tuple(matrix_modes)
    if offset < len(data):
        diagnostics["sptech_effect_layout_tail"] = data[offset:].hex()


def _parse_fun_switch_chunk(
    data: bytes,
    diagnostics: dict[str, object],
) -> None:
    """Parse old-UniLED SPTech chunk 7 fun-switch status byte."""
    if not data:
        diagnostics["power_fun_switch_parse_error"] = "empty"
        return

    diagnostics["power_fun_switch"] = data[0]
    if len(data) > 1:
        diagnostics["power_fun_switch_tail"] = data[1:].hex()


def _parse_unknown_chunks(
    chunks: dict[int, tuple[bytes, ...]],
    diagnostics: dict[str, object],
    *,
    handled_types: frozenset[int],
) -> None:
    """Preserve unhandled SPTech chunks as bounded diagnostic evidence."""
    records: list[dict[str, object]] = []
    for chunk_type, payloads in chunks.items():
        if chunk_type in handled_types:
            continue
        for index, data in enumerate(payloads):
            sample = data[:_UNKNOWN_CHUNK_HEX_LIMIT]
            record: dict[str, object] = {
                "type": chunk_type,
                "index": index,
                "size": len(data),
                "hex": sample.hex(),
            }
            ascii_runs = _printable_ascii_runs(sample)
            if ascii_runs:
                record["ascii_runs"] = ascii_runs
            if len(sample) < len(data):
                record["truncated"] = True
            records.append(record)

    if records:
        diagnostics["unknown_chunk_count"] = len(records)
        diagnostics["unknown_chunk_types"] = tuple(
            record["type"] for record in records
        )
        diagnostics["unknown_chunks"] = tuple(records)


def _printable_ascii_runs(data: bytes) -> tuple[str, ...]:
    runs: list[str] = []
    current: list[str] = []
    for byte in data:
        if 0x20 <= byte <= 0x7E:
            current.append(chr(byte))
            continue
        _append_ascii_run(runs, current)

    _append_ascii_run(runs, current)
    return tuple(runs)


def _append_ascii_run(runs: list[str], current: list[str]) -> None:
    text = "".join(current).strip()
    if len(text) >= _UNKNOWN_CHUNK_ASCII_MIN_RUN:
        runs.append(text)
    current.clear()


def _require_length(label: str, data: bytes, minimum: int) -> None:
    if len(data) < minimum:
        raise ParseNotificationError(
            f"sptech_lan {label} chunk requires at least {minimum} bytes, "
            f"got {len(data)}"
        )
