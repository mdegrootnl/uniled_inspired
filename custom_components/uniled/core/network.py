"""APK-derived BanlanX network-controller profile metadata."""

from __future__ import annotations

from dataclasses import dataclass

from .apk_commands import ApkCommandIdHint, apk_command_id_hints_for_names
from .catalog import CatalogModel, ProtocolFamily

SP801E_PACKAGE = "packages/module_sp801e"
SP802E_PACKAGE = "packages/sp802e"
SP801E_PACKAGE_ASSET_COUNT = 143
SP802E_PACKAGE_ASSET_COUNT = 81

SP801E_ROUTE_HINTS = ("/sp801e",)
SP802E_ROUTE_HINTS = (
    "/sp802e",
    "/sp802e/settings",
    "/sp802e/edit_led_layout",
)

SP801E_CONTROL_SURFACES = (
    "Art-Net settings",
    "Port configuration",
    "LED layout",
    "Scene list",
    "Playlist",
    "Color correction",
    "Brightness",
    "Speed",
    "Graffiti canvas",
    "DXF import",
    "Firmware update",
)

SP801E_CONTENT_MODES = (
    "Regular effect",
    "Image",
    "GIF",
    "Graffiti",
    "Music",
    "Text",
    "Video",
)

SP801E_ARTNET_FIELDS = (
    "portActions",
    "portUniverseCounts",
    "protocolVersion",
    "startUniverse",
)

SP801E_PORT_FIELDS = (
    "channel_index",
    "sp_channel_group",
    "portDriverType",
    "portId",
    "portNo",
    "port_id",
)

SP801E_PLAYLIST_ACTIONS = (
    "getPlaylistList",
    "addPlaylist",
    "updatePlaylist",
    "removePlaylist",
)

SP802E_CONTROL_SURFACES = (
    "LFX effects",
    "Material library",
    "Favorites",
    "GIF LFX",
    "Image LFX",
    "Text LFX",
    "Graffiti LFX",
    "Rhythm LFX",
    "Animation LFX",
    "LED panel layout",
    "DIY gradient",
    "Color editing",
)

SP802E_CONTENT_MODES = (
    "Regular LFX",
    "Animation LFX",
    "GIF LFX",
    "Graffiti LFX",
    "Image LFX",
    "Text LFX",
    "Rhythm LFX",
)

SP802E_MATRIX_MUSIC_CONTROLS = (
    "setMatrixMusicMode",
    "setMatrixMusicDotColor",
    "setMatrixMusicColColor",
    "setMatrixMusicColColorType",
    "setMatrixMusicColGradientColor",
)

SP802E_LFX_GIF_COUNT = 30

SP802E_REGULAR_LFX_EFFECTS = (
    "Black hole",
    "Bursts",
    "Circle fade",
    "Diagonal fade",
    "Diamond fade",
    "GEQ",
    "Hiphotic",
    "Horizontal DNA",
    "Horizontal fade",
    "Hyper fade",
    "Matrix",
    "Metaballs",
    "Palette",
    "Party",
    "Plasmaball",
    "Soap",
    "Squared swirl",
    "Static",
    "Vertical DNA",
    "Waverly",
)

SP802E_REGULAR_LFX_EFFECT_ASSETS = (
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_black_hole.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_bursts.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_circle_fade.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_diagonal_fade.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_diamond_fade.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_geq.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_hiphotic.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_horiz_dna.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_horiz_fade.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_hyper_fade.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_matrix.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_metaballs.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_palette.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_party.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_plasmaball.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_soap.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_squaredswirl.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_static.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_vert_dna.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx_waverly.png",
)

