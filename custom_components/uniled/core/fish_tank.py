"""APK-derived FT001 fish-tank profile metadata."""

from __future__ import annotations

from dataclasses import dataclass

from .apk_commands import ApkCommandIdHint, apk_command_id_hints_for_names
from .catalog import CatalogModel, ProtocolFamily

FISH_TANK_PACKAGE = "packages/fish_tank_lights"
FISH_TANK_PACKAGE_ASSET_COUNT = 30

FISH_TANK_LIGHT_CHANNELS = (
    "First light",
    "Second light",
)

FISH_TANK_CONTROL_SURFACES = (
    "Color palette",
    "Color correction",
    "Brightness",
    "Speed",
    "Windmill",
    "Timer",
    "Favorite effects",
    "Settings",
    "Device rename",
    "Network configuration",
)

FISH_TANK_ROUTE_HINTS = (
    "/device/fish_tank_lights",
    "/device/fish_tank_lights/settings",
    "/device/fish_tank_lights/settings/rename",
    "/device/fish_tank_lights/settings/timer_list2",
    "/device/fish_tank_lights/settings/timer_list/timer_config",
    "/device/fish_tank_lights/favorite/favorite_edit",
)

FISH_TANK_EFFECT_HINTS = (
    "Windmill",
    "springwater",
)

FISH_TANK_EFFECT_STRING_HINTS = (
    "Windmill",
    "springwater",
    "waterdrop",
    "Flowing Water",
    "Spring Water2",
    "Stromend Water",
)

FISH_TANK_WORKFLOW_HINTS = (
    "First/second light channel selection",
    "Color palette editing",
    "Color correction",
    "Windmill effect",
    "Timer add/edit/delete/select workflow",
    "Favorite effect edit/empty state",
    "Device settings and rename",
    "Network configuration",
)

FISH_TANK_FAVORITE_SLOTS = (
    "Favorite 1",
    "Favorite 2",
    "Favorite 3",
    "Favorite 4",
)

FISH_TANK_FAVORITE_ACTION_HINTS = (
    "FavoriteStore0",
    "FavoriteStore1",
    "FavoriteStore2",
    "FavoriteStore3",
    "FavoriteRecall0",
    "FavoriteRecall1",
    "FavoriteRecall2",
    "FavoriteRecall3",
    "FavoriteClear0",
    "FavoriteClear1",
    "FavoriteClear2",
    "FavoriteClear3",
)

FISH_TANK_FAVORITE_STORE_HINTS = (
    "FavoriteStore0",
    "FavoriteStore1",
    "FavoriteStore2",
    "FavoriteStore3",
)

FISH_TANK_FAVORITE_RECALL_HINTS = (
    "FavoriteRecall0",
    "FavoriteRecall1",
    "FavoriteRecall2",
    "FavoriteRecall3",
)

FISH_TANK_FAVORITE_CLEAR_HINTS = (
    "FavoriteClear0",
    "FavoriteClear1",
    "FavoriteClear2",
    "FavoriteClear3",
)

FISH_TANK_FAVORITE_ACTIONS = (
    "Store favorite",
    "Recall favorite",
    "Clear favorite",
)

FISH_TANK_FAVORITE_LOOP_HINTS = (
    "favoriteLightingEffectLoopEnabled",
    "favoriteLfx",
    "NextFavoriteChannel",
    "Loop all favorite effects",
    "Stop looping the favorite effects",
)

FISH_TANK_FAVORITE_LOOP_ACTIONS = (
    "Loop all favorite effects",
    "Stop looping the favorite effects",
)

FISH_TANK_FIRMWARE_PROMPT_HINTS = (
    "FishTankLights:fw_prompted_",
)

FISH_TANK_TIMER_LIMIT = 5

FISH_TANK_TIMER_SLOTS = (
    "Timer 1",
    "Timer 2",
    "Timer 3",
    "Timer 4",
    "Timer 5",
)

FISH_TANK_TIMER_HINTS = (
    "idxTimerTaskCount",
    "Flutter | D -> idxTimerTaskCount = ",
    "newTimerId",
    "Timer interface not supported.",
    "removeTimingTask",
    "saveTimingTask",
    "timing_task",
    "You can only add up to 5 timers!",
)

