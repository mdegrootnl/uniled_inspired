"""Protocol-family option maps for command selects."""

from __future__ import annotations

import itertools
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .catalog import CatalogModel, ProtocolFamily

_BANLANX6XX_STYLE_FAMILIES = frozenset(
    {
        ProtocolFamily.BANLANX_6XX,
        ProtocolFamily.BANLANX_CUSTOM_5XX,
    }
)


@dataclass(frozen=True, slots=True)
class SelectOptionMap:
    """Bidirectional string/int option map for one select feature."""

    key: str
    values: Mapping[int, str]

    @property
    def options(self) -> tuple[str, ...]:
        """Return options in declared user-facing order."""
        return tuple(self.values.values())

    def option_for_value(self, value: int | str | None) -> str | None:
        """Return the option label for a raw state value."""
        if value is None:
            return None
        if isinstance(value, str):
            return value if value in self.options else None
        return self.values.get(int(value))

    def value_for_option(self, option: str) -> int:
        """Return the raw protocol value for an option label."""
        for value, label in self.values.items():
            if label == option:
                return value
        raise ValueError(f"{option!r} is not a valid {self.key} option")


@dataclass(frozen=True, slots=True)
class BanlanX6xxEffectAttributes:
    """Old-UniLED effect flags for an SP6xx mode/effect pair."""

    speedable: bool = False
    sizeable: bool = False
    directional: bool = False
    pausable: bool = False


def banlanx6xx_style_family(family: ProtocolFamily) -> bool:
    """Return whether a family uses the SP6xx command/status model."""
    return family in _BANLANX6XX_STYLE_FAMILIES


