"""APK-derived BanlanX scene UI profile metadata."""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import CatalogModel, ProtocolFamily


@dataclass(frozen=True, slots=True)
class SceneNativePersistenceExport:
    """Scene native favorite/routine/system persistence export evidence."""

    capability: str
    driver: str
    symbol: str
    value: int
    size: int


SCENE_PACKAGE = "packages/scene_ui"
SCENE_MODE_ICON_COUNT = 80
SCENE_PACKAGE_ASSET_COUNT = 204

SCENE_MODE_EFFECTS = (
    "Bouncing Ball",
    "Breath",
    "Color Twinkles",
    "Comet",
    "Comet Spin",
    "Dissolve",
    "Dot Spin",
    "Drip",
    "Dynamic",
    "Ejection",
    "Energy",
    "Fire",
    "Full Color Stacking",
    "Glitter",
    "Gradient",
    "Gradual Snake",
    "Illumination",
    "Juggle",
    "Jump",
    "Lightning",
    "Meteor",
    "New Year",
    "Night Lake",
    "One Color Breathe",
    "Party",
    "Plasma",
    "Pulse",
    "Rainbow",
    "Rainbow Meteor",
    "Rainbow Ripple",
    "Rainbow Spin",
    "Ripple",
    "Scan",
    "Segment",
    "Segment Spin",
    "Seven Color Breathe",
    "Seven Color Gradient",
    "Seven Color Heartbeat",
    "Seven Color Jump",
    "Seven Color Strobe",
    "Sine",
    "Solid Fade",
    "Spectrum",
    "Stacking",
    "Stars",
    "Static",
    "Static Colors",
    "Strobe",
    "Theater",
    "Twinkle Up",
    "Vu Meter",
    "Wave",
    "White Blink",
    "White Bouncing Ball",
    "White Breathe",
    "White Chasing Dots",
    "White Comet",
    "White Comet 2",
    "White Comet Spin",
    "White Dissolve",
    "White Dot Spin",
    "White Drip",
    "White Ejection",
    "White Flowing Water",
    "White Force",
    "White Glitter",
    "White Heartbeat",
    "White Hits",
    "White Juggle",
    "White Lightning",
    "White Meteor",
    "White Night Lake",
    "White Ripple",
    "White Scan",
    "White Segment Spin",
    "White Stacking",
    "White Stars",
    "White Static",
    "White Strobe",
    "White Wave",
)

SCENE_PRESETS = (
    "Christmas",
    "Dynamic bar",
    "Eaves",
    "Esports 181",
    "Living room",
)

SCENE_CONTROL_SURFACES = (
    "Scene selection",
    "Favorites",
    "Timers",
    "Pixel count",
    "Color settings",
    "White brightness",
    "DIY gradient",
    "DIY solid",
    "Music input",
    "Inner microphone",
    "Phone microphone",
    "PC mode",
    "Speed",
    "Sensitivity",
)

SCENE_ROUTE_HINTS = (
    "/device/scene_ui",
    "/device/scene_ui/settings",
    "/device/scene_ui/settings/color",
    "/device/scene_ui/settings/more",
    "/device/scene_ui/settings/rename",
)

SCENE_LFX_ROUTE_HINTS = (
    "/device/lfx/regular",
    "/device/lfx/rhythm",
    "/device/lfx/animation",
    "/device/lfx/gif",
    "/device/lfx/graffiti2",
    "/device/lfx/image",
    "/device/lfx/text",
    "/device/scene/image/get",
)

SCENE_TIMER_ROUTE_HINTS = (
    "/device/universal/timers",
    "/device/universal/timer/config",
)

SCENE_MODE_ICON_SAMPLES = (
    "ic_mode_bouncing_ball",
    "ic_mode_breath",
    "ic_mode_comet",
    "ic_mode_fire",
    "ic_mode_rainbow",
    "ic_mode_static",
    "ic_mode_white_breathe",
    "ic_mode_white_flowing_water",
)

SCENE_APP_METHOD_HINTS = (
    "getFrameInfoHandler",
    "getFrameLenHandler",
    "getPWMFrameInfoHandler",
    "setBrightness",
    "setLfxMode",
    "setLfxSpeed",
    "setLfxPixelCount",
    "setLfxLoopMode",
    "setLfxColor",
    "setLfxColorTemp",
    "setLfxGradient",
    "setLfxDir",
    "setOnOffLfx",
    "setSensitivity",
    "setSoundSource",
    "setSolidColor",
    "setSolidColorTemp",
    "setWhiteLightCoexistWithRGB",
    "setLedPanelLayout",
)

SCENE_STORAGE_HINTS = (
    "scene_ui:scene_light_info",
    "scene_ui:effect_multi_colors",
    "addRecScene",
    "getRecSceneList",
    "removeRecScene",
    "saveDiyLfx",
    "saveFavoriteEffectList",
    "updateFavoriteLfxList",
    "resetLfx",
)

SCENE_RECENT_ACTIONS = (
    "addRecScene",
    "getRecSceneList",
    "removeRecScene",
)

SCENE_FAVORITE_ACTIONS = (
    "saveFavoriteEffectList",
    "updateFavoriteLfxList",
)

SCENE_TIMER_ACTIONS = (
    "saveTimingTask",
    "removeTimingTask",
)

