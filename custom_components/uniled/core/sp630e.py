"""APK-derived /sp630e surface metadata for SP6xx and custom 5xx models."""

from __future__ import annotations

from dataclasses import dataclass

from .apk_commands import ApkCommandIdHint, apk_command_id_hints_for_names
from .catalog import CatalogModel, ProtocolFamily

SP630E_PACKAGE = "packages/sp630e"
SP630E_HOME_URI = "/sp630e"
SP630E_PACKAGE_ASSET_COUNT = 217

SP630E_ROUTE_HINTS = (
    "/sp630e",
    "/sp630e/diy/fav",
    "/sp630e/music/config/matrix",
    "/sp630e/music/config/strip",
    "/sp630e/settings",
    "/sp630e/settings/color",
    "/sp630e/settings/color/dual",
    "/sp630e/settings/lightType",
    "/sp630e/settings/more",
    "/sp630e/settings/more/experiment",
    "/sp630e/settings/music",
    "/sp630e/settings/netConfig",
    "/sp630e/settings/powerOn",
    "/sp630e/settings/rename",
    "/sp630e/settings/timer/config",
    "/sp630e/settings/timer/list",
)

SP630E_CONTROL_SURFACES = (
    "Power",
    "Brightness",
    "Static color",
    "Dynamic effects",
    "Sound effects",
    "DIY solid effects",
    "DIY gradient effects",
    "Favorite effects",
    "Favorite effect loop",
    "Timers",
    "Light type",
    "Color order",
    "Color correction",
    "Music matrix layout",
    "Music strip layout",
    "Audio source",
    "Sensitivity",
    "Network configuration",
    "Remote status",
    "Motor mode",
    "Power-on behavior",
    "Firmware/version",
    "Device rename",
)

SP630E_FAVORITE_LIMIT_HINTS = (
    "You can only add up to 10 favorite effects",
    "You can only add up to 20 favorite effects",
    "You can only add up to 20 DIY favorite effects",
    "You can only add up to 9 favorite modes",
)

SP630E_TIMER_LIMIT = 5

SP630E_TIMER_HINTS = (
    "You can only add up to 5 timers!",
    (
        "There may be some deviations in timing, and once the device is "
        "powered off, all timers will be deleted."
    ),
    "/sp630e/settings/timer/list",
    "/sp630e/settings/timer/config",
)

SP630E_MUSIC_ASSET_HINTS = (
    f"{SP630E_PACKAGE}/assets/files/snap_fingers.mp3",
    f"{SP630E_PACKAGE}/assets/files/whistle.mp3",
    f"{SP630E_PACKAGE}/assets/images/music/matrix/1.png",
    f"{SP630E_PACKAGE}/assets/images/music/matrix/2.png",
    f"{SP630E_PACKAGE}/assets/images/music/matrix/3.png",
    f"{SP630E_PACKAGE}/assets/images/music/matrix/4.png",
    f"{SP630E_PACKAGE}/assets/images/music/matrix/5.png",
    f"{SP630E_PACKAGE}/assets/images/music/matrix/6.png",
    f"{SP630E_PACKAGE}/assets/images/music/matrix/7.png",
    f"{SP630E_PACKAGE}/assets/images/music/matrix/8.png",
    f"{SP630E_PACKAGE}/assets/images/music/matrix/9.png",
    f"{SP630E_PACKAGE}/assets/images/music/strip/1.png",
    f"{SP630E_PACKAGE}/assets/images/music/strip/2.png",
    f"{SP630E_PACKAGE}/assets/images/music/strip/3.png",
    f"{SP630E_PACKAGE}/assets/images/music/strip/4.png",
    f"{SP630E_PACKAGE}/assets/images/music/strip/5.png",
    f"{SP630E_PACKAGE}/assets/images/music/strip/6.png",
    f"{SP630E_PACKAGE}/assets/images/music/strip/7.png",
    f"{SP630E_PACKAGE}/assets/images/music/strip/8.png",
)

SP630E_NETWORK_HINTS = (
    "/sp630e/settings/netConfig",
    f"{SP630E_PACKAGE}/assets/icons/ic_network_available.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_network_reconfig.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_network_refresh.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_network_wifi.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_network_wlan.png",
    f"{SP630E_PACKAGE}/assets/images/img_network_config.png",
    f"{SP630E_PACKAGE}/assets/images/img_network_configuring.png",
    f"{SP630E_PACKAGE}/assets/images/img_network_connected.png",
    f"{SP630E_PACKAGE}/assets/images/img_network_disconnected.png",
    "device network information resolve error!",
    "supportGetNetInfo",
)