FISH_TANK_TIMER_ACTIONS = (
    "Save timer",
    "Remove timer",
)

FISH_TANK_APP_METHOD_HINTS = (
    "getNetworkInfo",
    "setBrightness",
    "setLfxMode",
    "setLfxColor",
    "setLfxColorTemp",
    "setLfxLoopMode",
    "setLfxSpeed",
    "setSolidColor",
    "setSolidColorTemp",
    "saveFavoriteEffectList",
    "updateFavoriteLfxList",
    "favoriteLfx",
)

FISH_TANK_APP_COMMAND_ID_NAMES = (
    *FISH_TANK_APP_METHOD_HINTS,
    "saveTimingTask",
    "removeTimingTask",
)

FISH_TANK_APP_COMMAND_ID_HINTS = apk_command_id_hints_for_names(
    FISH_TANK_APP_COMMAND_ID_NAMES
)

FISH_TANK_DATA_MODEL_HINTS = (
    "FavoriteLightingEffectApiService",
    "FavEffectNameEntity",
    "FavoriteEffectName",
    "FavoriteStore0-3",
    "FavoriteRecall0-3",
    "FavoriteClear0-3",
    "favoriteLightingEffectIds",
    "favoriteLightingEffectLoopEnabled",
)

FISH_TANK_FAVORITE_SERVICE_HINTS = (
    "FavoriteLightingEffectApiService",
)

FISH_TANK_FAVORITE_STORAGE_HINTS = (
    "FavEffectNameEntity",
    "FavoriteEffectName",
    "favoriteLightingEffectIds",
    "favoriteLightingEffectLoopEnabled",
    "favoriteLfx",
)

FISH_TANK_TIMER_STORAGE_HINTS = (
    "idxTimerTaskCount",
    "newTimerId",
    "timerConfig",
    "timing_task",
)

FISH_TANK_BRIGHTNESS_STATE_HINTS = (
    "raw-brightness-",
    "whiteBrightness",
    "white_brightness",
)

FISH_TANK_RAW_STRING_HINTS = (
    "newTimerId: 2",
    "timerConfig",
    "raw-brightness-",
    ", whiteBrightness: ",
    "whiteBrightness",
    "white_brightness",
    "white_brightness INTEGER",
    *FISH_TANK_EFFECT_STRING_HINTS,
    *FISH_TANK_FAVORITE_LOOP_HINTS,
    *FISH_TANK_FIRMWARE_PROMPT_HINTS,
)

FISH_TANK_TIMER_STRING_HINTS = (
    "idxTimerTaskCount",
    "Flutter | D -> idxTimerTaskCount = ",
    "newTimerId",
    "newTimerId: 2",
    "timerConfig",
    "Timer interface not supported.",
    "You can only add up to 5 timers!",
    "removeTimingTask",
    "saveTimingTask",
    "timing_task",
)

FISH_TANK_BRIGHTNESS_STRING_HINTS = (
    "raw-brightness-",
    ", whiteBrightness: ",
    "whiteBrightness",
    "white_brightness",
    "white_brightness INTEGER",
)

FISH_TANK_TRANSPORT_HINTS = (
    "connectCaps=7 maps to BLE, LAN, and optional cloud in the catalog",
    "Native UUID pool includes ffe0/ffe1 and ff12/ff14/ff15 but no FT001 binding",
    "LAN discovery/control packet shape remains unconfirmed",
)

FISH_TANK_PROTOCOL_GAP_HINTS = (
    "No old-UniLED FT001 implementation was found",
    "No FT001-specific BLE opcode table was recovered",
    "No FT001 notification/status parser shape was recovered",
    "No FT001 LAN endpoint or refresh packet was recovered",
    "FT001 has no supportGetNetInfo catalog extra in APK 3.3.1",
)