_AUDIO_INPUTS_AUX = MappingProxyType(
    {
        0x00: "Int. Mic",
        0x01: "Player",
        0x02: "Aux In",
    }
)
_AUDIO_INPUTS_EXT_MIC = MappingProxyType(
    {
        0x00: "Int. Mic",
        0x01: "Player",
        0x02: "Ext. Mic",
    }
)
_LIGHT_MODES_CYCLE = MappingProxyType(
    {
        0x00: "Single FX",
        0x01: "Cycle Dynamic FX's",
        0x02: "Cycle Sound FX's",
    }
)
_LED_CHORD_LIGHT_MODES = MappingProxyType(
    {
        0x00: "Single FX",
        0x01: "Cycle Dynamic FX's",
        0x02: "Cycle Strip FX's",
        0x03: "Cycle Matrix FX's",
    }
)
_LEGACY_LED_CHIP_TYPES = MappingProxyType(
    {
        0x00: "SM16703",
        0x01: "TM1804",
        0x02: "UCS1903",
        0x03: "WS2811",
        0x04: "WS2801",
        0x05: "SK6812",
        0x06: "LPD6803",
        0x07: "LPD8806",
        0x08: "APA102",
        0x09: "APA105",
        0x0A: "DMX512",
        0x0B: "TM1914",
        0x0C: "TM1913",
        0x0D: "P9813",
        0x0E: "INK1003",
        0x0F: "P943S",
        0x10: "P9411",
        0x11: "P9413",
        0x12: "TX1812",
        0x13: "TX1813",
        0x14: "GS8206",
        0x15: "GS8208",
        0x16: "SK9822",
        0x17: "TM1814",
        0x18: "SK6812_RGBW",
        0x19: "P9414",
        0x1A: "P9412",
    }
)
_BANLANX_601_EFFECTS = MappingProxyType(
    {
        0x19: "Solid",
        0x01: "Rainbow",
        0x02: "Rainbow Stars",
        0x03: "Twinkle Stars",
        0x04: "Fire",
        0x05: "Stacking",
        0x06: "Comet",
        0x07: "Wave",
        0x08: "Chasing",
        0x09: "Red/Blue/White",
        0x0A: "Green/Yellow/White",
        0x0B: "Red/Green/White",
        0x0C: "Red/Yellow",
        0x0D: "Red/White",
        0x0E: "Green/White",
        0x0F: "Gradient",
        0x10: "Wiping",
        0x11: "Breath",
        0x12: "Full Color Comet Wiping",
        0x13: "Comet Wiping",
        0x14: "Pixel Dot Wiping",
        0x15: "Full Color Meteor Rain",
        0x16: "Meteor Rain",
        0x17: "Color Dots",
        0x18: "Color Block",
        0x65: "Sound - Full Color Rhythm Spectrum",
        0x66: "Sound - Single Color Rhythm Spectrum",
        0x67: "Sound - Full Color Rhythm Stars",
        0x68: "Sound - Single Color Rhythm Stars",
        0x69: "Sound - Full Color Beat Injection",
        0x6A: "Sound - Beat Injection",
        0x6B: "Sound - Gradient Energy",
        0x6C: "Sound - Single Color Energy",
        0x6D: "Sound - Gradient Pulse",
        0x6E: "Sound - Single Color Pulse",
        0x6F: "Sound - Full Color Ripple",
        0x70: "Sound - Ripple",
        0x71: "Sound - Love & Peace",
        0x72: "Sound - Christmas",
        0x73: "Sound - Heartbeat",
        0x74: "Sound - Party",
    }
)
_LED_CHORD_EFFECTS = MappingProxyType(
    {
        0xB5: "Solid",
        **{0x01 + index: f"Dynamic FX {index + 1}" for index in range(180)},
        **{0xBE + index: f"Sound - Strip FX {index + 1}" for index in range(18)},
        **{0xDC + index: f"Sound - Matrix FX {index + 1}" for index in range(30)},
    }
)
_LED_HUE_EFFECTS = MappingProxyType(
    {
        0x79: "Solid",
        **{0x01 + index: f"Pattern {index + 1}" for index in range(0x78)},
    }
)
_BANLANX2_EFFECTS_RGB = MappingProxyType(
    {
        0xBE: "Solid Color",
        0x01: "Rainbow",
        0x02: "Rainbow Metor",
        0x03: "Rainbow Stars",
        0x04: "Rainbow Spin",
        0x05: "Red/Yellow Fire",
        0x06: "Red/Purple Fire",
        0x07: "Green/Yellow Fire",
        0x08: "Green/Cyan Fire",
        0x09: "Blue/Purple Fire",
        0x0A: "Blue/Cyan Fire",
        0x0B: "Red Comet",
        0x0C: "Green Comet",
        0x0D: "Blue Comet",
        0x0E: "Yellow Comet",
        0x0F: "Cyan Comet",
        0x10: "Purple Comet",
        0x11: "White Comet",
        0x12: "Red Meteor",
        0x13: "Green Meteor",
        0x14: "Blue Meteor",
        0x15: "Yellow Meteor",
        0x16: "Cyan Meteor",
        0x17: "Purple Meteor",
        0x18: "White Meteor",
        0x19: "Red/Green Gradual Snake",
        0x1A: "Red/Blue Gradual Snake",
        0x1B: "Red/Yellow Gradual Snake",
        0x1C: "Red/Cyan Gradual Snake",
        0x1D: "Red/Purple Gradual Snake",
        0x1E: "Red/White Gradual Snake",
        0x1F: "Green/Blue Gradual Snake",
        0x20: "Green/Yellow Gradual Snake",
        0x21: "Green/Cyan Gradual Snake",
        0x22: "Green/Purple Gradual Snake",
        0x23: "Green/White Gradual Snake",
        0x24: "Blue/Yellow Gradual Snake",
        0x25: "Blue/Cyan Gradual Snake",
        0x26: "Blue/Purple Gradual Snake",
        0x27: "Blue/White Gradual Snake",
        0x28: "Yellow/Cyan Gradual Snake",
        0x29: "Yellow/Purple Gradual Snake",
        0x2A: "Yellow/White Gradual Snake",
        0x2B: "Cyan/Purple Gradual Snake",
        0x2C: "Cyan/White Gradual Snake",
        0x2D: "Purple/White Gradual Snake",
        0x2E: "Red Wave",
        0x2F: "Green Wave",
        0x30: "Blue Wave",
        0x31: "Yellow Wave",
        0x32: "Cyan Wave",
        0x33: "Purple Wave",
        0x34: "White Wave",
        0x35: "Red/Green Wave",
        0x36: "Red/Blue Wave",
        0x37: "Red/Yellow Wave",
        0x38: "Red/Cyan Wave",
        0x39: "Red/Purple Wave",
        0x3A: "Red/White Wave",
        0x3B: "Green/Blue Wave",
        0x3C: "Green/Yellow Wave",
        0x3D: "Green/Cyan Wave",
        0x3E: "Green/Purple Wave",
        0x3F: "Green/White Wave",
        0x40: "Blue/Yellow Wave",
        0x41: "Blue/Cyan Wave",
        0x42: "Blue/Purple Wave",
        0x43: "Blue/White Wave",
        0x44: "Yellow/Cyan Wave",
        0x45: "Yellow/Purple Wave",
        0x46: "Yellow/White Wave",
        0x47: "Cyan/Purple Wave",
        0x48: "Cyan/White Wave",
        0x49: "Purple/White Wave",
        0x4A: "Red Stars",
        0x4B: "Green Stars",
        0x4C: "Blue Stars",
        0x4D: "Yellow Stars",
        0x4E: "Cyan Stars",
        0x4F: "Purple Stars",
        0x50: "White Stars",
        0x51: "Red Background Stars",
        0x52: "Green Background Stars",
        0x53: "Blue Background Stars",
        0x54: "Yellow Background Stars",
        0x55: "Cyan Background Stars",
        0x56: "Purple Background Stars",
        0x57: "Red/White Background Stars",
        0x58: "Green/White Background Stars",
        0x59: "Blue/White Background Stars",
        0x5A: "Yellow/White Background Stars",
        0x5B: "Cyan/White Background Stars",
        0x5C: "Purple/White Background Stars",
        0x5D: "White/White Background Stars",
        0x5E: "Red Breath",
        0x5F: "Green Breath",
        0x60: "Blue Breath",
        0x61: "Yellow Breath",
        0x62: "Cyan Breath",
        0x63: "Purple Breath",
        0x64: "White Breath",
        0x65: "Red Stacking",
        0x66: "Green Stacking",
        0x67: "Blue Stacking",
        0x68: "Yellow Stacking",
        0x69: "Cyan Stacking",
        0x6A: "Purple Stacking",
        0x6B: "White Stacking",
        0x6C: "Full Color Stack",
        0x6D: "Red to Green Stack",
        0x6E: "Green to Blue Stack",
        0x6F: "Blue to Yellow Stack",
        0x70: "Yellow to Cyan Stack",
        0x71: "Cyan to Purple Stack",
        0x72: "Purple to White Stack",
        0x73: "Red/Blue/White Snake",
        0x74: "Green/Yellow/White Snake",
        0x75: "Red/Green/White Snake",
        0x76: "Red/Yellow Snake",
        0x77: "Red/White Snake",
        0x78: "Green/White Snake",
        0x79: "Red Comet Spin",
        0x7A: "Green Comet Spin",
        0x7B: "Blue Comet Spin",
        0x7C: "Yellow Comet Spin",
        0x7D: "Cyan Comet Spin",
        0x7E: "Purple Comet Spin",
        0x7F: "White Comet Spin",
        0x80: "Red Dot Spin",
        0x81: "Green Dot Spin",
        0x82: "Blue Dot Spin",
        0x83: "Yellow Dot Spin",
        0x84: "Cyan Dot Spin",
        0x85: "Purple Dot Spin",
        0x86: "White Dot Spin",
        0x87: "Red Segment Spin",
        0x88: "Green Segment Spin",
        0x89: "Blue Segment Spin",
        0x8A: "Yellow Segment Spin",
        0x8B: "Cyan Segment Spin",
        0x8C: "Purple Segment Spin",
        0x8D: "White Segment Spin",
        0x8E: "Gradient",
    }
)
_BANLANX2_EFFECTS_SOUND = MappingProxyType(
    {
        0xC9: "Sound - Full Color Rhythm Spectrum",
        0xCA: "Sound - Single Color Rhythm Spectrum",
        0xCB: "Sound - Full Color Rhythm Stars",
        0xCC: "Sound - Single Color Rhythm Stars",
        0xCD: "Sound - Gradient Energy",
        0xCE: "Sound - Single Color Energy",
        0xCF: "Sound - Gradient Pulse",
        0xD0: "Sound - Single Color Pulse",
        0xD1: "Sound - Full Color Ejection Forward",
        0xD2: "Sound - Single Color Ejection Forward",
        0xD3: "Sound - Full Color Ejection Backward",
        0xD4: "Sound - Single Color Ejection Backward",
        0xD5: "Sound - Full Color VuMeter",
        0xD6: "Sound - Single Color VuMeter",
        0xD7: "Sound - Love & Peace",
        0xD8: "Sound - Christmas",
        0xD9: "Sound - Heartbeat",
        0xDA: "Sound - Party",
    }
)
_BANLANX2_EFFECTS_RGBW = MappingProxyType(
    {
        0xBF: "Solid White",
        **_BANLANX2_EFFECTS_RGB,
    }
)
_BANLANX2_EFFECTS_RGB_SOUND = MappingProxyType(
    {
        **_BANLANX2_EFFECTS_RGB,
        **_BANLANX2_EFFECTS_SOUND,
    }
)
_BANLANX2_EFFECTS_RGBW_SOUND = MappingProxyType(
    {
        **_BANLANX2_EFFECTS_RGBW,
        **_BANLANX2_EFFECTS_SOUND,
    }
)
_BANLANX3_EFFECTS_RGB = MappingProxyType(
    {
        0x63: "Solid Color",
        0x01: "Seven Color Gradient",
        0x02: "Seven Color Jump",
        0x03: "Seven Color Breath",
        0x04: "Seven Color Strobe",
        0x05: "Red Breath",
        0x06: "Green Breath",
        0x07: "Blue Breath",
        0x08: "Yellow Breath",
        0x09: "Cyan Breath",
        0x0A: "Purple Breath",
        0x0B: "White Breath",
        0x0C: "Red Strobe",
        0x0D: "Green Strobe",
        0x0E: "Blue Strobe",
        0x0F: "Yellow Strobe",
        0x10: "Cyan Strobe",
        0x11: "Purple Strobe",
        0x12: "White Strobe",
        0x20: "Adjustable Color Breath",
        0x21: "Adjustable Color Strobe",
        0x64: "Custom",
    }
)
_BANLANX3_EFFECTS_SOUND = MappingProxyType(
    {
        0x65: "Sound - Music Breath",
        0x66: "Sound - Music Jump",
        0x67: "Sound - Monochrome Music Breath",
    }
)
_BANLANX3_EFFECTS_RGBW = MappingProxyType(
    {
        0xCC: "Solid White",
        **_BANLANX3_EFFECTS_RGB,
    }
)
_BANLANX3_EFFECTS_RGB_SOUND = MappingProxyType(
    {
        **_BANLANX3_EFFECTS_RGB,
        **_BANLANX3_EFFECTS_SOUND,
    }
)
_BANLANX3_EFFECTS_RGBW_SOUND = MappingProxyType(
    {
        **_BANLANX3_EFFECTS_RGBW,
        **_BANLANX3_EFFECTS_SOUND,
    }
)
_BANLANX6XX_MODE_STATIC_COLOR = 0x01
_BANLANX6XX_MODE_STATIC_WHITE = 0x02
_BANLANX6XX_MODE_DYNAMIC_COLOR = 0x03
_BANLANX6XX_MODE_DYNAMIC_WHITE = 0x04
_BANLANX6XX_MODE_SOUND_COLOR = 0x05
_BANLANX6XX_MODE_SOUND_WHITE = 0x06
_BANLANX6XX_MODE_CUSTOM_COLOR = 0x07
_BANLANX6XX_MODE_CUSTOM_GRADIENT = 0x08
_BANLANX6XX_LIGHT_MODES = MappingProxyType(
    {
        _BANLANX6XX_MODE_STATIC_COLOR: "Static Color",
        _BANLANX6XX_MODE_STATIC_WHITE: "Static White",
        _BANLANX6XX_MODE_DYNAMIC_COLOR: "Dynamic Color",
        _BANLANX6XX_MODE_DYNAMIC_WHITE: "Dynamic White",
        _BANLANX6XX_MODE_SOUND_COLOR: "Sound - Color",
        _BANLANX6XX_MODE_SOUND_WHITE: "Sound - White",
        _BANLANX6XX_MODE_CUSTOM_COLOR: "Custom Solid",
        _BANLANX6XX_MODE_CUSTOM_GRADIENT: "Custom Gradient",
    }
)
_BANLANX6XX_ONOFF_EFFECTS = MappingProxyType(
    {
        0x01: "Flow Forward",
        0x02: "Flow Backward",
        0x03: "Gradient",
        0x04: "Stars",
    }
)
_BANLANX6XX_ONOFF_SPEEDS = MappingProxyType(
    {
        0x01: "Slow",
        0x02: "Medium",
        0x03: "Fast",
    }
)
_BANLANX6XX_ON_POWER_STATES = MappingProxyType(
    {
        0x00: "Light Off",
        0x01: "Light On",
        0x02: "Last state",
    }
)
_BANLANX6XX_CHIP_ORDER_CW = "CW"
_BANLANX6XX_CHIP_ORDER_123 = "123"
_BANLANX6XX_CHIP_ORDER_CWX = "CWX"
_BANLANX6XX_CHIP_ORDER_RGB = "RGB"
_BANLANX6XX_CHIP_ORDER_RGBW = "RGBW"
_BANLANX6XX_CHIP_ORDER_RGBCW = "RGBCW"
_LEGACY_RGBW_CHIP_ORDER_MODELS = frozenset({"SP617E", "SP614E", "SP624E"})
_LEGACY_V23_AUDIO_CONTROL_BIT = 0x02
_LEGACY_V23_NO_AUDIO_MODELS = frozenset(
    {
        "SP603E",
        "SP621E",
        "SP623E",
        "SP624E",
    }
)
_BANLANX6XX_EFFECTS_STATIC_COLOR = MappingProxyType({0x01: "Solid"})
_BANLANX6XX_EFFECTS_STATIC_WHITE = MappingProxyType({0x01: "Solid"})
_BANLANX6XX_PWM_EFFECTS_DYNAMIC_WHITE = MappingProxyType(
    {
        0x01: "White Color Breath",
        0x02: "White Color Strobe",
        0x03: "White Color Heart Beat",
    }
)
_BANLANX6XX_PWM_EFFECTS_SOUND_WHITE = MappingProxyType(
    {0x01: "Sound - White Color Music Breath"}
)
_BANLANX6XX_PWM_EFFECTS_DYNAMIC_COLOR = MappingProxyType(
    {
        0x01: "Seven Color Jump",
        0x02: "Seven Color Breath",
        0x03: "Seven Color Strobe",
        0x04: "Seven Color Heart Beat",
        0x05: "Seven Color Gradient",
        0x06: "Red Breath",
        0x07: "Green Breath",
        0x08: "Blue Breath",
        0x09: "Yellow Breath",
        0x0A: "Cyan Breath",
        0x0B: "Purple Breath",
        0x0C: "White Breath",
    }
)
_BANLANX6XX_PWM_EFFECTS_SOUND_COLOR = MappingProxyType(
    {
        index: label
        for index, label in enumerate(_BANLANX3_EFFECTS_SOUND.values())
    }
)
_BANLANX6XX_SPI_EFFECTS_DYNAMIC_WHITE = MappingProxyType(
    {
        0x01: "White Color Breath",
        0x02: "White Color Stars",
        0x03: "White Color Meteor",
        0x04: "White Color Comet Spin",
        0x05: "White Color Dot Spin",
        0x06: "White Color Segment Spin",
        0x07: "White Color Chasing Dots",
        0x08: "White Color Comet",
        0x09: "White Color Wave",
        0x0A: "White Color Stacking",
    }
)
_BANLANX6XX_SPI_EFFECTS_DYNAMIC_COLOR = MappingProxyType(
    {
        0x01: "Rainbow",
        0x02: "Rainbow Metor",
        0x03: "Rainbow Comet",
        0x04: "Rainbow Segment",
        0x05: "Rainbow Wave",
        0x06: "Rainbow Jump",
        0x07: "Rainbow Stars",
        0x08: "Rainbow Spin",
        **{
            value + 4: label
            for value, label in _BANLANX2_EFFECTS_RGB.items()
            if 0x05 <= value <= 0x8E
        },
    }
)
_BANLANX6XX_SPI_EFFECTS_SOUND_WHITE = MappingProxyType(
    {
        0x01: "Sound - White Color Music Blink",
        0x02: "Sound - White Color Music Force",
        0x03: "Sound - White Color Music Hits",
        0x04: "Sound - White Color Music Eject Forward",
        0x05: "Sound - White Color Music Eject Backward",
    }
)
_BANLANX6XX_SPI_EFFECTS_SOUND_COLOR = MappingProxyType(
    {
        index + 1: label
        for index, label in enumerate(_BANLANX2_EFFECTS_SOUND.values())
    }
)
_BANLANX6XX_PWM_EFFECTS_CUSTOM_COLOR = MappingProxyType(
    {
        0x01: "Jump",
        0x02: "Breath",
        0x03: "Strobe",
    }
)
_BANLANX6XX_SPI_EFFECTS_CUSTOM_COLOR = MappingProxyType(
    {
        0x01: "Static",
        0x02: "Chase Forward",
        0x03: "Chase Backward",
        0x04: "Chase Middle to Out",
        0x05: "Chase Out to Middle",
        0x06: "Twinkle",
        0x07: "Fade",
        0x08: "Comet Forward",
        0x09: "Comet Backward",
        0x0A: "Comet Middle to Out",
        0x0B: "Comet Out to Middle",
        0x0C: "Wave Forward",
        0x0D: "Wave Backward",
        0x0E: "Wave Middle to Out",
        0x0F: "Wave Out to Middle",
        0x10: "Strobe",
        0x11: "Solid Fade",
        0x12: "Full Strobe",
    }
)
_BANLANX6XX_SPI_EFFECTS_CUSTOM_COLOR_FIREWORK = MappingProxyType(
    {
        **_BANLANX6XX_SPI_EFFECTS_CUSTOM_COLOR,
        0x13: "Firework",
    }
)
_BANLANX6XX_SPI_EFFECTS_CUSTOM_GRADIENT = MappingProxyType(
    {
        0x01: "Static",
        0x02: "Chase Forward",
        0x03: "Chase Backward",
        0x04: "Spin",
        0x05: "Sine Chase Forward",
        0x06: "Sine Chase Backward",
        0x07: "Fire Forward",
        0x08: "Fire Backward",
        0x09: "Juggle",
        0x0A: "Meteor Forward",
        0x0B: "Meteor Backward",
    }
)
_BANLANX6XX_ATTR_NONE = BanlanX6xxEffectAttributes()
_BANLANX6XX_ATTR_SPEED = BanlanX6xxEffectAttributes(speedable=True)
_BANLANX6XX_ATTR_SIZE = BanlanX6xxEffectAttributes(sizeable=True)
_BANLANX6XX_ATTR_DIRECTION = BanlanX6xxEffectAttributes(directional=True)
_BANLANX6XX_ATTR_SIZE_DIRECTION = BanlanX6xxEffectAttributes(
    sizeable=True,
    directional=True,
)
_BANLANX6XX_ATTR_SPEED_SIZE = BanlanX6xxEffectAttributes(
    speedable=True,
    sizeable=True,
)
_BANLANX6XX_ATTR_SPEED_SIZE_DIRECTION = BanlanX6xxEffectAttributes(
    speedable=True,
    sizeable=True,
    directional=True,
)
_BANLANX6XX_ATTR_SPEED_SIZE_DIRECTION_PAUSE = BanlanX6xxEffectAttributes(
    speedable=True,
    sizeable=True,
    directional=True,
    pausable=True,
)
_BANLANX6XX_ATTR_SPEED_SIZE_PAUSE = BanlanX6xxEffectAttributes(
    speedable=True,
    sizeable=True,
    pausable=True,
)
_BANLANX6XX_CFG_PWM_WHITE = MappingProxyType(
    {
        _BANLANX6XX_MODE_STATIC_WHITE: _BANLANX6XX_EFFECTS_STATIC_WHITE,
        _BANLANX6XX_MODE_DYNAMIC_WHITE: _BANLANX6XX_PWM_EFFECTS_DYNAMIC_WHITE,
        _BANLANX6XX_MODE_SOUND_WHITE: _BANLANX6XX_PWM_EFFECTS_SOUND_WHITE,
    }
)
_BANLANX6XX_CFG_PWM_COLOR = MappingProxyType(
    {
        _BANLANX6XX_MODE_STATIC_COLOR: _BANLANX6XX_EFFECTS_STATIC_COLOR,
        _BANLANX6XX_MODE_DYNAMIC_COLOR: _BANLANX6XX_PWM_EFFECTS_DYNAMIC_COLOR,
        _BANLANX6XX_MODE_SOUND_COLOR: _BANLANX6XX_PWM_EFFECTS_SOUND_COLOR,
        _BANLANX6XX_MODE_CUSTOM_COLOR: _BANLANX6XX_PWM_EFFECTS_CUSTOM_COLOR,
    }
)
_BANLANX6XX_CFG_PWM_COLOR_WHITE = MappingProxyType(
    {
        **_BANLANX6XX_CFG_PWM_COLOR,
        _BANLANX6XX_MODE_STATIC_WHITE: _BANLANX6XX_EFFECTS_STATIC_WHITE,
        _BANLANX6XX_MODE_DYNAMIC_WHITE: _BANLANX6XX_PWM_EFFECTS_DYNAMIC_WHITE,
        _BANLANX6XX_MODE_SOUND_WHITE: _BANLANX6XX_PWM_EFFECTS_SOUND_WHITE,
    }
)
_BANLANX6XX_CFG_SPI_WHITE = MappingProxyType(
    {
        _BANLANX6XX_MODE_STATIC_WHITE: _BANLANX6XX_EFFECTS_STATIC_WHITE,
        _BANLANX6XX_MODE_DYNAMIC_WHITE: _BANLANX6XX_SPI_EFFECTS_DYNAMIC_WHITE,
        _BANLANX6XX_MODE_SOUND_WHITE: _BANLANX6XX_SPI_EFFECTS_SOUND_WHITE,
    }
)
_BANLANX6XX_CFG_SPI_COLOR = MappingProxyType(
    {
        _BANLANX6XX_MODE_STATIC_COLOR: _BANLANX6XX_EFFECTS_STATIC_COLOR,
        _BANLANX6XX_MODE_DYNAMIC_COLOR: _BANLANX6XX_SPI_EFFECTS_DYNAMIC_COLOR,
        _BANLANX6XX_MODE_SOUND_COLOR: _BANLANX6XX_SPI_EFFECTS_SOUND_COLOR,
        _BANLANX6XX_MODE_CUSTOM_COLOR: _BANLANX6XX_SPI_EFFECTS_CUSTOM_COLOR,
    }
)
_BANLANX6XX_CFG_SPI_COLOR_GRADIENT = MappingProxyType(
    {
        **_BANLANX6XX_CFG_SPI_COLOR,
        _BANLANX6XX_MODE_CUSTOM_GRADIENT: _BANLANX6XX_SPI_EFFECTS_CUSTOM_GRADIENT,
    }
)
_BANLANX6XX_CFG_SPI_COLOR_SPTECH_NET = MappingProxyType(
    {
        **_BANLANX6XX_CFG_SPI_COLOR_GRADIENT,
        _BANLANX6XX_MODE_CUSTOM_COLOR: (
            _BANLANX6XX_SPI_EFFECTS_CUSTOM_COLOR_FIREWORK
        ),
    }
)
_BANLANX6XX_CFG_SPI_COLOR_WHITE = MappingProxyType(
    {
        **_BANLANX6XX_CFG_SPI_COLOR,
        _BANLANX6XX_MODE_STATIC_WHITE: _BANLANX6XX_EFFECTS_STATIC_WHITE,
        _BANLANX6XX_MODE_DYNAMIC_WHITE: _BANLANX6XX_SPI_EFFECTS_DYNAMIC_WHITE,
        _BANLANX6XX_MODE_SOUND_WHITE: _BANLANX6XX_SPI_EFFECTS_SOUND_WHITE,
    }
)
_BANLANX6XX_CFG_SPI_COLOR_WHITE_GRADIENT = MappingProxyType(
    {
        **_BANLANX6XX_CFG_SPI_COLOR_WHITE,
        _BANLANX6XX_MODE_CUSTOM_GRADIENT: _BANLANX6XX_SPI_EFFECTS_CUSTOM_GRADIENT,
    }
)
_BANLANX6XX_CFG_SPI_COLOR_WHITE_SPTECH_NET = MappingProxyType(
    {
        **_BANLANX6XX_CFG_SPI_COLOR_WHITE_GRADIENT,
        _BANLANX6XX_MODE_CUSTOM_COLOR: (
            _BANLANX6XX_SPI_EFFECTS_CUSTOM_COLOR_FIREWORK
        ),
    }
)
_BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE = MappingProxyType(
    {
        **_BANLANX6XX_CFG_SPI_COLOR,
        _BANLANX6XX_MODE_STATIC_WHITE: _BANLANX6XX_EFFECTS_STATIC_WHITE,
        _BANLANX6XX_MODE_DYNAMIC_WHITE: _BANLANX6XX_PWM_EFFECTS_DYNAMIC_WHITE,
        _BANLANX6XX_MODE_SOUND_WHITE: _BANLANX6XX_PWM_EFFECTS_SOUND_WHITE,
    }
)
_BANLANX6XX_MODEL_CONFIGS = {
    "SP538E": _BANLANX6XX_CFG_SPI_COLOR_SPTECH_NET,
    "SP548E": _BANLANX6XX_CFG_SPI_COLOR_SPTECH_NET,
    "SP539E": _BANLANX6XX_CFG_SPI_COLOR_WHITE_SPTECH_NET,
    "SP549E": _BANLANX6XX_CFG_SPI_COLOR_WHITE_SPTECH_NET,
    "SP631E": _BANLANX6XX_CFG_PWM_WHITE,
    "SP641E": _BANLANX6XX_CFG_PWM_WHITE,
    "SP651E": _BANLANX6XX_CFG_PWM_WHITE,
    "SP632E": _BANLANX6XX_CFG_PWM_WHITE,
    "SP642E": _BANLANX6XX_CFG_PWM_WHITE,
    "SP652E": _BANLANX6XX_CFG_PWM_WHITE,
    "SP633E": _BANLANX6XX_CFG_PWM_COLOR,
    "SP643E": _BANLANX6XX_CFG_PWM_COLOR,
    "SP653E": _BANLANX6XX_CFG_PWM_COLOR,
    "SP634E": _BANLANX6XX_CFG_PWM_COLOR_WHITE,
    "SP644E": _BANLANX6XX_CFG_PWM_COLOR_WHITE,
    "SP654E": _BANLANX6XX_CFG_PWM_COLOR_WHITE,
    "SP635E": _BANLANX6XX_CFG_PWM_COLOR_WHITE,
    "SP645E": _BANLANX6XX_CFG_PWM_COLOR_WHITE,
    "SP655E": _BANLANX6XX_CFG_PWM_COLOR_WHITE,
    "SP636E": _BANLANX6XX_CFG_SPI_WHITE,
    "SP646E": _BANLANX6XX_CFG_SPI_WHITE,
    "SP656E": _BANLANX6XX_CFG_SPI_WHITE,
    "SP637E": _BANLANX6XX_CFG_SPI_WHITE,
    "SP647E": _BANLANX6XX_CFG_SPI_WHITE,
    "SP657E": _BANLANX6XX_CFG_SPI_WHITE,
    "SP638E": _BANLANX6XX_CFG_SPI_COLOR,
    "SP648E": _BANLANX6XX_CFG_SPI_COLOR,
    "SP658E": _BANLANX6XX_CFG_SPI_COLOR,
    "SP639E": _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    "SP649E": _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    "SP659E": _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    "SP63AE": _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    "SP64AE": _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    "SP65AE": _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    "SP63BE": _BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE,
    "SP64BE": _BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE,
    "SP65BE": _BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE,
    "SP63CE": _BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE,
    "SP64CE": _BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE,
    "SP65CE": _BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE,
}
_BANLANX_CUSTOM_5XX_MODEL_NAMES = (
    "SP521E",
    "SP522E",
    "SP523E",
    "SP524E",
    "SP525E",
    "SP526E",
    "SP527E",
    "SP528E",
    "SP529E",
    "SP52AE",
    "SP52BE",
    "SP52CE",
    "SP530E",
    "SP531E",
    "SP532E",
    "SP533E",
    "SP534E",
    "SP535E",
    "SP536E",
    "SP537E",
    "SP538E",
    "SP539E",
    "SP53AE",
    "SP53BE",
    "SP53CE",
    "SP540E",
    "SP541E",
    "SP542E",
    "SP543E",
    "SP544E",
    "SP545E",
    "SP546E",
    "SP547E",
    "SP548E",
    "SP549E",
    "SP54AE",
    "SP54BE",
    "SP54CE",
)
_BANLANX_CUSTOM_5XX_MODEL_NAME_SET = frozenset(_BANLANX_CUSTOM_5XX_MODEL_NAMES)
_BANLANX_CUSTOM_5XX_SPTECH_NET_RGB_MODELS = frozenset({"SP538E", "SP548E"})
_BANLANX_CUSTOM_5XX_SPTECH_NET_RGBW_MODELS = frozenset({"SP539E", "SP549E"})
_BANLANX6XX_DYNAMIC_LIGHT_TYPE_MODELS = (
    frozenset({"360PhotoB", "SP630E"})
    | (
        _BANLANX_CUSTOM_5XX_MODEL_NAME_SET
        - _BANLANX_CUSTOM_5XX_SPTECH_NET_RGB_MODELS
        - _BANLANX_CUSTOM_5XX_SPTECH_NET_RGBW_MODELS
    )
)
_BANLANX6XX_COEXISTENCE_MODELS = frozenset(
    {
        "SP634E",
        "SP644E",
        "SP654E",
        "SP635E",
        "SP645E",
        "SP655E",
        "SP639E",
        "SP649E",
        "SP659E",
        "SP63AE",
        "SP64AE",
        "SP65AE",
        "SP63BE",
        "SP64BE",
        "SP65BE",
        "SP63CE",
        "SP64CE",
        "SP65CE",
    }
)
_BANLANX6XX_COEXISTENCE_LIGHT_TYPES = frozenset(
    {
        0x07,
        0x0A,
        0x08,
        0x0B,
        0x0E,
        0x09,
        0x0C,
    }
)
_BANLANX6XX_HUE_LIGHT_TYPES = frozenset(
    {
        0x05,
        0x07,
        0x0A,
        0x06,
        0x08,
        0x0B,
        0x0E,
        0x09,
        0x0C,
        0x85,
        0x87,
        0x8A,
        0x86,
        0x88,
        0x8B,
        0x8E,
        0x89,
        0x8C,
    }
)
_BANLANX6XX_CCT_LIGHT_TYPES = frozenset(
    {
        0x03,
        0x0A,
        0x04,
        0x0D,
        0x0B,
        0x0E,
        0x0C,
        0x83,
        0x8A,
        0x84,
        0x8D,
        0x8B,
        0x8E,
        0x8C,
    }
)
_BANLANX6XX_WHITE_LIGHT_TYPES = frozenset(
    {
        0x01,
        0x03,
        0x07,
        0x0A,
        0x02,
        0x04,
        0x0D,
        0x08,
        0x0B,
        0x0E,
        0x09,
        0x0C,
        0x81,
        0x83,
        0x87,
        0x8A,
        0x82,
        0x84,
        0x8D,
        0x88,
        0x8B,
        0x8E,
        0x89,
        0x8C,
    }
)
_BANLANX6XX_SP630E_LIGHT_TYPES = (
    0x81,
    0x83,
    0x85,
    0x87,
    0x8A,
    0x82,
    0x84,
    0x8D,
    0x86,
    0x88,
    0x8B,
    0x8E,
    0x89,
    0x8C,
)
_BANLANX6XX_MODEL_LIGHT_TYPES = {
    "360PhotoB": _BANLANX6XX_SP630E_LIGHT_TYPES,
    "SP630E": _BANLANX6XX_SP630E_LIGHT_TYPES,
    **{
        name: _BANLANX6XX_SP630E_LIGHT_TYPES
        for name in _BANLANX_CUSTOM_5XX_MODEL_NAMES
    },
    "SP538E": (0x06,),
    "SP548E": (0x06,),
    "SP539E": (0x08,),
    "SP549E": (0x08,),
    "SP631E": (0x01,),
    "SP641E": (0x01,),
    "SP651E": (0x01,),
    "SP632E": (0x03,),
    "SP642E": (0x03,),
    "SP652E": (0x03,),
    "SP633E": (0x05,),
    "SP643E": (0x05,),
    "SP653E": (0x05,),
    "SP634E": (0x07,),
    "SP644E": (0x07,),
    "SP654E": (0x07,),
    "SP635E": (0x0A,),
    "SP645E": (0x0A,),
    "SP655E": (0x0A,),
    "SP636E": (0x02,),
    "SP646E": (0x02,),
    "SP656E": (0x02,),
    "SP637E": (0x04, 0x0D),
    "SP647E": (0x04, 0x0D),
    "SP657E": (0x04, 0x0D),
    "SP638E": (0x06,),
    "SP648E": (0x06,),
    "SP658E": (0x06,),
    "SP639E": (0x08,),
    "SP649E": (0x08,),
    "SP659E": (0x08,),
    "SP63AE": (0x0B, 0x0E),
    "SP64AE": (0x0B, 0x0E),
    "SP65AE": (0x0B, 0x0E),
    "SP63BE": (0x09,),
    "SP64BE": (0x09,),
    "SP65BE": (0x09,),
    "SP63CE": (0x0C,),
    "SP64CE": (0x0C,),
    "SP65CE": (0x0C,),
}
_BANLANX6XX_LIGHT_TYPE_LABELS = MappingProxyType(
    {
        0x01: "1 CH PWM - Single Color",
        0x03: "2 CH PWM - CCT",
        0x05: "3 CH PWM - RGB",
        0x07: "4 CH PWM - RGBW",
        0x0A: "5 CH PWM - RGBCCT",
        0x02: "SPI - Single Color",
        0x04: "SPI - CCT1",
        0x0D: "SPI - CCT2",
        0x06: "SPI - RGB",
        0x08: "SPI - RGBW",
        0x0B: "SPI - RGBCCT (1)",
        0x0E: "SPI - RGBCCT (2)",
        0x09: "SPI - RGB + 1 CH PWM",
        0x0C: "SPI - RGB + 2 CH PWM",
        0x81: "1 CH PWM - Single Color",
        0x83: "2 CH PWM - CCT",
        0x85: "3 CH PWM - RGB",
        0x87: "4 CH PWM - RGBW",
        0x8A: "5 CH PWM - RGBCCT",
        0x82: "SPI - Single Color",
        0x84: "SPI - CCT1",
        0x8D: "SPI - CCT2",
        0x86: "SPI - RGB",
        0x88: "SPI - RGBW",
        0x8B: "SPI - RGBCCT (1)",
        0x8E: "SPI - RGBCCT (2)",
        0x89: "SPI - RGB + 1 CH PWM",
        0x8C: "SPI - RGB + 2 CH PWM",
    }
)
_BANLANX6XX_LIGHT_TYPE_ORDERS = {
    0x03: _BANLANX6XX_CHIP_ORDER_CW,
    0x05: _BANLANX6XX_CHIP_ORDER_RGB,
    0x07: _BANLANX6XX_CHIP_ORDER_RGBW,
    0x0A: _BANLANX6XX_CHIP_ORDER_RGBCW,
    0x02: _BANLANX6XX_CHIP_ORDER_123,
    0x04: _BANLANX6XX_CHIP_ORDER_CWX,
    0x0D: _BANLANX6XX_CHIP_ORDER_CWX,
    0x06: _BANLANX6XX_CHIP_ORDER_RGB,
    0x08: _BANLANX6XX_CHIP_ORDER_RGBW,
    0x0B: _BANLANX6XX_CHIP_ORDER_RGBCW,
    0x0E: _BANLANX6XX_CHIP_ORDER_RGBCW,
    0x09: _BANLANX6XX_CHIP_ORDER_RGB,
    0x0C: _BANLANX6XX_CHIP_ORDER_RGBCW,
    0x83: _BANLANX6XX_CHIP_ORDER_CW,
    0x85: _BANLANX6XX_CHIP_ORDER_RGB,
    0x87: _BANLANX6XX_CHIP_ORDER_RGBW,
    0x8A: _BANLANX6XX_CHIP_ORDER_RGBCW,
    0x82: _BANLANX6XX_CHIP_ORDER_123,
    0x84: _BANLANX6XX_CHIP_ORDER_CWX,
    0x8D: _BANLANX6XX_CHIP_ORDER_CWX,
    0x86: _BANLANX6XX_CHIP_ORDER_RGB,
    0x88: _BANLANX6XX_CHIP_ORDER_RGBW,
    0x8B: _BANLANX6XX_CHIP_ORDER_RGBCW,
    0x8E: _BANLANX6XX_CHIP_ORDER_RGBCW,
    0x89: _BANLANX6XX_CHIP_ORDER_RGB,
    0x8C: _BANLANX6XX_CHIP_ORDER_RGBCW,
}
_BANLANX6XX_LIGHT_TYPE_CONFIGS = {
    0x01: _BANLANX6XX_CFG_PWM_WHITE,
    0x03: _BANLANX6XX_CFG_PWM_WHITE,
    0x05: _BANLANX6XX_CFG_PWM_COLOR,
    0x07: _BANLANX6XX_CFG_PWM_COLOR_WHITE,
    0x0A: _BANLANX6XX_CFG_PWM_COLOR_WHITE,
    0x02: _BANLANX6XX_CFG_SPI_WHITE,
    0x04: _BANLANX6XX_CFG_SPI_WHITE,
    0x0D: _BANLANX6XX_CFG_SPI_WHITE,
    0x06: _BANLANX6XX_CFG_SPI_COLOR,
    0x08: _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    0x0B: _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    0x0E: _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    0x09: _BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE,
    0x0C: _BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE,
    0x81: _BANLANX6XX_CFG_PWM_WHITE,
    0x83: _BANLANX6XX_CFG_PWM_WHITE,
    0x85: _BANLANX6XX_CFG_PWM_COLOR,
    0x87: _BANLANX6XX_CFG_PWM_COLOR_WHITE,
    0x8A: _BANLANX6XX_CFG_PWM_COLOR_WHITE,
    0x82: _BANLANX6XX_CFG_SPI_WHITE,
    0x84: _BANLANX6XX_CFG_SPI_WHITE,
    0x8D: _BANLANX6XX_CFG_SPI_WHITE,
    0x86: _BANLANX6XX_CFG_SPI_COLOR_GRADIENT,
    0x88: _BANLANX6XX_CFG_SPI_COLOR_WHITE_GRADIENT,
    0x8B: _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    0x8E: _BANLANX6XX_CFG_SPI_COLOR_WHITE,
    0x89: _BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE,
    0x8C: _BANLANX6XX_CFG_SPI_COLOR_PWM_WHITE,
}


