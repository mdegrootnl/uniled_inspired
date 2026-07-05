"""Status parser parity tests."""

from __future__ import annotations

from custom_components.uniled.core import (
    BanlanX2Protocol,
    BanlanX3Protocol,
    BanlanX6xxProtocol,
    BanlanX60xProtocol,
    BanlanX601Protocol,
    BanlanXCustom5xxProtocol,
    LegacyLEDChordProtocol,
    LegacyLEDHueProtocol,
    ParseNotificationError,
    SPTechLANProtocol,
    default_catalog,
    protocol_for_model,
)


def test_banlanx_601_channel_parser_matches_legacy_offsets() -> None:
    """SP601E channel blocks use the same offsets as old UniLED."""
    protocol = BanlanX601Protocol()
    data = bytes([1, 0x02, 0x03, 0x80, 0x05, 0x06, 1, 10, 20, 30, 0x10])

    channel = protocol.parse_channel_status(data, channel=2)

    assert channel.channel_id == 2
    assert channel.power is True
    assert channel.effect == "Rainbow Stars"
    assert channel.effect_number == 0x02
    assert channel.effect_type == "Dynamic"
    assert channel.chip_order == 0x03
    assert channel.brightness == 0x80
    assert channel.effect_speed == 0x05
    assert channel.effect_length == 0x06
    assert channel.effect_direction is True
    assert channel.rgb == (10, 20, 30)
    assert channel.sensitivity == 0x10


def test_banlanx_601_combined_status_builds_master_state() -> None:
    """SP601E combined status produces channels plus an aggregate master."""
    protocol = BanlanX601Protocol()
    ch1 = bytes([1, 0x02, 0x03, 100, 5, 6, 1, 10, 20, 30, 0x10])
    ch2 = bytes([0, 0x03, 0x04, 200, 7, 8, 0, 40, 50, 60, 0x09])

    state = protocol.parse_status(ch1 + ch2 + b"\x00\x00")

    assert state.channels[1].brightness == 100
    assert state.channels[1].effect == "Rainbow Stars"
    assert state.channels[2].power is False
    assert state.channels[2].effect == "Twinkle Stars"
    assert state.channels[0].power is True
    assert state.channels[0].brightness == 150
    assert state.channels[0].effect_loop is False
    assert state.diagnostics["channel_count"] == 2
    assert state.diagnostics["trailing_bytes"] == b"\x00\x00"
    assert state.diagnostics["timer_count"] == 0
    assert state.diagnostics["timer_record_count"] == 0
    assert state.diagnostics["timer_records"] == ()
    assert state.diagnostics["scene_loop"] is False


def test_banlanx_601_tail_preserves_timer_records_for_diagnostics() -> None:
    """SP601E tail timer records stay available as raw diagnostics."""
    protocol = BanlanX601Protocol()
    ch1 = bytes([1, 0x02, 0x03, 100, 5, 6, 1, 10, 20, 30, 0x10])
    ch2 = bytes([0, 0x03, 0x04, 200, 7, 8, 0, 40, 50, 60, 0x09])
    timer = bytes.fromhex("01 02 03 04 05 06 07")

    state = protocol.parse_status(ch1 + ch2 + bytes([1]) + timer + bytes([1]))

    assert state.diagnostics["timer_count"] == 1
    assert state.diagnostics["timer_record_count"] == 1
    assert state.diagnostics["timer_records"] == (timer,)
    assert state.diagnostics["scene_loop"] is True


def test_banlanx_60x_channel_parser_matches_legacy_offsets() -> None:
    """SP602E/SP608E channel blocks keep their two-byte length field."""
    protocol = BanlanX60xProtocol(channels=4)
    data = bytes([1, 0x02, 0x03, 0x80, 0x05, 0x00, 0xF0, 1, 10, 20, 30])

    channel = protocol.parse_channel_status(data, channel=4)

    assert channel.channel_id == 4
    assert channel.power is True
    assert channel.effect == "Rainbow Stars"
    assert channel.effect_number == 0x02
    assert channel.effect_type == "Dynamic"
    assert channel.chip_order == 0x03
    assert channel.brightness == 0x80
    assert channel.effect_speed == 0x05
    assert channel.effect_length == 240
    assert channel.effect_direction is True
    assert channel.rgb == (10, 20, 30)