SCENE_DIY_ACTIONS = (
    "saveDiyLfx",
    "resetLfx",
)

SCENE_WHITE_BRIGHTNESS_ANCHORS = (
    "raw-brightness-",
    "whiteBrightness",
    "white_brightness",
    "setWhiteLightCoexistWithRGB",
)

SCENE_RAW_STRING_HINTS = (
    "recScene",
    "removeTimingTask",
    "saveTimingTask",
    "timing_task",
    "favoriteLightingEffectIds",
    "favoriteLightingEffectLoopEnabled",
    "raw-brightness-",
    "whiteBrightness",
    "white_brightness",
    "SP31XE series requires firmware V1.1",
    "SP32XE series requires firmware V1.1",
    "One-touch Provisioning",
)

SCENE_LFX_DATA_MODEL_HINTS = (
    "Lfx(",
    "LfxColorProps.",
    "LfxColorSet{fx: ",
    "LfxDirection.",
    "LfxExternParams(",
    "LfxLoopMode.2",
    "DiyLfx(modeId: ",
    "DiyGradientLfx(modeId: ",
    "DiyLfxSegment{pixelCount: ",
    "CreativeLfxModeType.2",
    "TriggerLfxMode.",
    "WLedLfx",
    "wrappedLfx",
)

SCENE_LFX_FRAME_FIELD_HINTS = (
    "opCode = ",
    "opCode: ",
    "checksum",
    "lfxParams",
    "lfxMode-",
    "lfx_mode_id",
    "lfx_mode_type",
    "lfx_colors",
    "lfx_color_sets",
    "lfx_gradients",
    "gif_lfx_frames",
    "favLfxModeIds: [",
    "diyGradientLfx: ",
    "lfxDurationInLoop: ",
    "lfxLoopMode: ",
    "lfx: ",
)

SCENE_NATIVE_HANDLER_HINTS = (
    "API_IC_Param_Get_Handler",
    "API_IC_Scene_Set_Handler",
    "API_IC_OnOff_Set_Handler",
    "API_IC_Inrt_Set_Handler",
    "API_IC_Inrt_Reset_Handler",
    "API_IC_Channel_Set_Handler",
    "API_IC_Bright_Set_Handler",
    "API_IC_Speed_Set_Handler",
    "API_IC_Loop_Set_Handler",
    "API_IC_Sta_Clr_Set_Handler",
    "API_IC_Clr_Set_Handler",
    "API_IC_Clr_Temper_Set_Handler",
    "API_IC_Pixel_Len_Set_Handler",
    "API_IC_Direction_Set_Handler",
    "API_IC_Diy_Clr_Set_Handler",
    "API_IC_OnOff_Anim_Set_Handler",
    "API_IC_WRGB_Coexist_Set_Handler",
    "API_IC_All_Reset_Handler",
    "API_IC_Pause_Set_Handler",
    "API_IC_Clr_Paletter_Set_Handler",
    "API_PWM_Param_Get_Handler",
    "API_PWM_Scene_Set_Handler",
    "API_PWM_OnOff_Set_Handler",
    "API_PWM_Inrt_Set_Handler",
    "API_PWM_Inrt_Reset_Handler",
    "API_PWM_Channel_Set_Handler",
    "API_PWM_Bright_Set_Handler",
    "API_PWM_Speed_Set_Handler",
    "API_PWM_Loop_Set_Handler",
    "API_PWM_Sta_Clr_Set_Handler",
    "API_PWM_Clr_Set_Handler",
    "API_PWM_Clr_Temper_Set_Handler",
    "API_PWM_Diy_Clr_Set_Handler",
    "API_PWM_OnOff_Anim_Set_Handler",
    "API_PWM_WRGB_Coexist_Set_Handler",
    "API_PWM_All_Reset_Handler",
    "_IC_Scene_Loop_Handler",
    "_PWM_Scene_Loop_Handler",
)

SCENE_NATIVE_PAIRED_API_HANDLER_PAIRS = (
    ("param_get", "API_IC_Param_Get_Handler", "API_PWM_Param_Get_Handler"),
    ("scene_set", "API_IC_Scene_Set_Handler", "API_PWM_Scene_Set_Handler"),
    ("on_off_set", "API_IC_OnOff_Set_Handler", "API_PWM_OnOff_Set_Handler"),
    ("inrt_set", "API_IC_Inrt_Set_Handler", "API_PWM_Inrt_Set_Handler"),
    (
        "inrt_reset",
        "API_IC_Inrt_Reset_Handler",
        "API_PWM_Inrt_Reset_Handler",
    ),
    ("channel_set", "API_IC_Channel_Set_Handler", "API_PWM_Channel_Set_Handler"),
    ("bright_set", "API_IC_Bright_Set_Handler", "API_PWM_Bright_Set_Handler"),
    ("speed_set", "API_IC_Speed_Set_Handler", "API_PWM_Speed_Set_Handler"),
    ("loop_set", "API_IC_Loop_Set_Handler", "API_PWM_Loop_Set_Handler"),
    ("sta_clr_set", "API_IC_Sta_Clr_Set_Handler", "API_PWM_Sta_Clr_Set_Handler"),
    ("clr_set", "API_IC_Clr_Set_Handler", "API_PWM_Clr_Set_Handler"),
    (
        "clr_temper_set",
        "API_IC_Clr_Temper_Set_Handler",
        "API_PWM_Clr_Temper_Set_Handler",
    ),
    ("diy_clr_set", "API_IC_Diy_Clr_Set_Handler", "API_PWM_Diy_Clr_Set_Handler"),
    (
        "on_off_anim_set",
        "API_IC_OnOff_Anim_Set_Handler",
        "API_PWM_OnOff_Anim_Set_Handler",
    ),
    (
        "wrgb_coexist_set",
        "API_IC_WRGB_Coexist_Set_Handler",
        "API_PWM_WRGB_Coexist_Set_Handler",
    ),
    ("all_reset", "API_IC_All_Reset_Handler", "API_PWM_All_Reset_Handler"),
)

