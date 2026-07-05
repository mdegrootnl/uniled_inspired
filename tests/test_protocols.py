"""Protocol command parity tests."""

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
    ProtocolCommandError,
    SPTechLANProtocol,
    UnsupportedCommand,
    default_catalog,
    protocol_for_model,
)


def test_protocol_registry_routes_legacy_parity_families() -> None:
    """Legacy parity model names resolve to command builders."""
    catalog = default_catalog()

    expected = {
        "SP601E": BanlanX601Protocol,
        "SP602E": BanlanX60xProtocol,
        "SP611E": BanlanX2Protocol,
        "SP613E": BanlanX3Protocol,
        "SP630E": BanlanX6xxProtocol,
        "SP65CE": BanlanX6xxProtocol,
        "SP530E": BanlanXCustom5xxProtocol,
        "SP107E": LegacyLEDChordProtocol,
        "SP110E": LegacyLEDHueProtocol,
    }

    for name, protocol_type in expected.items():
        model = catalog.resolve_name(name)
        assert model is not None

        assert isinstance(protocol_for_model(model), protocol_type), name

    sp602 = catalog.resolve_name("SP602E")
    sp608 = catalog.resolve_name("SP608E")
    assert sp602 is not None
    assert sp608 is not None

    sp602_protocol = protocol_for_model(sp602)
    sp608_protocol = protocol_for_model(sp608)

    assert isinstance(sp602_protocol, BanlanX60xProtocol)
    assert isinstance(sp608_protocol, BanlanX60xProtocol)
    assert sp602_protocol.channels == 4
    assert sp608_protocol.channels == 8
    assert sp602_protocol.triggers == 4
    assert sp608_protocol.triggers == 4


def test_banlanx_601_commands_match_legacy_payloads() -> None:
    """SP601E commands preserve legacy bytes and fan out aggregate light writes."""
    protocol = BanlanX601Protocol()

    assert protocol.build_state_query() == bytes.fromhex("aa 2f 00")
    assert protocol.build_power(True) == (
        bytes.fromhex("aa 22 02 00 01"),
        bytes.fromhex("aa 22 02 01 01"),
    )
    assert protocol.build_power(False, channel=1) == bytes.fromhex("aa 22 02 00 00")
    assert protocol.build_brightness(64) == (
        bytes.fromhex("aa 25 02 00 40"),
        bytes.fromhex("aa 25 02 01 40"),
    )
    assert protocol.build_brightness(64, channel=1) == bytes.fromhex("aa 25 02 00 40")
    assert protocol.build_rgb_color(1, 2, 3) == (
        bytes.fromhex("aa 29 05 00 01 02 03 ff"),
        bytes.fromhex("aa 29 05 01 01 02 03 ff"),
    )
    assert protocol.build_rgb_color(1, 2, 3, channel=2) == (
        bytes.fromhex("aa 29 05 01 01 02 03 ff"),
    )
    assert protocol.build_effect(0x08, channel=1) == bytes.fromhex(
        "aa 23 02 00 08"
    )
    try:
        protocol.build_effect(0x08)
    except ProtocolCommandError as ex:
        assert "physical output channel" in str(ex)
    else:
        raise AssertionError("SP601E should reject aggregate effect commands")
    assert protocol.build_effect_speed(5, channel=1) == bytes.fromhex(
        "aa 26 02 00 05"
    )
    assert protocol.build_effect_length(6, channel=1) == bytes.fromhex(
        "aa 27 02 00 06"
    )
    assert protocol.build_audio_input(2, channel=1) == bytes.fromhex(
        "aa 28 02 00 02"
    )
    assert protocol.build_sensitivity(4, channel=1) == bytes.fromhex(
        "aa 2b 02 00 04"
    )
    try:
        protocol.build_effect_loop(True)
    except UnsupportedCommand as ex:
        assert "effect loop" in str(ex)
    else:
        raise AssertionError("SP601E should not expose lighting effect loop")
    for builder in (
        lambda: protocol.build_effect_speed(5),
        lambda: protocol.build_effect_length(6),
        lambda: protocol.build_effect_direction(True),
        lambda: protocol.build_sensitivity(4),
        lambda: protocol.build_chip_order(2),
    ):
        try:
            builder()
        except ProtocolCommandError as ex:
            assert "output-scoped" in str(ex)
        else:
            raise AssertionError("SP601E should reject aggregate output controls")
    assert protocol.build_scene_loop(True) == bytes.fromhex("aa 30 01 01")
    assert protocol.build_chip_order(2, channel=1) == bytes.fromhex(
        "aa 24 02 00 02"
    )
    assert protocol.build_scene(8) == bytes.fromhex("aa 2e 01 08")