FISH_TANK_COMMAND_BLOCKERS = (
    "fish_tank_ble_opcode_pending",
    "fish_tank_status_parser_pending",
    "fish_tank_lan_refresh_pending",
    "fish_tank_timer_frame_pending",
    "fish_tank_favorite_frame_pending",
    "fish_tank_effect_packet_pending",
    "fish_tank_brightness_parser_pending",
)

FISH_TANK_ICON_ASSETS = (
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_add_timer.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_checked.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_close.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_light_first.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_light_second.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_color_correct.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_color_palette.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_delete.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_edit.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_heart.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_lightness.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_speed.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_timer.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_network_config.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_pencil.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_pencil_color.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_reset.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_select_all.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_settings.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_unchecked.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_unselect_all.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_version.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_windmill.png",
)

FISH_TANK_IMAGE_ASSETS = (
    f"{FISH_TANK_PACKAGE}/assets/images/img_background.png",
    f"{FISH_TANK_PACKAGE}/assets/images/img_color_palette.png",
    f"{FISH_TANK_PACKAGE}/assets/images/img_fav_empty.png",
    f"{FISH_TANK_PACKAGE}/assets/images/img_fish_tank.png",
    f"{FISH_TANK_PACKAGE}/assets/images/img_timer_empty.png",
    f"{FISH_TANK_PACKAGE}/assets/images/img_timer_tip.png",
    f"{FISH_TANK_PACKAGE}/assets/images/img_windmill.png",
)

FISH_TANK_CHANNEL_ASSETS = (
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_light_first.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_light_second.png",
)

FISH_TANK_TIMER_ASSETS = (
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_add_timer.png",
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_timer.png",
    f"{FISH_TANK_PACKAGE}/assets/images/img_timer_empty.png",
    f"{FISH_TANK_PACKAGE}/assets/images/img_timer_tip.png",
)

FISH_TANK_FAVORITE_ASSETS = (
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_heart.png",
    f"{FISH_TANK_PACKAGE}/assets/images/img_fav_empty.png",
)

FISH_TANK_EFFECT_ASSETS = (
    f"{FISH_TANK_PACKAGE}/assets/icons/ic_windmill.png",
    f"{FISH_TANK_PACKAGE}/assets/images/img_windmill.png",
)

FISH_TANK_APK_ASSET_EVIDENCE = (
    *FISH_TANK_ICON_ASSETS,
    *FISH_TANK_IMAGE_ASSETS,
)

FISH_TANK_APK_STRING_EVIDENCE = (
    "FT001 catalog home_uri is /device/fish_tank_lights",
    "FT001 catalog flags are connectCaps=7, specFunctions=145, colorCap=1",
    (
        "Native routes expose settings, rename, timer_list2, timer_config, "
        "and favorite_edit"
    ),
    (
        "Native strings/assets include Windmill; native string table also "
        "includes springwater"
    ),
    (
        "Native string table includes waterdrop, Flowing Water, Spring Water2, "
        "and Stromend Water labels"
    ),
    (
        "Native strings include favorite effect service/storage names and "
        "save/update methods"
    ),
    "Native strings expose FavoriteStore/Recall/Clear slots 0-3",
    "Native strings expose favorite-loop actions and NextFavoriteChannel",
    "Native strings expose FishTankLights:fw_prompted_ firmware prompt storage",
    (
        "Native timer strings include idxTimerTaskCount, newTimerId, "
        "and exact 5-timer limit text"
    ),
    "Native string table includes raw brightness and white-brightness state labels",
)


