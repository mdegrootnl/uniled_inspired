"""Notification frame assembly tests."""

from __future__ import annotations

from custom_components.uniled.core import (
    BanlanX2Protocol,
    BanlanX3Protocol,
    BanlanX6xxProtocol,
    BanlanX60xProtocol,
    BanlanX601Protocol,
    ParseNotificationError,
)


def test_banlanx_601_status_assembler_rebuilds_legacy_packets() -> None:
    """SP601E two-part notifications assemble into the legacy payload."""
    protocol = BanlanX601Protocol()
    assembler = protocol.make_status_assembler()
    first = bytes.fromhex(
        "53 43 01 18 0f 00 01 02 ff 0a 1e 01 ff 00 00 10 00 01 02 ff"
    )
    second = bytes.fromhex("53 43 02 18 09 0a 1e 00 00 ff 00 10 00 00")

    assert assembler.feed(first) is None
    payload = assembler.feed(second)

    assert payload is not None
    state = protocol.parse_status(payload)
    assert state.channels[1].rgb == (255, 0, 0)
    assert state.channels[2].rgb == (0, 255, 0)
    assert state.diagnostics["trailing_bytes"] == b"\x00\x00"


def test_banlanx_60x_status_assembler_uses_3638_header() -> None:
    """SP60x notifications use the 0x36 0x38 family marker."""
    protocol = BanlanX60xProtocol(channels=4)
    assembler = protocol.make_status_assembler()
    channel_payload = bytes([1, 2, 3, 128, 5, 0, 240, 1, 10, 20, 30])
    packet = bytes([0x36, 0x38, 1, len(channel_payload), len(channel_payload)])

    payload = assembler.feed(packet + channel_payload)

    assert payload == channel_payload
    assert protocol.parse_status(payload).channels[1].effect_length == 240


def test_banlanx_2_status_assembler_accepts_single_packet_fixture() -> None:
    """BanlanX v2 status can arrive as one complete 0x53 0x43 packet."""
    protocol = BanlanX2Protocol()
    assembler = protocol.make_status_assembler()
    fixture = bytes.fromhex(
        "01 00 be 02 ff 0a 48 00 00 ff 00 10 "
        "09 04 0b 14 1a 32 37 50 53 73 00"
    )
    packet = bytes([0x53, 0x43, 1, len(fixture), len(fixture)])

    payload = assembler.feed(packet + fixture)

    assert payload == fixture
    assert protocol.parse_status(payload).channels[0].effect_number == 0xBE


def test_banlanx_3_status_assembler_rebuilds_indexed_packets() -> None:
    """BanlanX v3 uses a short indexed first/continuation packet format."""
    protocol = BanlanX3Protocol()
    assembler = protocol.make_status_assembler()
    payload = bytes(
        [
            1,
            128,
            5,
            2,
            0xBE,
            0,
            1,
            2,
            3,
            16,
            0xAA,
            0xBB,
            2,
            0x44,
            0x55,
        ]
    )

    assert assembler.feed(bytes([1, len(payload), 9]) + payload[:9]) is None
    result = assembler.feed(bytes([2, len(payload[9:])]) + payload[9:])

    assert result == payload
    assert protocol.parse_status(result).channels[0].audio_input == 2


def test_banlanx_6xx_status_assembler_passes_complete_packet() -> None:
    """SP6xx packets are already framed for the parser."""
    protocol = BanlanX6xxProtocol()
    assembler = protocol.make_status_assembler()
    packet = bytes([0x53, 0x02, 0x00, 0x01, 0x00, 1, 1])

    assert assembler.feed(packet) == packet


def test_status_assembler_rejects_bad_sequence_or_lengths() -> None:
    """Assembler failures are explicit before a parser sees bad payloads."""
    assembler = BanlanX601Protocol().make_status_assembler()

    try:
        assembler.feed(bytes.fromhex("53 43 02 18 00"))
    except ParseNotificationError:
        pass
    else:
        raise AssertionError("continuation without first packet should fail")

    try:
        assembler.feed(bytes.fromhex("53 43 01 02 01 00 00"))
    except ParseNotificationError:
        pass
    else:
        raise AssertionError("payload length mismatch should fail")
