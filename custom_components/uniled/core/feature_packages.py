"""APK feature-package metadata that is not a catalog device family."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NonCatalogFeaturePackageProfile:
    """APK package with app UI/resources but no model-catalog device row."""

    name: str
    package: str
    package_key: str
    package_asset_count: int
    route_hints: tuple[str, ...]
    control_surfaces: tuple[str, ...]
    required_assets: tuple[str, ...]
    storage_hints: tuple[str, ...]
    catalog_absent_terms: tuple[str, ...]
    catalog_absent_reason: str
    command_protocol_known: bool

    @property
    def asset_file_name(self) -> str:
        """Return the APK-analysis asset-list file name for this package."""
        return f"assets_{self.package_key}.txt"


GUNDAM_PACKAGE = "packages/gundam_lights"
GUNDAM_PACKAGE_KEY = "gundam_lights"
GUNDAM_PACKAGE_ASSET_COUNT = 177

GUNDAM_ROUTE_HINTS = (
    "/device/gundam_lights",
    "/device/gundam_lights/settings",
    "/device/gundam_lights/settings/on_off_mode",
    "/device/gundam_lights/settings/rename",
    "/device/gundam_lights/settings_more",
)

GUNDAM_CONTROL_SURFACES = (
    "Main device view",
    "Settings",
    "On/off mode settings",
    "Rename settings",
    "More settings",
    "Favorites",
    "Color correction",
    "Remote control",
    "Timer",
    "DIY gradient",
    "DIY solid",
    "Firmware update",
)

GUNDAM_APK_ASSET_EVIDENCE = (
    f"{GUNDAM_PACKAGE}/assets/icons/ic_beam_cannon.png",
    f"{GUNDAM_PACKAGE}/assets/icons/ic_color_correction.png",
    f"{GUNDAM_PACKAGE}/assets/icons/ic_exclusive.png",
    f"{GUNDAM_PACKAGE}/assets/icons/ic_firmware_update.png",
    f"{GUNDAM_PACKAGE}/assets/icons/ic_on_off_mode.png",
    f"{GUNDAM_PACKAGE}/assets/icons/ic_remote_control.png",
    f"{GUNDAM_PACKAGE}/assets/icons/ic_timer.png",
)

GUNDAM_STORAGE_HINTS = ("gundam_lights:effect_multi_colors",)

GUNDAM_CATALOG_ABSENT_TERMS = ("gundam", "/device/gundam_lights")

GUNDAM_CATALOG_ABSENT_REASON = (
    "APK feature package is present, but model_catalog.raw.json and "
    "model_catalog.pretty.json contain no Gundam model name or "
    "/device/gundam_lights home URI."
)

GUNDAM_COMMAND_PROTOCOL_KNOWN = False

GUNDAM_PROFILE = NonCatalogFeaturePackageProfile(
    name=GUNDAM_PACKAGE_KEY,
    package=GUNDAM_PACKAGE,
    package_key=GUNDAM_PACKAGE_KEY,
    package_asset_count=GUNDAM_PACKAGE_ASSET_COUNT,
    route_hints=GUNDAM_ROUTE_HINTS,
    control_surfaces=GUNDAM_CONTROL_SURFACES,
    required_assets=GUNDAM_APK_ASSET_EVIDENCE,
    storage_hints=GUNDAM_STORAGE_HINTS,
    catalog_absent_terms=GUNDAM_CATALOG_ABSENT_TERMS,
    catalog_absent_reason=GUNDAM_CATALOG_ABSENT_REASON,
    command_protocol_known=GUNDAM_COMMAND_PROTOCOL_KNOWN,
)

NON_CATALOG_FEATURE_PACKAGE_PROFILES = (GUNDAM_PROFILE,)


def non_catalog_feature_package_profiles() -> (
    tuple[NonCatalogFeaturePackageProfile, ...]
):
    """Return APK feature packages that must not be exposed as devices yet."""
    return NON_CATALOG_FEATURE_PACKAGE_PROFILES


def describe_non_catalog_feature_package_profile(
    profile: NonCatalogFeaturePackageProfile,
) -> tuple[str, ...]:
    """Return human-readable profile notes for diagnostics and docs."""
    protocol_status = (
        "known" if profile.command_protocol_known else "unknown"
    )
    return (
        (
            f"{profile.name}: package={profile.package}, "
            f"assets={profile.package_asset_count}"
        ),
        "catalog device: absent",
        f"catalog absence: {profile.catalog_absent_reason}",
        f"route hints: {', '.join(profile.route_hints)}",
        f"storage hints: {', '.join(profile.storage_hints)}",
        f"command protocol: {protocol_status}",
    )
