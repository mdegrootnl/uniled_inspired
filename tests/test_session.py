"""Protocol session tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from custom_components.uniled.const import CONF_DEVICE_ID, CONF_MODEL
from custom_components.uniled.core import (
    BanlanX2Protocol,
    BanlanX3Protocol,
    BanlanX6xxProtocol,
    BanlanX601Protocol,
    BanlanXCustom5xxProtocol,
    CommandKind,
    DeviceSession,
    LegacyLEDChordProtocol,
    LegacyLEDHueProtocol,
    ProtocolCommandError,
    SPTechLANProtocol,
)
from custom_components.uniled.runtime import RuntimeSetupError, build_runtime
from tests.test_state_parsers import _custom_5xx_sptech_issue_67_payload


@dataclass(slots=True)
class RecordingTransport:
    """Transport test double that records outgoing payloads."""

    response: bytes | None = None
    sent: list[tuple[bytes, bool]] = field(default_factory=list)
    closed: bool = False

    async def send(self, payload: bytes, *, response: bool = False) -> bytes | None:
        """Record one payload."""
        self.sent.append((payload, response))
        return self.response if response else None

    async def close(self) -> None:
        """Record close."""
        self.closed = True


@dataclass(slots=True)
class YieldingTransport:
    """Transport double that reveals overlapping sends."""

    sent: list[tuple[bytes, bool]] = field(default_factory=list)
    active: int = 0
    max_active: int = 0
    query_sent: asyncio.Event = field(default_factory=asyncio.Event)

    async def send(self, payload: bytes, *, response: bool = False) -> bytes | None:
        """Record one payload and yield while it is in flight."""
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        self.sent.append((payload, response))
        if response:
            self.query_sent.set()
        await asyncio.sleep(0)
        self.active -= 1
        return None


def test_session_dispatches_power_command_to_transport() -> None:
    """A high-level power command becomes the legacy wire payload."""
    transport = RecordingTransport()
    session = DeviceSession(BanlanX601Protocol(), transport)

    result = asyncio.run(session.set_power(False, channel=1))

    assert result.kind is CommandKind.POWER
    assert result.payloads == (bytes.fromhex("aa 22 02 00 00"),)
    assert result.responses == (None,)
    assert transport.sent == [(bytes.fromhex("aa 22 02 00 00"), False)]


def test_session_dispatches_banlanx_v23_white_brightness_payload() -> None:
    """BanlanX2/3 white brightness can be sent without an effect switch."""
    transport = RecordingTransport()
    session = DeviceSession(BanlanX2Protocol(color_cap=2), transport)

    result = asyncio.run(session.set_white_brightness(0x44))

    assert result.kind is CommandKind.WHITE_LEVEL
    assert result.payloads == (bytes.fromhex("a0 76 02 44 00"),)
    assert transport.sent == [(bytes.fromhex("a0 76 02 44 00"), False)]

    transport = RecordingTransport()
    session = DeviceSession(BanlanX3Protocol(color_cap=2), transport)

    result = asyncio.run(session.set_white_brightness(0x55))

    assert result.kind is CommandKind.WHITE_LEVEL
    assert result.payloads == (bytes.fromhex("21 02 55 ff"),)
    assert transport.sent == [(bytes.fromhex("21 02 55 ff"), False)]


def test_session_fans_out_sp601_aggregate_light_commands() -> None:
    """SP601E aggregate light commands dispatch to both physical outputs."""
    transport = RecordingTransport()
    session = DeviceSession(BanlanX601Protocol(), transport)

    result = asyncio.run(session.set_brightness(128))

    assert result.kind is CommandKind.BRIGHTNESS
    assert result.payloads == (
        bytes.fromhex("aa 25 02 00 80"),
        bytes.fromhex("aa 25 02 01 80"),
    )
    assert transport.sent == [
        (bytes.fromhex("aa 25 02 00 80"), False),
        (bytes.fromhex("aa 25 02 01 80"), False),
    ]


def test_session_request_state_marks_transport_response_expected() -> None:
    """State requests use the protocol query command and response flag."""
    transport = RecordingTransport(response=b"ok")
    session = DeviceSession(BanlanX601Protocol(), transport)

    result = asyncio.run(session.request_state())

    assert result.kind is CommandKind.STATE_QUERY
    assert result.payloads == (bytes.fromhex("aa 2f 00"),)
    assert result.responses == (b"ok",)
    assert transport.sent == [(bytes.fromhex("aa 2f 00"), True)]


def test_session_refresh_state_parses_direct_response() -> None:
    """Refresh can parse transports that return raw status bytes directly."""
    response = bytes.fromhex(
        "01 02 00 ff 0a 1e 01 ff 00 00 10"
        "00 01 02 ff 0a 1e 00 00 ff 00 10"
    )
    transport = RecordingTransport(response=response)
    session = DeviceSession(BanlanX601Protocol(), transport)

    state = asyncio.run(session.refresh_state(response_timeout=0))

    assert state is not None
    assert state.channels[1].power is True
    assert state.channels[1].rgb == (255, 0, 0)
    assert state.channels[2].power is False
    assert state.channels[2].rgb == (0, 255, 0)
    assert transport.sent == [(bytes.fromhex("aa 2f 00"), True)]


def test_session_refresh_state_waits_for_notification() -> None:
    """Refresh waits for a complete notification when writes return no bytes."""
    session = DeviceSession(BanlanX601Protocol(), RecordingTransport())
    first = bytes.fromhex(
        "53 43 01 18 0f 00 01 02 ff 0a 1e 01 ff 00 00 10 00 01 02 ff"
    )
    second = bytes.fromhex("53 43 02 18 09 0a 1e 00 00 ff 00 10 00 00")

    async def scenario() -> None:
        task = asyncio.create_task(session.refresh_state(response_timeout=1))
        await asyncio.sleep(0)
        assert session.transport.sent == [(bytes.fromhex("aa 2f 00"), True)]

        assert session.apply_notification(first) is None
        assert not task.done()
        assert session.apply_notification(second) is not None

        state = await task

        assert state is not None
        assert state.channels[1].rgb == (255, 0, 0)
        assert state.channels[2].rgb == (0, 255, 0)

    asyncio.run(scenario())


def test_session_serializes_concurrent_command_payload_groups() -> None:
    """Concurrent HA entity calls cannot interleave session payload groups."""
    transport = YieldingTransport()
    session = DeviceSession(BanlanX6xxProtocol(), transport)

    async def scenario() -> None:
        await asyncio.gather(
            session.set_rgbw_color(1, 2, 3, 4, level=128),
            session.set_effect_speed(7),
        )

    asyncio.run(scenario())

    rgbw_group = [
        (bytes.fromhex("53 52 00 01 00 04 01 02 03 80"), False),
        (bytes.fromhex("53 51 00 01 00 02 01 04"), False),
    ]
    speed_group = [(bytes.fromhex("53 54 00 01 00 01 07"), False)]
    assert transport.max_active == 1
    assert transport.sent in (rgbw_group + speed_group, speed_group + rgbw_group)


def test_session_refresh_blocks_entity_commands_until_state_result() -> None:
    """State refresh holds the session lock through notification handling."""
    transport = YieldingTransport()
    session = DeviceSession(BanlanX601Protocol(), transport)
    first = bytes.fromhex(
        "53 43 01 18 0f 00 01 02 ff 0a 1e 01 ff 00 00 10 00 01 02 ff"
    )
    second = bytes.fromhex("53 43 02 18 09 0a 1e 00 00 ff 00 10 00 00")

    async def scenario() -> None:
        refresh = asyncio.create_task(session.refresh_state(response_timeout=1))
        await transport.query_sent.wait()

        command = asyncio.create_task(session.set_power(False, channel=1))
        await asyncio.sleep(0)

        assert transport.sent == [(bytes.fromhex("aa 2f 00"), True)]

        assert session.apply_notification(first) is None
        assert session.apply_notification(second) is not None
        assert await refresh is session.state
        await command

    asyncio.run(scenario())

    assert transport.max_active == 1
    assert transport.sent == [
        (bytes.fromhex("aa 2f 00"), True),
        (bytes.fromhex("aa 22 02 00 00"), False),
    ]


def test_session_refresh_state_returns_none_on_timeout() -> None:
    """Refresh returns None when no response or notification arrives."""
    session = DeviceSession(BanlanX601Protocol(), RecordingTransport())

    state = asyncio.run(session.refresh_state(response_timeout=0))

    assert state is None
    assert session.transport.sent == [(bytes.fromhex("aa 2f 00"), True)]


def test_session_dispatches_select_commands_to_transport() -> None:
    """High-level select commands become legacy wire payloads."""
    transport = RecordingTransport()
    session = DeviceSession(BanlanX2Protocol(), transport)

    audio = asyncio.run(session.set_audio_input(2))
    mode = asyncio.run(session.set_light_mode(1))
    chip_order = asyncio.run(session.set_chip_order(2))

    assert audio.kind is CommandKind.AUDIO_INPUT
    assert audio.payloads == (bytes.fromhex("a0 6c 01 02"),)
    assert mode.kind is CommandKind.LIGHT_MODE
    assert mode.payloads == (bytes.fromhex("a0 6a 01 01"),)
    assert chip_order.kind is CommandKind.CHIP_ORDER
    assert chip_order.payloads == (bytes.fromhex("a0 64 01 02"),)
    assert transport.sent == [
        (bytes.fromhex("a0 6c 01 02"), False),
        (bytes.fromhex("a0 6a 01 01"), False),
        (bytes.fromhex("a0 64 01 02"), False),
    ]

    transport = RecordingTransport()
    session = DeviceSession(BanlanX6xxProtocol(), transport)

    mode_effect = asyncio.run(session.set_light_mode(0x03, 0x02))

    assert mode_effect.kind is CommandKind.LIGHT_MODE
    assert mode_effect.payloads == (bytes.fromhex("53 53 00 01 00 02 03 02"),)
    assert transport.sent == [
        (bytes.fromhex("53 53 00 01 00 02 03 02"), False)
    ]

    transport = RecordingTransport()
    session = DeviceSession(BanlanX601Protocol(), transport)

    effect = asyncio.run(session.set_effect(8, channel=1))
    scene_loop = asyncio.run(session.set_scene_loop(True))
    scene = asyncio.run(session.set_scene(8))

    assert effect.kind is CommandKind.EFFECT
    assert effect.payloads == (bytes.fromhex("aa 23 02 00 08"),)
    assert scene_loop.kind is CommandKind.SCENE_LOOP
    assert scene_loop.payloads == (bytes.fromhex("aa 30 01 01"),)
    assert scene.kind is CommandKind.SCENE
    assert scene.payloads == (bytes.fromhex("aa 2e 01 08"),)
    assert transport.sent == [
        (bytes.fromhex("aa 23 02 00 08"), False),
        (bytes.fromhex("aa 30 01 01"), False),
        (bytes.fromhex("aa 2e 01 08"), False),
    ]


def test_session_dispatches_legacy_led_config_commands_to_transport() -> None:
    """Legacy LED Chord/Hue config builders dispatch through sessions."""
    transport = RecordingTransport()
    chord_protocol = LegacyLEDChordProtocol()
    chord = DeviceSession(chord_protocol, transport)
    chord.state = chord_protocol.parse_status(
        bytes(
            [
                1,
                2,
                3,
                4,
                5,
                0xB5,
                0,
                0,
                0,
                6,
                100,
                20,
                0,
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                15,
            ]
        )
    )

    rgb2 = asyncio.run(chord.set_rgb2_color(1, 2, 3))
    chip_type = asyncio.run(chord.set_chip_type(4))
    segment_count = asyncio.run(chord.set_segment_count(6))
    segment_pixels = asyncio.run(chord.set_segment_pixels(7))

    assert rgb2.kind is CommandKind.RGB2_COLOR
    assert rgb2.payloads == (bytes.fromhex("01 02 03 10"),)
    assert chip_type.kind is CommandKind.CHIP_TYPE
    assert chip_type.payloads == (bytes.fromhex("04 00 00 05"),)
    assert segment_count.kind is CommandKind.SEGMENT_COUNT
    assert segment_count.payloads == (bytes.fromhex("06 05 00 06"),)
    assert segment_pixels.kind is CommandKind.SEGMENT_PIXELS
    assert segment_pixels.payloads == (bytes.fromhex("04 07 00 06"),)
    assert transport.sent == [
        (bytes.fromhex("01 02 03 10"), False),
        (bytes.fromhex("04 00 00 05"), False),
        (bytes.fromhex("06 05 00 06"), False),
        (bytes.fromhex("04 07 00 06"), False),
    ]

    transport = RecordingTransport()
    hue = DeviceSession(LegacyLEDHueProtocol(), transport)

    hue_chip_type = asyncio.run(hue.set_chip_type(4))
    hue_segment_pixels = asyncio.run(hue.set_segment_pixels(300))

    assert hue_chip_type.kind is CommandKind.CHIP_TYPE
    assert hue_chip_type.payloads == (bytes.fromhex("04 00 00 1c"),)
    assert hue_segment_pixels.kind is CommandKind.SEGMENT_PIXELS
    assert hue_segment_pixels.payloads == (bytes.fromhex("01 2c 00 2d"),)
    assert transport.sent == [
        (bytes.fromhex("04 00 00 1c"), False),
        (bytes.fromhex("01 2c 00 2d"), False),
    ]


def test_session_dispatches_sp6xx_advanced_commands_to_transport() -> None:
    """High-level SP6xx advanced commands become old UniLED wire payloads."""
    transport = RecordingTransport()
    session = DeviceSession(BanlanX6xxProtocol(), transport)

    dynamic_rgb = asyncio.run(session.set_dynamic_rgb_color(1, 2, 3))
    rgbw = asyncio.run(session.set_rgbw_color(1, 2, 3, 4, level=128))
    rgbww = asyncio.run(session.set_rgbww_color(1, 2, 3, 4, 5, level=128))
    white = asyncio.run(session.set_white_level(64))
    cct = asyncio.run(session.set_cct_color(10, 20, static=False))
    onoff = asyncio.run(session.set_onoff_config(3, 2, 300))
    coexistence = asyncio.run(session.set_coexistence(True))
    on_power = asyncio.run(session.set_on_power(2))
    play = asyncio.run(session.set_effect_play(False))
    chip_order = asyncio.run(session.set_chip_order(2))
    light_type = asyncio.run(
        session.set_light_type(
            0x86,
            2,
            0x03,
            0x01,
            power=True,
            refresh=True,
        )
    )

    assert dynamic_rgb.kind is CommandKind.DYNAMIC_RGB_COLOR
    assert dynamic_rgb.payloads == (bytes.fromhex("53 57 00 01 00 03 01 02 03"),)
    assert rgbw.kind is CommandKind.RGBW_COLOR
    assert rgbw.payloads == (
        bytes.fromhex("53 52 00 01 00 04 01 02 03 80"),
        bytes.fromhex("53 51 00 01 00 02 01 04"),
    )
    assert rgbww.kind is CommandKind.RGBWW_COLOR
    assert rgbww.payloads == (
        bytes.fromhex("53 52 00 01 00 04 01 02 03 80"),
        bytes.fromhex("53 61 00 01 00 02 04 05"),
    )
    assert white.kind is CommandKind.WHITE_LEVEL
    assert white.payloads == (bytes.fromhex("53 51 00 01 00 02 01 40"),)
    assert cct.kind is CommandKind.CCT_COLOR
    assert cct.payloads == (bytes.fromhex("53 60 00 01 00 02 0a 14"),)
    assert onoff.kind is CommandKind.ONOFF_CONFIG
    assert onoff.payloads == (bytes.fromhex("53 08 00 01 00 05 01 03 02 01 2c"),)
    assert coexistence.kind is CommandKind.COEXISTENCE
    assert coexistence.payloads == (bytes.fromhex("53 0a 00 01 00 01 01"),)
    assert on_power.kind is CommandKind.ON_POWER
    assert on_power.payloads == (bytes.fromhex("53 0b 00 01 00 01 02"),)
    assert play.kind is CommandKind.EFFECT_PLAY
    assert play.payloads == (bytes.fromhex("53 5d 00 01 00 01 00"),)
    assert chip_order.kind is CommandKind.CHIP_ORDER
    assert chip_order.payloads == (bytes.fromhex("53 6b 00 01 00 01 02"),)
    assert light_type.kind is CommandKind.LIGHT_TYPE
    assert light_type.payloads == (
        bytes.fromhex("53 50 00 01 00 01 00"),
        bytes.fromhex("53 6a 00 01 00 02 01 06"),
        bytes.fromhex("53 6b 00 01 00 01 02"),
        bytes.fromhex("53 53 00 01 00 02 03 01"),
        bytes.fromhex("53 02 00 01 00 01 01"),
    )
    assert transport.sent == [
        (bytes.fromhex("53 57 00 01 00 03 01 02 03"), False),
        (bytes.fromhex("53 52 00 01 00 04 01 02 03 80"), False),
        (bytes.fromhex("53 51 00 01 00 02 01 04"), False),
        (bytes.fromhex("53 52 00 01 00 04 01 02 03 80"), False),
        (bytes.fromhex("53 61 00 01 00 02 04 05"), False),
        (bytes.fromhex("53 51 00 01 00 02 01 40"), False),
        (bytes.fromhex("53 60 00 01 00 02 0a 14"), False),
        (bytes.fromhex("53 08 00 01 00 05 01 03 02 01 2c"), False),
        (bytes.fromhex("53 0a 00 01 00 01 01"), False),
        (bytes.fromhex("53 0b 00 01 00 01 02"), False),
        (bytes.fromhex("53 5d 00 01 00 01 00"), False),
        (bytes.fromhex("53 6b 00 01 00 01 02"), False),
        (bytes.fromhex("53 50 00 01 00 01 00"), False),
        (bytes.fromhex("53 6a 00 01 00 02 01 06"), False),
        (bytes.fromhex("53 6b 00 01 00 01 02"), False),
        (bytes.fromhex("53 53 00 01 00 02 03 01"), False),
        (bytes.fromhex("53 02 00 01 00 01 01"), False),
    ]


def test_session_dispatches_custom_5xx_with_6xx_payloads() -> None:
    """Custom 5xx sessions reuse SP6xx command bytes under their own family."""
    transport = RecordingTransport()
    session = DeviceSession(BanlanXCustom5xxProtocol(), transport)

    result = asyncio.run(session.set_light_mode(0x03, 0x02))

    assert result.kind is CommandKind.LIGHT_MODE
    assert result.payloads == (bytes.fromhex("53 53 00 01 00 02 03 02"),)
    assert transport.sent == [
        (bytes.fromhex("53 53 00 01 00 02 03 02"), False)
    ]


def test_session_refresh_state_parses_sptech_lan_response() -> None:
    """SPTech LAN direct responses can drive DeviceSession refresh."""
    response = _sptech_sp541e_status_frame()
    transport = RecordingTransport(response=response)
    session = DeviceSession(SPTechLANProtocol(), transport)

    state = asyncio.run(session.refresh_state(response_timeout=0))

    assert state is not None
    assert state.channels[0].power is True
    assert state.channels[0].brightness == 73
    assert transport.sent == [
        (
            bytes.fromhex("53 50 54 45 43 48 00 02 00 00 00 00 00"),
            True,
        )
    ]


def test_session_rejects_commands_missing_from_protocol() -> None:
    """Unsupported protocol capabilities fail before bytes are sent."""
    transport = RecordingTransport()
    session = DeviceSession(BanlanX3Protocol(), transport)

    try:
        asyncio.run(session.set_effect_length(10))
    except ProtocolCommandError:
        pass
    else:
        raise AssertionError("BanlanX v3 has no effect-length command")

    assert transport.sent == []


def test_session_applies_segmented_notifications_to_state() -> None:
    """Sessions own assembler state across segmented notifications."""
    session = DeviceSession(BanlanX601Protocol(), RecordingTransport())
    first = bytes.fromhex(
        "53 43 01 18 0f 00 01 02 ff 0a 1e 01 ff 00 00 10 00 01 02 ff"
    )
    second = bytes.fromhex("53 43 02 18 09 0a 1e 00 00 ff 00 10 00 00")

    assert session.apply_notification(first) is None
    state = session.apply_notification(second)

    assert state is not None
    assert session.state is state
    assert state.channels[1].rgb == (255, 0, 0)
    assert state.channels[2].rgb == (0, 255, 0)


def test_session_applies_custom_5xx_issue_67_fragments_to_state() -> None:
    """SP530E issue #67-style BLE fragments refresh custom 5xx state."""
    payload = _custom_5xx_sptech_issue_67_payload()
    fragments = (
        bytes([0x53, 0x02, 0x00, len(payload), 0x00, 14]) + payload[:14],
        bytes([0x53, 0x02, 0x00, len(payload), 0x01, 14]) + payload[14:28],
        bytes([0x53, 0x02, 0x00, len(payload), 0x02, len(payload[28:])])
        + payload[28:],
    )
    session = DeviceSession(BanlanXCustom5xxProtocol(), RecordingTransport())

    assert session.apply_notification(fragments[0]) is None
    assert session.apply_notification(fragments[1]) is None
    state = session.apply_notification(fragments[2])

    assert state is not None
    assert session.state is state
    assert state.firmware == "V2.0.08"
    assert state.diagnostics["chunk_types"] == (1, 3)
    assert state.channels[0].cold_white == 0x50