SP802E_LFX_GIF_ASSETS = (
    f"{SP802E_PACKAGE}/assets/gifs/200.gif",
    f"{SP802E_PACKAGE}/assets/gifs/207.gif",
    f"{SP802E_PACKAGE}/assets/gifs/215_3.gif",
    f"{SP802E_PACKAGE}/assets/gifs/223.gif",
    f"{SP802E_PACKAGE}/assets/gifs/235_2.gif",
    f"{SP802E_PACKAGE}/assets/gifs/256_2.gif",
    f"{SP802E_PACKAGE}/assets/gifs/264.gif",
    f"{SP802E_PACKAGE}/assets/gifs/266.gif",
    f"{SP802E_PACKAGE}/assets/gifs/268.gif",
    f"{SP802E_PACKAGE}/assets/gifs/269.gif",
    f"{SP802E_PACKAGE}/assets/gifs/272.gif",
    f"{SP802E_PACKAGE}/assets/gifs/292_3.gif",
    f"{SP802E_PACKAGE}/assets/gifs/302.gif",
    f"{SP802E_PACKAGE}/assets/gifs/314.gif",
    f"{SP802E_PACKAGE}/assets/gifs/334.gif",
    f"{SP802E_PACKAGE}/assets/gifs/360.gif",
    f"{SP802E_PACKAGE}/assets/gifs/361.gif",
    f"{SP802E_PACKAGE}/assets/gifs/361_2.gif",
    f"{SP802E_PACKAGE}/assets/gifs/362.gif",
    f"{SP802E_PACKAGE}/assets/gifs/365.gif",
    f"{SP802E_PACKAGE}/assets/gifs/376.gif",
    f"{SP802E_PACKAGE}/assets/gifs/418_2.gif",
    f"{SP802E_PACKAGE}/assets/gifs/427_2.gif",
    f"{SP802E_PACKAGE}/assets/gifs/453_3.gif",
    f"{SP802E_PACKAGE}/assets/gifs/466.gif",
    f"{SP802E_PACKAGE}/assets/gifs/474.gif",
    f"{SP802E_PACKAGE}/assets/gifs/485_2.gif",
    f"{SP802E_PACKAGE}/assets/gifs/cs_1.gif",
    f"{SP802E_PACKAGE}/assets/gifs/cs_2.gif",
    f"{SP802E_PACKAGE}/assets/gifs/cs_3.gif",
)

SP801E_APP_METHOD_HINTS = (
    "getNetworkInfo",
    "getArtNetConfig",
    "setArtNetConfig",
    "getPlaylistList",
    "addPlaylist",
    "updatePlaylist",
    "removePlaylist",
)

SP801E_APP_COMMAND_ID_HINTS = apk_command_id_hints_for_names(
    SP801E_APP_METHOD_HINTS
)

SP802E_APP_METHOD_HINTS = (
    "getNetworkInfo",
    "setLedPanelLayout",
    "setLfxMode",
    "setLfxSpeed",
    "setLfxPixelCount",
    "setLfxLoopMode",
    "setLfxColor",
    "setLfxColorTemp",
    "setLfxGradient",
    "setLfxDir",
    "setOnOffLfx",
    "setBrightness",
    "setSensitivity",
    "setSoundSource",
    "setMatrixMusicMode",
    "setMatrixMusicDotColor",
    "setMatrixMusicColColor",
    "setMatrixMusicColColorType",
    "setMatrixMusicColGradientColor",
)

SP802E_APP_COMMAND_ID_HINTS = apk_command_id_hints_for_names(
    SP802E_APP_METHOD_HINTS
)

SP801E_WORKFLOW_HINTS = (
    (
        "ArtNetConfig includes portActions, portUniverseCounts, protocolVersion, "
        "and startUniverse fields"
    ),
    "Port setup strings use controller port numbers such as #1, p1, and P1",
    (
        "Playlist methods include getPlaylistList, addPlaylist, updatePlaylist, "
        "and removePlaylist"
    ),
    (
        "SP801E content creation includes regular, image, GIF, graffiti, music, "
        "text, and video flows"
    ),
)

SP802E_WORKFLOW_HINTS = (
    "SP802E reuses the shared /device/lfx creation routes",
    "Matrix music setters expose dot, column, color-type, and gradient color controls",
    (
        "libwled_lfx.so exposes matrix layout and 2D WLED-style effect generator "
        "symbols"
    ),
    "LFX favorite and material assets are present alongside 30 GIF previews",
)

