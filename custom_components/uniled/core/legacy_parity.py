"""Old UniLED parity profile metadata for ported BanlanX families."""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import CatalogModel, ProtocolFamily

BANLANX_601_COMMAND_BUILDERS = (
    "state_query",
    "power",
    "brightness",
    "rgb_color",
    "effect",
    "effect_speed",
    "effect_length",
    "effect_direction",
    "audio_input",
    "sensitivity",
    "scene",
    "scene_loop",
    "chip_order",
)

BANLANX_V2_COMMAND_BUILDERS = (
    "state_query",
    "light_mode",
    "power",
    "white_level",
    "brightness",
    "rgb_color",
    "rgbw_color",
    "effect",
    "effect_speed",
    "effect_length",
    "effect_loop",
    "audio_input",
    "sensitivity",
    "chip_order",
)

BANLANX_V3_COMMAND_BUILDERS = (
    "state_query",
    "light_mode",
    "power",
    "white_level",
    "brightness",
    "rgb_color",
    "effect",
    "effect_speed",
    "effect_loop",
    "audio_input",
    "sensitivity",
    "chip_order",
)

BANLANX_6XX_COMMAND_BUILDERS = (
    "state_query",
    "power",
    "brightness",
    "rgb_color",
    "dynamic_rgb_color",
    "rgbw_color",
    "rgbww_color",
    "white_level",
    "cct_color",
    "light_mode",
    "effect_speed",
    "effect_length",
    "effect_direction",
    "effect_loop",
    "audio_input",
    "sensitivity",
    "onoff_config",
    "coexistence",
    "on_power",
    "effect_play",
    "light_type",
    "chip_order",
)

LED_CHORD_COMMAND_BUILDERS = (
    "state_query",
    "power",
    "light_mode",
    "brightness",
    "white_level",
    "rgb_color",
    "rgb2_color",
    "rgbw_color",
    "effect",
    "effect_speed",
    "sensitivity",
    "chip_type",
    "chip_order",
    "segment_count",
    "segment_pixels",
)

LED_HUE_COMMAND_BUILDERS = (
    "state_query",
    "power",
    "brightness",
    "white_level",
    "rgb_color",
    "rgbw_color",
    "effect",
    "effect_loop",
    "effect_speed",
    "chip_type",
    "chip_order",
    "segment_pixels",
)

SEGMENTED_601_PARSER_HINTS = (
    "0x53/0x43 segmented notification framing",
    "per-output channel state",
    "tail scene-loop and sensitivity fields",
    "legacy scene recall slots 0-8",
)

SEGMENTED_60X_PARSER_HINTS = (
    "0x36/0x38 segmented notification framing",
    "per-output channel state",
    "tail scene-loop and sensitivity fields",
    "legacy scene recall slots 0-8",
)

BANLANX_V2_PARSER_HINTS = (
    "0xA0 status frame",
    "timer-count byte",
    "RGB-plus-white status fields",
    "BanlanX2 light-mode state",
)

BANLANX_V3_PARSER_HINTS = (
    "BanlanX3 indexed notification framing",
    "RGB-plus-white status fields",
    "DIY effect metadata",
    "BanlanX3 light-mode state",
)

BANLANX_6XX_PARSER_HINTS = (
    "0x53 unencrypted status packet",
    "light-type byte",
    "static and dynamic RGB/CCT fields",
    "on/off animation fields",
    "power-restore and coexistence fields",
    "DIY/custom slot metadata",
)

LED_CHORD_PARSER_HINTS = (
    "two 15-byte notification packets assembled into one 26-byte status",
    "effect ranges for static, dynamic, strip music, and matrix music modes",
    "RGBW detection from old chip-type table",
    "segment count and pixel diagnostics",
)

LED_HUE_PARSER_HINTS = (
    "12-byte status packet with optional leading byte",
    "effect zero as auto-loop mode",
    "RGBW detection from old chip-type table",
    "segment pixel diagnostics",
)