SCENE_NATIVE_PAIRED_API_CAPABILITIES = tuple(
    capability
    for capability, _ic_handler, _pwm_handler in SCENE_NATIVE_PAIRED_API_HANDLER_PAIRS
)

SCENE_NATIVE_IC_ONLY_API_HANDLERS = (
    ("pixel_len_set", "API_IC_Pixel_Len_Set_Handler"),
    ("direction_set", "API_IC_Direction_Set_Handler"),
    ("pause_set", "API_IC_Pause_Set_Handler"),
    ("clr_paletter_set", "API_IC_Clr_Paletter_Set_Handler"),
)

SCENE_NATIVE_IC_ONLY_API_CAPABILITIES = tuple(
    capability for capability, _handler in SCENE_NATIVE_IC_ONLY_API_HANDLERS
)

SCENE_NATIVE_LOOP_HANDLERS = (
    "_IC_Scene_Loop_Handler",
    "_PWM_Scene_Loop_Handler",
)

SCENE_NATIVE_LIBRARY_HINTS = (
    "libscene_lfx.so",
    "DiyEffect",
    "DiyGradEffect",
    "Music_VuMeter",
    "pwmDiyGradient",
    "pwmOnOffAnimation",
    "fillGradientRGB",
    "setPixelColor",
    "hal_App_Opcode_Handler",
    "Coexist_Map",
    "SetCoexistColor",
    "_IC_Favor_Recover_Handler",
    "_IC_Favor_Record_Handler",
    "_IC_Routine_Recover_Handler",
    "_IC_Routine_Record_Handler",
    "_IC_System_Recover_Handler",
    "_IC_LED_Type_Para_Handler",
    "_IC_Para_Default_Handler",
    "_PWM_Favor_Recover_Handler",
    "_PWM_Favor_Record_Handler",
    "_PWM_Routine_Recover_Handler",
    "_PWM_Routine_Record_Handler",
    "_PWM_System_Recover_Handler",
    "_PWM_LED_Type_Para_Handler",
    "_PWM_Para_Default_Handler",
)

SCENE_NATIVE_FRAME_HINTS = (
    "createFrameHandler",
    "getFrameInfoHandler",
    "getFrameLenHandler",
    "getPWMFrameInfoHandler",
    "getCurrFrameIntv",
    "getCurrFrameIntvHandler",
    "getChanNumHandler",
)

SCENE_NATIVE_OPCODE_HINTS = (
    "hal_App_Opcode_Handler",
    "hal_pwmCtrl_Handler_R1",
    "hal_pwmCtrl_Handler_G1",
    "hal_pwmCtrl_Handler_B1",
    "hal_pwmCtrl_Handler_CW1",
    "hal_pwmCtrl_Handler_WW1",
    "hal_WpwmCtrl_Handler_CW1",
    "hal_WpwmCtrl_Handler_WW1",
    "hal_rgbToBus_Handler_01",
)

SCENE_NATIVE_STATE_HINTS = (
    "getStaDat",
    "syncBriChangeHandler",
    "getBitState",
    "setBitlOn",
    "setBitlOff",
)

SCENE_NATIVE_STATE_EXPORTS = (
    "getStaDat@0x0001119d/256",
    "syncBriChangeHandler@0x0001118d/16",
    "getBitState@0x0000fbe9/16",
    "setBitlOn@0x0000fbb9/24",
    "setBitlOff@0x0000fbd1/24",
)

SCENE_NATIVE_COLOR_ORDER_HINTS = (
    "CRGBW",
    "CWRGB",
    "HAVE_RGB",
    "ONLY_PWM",
    "ONLY_PWM_W",
    "ONLY_RGB",
    "RGBCW",
    "RGBWC",
    "WCRGB",
    "WRGBC",
)

SCENE_NATIVE_PWM_TABLE_HINTS = (
    "IC_PWM_WDYN_TAB",
    "IC_PWM_WRHY_TAB",
    "IC_PWM_WSTA_TAB",
    "PWM_DIY_TAB",
    "PWM_DYN_TAB",
    "PWM_INRT_TAB",
    "PWM_RHY_TAB",
    "PWM_STA_TAB",
    "PWM_WDYN_TAB",
    "PWM_WRHY_TAB",
    "PWM_WSTA_TAB",
)