def _banlanx6xx_light_type_config(
    light_type: int | None,
    *,
    model_name: str | None = None,
) -> Mapping[int, Mapping[int, str]] | None:
    if light_type is None:
        return None
    raw = int(light_type)
    if model_name == "SP530E":
        if raw == 0x86:
            return _BANLANX6XX_CFG_SPI_COLOR_SPTECH_NET
        if raw == 0x88:
            return _BANLANX6XX_CFG_SPI_COLOR_WHITE_SPTECH_NET
    if model_name in _BANLANX_CUSTOM_5XX_SPTECH_NET_RGB_MODELS and raw == 0x06:
        return _BANLANX6XX_CFG_SPI_COLOR_SPTECH_NET
    if model_name in _BANLANX_CUSTOM_5XX_SPTECH_NET_RGBW_MODELS and raw == 0x08:
        return _BANLANX6XX_CFG_SPI_COLOR_WHITE_SPTECH_NET
    return _BANLANX6XX_LIGHT_TYPE_CONFIGS.get(raw)

_SELECT_OPTIONS = {
    (ProtocolFamily.BANLANX_601, "effect"): SelectOptionMap(
        "effect",
        _BANLANX_601_EFFECTS,
    ),
    (ProtocolFamily.BANLANX_601, "audio_input"): SelectOptionMap(
        "audio_input",
        _AUDIO_INPUTS_AUX,
    ),
    (ProtocolFamily.BANLANX_60X, "effect"): SelectOptionMap(
        "effect",
        _BANLANX_601_EFFECTS,
    ),
    (ProtocolFamily.BANLANX_60X, "audio_input"): SelectOptionMap(
        "audio_input",
        _AUDIO_INPUTS_AUX,
    ),
    (ProtocolFamily.BANLANX_V2, "effect"): SelectOptionMap(
        "effect",
        _BANLANX2_EFFECTS_RGBW_SOUND,
    ),
    (ProtocolFamily.BANLANX_V2, "audio_input"): SelectOptionMap(
        "audio_input",
        _AUDIO_INPUTS_EXT_MIC,
    ),
    (ProtocolFamily.BANLANX_V3, "effect"): SelectOptionMap(
        "effect",
        _BANLANX3_EFFECTS_RGBW_SOUND,
    ),
    (ProtocolFamily.BANLANX_V3, "audio_input"): SelectOptionMap(
        "audio_input",
        _AUDIO_INPUTS_EXT_MIC,
    ),
    (ProtocolFamily.BANLANX_6XX, "audio_input"): SelectOptionMap(
        "audio_input",
        _AUDIO_INPUTS_EXT_MIC,
    ),
    (ProtocolFamily.BANLANX_6XX, "onoff_effect"): SelectOptionMap(
        "onoff_effect",
        _BANLANX6XX_ONOFF_EFFECTS,
    ),
    (ProtocolFamily.BANLANX_6XX, "onoff_speed"): SelectOptionMap(
        "onoff_speed",
        _BANLANX6XX_ONOFF_SPEEDS,
    ),
    (ProtocolFamily.BANLANX_6XX, "on_power"): SelectOptionMap(
        "on_power",
        _BANLANX6XX_ON_POWER_STATES,
    ),
    (ProtocolFamily.BANLANX_V2, "light_mode"): SelectOptionMap(
        "light_mode",
        _LIGHT_MODES_CYCLE,
    ),
    (ProtocolFamily.BANLANX_V3, "light_mode"): SelectOptionMap(
        "light_mode",
        _LIGHT_MODES_CYCLE,
    ),
    (ProtocolFamily.LEGACY_LED_CHORD, "light_mode"): SelectOptionMap(
        "light_mode",
        _LED_CHORD_LIGHT_MODES,
    ),
}
_BANLANX2_EFFECT_PROFILES = {
    "SP617E": _BANLANX2_EFFECTS_RGBW_SOUND,
    "SP621E": _BANLANX2_EFFECTS_RGB,
}
_BANLANX3_EFFECT_PROFILES = {
    "SP614E": _BANLANX3_EFFECTS_RGBW_SOUND,
    "SP623E": _BANLANX3_EFFECTS_RGB,
    "SP624E": _BANLANX3_EFFECTS_RGBW,
}


