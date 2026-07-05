"""Telink/Zengge mesh packet helper tests."""

from __future__ import annotations

import asyncio

from custom_components.uniled.core.protocols import (
    ZenggeCryptoError,
    ZenggeMeshConnection,
    ZenggeMeshSession,
    ZenggeNodeContext,
    build_brightness_packet,
    build_cct_packet,
    build_effect_packet,
    build_power_packet,
    build_rgb_packet,
    build_state_query_packet,
    build_status_notify_request,
    build_white_packet,
    cct_percentage_to_kelvin,
    crc16,
    crypt_payload,
    decode_zengge_hsv_rgb,
    encrypt_block,
    kelvin_to_cct_percentage,
    make_checksum,
    make_command_packet,
    make_control_payload,
    make_pair_packet,
    make_session_key,
    parse_zengge_notification_block,
    parse_zengge_notification_message,
    zengge_crypto_available,
    zengge_node_kind,
)
from custom_components.uniled.core.state import ParseNotificationError


def _identity_block_encryptor(key: bytes, block: bytes) -> bytes:
    return block


class RecordingZenggeTransport:
    """Characteristic-specific Zengge transport test double."""

    def __init__(self, pair_response: bytes = b"\x0dABCDEFGH") -> None:
        self.pair_response = pair_response
        self.writes: list[tuple[str, bytes, bool]] = []

    async def write_pair(self, payload: bytes) -> bytes | None:
        self.writes.append(("pair", payload, False))
        return None

    async def read_pair(self) -> bytes:
        return self.pair_response

    async def write_status(self, payload: bytes) -> bytes | None:
        self.writes.append(("status", payload, False))
        return None

    async def write_command(
        self,
        payload: bytes,
        *,
        response: bool = False,
    ) -> bytes | None:
        self.writes.append(("command", payload, response))
        return b"ack" if response else None


class YieldingZenggeTransport(RecordingZenggeTransport):
    """Zengge transport double that detects overlapping characteristic writes."""

    def __init__(self, pair_response: bytes = b"\x0dABCDEFGH") -> None:
        super().__init__(pair_response)
        self.active = 0
        self.max_active = 0

    async def write_command(
        self,
        payload: bytes,
        *,
        response: bool = False,
    ) -> bytes | None:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        self.writes.append(("command", payload, response))
        await asyncio.sleep(0)
        self.active -= 1
        return b"ack" if response else None


def test_encrypt_block_preserves_old_uniled_reversal_convention() -> None:
    """The helper owns old UniLED key/block reversal around AES."""
    block = encrypt_block(
        bytes(range(16)),
        b"\x01\x02",
        block_encryptor=_identity_block_encryptor,
    )

    assert block == bytes.fromhex(
        "01 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
    )


