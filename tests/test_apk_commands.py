"""Tests for APK-recovered BanlanX app command enum evidence."""

from __future__ import annotations

from custom_components.uniled.core.apk_commands import (
    BANLANX_APP_COMMAND_ID_HINTS,
    apk_command_id_hint_for_name,
    apk_command_id_hints_for_names,
    missing_apk_command_id_hint_names,
)
from custom_components.uniled.core.car_lights import (
    CAR_LIGHT_APP_COMMAND_ID_HINTS,
    CAR_LIGHT_APP_COMMAND_ID_NAMES,
)
from custom_components.uniled.core.fish_tank import (
    FISH_TANK_APP_COMMAND_ID_HINTS,
    FISH_TANK_APP_COMMAND_ID_NAMES,
    FISH_TANK_APP_METHOD_HINTS,
)
from custom_components.uniled.core.network import (
    SP801E_APP_COMMAND_ID_HINTS,
    SP801E_APP_METHOD_HINTS,
    SP802E_APP_COMMAND_ID_HINTS,
    SP802E_APP_METHOD_HINTS,
)
from custom_components.uniled.core.scene import (
    SCENE_APP_COMMAND_ID_HINTS,
    SCENE_APP_COMMAND_ID_NAMES,
    SCENE_APP_METHOD_HINTS,
)
from custom_components.uniled.core.sp630e import (
    SP630E_APP_COMMAND_ID_HINTS,
    SP630E_APP_METHOD_HINTS,
)
from custom_components.uniled.core.transports.mesh import (
    MESH_APP_COMMAND_ID_HINTS,
    MESH_APP_COMMAND_ID_NAMES,
)


def test_banlanx_app_command_id_hints_capture_blutter_enum_anchors() -> None:
    """High-value Blutter HJ enum IDs are checked in as app-layer evidence."""
    assert len(BANLANX_APP_COMMAND_ID_HINTS) == 82
    assert len({hint.name for hint in BANLANX_APP_COMMAND_ID_HINTS}) == 82

    expected = {
        "getNetworkInfo": (90, 0x92),
        "getArtNetConfig": (23, 0x21),
        "setArtNetConfig": (24, 0x22),
        "setLfxMode": (41, 0x53),
        "setLedPanelLayout": (77, 0x7E),
        "setMatrixMusicColGradientColor": (87, 0x88),
    }
    for name, (ordinal, command_id) in expected.items():
        hint = apk_command_id_hint_for_name(name)
        assert hint is not None
        assert hint.ordinal == ordinal
        assert hint.command_id == command_id
        assert hint.command_id_hex == f"0x{command_id:02x}"
        assert hint.source == "blutter_hj_enum"


def test_app_command_id_hints_for_names_preserve_requested_order() -> None:
    """Profile-specific views keep method order and ignore unknown names."""
    hints = apk_command_id_hints_for_names(
        ("missingMethod", "setBrightness", "setLfxSpeed", "setBrightness")
    )

    assert [hint.name for hint in hints] == ["setBrightness", "setLfxSpeed"]
    assert [hint.command_id for hint in hints] == [0x51, 0x54]
    assert missing_apk_command_id_hint_names(
        ("setBrightness", "missingMethod")
    ) == ("missingMethod",)


def test_profiles_only_use_recovered_app_command_id_names() -> None:
    """All profile method hints used for app IDs are backed by Blutter rows."""
    assert missing_apk_command_id_hint_names(FISH_TANK_APP_METHOD_HINTS) == ()
    assert missing_apk_command_id_hint_names(SP630E_APP_METHOD_HINTS) == ()
    assert missing_apk_command_id_hint_names(SP801E_APP_METHOD_HINTS) == ()
    assert missing_apk_command_id_hint_names(SP802E_APP_METHOD_HINTS) == ()
    assert missing_apk_command_id_hint_names(CAR_LIGHT_APP_COMMAND_ID_NAMES) == ()
    assert missing_apk_command_id_hint_names(FISH_TANK_APP_COMMAND_ID_NAMES) == ()
    assert missing_apk_command_id_hint_names(MESH_APP_COMMAND_ID_NAMES) == ()
    assert missing_apk_command_id_hint_names(SCENE_APP_COMMAND_ID_NAMES) == ()

    assert missing_apk_command_id_hint_names(SCENE_APP_METHOD_HINTS) == (
        "getFrameInfoHandler",
        "getFrameLenHandler",
        "getPWMFrameInfoHandler",
    )

    assert [hint.name for hint in FISH_TANK_APP_COMMAND_ID_HINTS] == list(
        FISH_TANK_APP_COMMAND_ID_NAMES
    )
    assert len(FISH_TANK_APP_COMMAND_ID_HINTS) == 14
    assert [hint.name for hint in FISH_TANK_APP_COMMAND_ID_HINTS[-3:]] == [
        "favoriteLfx",
        "saveTimingTask",
        "removeTimingTask",
    ]
    assert [hint.name for hint in SCENE_APP_COMMAND_ID_HINTS] == list(
        SCENE_APP_COMMAND_ID_NAMES
    )
    assert len(SCENE_APP_COMMAND_ID_HINTS) == 25
    assert [hint.name for hint in CAR_LIGHT_APP_COMMAND_ID_HINTS] == list(
        CAR_LIGHT_APP_COMMAND_ID_NAMES
    )
    assert [hint.command_id for hint in CAR_LIGHT_APP_COMMAND_ID_HINTS] == [
        0x24,
        0x36,
        0x91,
    ]
    assert [hint.name for hint in MESH_APP_COMMAND_ID_HINTS] == list(
        MESH_APP_COMMAND_ID_NAMES
    )
    assert [hint.command_id for hint in MESH_APP_COMMAND_ID_HINTS] == [
        0x02,
        0x23,
        0x24,
        0x26,
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC4,
        0xC5,
        0xC7,
        0xC8,
    ]
    assert [hint.name for hint in SP630E_APP_COMMAND_ID_HINTS] == list(
        SP630E_APP_METHOD_HINTS
    )
    assert len(SP630E_APP_COMMAND_ID_HINTS) == 35
    assert [hint.command_id for hint in SP630E_APP_COMMAND_ID_HINTS[:4]] == [
        0x50,
        0x51,
        0x52,
        0x61,
    ]
    assert [hint.command_id for hint in SP630E_APP_COMMAND_ID_HINTS[-5:]] == [
        0x81,
        0x82,
        0x84,
        0x92,
        0x09,
    ]
    assert [hint.name for hint in SP801E_APP_COMMAND_ID_HINTS] == list(
        SP801E_APP_METHOD_HINTS
    )
    assert [hint.name for hint in SP802E_APP_COMMAND_ID_HINTS] == list(
        SP802E_APP_METHOD_HINTS
    )
    assert [hint.command_id for hint in SP802E_APP_COMMAND_ID_HINTS[:2]] == [
        0x92,
        0x7E,
    ]