def select_option_map(
    family: ProtocolFamily,
    key: str,
    *,
    color_cap: int | None = None,
    model_name: str | None = None,
    spec_functions: int | None = None,
) -> SelectOptionMap | None:
    """Return a command-select option map for a protocol family."""
    if key == "audio_input" and family in {
        ProtocolFamily.BANLANX_V2,
        ProtocolFamily.BANLANX_V3,
    }:
        if not legacy_v23_model_has_audio_controls(
            family,
            model_name=model_name,
            spec_functions=spec_functions,
        ):
            return None
    if key == "light_mode" and family in {
        ProtocolFamily.BANLANX_V2,
        ProtocolFamily.BANLANX_V3,
    }:
        if not legacy_v23_model_has_audio_controls(
            family,
            model_name=model_name,
            spec_functions=spec_functions,
        ):
            return None
    if banlanx6xx_style_family(family) and key == "light_type":
        values = banlanx6xx_light_type_values_for_model(model_name)
        if values is not None and len(values) > 1:
            return SelectOptionMap(key, values)
    if banlanx6xx_style_family(family) and key == "light_mode":
        values = banlanx6xx_light_mode_values_for_model(model_name)
        if values is not None:
            return SelectOptionMap(key, values)
    if banlanx6xx_style_family(family) and key == "chip_order":
        values = banlanx6xx_chip_order_values_for_model(model_name)
        if values is not None:
            return SelectOptionMap(key, values)
    if key == "chip_type" and family in {
        ProtocolFamily.LEGACY_LED_CHORD,
        ProtocolFamily.LEGACY_LED_HUE,
    }:
        return SelectOptionMap(key, _LEGACY_LED_CHIP_TYPES)
    if key == "chip_order":
        values = _legacy_chip_order_values_for_model(
            family,
            color_cap=color_cap,
            model_name=model_name,
        )
        if values is not None:
            return SelectOptionMap(key, values)
    if key == "effect":
        values = _effect_values_for_family(
            family,
            color_cap=color_cap,
            model_name=model_name,
            spec_functions=spec_functions,
        )
        if values is not None:
            return SelectOptionMap(key, values)
    option_family = (
        ProtocolFamily.BANLANX_6XX if banlanx6xx_style_family(family) else family
    )
    return _SELECT_OPTIONS.get((option_family, key))