SP801E_RAW_STRING_HINTS = (
    "portActions: [",
    "portUniverseCounts: [",
    "protocolVersion: ",
    "startUniverse: ",
    (
        "CREATE TABLE channel "
        "(id INTEGER PRIMARY KEY, device_id INTEGER, channel_index INTEGER, name TEXT)"
    ),
    (
        "CREATE TABLE sp_channel_group "
        "(id INTEGER PRIMARY KEY, device_id INTEGER, group_id INTEGER, "
        "name TEXT, channels INTEGER)"
    ),
    "channel_index",
    "device_id = ? AND channel_index = ?",
    "peripheral_group_id = ? AND channel_id = ?",
    "portDriverType",
    "portId",
    "portNo",
    "port_id",
    "music/playlist",
    "scene_playlist_action_bar",
    "scene_playlist_action_bar_empty",
)

SP802E_RAW_STRING_HINTS = (
    "lfxDurationInLoop: ",
    "lfxLoopMode: ",
    "lfxMode-",
    "lfxParams",
    "lfx_color_sets",
    "lfx_colors",
    "lfx_gradients",
    "lfx_mode_id",
    "lfx_mode_type",
    "gif_lfx_frames",
    "led_matrix_info",
    "matrixType = ",
    "wifiState",
    "wifiStrength2",
    "supportGetNetInfo",
)

SP801E_IMPORT_CONSTRAINTS = (
    (
        "Art-Net V4 control is expected to be handled by external Art-Net "
        "lighting software"
    ),
    "DXF imports are limited to no more than 4 ports",
    "DXF imports are limited to no more than 1024 LEDs per port",
    "LED screen pixel count cannot exceed 1024 in the visible layout strings",
)

SP802E_IMPORT_CONSTRAINTS = (
    "LED panel size must stay within canvas bounds",
    "Recommended canvas size should match the total size of the LED panels",
)

SP801E_TRANSPORT_HINTS = (
    "connectCaps=2 maps to LAN-only in the catalog",
    "No BLE transport is advertised for SP801E",
    (
        "The APK exposes Bonsoir/Android NSD, com.spled.plugins/multicast_lock, "
        "mDNS 224.0.0.251:5353, and raw datagram sockets, but no SP801E "
        "socket frame"
    ),
)

SP802E_TRANSPORT_HINTS = (
    "connectCaps=3 maps to BLE plus LAN in the catalog",
    "supportGetNetInfo=9 is present on SP802E",
    (
        "The APK exposes Bonsoir/Android NSD, com.spled.plugins/multicast_lock, "
        "mDNS 224.0.0.251:5353, and raw datagram sockets, but no SP802E "
        "socket frame"
    ),
    (
        "SP802E may need BLE for setup or network-info flow and LAN for local "
        "content control"
    ),
)

NETWORK_PROTOCOL_GAP_HINTS = (
    "No old-UniLED SP801E/SP802E command implementation was found",
    "No confirmed LAN discovery response or local socket frame has been mapped",
    "No concrete DNS-SD service type was recovered from the APK string surfaces",
    "No Art-Net configuration payload encoding has been mapped",
    "No SP802E BLE/LAN LFX command or status parser has been mapped",
    "No playlist, scene-list, DXF import, or panel-layout packet flow is known",
)

NETWORK_COMMON_COMMAND_BLOCKERS = (
    "network_discovery_pending",
    "network_socket_frame_pending",
    "network_dns_sd_service_pending",
)

SP801E_COMMAND_BLOCKERS = (
    *NETWORK_COMMON_COMMAND_BLOCKERS,
    "network_artnet_config_pending",
    "network_playlist_packet_pending",
    "network_dxf_import_pending",
    "network_panel_layout_pending",
)

SP802E_COMMAND_BLOCKERS = (
    *NETWORK_COMMON_COMMAND_BLOCKERS,
    "network_lfx_packet_pending",
    "network_lfx_status_parser_pending",
    "network_panel_layout_pending",
    "network_matrix_music_pending",
)