def test_banlanx_60x_combined_status_parses_legacy_tail() -> None:
    """SP60x tail bytes expose master sensitivity and scene loop."""
    protocol = BanlanX60xProtocol(channels=4)
    ch1 = bytes([1, 0x02, 0x03, 100, 5, 0, 120, 1, 10, 20, 30])
    ch2 = bytes([0, 0x03, 0x04, 200, 7, 0, 80, 0, 40, 50, 60])
    ch3 = bytes([0, 0x04, 0x05, 50, 8, 0, 60, 1, 70, 80, 90])
    ch4 = bytes([0, 0x05, 0x00, 25, 9, 0, 40, 0, 1, 2, 3])
    tail = bytes([9, 0]) + bytes(4 * 13) + bytes([1])

    state = protocol.parse_status(ch1 + ch2 + ch3 + ch4 + tail)

    assert state.channels[0].power is True
    assert state.channels[0].brightness == 93
    assert state.channels[0].sensitivity == 9
    assert state.channels[0].effect_loop is True
    assert state.diagnostics["tail_sensitivity"] == 9
    assert state.diagnostics["timer_count"] == 0
    assert state.diagnostics["timer_record_count"] == 0
    assert state.diagnostics["timer_records"] == ()
    assert state.diagnostics["trigger_record_count"] == 4
    assert state.diagnostics["trigger_records"] == (bytes(13),) * 4
    assert state.diagnostics["scene_loop"] is True


def test_banlanx_2_status_parser_matches_legacy_fixture() -> None:
    """BanlanX v2 status fixture from old UniLED comments parses correctly."""
    protocol = BanlanX2Protocol()
    data = bytes.fromhex(
        "01 00 be 02 ff 0a 48 00 00 ff 00 10 "
        "09 04 0b 14 1a 32 37 50 53 73 00"
    )

    state = protocol.parse_status(data)
    channel = state.channels[0]

    assert channel.power is True
    assert channel.light_mode_number == 0
    assert channel.effect_loop is False
    assert channel.effect == "Solid Color"
    assert channel.effect_number == 0xBE
    assert channel.effect_type == "Static"
    assert channel.chip_order == 0x02
    assert channel.brightness == 0xFF
    assert channel.effect_speed is None
    assert channel.effect_length is None
    assert channel.rgb == (0, 0, 255)
    assert channel.audio_input == 0
    assert channel.sensitivity == 0x10
    assert channel.cold_white == 0x73
    assert channel.warm_white == 0x00
    assert channel.extra["timer_count"] == 0
    assert channel.extra["timer_header"] == bytes.fromhex(
        "09 04 0b 14 1a 32 37 50 53 73"
    )
    assert channel.extra["timer_records"] == ()
    assert state.diagnostics["timer_count"] == 0
    assert state.diagnostics["timer_record_count"] == 0
    assert state.diagnostics["timer_records"] == ()