def select_options_for_family(
    family: ProtocolFamily,
    key: str,
    *,
    color_cap: int | None = None,
    model_name: str | None = None,
    spec_functions: int | None = None,
) -> tuple[str, ...]:
    """Return option labels for a protocol-family select feature."""
    option_map = select_option_map(
        family,
        key,
        color_cap=color_cap,
        model_name=model_name,
        spec_functions=spec_functions,
    )
    return () if option_map is None else option_map.options


def select_options_for_model(model: CatalogModel, key: str) -> tuple[str, ...]:
    """Return option labels for a catalog model select feature."""
    return select_options_for_family(
        model.family,
        key,
        color_cap=model.color_cap,
        model_name=model.name,
        spec_functions=model.spec_functions,
    )


def legacy_v23_model_has_audio_controls(
    family: ProtocolFamily,
    *,
    model_name: str | None = None,
    spec_functions: int | None = None,
) -> bool:
    """Return whether a BanlanX2/BanlanX3 model has old-UniLED audio controls."""
    if family not in {ProtocolFamily.BANLANX_V2, ProtocolFamily.BANLANX_V3}:
        return False
    if spec_functions is not None:
        return bool(int(spec_functions) & _LEGACY_V23_AUDIO_CONTROL_BIT)
    if model_name in _LEGACY_V23_NO_AUDIO_MODELS:
        return False
    return True