def test_checksum_and_payload_crypto_are_deterministic_with_fake_cipher() -> None:
    """Checksum and stream crypto keep the old Telink block construction."""
    key = bytes(range(16))
    nonce = bytes.fromhex("ff ee dd cc 01 01 02 03")
    payload = bytes.fromhex("11 02 d0 11 02 ff 01 ff 00 00 00 00 00 00 00")

    assert make_checksum(
        key,
        nonce,
        payload,
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex("ee ec 0d dd 03 fe 03 fc 0f 00 00 00 00 00 00 00")
    assert crypt_payload(
        key,
        nonce,
        payload,
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex("11 fd 3e cc ce fe 00 fd 03 00 00 00 00 00 00")


def test_make_command_packet_uses_old_uniled_nonce_and_payload_layout() -> None:
    """Command packets match old UniLED Telink/Zengge field order."""
    packet = make_command_packet(
        bytes(range(16)),
        "AA:BB:CC:DD:EE:FF",
        0x0211,
        0xD0,
        bytes.fromhex("ff 01 ff 00 00 00 00 00 00"),
        sequence=bytes.fromhex("01 02 03"),
        block_encryptor=_identity_block_encryptor,
    )

    assert packet == bytes.fromhex(
        "01 02 03 ee ec 11 fd 3e cc ce fe 00 fd 03 00 00 00 00 00 00"
    )


def test_zengge_control_payload_matches_old_uniled_struct_layout() -> None:
    """Control payloads use device type, opcode, values, delay, then gradual."""
    payload = make_control_payload(0x02, 50, 0x06)
    timed_payload = make_control_payload(
        0x02,
        50,
        0x06,
        delay_seconds=1.2,
        gradual_seconds=3.4,
    )

    assert payload == bytes.fromhex("ff 02 32 06 00 00 00 00 00")
    assert timed_payload == bytes.fromhex("ff 02 32 06 00 0c 00 22 00")


def test_zengge_command_builders_match_old_uniled_payloads() -> None:
    """High-level mesh commands wrap old UniLED command payloads."""
    key = bytes(range(16))
    address = "AA:BB:CC:DD:EE:FF"
    node = 0x44

    assert build_status_notify_request() == b"\x01"
    assert build_state_query_packet(
        key,
        address,
        0x0211,
        sequence=bytes.fromhex("04 05 06"),
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex(
        "04 05 06 ee ec 11 fd 34 cc ce 01 04 05 06 00 00 00 00 00 00"
    )
    assert build_power_packet(
        key,
        address,
        node,
        True,
        sequence=bytes.fromhex("07 08 09"),
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex(
        "07 08 09 bb ee 44 ff 3e cc ce fe 06 f7 09 00 00 00 00 00 00"
    )
    assert build_brightness_packet(
        key,
        address,
        node,
        128,
        sequence=bytes.fromhex("0d 0e 0f"),
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex(
        "0d 0e 0f bb ee 44 ff 3e cc ce fe 0f 3c 09 00 00 00 00 00 00"
    )
    assert build_brightness_packet(
        key,
        address,
        node,
        128,
        gradual_seconds=2.5,
        sequence=bytes.fromhex("0d 0e 0f"),
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex(
        "0d 0e 0f bb ee 44 ff 3e cc ce fe 0f 3c 09 00 00 00 19 00 00"
    )
    assert build_rgb_packet(
        key,
        address,
        node,
        1,
        2,
        3,
        sequence=bytes.fromhex("10 11 12"),
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex(
        "10 11 12 bb ee 44 ff 0c cc ce fe 70 10 10 03 00 00 00 00 00"
    )
    assert build_cct_packet(
        key,
        address,
        node,
        4600,
        level=128,
        sequence=bytes.fromhex("13 14 15"),
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex(
        "13 14 15 bb ee 44 ff 0c cc ce fe 71 25 27 00 00 00 00 00 00"
    )
    assert build_white_packet(
        key,
        address,
        node,
        64,
        sequence=bytes.fromhex("01 02 03"),
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex(
        "01 02 03 bb ee 44 ff 0c cc ce fe 60 42 03 00 00 00 00 00 00"
    )
    assert build_effect_packet(
        key,
        address,
        node,
        0x14,
        sequence=bytes.fromhex("04 05 06"),
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex(
        "04 05 06 bb ee 44 ff 03 cc ce fe 10 05 62 00 00 00 00 00 00"
    )
    assert build_effect_packet(
        key,
        address,
        node,
        0x14,
        speed=9,
        level=80,
        sequence=bytes.fromhex("04 05 06"),
        block_encryptor=_identity_block_encryptor,
    ) == bytes.fromhex(
        "04 05 06 bb ee 44 ff 03 cc ce fe 10 0c 56 00 00 00 00 00 00"
    )


def test_zengge_cct_conversion_matches_old_percentage_scale() -> None:
    """Zengge CCT uses a 2800K-6500K percentage byte."""
    assert kelvin_to_cct_percentage(2800) == 0
    assert kelvin_to_cct_percentage(4600) == 49
    assert kelvin_to_cct_percentage(6500) == 100
    assert cct_percentage_to_kelvin(50) == 4650


def test_zengge_hsv_decode_matches_old_uniled_color_helper() -> None:
    """Notification HSV bytes preserve old UniLED's h/255 and s/63 scale."""
    assert decode_zengge_hsv_rgb(127, 47) == (65, 255, 253)


def test_pair_packet_and_session_key_match_old_uniled_inputs() -> None:
    """Pairing packets use mesh name/password XOR and eight-byte randoms."""
    pair = make_pair_packet(
        b"ZenggeMesh",
        b"ZenggeTechnology",
        b"12345678",
        block_encryptor=_identity_block_encryptor,
    )
    session_key = make_session_key(
        b"ZenggeMesh",
        b"ZenggeTechnology",
        b"12345678",
        b"ABCDEFGH",
        block_encryptor=_identity_block_encryptor,
    )

    assert pair == bytes.fromhex("0c 31 32 33 34 35 36 37 38 00 00 00 00 00 00 19 00")
    assert session_key == bytes.fromhex(
        "31 32 33 34 35 36 37 38 41 42 43 44 45 46 47 48"
    )


def test_zengge_mesh_session_pairs_and_builds_node_commands() -> None:
    """The core mesh session stores pair state before building commands."""
    session = ZenggeMeshSession(
        mesh_uuid=0x0211,
        address="AA:BB:CC:DD:EE:FF",
        block_encryptor=_identity_block_encryptor,
    )

    pair = session.build_pair_request(session_random=b"12345678")
    key = session.complete_pairing(b"\x0dABCDEFGH")
    power = session.build_power(0x44, True, sequence=bytes.fromhex("07 08 09"))

    assert session.paired is True
    assert pair == bytes.fromhex("0c 31 32 33 34 35 36 37 38 00 00 00 00 00 00 19 00")
    assert key == bytes.fromhex(
        "31 32 33 34 35 36 37 38 41 42 43 44 45 46 47 48"
    )
    assert session.build_status_request() == b"\x01"
    assert session.build_state_query(sequence=bytes.fromhex("04 05 06")) == (
        bytes.fromhex(
            "04 05 06 ee ec 11 fd 34 cc ce 01 04 05 06 00 00 00 00 00 00"
        )
    )
    assert power == bytes.fromhex(
        "07 08 09 bb ee 44 ff 3e cc ce fe 06 f7 09 00 00 00 00 00 00"
    )


def test_zengge_mesh_session_applies_decrypted_notifications() -> None:
    """Mesh session stores parsed notification state with node context."""
    session = ZenggeMeshSession(mesh_uuid=0x0211, address="AA:BB:CC:DD:EE:FF")
    session.register_node(
        ZenggeNodeContext(
            node_id=0x11,
            node_type=2,
            node_wiring=4,
            name="Strip",
        )
    )

    state = session.apply_decrypted_notification(
        bytes.fromhex(
            "81 98 5d 00 00 27 34 dc 11 02 "
            "11 b1 64 2f 7f 00 00 00 00 00"
        )
    )

    assert session.state is state
    assert state.channel(0x11).rgb == (65, 255, 253)
    assert state.channel(0x11).extra["node_name"] == "Strip"


def test_zengge_mesh_session_fails_visibly_before_pairing() -> None:
    """Command builders require a paired mesh session key."""
    session = ZenggeMeshSession(mesh_uuid=0x0211, address="AA:BB:CC:DD:EE:FF")

    try:
        session.build_power(0x44, True)
    except ZenggeCryptoError as ex:
        assert "not paired" in str(ex)
    else:
        raise AssertionError("unpaired Zengge commands should fail")

    try:
        session.complete_pairing(b"\x0eABCDEFGH", session_random=b"12345678")
    except ZenggeCryptoError as ex:
        assert "rejected" in str(ex)
    else:
        raise AssertionError("Zengge auth errors should fail visibly")


def test_zengge_mesh_connection_uses_characteristic_specific_transport() -> None:
    """Pair/status/command writes use the future BLE mesh transport contract."""
    session = ZenggeMeshSession(
        mesh_uuid=0x0211,
        address="AA:BB:CC:DD:EE:FF",
        block_encryptor=_identity_block_encryptor,
    )
    transport = RecordingZenggeTransport()
    connection = ZenggeMeshConnection(session, transport)

    key = asyncio.run(connection.pair(session_random=b"12345678"))
    asyncio.run(connection.request_status())
    reply = asyncio.run(
        connection.send_power(
            0x44,
            True,
            sequence=bytes.fromhex("07 08 09"),
            response=True,
        )
    )

    assert key == bytes.fromhex(
        "31 32 33 34 35 36 37 38 41 42 43 44 45 46 47 48"
    )
    assert reply == b"ack"
    assert transport.writes == [
        (
            "pair",
            bytes.fromhex(
                "0c 31 32 33 34 35 36 37 38 00 00 00 00 00 00 19 00"
            ),
            False,
        ),
        ("status", b"\x01", False),
        (
            "command",
            bytes.fromhex(
                "07 08 09 bb ee 44 ff 3e cc ce fe 06 f7 09 00 00 00 00 00 00"
            ),
            True,
        ),
    ]


def test_zengge_mesh_connection_serializes_paired_node_commands() -> None:
    """Concurrent paired-node commands do not overlap on the mesh transport."""
    session = ZenggeMeshSession(
        mesh_uuid=0x0211,
        address="AA:BB:CC:DD:EE:FF",
        block_encryptor=_identity_block_encryptor,
    )
    transport = YieldingZenggeTransport()
    connection = ZenggeMeshConnection(session, transport)

    async def scenario() -> None:
        await connection.pair(session_random=b"12345678")
        transport.writes.clear()
        await asyncio.gather(
            connection.send_power(
                0x44,
                True,
                sequence=bytes.fromhex("01 02 03"),
            ),
            connection.send_brightness(
                0x44,
                128,
                sequence=bytes.fromhex("04 05 06"),
            ),
        )

    asyncio.run(scenario())

    assert transport.max_active == 1
    assert [kind for kind, _, _ in transport.writes] == ["command", "command"]


def test_crc16_matches_old_telink_helper() -> None:
    """CRC16 preserves the old Telink polynomial behavior."""
    assert crc16(bytes.fromhex("01 02 03 04")) == 0x2BA1


def test_zengge_notification_block_parses_old_uniled_rgb_status() -> None:
    """A five-byte node block becomes normalized RGB channel state."""
    context = ZenggeNodeContext(
        node_id=0x11,
        node_type=2,
        node_wiring=4,
        address="AA:BB:CC:DD:EE:FF",
        rssi=-57,
        name="Strip",
        area="Kitchen",
    )

    channel = parse_zengge_notification_block(
        bytes.fromhex("11 b1 64 2f 7f"),
        context=context,
    )

    assert channel is not None
    assert channel.channel_id == 0x11
    assert channel.power is True
    assert channel.brightness == 255
    assert channel.rgb == (65, 255, 253)
    assert channel.effect == "Solid"
    assert channel.light_mode == "rgb"
    assert channel.light_mode_number == 0
    assert channel.extra["status"] == "Online"
    assert channel.extra["node_kind"] == "strip"
    assert channel.extra["color_mode"] == "rgb"
    assert channel.extra["color_level"] == 255
    assert channel.extra["supported_color_modes"] == ("rgb", "color_temp")
    assert channel.extra["node_address"] == "AA:BB:CC:DD:EE:FF"


def test_zengge_notification_block_parses_cct_and_dynamic_modes() -> None:
    """CCT and dynamic mode bytes follow old UniLED status semantics."""
    cct = parse_zengge_notification_block(
        bytes((0x22, 0x01, 50, 0x40, 50)),
        context=ZenggeNodeContext(node_id=0x22, node_type=2, node_wiring=7),
    )
    dynamic = parse_zengge_notification_block(
        bytes((0x23, 0x01, 80, 0x80, 0x10)),
        context=ZenggeNodeContext(node_id=0x23, node_type=2, node_wiring=1),
    )

    assert cct is not None
    assert cct.power is True
    assert cct.brightness == 128
    assert cct.color_temp_kelvin == 4650
    assert cct.extra["color_mode"] == "color_temp"
    assert dynamic is not None
    assert dynamic.effect == "?FX?"
    assert dynamic.effect_type == "dynamic"
    assert dynamic.light_mode == "dynamic"


def test_zengge_notification_block_handles_empty_bridge_and_panel_nodes() -> None:
    """Special node IDs remain safe metadata instead of command light state."""
    panel = parse_zengge_notification_block(
        bytes((0x20, 0x01, 100, 0x00, 0x00)),
        context=ZenggeNodeContext(node_id=0x20, node_type=35),
    )
    bridge = parse_zengge_notification_block(bytes((0xFF, 0x01, 0, 0, 0)))

    assert parse_zengge_notification_block(bytes(5)) is None
    assert panel is not None
    assert panel.power is None
    assert panel.brightness is None
    assert panel.extra["node_kind"] == "panel"
    assert bridge is not None
    assert bridge.extra["node_kind"] == "bridge"
    assert zengge_node_kind(2) == "strip"
    assert zengge_node_kind(5) == "bulb"
    assert zengge_node_kind(35) == "panel"
    assert zengge_node_kind(99) == "light"


def test_zengge_notification_message_parses_two_old_uniled_blocks() -> None:
    """A decrypted notification message carries two five-byte node blocks."""
    state = parse_zengge_notification_message(
        bytes.fromhex(
            "81 98 5d 00 00 27 34 dc 11 02 "
            "11 b1 64 2f 7f 10 45 00 00 00"
        ),
        contexts={
            0x11: ZenggeNodeContext(node_id=0x11, node_type=2, node_wiring=4),
            0x10: ZenggeNodeContext(node_id=0x10, node_type=2, node_wiring=2),
        },
    )

    assert state.available is True
    assert set(state.channels) == {0x10, 0x11}
    assert state.channel(0x11).rgb == (65, 255, 253)
    assert state.channel(0x10).power is False
    assert state.channel(0x10).brightness == 255
    assert state.diagnostics["mesh_command"] == 0xDC
    assert state.diagnostics["response_node_id"] == 0x11
    assert state.diagnostics["notification_blocks"] == 2


def test_zengge_notification_message_rejects_unknown_commands() -> None:
    """Only the old UniLED 0xDC notification shape is parsed as node state."""
    try:
        parse_zengge_notification_message(bytes.fromhex("00 00 00 00 00 00 00 db"))
    except ParseNotificationError as ex:
        assert "20 bytes" in str(ex)
    else:
        raise AssertionError("short Zengge message should fail")

    packet = bytearray(20)
    packet[7] = 0xDB
    try:
        parse_zengge_notification_message(packet)
    except ParseNotificationError as ex:
        assert "0xdb" in str(ex)
    else:
        raise AssertionError("unexpected Zengge command should fail")


def test_packet_helpers_reject_unsafe_inputs() -> None:
    """Packet helpers fail visibly for invalid mesh inputs."""
    try:
        make_command_packet(
            bytes(range(16)),
            "AA:BB:CC:DD:EE:FF",
            0x0211,
            0xD0,
            b"\x00" * 11,
            sequence=b"\x01\x02\x03",
            block_encryptor=_identity_block_encryptor,
        )
    except ZenggeCryptoError:
        pass
    else:
        raise AssertionError("oversized mesh command payload should fail")

    try:
        make_pair_packet(
            b"mesh",
            b"pass",
            b"short",
            block_encryptor=_identity_block_encryptor,
        )
    except ZenggeCryptoError:
        pass
    else:
        raise AssertionError("pair randoms must be eight bytes")

    try:
        build_cct_packet(
            bytes(range(16)),
            "AA:BB:CC:DD:EE:FF",
            0x44,
            2000,
            sequence=b"\x01\x02\x03",
            block_encryptor=_identity_block_encryptor,
        )
    except ZenggeCryptoError:
        pass
    else:
        raise AssertionError("CCT outside Zengge range should fail")


def test_crypto_dependency_is_optional_until_real_mesh_session_use() -> None:
    """The module imports without pycryptodome but reports missing AES."""
    if zengge_crypto_available():
        return
    try:
        encrypt_block(bytes(range(16)), b"\x00")
    except ZenggeCryptoError as ex:
        assert "pycryptodome" in str(ex)
    else:
        raise AssertionError("missing AES provider should fail visibly")
