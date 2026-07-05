"""APK asset-package inventory recovered from BanlanX 3.3.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .car_lights import CAR_LIGHT_PACKAGE_ASSET_COUNT
from .feature_packages import GUNDAM_PROFILE
from .fish_tank import FISH_TANK_PACKAGE_ASSET_COUNT
from .network import SP801E_PACKAGE_ASSET_COUNT, SP802E_PACKAGE_ASSET_COUNT
from .scene import SCENE_PACKAGE_ASSET_COUNT
from .sp630e import SP630E_PACKAGE_ASSET_COUNT
from .transports.mesh import RG4_ACCESSORIES_PACKAGE_ASSET_COUNT


class APKAssetPackageRole(StrEnum):
    """Classification for one APK asset-package-count bucket."""

    CATALOG_DEVICE_PROFILE = "catalog_device_profile"
    NON_CATALOG_FEATURE_PACKAGE = "non_catalog_feature_package"
    SHARED_APP_SHELL = "shared_app_shell"
    SHARED_DEVICE_COMPONENT = "shared_device_component"
    ROOT_SHARED_ASSET = "root_shared_asset"
    THIRD_PARTY_ASSET = "third_party_asset"


@dataclass(frozen=True, slots=True)
class APKAssetPackageProfile:
    """One classified package from asset_package_counts.txt."""

    key: str
    expected_asset_count: int
    role: APKAssetPackageRole
    package_prefix: str
    summary: str
    representative_assets: tuple[str, ...] = ()
    related_families: tuple[str, ...] = ()

    @property
    def asset_file_name(self) -> str:
        """Return the APK-analysis asset-list file name for this bucket."""
        return f"assets_{self.key.replace('/', '_')}.txt"

    @property
    def is_device_specific(self) -> bool:
        """Return whether this bucket represents a device-facing surface."""
        return self.role in {
            APKAssetPackageRole.CATALOG_DEVICE_PROFILE,
            APKAssetPackageRole.NON_CATALOG_FEATURE_PACKAGE,
        }


APK_ASSET_PACKAGE_PROFILES = (
    APKAssetPackageProfile(
        key="sp630e",
        expected_asset_count=SP630E_PACKAGE_ASSET_COUNT,
        role=APKAssetPackageRole.CATALOG_DEVICE_PROFILE,
        package_prefix="packages/sp630e",
        summary="Shared SP6xx-style direct-light control package",
        related_families=("banlanx_6xx", "banlanx_custom_5xx"),
    ),
    APKAssetPackageProfile(
        key="scene_ui",
        expected_asset_count=SCENE_PACKAGE_ASSET_COUNT,
        role=APKAssetPackageRole.CATALOG_DEVICE_PROFILE,
        package_prefix="packages/scene_ui",
        summary="Scene UI and scene mesh LFX package",
        related_families=("banlanx_scene_ui", "banlanx_scene_mesh"),
    ),
    APKAssetPackageProfile(
        key=GUNDAM_PROFILE.package_key,
        expected_asset_count=GUNDAM_PROFILE.package_asset_count,
        role=APKAssetPackageRole.NON_CATALOG_FEATURE_PACKAGE,
        package_prefix=GUNDAM_PROFILE.package,
        summary="Gundam feature package present without model-catalog device row",
        representative_assets=GUNDAM_PROFILE.required_assets,
    ),
    APKAssetPackageProfile(
        key="module_sp801e",
        expected_asset_count=SP801E_PACKAGE_ASSET_COUNT,
        role=APKAssetPackageRole.CATALOG_DEVICE_PROFILE,
        package_prefix="packages/module_sp801e",
        summary="SP801E network controller package",
        related_families=("banlanx_network",),
    ),
    APKAssetPackageProfile(
        key="module_home",
        expected_asset_count=115,
        role=APKAssetPackageRole.SHARED_APP_SHELL,
        package_prefix="packages/module_home",
        summary="Home, discovery, account, setup, and smart-assistant shell assets",
        representative_assets=(
            "packages/module_home/assets/icons/ic_add_device.png",
            "packages/module_home/assets/images/net_config_guide/sp801e_ap.png",
            "packages/module_home/assets/images/net_config_guide/sp801e_ble.png",
        ),
    ),
    APKAssetPackageProfile(
        key="common",
        expected_asset_count=91,
        role=APKAssetPackageRole.SHARED_DEVICE_COMPONENT,
        package_prefix="packages/common",
        summary="Shared device controls for scenes, music, timers, mesh, and settings",
        representative_assets=(
            "packages/common/assets/icons/ic_ble_mesh_group.png",
            "packages/common/assets/icons/ic_led_panel_layout.png",
            "packages/common/assets/icons/ic_network_config.png",
        ),
    ),
    APKAssetPackageProfile(
        key="sp802e",
        expected_asset_count=SP802E_PACKAGE_ASSET_COUNT,
        role=APKAssetPackageRole.CATALOG_DEVICE_PROFILE,
        package_prefix="packages/sp802e",
        summary="SP802E matrix/LFX network controller package",
        related_families=("banlanx_network",),
    ),
    APKAssetPackageProfile(
        key="car_lights",
        expected_asset_count=CAR_LIGHT_PACKAGE_ASSET_COUNT,
        role=APKAssetPackageRole.CATALOG_DEVICE_PROFILE,
        package_prefix="packages/car_lights",
        summary="Car-light controller and accessory package",
        related_families=("banlanx_car_lights",),
    ),
    APKAssetPackageProfile(
        key="fish_tank_lights",
        expected_asset_count=FISH_TANK_PACKAGE_ASSET_COUNT,
        role=APKAssetPackageRole.CATALOG_DEVICE_PROFILE,
        package_prefix="packages/fish_tank_lights",
        summary="FT001 fish-tank light package",
        related_families=("fish_tank",),
    ),
    APKAssetPackageProfile(
        key="assets/images",
        expected_asset_count=29,
        role=APKAssetPackageRole.ROOT_SHARED_ASSET,
        package_prefix="assets/images",
        summary="Root shared imagery for legacy direct-light surfaces and onboarding",
        representative_assets=(
            "assets/images/lightbar.png",
            "assets/images/xx_bg_wall_light.png",
            "assets/images/music_effect_home.jpg",
        ),
    ),
    APKAssetPackageProfile(
        key="assets/icons",
        expected_asset_count=20,
        role=APKAssetPackageRole.ROOT_SHARED_ASSET,
        package_prefix="assets/icons",
        summary="Root shared icons for direct-light surfaces",
        representative_assets=(
            "assets/icons/ic_lamp.png",
            "assets/icons/ic_solid_color_selected.png",
            "assets/icons/ic_effect_selected.png",
        ),
    ),
    APKAssetPackageProfile(
        key="component_music",
        expected_asset_count=18,
        role=APKAssetPackageRole.SHARED_DEVICE_COMPONENT,
        package_prefix="packages/component_music",
        summary="Shared audio/music playback component assets",
        representative_assets=(
            "packages/component_music/assets/audio/hold_on_a_sec.mp3",
            "packages/component_music/assets/icons/ic_play.png",
            "packages/component_music/assets/lottie/audio.json",
        ),
    ),
    APKAssetPackageProfile(
        key="accessories",
        expected_asset_count=RG4_ACCESSORIES_PACKAGE_ASSET_COUNT,
        role=APKAssetPackageRole.CATALOG_DEVICE_PROFILE,
        package_prefix="packages/accessories",
        summary="RG4 BLE mesh accessory package",
        related_families=("zengge_mesh",),
    ),
    APKAssetPackageProfile(
        key="module_user",
        expected_asset_count=6,
        role=APKAssetPackageRole.SHARED_APP_SHELL,
        package_prefix="packages/module_user",
        summary="Account/login feature shell",
        representative_assets=(
            "packages/module_user/assets/icons/ic_login_arrow.png",
            "packages/module_user/assets/images/img_login_bg.png",
        ),
    ),
    APKAssetPackageProfile(
        key="basic",
        expected_asset_count=5,
        role=APKAssetPackageRole.SHARED_APP_SHELL,
        package_prefix="packages/basic",
        summary="Shared status and message icons",
        representative_assets=(
            "packages/basic/assets/icons/ic_error.png",
            "packages/basic/assets/icons/ic_success.png",
            "packages/basic/assets/icons/ic_warn.png",
        ),
    ),
    APKAssetPackageProfile(
        key="assets/fonts",
        expected_asset_count=4,
        role=APKAssetPackageRole.ROOT_SHARED_ASSET,
        package_prefix="assets/fonts",
        summary="Bundled root application fonts",
        representative_assets=(
            "assets/fonts/AntIcons.ttf",
            "assets/fonts/SongBold.ttf",
            "assets/fonts/unifont.otf",
        ),
    ),
    APKAssetPackageProfile(
        key="component_device",
        expected_asset_count=4,
        role=APKAssetPackageRole.SHARED_DEVICE_COMPONENT,
        package_prefix="packages/component_device",
        summary="Shared device connection-state component",
        representative_assets=(
            "packages/component_device/assets/icons/ic_connect.png",
            "packages/component_device/assets/icons/ic_disconnect.png",
            "packages/component_device/assets/icons/ic_reconnect.png",
        ),
    ),
    APKAssetPackageProfile(
        key="font_awesome_flutter",
        expected_asset_count=3,
        role=APKAssetPackageRole.THIRD_PARTY_ASSET,
        package_prefix="packages/font_awesome_flutter",
        summary="Bundled Font Awesome Flutter fonts",
        representative_assets=(
            "packages/font_awesome_flutter/lib/fonts/fa-brands-400.ttf",
            "packages/font_awesome_flutter/lib/fonts/fa-solid-900.ttf",
        ),
    ),
    APKAssetPackageProfile(
        key="assets/lottie",
        expected_asset_count=1,
        role=APKAssetPackageRole.ROOT_SHARED_ASSET,
        package_prefix="assets/lottie",
        summary="Root shared Lottie animation",
        representative_assets=("assets/lottie/audio.json",),
    ),
    APKAssetPackageProfile(
        key="assets/pages",
        expected_asset_count=1,
        role=APKAssetPackageRole.ROOT_SHARED_ASSET,
        package_prefix="assets/pages",
        summary="Bundled local HTML placeholder page",
        representative_assets=("assets/pages/empty.html",),
    ),
    APKAssetPackageProfile(
        key="cupertino_icons",
        expected_asset_count=1,
        role=APKAssetPackageRole.THIRD_PARTY_ASSET,
        package_prefix="packages/cupertino_icons",
        summary="Bundled Cupertino icon font",
        representative_assets=("packages/cupertino_icons/assets/CupertinoIcons.ttf",),
    ),
    APKAssetPackageProfile(
        key="leditor_api",
        expected_asset_count=1,
        role=APKAssetPackageRole.SHARED_DEVICE_COMPONENT,
        package_prefix="packages/leditor_api",
        summary="Shared LED editor bead image",
        representative_assets=("packages/leditor_api/assets/images/lamp_bead.png",),
    ),
)


def apk_asset_package_profiles() -> tuple[APKAssetPackageProfile, ...]:
    """Return the classified APK asset package inventory."""
    return APK_ASSET_PACKAGE_PROFILES


def apk_asset_package_profile_for_key(key: str) -> APKAssetPackageProfile | None:
    """Return a classified APK asset package by count-file key."""
    for profile in APK_ASSET_PACKAGE_PROFILES:
        if profile.key == key:
            return profile
    return None


def apk_asset_package_keys_by_role(
    role: APKAssetPackageRole,
) -> tuple[str, ...]:
    """Return package keys for one inventory role."""
    return tuple(
        profile.key
        for profile in APK_ASSET_PACKAGE_PROFILES
        if profile.role is role
    )