SP802E_NATIVE_LIBRARY_HINTS = (
    "libwled_lfx.so",
    "setup_matrix_layout",
    "switch_lfx_mode",
    "set_effect_params",
    "recover_effect_param",
    "updateMusicDat",
    "initRegularLfxGenerator",
    "render_frame",
    "get_frame_data",
    "mode_2Dmatrix",
    "mode_2Dmusicsoap",
    "mode_2Dmusicsquaredswirl",
    "setPixelColorXY",
    "getPixelColorXY",
    "setLineColorXY",
    "wled_DrawCircle",
)

SP802E_NATIVE_FRAME_HINTS = (
    "render_frame",
    "get_frame_data",
    "setPixelColorXY",
    "getPixelColorXY",
    "setLineColorXY",
    "addPixelColorXY",
    "fadePixelColorXY",
    "sysMatrixW",
    "sysMatrixH",
)

SP802E_NATIVE_LFX_PARAM_HINTS = (
    "switch_lfx_mode",
    "set_effect_params",
    "recover_effect_param",
    "effect_prj",
    "Create_effectsTables",
    "EFFECT_GENERATOR_CONSTRUCTORS",
    "Dyneffect_num",
    "Rhyeffect_num",
)

SP802E_NATIVE_EFFECT_GENERATOR_HINTS = (
    "create_circle_fade_effect_generator",
    "create_diamond_fade_effect_generator",
    "create_horiz_fade_effect_generator",
    "create_horiz_sym_fade_effect_generator",
    "create_hyper_fade_effect_generator",
    "create_main_diagonally_fade_effect_generator",
    "create_plasma_fade_effect_generator",
    "create_regular_fade_effect_generator",
    "create_secondary_diagonally_fade_effect_generator",
    "create_vert_fade_effect_generator",
    "create_vert_sym_fade_effect_generator",
)

SP802E_NATIVE_MATRIX_MODE_HINTS = (
    "setup_matrix_layout",
    "mode_2Dmatrix",
    "mode_2Dmusicsoap",
    "mode_2Dmusicsquaredswirl",
    "sysMatrixW",
    "sysMatrixH",
    "staRGBIC",
    "RGBCW",
)

SP802E_NATIVE_PIXEL_HELPER_HINTS = (
    "render_frame",
    "get_frame_data",
    "setPixelColorXY",
    "getPixelColorXY",
    "setLineColorXY",
    "addPixelColorXY",
    "fadePixelColorXY",
    "fillGradientRGB",
    "wled_DrawCircle",
)

SP802E_NATIVE_EXPORT_SYMBOLS = (
    "Create_effectsTables",
    "Dyneffect_num",
    "EFFECT_GENERATOR_CONSTRUCTORS",
    "Rhyeffect_num",
    "addPixelColorXY",
    "arrangeAppMusicDat",
    "create_circle_fade_effect_generator",
    "create_diamond_fade_effect_generator",
    "create_horiz_fade_effect_generator",
    "create_horiz_sym_fade_effect_generator",
    "create_hyper_fade_effect_generator",
    "create_main_diagonally_fade_effect_generator",
    "create_plasma_fade_effect_generator",
    "create_regular_fade_effect_generator",
    "create_secondary_diagonally_fade_effect_generator",
    "create_vert_fade_effect_generator",
    "create_vert_sym_fade_effect_generator",
    "effect_prj",
    "fadePixelColorXY",
    "fillGradientRGB",
    "getPixelColorXY",
    "initRegularLfxGenerator",
    "mode_2Dmatrix",
    "mode_2Dmusicsoap",
    "mode_2Dmusicsquaredswirl",
    "recover_effect_param",
    "setPixelColorXY",
    "set_effect_params",
    "setup_matrix_layout",
    "staRGBIC",
    "switch_lfx_mode",
    "sysMatrixH",
    "sysMatrixW",
    "updateMusicDat",
    "wled_DrawCircle",
)