def legacy_v23_model_has_white_channel(
    family: ProtocolFamily,
    *,
    color_cap: int | None = None,
    model_name: str | None = None,
) -> bool:
    """Return whether a BanlanX2/BanlanX3 model has an RGBW white channel."""
    if family not in {ProtocolFamily.BANLANX_V2, ProtocolFamily.BANLANX_V3}:
        return False
    if color_cap == 2:
        return True
    if model_name in _LEGACY_RGBW_CHIP_ORDER_MODELS:
        return True
    return model_name is None and color_cap is None


def mode_effect_value(mode: int, effect: int) -> int:
    """Return a stable encoded value for protocols with mode-scoped effects."""
    return ((int(mode) & 0xFF) << 8) | (int(effect) & 0xFF)


def mode_effect_parts(value: int) -> tuple[int, int]:
    """Return mode and effect bytes from an encoded mode/effect value."""
    value = int(value)
    return (value >> 8) & 0xFF, value & 0xFF


def banlanx6xx_light_mode_name(mode: int | None) -> str | None:
    """Return the BanlanX6xx light-mode name for a raw mode value."""
    if mode is None:
        return None
    return _BANLANX6XX_LIGHT_MODES.get(int(mode))


def banlanx6xx_effect_name_for_state(
    light_type: int | None,
    mode: int | None,
    effect: int | None,
    *,
    model_name: str | None = None,
) -> str | None:
    """Return the BanlanX6xx combined effect label for parsed status bytes."""
    if mode is None or effect is None:
        return None
    values = banlanx6xx_effect_values_for_light_type(
        light_type,
        model_name=model_name,
    )
    if values is None:
        return None
    return values.get(mode_effect_value(mode, effect))