def test_banlanx_2_status_parser_preserves_timer_records() -> None:
    """BanlanX v2 timer records stay raw until their schema is proven."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP621E")
    assert model is not None
    protocol = protocol_for_model(model)
    assert isinstance(protocol, BanlanX2Protocol)
    timer = bytes.fromhex("00 01 6a 00 93 a8 01")
    data = bytes.fromhex(
        "01 00 0e 02 61 0a 1e ff 00 00 01 10 "
        "09 04 0b 14 1a 32 37 50 53 73 01"
    ) + timer

    state = protocol.parse_status(data)
    channel = state.channels[0]

    assert state.diagnostics["timer_header"] == bytes.fromhex(
        "09 04 0b 14 1a 32 37 50 53 73"
    )
    assert state.diagnostics["timer_count"] == 1
    assert state.diagnostics["timer_record_count"] == 1
    assert state.diagnostics["timer_records"] == (timer,)
    assert channel.extra["timer_count"] == 1
    assert channel.extra["timer_records"] == (timer,)
    assert channel.effect_type == "Dynamic"
    assert channel.effect_speed == 0x0A
    assert channel.effect_length == 0x1E
    assert channel.cold_white is None


def test_banlanx_2_status_parser_auto_modes_gate_effect_attributes() -> None:
    """V2 auto modes force old-UniLED effect type and dynamic attribute rules."""
    protocol = BanlanX2Protocol()
    dynamic_data = bytearray.fromhex(
        "01 01 be 02 ff 0a 48 00 00 ff 00 10 "
        "09 04 0b 14 1a 32 37 50 53 73 00"
    )
    sound_data = bytearray(dynamic_data)
    sound_data[1] = 0x02

    dynamic = protocol.parse_status(bytes(dynamic_data)).channels[0]
    sound = protocol.parse_status(bytes(sound_data)).channels[0]

    assert dynamic.effect == "Solid Color"
    assert dynamic.effect_type == "Dynamic"
    assert dynamic.effect_speed == 0x0A
    assert dynamic.effect_length == 0x48
    assert dynamic.brightness == 0xFF
    assert sound.effect == "Solid Color"
    assert sound.effect_type == "Sound"
    assert sound.brightness is None
    assert sound.effect_speed is None
    assert sound.effect_length is None
    assert sound.extra["color_mode"] == "onoff"


def test_banlanx_3_status_parser_matches_legacy_offsets() -> None:
    """BanlanX v3 status parser keeps input and white bytes at the tail."""
    protocol = BanlanX3Protocol()
    data = bytes(
        [1, 0x80, 0x05, 0x02, 0x63, 0x00, 1, 2, 3, 0x10, 0xAA, 0xBB, 2, 0x44, 0x55]
    )

    channel = protocol.parse_status(data).channels[0]

    assert channel.power is True
    assert channel.brightness == 0x80
    assert channel.effect_speed is None
    assert channel.chip_order == 0x02
    assert channel.effect == "Solid Color"
    assert channel.effect_number == 0x63
    assert channel.effect_type == "Static"
    assert channel.light_mode_number == 0
    assert channel.rgb == (1, 2, 3)
    assert channel.sensitivity == 0x10
    assert channel.audio_input == 2
    assert channel.cold_white == 0x44
    assert channel.warm_white == 0x55
    assert channel.extra["color_level"] == 0x80
    assert channel.extra["white_level"] == 0x44
    assert channel.extra["diy_effect_type"] == 0xAA
    assert channel.extra["diy_color_count"] == 0xBB


def test_banlanx_3_status_parser_preserves_dynamic_speed() -> None:
    """V3 singular dynamic status keeps speed while static statuses clear it."""
    protocol = BanlanX3Protocol()
    data = bytes(
        [1, 0x80, 0x07, 0x02, 0x20, 0x00, 1, 2, 3, 0x10, 0xAA, 0xBB, 2, 0x44, 0x55]
    )

    channel = protocol.parse_status(data).channels[0]

    assert channel.effect == "Adjustable Color Breath"
    assert channel.effect_number == 0x20
    assert channel.effect_type == "Dynamic"
    assert channel.effect_speed == 0x07
    assert channel.brightness == 0x80


def test_banlanx_3_status_parser_auto_modes_gate_effect_attributes() -> None:
    """V3 auto modes force old-UniLED effect type and speed visibility."""
    protocol = BanlanX3Protocol()
    dynamic_data = bytearray(
        [1, 0x80, 0x05, 0x02, 0x63, 0x01, 1, 2, 3, 0x10, 0xAA, 0xBB, 2, 0x44, 0x55]
    )
    sound_data = bytearray(dynamic_data)
    sound_data[5] = 0x02

    dynamic = protocol.parse_status(bytes(dynamic_data)).channels[0]
    sound = protocol.parse_status(bytes(sound_data)).channels[0]

    assert dynamic.effect == "Solid Color"
    assert dynamic.effect_type == "Dynamic"
    assert dynamic.effect_speed == 0x05
    assert dynamic.brightness == 0x80
    assert sound.effect == "Solid Color"
    assert sound.effect_type == "Sound"
    assert sound.brightness is None
    assert sound.effect_speed is None
    assert sound.extra["color_mode"] == "onoff"


def test_model_aware_banlanx_2_status_parser_uses_non_music_profile() -> None:
    """SP621E parsed state follows old UniLED's no-microphone profile."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP621E")
    assert model is not None
    protocol = protocol_for_model(model)
    assert isinstance(protocol, BanlanX2Protocol)

    data = bytes.fromhex(
        "01 00 da 02 61 0a 1e ff 00 00 01 10 "
        "09 04 0b 14 1a 32 37 50 53 73 00"
    )

    state = protocol.parse_status(data)
    channel = state.channels[0]

    assert state.diagnostics["protocol_model"] == "SP621E"
    assert state.diagnostics["audio_controls"] is False
    assert state.diagnostics["white_channel"] is False
    assert channel.effect is None
    assert channel.effect_number == 0xDA
    assert channel.effect_type is None
    assert channel.audio_input is None
    assert channel.sensitivity is None
    assert channel.cold_white is None
    assert channel.warm_white is None