SP802E_NATIVE_EXPORT_DETAIL_ANCHORS = (
    ("set_effect_params", 0x0000A4DD, 26),
    ("setup_matrix_layout", 0x000039FD, 92),
    ("render_frame", 0x00003ABD, 188),
    ("get_frame_data", 0x00003B79, 6),
    ("sysMatrixW", 0x0000E089, 1),
    ("sysMatrixH", 0x0000E08A, 1),
)

SP802E_NATIVE_EXPORT_HINTS = (
    "libwled_lfx.so ELF .dynsym exports 186 named symbols",
    "High-signal export scan found 35 matrix/effect/LFX/generator-related symbols",
    "The recovered RGBCW native string is not exported in .dynsym",
    "Exported setup and mode helpers include setup_matrix_layout, "
    "switch_lfx_mode, initRegularLfxGenerator, set_effect_params, and "
    "recover_effect_param",
    "Detailed dynsym scan places set_effect_params at 0x0000a4dd (26 bytes)",
    "Exported matrix/frame helpers include setPixelColorXY, getPixelColorXY, "
    "setLineColorXY, render_frame, get_frame_data, sysMatrixW, and sysMatrixH",
    "Exported regular-effect generator names include "
    "create_horiz_fade_effect_generator, "
    "create_circle_fade_effect_generator, create_diamond_fade_effect_generator, "
    "and create_plasma_fade_effect_generator",
    "Exported symbols still do not expose SP802E BLE/LAN command envelopes, "
    "local socket frames, or status parser offsets",
)

SP801E_APK_ASSET_EVIDENCE = (
    f"{SP801E_PACKAGE}/assets/animations/create.zip",
    f"{SP801E_PACKAGE}/assets/animations/home.zip",
    f"{SP801E_PACKAGE}/assets/animations/setting.zip",
    f"{SP801E_PACKAGE}/assets/icons/ic_artnet.png",
    f"{SP801E_PACKAGE}/assets/icons/ic_port.png",
    f"{SP801E_PACKAGE}/assets/icon/ic_led.png",
    f"{SP801E_PACKAGE}/assets/icons/ic_graffiti_tool_brush.png",
    f"{SP801E_PACKAGE}/assets/images/img_add_port.png",
    f"{SP801E_PACKAGE}/assets/images/img_artnet_bg.png",
    f"{SP801E_PACKAGE}/assets/images/img_artnet_config.png",
    f"{SP801E_PACKAGE}/assets/images/img_artnet_mode.png",
    f"{SP801E_PACKAGE}/assets/images/img_create_regular.png",
    f"{SP801E_PACKAGE}/assets/images/img_create_gif.png",
    f"{SP801E_PACKAGE}/assets/images/img_create_graffiti.png",
    f"{SP801E_PACKAGE}/assets/images/img_create_image.png",
    f"{SP801E_PACKAGE}/assets/images/img_create_music.png",
    f"{SP801E_PACKAGE}/assets/images/img_create_text.png",
    f"{SP801E_PACKAGE}/assets/images/img_create_video.png",
    f"{SP801E_PACKAGE}/assets/images/img_dxf_canvas_type.png",
    f"{SP801E_PACKAGE}/assets/images/img_led_layout.png",
    f"{SP801E_PACKAGE}/assets/images/img_wiring_connect.png",
)

SP802E_APK_ASSET_EVIDENCE = (
    f"{SP802E_PACKAGE}/assets/icons/ic_lfx.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_gif_lfx.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_graffiti_lfx.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_image_lfx.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_text_lfx.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_rhythm_lfx.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_animation_lfx.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_material.png",
    f"{SP802E_PACKAGE}/assets/icons/ic_favorite_lfx.png",
    f"{SP802E_PACKAGE}/assets/images/setup_led_panel_layout.png",
    f"{SP802E_PACKAGE}/assets/images/device_banner.png",
    f"{SP802E_PACKAGE}/assets/images/scene_background.png",
    f"{SP802E_PACKAGE}/assets/images/tooltip_slide_horiz.png",
    *SP802E_LFX_GIF_ASSETS,
)