def banlanx6xx_effect_values_for_light_type(
    light_type: int | None,
    *,
    model_name: str | None = None,
) -> Mapping[int, str] | None:
    """Return combined mode/effect values for an SP6xx light-type byte."""
    config = _banlanx6xx_light_type_config(
        light_type,
        model_name=model_name,
    )
    if config is None:
        return None
    return _flatten_banlanx6xx_mode_effects(config)


def banlanx6xx_light_mode_values_for_light_type(
    light_type: int | None,
    *,
    model_name: str | None = None,
) -> Mapping[int, str] | None:
    """Return mode choices for an SP6xx light-type byte."""
    config = _banlanx6xx_light_type_config(
        light_type,
        model_name=model_name,
    )
    if config is None:
        return None
    return _light_mode_values_for_config(config)


def banlanx6xx_light_mode_values_for_model(
    model_name: str | None,
) -> Mapping[int, str] | None:
    """Return fixed-model SP6xx mode choices, if the model has a fixed config."""
    config = _BANLANX6XX_MODEL_CONFIGS.get(model_name or "")
    if config is None:
        return None
    return _light_mode_values_for_config(config)


def banlanx6xx_effect_attributes_for_state(
    light_type: int | None,
    mode: int | None,
    effect: int | None,
    *,
    model_name: str | None = None,
) -> BanlanX6xxEffectAttributes | None:
    """Return old-UniLED control flags for an SP6xx effect state."""
    if light_type is None or mode is None or effect is None:
        return None
    config = _banlanx6xx_light_type_config(
        light_type,
        model_name=model_name,
    )
    if config is None:
        return None
    effect_map = config.get(int(mode))
    if effect_map is None or int(effect) not in effect_map:
        return None
    return _banlanx6xx_effect_attributes(effect_map, int(effect))


def banlanx6xx_effect_type_for_mode(mode: int | None) -> str | None:
    """Return the broad effect type for a BanlanX6xx mode."""
    if mode in {
        _BANLANX6XX_MODE_STATIC_COLOR,
        _BANLANX6XX_MODE_STATIC_WHITE,
    }:
        return "Static"
    if mode in {
        _BANLANX6XX_MODE_SOUND_COLOR,
        _BANLANX6XX_MODE_SOUND_WHITE,
    }:
        return "Sound"
    if mode in {
        _BANLANX6XX_MODE_DYNAMIC_COLOR,
        _BANLANX6XX_MODE_DYNAMIC_WHITE,
        _BANLANX6XX_MODE_CUSTOM_COLOR,
        _BANLANX6XX_MODE_CUSTOM_GRADIENT,
    }:
        return "Dynamic"
    return None


def banlanx6xx_light_type_name(light_type: int | None) -> str | None:
    """Return the BanlanX6xx light-type label for a raw light-type value."""
    if light_type is None:
        return None
    return _BANLANX6XX_LIGHT_TYPE_LABELS.get(int(light_type))


def banlanx6xx_light_type_values_for_model(
    model_name: str | None,
) -> Mapping[int, str] | None:
    """Return SP6xx light-type choices for a model."""
    light_types = _BANLANX6XX_MODEL_LIGHT_TYPES.get(model_name or "")
    if light_types is None:
        return None
    return MappingProxyType(
        {
            light_type: _BANLANX6XX_LIGHT_TYPE_LABELS[light_type]
            for light_type in light_types
        }
    )


def banlanx6xx_default_light_type_for_model(model_name: str | None) -> int | None:
    """Return the first known SP6xx light-type value for a model."""
    light_types = _BANLANX6XX_MODEL_LIGHT_TYPES.get(model_name or "")
    if not light_types:
        return None
    return light_types[0]


def banlanx6xx_model_has_light_type_select(model_name: str | None) -> bool:
    """Return whether an SP6xx model exposes more than one light type."""
    light_types = _BANLANX6XX_MODEL_LIGHT_TYPES.get(model_name or "")
    return light_types is not None and len(light_types) > 1


def banlanx6xx_model_has_static_effects(model_name: str | None) -> bool:
    """Return whether an SP6xx model has a fixed old-UniLED light-type profile."""
    return model_name in _BANLANX6XX_MODEL_CONFIGS


def banlanx6xx_model_has_dynamic_light_type(model_name: str | None) -> bool:
    """Return whether an SP6xx model needs status-derived light-type options."""
    return model_name in _BANLANX6XX_DYNAMIC_LIGHT_TYPE_MODELS


def banlanx6xx_model_has_coexistence(model_name: str | None) -> bool:
    """Return whether a fixed SP6xx model supports color/white coexistence."""
    return model_name in _BANLANX6XX_COEXISTENCE_MODELS


def banlanx6xx_light_type_has_coexistence(light_type: int | None) -> bool:
    """Return whether an SP6xx status light type supports coexistence."""
    if light_type is None:
        return False
    return (int(light_type) & 0x7F) in _BANLANX6XX_COEXISTENCE_LIGHT_TYPES


def banlanx6xx_light_type_capabilities(light_type: int | None) -> tuple[str, ...]:
    """Return broad color-channel capabilities for an SP6xx light type."""
    if light_type is None:
        return ()
    raw = int(light_type)
    capabilities: list[str] = []
    if raw in _BANLANX6XX_HUE_LIGHT_TYPES:
        capabilities.append("hue")
    if raw in _BANLANX6XX_CCT_LIGHT_TYPES:
        capabilities.append("cct")
    if raw in _BANLANX6XX_WHITE_LIGHT_TYPES:
        capabilities.append("white")
    return tuple(capabilities)


def banlanx6xx_chip_order_values_for_model(
    model_name: str | None,
    *,
    light_type: int | None = None,
) -> Mapping[int, str] | None:
    """Return SP6xx chip-order choices for a model or current light type."""
    if light_type is None:
        if banlanx6xx_model_has_dynamic_light_type(model_name):
            return None
        light_type = banlanx6xx_default_light_type_for_model(model_name)
    return banlanx6xx_chip_order_values_for_light_type(light_type)


def banlanx6xx_chip_order_values_for_light_type(
    light_type: int | None,
) -> Mapping[int, str] | None:
    """Return chip-order choices for an SP6xx light type."""
    if light_type is None:
        return None
    sequence = _BANLANX6XX_LIGHT_TYPE_ORDERS.get(int(light_type))
    if not sequence:
        return None
    return MappingProxyType(
        {index: label for index, label in enumerate(_chip_order_list(sequence))}
    )