SCENE_NATIVE_MUSIC_EFFECT_HINTS = (
    "Music_Blink",
    "Music_Eject",
    "Music_Firework",
    "Music_Force",
    "Music_Hits",
    "Music_Spectrum",
    "Music_SymbolColors",
    "Music_VuMeter",
    "pwmDiyBreath",
    "pwmDiyGradient",
    "pwmDiyJumpColor",
    "pwmDiyStrobe",
    "pwmDynBreath",
    "pwmDynGradient",
    "pwmDynHeartBeat",
    "pwmDynJumpColor",
    "pwmDynStrobe",
    "pwmRhyBeat",
    "pwmRhyJumpColor",
    "pwmStaMode",
    "pwmOnOffAnimation",
)

SCENE_NATIVE_PWM_DRIVER_HINTS = (
    "Anim_Calibrate_PWM_Handle",
    "Anim_Echo_PWM_Handler",
    "Anim_FacTest_PWM_Handler",
    "IC_DriveRGB",
    "PWM_DriveRGB",
    "PWM_DriveW",
    "WpickClrPWM",
    "Wpwm_Ctl_s",
    "WsetPWM",
    "WsetPwmBuf",
    "hal_Wpwm_led_Init",
    "pickClrPWM",
    "pwm_Ctl_s",
    "pwm_buffer",
    "setCCTBri",
    "setPWM",
    "setPwmBuf",
)

SCENE_NATIVE_ANIMATION_EXPORTS = (
    "Anim_Calibrate_IC_Handle@0x0000f83d/96",
    "Anim_Calibrate_PWM_Handle@0x00014255/44",
    "Anim_Echo_IC_Handler@0x0000fa6d/332",
    "Anim_Echo_PWM_Handler@0x0001437d/212",
    "Anim_FacTest_IC_Handler@0x0000f89d/464",
    "Anim_FacTest_PWM_Handler@0x00014281/252",
    "API_IC_OnOff_Anim_Set_Handler@0x000152c9/28",
    "API_PWM_OnOff_Anim_Set_Handler@0x00016011/28",
    "pwmOnOffAnimation@0x000133c5/128",
    "WOnOffAnimation@0x0000f2e5/104",
)

SCENE_NATIVE_DRIVE_EXPORTS = (
    "IC_DriveRGB@0x00006904/7",
    "IC_DriveW@0x0000690b/7",
    "LED_DRIVE_TYPE@0x000196e4/4",
    "PWM_DriveRGB@0x00006912/4",
    "PWM_DriveW@0x00006916/7",
)

SCENE_NATIVE_PERSISTENCE_HANDLERS = (
    "_IC_Favor_Recover_Handler",
    "_IC_Favor_Record_Handler",
    "_IC_Routine_Recover_Handler",
    "_IC_Routine_Record_Handler",
    "_IC_System_Recover_Handler",
    "_IC_LED_Type_Para_Handler",
    "_IC_Para_Default_Handler",
    "_PWM_Favor_Recover_Handler",
    "_PWM_Favor_Record_Handler",
    "_PWM_Routine_Recover_Handler",
    "_PWM_Routine_Record_Handler",
    "_PWM_System_Recover_Handler",
    "_PWM_LED_Type_Para_Handler",
    "_PWM_Para_Default_Handler",
)

SCENE_NATIVE_PERSISTENCE_EXPORTS = (
    SceneNativePersistenceExport(
        "favor_recover",
        "ic",
        "_IC_Favor_Recover_Handler",
        0x00014451,
        368,
    ),
    SceneNativePersistenceExport(
        "favor_record",
        "ic",
        "_IC_Favor_Record_Handler",
        0x000145C1,
        372,
    ),
    SceneNativePersistenceExport(
        "routine_recover",
        "ic",
        "_IC_Routine_Recover_Handler",
        0x00014735,
        276,
    ),
    SceneNativePersistenceExport(
        "routine_record",
        "ic",
        "_IC_Routine_Record_Handler",
        0x00014849,
        4,
    ),
    SceneNativePersistenceExport(
        "system_recover",
        "ic",
        "_IC_System_Recover_Handler",
        0x0001484D,
        4,
    ),
    SceneNativePersistenceExport(
        "led_type_para",
        "ic",
        "_IC_LED_Type_Para_Handler",
        0x00014851,
        84,
    ),
    SceneNativePersistenceExport(
        "para_default",
        "ic",
        "_IC_Para_Default_Handler",
        0x000148A5,
        488,
    ),
    SceneNativePersistenceExport(
        "favor_recover",
        "pwm",
        "_PWM_Favor_Recover_Handler",
        0x000152E5,
        244,
    ),
    SceneNativePersistenceExport(
        "favor_record",
        "pwm",
        "_PWM_Favor_Record_Handler",
        0x000153D9,
        460,
    ),
    SceneNativePersistenceExport(
        "routine_recover",
        "pwm",
        "_PWM_Routine_Recover_Handler",
        0x000155A5,
        196,
    ),
    SceneNativePersistenceExport(
        "routine_record",
        "pwm",
        "_PWM_Routine_Record_Handler",
        0x00015669,
        280,
    ),
    SceneNativePersistenceExport(
        "system_recover",
        "pwm",
        "_PWM_System_Recover_Handler",
        0x00015781,
        332,
    ),
    SceneNativePersistenceExport(
        "led_type_para",
        "pwm",
        "_PWM_LED_Type_Para_Handler",
        0x000158CD,
        88,
    ),
    SceneNativePersistenceExport(
        "para_default",
        "pwm",
        "_PWM_Para_Default_Handler",
        0x00015925,
        400,
    ),
)