SP801E_APK_STRING_EVIDENCE = (
    "Native route strings expose /sp801e as the SP801E home URI",
    "Native strings and assets expose Art-Net V4 settings and port configuration",
    (
        "Native strings expose getArtNetConfig, setArtNetConfig, and playlist "
        "app methods"
    ),
    "Native strings include the Flutter debug label: artnet config",
    (
        "Native strings expose ArtNetConfig fields including portActions and "
        "portUniverseCounts"
    ),
    "Native strings expose channel, sp_channel_group, and playlist storage labels",
    "Native strings expose DXF import limits of 4 ports and 1024 LEDs per port",
    (
        "Assets expose create flows for regular, image, GIF, graffiti, music, "
        "text, and video content"
    ),
)

SP802E_APK_STRING_EVIDENCE = (
    (
        "Native route strings expose /sp802e, /sp802e/settings, and "
        "/sp802e/edit_led_layout"
    ),
    (
        "Native strings expose getNetworkInfo and LFX setter names including "
        "setLfxMode, setLfxSpeed, and setLedPanelLayout"
    ),
    "Native library exports expose libwled_lfx.so matrix/LFX symbols",
    "Native library strings expose SP802E LFX parameter and mode-switch helpers",
    "Native library strings expose SP802E regular LFX effect generator anchors",
    "Native library strings expose SP802E matrix layout and music-mode anchors",
    "Native library strings expose SP802E pixel/frame helper anchors",
    (
        "ELF .dynsym export inspection confirms SP802E matrix/effect helpers "
        "but no BLE or LAN packet envelope"
    ),
    (
        "Native strings expose LFX state labels, gif_lfx_frames, "
        "led_matrix_info, and Wi-Fi state labels"
    ),
    (
        "Assets expose LFX modes for regular, animation, GIF, graffiti, image, "
        "text, and rhythm content"
    ),
    "Assets expose 20 regular LFX effect icons for SP802E",
    "The asset manifest exposes 30 packages/sp802e/assets/gifs previews",
)


@dataclass(frozen=True, slots=True)
class NetworkProfile:
    """Family profile recovered from SP801E/SP802E APK assets and strings."""

    family: ProtocolFamily
    package: str
    route_hints: tuple[str, ...]
    control_surfaces: tuple[str, ...]
    content_modes: tuple[str, ...]
    artnet_fields: tuple[str, ...]
    port_fields: tuple[str, ...]
    playlist_actions: tuple[str, ...]
    matrix_music_controls: tuple[str, ...]
    supports_artnet: bool
    supports_lfx: bool
    panel_layout_supported: bool
    regular_lfx_effects: tuple[str, ...]
    regular_lfx_effect_assets: tuple[str, ...]
    lfx_gif_count: int
    lfx_gif_assets: tuple[str, ...]
    app_method_hints: tuple[str, ...]
    app_command_id_hints: tuple[ApkCommandIdHint, ...]
    workflow_hints: tuple[str, ...]
    raw_string_hints: tuple[str, ...]
    import_constraints: tuple[str, ...]
    catalog_hints: tuple[str, ...]
    transport_hints: tuple[str, ...]
    protocol_gap_hints: tuple[str, ...]
    command_blockers: tuple[str, ...]
    native_library_hints: tuple[str, ...]
    native_frame_hints: tuple[str, ...]
    native_lfx_param_hints: tuple[str, ...]
    native_effect_generator_hints: tuple[str, ...]
    native_matrix_mode_hints: tuple[str, ...]
    native_pixel_helper_hints: tuple[str, ...]
    native_export_hints: tuple[str, ...]
    native_export_detail_anchors: tuple[tuple[str, int, int], ...]
    command_protocol_known: bool
    package_asset_count: int
    apk_asset_evidence: tuple[str, ...]
    apk_string_evidence: tuple[str, ...]