def test_banlanx_60x_commands_match_legacy_payloads() -> None:
    """SP602E/SP608E command bytes match old UniLED command behavior."""
    protocol = BanlanX60xProtocol()

    assert protocol.build_state_query() == bytes.fromhex("88 8f 00")
    assert protocol.build_power(True) == bytes.fromhex("88 82 02 ff 01")
    assert protocol.build_power(False, channel=4) == bytes.fromhex("88 82 02 08 00")
    assert protocol.build_brightness(64, channel=2) == bytes.fromhex(
        "88 85 02 02 40"
    )
    assert protocol.build_rgb_color(1, 2, 3, channel=1) == (
        bytes.fromhex("88 89 05 01 01 02 03 ff"),
    )
    assert protocol.build_effect(0x08, channel=1) == bytes.fromhex(
        "88 83 02 01 08"
    )
    try:
        protocol.build_effect(0x08)
    except ProtocolCommandError as ex:
        assert "physical output channel" in str(ex)
    else:
        raise AssertionError("SP60x should reject aggregate effect commands")
    assert protocol.build_effect_length(240, channel=1) == bytes.fromhex(
        "88 87 03 01 00 f0"
    )
    for builder in (
        lambda: protocol.build_effect_speed(5),
        lambda: protocol.build_effect_length(6),
        lambda: protocol.build_effect_direction(True),
        lambda: protocol.build_chip_order(2),
    ):
        try:
            builder()
        except ProtocolCommandError as ex:
            assert "output-scoped" in str(ex)
        else:
            raise AssertionError("SP60x should reject aggregate output controls")
    assert protocol.build_sensitivity(4) == bytes.fromhex("88 8b 02 ff 04")
    try:
        protocol.build_effect_loop(True)
    except UnsupportedCommand as ex:
        assert "effect loop" in str(ex)
    else:
        raise AssertionError("SP60x should not expose lighting effect loop")
    assert protocol.build_scene_loop(True) == bytes.fromhex("88 90 01 01")
    assert protocol.build_chip_order(2, channel=2) == bytes.fromhex(
        "88 84 02 02 02"
    )
    assert protocol.build_scene(8) == bytes.fromhex("88 8e 01 08")

    sp602 = BanlanX60xProtocol(channels=4)
    assert sp602.build_power(True, channel=4) == bytes.fromhex("88 82 02 08 01")
    try:
        sp602.build_power(True, channel=5)
    except ProtocolCommandError as ex:
        assert "0..4" in str(ex)
    else:
        raise AssertionError("SP602E should reject channel 5")


def test_banlanx_2_commands_match_legacy_payloads() -> None:
    """SP611E/SP616E/SP617E/SP620E/SP621E bytes match old UniLED behavior."""
    protocol = BanlanX2Protocol()

    assert protocol.build_state_query() == bytes.fromhex("a0 70 00")
    assert protocol.build_power(True) == bytes.fromhex("a0 62 01 01")
    assert protocol.build_brightness(64) == bytes.fromhex("a0 66 01 40")
    assert protocol.build_rgb_color(1, 2, 3, level=128) == (
        bytes.fromhex("a0 69 04 01 02 03 80"),
    )
    assert protocol.build_effect(5) == bytes.fromhex("a0 63 01 05")
    assert protocol.build_effect_speed(6) == bytes.fromhex("a0 67 01 06")
    assert protocol.build_effect_length(7) == bytes.fromhex("a0 68 01 07")
    assert protocol.build_effect_loop(True) == bytes.fromhex("a0 6a 01 01")
    assert protocol.build_audio_input(2) == bytes.fromhex("a0 6c 01 02")
    assert protocol.build_chip_order(2) == bytes.fromhex("a0 64 01 02")


def test_banlanx_3_commands_match_legacy_payloads() -> None:
    """SP613E/SP614E/SP623E/SP624E bytes match old UniLED behavior."""
    protocol = BanlanX3Protocol()

    assert protocol.build_state_query() == bytes.fromhex("1d 00")
    assert protocol.build_power(True) == bytes.fromhex("0f 01 01")
    assert protocol.build_brightness(64) == bytes.fromhex("12 01 40")
    assert protocol.build_rgb_color(1, 2, 3, level=128) == (
        bytes.fromhex("13 04 01 02 03 80"),
    )
    assert protocol.build_effect(5) == bytes.fromhex("15 01 05")
    assert protocol.build_effect_speed(6) == bytes.fromhex("14 01 06")
    assert protocol.build_effect_loop(True) == bytes.fromhex("16 01 01")
    assert protocol.build_audio_input(2) == bytes.fromhex("19 01 02")
    assert protocol.build_chip_order(2) == bytes.fromhex("02 00 00 3c")