SCENE_NATIVE_PERSISTENCE_CAPABILITIES = tuple(
    dict.fromkeys(export.capability for export in SCENE_NATIVE_PERSISTENCE_EXPORTS)
)

SCENE_NATIVE_EXPORT_HINTS = (
    "libscene_lfx.so ELF .dynsym exports 378 named symbols",
    "High-signal export scan found 76 handler/frame/opcode/LFX-related symbols",
    "Exported frame helpers include createFrameHandler, getFrameInfoHandler, "
    "getFrameLenHandler, getPWMFrameInfoHandler, and getCurrFrameIntvHandler",
    "Exported routing helper hal_App_Opcode_Handler confirms native opcode "
    "dispatch exists inside the scene LFX library",
    "Detailed dynsym scan places hal_App_Opcode_Handler at 0x000130a9 "
    "(128 bytes)",
    "Largest exported scene handlers include API_IC_All_Reset_Handler at "
    "0x00014ec9 (864 bytes), API_PWM_All_Reset_Handler at 0x00015e05 "
    "(524 bytes), and _IC_Para_Default_Handler at 0x000148a5 (488 bytes)",
    "Scene write anchors include API_IC_Scene_Set_Handler at 0x00014a91 "
    "(292 bytes) and API_PWM_Scene_Set_Handler at 0x00015ab9 (200 bytes)",
    "Exported state helpers include getStaDat, syncBriChangeHandler, "
    "getBitState, setBitlOn, and setBitlOff",
    "Exported animation/self-test anchors include IC/PWM calibrate, echo, "
    "factory-test, and on/off animation handlers",
    "Exported drive-type anchors include IC_DriveRGB, IC_DriveW, "
    "LED_DRIVE_TYPE, PWM_DriveRGB, and PWM_DriveW",
    "Exported persistence anchors include IC/PWM favor, routine, "
    "system-recover, LED-type parameter, and parameter-default handlers",
    "Exported symbols still do not expose BLE UUID binding, command envelope "
    "bytes, or notification parser offsets",
)

SCENE_NATIVE_CODE_ANCHORS = (
    (
        "hal_App_Opcode_Handler",
        0x000130A9,
        128,
        "dd2e959db00e5af77f5e499109ae066ca2e75fdd0b547b465ec2173f41266dcf",
        "f0 b5 03 af 4d f8 04 8d 82 b0 0d 46 18 49 90 46",
        "2e 53 00 00 30 53 00 00 10 53 00 00 ee 52 00 00",
    ),
    (
        "API_IC_Scene_Set_Handler",
        0x00014A91,
        292,
        "ea67cd5706ef95ca64032ff09704cf620fc9f12cbfeac6609b9511985a690266",
        "f0 b5 03 af 4d f8 04 8d 05 46 41 48 00 2d 90 46",
        "ea 37 00 00 cc 37 00 00 a2 1b ff ff ec 1b ff ff",
    ),
    (
        "API_PWM_Scene_Set_Handler",
        0x00015AB9,
        200,
        "31199530ad84f32287b0edf244329f50ef08bb6a23490c2db29403327398d50a",
        "f0 b5 03 af 4d f8 04 8d 05 46 2b 48 00 2d 90 46",
        "28 28 00 00 16 18 ff ff a0 0b ff ff d4 0b ff ff",
    ),
    (
        "API_IC_Param_Get_Handler",
        0x00014BB5,
        160,
        "9e73876748f1eb3dbc30fd9c9788568379ea978de7f928965baddc7a5de93cbb",
        "23 4a 00 28 a1 f1 01 01 7a 44 08 bf 10 68 03 29",
        "34 37 00 00 da 36 00 00 c8 36 00 00 f6 37 00 00",
    ),
    (
        "API_PWM_Param_Get_Handler",
        0x00015B81,
        120,
        "5c2f2d31da3f7e4ceb218405d8f0541ef976fe20d7c9ae0a13227e0d88f76a2f",
        "1b 4a 00 28 a1 f1 01 01 7a 44 12 68 08 bf 02 f5",
        "34 08 70 47 00 20 70 47 68 27 00 00 4a 28 00 00",
    ),
    (
        "API_IC_All_Reset_Handler",
        0x00014EC9,
        864,
        "f2d99955a7371463ba84bfc3e49c46abc6e2197a67f9cf60ab67d1b6861c5fa1",
        "f0 b5 03 af 2d e9 00 0f 81 b0 80 46 d0 48 8b 46",
        "14 34 00 00 0c 18 ff ff 68 17 ff ff 31 16 ff ff",
    ),
    (
        "API_PWM_All_Reset_Handler",
        0x00015E05,
        524,
        "78751534b78c5226d2a0f1c9ee05aeb09c7fd467c0222676cb9ac75ab69c060b",
        "f0 b5 03 af 2d e9 00 0f 83 b0 83 46 78 48 8a 46",
        "02 09 ff ff bd 08 ff ff 4d 07 ff ff 66 07 ff ff",
    ),
)

SCENE_SETUP_REQUIREMENTS = (
    "SP31XE and SP32XE require firmware V1.1+ for one-touch provisioning",
)