def network_profile_for_model(model: CatalogModel) -> NetworkProfile | None:
    """Return the APK-derived network profile for matching models."""
    if model.family is not ProtocolFamily.BANLANX_NETWORK:
        return None
    if model.name == "SP801E":
        return NetworkProfile(
            family=ProtocolFamily.BANLANX_NETWORK,
            package=SP801E_PACKAGE,
            route_hints=SP801E_ROUTE_HINTS,
            control_surfaces=SP801E_CONTROL_SURFACES,
            content_modes=SP801E_CONTENT_MODES,
            artnet_fields=SP801E_ARTNET_FIELDS,
            port_fields=SP801E_PORT_FIELDS,
            playlist_actions=SP801E_PLAYLIST_ACTIONS,
            matrix_music_controls=(),
            supports_artnet=True,
            supports_lfx=False,
            panel_layout_supported=True,
            regular_lfx_effects=(),
            regular_lfx_effect_assets=(),
            lfx_gif_count=0,
            lfx_gif_assets=(),
            app_method_hints=SP801E_APP_METHOD_HINTS,
            app_command_id_hints=SP801E_APP_COMMAND_ID_HINTS,
            workflow_hints=SP801E_WORKFLOW_HINTS,
            raw_string_hints=SP801E_RAW_STRING_HINTS,
            import_constraints=SP801E_IMPORT_CONSTRAINTS,
            catalog_hints=_catalog_hints(model),
            transport_hints=SP801E_TRANSPORT_HINTS,
            protocol_gap_hints=NETWORK_PROTOCOL_GAP_HINTS,
            command_blockers=SP801E_COMMAND_BLOCKERS,
            native_library_hints=(),
            native_frame_hints=(),
            native_lfx_param_hints=(),
            native_effect_generator_hints=(),
            native_matrix_mode_hints=(),
            native_pixel_helper_hints=(),
            native_export_hints=(),
            native_export_detail_anchors=(),
            command_protocol_known=False,
            package_asset_count=SP801E_PACKAGE_ASSET_COUNT,
            apk_asset_evidence=SP801E_APK_ASSET_EVIDENCE,
            apk_string_evidence=SP801E_APK_STRING_EVIDENCE,
        )
    if model.name == "SP802E":
        return NetworkProfile(
            family=ProtocolFamily.BANLANX_NETWORK,
            package=SP802E_PACKAGE,
            route_hints=SP802E_ROUTE_HINTS,
            control_surfaces=SP802E_CONTROL_SURFACES,
            content_modes=SP802E_CONTENT_MODES,
            artnet_fields=(),
            port_fields=(),
            playlist_actions=(),
            matrix_music_controls=SP802E_MATRIX_MUSIC_CONTROLS,
            supports_artnet=False,
            supports_lfx=True,
            panel_layout_supported=True,
            regular_lfx_effects=SP802E_REGULAR_LFX_EFFECTS,
            regular_lfx_effect_assets=SP802E_REGULAR_LFX_EFFECT_ASSETS,
            lfx_gif_count=SP802E_LFX_GIF_COUNT,
            lfx_gif_assets=SP802E_LFX_GIF_ASSETS,
            app_method_hints=SP802E_APP_METHOD_HINTS,
            app_command_id_hints=SP802E_APP_COMMAND_ID_HINTS,
            workflow_hints=SP802E_WORKFLOW_HINTS,
            raw_string_hints=SP802E_RAW_STRING_HINTS,
            import_constraints=SP802E_IMPORT_CONSTRAINTS,
            catalog_hints=_catalog_hints(model),
            transport_hints=SP802E_TRANSPORT_HINTS,
            protocol_gap_hints=NETWORK_PROTOCOL_GAP_HINTS,
            command_blockers=SP802E_COMMAND_BLOCKERS,
            native_library_hints=SP802E_NATIVE_LIBRARY_HINTS,
            native_frame_hints=SP802E_NATIVE_FRAME_HINTS,
            native_lfx_param_hints=SP802E_NATIVE_LFX_PARAM_HINTS,
            native_effect_generator_hints=SP802E_NATIVE_EFFECT_GENERATOR_HINTS,
            native_matrix_mode_hints=SP802E_NATIVE_MATRIX_MODE_HINTS,
            native_pixel_helper_hints=SP802E_NATIVE_PIXEL_HELPER_HINTS,
            native_export_hints=SP802E_NATIVE_EXPORT_HINTS,
            native_export_detail_anchors=SP802E_NATIVE_EXPORT_DETAIL_ANCHORS,
            command_protocol_known=False,
            package_asset_count=SP802E_PACKAGE_ASSET_COUNT,
            apk_asset_evidence=SP802E_APK_ASSET_EVIDENCE,
            apk_string_evidence=SP802E_APK_STRING_EVIDENCE,
        )
    return None