def test_model_aware_banlanx_2_commands_reject_unsupported_profile_values() -> None:
    """Concrete BanlanX v2 profiles reject unsupported old-UniLED controls."""
    catalog = default_catalog()
    sp621 = catalog.resolve_name("SP621E")
    sp617 = catalog.resolve_name("SP617E")
    assert sp621 is not None
    assert sp617 is not None
    sp621_protocol = protocol_for_model(sp621)
    sp617_protocol = protocol_for_model(sp617)
    assert isinstance(sp621_protocol, BanlanX2Protocol)
    assert isinstance(sp617_protocol, BanlanX2Protocol)

    assert sp621_protocol.build_effect(0xBE) == bytes.fromhex("a0 63 01 be")
    assert sp621_protocol.build_effect_loop(True) == bytes.fromhex("a0 6a 01 01")
    assert sp617_protocol.build_effect(0xDA) == bytes.fromhex("a0 63 01 da")
    assert sp617_protocol.build_light_mode(2) == bytes.fromhex("a0 6a 01 02")
    assert sp617_protocol.build_audio_input(2) == bytes.fromhex("a0 6c 01 02")
    assert sp617_protocol.build_chip_order(23) == bytes.fromhex("a0 64 01 17")
    assert sp617_protocol.build_white_level(0x44) == (
        bytes.fromhex("a0 63 01 bf"),
        bytes.fromhex("a0 76 02 44 00"),
    )
    assert sp617_protocol.build_rgbw_color(1, 2, 3, 4, level=128) == (
        bytes.fromhex("a0 69 04 01 02 03 80"),
        bytes.fromhex("a0 76 02 04 00"),
    )

    for builder in (
        lambda: sp621_protocol.build_effect(0xDA),
        lambda: sp621_protocol.build_light_mode(2),
        lambda: sp621_protocol.build_audio_input(2),
        lambda: sp621_protocol.build_sensitivity(8),
        lambda: sp621_protocol.build_chip_order(6),
        lambda: sp621_protocol.build_white_level(0x44),
        lambda: sp621_protocol.build_rgbw_color(1, 2, 3, 4),
    ):
        try:
            builder()
        except ProtocolCommandError:
            pass
        else:
            raise AssertionError("SP621E should reject unsupported command value")


def test_model_aware_banlanx_3_commands_reject_unsupported_profile_values() -> None:
    """Concrete BanlanX v3 profiles reject unsupported old-UniLED controls."""
    catalog = default_catalog()
    sp623 = catalog.resolve_name("SP623E")
    sp624 = catalog.resolve_name("SP624E")
    assert sp623 is not None
    assert sp624 is not None
    sp623_protocol = protocol_for_model(sp623)
    sp624_protocol = protocol_for_model(sp624)
    assert isinstance(sp623_protocol, BanlanX3Protocol)
    assert isinstance(sp624_protocol, BanlanX3Protocol)

    assert sp623_protocol.build_effect(0x63) == bytes.fromhex("15 01 63")
    assert sp623_protocol.build_effect_loop(True) == bytes.fromhex("16 01 01")
    assert sp624_protocol.build_effect(0xCC) == bytes.fromhex("15 01 cc")
    assert sp624_protocol.build_chip_order(23) == bytes.fromhex("17 00 00 3c")
    assert sp624_protocol.build_white_level(0x44) == (
        bytes.fromhex("15 01 cc"),
        bytes.fromhex("21 02 44 ff"),
    )

    for builder in (
        lambda: sp623_protocol.build_effect(0x65),
        lambda: sp623_protocol.build_effect(0xCC),
        lambda: sp623_protocol.build_light_mode(2),
        lambda: sp623_protocol.build_audio_input(2),
        lambda: sp623_protocol.build_sensitivity(8),
        lambda: sp623_protocol.build_chip_order(6),
        lambda: sp623_protocol.build_white_level(0x44),
        lambda: sp624_protocol.build_audio_input(2),
        lambda: sp624_protocol.build_sensitivity(8),
        lambda: sp624_protocol.build_light_mode(2),
    ):
        try:
            builder()
        except ProtocolCommandError:
            pass
        else:
            raise AssertionError("BanlanX v3 profile should reject command value")