def _legacy_chip_order_values_for_model(
    family: ProtocolFamily,
    *,
    color_cap: int | None,
    model_name: str | None,
) -> Mapping[int, str] | None:
    if family in {ProtocolFamily.BANLANX_601, ProtocolFamily.BANLANX_60X}:
        sequence = _BANLANX6XX_CHIP_ORDER_RGB
    elif family in {ProtocolFamily.BANLANX_V2, ProtocolFamily.BANLANX_V3}:
        sequence = (
            _BANLANX6XX_CHIP_ORDER_RGBW
            if color_cap == 2 or model_name in _LEGACY_RGBW_CHIP_ORDER_MODELS
            else _BANLANX6XX_CHIP_ORDER_RGB
        )
    elif family in {ProtocolFamily.LEGACY_LED_CHORD, ProtocolFamily.LEGACY_LED_HUE}:
        sequence = (
            _BANLANX6XX_CHIP_ORDER_RGBW
            if color_cap in {2, 8}
            else _BANLANX6XX_CHIP_ORDER_RGB
        )
    else:
        return None
    return MappingProxyType(
        {index: label for index, label in enumerate(_chip_order_list(sequence))}
    )


def banlanx6xx_default_mode_effect_for_light_type(
    light_type: int,
    *,
    mode: int | None = None,
    effect: int | None = None,
    model_name: str | None = None,
) -> tuple[int, int, bool]:
    """Return a valid mode/effect pair for a light type.

    The boolean is true when the current pair had to be changed.
    """
    config = _banlanx6xx_light_type_config(
        light_type,
        model_name=model_name,
    )
    if config is None:
        raise KeyError(light_type)
    changed = False
    if mode not in config:
        mode = next(iter(config))
        changed = True
    effects = config[int(mode)]
    if effect not in effects:
        effect = next(iter(effects))
        changed = True
    return int(mode), int(effect), changed


def _effect_values_for_family(
    family: ProtocolFamily,
    *,
    color_cap: int | None,
    model_name: str | None,
    spec_functions: int | None,
) -> Mapping[int, str] | None:
    if family in {ProtocolFamily.BANLANX_601, ProtocolFamily.BANLANX_60X}:
        return _BANLANX_601_EFFECTS
    if family is ProtocolFamily.LEGACY_LED_CHORD:
        return _LED_CHORD_EFFECTS
    if family is ProtocolFamily.LEGACY_LED_HUE:
        return _LED_HUE_EFFECTS
    if family is ProtocolFamily.BANLANX_V2:
        if model_name in _BANLANX2_EFFECT_PROFILES:
            return _BANLANX2_EFFECT_PROFILES[model_name]
        has_audio = legacy_v23_model_has_audio_controls(
            family,
            model_name=model_name,
            spec_functions=spec_functions,
        )
        if color_cap == 2:
            return (
                _BANLANX2_EFFECTS_RGBW_SOUND
                if has_audio
                else _BANLANX2_EFFECTS_RGBW
            )
        if model_name is None:
            return _BANLANX2_EFFECTS_RGBW_SOUND
        return _BANLANX2_EFFECTS_RGB_SOUND if has_audio else _BANLANX2_EFFECTS_RGB
    if family is ProtocolFamily.BANLANX_V3:
        if model_name in _BANLANX3_EFFECT_PROFILES:
            return _BANLANX3_EFFECT_PROFILES[model_name]
        has_audio = legacy_v23_model_has_audio_controls(
            family,
            model_name=model_name,
            spec_functions=spec_functions,
        )
        if color_cap == 2:
            return (
                _BANLANX3_EFFECTS_RGBW_SOUND
                if has_audio
                else _BANLANX3_EFFECTS_RGBW
            )
        if model_name is None:
            return _BANLANX3_EFFECTS_RGBW_SOUND
        return _BANLANX3_EFFECTS_RGB_SOUND if has_audio else _BANLANX3_EFFECTS_RGB
    if banlanx6xx_style_family(family):
        if model_name is None:
            return None
        config = _BANLANX6XX_MODEL_CONFIGS.get(model_name)
        if config is None:
            return None
        return _flatten_banlanx6xx_mode_effects(config)
    return None


def _flatten_banlanx6xx_mode_effects(
    config: Mapping[int, Mapping[int, str]],
) -> Mapping[int, str]:
    values: dict[int, str] = {}
    for mode, effects in config.items():
        mode_name = _BANLANX6XX_LIGHT_MODES[mode]
        for effect, name in effects.items():
            values[mode_effect_value(mode, effect)] = f"{mode_name} - {name}"
    return MappingProxyType(values)


def _light_mode_values_for_config(
    config: Mapping[int, Mapping[int, str]],
) -> Mapping[int, str]:
    return MappingProxyType({mode: _BANLANX6XX_LIGHT_MODES[mode] for mode in config})


def _banlanx6xx_effect_attributes(
    effect_map: Mapping[int, str],
    effect: int,
) -> BanlanX6xxEffectAttributes:
    if (
        effect_map is _BANLANX6XX_EFFECTS_STATIC_COLOR
        or effect_map is _BANLANX6XX_EFFECTS_STATIC_WHITE
    ):
        return _BANLANX6XX_ATTR_NONE
    if (
        effect_map is _BANLANX6XX_PWM_EFFECTS_DYNAMIC_COLOR
        or effect_map is _BANLANX6XX_PWM_EFFECTS_DYNAMIC_WHITE
        or effect_map is _BANLANX6XX_PWM_EFFECTS_CUSTOM_COLOR
    ):
        return _BANLANX6XX_ATTR_SPEED
    if (
        effect_map is _BANLANX6XX_PWM_EFFECTS_SOUND_COLOR
        or effect_map is _BANLANX6XX_PWM_EFFECTS_SOUND_WHITE
    ):
        return _BANLANX6XX_ATTR_NONE
    if effect_map is _BANLANX6XX_SPI_EFFECTS_DYNAMIC_WHITE:
        if 5 <= effect <= 9:
            return _BANLANX6XX_ATTR_SPEED_SIZE_DIRECTION_PAUSE
        if 3 <= effect <= 10:
            return _BANLANX6XX_ATTR_SPEED_SIZE_DIRECTION
        return BanlanX6xxEffectAttributes(speedable=True, directional=True)
    if effect_map is _BANLANX6XX_SPI_EFFECTS_DYNAMIC_COLOR:
        return _banlanx6xx_spi_dynamic_color_attributes(effect)
    if effect_map is _BANLANX6XX_SPI_EFFECTS_SOUND_WHITE:
        if effect == 2:
            return _BANLANX6XX_ATTR_SIZE
        if effect in {4, 5}:
            return _BANLANX6XX_ATTR_DIRECTION
        return _BANLANX6XX_ATTR_NONE
    if effect_map is _BANLANX6XX_SPI_EFFECTS_SOUND_COLOR:
        if effect in {5, 6, 9, 10, 11, 12, 13, 14}:
            return _BANLANX6XX_ATTR_SIZE
        return _BANLANX6XX_ATTR_NONE
    if (
        effect_map is _BANLANX6XX_SPI_EFFECTS_CUSTOM_COLOR
        or effect_map is _BANLANX6XX_SPI_EFFECTS_CUSTOM_COLOR_FIREWORK
        or effect_map is _BANLANX6XX_SPI_EFFECTS_CUSTOM_GRADIENT
    ):
        return _BANLANX6XX_ATTR_NONE if effect == 1 else _BANLANX6XX_ATTR_SPEED
    return _BANLANX6XX_ATTR_NONE


def _banlanx6xx_spi_dynamic_color_attributes(
    effect: int,
) -> BanlanX6xxEffectAttributes:
    if effect in {
        0x01,
        *range(0x0F, 0x16),
        *range(0x1D, 0x4E),
        *range(0x69, 0x7D),
    }:
        return _BANLANX6XX_ATTR_SPEED_SIZE_DIRECTION_PAUSE
    if 0x8B <= effect <= 0x91:
        return _BANLANX6XX_ATTR_SPEED_SIZE_PAUSE
    if 0x01 <= effect <= 0x05 or 0x09 <= effect <= 0x7C:
        return _BANLANX6XX_ATTR_SPEED_SIZE_DIRECTION
    if effect == 0x08 or 0x7D <= effect <= 0x8A:
        return _BANLANX6XX_ATTR_SPEED_SIZE
    return _BANLANX6XX_ATTR_SPEED


def _chip_order_list(sequence: str, suffix: str = "") -> tuple[str, ...]:
    values: list[str] = []
    letters = len(sequence)
    if sequence and letters <= 3:
        values.extend(
            "".join(combo) + suffix for combo in itertools.permutations(sequence)
        )
    elif letters <= 5:
        values.extend(_chip_order_list(sequence[:3], sequence[3:]))
        for combo in itertools.permutations(sequence, len(sequence)):
            order = "".join(combo) + suffix
            if order not in values:
                values.append(order)
    return tuple(values)