SP630E_REMOTE_HINTS = (
    f"{SP630E_PACKAGE}/assets/icons/ic_network_remote.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_state_remote.png",
    f"{SP630E_PACKAGE}/assets/images/img_remote_connected.png",
    f"{SP630E_PACKAGE}/assets/images/img_remote_not_connected.png",
    "bind remote device failed",
    "fetch from remote error",
    "sync network to remote",
)

SP630E_MOTOR_HINTS = (
    f"{SP630E_PACKAGE}/assets/icons/ic_motor_forward.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_motor_reversal.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_motor_speed_down.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_motor_speed_up.png",
    f"{SP630E_PACKAGE}/assets/images/img_motor.png",
    f"{SP630E_PACKAGE}/assets/images/img_motor_mode.png",
)

SP630E_APP_METHOD_HINTS = (
    "turnOnOff",
    "setBrightness",
    "setSolidColor",
    "setSolidColorTemp",
    "setLfxMode",
    "setLfxSpeed",
    "setLfxPixelCount",
    "setLfxDir",
    "setLfxColor",
    "setLfxColorTemp",
    "setLfxGradient",
    "setLfxLoopMode",
    "playPauseLfx",
    "resetLfx",
    "saveDiyLfx",
    "saveFavoriteEffectList",
    "favoriteLfx",
    "updateFavoriteLfxList",
    "saveTimingTask",
    "removeTimingTask",
    "setLightsDriverType",
    "setLedColorChannelOrder",
    "setWhiteLightCoexistWithRGB",
    "setStartupState",
    "setOnOffLfx",
    "setFunToggleSwitch",
    "setSoundSource",
    "setSensitivity",
    "setMusicType",
    "addStripMusicSegment",
    "delStripMusicSegment",
    "updateStripMusicSegment",
    "setMatrixMusicMode",
    "getNetworkInfo",
    "toggleRemoteControl",
)

SP630E_APP_COMMAND_ID_HINTS = apk_command_id_hints_for_names(
    SP630E_APP_METHOD_HINTS
)

SP630E_DATA_MODEL_HINTS = (
    "diyGradientLfx",
    "favLfxModeIds",
    "favoriteLightingEffectIds",
    "favoriteLightingEffectLoopEnabled",
    "favModeList",
    "fav_effect_name",
    "fav_lighting_effect_codes",
    "favoriteLfx",
)

SP630E_NATIVE_LFX_HINTS = (
    "liblfx.so",
    "IC_DriveRGB",
    "IC_PWM_C",
    "IC_PWM_CYBER",
    "PWM_DriveRGB",
    "PWM_DriveW",
    "ONLY_RGB",
    "ONLY_PWM",
    "ONLY_PWM_W",
    "RGBW_COM",
    "RGBCW",
    "CWRGB",
    "Music_Blink",
    "Music_Eject",
    "Music_Force",
    "Music_Hits",
    "Music_Spectrum",
    "Music_SymbolColors",
    "Music_VuMeter",
    "arrangeAppMusicDat",
    "getBufPixelVals",
    "maxPixelCount",
    "maxSecPixelNum",
    "lfxParams",
    "pwmEffect",
    "pwmMusicEffect",
    "pwmRerouteType",
)

SP630E_NATIVE_EXPORT_SYMBOLS = (
    "arrangeAppMusicDat",
    "COMBINE_CW",
    "CROSS_COMBINE_CW",
    "CROSS_COMBINE_W",
    "curPWMVals",
    "getBufPixelVals",
    "HAVE_CW",
    "HAVE_RGB",
    "HAVE_W",
    "IC_DriveRGB",
    "IC_DriveW",
    "IC_PWM_C",
    "IC_PWM_CYBER",
    "lfxParams",
    "maxPixelCount",
    "maxSecPixelNum",
    "Music_Blink",
    "Music_Eject",
    "Music_Force",
    "Music_Hits",
    "Music_Spectrum",
    "Music_SymbolColors",
    "Music_VuMeter",
    "ONLY_IC_W",
    "ONLY_PWM",
    "ONLY_PWM_W",
    "ONLY_RGB",
    "ONLY_W",
    "PWM_DriveRGB",
    "PWM_DriveW",
    "pwmEffect",
    "pwmMusicEffect",
    "pwmRerouteType",
    "Spin",
)