def test_model_aware_banlanx_2_status_parser_uses_rgbw_white_level() -> None:
    """SP617E maps Solid White status to the RGBW white level."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP617E")
    assert model is not None
    protocol = protocol_for_model(model)
    assert isinstance(protocol, BanlanX2Protocol)

    data = bytes(
        [
            1,
            0,
            0xBF,
            0x17,
            0x80,
            0x0A,
            0x1E,
            1,
            2,
            3,
            2,
            0x10,
            9,
            4,
            0x0B,
            0x14,
            0x1A,
            0x32,
            0x37,
            0x50,
            0x53,
            0x44,
            0,
        ]
    )

    state = protocol.parse_status(data)
    channel = state.channels[0]

    assert state.diagnostics["protocol_model"] == "SP617E"
    assert state.diagnostics["white_channel"] is True
    assert channel.effect == "Solid White"
    assert channel.effect_number == 0xBF
    assert channel.brightness == 0x44
    assert channel.audio_input == 2
    assert channel.sensitivity == 0x10
    assert channel.cold_white == 0x44
    assert channel.warm_white == 0
    assert channel.extra["color_level"] == 0x80
    assert channel.extra["white_level"] == 0x44


def test_model_aware_banlanx_2_status_parser_keeps_sound_onoff_only() -> None:
    """SP611E sound status clears HA brightness and preserves color level."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP611E")
    assert model is not None
    protocol = protocol_for_model(model)
    assert isinstance(protocol, BanlanX2Protocol)

    data = bytes.fromhex(
        "01 00 da 02 61 0a 1e ff 00 00 01 10 "
        "09 04 0b 14 1a 32 37 50 53 73 00"
    )

    state = protocol.parse_status(data)
    channel = state.channels[0]

    assert state.diagnostics["protocol_model"] == "SP611E"
    assert state.diagnostics["audio_controls"] is True
    assert channel.effect == "Sound - Party"
    assert channel.effect_number == 0xDA
    assert channel.effect_type == "Sound"
    assert channel.brightness is None
    assert channel.effect_speed is None
    assert channel.effect_length is None
    assert channel.extra["color_level"] == 0x61
    assert channel.extra["color_mode"] == "onoff"