@dataclass(frozen=True, slots=True)
class FishTankProfile:
    """Family profile recovered from FT001 APK assets and native strings."""

    family: ProtocolFamily
    package: str
    light_channels: tuple[str, ...]
    control_surfaces: tuple[str, ...]
    route_hints: tuple[str, ...]
    effect_hints: tuple[str, ...]
    effect_string_hints: tuple[str, ...]
    workflow_hints: tuple[str, ...]
    favorite_slots: tuple[str, ...]
    favorite_action_hints: tuple[str, ...]
    favorite_store_hints: tuple[str, ...]
    favorite_recall_hints: tuple[str, ...]
    favorite_clear_hints: tuple[str, ...]
    favorite_actions: tuple[str, ...]
    favorite_loop_hints: tuple[str, ...]
    favorite_loop_actions: tuple[str, ...]
    firmware_prompt_hints: tuple[str, ...]
    timer_limit: int | None
    timer_slots: tuple[str, ...]
    timer_hints: tuple[str, ...]
    timer_string_hints: tuple[str, ...]
    timer_actions: tuple[str, ...]
    catalog_hints: tuple[str, ...]
    app_method_hints: tuple[str, ...]
    app_command_id_hints: tuple[ApkCommandIdHint, ...]
    data_model_hints: tuple[str, ...]
    favorite_service_hints: tuple[str, ...]
    favorite_storage_hints: tuple[str, ...]
    timer_storage_hints: tuple[str, ...]
    brightness_state_hints: tuple[str, ...]
    raw_string_hints: tuple[str, ...]
    brightness_string_hints: tuple[str, ...]
    icon_assets: tuple[str, ...]
    image_assets: tuple[str, ...]
    channel_assets: tuple[str, ...]
    timer_assets: tuple[str, ...]
    favorite_assets: tuple[str, ...]
    effect_assets: tuple[str, ...]
    transport_hints: tuple[str, ...]
    protocol_gap_hints: tuple[str, ...]
    command_blockers: tuple[str, ...]
    command_protocol_known: bool
    package_asset_count: int
    apk_asset_evidence: tuple[str, ...]
    apk_string_evidence: tuple[str, ...]


def fish_tank_profile_for_model(model: CatalogModel) -> FishTankProfile | None:
    """Return the APK-derived fish-tank profile for matching models."""
    if model.family is not ProtocolFamily.FISH_TANK:
        return None
    return FishTankProfile(
        family=ProtocolFamily.FISH_TANK,
        package=FISH_TANK_PACKAGE,
        light_channels=FISH_TANK_LIGHT_CHANNELS,
        control_surfaces=FISH_TANK_CONTROL_SURFACES,
        route_hints=FISH_TANK_ROUTE_HINTS,
        effect_hints=FISH_TANK_EFFECT_HINTS,
        effect_string_hints=FISH_TANK_EFFECT_STRING_HINTS,
        workflow_hints=FISH_TANK_WORKFLOW_HINTS,
        favorite_slots=FISH_TANK_FAVORITE_SLOTS,
        favorite_action_hints=FISH_TANK_FAVORITE_ACTION_HINTS,
        favorite_store_hints=FISH_TANK_FAVORITE_STORE_HINTS,
        favorite_recall_hints=FISH_TANK_FAVORITE_RECALL_HINTS,
        favorite_clear_hints=FISH_TANK_FAVORITE_CLEAR_HINTS,
        favorite_actions=FISH_TANK_FAVORITE_ACTIONS,
        favorite_loop_hints=FISH_TANK_FAVORITE_LOOP_HINTS,
        favorite_loop_actions=FISH_TANK_FAVORITE_LOOP_ACTIONS,
        firmware_prompt_hints=FISH_TANK_FIRMWARE_PROMPT_HINTS,
        timer_limit=FISH_TANK_TIMER_LIMIT,
        timer_slots=FISH_TANK_TIMER_SLOTS,
        timer_hints=FISH_TANK_TIMER_HINTS,
        timer_string_hints=FISH_TANK_TIMER_STRING_HINTS,
        timer_actions=FISH_TANK_TIMER_ACTIONS,
        catalog_hints=(
            f"model_id={model.model_id}",
            f"connectCaps={model.connect_caps}",
            f"specFunctions={model.spec_functions}",
            f"colorCap={model.color_cap}",
            "transports="
            + ",".join(transport.value for transport in model.transports),
        ),
        app_method_hints=FISH_TANK_APP_METHOD_HINTS,
        app_command_id_hints=FISH_TANK_APP_COMMAND_ID_HINTS,
        data_model_hints=FISH_TANK_DATA_MODEL_HINTS,
        favorite_service_hints=FISH_TANK_FAVORITE_SERVICE_HINTS,
        favorite_storage_hints=FISH_TANK_FAVORITE_STORAGE_HINTS,
        timer_storage_hints=FISH_TANK_TIMER_STORAGE_HINTS,
        brightness_state_hints=FISH_TANK_BRIGHTNESS_STATE_HINTS,
        raw_string_hints=FISH_TANK_RAW_STRING_HINTS,
        brightness_string_hints=FISH_TANK_BRIGHTNESS_STRING_HINTS,
        icon_assets=FISH_TANK_ICON_ASSETS,
        image_assets=FISH_TANK_IMAGE_ASSETS,
        channel_assets=FISH_TANK_CHANNEL_ASSETS,
        timer_assets=FISH_TANK_TIMER_ASSETS,
        favorite_assets=FISH_TANK_FAVORITE_ASSETS,
        effect_assets=FISH_TANK_EFFECT_ASSETS,
        transport_hints=FISH_TANK_TRANSPORT_HINTS,
        protocol_gap_hints=FISH_TANK_PROTOCOL_GAP_HINTS,
        command_blockers=FISH_TANK_COMMAND_BLOCKERS,
        command_protocol_known=False,
        package_asset_count=FISH_TANK_PACKAGE_ASSET_COUNT,
        apk_asset_evidence=FISH_TANK_APK_ASSET_EVIDENCE,
        apk_string_evidence=FISH_TANK_APK_STRING_EVIDENCE,
    )