def test_banlanx_6xx_commands_match_legacy_payloads() -> None:
    """SP63x/SP64x/SP65x command bytes match old UniLED encoder behavior."""
    protocol = BanlanX6xxProtocol()

    assert protocol.build_state_query() == bytes.fromhex("53 02 00 01 00 01 01")
    assert protocol.build_power(True) == bytes.fromhex("53 50 00 01 00 01 01")
    assert protocol.build_brightness(64) == bytes.fromhex("53 51 00 01 00 02 00 40")
    assert protocol.build_rgb_color(1, 2, 3, level=128) == (
        bytes.fromhex("53 52 00 01 00 04 01 02 03 80"),
    )
    assert protocol.build_dynamic_rgb_color(1, 2, 3) == bytes.fromhex(
        "53 57 00 01 00 03 01 02 03"
    )
    assert protocol.build_white_level(64) == bytes.fromhex(
        "53 51 00 01 00 02 01 40"
    )
    assert protocol.build_cct_color(10, 20) == bytes.fromhex(
        "53 61 00 01 00 02 0a 14"
    )
    assert protocol.build_cct_color(10, 20, static=False) == bytes.fromhex(
        "53 60 00 01 00 02 0a 14"
    )
    assert protocol.build_rgbw_color(1, 2, 3, 4, level=128) == (
        bytes.fromhex("53 52 00 01 00 04 01 02 03 80"),
        bytes.fromhex("53 51 00 01 00 02 01 04"),
    )
    assert protocol.build_rgbww_color(1, 2, 3, 4, 5, level=128) == (
        bytes.fromhex("53 52 00 01 00 04 01 02 03 80"),
        bytes.fromhex("53 61 00 01 00 02 04 05"),
    )
    assert protocol.build_effect_speed(6) == bytes.fromhex(
        "53 54 00 01 00 01 06"
    )
    assert protocol.build_effect_length(7) == bytes.fromhex(
        "53 55 00 01 00 01 07"
    )
    assert protocol.build_effect_direction(True) == bytes.fromhex(
        "53 56 00 01 00 01 01"
    )
    assert protocol.build_effect_loop(False) == bytes.fromhex(
        "53 58 00 01 00 01 00"
    )
    assert protocol.build_light_mode(0x03, 0x02) == bytes.fromhex(
        "53 53 00 01 00 02 03 02"
    )
    assert protocol.build_audio_input(2) == bytes.fromhex("53 59 00 01 00 01 02")
    assert protocol.build_sensitivity(4) == bytes.fromhex("53 5a 00 01 00 01 04")
    assert protocol.build_onoff_config(3, 2, 300) == bytes.fromhex(
        "53 08 00 01 00 05 01 03 02 01 2c"
    )
    assert protocol.build_coexistence(True) == bytes.fromhex(
        "53 0a 00 01 00 01 01"
    )
    assert protocol.build_on_power(2) == bytes.fromhex("53 0b 00 01 00 01 02")
    assert protocol.build_effect_play(False) == bytes.fromhex(
        "53 5d 00 01 00 01 00"
    )
    assert protocol.build_chip_order(2) == bytes.fromhex("53 6b 00 01 00 01 02")
    assert protocol.build_light_type(
        0x86,
        2,
        0x03,
        0x01,
        power=True,
        refresh=True,
    ) == (
        bytes.fromhex("53 50 00 01 00 01 00"),
        bytes.fromhex("53 6a 00 01 00 02 01 06"),
        bytes.fromhex("53 6b 00 01 00 01 02"),
        bytes.fromhex("53 53 00 01 00 02 03 01"),
        bytes.fromhex("53 02 00 01 00 01 01"),
    )


def test_custom_5xx_uses_6xx_wire_payloads_with_own_family_name() -> None:
    """SP52x/SP53x/SP54x models use the APK-matched SP6xx byte format."""
    protocol = BanlanXCustom5xxProtocol()

    assert protocol.name == "banlanx_custom_5xx"
    assert protocol.build_state_query() == bytes.fromhex("53 02 00 01 00 01 01")
    assert protocol.build_power(True) == bytes.fromhex("53 50 00 01 00 01 01")
    assert protocol.build_rgb_color(1, 2, 3, level=128) == (
        bytes.fromhex("53 52 00 01 00 04 01 02 03 80"),
    )