SCENE_TRANSPORT_HINTS = (
    "Scene UI records with connectCaps=1 map to direct BLE",
    "Scene mesh records with connectCaps=8 map to BLE mesh",
    "Both scene families share home_uri=/device/scene_ui",
)

SCENE_PROTOCOL_GAP_HINTS = (
    "No old-UniLED scene UI or scene mesh implementation was found",
    "No confirmed scene BLE command opcode table was recovered",
    "No scene notification/status parser has been mapped",
    "No saved-scene, timer, favorite, or DIY LFX packet layout is known",
    "No SP31x/SP32x BLE-mesh routing or provisioning frame map is known",
)

SCENE_COMMAND_BLOCKERS = (
    "scene_command_envelope_pending",
    "scene_status_parser_pending",
    "scene_lfx_frame_pending",
    "scene_timer_frame_pending",
    "scene_favorite_frame_pending",
    "scene_diy_frame_pending",
    "scene_white_brightness_parser_pending",
)

SCENE_APK_ASSET_EVIDENCE = (
    f"{SCENE_PACKAGE}/assets/animations/inner_mic.json",
    f"{SCENE_PACKAGE}/assets/animations/mobile_mic.json",
    f"{SCENE_PACKAGE}/assets/animations/light_off.json",
    f"{SCENE_PACKAGE}/assets/images/scenes/christmas/thumb.png",
    f"{SCENE_PACKAGE}/assets/images/scenes/dynamic_bar/dynamic_light.png",
    f"{SCENE_PACKAGE}/assets/images/scenes/eaves/thumb.png",
    f"{SCENE_PACKAGE}/assets/images/scenes/esports_181/thumb.png",
    f"{SCENE_PACKAGE}/assets/images/scenes/living_room/thumb.png",
    f"{SCENE_PACKAGE}/assets/images/img_fav_empty.png",
    f"{SCENE_PACKAGE}/assets/images/img_timer_empty.png",
    f"{SCENE_PACKAGE}/assets/images/img_setting_color.png",
    f"{SCENE_PACKAGE}/assets/icons/ic_white_brightness.png",
    f"{SCENE_PACKAGE}/assets/icons/ic_setting_scene.png",
    f"{SCENE_PACKAGE}/assets/icons/ic_setting_timer.png",
    f"{SCENE_PACKAGE}/assets/icons/ic_setting_pixel_count.png",
    f"{SCENE_PACKAGE}/assets/icons/ic_opr_inner_mic.png",
    f"{SCENE_PACKAGE}/assets/icons/ic_opr_phone_mic.png",
    f"{SCENE_PACKAGE}/assets/icons/ic_opr_music.png",
    f"{SCENE_PACKAGE}/assets/icons/ic_effect_loop.png",
    f"{SCENE_PACKAGE}/assets/icons/ic_effect_play.png",
    f"{SCENE_PACKAGE}/assets/icons/ic_opr_direction_forward.png",
)

SCENE_APK_STRING_EVIDENCE = (
    "Scene models use the /device/scene_ui home URI in the APK catalog",
    "Native strings expose scene_ui settings, color, more, and rename routes",
    (
        "Native strings expose LFX creation routes for regular, rhythm, "
        "animation, GIF, graffiti, image, and text modes"
    ),
    (
        "Native strings expose scene LFX methods including setLfxMode, "
        "setLfxSpeed, setLfxPixelCount, and setLedPanelLayout"
    ),
    (
        "Native strings expose recent-scene and favorite-effect methods "
        "including addRecScene, getRecSceneList, and saveFavoriteEffectList"
    ),
    (
        "Native strings expose timing task and white-brightness labels, "
        "but no packet schema"
    ),
    "Native routes expose the shared universal timer list/config pages",
    "Native strings expose SP31XE/SP32XE firmware V1.1+ one-touch provisioning text",
    "Native library exports expose libscene_lfx.so IC/PWM API handler names",
    "Native library strings expose frame, opcode, and state helper anchors",
    "Native library strings expose color-order and LED-type capability anchors",
    "Native library strings expose PWM static, dynamic, rhythm, and DIY tables",
    "Native library strings expose scene music, rhythm, and LFX effect routines",
    "Native library strings expose PWM driver, buffer, and write helpers",
    (
        "Native library exports expose animation calibrate, echo, "
        "factory-test, and on/off animation handlers"
    ),
    (
        "Native library exports expose IC/PWM RGB/W drive-type objects and "
        "LED_DRIVE_TYPE"
    ),
    "Native library strings expose favor/routine/system record and recover handlers",
    (
        "Native strings expose scene LFX DTO/model anchors including Lfx, "
        "DiyLfx, DiyGradientLfx, TriggerLfxMode, WLedLfx, and wrappedLfx"
    ),
    (
        "Native strings expose app-side LFX frame field labels including "
        "opCode, checksum, lfxParams, lfxMode, lfx colors, GIF frames, "
        "favorite mode IDs, loop duration, and loop mode"
    ),
    (
        "ELF .dynsym export inspection confirms frame, state, and "
        "opcode-dispatch helpers but no BLE packet envelope"
    ),
    (
        "ELF .dynsym export inspection groups 16 paired IC/PWM API handlers, "
        "4 IC-only API handlers, 2 loop handlers, and 5 state helpers"
    ),
    "The asset manifest exposes 80 packages/scene_ui ic_mode_* mode icons",
)