SCENE_SAVE_STUB_GAP = (
    "scene_save existed as an empty old-UniLED stub and is intentionally not "
    "ported as a command",
)
@dataclass(frozen=True, slots=True)
class LegacyUniLEDParityProfile:
    """Evidence summary for an old-UniLED-backed protocol family."""

    family: ProtocolFamily
    source_module: str
    command_builders: tuple[str, ...]
    status_parser_hints: tuple[str, ...]
    stubbed_builders: tuple[str, ...] = ()
    gap_hints: tuple[str, ...] = ()


def legacy_uniled_parity_profile_for_model(
    model: CatalogModel,
) -> LegacyUniLEDParityProfile | None:
    """Return old-UniLED parity evidence for a catalog model, if applicable."""
    if not model.legacy_uniled_supported and model.family not in {
        ProtocolFamily.LEGACY_LED_CHORD,
        ProtocolFamily.LEGACY_LED_HUE,
    }:
        return None

    if model.family is ProtocolFamily.BANLANX_601:
        return LegacyUniLEDParityProfile(
            family=model.family,
            source_module="custom_components/uniled/lib/ble/banlanx_601.py",
            command_builders=BANLANX_601_COMMAND_BUILDERS,
            status_parser_hints=SEGMENTED_601_PARSER_HINTS,
            stubbed_builders=("scene_save",),
            gap_hints=SCENE_SAVE_STUB_GAP,
        )
    if model.family is ProtocolFamily.BANLANX_60X:
        return LegacyUniLEDParityProfile(
            family=model.family,
            source_module="custom_components/uniled/lib/ble/banlanx_60x.py",
            command_builders=BANLANX_601_COMMAND_BUILDERS,
            status_parser_hints=SEGMENTED_60X_PARSER_HINTS,
            stubbed_builders=("scene_save",),
            gap_hints=SCENE_SAVE_STUB_GAP,
        )
    if model.family is ProtocolFamily.BANLANX_V2:
        return LegacyUniLEDParityProfile(
            family=model.family,
            source_module="custom_components/uniled/lib/ble/banlanx2.py",
            command_builders=BANLANX_V2_COMMAND_BUILDERS,
            status_parser_hints=BANLANX_V2_PARSER_HINTS,
        )
    if model.family is ProtocolFamily.BANLANX_V3:
        return LegacyUniLEDParityProfile(
            family=model.family,
            source_module="custom_components/uniled/lib/ble/banlanx3.py",
            command_builders=BANLANX_V3_COMMAND_BUILDERS,
            status_parser_hints=BANLANX_V3_PARSER_HINTS,
        )
    if model.family is ProtocolFamily.BANLANX_6XX:
        return LegacyUniLEDParityProfile(
            family=model.family,
            source_module="custom_components/uniled/lib/ble/banlanx_6xx.py",
            command_builders=BANLANX_6XX_COMMAND_BUILDERS,
            status_parser_hints=BANLANX_6XX_PARSER_HINTS,
        )
    if model.family is ProtocolFamily.LEGACY_LED_CHORD:
        return LegacyUniLEDParityProfile(
            family=model.family,
            source_module="custom_components/uniled/lib/ble/led_chord.py",
            command_builders=LED_CHORD_COMMAND_BUILDERS,
            status_parser_hints=LED_CHORD_PARSER_HINTS,
        )
    if model.family is ProtocolFamily.LEGACY_LED_HUE:
        return LegacyUniLEDParityProfile(
            family=model.family,
            source_module="custom_components/uniled/lib/ble/led_hue.py",
            command_builders=LED_HUE_COMMAND_BUILDERS,
            status_parser_hints=LED_HUE_PARSER_HINTS,
        )
    return None


def describe_legacy_uniled_parity_profile(
    profile: LegacyUniLEDParityProfile | None,
) -> str | None:
    """Return a compact old-UniLED parity diagnostic string."""
    if profile is None:
        return None
    return (
        f"{profile.family.value}; old_uniled={profile.source_module}; "
        f"commands={len(profile.command_builders)}; "
        f"parsers={len(profile.status_parser_hints)}; "
        f"stubbed={len(profile.stubbed_builders)}; "
        f"gaps={len(profile.gap_hints)}"
    )