def test_legacy_led_chord_commands_match_old_uniled_payloads() -> None:
    """SP107E command bytes match old UniLED LED Chord behavior."""
    protocol = LegacyLEDChordProtocol()

    assert protocol.build_state_query() == bytes.fromhex("00 00 00 02")
    assert protocol.build_power(True) == bytes.fromhex("00 00 00 aa")
    assert protocol.build_power(False) == bytes.fromhex("00 00 00 bb")
    assert protocol.build_brightness(64) == bytes.fromhex("40 00 00 0a")
    assert protocol.build_white_level(65) == bytes.fromhex("41 00 00 0b")
    assert protocol.build_rgb_color(1, 2, 3) == (bytes.fromhex("01 02 03 0c"),)
    assert protocol.build_rgbw_color(1, 2, 3, 4) == (
        bytes.fromhex("01 02 03 0c"),
        bytes.fromhex("04 00 00 0b"),
    )
    assert protocol.build_effect(0xB5) == bytes.fromhex("b5 00 00 08")
    assert protocol.build_light_mode(1) == bytes.fromhex("01 00 00 0d")
    assert protocol.build_light_mode(2) == bytes.fromhex("01 00 00 0f")
    assert protocol.build_light_mode(3) == bytes.fromhex("01 00 00 12")
    assert protocol.build_effect_speed(6) == bytes.fromhex("06 00 00 09")
    assert protocol.build_sensitivity(7) == bytes.fromhex("07 00 00 13")
    assert protocol.build_chip_order(2) == bytes.fromhex("02 00 00 04")


def test_legacy_led_hue_commands_match_old_uniled_payloads() -> None:
    """SP110E command bytes match old UniLED LED Hue behavior."""
    protocol = LegacyLEDHueProtocol()

    assert protocol.build_state_query() == bytes.fromhex("00 00 00 10")
    assert protocol.build_power(True) == bytes.fromhex("00 00 00 aa")
    assert protocol.build_power(False) == bytes.fromhex("00 00 00 ab")
    assert protocol.build_brightness(64) == bytes.fromhex("40 00 00 2a")
    assert protocol.build_white_level(65) == bytes.fromhex("41 00 00 69")
    assert protocol.build_rgb_color(1, 2, 3) == (bytes.fromhex("01 02 03 1e"),)
    assert protocol.build_rgbw_color(1, 2, 3, 4) == (
        bytes.fromhex("01 02 03 1e"),
        bytes.fromhex("04 00 00 69"),
    )
    assert protocol.build_effect(0x79) == bytes.fromhex("79 00 00 2c")
    assert protocol.build_effect_loop(True) == bytes.fromhex("00 00 00 06")
    assert protocol.build_effect_loop(False) == bytes.fromhex("79 00 00 2c")
    assert protocol.build_effect_speed(6) == bytes.fromhex("06 00 00 03")
    assert protocol.build_chip_order(2) == bytes.fromhex("02 00 00 3c")


def test_sptech_lan_commands_match_recovered_frame_shape() -> None:
    """SP541E LAN commands use the recovered SPTECH TCP envelope."""
    protocol = SPTechLANProtocol()

    assert protocol.build_state_query() == bytes.fromhex(
        "53 50 54 45 43 48 00 02 00 00 00 00 00"
    )
    assert protocol.build_power(True) == bytes.fromhex(
        "53 50 54 45 43 48 00 50 00 00 00 00 01 01"
    )
    assert protocol.build_power(False) == bytes.fromhex(
        "53 50 54 45 43 48 00 50 00 00 00 00 01 00"
    )
    assert protocol.build_brightness(64) == bytes.fromhex(
        "53 50 54 45 43 48 00 51 00 00 00 00 02 01 40"
    )
    assert protocol.build_white_level(65) == bytes.fromhex(
        "53 50 54 45 43 48 00 51 00 00 00 00 02 01 41"
    )
    assert protocol.build_light_mode(0x02, 0x01) == bytes.fromhex(
        "53 50 54 45 43 48 00 53 00 00 00 00 02 02 01"
    )
    assert protocol.build_effect_speed(6) == bytes.fromhex(
        "53 50 54 45 43 48 00 54 00 00 00 00 01 06"
    )


def test_command_validation_rejects_unsafe_values() -> None:
    """Command builders reject values outside safe protocol ranges."""
    protocol = BanlanX6xxProtocol()

    try:
        protocol.build_brightness(256)
    except ProtocolCommandError:
        pass
    else:
        raise AssertionError("brightness above one byte should fail")

    try:
        protocol.build_effect_speed(0)
    except ProtocolCommandError:
        pass
    else:
        raise AssertionError("effect speed below valid range should fail")

    try:
        BanlanX601Protocol().build_effect_length(151)
    except ProtocolCommandError:
        pass
    else:
        raise AssertionError("SP601E effect length above legacy limit should fail")

    try:
        BanlanX60xProtocol().build_power(True, channel=9)
    except ProtocolCommandError:
        pass
    else:
        raise AssertionError("channel outside protocol range should fail")

    try:
        BanlanX601Protocol().build_scene(9)
    except ProtocolCommandError:
        pass
    else:
        raise AssertionError("scene outside legacy recall range should fail")
