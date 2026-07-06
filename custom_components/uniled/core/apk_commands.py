"""APK-recovered BanlanX app command enum evidence."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApkCommandIdHint:
    """One BanlanX Dart app-command enum entry recovered by Blutter."""

    name: str
    ordinal: int
    command_id: int
    source: str = "blutter_hj_enum"

    @property
    def command_id_hex(self) -> str:
        """Return the command enum ID in compact hexadecimal form."""
        return f"0x{self.command_id:02x}"

    def diagnostic_summary(self) -> str:
        """Return a concise diagnostics-friendly summary."""
        return f"{self.name}={self.command_id_hex} (ordinal {self.ordinal})"


# These are app-layer enum IDs from the BanlanX 3.3.1 arm64 Dart snapshot.
# They are not, by themselves, confirmed BLE/LAN packet envelopes.
BANLANX_APP_COMMAND_ID_HINTS: tuple[ApkCommandIdHint, ...] = (
    ApkCommandIdHint("verify", 0, 0x01),
    ApkCommandIdHint("getCompositionData", 1, 0x02),
    ApkCommandIdHint("rename", 2, 0x03),
    ApkCommandIdHint("configNetwork", 3, 0x04),
    ApkCommandIdHint("heartbeat", 4, 0x05),
    ApkCommandIdHint("getStorageInfo", 5, 0x06),
    ApkCommandIdHint("formattingDisk", 6, 0x07),
    ApkCommandIdHint("setOnOffLfx", 7, 0x08),
    ApkCommandIdHint("toggleRemoteControl", 8, 0x09),
    ApkCommandIdHint("setWhiteLightCoexistWithRGB", 9, 0x0A),
    ApkCommandIdHint("setStartupState", 10, 0x0B),
    ApkCommandIdHint("setFunToggleSwitch", 11, 0x0C),
    ApkCommandIdHint("toggleSceneImage", 12, 0x0D),
    ApkCommandIdHint("updatePriFirmware", 15, 0x11),
    ApkCommandIdHint("setupAuth", 17, 0x13),
    ApkCommandIdHint("resetAuth", 18, 0x15),
    ApkCommandIdHint("getVerificationCode", 19, 0x14),
    ApkCommandIdHint("resetDevice", 20, 0x16),
    ApkCommandIdHint("configResetDeviceArgs", 21, 0x17),
    ApkCommandIdHint("switchOperatingMode", 22, 0x20),
    ApkCommandIdHint("getArtNetConfig", 23, 0x21),
    ApkCommandIdHint("setArtNetConfig", 24, 0x22),
    ApkCommandIdHint("configProvisoner", 25, 0x23),
    ApkCommandIdHint("configZoneKeyAddrMapping", 26, 0x24),
    ApkCommandIdHint("getMeshNodeUnicastAddress", 28, 0x26),
    ApkCommandIdHint("saveTimingTask", 29, 0x30),
    ApkCommandIdHint("removeTimingTask", 30, 0x31),
    ApkCommandIdHint("configTrigger", 31, 0x36),
    ApkCommandIdHint("turnOnOff", 38, 0x50),
    ApkCommandIdHint("setBrightness", 39, 0x51),
    ApkCommandIdHint("setSolidColor", 40, 0x52),
    ApkCommandIdHint("setLfxMode", 41, 0x53),
    ApkCommandIdHint("setLfxSpeed", 42, 0x54),
    ApkCommandIdHint("setLfxPixelCount", 43, 0x55),
    ApkCommandIdHint("setLfxDir", 44, 0x56),
    ApkCommandIdHint("setLfxColor", 45, 0x57),
    ApkCommandIdHint("setLfxLoopMode", 46, 0x58),
    ApkCommandIdHint("setSoundSource", 47, 0x59),
    ApkCommandIdHint("setSensitivity", 48, 0x5A),
    ApkCommandIdHint("sendSpectrum", 49, 0x5B),
    ApkCommandIdHint("saveFavoriteEffectList", 50, 0x5C),
    ApkCommandIdHint("playPauseLfx", 51, 0x5D),
    ApkCommandIdHint("resetLfx", 52, 0x5E),
    ApkCommandIdHint("setLfxColorTemp", 54, 0x60),
    ApkCommandIdHint("setSolidColorTemp", 55, 0x61),
    ApkCommandIdHint("saveDiyLfx", 57, 0x63),
    ApkCommandIdHint("setLightsDriverType", 58, 0x6A),
    ApkCommandIdHint("setLedColorChannelOrder", 59, 0x6B),
    ApkCommandIdHint("detectLedColorChannel", 60, 0x6C),
    ApkCommandIdHint("favoriteLfx", 61, 0x6D),
    ApkCommandIdHint("updateFavoriteLfxList", 62, 0x6E),
    ApkCommandIdHint("addRecScene", 65, 0x70),
    ApkCommandIdHint("renameRecScene", 66, 0x71),
    ApkCommandIdHint("getRecSceneList", 67, 0x72),
    ApkCommandIdHint("removeRecScene", 68, 0x73),
    ApkCommandIdHint("previewRecScene", 69, 0x74),
    ApkCommandIdHint("addPlaylist", 70, 0x75),
    ApkCommandIdHint("updatePlaylist", 71, 0x76),
    ApkCommandIdHint("getPlaylistList", 72, 0x77),
    ApkCommandIdHint("playPlaylist", 73, 0x78),
    ApkCommandIdHint("removePlaylist", 74, 0x79),
    ApkCommandIdHint("setLedPanelLayout", 77, 0x7E),
    ApkCommandIdHint("setMusicType", 78, 0x7F),
    ApkCommandIdHint("addStripMusicSegment", 79, 0x80),
    ApkCommandIdHint("delStripMusicSegment", 80, 0x81),
    ApkCommandIdHint("updateStripMusicSegment", 81, 0x82),
    ApkCommandIdHint("setMatrixMusicMode", 83, 0x84),
    ApkCommandIdHint("setMatrixMusicDotColor", 84, 0x85),
    ApkCommandIdHint("setMatrixMusicColColorType", 85, 0x86),
    ApkCommandIdHint("setMatrixMusicColColor", 86, 0x87),
    ApkCommandIdHint("setMatrixMusicColGradientColor", 87, 0x88),
    ApkCommandIdHint("setLfxGradient", 88, 0x90),
    ApkCommandIdHint("configWelcomeLights", 89, 0x91),
    ApkCommandIdHint("getNetworkInfo", 90, 0x92),
    ApkCommandIdHint("identify", 92, 0xC0),
    ApkCommandIdHint("bindGroup", 93, 0xC1),
    ApkCommandIdHint("unbindGroup", 94, 0xC2),
    ApkCommandIdHint("subscribeSubgroup", 95, 0xC3),
    ApkCommandIdHint("opUnsubscribeSubgroup", 96, 0xC4),
    ApkCommandIdHint("saveGroupConfig", 97, 0xC5),
    ApkCommandIdHint("assignFrameSyncMaster", 99, 0xC7),
    ApkCommandIdHint("toggleMasterSlaveHeartbeat", 100, 0xC8),
)

_BANLANX_APP_COMMAND_ID_HINTS_BY_NAME = {
    hint.name: hint for hint in BANLANX_APP_COMMAND_ID_HINTS
}


def apk_command_id_hint_for_name(name: str) -> ApkCommandIdHint | None:
    """Return the recovered app-command ID hint for a method name."""
    return _BANLANX_APP_COMMAND_ID_HINTS_BY_NAME.get(name)


def apk_command_id_hints_for_names(
    names: Iterable[str],
) -> tuple[ApkCommandIdHint, ...]:
    """Return recovered app-command ID hints for names, preserving order."""
    seen: set[str] = set()
    hints: list[ApkCommandIdHint] = []
    for name in names:
        hint = apk_command_id_hint_for_name(name)
        if hint is None or hint.name in seen:
            continue
        seen.add(hint.name)
        hints.append(hint)
    return tuple(hints)


def missing_apk_command_id_hint_names(names: Iterable[str]) -> tuple[str, ...]:
    """Return names that do not have recovered app-command enum IDs."""
    return tuple(
        name
        for name in names
        if name not in _BANLANX_APP_COMMAND_ID_HINTS_BY_NAME
    )