SP630E_NATIVE_EXPORT_DETAIL_ANCHORS = (
    ("pwmEffect", 0x00005435, 612),
    ("pwmMusicEffect", 0x00005925, 268),
    ("Music_Spectrum", 0x00005A31, 1314),
    ("getBufPixelVals", 0x000077E5, 288),
    ("arrangeAppMusicDat", 0x000085D9, 692),
    ("lfxParams", 0x0000B650, 136),
    ("curPWMVals", 0x0000B6ED, 7),
)

SP630E_PROTOCOL_GAP_HINTS = (
    "DIY edit/save command packets are not proven",
    "Favorite-effect add/delete/loop packets are not proven",
    "Timer add/edit/delete packet layout is not proven",
    "Remote bind/sync event packets are not proven",
    "Motor-control packet mapping is not proven",
    "LAN network-info and provisioning frames are not proven for custom 5xx",
    "liblfx.so exposes renderer internals but not BLE or LAN packet envelopes",
)

SP630E_APK_ASSET_EVIDENCE = (
    f"{SP630E_PACKAGE}/assets/icons/ic_diy_fav_del.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_diy_fav_edit.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_diy_fav_mark.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_fav_effect_loop.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_fav_loop_off.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_fav_loop_on.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_add_timer.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_setting_timer.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_setting_light.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_setting_music_layout.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_setting_network_config.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_setting_power_on.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_light_type_ic.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_light_type_pwm.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_white_brightness.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_inner_mic_selected.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_mobile_mic_selected.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_network_remote.png",
    f"{SP630E_PACKAGE}/assets/icons/ic_motor_forward.png",
    f"{SP630E_PACKAGE}/assets/images/img_custom.png",
    f"{SP630E_PACKAGE}/assets/images/img_diy_gradient_bk.png",
    f"{SP630E_PACKAGE}/assets/images/img_fav_empty.png",
    f"{SP630E_PACKAGE}/assets/images/img_light_type.png",
    f"{SP630E_PACKAGE}/assets/images/img_music_config.png",
    f"{SP630E_PACKAGE}/assets/images/img_network_config.png",
    f"{SP630E_PACKAGE}/assets/images/img_remote_connected.png",
    f"{SP630E_PACKAGE}/assets/images/img_motor.png",
    *SP630E_MUSIC_ASSET_HINTS,
)

SP630E_APK_STRING_EVIDENCE = (
    "Catalog records for SP6xx and custom 5xx models use homeUri=/sp630e",
    (
        "Native routes expose /sp630e settings, DIY favorite, music, timer, "
        "and network pages"
    ),
    "Native strings expose favorite effect IDs and loop-enabled storage fields",
    "Native strings expose save/update favorite method names",
    "Native strings include 10, 20, DIY-20, and 9-mode favorite limit text",
    (
        "Native strings include exact 5-timer limit text and power-loss "
        "timer warning"
    ),
    "Native strings expose remote bind/sync/fetch labels",
    "Native strings expose network configuration and network-info labels",
    "Native strings expose shared liblfx.so renderer, wiring, music, and PWM anchors",
    "APK assets expose light-type, music, remote, motor, timer, and favorite surfaces",
)


@dataclass(frozen=True, slots=True)
class SP630EProfile:
    """Family profile recovered from APK /sp630e assets and strings."""

    family: ProtocolFamily
    package: str
    route_hints: tuple[str, ...]
    control_surfaces: tuple[str, ...]
    favorite_limit_hints: tuple[str, ...]
    timer_limit: int | None
    timer_hints: tuple[str, ...]
    music_asset_hints: tuple[str, ...]
    network_hints: tuple[str, ...]
    remote_hints: tuple[str, ...]
    motor_hints: tuple[str, ...]
    app_method_hints: tuple[str, ...]
    app_command_id_hints: tuple[ApkCommandIdHint, ...]
    data_model_hints: tuple[str, ...]
    native_lfx_hints: tuple[str, ...]
    native_export_detail_anchors: tuple[tuple[str, int, int], ...]
    catalog_hints: tuple[str, ...]
    protocol_gap_hints: tuple[str, ...]
    command_protocol_known: bool
    package_asset_count: int
    apk_asset_evidence: tuple[str, ...]
    apk_string_evidence: tuple[str, ...]