def describe_fish_tank_profile(profile: FishTankProfile | None) -> str | None:
    """Return a compact diagnostic string for the fish-tank profile."""
    if profile is None:
        return None
    status = (
        "command_protocol_known"
        if profile.command_protocol_known
        else "command_protocol_pending"
    )
    return (
        f"{profile.family.value}; package={profile.package}; "
        f"channels={len(profile.light_channels)}; "
        f"surfaces={len(profile.control_surfaces)}; "
        f"effects={len(profile.effect_hints)}; "
        f"effect_strings={len(profile.effect_string_hints)}; "
        f"icons={len(profile.icon_assets)}; "
        f"images={len(profile.image_assets)}; "
        f"channel_assets={len(profile.channel_assets)}; "
        f"timer_assets={len(profile.timer_assets)}; "
        f"favorite_assets={len(profile.favorite_assets)}; "
        f"effect_assets={len(profile.effect_assets)}; "
        f"workflows={len(profile.workflow_hints)}; "
        f"favorites={len(profile.favorite_slots)}; "
        f"favorite_actions={len(profile.favorite_action_hints)}; "
        f"favorite_store={len(profile.favorite_store_hints)}; "
        f"favorite_recall={len(profile.favorite_recall_hints)}; "
        f"favorite_clear={len(profile.favorite_clear_hints)}; "
        f"favorite_action_types={len(profile.favorite_actions)}; "
        f"favorite_loop_hints={len(profile.favorite_loop_hints)}; "
        f"favorite_loop_actions={len(profile.favorite_loop_actions)}; "
        f"firmware_prompts={len(profile.firmware_prompt_hints)}; "
        f"timer_limit={profile.timer_limit or 'unknown'}; "
        f"timers={len(profile.timer_slots)}; "
        f"timer_strings={len(profile.timer_string_hints)}; "
        f"timer_actions={len(profile.timer_actions)}; "
        f"methods={len(profile.app_method_hints)}; "
        f"app_command_ids={len(profile.app_command_id_hints)}; "
        f"data={len(profile.data_model_hints)}; "
        f"favorite_services={len(profile.favorite_service_hints)}; "
        f"favorite_storage={len(profile.favorite_storage_hints)}; "
        f"timer_storage={len(profile.timer_storage_hints)}; "
        f"brightness_state={len(profile.brightness_state_hints)}; "
        f"raw_strings={len(profile.raw_string_hints)}; "
        f"brightness_strings={len(profile.brightness_string_hints)}; "
        f"gaps={len(profile.protocol_gap_hints)}; "
        f"blockers={len(profile.command_blockers)}; "
        f"package_assets={profile.package_asset_count}; {status}; "
        f"routes={len(profile.route_hints)}"
    )