@dataclass(frozen=True, slots=True)
class SceneProfile:
    """Family profile recovered from scene UI APK assets and strings."""

    family: ProtocolFamily
    package: str
    presets: tuple[str, ...]
    control_surfaces: tuple[str, ...]
    route_hints: tuple[str, ...]
    lfx_route_hints: tuple[str, ...]
    timer_route_hints: tuple[str, ...]
    mode_icon_count: int
    mode_effects: tuple[str, ...]
    mode_icon_samples: tuple[str, ...]
    app_method_hints: tuple[str, ...]
    storage_hints: tuple[str, ...]
    recent_actions: tuple[str, ...]
    favorite_actions: tuple[str, ...]
    timer_actions: tuple[str, ...]
    diy_actions: tuple[str, ...]
    white_brightness_anchors: tuple[str, ...]
    raw_string_hints: tuple[str, ...]
    lfx_data_model_hints: tuple[str, ...]
    lfx_frame_field_hints: tuple[str, ...]
    native_handler_hints: tuple[str, ...]
    native_paired_api_capabilities: tuple[str, ...]
    native_ic_only_api_capabilities: tuple[str, ...]
    native_loop_handlers: tuple[str, ...]
    native_library_hints: tuple[str, ...]
    native_frame_hints: tuple[str, ...]
    native_opcode_hints: tuple[str, ...]
    native_state_hints: tuple[str, ...]
    native_state_exports: tuple[str, ...]
    native_color_order_hints: tuple[str, ...]
    native_pwm_table_hints: tuple[str, ...]
    native_music_effect_hints: tuple[str, ...]
    native_pwm_driver_hints: tuple[str, ...]
    native_animation_exports: tuple[str, ...]
    native_drive_exports: tuple[str, ...]
    native_persistence_handlers: tuple[str, ...]
    native_persistence_exports: tuple[SceneNativePersistenceExport, ...]
    native_persistence_capabilities: tuple[str, ...]
    native_export_hints: tuple[str, ...]
    native_code_anchors: tuple[tuple[str, int, int, str, str, str], ...]
    setup_requirements: tuple[str, ...]
    catalog_hints: tuple[str, ...]
    transport_hints: tuple[str, ...]
    protocol_gap_hints: tuple[str, ...]
    command_blockers: tuple[str, ...]
    command_protocol_known: bool
    package_asset_count: int
    apk_asset_evidence: tuple[str, ...]
    apk_string_evidence: tuple[str, ...]


def scene_profile_for_model(model: CatalogModel) -> SceneProfile | None:
    """Return the APK-derived scene profile for matching models."""
    if model.family not in {
        ProtocolFamily.BANLANX_SCENE_UI,
        ProtocolFamily.BANLANX_SCENE_MESH,
    }:
        return None
    return SceneProfile(
        family=model.family,
        package=SCENE_PACKAGE,
        presets=SCENE_PRESETS,
        control_surfaces=SCENE_CONTROL_SURFACES,
        route_hints=SCENE_ROUTE_HINTS,
        lfx_route_hints=SCENE_LFX_ROUTE_HINTS,
        timer_route_hints=SCENE_TIMER_ROUTE_HINTS,
        mode_icon_count=SCENE_MODE_ICON_COUNT,
        mode_effects=SCENE_MODE_EFFECTS,
        mode_icon_samples=SCENE_MODE_ICON_SAMPLES,
        app_method_hints=SCENE_APP_METHOD_HINTS,
        storage_hints=SCENE_STORAGE_HINTS,
        recent_actions=SCENE_RECENT_ACTIONS,
        favorite_actions=SCENE_FAVORITE_ACTIONS,
        timer_actions=SCENE_TIMER_ACTIONS,
        diy_actions=SCENE_DIY_ACTIONS,
        white_brightness_anchors=SCENE_WHITE_BRIGHTNESS_ANCHORS,
        raw_string_hints=SCENE_RAW_STRING_HINTS,
        lfx_data_model_hints=SCENE_LFX_DATA_MODEL_HINTS,
        lfx_frame_field_hints=SCENE_LFX_FRAME_FIELD_HINTS,
        native_handler_hints=SCENE_NATIVE_HANDLER_HINTS,
        native_paired_api_capabilities=SCENE_NATIVE_PAIRED_API_CAPABILITIES,
        native_ic_only_api_capabilities=SCENE_NATIVE_IC_ONLY_API_CAPABILITIES,
        native_loop_handlers=SCENE_NATIVE_LOOP_HANDLERS,
        native_library_hints=SCENE_NATIVE_LIBRARY_HINTS,
        native_frame_hints=SCENE_NATIVE_FRAME_HINTS,
        native_opcode_hints=SCENE_NATIVE_OPCODE_HINTS,
        native_state_hints=SCENE_NATIVE_STATE_HINTS,
        native_state_exports=SCENE_NATIVE_STATE_EXPORTS,
        native_color_order_hints=SCENE_NATIVE_COLOR_ORDER_HINTS,
        native_pwm_table_hints=SCENE_NATIVE_PWM_TABLE_HINTS,
        native_music_effect_hints=SCENE_NATIVE_MUSIC_EFFECT_HINTS,
        native_pwm_driver_hints=SCENE_NATIVE_PWM_DRIVER_HINTS,
        native_animation_exports=SCENE_NATIVE_ANIMATION_EXPORTS,
        native_drive_exports=SCENE_NATIVE_DRIVE_EXPORTS,
        native_persistence_handlers=SCENE_NATIVE_PERSISTENCE_HANDLERS,
        native_persistence_exports=SCENE_NATIVE_PERSISTENCE_EXPORTS,
        native_persistence_capabilities=SCENE_NATIVE_PERSISTENCE_CAPABILITIES,
        native_export_hints=SCENE_NATIVE_EXPORT_HINTS,
        native_code_anchors=SCENE_NATIVE_CODE_ANCHORS,
        setup_requirements=SCENE_SETUP_REQUIREMENTS,
        catalog_hints=_catalog_hints(model),
        transport_hints=SCENE_TRANSPORT_HINTS,
        protocol_gap_hints=SCENE_PROTOCOL_GAP_HINTS,
        command_blockers=SCENE_COMMAND_BLOCKERS,
        command_protocol_known=False,
        package_asset_count=SCENE_PACKAGE_ASSET_COUNT,
        apk_asset_evidence=SCENE_APK_ASSET_EVIDENCE,
        apk_string_evidence=SCENE_APK_STRING_EVIDENCE,
    )