def sp630e_profile_for_model(model: CatalogModel) -> SP630EProfile | None:
    """Return the APK-derived /sp630e profile for matching models."""
    if model.home_uri != SP630E_HOME_URI:
        return None
    if model.family not in {
        ProtocolFamily.BANLANX_6XX,
        ProtocolFamily.BANLANX_CUSTOM_5XX,
    }:
        return None
    return SP630EProfile(
        family=model.family,
        package=SP630E_PACKAGE,
        route_hints=SP630E_ROUTE_HINTS,
        control_surfaces=SP630E_CONTROL_SURFACES,
        favorite_limit_hints=SP630E_FAVORITE_LIMIT_HINTS,
        timer_limit=SP630E_TIMER_LIMIT,
        timer_hints=SP630E_TIMER_HINTS,
        music_asset_hints=SP630E_MUSIC_ASSET_HINTS,
        network_hints=SP630E_NETWORK_HINTS,
        remote_hints=SP630E_REMOTE_HINTS,
        motor_hints=SP630E_MOTOR_HINTS,
        app_method_hints=SP630E_APP_METHOD_HINTS,
        app_command_id_hints=SP630E_APP_COMMAND_ID_HINTS,
        data_model_hints=SP630E_DATA_MODEL_HINTS,
        native_lfx_hints=SP630E_NATIVE_LFX_HINTS,
        native_export_detail_anchors=SP630E_NATIVE_EXPORT_DETAIL_ANCHORS,
        catalog_hints=_catalog_hints(model),
        protocol_gap_hints=SP630E_PROTOCOL_GAP_HINTS,
        command_protocol_known=True,
        package_asset_count=SP630E_PACKAGE_ASSET_COUNT,
        apk_asset_evidence=SP630E_APK_ASSET_EVIDENCE,
        apk_string_evidence=SP630E_APK_STRING_EVIDENCE,
    )


def describe_sp630e_profile(profile: SP630EProfile | None) -> str | None:
    """Return a compact diagnostic string for the APK /sp630e profile."""
    if profile is None:
        return None
    status = (
        "legacy_ble_protocol_known"
        if profile.command_protocol_known
        else "command_protocol_pending"
    )
    return (
        f"{profile.family.value}; package={profile.package}; "
        f"surfaces={len(profile.control_surfaces)}; "
        f"routes={len(profile.route_hints)}; "
        f"favorite_limits={len(profile.favorite_limit_hints)}; "
        f"timer_limit={profile.timer_limit or 'unknown'}; "
        f"music_assets={len(profile.music_asset_hints)}; "
        f"network_hints={len(profile.network_hints)}; "
        f"remote_hints={len(profile.remote_hints)}; "
        f"motor_hints={len(profile.motor_hints)}; "
        f"methods={len(profile.app_method_hints)}; "
        f"app_command_ids={len(profile.app_command_id_hints)}; "
        f"data={len(profile.data_model_hints)}; "
        f"native_lfx={len(profile.native_lfx_hints)}; "
        f"native_export_details={len(profile.native_export_detail_anchors)}; "
        f"gaps={len(profile.protocol_gap_hints)}; "
        f"package_assets={profile.package_asset_count}; {status}"
    )


def _catalog_hints(model: CatalogModel) -> tuple[str, ...]:
    """Return model-specific APK catalog facts for /sp630e diagnostics."""
    transports = ",".join(transport.value for transport in model.transports) or "none"
    hints = [
        f"model_id={model.model_id}",
        f"parent_id={'none' if model.parent_id is None else model.parent_id}",
        f"connectCaps={model.connect_caps}",
        f"specFunctions={model.spec_functions}",
        f"colorCap={model.color_cap}",
        f"transports={transports}",
    ]
    if "supportGetNetInfo" in model.features:
        hints.append(f"supportGetNetInfo={model.features['supportGetNetInfo']}")
    if "maxPixelChannels" in model.features:
        hints.append(f"maxPixelChannels={model.features['maxPixelChannels']}")
    return tuple(hints)