def test_model_aware_banlanx_3_status_parser_keeps_rgbw_without_audio() -> None:
    """SP624E keeps RGBW white bytes while suppressing microphone fields."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP624E")
    assert model is not None
    protocol = protocol_for_model(model)
    assert isinstance(protocol, BanlanX3Protocol)

    data = bytes(
        [1, 0x80, 0x05, 0x02, 0xCC, 0x00, 1, 2, 3, 0x10, 0xAA, 0xBB, 2, 0x44, 0x55]
    )

    state = protocol.parse_status(data)
    channel = state.channels[0]

    assert state.diagnostics["protocol_model"] == "SP624E"
    assert state.diagnostics["audio_controls"] is False
    assert state.diagnostics["white_channel"] is True
    assert channel.effect == "Solid White"
    assert channel.effect_number == 0xCC
    assert channel.effect_type == "Static"
    assert channel.brightness == 0x44
    assert channel.audio_input is None
    assert channel.sensitivity is None
    assert channel.cold_white == 0x44
    assert channel.warm_white == 0x55
    assert channel.extra["color_level"] == 0x80
    assert channel.extra["white_level"] == 0x44
    assert channel.extra["diy_effect_type"] == 0xAA
    assert channel.extra["diy_color_count"] == 0xBB


def test_model_aware_banlanx_3_status_parser_keeps_sound_onoff_only() -> None:
    """SP614E sound status clears HA brightness and preserves color level."""
    catalog = default_catalog()
    model = catalog.resolve_name("SP614E")
    assert model is not None
    protocol = protocol_for_model(model)
    assert isinstance(protocol, BanlanX3Protocol)

    data = bytes(
        [1, 0x77, 0x05, 0x02, 0x65, 0x00, 1, 2, 3, 0x10, 0xAA, 0xBB, 2, 0x44, 0x55]
    )

    state = protocol.parse_status(data)
    channel = state.channels[0]

    assert state.diagnostics["protocol_model"] == "SP614E"
    assert state.diagnostics["audio_controls"] is True
    assert channel.effect == "Sound - Music Breath"
    assert channel.effect_number == 0x65
    assert channel.effect_type == "Sound"
    assert channel.brightness is None
    assert channel.effect_speed is None
    assert channel.extra["color_level"] == 0x77
    assert channel.extra["color_mode"] == "onoff"


def test_banlanx_6xx_status_parser_matches_legacy_offsets() -> None:
    """SP6xx status parser validates the frame and reads known offsets."""
    protocol = BanlanX6xxProtocol()
    packet = _banlanx_6xx_status_packet()

    state = protocol.parse_status(packet)
    channel = state.channels[0]

    assert state.firmware == "1.0.000"
    assert state.diagnostics["light_type"] == 6
    assert state.diagnostics["onoff_effect"] == 1
    assert state.diagnostics["onoff_speed"] == 2
    assert state.diagnostics["onoff_pixels"] == 300
    assert state.diagnostics["coexistence"] == 1
    assert state.diagnostics["on_power"] == 2
    assert channel.power is True
    assert channel.chip_order == 3
    assert channel.light_mode == "Dynamic Color"
    assert channel.light_mode_number == 3
    assert channel.effect == "Dynamic Color - Rainbow Metor"
    assert channel.effect_number == 2
    assert channel.effect_type == "Dynamic"
    assert channel.effect_loop is True
    assert channel.brightness == 128
    assert channel.rgb == (11, 22, 33)
    assert channel.effect_speed == 5
    assert channel.effect_length == 6
    assert channel.effect_direction is True
    assert channel.sensitivity is None
    assert channel.audio_input is None
    assert channel.extra["play"] is None
    assert channel.extra["white_level"] == 64
    assert channel.extra["diy_mode"] == 7


def test_custom_5xx_status_parser_uses_6xx_offsets_with_custom_family() -> None:
    """Custom 5xx status parsing uses SP6xx offsets but keeps its family name."""
    state = BanlanXCustom5xxProtocol().parse_status(_banlanx_6xx_status_packet())

    assert state.diagnostics["protocol_family"] == "banlanx_custom_5xx"
    assert state.diagnostics["light_type"] == 6
    assert state.channels[0].effect == "Dynamic Color - Rainbow Metor"
    assert state.channels[0].rgb == (11, 22, 33)


def test_sptech_lan_status_parser_decodes_sp541e_mono_response() -> None:
    """SPTech chunked LAN status becomes brightness-only SP541E state."""
    state = SPTechLANProtocol().parse_status(_sptech_sp541e_status_frame())
    channel = state.channels[0]

    assert state.firmware == "V3.0.11"
    assert state.diagnostics["protocol_family"] == "sptech_lan"
    assert state.diagnostics["light_type"] == 0x01
    assert state.diagnostics["light_type_name"] == "1 CH PWM - Single Color"
    assert state.diagnostics["onoff_effect"] == 1
    assert state.diagnostics["onoff_speed"] == 2
    assert state.diagnostics["onoff_pixels"] == 300
    assert state.diagnostics["on_power"] == 2
    assert channel.power is True
    assert channel.brightness == 73
    assert channel.light_mode == "Static White"
    assert channel.light_mode_number == 0x02
    assert channel.effect == "Static White - Solid"
    assert channel.effect_number == 0x01
    assert channel.effect_type == "Static"
    assert channel.effect_speed is None
    assert channel.effect_length is None
    assert channel.effect_direction is None
    assert channel.extra["white_level"] == 73


def test_sptech_lan_status_parser_decodes_live_sp541e_capture() -> None:
    """Parser handles a live SP541E TCP response captured from house hardware."""
    data = bytes.fromhex(
        "535054454348000200000000ea01010011002056332e302e313120010303003c000103006d010100010078020101ff03ff0000ffff0a3c011000ff0000ffff010e06ff00000600ff00060000ff0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010400ff00005556d500aa0000ffffd5002b0304010402040304000700000000000000060037000205496e6672610c3139322e3136382e302e383201203964376131376461326333613132643462373233623763333131303130393031070001000a001a01002056332e302e31312004010303003c078000000000000000"
    )

    state = SPTechLANProtocol().parse_status(data)
    channel = state.channels[0]

    assert state.firmware == "V3.0.11"
    assert state.diagnostics["light_type"] == 1
    assert state.diagnostics["onoff_pixels"] == 60
    assert channel.power is True
    assert channel.brightness == 3
    assert channel.light_mode == "Static White"
    assert channel.effect == "Static White - Solid"


def test_sptech_lan_status_parser_gates_dynamic_white_attributes() -> None:
    """SPTech dynamic white status exposes only supported effect controls."""
    frame = bytearray(_sptech_sp541e_status_frame())
    payload_offset = 13
    chunk_3_data_offset = payload_offset + 1 + 1 + 1 + 17 + 1 + 1
    frame[chunk_3_data_offset + 2 + 4] = 0x04
    frame[chunk_3_data_offset + 2 + 5] = 0x01
    frame[chunk_3_data_offset + 2 + 14] = 7
    frame[chunk_3_data_offset + 2 + 15] = 8

    channel = SPTechLANProtocol().parse_status(bytes(frame)).channels[0]

    assert channel.light_mode == "Dynamic White"
    assert channel.effect == "Dynamic White - White Color Breath"
    assert channel.effect_type == "Dynamic"
    assert channel.effect_speed == 7
    assert channel.effect_length is None


def test_legacy_led_chord_assembles_and_parses_status_packets() -> None:
    """SP107E keeps old UniLED's two-packet LED Chord status layout."""
    protocol = LegacyLEDChordProtocol()
    packet = bytes(
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
    assembler = protocol.make_status_assembler()

    assert assembler.feed(b"\x00\x01" + packet[:13]) is None
    assembled = assembler.feed(b"\x00\x02" + packet[13:])
    assert assembled == packet

    state = protocol.parse_status(assembled)
    channel = state.channels[0]

    assert channel.power is True
    assert channel.brightness == 100
    assert channel.rgbw == (10, 20, 30, 20)
    assert channel.effect == "Solid"
    assert channel.effect_number == 0xB5
    assert channel.effect_type == "Static"
    assert channel.light_mode == "Single FX"
    assert channel.light_mode_number == 0
    assert channel.effect_speed is None
    assert channel.sensitivity is None
    assert channel.chip_order == 2
    assert channel.extra["chip_type"] == 3
    assert channel.extra["segment_count"] == 4
    assert channel.extra["segment_pixels"] == 5
    assert channel.extra["total_pixels"] == 20


def test_legacy_led_hue_parses_status_with_optional_leading_byte() -> None:
    """SP110E keeps old UniLED's 12-byte LED Hue status layout."""
    protocol = LegacyLEDHueProtocol()
    packet = bytes([1, 0x79, 5, 128, 3, 2, 0, 150, 10, 20, 30, 40])
    state = protocol.parse_status(b"\xff" + packet)
    channel = state.channels[0]

    assert channel.power is True
    assert channel.brightness == 128
    assert channel.rgbw == (10, 20, 30, 40)
    assert channel.effect == "Solid"
    assert channel.effect_number == 0x79
    assert channel.effect_type == "Static"
    assert channel.effect_speed is None
    assert channel.effect_loop is False
    assert channel.chip_order == 2
    assert channel.extra["chip_type"] == 3
    assert channel.extra["segment_pixels"] == 150

    auto_state = protocol.parse_status(
        bytes([1, 0, 6, 80, 2, 1, 0, 60, 7, 8, 9, 0])
    )
    auto = auto_state.channels[0]
    assert auto.effect == "Auto Cycle FX's"
    assert auto.effect_type == "Dynamic"
    assert auto.effect_speed == 6
    assert auto.effect_loop is True
    assert auto.rgb == (7, 8, 9)


def test_banlanx_6xx_status_parser_maps_richer_light_types() -> None:
    """SP6xx status parser maps RGBW, RGBWW, and CCT light-type channels."""
    protocol = BanlanX6xxProtocol()

    rgbw_packet = bytearray(_banlanx_6xx_status_packet())
    rgbw_packet[19] = 0x08
    rgbw_packet[24] = 1
    rgbw_packet[32] = 0x01
    rgbw_packet[33] = 0x01
    rgbw_state = protocol.parse_status(bytes(rgbw_packet)).channels[0]

    assert rgbw_state.rgbw == (10, 20, 30, 64)
    assert rgbw_state.rgbww is None
    assert rgbw_state.brightness == 128

    rgbww_packet = bytearray(_banlanx_6xx_status_packet())
    rgbww_packet[19] = 0x0B
    rgbww_packet[24] = 1
    rgbww_packet[32] = 0x01
    rgbww_packet[33] = 0x01
    rgbww_packet[40] = 44
    rgbww_packet[41] = 55
    rgbww_state = protocol.parse_status(bytes(rgbww_packet)).channels[0]

    assert rgbww_state.rgbww == (10, 20, 30, 44, 55)
    assert rgbww_state.rgbw is None
    assert rgbww_state.cold_white == 44
    assert rgbww_state.warm_white == 55

    cct_packet = bytearray(_banlanx_6xx_status_packet())
    cct_packet[19] = 0x04
    cct_packet[32] = 0x02
    cct_packet[33] = 0x01
    cct_packet[36] = 155
    cct_packet[40] = 100
    cct_packet[41] = 155
    cct_state = protocol.parse_status(bytes(cct_packet)).channels[0]

    assert cct_state.rgbw is None
    assert cct_state.rgbww is None
    assert cct_state.brightness == 155
    assert cct_state.cold_white == 100
    assert cct_state.warm_white == 155
    assert cct_state.color_temp_kelvin == 4190

    dynamic_white_packet = bytearray(_banlanx_6xx_status_packet())
    dynamic_white_packet[19] = 0x04
    dynamic_white_packet[32] = 0x04
    dynamic_white_packet[33] = 0x01
    dynamic_white_packet[36] = 120
    dynamic_white_packet[50] = 45
    dynamic_white_packet[51] = 210
    dynamic_white_state = protocol.parse_status(bytes(dynamic_white_packet)).channels[0]

    assert dynamic_white_state.brightness == 120
    assert dynamic_white_state.cold_white == 45
    assert dynamic_white_state.warm_white == 210
    assert dynamic_white_state.color_temp_kelvin == 3371


def test_banlanx_6xx_status_parser_reports_sound_modes_full_brightness() -> None:
    """SP6xx sound modes mirror old UniLED's full-brightness status state."""
    protocol = BanlanX6xxProtocol()

    sound_color_packet = bytearray(_banlanx_6xx_status_packet())
    sound_color_packet[32] = 0x05
    sound_color_packet[33] = 0x01
    sound_color_packet[35] = 37
    sound_color_state = protocol.parse_status(bytes(sound_color_packet)).channels[0]

    assert sound_color_state.light_mode == "Sound - Color"
    assert sound_color_state.effect_type == "Sound"
    assert sound_color_state.brightness == 0xFF
    assert sound_color_state.rgb == (11, 22, 33)
    assert sound_color_state.sensitivity == 16
    assert sound_color_state.audio_input == 2
    assert sound_color_state.extra["color_level"] == 37

    sound_white_packet = bytearray(_banlanx_6xx_status_packet())
    sound_white_packet[19] = 0x04
    sound_white_packet[32] = 0x06
    sound_white_packet[33] = 0x01
    sound_white_packet[36] = 22
    sound_white_packet[50] = 80
    sound_white_packet[51] = 120
    sound_white_state = protocol.parse_status(bytes(sound_white_packet)).channels[0]

    assert sound_white_state.light_mode == "Sound - White"
    assert sound_white_state.effect_type == "Sound"
    assert sound_white_state.brightness == 0xFF
    assert sound_white_state.cold_white == 80
    assert sound_white_state.warm_white == 120
    assert sound_white_state.sensitivity == 16
    assert sound_white_state.audio_input == 2
    assert sound_white_state.extra["white_level"] == 22

    powered_off_sound = bytearray(sound_color_packet)
    powered_off_sound[29] = 0
    powered_off_state = protocol.parse_status(bytes(powered_off_sound)).channels[0]

    assert powered_off_state.power is False
    assert powered_off_state.sensitivity is None
    assert powered_off_state.audio_input is None


def test_banlanx_6xx_status_parser_gates_effect_parameters_by_effect() -> None:
    """SP6xx speed/size/direction/play follow old-UniLED effect attributes."""
    protocol = BanlanX6xxProtocol()

    pausable_packet = bytearray(_banlanx_6xx_status_packet())
    pausable_packet[19] = 0x06
    pausable_packet[32] = 0x03
    pausable_packet[33] = 0x01
    pausable_state = protocol.parse_status(bytes(pausable_packet)).channels[0]

    assert pausable_state.effect == "Dynamic Color - Rainbow"
    assert pausable_state.effect_speed == 5
    assert pausable_state.effect_length == 6
    assert pausable_state.effect_direction is True
    assert pausable_state.extra["play"] is True

    pwm_packet = bytearray(_banlanx_6xx_status_packet())
    pwm_packet[19] = 0x05
    pwm_packet[32] = 0x03
    pwm_packet[33] = 0x01
    pwm_state = protocol.parse_status(bytes(pwm_packet)).channels[0]

    assert pwm_state.effect == "Dynamic Color - Seven Color Jump"
    assert pwm_state.effect_speed == 5
    assert pwm_state.effect_length is None
    assert pwm_state.effect_direction is None
    assert pwm_state.extra["play"] is None

    static_packet = bytearray(_banlanx_6xx_status_packet())
    static_packet[32] = 0x01
    static_packet[33] = 0x01
    static_state = protocol.parse_status(bytes(static_packet)).channels[0]

    assert static_state.effect == "Static Color - Solid"
    assert static_state.effect_speed is None
    assert static_state.effect_length is None
    assert static_state.effect_direction is None
    assert static_state.extra["play"] is None

    sound_packet = bytearray(_banlanx_6xx_status_packet())
    sound_packet[32] = 0x05
    sound_packet[33] = 0x05
    sound_state = protocol.parse_status(bytes(sound_packet)).channels[0]

    assert sound_state.effect == "Sound - Color - Sound - Gradient Energy"
    assert sound_state.effect_speed is None
    assert sound_state.effect_length == 6
    assert sound_state.effect_direction is None
    assert sound_state.extra["play"] is None


def test_banlanx_6xx_status_parser_gates_effect_loop_by_mode() -> None:
    """SP6xx effect-loop status is only valid in old-UniLED loopable modes."""
    protocol = BanlanX6xxProtocol()

    dynamic_packet = bytearray(_banlanx_6xx_status_packet())
    dynamic_packet[32] = 0x03
    dynamic_packet[30] = 1
    dynamic_state = protocol.parse_status(bytes(dynamic_packet)).channels[0]

    assert dynamic_state.effect_loop is True

    static_packet = bytearray(_banlanx_6xx_status_packet())
    static_packet[32] = 0x01
    static_packet[30] = 1
    static_state = protocol.parse_status(bytes(static_packet)).channels[0]

    assert static_state.light_mode == "Static Color"
    assert static_state.effect_loop is None

    custom_packet = bytearray(_banlanx_6xx_status_packet())
    custom_packet[32] = 0x07
    custom_packet[30] = 1
    custom_state = protocol.parse_status(bytes(custom_packet)).channels[0]

    assert custom_state.light_mode == "Custom"
    assert custom_state.effect_loop is None


def test_status_parsers_reject_short_or_encoded_packets() -> None:
    """Parser failures are explicit and do not return partial state."""
    try:
        BanlanX2Protocol().parse_status(b"\x01\x00")
    except ParseNotificationError:
        pass
    else:
        raise AssertionError("short BanlanX v2 status should fail")

    encoded = bytearray(_banlanx_6xx_status_packet())
    encoded[2] = 1
    try:
        BanlanX6xxProtocol().parse_status(bytes(encoded))
    except ParseNotificationError:
        pass
    else:
        raise AssertionError("encoded SP6xx status should fail until supported")


def _banlanx_6xx_status_packet() -> bytes:
    packet = bytearray([0x53, 0x02, 0x00, 0x01, 0x00, 48, *([0] * 48)])
    packet[11:18] = b"1.0.000"
    packet[19] = 6
    packet[20] = 1
    packet[21] = 2
    packet[22:24] = (300).to_bytes(2, "big")
    packet[24] = 1
    packet[25] = 2
    packet[29] = 1
    packet[30] = 1
    packet[31] = 3
    packet[32] = 3
    packet[33] = 2
    packet[34] = 1
    packet[35] = 128
    packet[36] = 64
    packet[37:40] = bytes([10, 20, 30])
    packet[47:50] = bytes([11, 22, 33])
    packet[42] = 5
    packet[43] = 6
    packet[44] = 1
    packet[45] = 16
    packet[46] = 2
    packet[52] = 7
    return bytes(packet)


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

    payload = bytes([0x00, 0x01, len(settings), *settings, 0x03, len(status), *status])
    header = bytes.fromhex("53 50 54 45 43 48 00 02 00 00 00") + len(
        payload
    ).to_bytes(2, "big")
    return header + payload