def _catalog_hints(model: CatalogModel) -> tuple[str, ...]:
    """Return model-specific APK catalog facts for network diagnostics."""
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
    return tuple(hints)


def describe_network_profile(profile: NetworkProfile | None) -> str | None:
    """Return a compact diagnostic string for a network-controller profile."""
    if profile is None:
        return None

    markers: list[str] = []
    if profile.supports_artnet:
        markers.append("artnet")
    if profile.artnet_fields:
        markers.append(f"artnet_fields={len(profile.artnet_fields)}")
    if profile.port_fields:
        markers.append(f"port_fields={len(profile.port_fields)}")
    if profile.playlist_actions:
        markers.append(f"playlist_actions={len(profile.playlist_actions)}")
    if profile.supports_lfx:
        markers.append(f"lfx_gifs={profile.lfx_gif_count}")
    if profile.regular_lfx_effects:
        markers.append(f"lfx_effects={len(profile.regular_lfx_effects)}")
    if profile.matrix_music_controls:
        markers.append(f"matrix_music_controls={len(profile.matrix_music_controls)}")
    if profile.panel_layout_supported:
        markers.append("panel_layout")
    if profile.app_method_hints:
        markers.append(f"methods={len(profile.app_method_hints)}")
    if profile.app_command_id_hints:
        markers.append(f"app_command_ids={len(profile.app_command_id_hints)}")
    if profile.native_library_hints:
        markers.append(f"native_hints={len(profile.native_library_hints)}")
    if profile.native_frame_hints:
        markers.append(f"native_frames={len(profile.native_frame_hints)}")
    if profile.native_lfx_param_hints:
        markers.append(f"native_lfx_params={len(profile.native_lfx_param_hints)}")
    if profile.native_effect_generator_hints:
        markers.append(
            f"native_effect_generators={len(profile.native_effect_generator_hints)}"
        )
    if profile.native_matrix_mode_hints:
        markers.append(
            f"native_matrix_modes={len(profile.native_matrix_mode_hints)}"
        )
    if profile.native_pixel_helper_hints:
        markers.append(
            f"native_pixel_helpers={len(profile.native_pixel_helper_hints)}"
        )
    if profile.native_export_hints:
        markers.append(f"native_exports={len(profile.native_export_hints)}")
    if profile.native_export_detail_anchors:
        markers.append(
            f"native_export_details={len(profile.native_export_detail_anchors)}"
        )
    if profile.workflow_hints:
        markers.append(f"workflows={len(profile.workflow_hints)}")
    if profile.raw_string_hints:
        markers.append(f"raw_strings={len(profile.raw_string_hints)}")
    if profile.import_constraints:
        markers.append(f"constraints={len(profile.import_constraints)}")
    if profile.catalog_hints:
        markers.append(f"catalog={len(profile.catalog_hints)}")
    if profile.transport_hints:
        markers.append(f"transport={len(profile.transport_hints)}")
    if profile.protocol_gap_hints:
        markers.append(f"gaps={len(profile.protocol_gap_hints)}")
    if profile.command_blockers:
        markers.append(f"blockers={len(profile.command_blockers)}")
    markers.append(f"package_assets={profile.package_asset_count}")
    markers.append(
        "command_protocol_known"
        if profile.command_protocol_known
        else "command_protocol_pending"
    )
    return (
        f"{profile.family.value}; package={profile.package}; "
        f"surfaces={len(profile.control_surfaces)}; "
        f"modes={len(profile.content_modes)}; "
        f"{'; '.join(markers)}; routes={len(profile.route_hints)}"
    )