def test_runtime_attach_transport_creates_session() -> None:
    """Runtime can attach a command session when a protocol exists."""
    runtime = build_runtime({CONF_MODEL: "SP601E", CONF_DEVICE_ID: "bench"})
    transport = RecordingTransport()

    session = runtime.attach_transport(transport)

    assert runtime.transport is transport
    assert runtime.session is session
    assert runtime.session_ready is True
    assert runtime.state.diagnostics["session_ready"] is True

    asyncio.run(runtime.async_close())

    assert transport.closed is True
    assert runtime.transport is None
    assert runtime.session is None


def _sptech_sp541e_status_frame() -> bytes:
    settings = bytearray(17)
    settings[2:10] = b"V3.0.11\x00"
    settings[10] = 0x81
    settings[11] = 1
    settings[12] = 2
    settings[13:15] = (300).to_bytes(2, "big")
    settings[16] = 2

    status = bytearray(26)
    status[1] = 0x01
    status[2 + 1] = 1
    status[2 + 4] = 0x02
    status[2 + 5] = 0x01
    status[2 + 7] = 11
    status[2 + 8] = 73

    payload = bytes([0, 1, len(settings), *settings, 3, len(status), *status])
    header = bytes.fromhex("53 50 54 45 43 48 00 02 00 00 00") + len(
        payload
    ).to_bytes(2, "big")
    return header + payload


def test_runtime_attach_transport_requires_protocol() -> None:
    """Models without ported protocols cannot create command sessions yet."""
    runtime = build_runtime({CONF_MODEL: "SP802E", CONF_DEVICE_ID: "bench"})

    try:
        runtime.attach_transport(RecordingTransport())
    except RuntimeSetupError:
        pass
    else:
        raise AssertionError("SP802E has no command protocol yet")