def _catalog_hints(model: CatalogModel) -> tuple[str, ...]:
    """Return model-specific APK catalog facts for scene diagnostics."""
    parent = "none" if model.parent_id is None else str(model.parent_id)
    transports = ",".join(transport.value for transport in model.transports) or "none"
    hints = [
        f"model_id={model.model_id}",
        f"parent_id={parent}",
        f"connectCaps={model.connect_caps}",
        f"specFunctions={model.spec_functions}",
        f"colorCap={model.color_cap}",
        f"transports={transports}",
    ]
    if "maxPixelChannels" in model.features:
        hints.append(f"maxPixelChannels={model.features['maxPixelChannels']}")
    if "features" in model.features:
        hints.append(f"featureFlags={model.features['features']}")
    return tuple(hints)


def describe_scene_profile(profile: SceneProfile | None) -> str | None:
    """Return a compact diagnostic string for the scene profile."""
    if profile is None:
        return None
    status = (
        "command_protocol_known"
        if profile.command_protocol_known
        else "command_protocol_pending"
    )
    return (
        f"{profile.family.value}; package={profile.package}; "
        f"presets={len(profile.presets)}; "
        f"surfaces={len(profile.control_surfaces)}; "
        f"mode_icons={profile.mode_icon_count}; "
        f"mode_effects={len(profile.mode_effects)}; "
        f"lfx_routes={len(profile.lfx_route_hints)}; "
        f"timer_routes={len(profile.timer_route_hints)}; "
        f"methods={len(profile.app_method_hints)}; "
        f"storage={len(profile.storage_hints)}; "
        f"recent_actions={len(profile.recent_actions)}; "
        f"favorite_actions={len(profile.favorite_actions)}; "
        f"timer_actions={len(profile.timer_actions)}; "
        f"diy_actions={len(profile.diy_actions)}; "
        f"white_brightness={len(profile.white_brightness_anchors)}; "
        f"raw_strings={len(profile.raw_string_hints)}; "
        f"lfx_data={len(profile.lfx_data_model_hints)}; "
        f"lfx_frame_fields={len(profile.lfx_frame_field_hints)}; "
        f"native_handlers={len(profile.native_handler_hints)}; "
        f"native_paired_api={len(profile.native_paired_api_capabilities)}; "
        f"native_ic_only_api={len(profile.native_ic_only_api_capabilities)}; "
        f"native_loop_handlers={len(profile.native_loop_handlers)}; "
        f"native_hints={len(profile.native_library_hints)}; "
        f"native_frames={len(profile.native_frame_hints)}; "
        f"native_opcode={len(profile.native_opcode_hints)}; "
        f"native_state={len(profile.native_state_hints)}; "
        f"native_state_exports={len(profile.native_state_exports)}; "
        f"native_color_order={len(profile.native_color_order_hints)}; "
        f"native_pwm_tables={len(profile.native_pwm_table_hints)}; "
        f"native_music_effects={len(profile.native_music_effect_hints)}; "
        f"native_pwm_drivers={len(profile.native_pwm_driver_hints)}; "
        f"native_animation_exports={len(profile.native_animation_exports)}; "
        f"native_drive_exports={len(profile.native_drive_exports)}; "
        f"native_persistence={len(profile.native_persistence_handlers)}; "
        f"native_persistence_exports={len(profile.native_persistence_exports)}; "
        f"native_persistence_capabilities="
        f"{len(profile.native_persistence_capabilities)}; "
        f"native_exports={len(profile.native_export_hints)}; "
        f"native_code_anchors={len(profile.native_code_anchors)}; "
        f"setup={len(profile.setup_requirements)}; "
        f"catalog={len(profile.catalog_hints)}; "
        f"transport={len(profile.transport_hints)}; "
        f"gaps={len(profile.protocol_gap_hints)}; "
        f"blockers={len(profile.command_blockers)}; "
        f"package_assets={profile.package_asset_count}; {status}; "
        f"routes={len(profile.route_hints)}"
    )
