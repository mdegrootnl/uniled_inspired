"""Audit checked-in APK evidence ledgers against local analysis artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from custom_components.uniled.core.apk_assets import (  # noqa: E402
    APK_ASSET_PACKAGE_PROFILES,
    APKAssetPackageProfile,
)
from custom_components.uniled.core.apk_commands import (  # noqa: E402
    BANLANX_APP_COMMAND_ID_HINTS,
)
from custom_components.uniled.core.car_lights import (  # noqa: E402
    CAR_LIGHT_APK_ASSET_EVIDENCE,
    CAR_LIGHT_PACKAGE,
    CAR_LIGHT_PACKAGE_ASSET_COUNT,
    CAR_LIGHT_PASSWORD_ENTRY_HINTS,
    CAR_LIGHT_PASSWORD_FLOW_STATES,
    CAR_LIGHT_PASSWORD_HINTS,
    CAR_LIGHT_PASSWORD_POLICY_HINTS,
    CAR_LIGHT_PASSWORD_RESET_HINTS,
    CAR_LIGHT_ROUTE_HINTS,
    CAR_LIGHT_SETUP_FLOW_HINTS,
    CAR_LIGHT_SETUP_KEY_HINTS,
    CAR_LIGHT_SETUP_REQUIREMENTS,
    CAR_LIGHT_SUBDEVICE_FILTERS,
    CAR_LIGHT_SUBDEVICE_HINTS,
    CAR_LIGHT_TRIGGER_ACTIONS,
    CAR_LIGHT_TRIGGER_STORAGE_HINTS,
)
from custom_components.uniled.core.cloud import (  # noqa: E402
    BANLANX_CLOUD_ENDPOINT_INVENTORY,
    BANLANX_CLOUD_RAW_STRING_HINTS,
)
from custom_components.uniled.core.feature_packages import (  # noqa: E402
    NON_CATALOG_FEATURE_PACKAGE_PROFILES,
)
from custom_components.uniled.core.fish_tank import (  # noqa: E402
    FISH_TANK_APK_ASSET_EVIDENCE,
    FISH_TANK_APP_METHOD_HINTS,
    FISH_TANK_BRIGHTNESS_STATE_HINTS,
    FISH_TANK_FAVORITE_ACTION_HINTS,
    FISH_TANK_FAVORITE_SERVICE_HINTS,
    FISH_TANK_FAVORITE_STORAGE_HINTS,
    FISH_TANK_PACKAGE,
    FISH_TANK_PACKAGE_ASSET_COUNT,
    FISH_TANK_RAW_STRING_HINTS,
    FISH_TANK_ROUTE_HINTS,
    FISH_TANK_TIMER_HINTS,
    FISH_TANK_TIMER_STORAGE_HINTS,
)
from custom_components.uniled.core.network import (  # noqa: E402
    SP801E_APK_ASSET_EVIDENCE,
    SP801E_APP_METHOD_HINTS,
    SP801E_ARTNET_FIELDS,
    SP801E_PACKAGE,
    SP801E_PACKAGE_ASSET_COUNT,
    SP801E_PLAYLIST_ACTIONS,
    SP801E_PORT_FIELDS,
    SP801E_RAW_STRING_HINTS,
    SP801E_ROUTE_HINTS,
    SP802E_APK_ASSET_EVIDENCE,
    SP802E_APP_METHOD_HINTS,
    SP802E_MATRIX_MUSIC_CONTROLS,
    SP802E_NATIVE_EFFECT_GENERATOR_HINTS,
    SP802E_NATIVE_EXPORT_DETAIL_ANCHORS,
    SP802E_NATIVE_EXPORT_SYMBOLS,
    SP802E_NATIVE_FRAME_HINTS,
    SP802E_NATIVE_LFX_PARAM_HINTS,
    SP802E_NATIVE_LIBRARY_HINTS,
    SP802E_NATIVE_MATRIX_MODE_HINTS,
    SP802E_NATIVE_PIXEL_HELPER_HINTS,
    SP802E_PACKAGE,
    SP802E_PACKAGE_ASSET_COUNT,
    SP802E_RAW_STRING_HINTS,
    SP802E_ROUTE_HINTS,
)
from custom_components.uniled.core.scene import (  # noqa: E402
    SCENE_APK_ASSET_EVIDENCE,
    SCENE_APP_METHOD_HINTS,
    SCENE_DIY_ACTIONS,
    SCENE_FAVORITE_ACTIONS,
    SCENE_LFX_DATA_MODEL_HINTS,
    SCENE_LFX_FRAME_FIELD_HINTS,
    SCENE_LFX_ROUTE_HINTS,
    SCENE_NATIVE_ANIMATION_EXPORTS,
    SCENE_NATIVE_CODE_ANCHORS,
    SCENE_NATIVE_COLOR_ORDER_HINTS,
    SCENE_NATIVE_DRIVE_EXPORTS,
    SCENE_NATIVE_FRAME_HINTS,
    SCENE_NATIVE_HANDLER_HINTS,
    SCENE_NATIVE_IC_ONLY_API_HANDLERS,
    SCENE_NATIVE_LIBRARY_HINTS,
    SCENE_NATIVE_LOOP_HANDLERS,
    SCENE_NATIVE_MUSIC_EFFECT_HINTS,
    SCENE_NATIVE_OPCODE_HINTS,
    SCENE_NATIVE_PAIRED_API_HANDLER_PAIRS,
    SCENE_NATIVE_PERSISTENCE_EXPORTS,
    SCENE_NATIVE_PERSISTENCE_HANDLERS,
    SCENE_NATIVE_PWM_DRIVER_HINTS,
    SCENE_NATIVE_PWM_TABLE_HINTS,
    SCENE_NATIVE_STATE_EXPORTS,
    SCENE_NATIVE_STATE_HINTS,
    SCENE_PACKAGE,
    SCENE_PACKAGE_ASSET_COUNT,
    SCENE_RAW_STRING_HINTS,
    SCENE_RECENT_ACTIONS,
    SCENE_ROUTE_HINTS,
    SCENE_STORAGE_HINTS,
    SCENE_TIMER_ACTIONS,
    SCENE_TIMER_ROUTE_HINTS,
    SCENE_WHITE_BRIGHTNESS_ANCHORS,
)
from custom_components.uniled.core.sp630e import (  # noqa: E402
    SP630E_APK_ASSET_EVIDENCE,
    SP630E_APP_METHOD_HINTS,
    SP630E_DATA_MODEL_HINTS,
    SP630E_FAVORITE_LIMIT_HINTS,
    SP630E_NATIVE_EXPORT_DETAIL_ANCHORS,
    SP630E_NATIVE_EXPORT_SYMBOLS,
    SP630E_NATIVE_LFX_HINTS,
    SP630E_NETWORK_HINTS,
    SP630E_PACKAGE,
    SP630E_PACKAGE_ASSET_COUNT,
    SP630E_REMOTE_HINTS,
    SP630E_ROUTE_HINTS,
    SP630E_TIMER_HINTS,
)
from custom_components.uniled.core.transports.ble import (  # noqa: E402
    APK_BLE_NOTIFICATION_STRING_HINTS,
    APK_BLE_PLUGIN_CONTRACT_STRING_HINTS,
    APK_BLE_UUID_STRING_HINTS,
)
from custom_components.uniled.core.transports.lan import (  # noqa: E402
    APK_DISCOVERY_STATUS_HINTS,
    APK_NETWORK_CLOUD_SETUP_PROMPTS,
    APK_NETWORK_SETUP_PROMPTS,
    APK_NETWORK_SETUP_ROUTE_HINTS,
    APK_RAW_SOCKET_HINTS,
    MODULE_HOME_PACKAGE,
    MODULE_HOME_PACKAGE_ASSET_COUNT,
    SP801E_NETWORK_SETUP_GUIDE_ASSETS,
)
from custom_components.uniled.core.transports.mesh import (  # noqa: E402
    APK_SIG_MESH_UUID_STRING_EVIDENCE,
    RG4_ACCESSORIES_PACKAGE,
    RG4_ACCESSORIES_PACKAGE_ASSET_COUNT,
    RG4_APK_ASSET_EVIDENCE,
    RG4_EXACT_PROVISIONING_STRING_HINTS,
    RG4_PROVISIONING_STATE_HINTS,
    RG4_ROUTE_HINTS,
    SCENE_MESH_PROVISIONING_HINTS,
)
from scripts.generate_catalog import catalog_rows_from_csv  # noqa: E402
from scripts.inspect_elf_exports import (  # noqa: E402
    read_symbol_bytes,
    read_symbol_tables,
)

DEFAULT_ANALYSIS_DIR = (
    REPO_ROOT.parent / ".codex" / "rev" / "BanlanX_3.3.1-analysis"
)
DEFAULT_BLUTTER_DIR = (
    REPO_ROOT.parent / ".codex" / "rev" / "BanlanX_3.3.1-blutter-arm64"
)
DEFAULT_BUNDLED_CATALOG_PATH = (
    REPO_ROOT
    / "custom_components"
    / "uniled"
    / "core"
    / "catalog"
    / "models.json"
)

BLUTTER_HJ_ENUM_PATTERN = re.compile(
    r"Obj!HJ@[^\n]*:\s*\{\s*"
    r"Super!_Enum\s*:\s*\{\s*"
    r"off_8:\s*int\((0x[0-9a-fA-F]+|\d+)\),\s*"
    r"off_10:\s*\"([^\"]+)\"\s*"
    r"\},\s*"
    r"off_14:\s*int\((0x[0-9a-fA-F]+|\d+)\)",
    re.MULTILINE,
)

DEFAULT_SCENE_NATIVE_LIB_CANDIDATES = (
    REPO_ROOT.parent
    / ".codex"
    / "rev"
    / "BanlanX_3.3.1-extracted"
    / "config.armeabi_v7a-apk"
    / "lib"
    / "armeabi-v7a"
    / "libscene_lfx.so",
    REPO_ROOT.parent
    / ".codex"
    / "rev"
    / "BanlanX_3.3.1-decompiled"
    / "config.armeabi_v7a"
    / "resources"
    / "lib"
    / "armeabi-v7a"
    / "libscene_lfx.so",
)

DEFAULT_SP802E_NATIVE_LIB_CANDIDATES = (
    REPO_ROOT.parent
    / ".codex"
    / "rev"
    / "BanlanX_3.3.1-extracted"
    / "config.armeabi_v7a-apk"
    / "lib"
    / "armeabi-v7a"
    / "libwled_lfx.so",
    REPO_ROOT.parent
    / ".codex"
    / "rev"
    / "BanlanX_3.3.1-decompiled"
    / "config.armeabi_v7a"
    / "resources"
    / "lib"
    / "armeabi-v7a"
    / "libwled_lfx.so",
)

DEFAULT_SP630E_NATIVE_LIB_CANDIDATES = (
    REPO_ROOT.parent
    / ".codex"
    / "rev"
    / "BanlanX_3.3.1-extracted"
    / "config.armeabi_v7a-apk"
    / "lib"
    / "armeabi-v7a"
    / "liblfx.so",
    REPO_ROOT.parent
    / ".codex"
    / "rev"
    / "BanlanX_3.3.1-decompiled"
    / "config.armeabi_v7a"
    / "resources"
    / "lib"
    / "armeabi-v7a"
    / "liblfx.so",
)


@dataclass(frozen=True, slots=True)
class EvidenceSpec:
    """One profile package to audit."""

    name: str
    package: str
    expected_package_count: int
    curated_assets: tuple[str, ...]
    curated_strings: tuple[str, ...] = ()

    @property
    def package_key(self) -> str:
        """Return the asset-package-count key used by the analysis file."""
        return self.package.rsplit("/", 1)[-1]

    @property
    def asset_file_name(self) -> str:
        """Return the analysis asset-list file name for this package."""
        return f"assets_{self.package_key}.txt"


@dataclass(frozen=True, slots=True)
class StringEvidenceSpec:
    """One non-package raw-string evidence group to audit."""

    name: str
    curated_strings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuditFailure:
    """One evidence mismatch."""

    name: str
    message: str


@dataclass(frozen=True, slots=True)
class NonCatalogFeaturePackageSpec:
    """One APK feature package that is not a catalog device family."""

    name: str
    package_key: str
    expected_package_count: int
    required_assets: tuple[str, ...]
    required_strings: tuple[str, ...]
    forbidden_catalog_terms: tuple[str, ...]

    @property
    def asset_file_name(self) -> str:
        """Return the analysis asset-list file name for this package."""
        return f"assets_{self.package_key}.txt"


EVIDENCE_SPECS = (
    EvidenceSpec(
        "sp630e",
        SP630E_PACKAGE,
        SP630E_PACKAGE_ASSET_COUNT,
        SP630E_APK_ASSET_EVIDENCE,
        (
            *SP630E_ROUTE_HINTS,
            *SP630E_FAVORITE_LIMIT_HINTS,
            *SP630E_TIMER_HINTS,
            *(
                hint
                for hint in SP630E_NETWORK_HINTS
                if not hint.startswith(f"{SP630E_PACKAGE}/")
            ),
            *(
                hint
                for hint in SP630E_REMOTE_HINTS
                if not hint.startswith(f"{SP630E_PACKAGE}/")
            ),
            *SP630E_APP_METHOD_HINTS,
            *SP630E_DATA_MODEL_HINTS,
            *SP630E_NATIVE_LFX_HINTS,
        ),
    ),
    EvidenceSpec(
        "scene_ui",
        SCENE_PACKAGE,
        SCENE_PACKAGE_ASSET_COUNT,
        SCENE_APK_ASSET_EVIDENCE,
        (
            *SCENE_ROUTE_HINTS,
            *SCENE_LFX_ROUTE_HINTS,
            *SCENE_TIMER_ROUTE_HINTS,
            *SCENE_APP_METHOD_HINTS,
            *SCENE_STORAGE_HINTS,
            *SCENE_RECENT_ACTIONS,
            *SCENE_FAVORITE_ACTIONS,
            *SCENE_TIMER_ACTIONS,
            *SCENE_DIY_ACTIONS,
            *SCENE_WHITE_BRIGHTNESS_ANCHORS,
            *SCENE_RAW_STRING_HINTS,
            *SCENE_LFX_DATA_MODEL_HINTS,
            *SCENE_LFX_FRAME_FIELD_HINTS,
            *SCENE_NATIVE_HANDLER_HINTS,
            *SCENE_NATIVE_FRAME_HINTS,
            *SCENE_NATIVE_OPCODE_HINTS,
            *SCENE_NATIVE_STATE_HINTS,
            *SCENE_NATIVE_COLOR_ORDER_HINTS,
            *SCENE_NATIVE_PWM_TABLE_HINTS,
            *SCENE_NATIVE_MUSIC_EFFECT_HINTS,
            *SCENE_NATIVE_PWM_DRIVER_HINTS,
            *(anchor.split("@", 1)[0] for anchor in SCENE_NATIVE_ANIMATION_EXPORTS),
            *(anchor.split("@", 1)[0] for anchor in SCENE_NATIVE_DRIVE_EXPORTS),
            *SCENE_NATIVE_PERSISTENCE_HANDLERS,
            *(
                hint
                for hint in SCENE_NATIVE_LIBRARY_HINTS
                if hint != "libscene_lfx.so"
            ),
        ),
    ),
    EvidenceSpec(
        "module_sp801e",
        SP801E_PACKAGE,
        SP801E_PACKAGE_ASSET_COUNT,
        SP801E_APK_ASSET_EVIDENCE,
        (
            *SP801E_ROUTE_HINTS,
            *SP801E_ARTNET_FIELDS,
            *SP801E_PORT_FIELDS,
            *SP801E_PLAYLIST_ACTIONS,
            *SP801E_APP_METHOD_HINTS,
            *SP801E_RAW_STRING_HINTS,
        ),
    ),
    EvidenceSpec(
        "module_home_network_setup",
        MODULE_HOME_PACKAGE,
        MODULE_HOME_PACKAGE_ASSET_COUNT,
        SP801E_NETWORK_SETUP_GUIDE_ASSETS,
    ),
    EvidenceSpec(
        "sp802e",
        SP802E_PACKAGE,
        SP802E_PACKAGE_ASSET_COUNT,
        SP802E_APK_ASSET_EVIDENCE,
        (
            *SP802E_ROUTE_HINTS,
            *SP802E_MATRIX_MUSIC_CONTROLS,
            *SP802E_APP_METHOD_HINTS,
            *SP802E_RAW_STRING_HINTS,
            *SP802E_NATIVE_FRAME_HINTS,
            *SP802E_NATIVE_LFX_PARAM_HINTS,
            *SP802E_NATIVE_EFFECT_GENERATOR_HINTS,
            *SP802E_NATIVE_MATRIX_MODE_HINTS,
            *SP802E_NATIVE_PIXEL_HELPER_HINTS,
            *(
                hint
                for hint in SP802E_NATIVE_LIBRARY_HINTS
                if hint != "libwled_lfx.so"
            ),
        ),
    ),
    EvidenceSpec(
        "car_lights",
        CAR_LIGHT_PACKAGE,
        CAR_LIGHT_PACKAGE_ASSET_COUNT,
        CAR_LIGHT_APK_ASSET_EVIDENCE,
        (
            *CAR_LIGHT_ROUTE_HINTS,
            *CAR_LIGHT_SUBDEVICE_HINTS,
            *CAR_LIGHT_SUBDEVICE_FILTERS,
            *CAR_LIGHT_PASSWORD_HINTS,
            *CAR_LIGHT_PASSWORD_FLOW_STATES,
            *CAR_LIGHT_PASSWORD_ENTRY_HINTS,
            *CAR_LIGHT_PASSWORD_POLICY_HINTS,
            *CAR_LIGHT_PASSWORD_RESET_HINTS,
            *CAR_LIGHT_TRIGGER_STORAGE_HINTS,
            *CAR_LIGHT_TRIGGER_ACTIONS,
            *CAR_LIGHT_SETUP_REQUIREMENTS,
            *CAR_LIGHT_SETUP_FLOW_HINTS,
            *CAR_LIGHT_SETUP_KEY_HINTS,
        ),
    ),
    EvidenceSpec(
        "fish_tank_lights",
        FISH_TANK_PACKAGE,
        FISH_TANK_PACKAGE_ASSET_COUNT,
        FISH_TANK_APK_ASSET_EVIDENCE,
        (
            *FISH_TANK_ROUTE_HINTS,
            *FISH_TANK_APP_METHOD_HINTS,
            *FISH_TANK_FAVORITE_ACTION_HINTS,
            *FISH_TANK_FAVORITE_SERVICE_HINTS,
            *FISH_TANK_FAVORITE_STORAGE_HINTS,
            *FISH_TANK_TIMER_HINTS,
            *FISH_TANK_TIMER_STORAGE_HINTS,
            *FISH_TANK_BRIGHTNESS_STATE_HINTS,
            *FISH_TANK_RAW_STRING_HINTS,
        ),
    ),
    EvidenceSpec(
        "accessories",
        RG4_ACCESSORIES_PACKAGE,
        RG4_ACCESSORIES_PACKAGE_ASSET_COUNT,
        RG4_APK_ASSET_EVIDENCE,
        (
            *RG4_ROUTE_HINTS,
            *RG4_EXACT_PROVISIONING_STRING_HINTS,
            *RG4_PROVISIONING_STATE_HINTS,
        ),
    ),
)

BANLANX_CLOUD_AUDITED_STRING_HINTS = tuple(
    dict.fromkeys(
        (
            *BANLANX_CLOUD_RAW_STRING_HINTS,
            *(endpoint.path for endpoint in BANLANX_CLOUD_ENDPOINT_INVENTORY),
        )
    )
)


STRING_EVIDENCE_SPECS = (
    StringEvidenceSpec(
        "cloud",
        BANLANX_CLOUD_AUDITED_STRING_HINTS,
    ),
    StringEvidenceSpec(
        "lan_network_setup",
        (
            *APK_NETWORK_SETUP_ROUTE_HINTS,
            *APK_NETWORK_SETUP_PROMPTS,
            *APK_NETWORK_CLOUD_SETUP_PROMPTS,
            *APK_RAW_SOCKET_HINTS,
            *APK_DISCOVERY_STATUS_HINTS,
        ),
    ),
    StringEvidenceSpec(
        "ble_uuid_inventory",
        APK_BLE_UUID_STRING_HINTS,
    ),
    StringEvidenceSpec(
        "ble_plugin_contract",
        APK_BLE_PLUGIN_CONTRACT_STRING_HINTS,
    ),
    StringEvidenceSpec(
        "ble_notification_contract",
        APK_BLE_NOTIFICATION_STRING_HINTS,
    ),
    StringEvidenceSpec(
        "scene_mesh_provisioning",
        SCENE_MESH_PROVISIONING_HINTS,
    ),
    StringEvidenceSpec(
        "rg4_provisioning",
        RG4_EXACT_PROVISIONING_STRING_HINTS,
    ),
    StringEvidenceSpec(
        "sig_mesh_uuid",
        APK_SIG_MESH_UUID_STRING_EVIDENCE,
    ),
)

NON_CATALOG_FEATURE_PACKAGE_SPECS = tuple(
    NonCatalogFeaturePackageSpec(
        profile.name,
        profile.package_key,
        profile.package_asset_count,
        profile.required_assets,
        (*profile.route_hints, *profile.storage_hints),
        profile.catalog_absent_terms,
    )
    for profile in NON_CATALOG_FEATURE_PACKAGE_PROFILES
)


def parse_package_counts(path: Path) -> dict[str, int]:
    """Parse asset package counts produced during APK analysis."""
    counts: dict[str, int] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"{path}:{line_number}: expected '<count> <package>'")
        counts[parts[1]] = int(parts[0])
    return counts


def read_asset_list(path: Path) -> frozenset[str]:
    """Read one analysis asset-list file."""
    return frozenset(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def parse_blutter_app_command_ids(text: str) -> dict[str, tuple[int, int]]:
    """Return Blutter HJ enum rows as name -> (ordinal, app command ID)."""
    return {
        name: (int(ordinal, 0), int(command_id, 0))
        for ordinal, name, command_id in BLUTTER_HJ_ENUM_PATTERN.findall(text)
    }


def audit_blutter_app_command_ids(blutter_dir: Path) -> list[AuditFailure]:
    """Verify recovered app-command enum IDs against a local Blutter dump."""
    objs_path = blutter_dir.resolve() / "objs.txt"
    if not objs_path.exists():
        return [
            AuditFailure(
                "blutter_app_command_ids",
                f"missing {objs_path}",
            )
        ]

    recovered = parse_blutter_app_command_ids(
        objs_path.read_text(encoding="utf-8", errors="ignore")
    )
    expected = {
        hint.name: (hint.ordinal, hint.command_id)
        for hint in BANLANX_APP_COMMAND_ID_HINTS
    }
    failures: list[AuditFailure] = []

    if len(recovered) != len(expected):
        failures.append(
            AuditFailure(
                "blutter_app_command_ids",
                f"recovered {len(recovered)} HJ enum IDs, expected {len(expected)}",
            )
        )

    missing = tuple(name for name in expected if name not in recovered)
    if missing:
        failures.append(
            AuditFailure(
                "blutter_app_command_ids",
                f"{len(missing)} expected IDs are absent: {', '.join(missing[:8])}",
            )
        )

    unexpected = tuple(name for name in recovered if name not in expected)
    if unexpected:
        failures.append(
            AuditFailure(
                "blutter_app_command_ids",
                (
                    f"{len(unexpected)} unexpected HJ enum IDs were recovered: "
                    f"{', '.join(unexpected[:8])}"
                ),
            )
        )

    mismatched = tuple(
        f"{name}: recovered={recovered[name]!r} expected={expected[name]!r}"
        for name in expected.keys() & recovered.keys()
        if recovered[name] != expected[name]
    )
    if mismatched:
        failures.append(
            AuditFailure(
                "blutter_app_command_ids",
                (
                    f"{len(mismatched)} app command IDs changed: "
                    f"{'; '.join(mismatched[:5])}"
                ),
            )
        )

    return failures


def audit_bundled_catalog_source(
    analysis_dir: Path,
    catalog_path: Path = DEFAULT_BUNDLED_CATALOG_PATH,
) -> list[AuditFailure]:
    """Verify bundled catalog rows still match the APK-derived CSV source."""
    source_path = analysis_dir / "model_catalog.csv"
    if not source_path.exists():
        return [AuditFailure("catalog_source", f"missing {source_path.name}")]
    if not catalog_path.exists():
        return [AuditFailure("catalog_source", f"missing {catalog_path.name}")]

    expected_rows = catalog_rows_from_csv(source_path)
    actual_rows = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(actual_rows, list):
        return [AuditFailure("catalog_source", f"{catalog_path.name} is not a list")]
    if actual_rows == expected_rows:
        return []

    failures: list[AuditFailure] = []
    if len(actual_rows) != len(expected_rows):
        failures.append(
            AuditFailure(
                "catalog_source",
                (
                    f"{catalog_path.name} has {len(actual_rows)} rows, "
                    f"expected {len(expected_rows)} from model_catalog.csv"
                ),
            )
        )

    actual_by_id = _catalog_rows_by_model_id(actual_rows)
    expected_by_id = _catalog_rows_by_model_id(expected_rows)
    missing = tuple(
        _catalog_row_label(expected_by_id[model_id])
        for model_id in sorted(set(expected_by_id) - set(actual_by_id))
    )
    unexpected = tuple(
        _catalog_row_label(actual_by_id[model_id])
        for model_id in sorted(set(actual_by_id) - set(expected_by_id))
    )
    if missing:
        failures.append(
            AuditFailure(
                "catalog_source",
                f"missing catalog rows: {', '.join(missing[:5])}",
            )
        )
    if unexpected:
        failures.append(
            AuditFailure(
                "catalog_source",
                f"unexpected catalog rows: {', '.join(unexpected[:5])}",
            )
        )

    changed: list[str] = []
    for model_id in sorted(set(actual_by_id) & set(expected_by_id)):
        actual = actual_by_id[model_id]
        expected = expected_by_id[model_id]
        if actual == expected:
            continue
        fields = tuple(
            field
            for field in sorted(set(actual) | set(expected))
            if actual.get(field) != expected.get(field)
        )
        changed.append(f"{_catalog_row_label(expected)} fields={','.join(fields)}")
        if len(changed) == 5:
            break
    if changed:
        failures.append(
            AuditFailure(
                "catalog_source",
                f"changed catalog rows: {'; '.join(changed)}",
            )
        )

    return failures or [
        AuditFailure("catalog_source", f"{catalog_path.name} differs from APK CSV")
    ]


def _catalog_rows_by_model_id(rows: object) -> dict[int, dict[str, object]]:
    """Return catalog rows keyed by model ID for audit messages."""
    by_model_id: dict[int, dict[str, object]] = {}
    if not isinstance(rows, list):
        return by_model_id
    for row in rows:
        if not isinstance(row, dict) or "model_id" not in row:
            continue
        by_model_id[int(row["model_id"])] = row
    return by_model_id


def _catalog_row_label(row: Mapping[str, object]) -> str:
    """Return a compact catalog row label for audit messages."""
    return f"{row.get('model_id')}:{row.get('name')}"


def _read_required_texts(
    paths: Iterable[Path],
    *,
    failures: list[AuditFailure],
    failure_name: str,
) -> str:
    text_parts: list[str] = []
    for path in paths:
        if not path.exists():
            failures.append(AuditFailure(failure_name, f"missing {path.name}"))
            continue
        text_parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(text_parts)


def _string_evidence_values(text: str) -> frozenset[str]:
    """Return exact recovered strings, including values from native ledgers."""
    values: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        values.add(stripped)
        if ": " in stripped:
            values.add(stripped.split(": ", 1)[1])
    return frozenset(values)


SCENE_NATIVE_DYNSYM_COUNT = 378
SP802E_NATIVE_DYNSYM_COUNT = 186
SP630E_NATIVE_DYNSYM_COUNT = 162


def default_scene_native_lib_path() -> Path | None:
    """Return the first local scene native library candidate, if present."""
    for candidate in DEFAULT_SCENE_NATIVE_LIB_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def default_sp802e_native_lib_path() -> Path | None:
    """Return the first local SP802E native library candidate, if present."""
    for candidate in DEFAULT_SP802E_NATIVE_LIB_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def default_sp630e_native_lib_path() -> Path | None:
    """Return the first local SP630E/shared LFX native library candidate."""
    for candidate in DEFAULT_SP630E_NATIVE_LIB_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def default_blutter_dir_path() -> Path | None:
    """Return the local Blutter output directory, if present."""
    if (DEFAULT_BLUTTER_DIR / "objs.txt").exists():
        return DEFAULT_BLUTTER_DIR
    return None


def audit_scene_native_exports(scene_native_lib: Path) -> list[AuditFailure]:
    """Return mismatches between scene native constants and an ELF library."""
    try:
        tables = read_symbol_tables(scene_native_lib)
    except (OSError, ValueError) as err:
        return [
            AuditFailure(
                "scene_native_exports",
                f"could not inspect {scene_native_lib}: {err}",
            )
        ]

    dynsym = next((table for table in tables if table.table_name == ".dynsym"), None)
    if dynsym is None:
        return [
            AuditFailure(
                "scene_native_exports",
                f"{scene_native_lib} does not expose .dynsym",
            )
        ]
    symbols = {symbol.name: (symbol.value, symbol.size) for symbol in dynsym.symbols}
    return audit_scene_native_export_symbols(
        symbols,
        dynsym_count=len(dynsym.symbols),
    )


def audit_scene_native_code_anchors(scene_native_lib: Path) -> list[AuditFailure]:
    """Return mismatches between scene native code anchors and an ELF library."""
    try:
        symbol_bytes = read_symbol_bytes(
            scene_native_lib,
            tuple(name for name, *_rest in SCENE_NATIVE_CODE_ANCHORS),
        )
    except (OSError, ValueError) as err:
        return [
            AuditFailure(
                "scene_native_code_anchors",
                f"could not inspect {scene_native_lib}: {err}",
            )
        ]

    values = {
        name: (
            body.symbol.value,
            body.symbol.size,
            body.thumb_entry,
            body.section.name,
            body.sha256_hex,
            body.first_hex(16),
            body.last_hex(16),
        )
        for name, body in symbol_bytes.items()
    }
    return audit_scene_native_code_anchor_values(values)


def audit_scene_native_code_anchor_values(
    values: Mapping[str, tuple[int, int, bool, str, str, str, str]],
) -> list[AuditFailure]:
    """Return mismatches between scene native code constants and parsed bytes."""
    failures: list[AuditFailure] = []
    for (
        name,
        expected_value,
        expected_size,
        expected_sha256,
        expected_first16,
        expected_last16,
    ) in SCENE_NATIVE_CODE_ANCHORS:
        actual = values.get(name)
        if actual is None:
            failures.append(
                AuditFailure(
                    "scene_native_code_anchors",
                    f"{name} code anchor is absent",
                )
            )
            continue
        (
            actual_value,
            actual_size,
            actual_thumb,
            actual_section,
            actual_sha256,
            actual_first16,
            actual_last16,
        ) = actual
        if (actual_value, actual_size) != (expected_value, expected_size):
            failures.append(
                AuditFailure(
                    "scene_native_code_anchors",
                    (
                        f"{name} export is {actual_value:#010x}/{actual_size}, "
                        f"expected {expected_value:#010x}/{expected_size}"
                    ),
                )
            )
        if actual_thumb is not True or actual_section != ".text":
            failures.append(
                AuditFailure(
                    "scene_native_code_anchors",
                    (
                        f"{name} maps to thumb={actual_thumb}, "
                        f"section={actual_section}; expected thumb=True, "
                        "section=.text"
                    ),
                )
            )
        if actual_sha256 != expected_sha256:
            failures.append(
                AuditFailure(
                    "scene_native_code_anchors",
                    (
                        f"{name} SHA-256 is {actual_sha256}, "
                        f"expected {expected_sha256}"
                    ),
                )
            )
        if actual_first16 != expected_first16:
            failures.append(
                AuditFailure(
                    "scene_native_code_anchors",
                    (
                        f"{name} first16 is {actual_first16}, "
                        f"expected {expected_first16}"
                    ),
                )
            )
        if actual_last16 != expected_last16:
            failures.append(
                AuditFailure(
                    "scene_native_code_anchors",
                    (
                        f"{name} last16 is {actual_last16}, "
                        f"expected {expected_last16}"
                    ),
                )
            )
    return failures


def audit_scene_native_export_symbols(
    symbols: Mapping[str, tuple[int, int]],
    *,
    dynsym_count: int | None = None,
) -> list[AuditFailure]:
    """Return mismatches between scene native constants and parsed symbols."""
    failures: list[AuditFailure] = []
    if dynsym_count is not None and dynsym_count != SCENE_NATIVE_DYNSYM_COUNT:
        failures.append(
            AuditFailure(
                "scene_native_exports",
                (
                    f".dynsym has {dynsym_count} named symbols, "
                    f"expected {SCENE_NATIVE_DYNSYM_COUNT}"
                ),
            )
        )

    expected_symbols = {
        *(
            handler
            for _capability, ic_handler, pwm_handler in (
                SCENE_NATIVE_PAIRED_API_HANDLER_PAIRS
            )
            for handler in (ic_handler, pwm_handler)
        ),
        *(handler for _capability, handler in SCENE_NATIVE_IC_ONLY_API_HANDLERS),
        *SCENE_NATIVE_LOOP_HANDLERS,
        *(anchor.split("@", 1)[0] for anchor in SCENE_NATIVE_ANIMATION_EXPORTS),
        *(anchor.split("@", 1)[0] for anchor in SCENE_NATIVE_DRIVE_EXPORTS),
        *(anchor.split("@", 1)[0] for anchor in SCENE_NATIVE_STATE_EXPORTS),
        *(export.symbol for export in SCENE_NATIVE_PERSISTENCE_EXPORTS),
    }
    missing_symbols = tuple(
        symbol for symbol in sorted(expected_symbols) if symbol not in symbols
    )
    if missing_symbols:
        failures.append(
            AuditFailure(
                "scene_native_exports",
                (
                    f"{len(missing_symbols)} expected native symbols are absent: "
                    f"{', '.join(missing_symbols[:5])}"
                ),
            )
        )

    for anchor in (
        *SCENE_NATIVE_STATE_EXPORTS,
        *SCENE_NATIVE_ANIMATION_EXPORTS,
        *SCENE_NATIVE_DRIVE_EXPORTS,
    ):
        name, expected_value, expected_size = _parse_native_export_anchor(anchor)
        actual = symbols.get(name)
        if actual is None:
            continue
        if actual != (expected_value, expected_size):
            failures.append(
                AuditFailure(
                    "scene_native_exports",
                    (
                        f"{name} export is {actual[0]:#010x}/{actual[1]}, "
                        f"expected {expected_value:#010x}/{expected_size}"
                    ),
                )
            )
    for export in SCENE_NATIVE_PERSISTENCE_EXPORTS:
        actual = symbols.get(export.symbol)
        if actual is None:
            continue
        if actual != (export.value, export.size):
            failures.append(
                AuditFailure(
                    "scene_native_exports",
                    (
                        f"{export.symbol} export is {actual[0]:#010x}/{actual[1]}, "
                        f"expected {export.value:#010x}/{export.size}"
                    ),
                )
            )
    return failures


def _parse_native_export_anchor(anchor: str) -> tuple[str, int, int]:
    name, address_and_size = anchor.split("@", 1)
    address, size = address_and_size.split("/", 1)
    return name, int(address, 16), int(size)


def audit_sp802e_native_exports(sp802e_native_lib: Path) -> list[AuditFailure]:
    """Return mismatches between SP802E native constants and an ELF library."""
    try:
        tables = read_symbol_tables(sp802e_native_lib)
    except (OSError, ValueError) as err:
        return [
            AuditFailure(
                "sp802e_native_exports",
                f"could not inspect {sp802e_native_lib}: {err}",
            )
        ]

    dynsym = next((table for table in tables if table.table_name == ".dynsym"), None)
    if dynsym is None:
        return [
            AuditFailure(
                "sp802e_native_exports",
                f"{sp802e_native_lib} does not expose .dynsym",
            )
        ]
    symbols = {symbol.name: (symbol.value, symbol.size) for symbol in dynsym.symbols}
    return audit_sp802e_native_export_symbols(
        symbols,
        dynsym_count=len(dynsym.symbols),
    )


def audit_sp802e_native_export_symbols(
    symbols: Mapping[str, tuple[int, int]],
    *,
    dynsym_count: int | None = None,
) -> list[AuditFailure]:
    """Return mismatches between SP802E native constants and parsed symbols."""
    failures: list[AuditFailure] = []
    if dynsym_count is not None and dynsym_count != SP802E_NATIVE_DYNSYM_COUNT:
        failures.append(
            AuditFailure(
                "sp802e_native_exports",
                (
                    f".dynsym has {dynsym_count} named symbols, "
                    f"expected {SP802E_NATIVE_DYNSYM_COUNT}"
                ),
            )
        )

    missing_symbols = tuple(
        symbol
        for symbol in sorted(SP802E_NATIVE_EXPORT_SYMBOLS)
        if symbol not in symbols
    )
    if missing_symbols:
        failures.append(
            AuditFailure(
                "sp802e_native_exports",
                (
                    f"{len(missing_symbols)} expected native symbols are absent: "
                    f"{', '.join(missing_symbols[:5])}"
                ),
            )
        )

    for name, expected_value, expected_size in SP802E_NATIVE_EXPORT_DETAIL_ANCHORS:
        actual = symbols.get(name)
        if actual is None:
            continue
        if actual != (expected_value, expected_size):
            failures.append(
                AuditFailure(
                    "sp802e_native_exports",
                    (
                        f"{name} export is {actual[0]:#010x}/{actual[1]}, "
                        f"expected {expected_value:#010x}/{expected_size}"
                    ),
                )
            )
    return failures


def audit_sp630e_native_exports(sp630e_native_lib: Path) -> list[AuditFailure]:
    """Return mismatches between SP630E native constants and an ELF library."""
    try:
        tables = read_symbol_tables(sp630e_native_lib)
    except (OSError, ValueError) as err:
        return [
            AuditFailure(
                "sp630e_native_exports",
                f"could not inspect {sp630e_native_lib}: {err}",
            )
        ]

    dynsym = next((table for table in tables if table.table_name == ".dynsym"), None)
    if dynsym is None:
        return [
            AuditFailure(
                "sp630e_native_exports",
                f"{sp630e_native_lib} does not expose .dynsym",
            )
        ]
    symbols = {symbol.name: (symbol.value, symbol.size) for symbol in dynsym.symbols}
    return audit_sp630e_native_export_symbols(
        symbols,
        dynsym_count=len(dynsym.symbols),
    )


def audit_sp630e_native_export_symbols(
    symbols: Mapping[str, tuple[int, int]],
    *,
    dynsym_count: int | None = None,
) -> list[AuditFailure]:
    """Return mismatches between SP630E native constants and parsed symbols."""
    failures: list[AuditFailure] = []
    if dynsym_count is not None and dynsym_count != SP630E_NATIVE_DYNSYM_COUNT:
        failures.append(
            AuditFailure(
                "sp630e_native_exports",
                (
                    f".dynsym has {dynsym_count} named symbols, "
                    f"expected {SP630E_NATIVE_DYNSYM_COUNT}"
                ),
            )
        )

    missing_symbols = tuple(
        symbol
        for symbol in sorted(SP630E_NATIVE_EXPORT_SYMBOLS)
        if symbol not in symbols
    )
    if missing_symbols:
        failures.append(
            AuditFailure(
                "sp630e_native_exports",
                (
                    f"{len(missing_symbols)} expected native symbols are absent: "
                    f"{', '.join(missing_symbols[:5])}"
                ),
            )
        )

    for name, expected_value, expected_size in SP630E_NATIVE_EXPORT_DETAIL_ANCHORS:
        actual = symbols.get(name)
        if actual is None:
            continue
        if actual != (expected_value, expected_size):
            failures.append(
                AuditFailure(
                    "sp630e_native_exports",
                    (
                        f"{name} export is {actual[0]:#010x}/{actual[1]}, "
                        f"expected {expected_value:#010x}/{expected_size}"
                    ),
                )
            )
    return failures


def _audit_asset_package_inventory(
    analysis_dir: Path,
    counts: dict[str, int],
    profiles: Iterable[APKAssetPackageProfile],
    *,
    covered_package_keys: set[str],
) -> list[AuditFailure]:
    """Verify that every APK asset package is classified exactly once."""
    profiles = tuple(profiles)
    failures: list[AuditFailure] = []
    expected_keys = {profile.key for profile in profiles}
    actual_keys = set(counts)
    duplicate_keys = sorted(
        key
        for key in expected_keys
        if sum(profile.key == key for profile in profiles) > 1
    )
    if duplicate_keys:
        failures.append(
            AuditFailure(
                "asset_package_inventory",
                f"duplicate classified package keys: {', '.join(duplicate_keys)}",
            )
        )

    missing_keys = sorted(expected_keys - actual_keys)
    if missing_keys:
        failures.append(
            AuditFailure(
                "asset_package_inventory",
                f"missing classified package keys: {', '.join(missing_keys)}",
            )
        )
    unexpected_keys = sorted(actual_keys - expected_keys)
    if unexpected_keys:
        failures.append(
            AuditFailure(
                "asset_package_inventory",
                f"unclassified APK package keys: {', '.join(unexpected_keys)}",
            )
        )

    for profile in profiles:
        if profile.key in covered_package_keys:
            continue
        actual_count = counts.get(profile.key)
        if actual_count != profile.expected_asset_count:
            failures.append(
                AuditFailure(
                    "asset_package_inventory",
                    (
                        f"package count for {profile.key} is {actual_count!r}, "
                        f"expected {profile.expected_asset_count}"
                    ),
                )
            )

        asset_path = analysis_dir / profile.asset_file_name
        if not asset_path.exists():
            failures.append(
                AuditFailure(
                    "asset_package_inventory",
                    f"missing {profile.asset_file_name}",
                )
            )
            continue
        assets = read_asset_list(asset_path)
        if len(assets) != profile.expected_asset_count:
            failures.append(
                AuditFailure(
                    "asset_package_inventory",
                    (
                        f"{profile.asset_file_name} has {len(assets)} assets, "
                        f"expected {profile.expected_asset_count}"
                    ),
                )
            )
        missing_assets = tuple(
            asset for asset in profile.representative_assets if asset not in assets
        )
        if missing_assets:
            failures.append(
                AuditFailure(
                    "asset_package_inventory",
                    (
                        f"{len(missing_assets)} representative assets for "
                        f"{profile.key} are absent: {', '.join(missing_assets)}"
                    ),
                )
            )
    return failures


def audit_analysis_dir(
    analysis_dir: Path,
    specs: Iterable[EvidenceSpec] = EVIDENCE_SPECS,
    string_specs: Iterable[StringEvidenceSpec] = STRING_EVIDENCE_SPECS,
    non_catalog_package_specs: Iterable[NonCatalogFeaturePackageSpec] = (
        NON_CATALOG_FEATURE_PACKAGE_SPECS
    ),
    asset_package_profiles: Iterable[APKAssetPackageProfile] = (
        APK_ASSET_PACKAGE_PROFILES
    ),
    catalog_path: Path = DEFAULT_BUNDLED_CATALOG_PATH,
    require_catalog_source: bool = False,
) -> list[AuditFailure]:
    """Return all mismatches between profile constants and analysis files."""
    analysis_dir = analysis_dir.resolve()
    specs = tuple(specs)
    string_specs = tuple(string_specs)
    non_catalog_package_specs = tuple(non_catalog_package_specs)
    counts_path = analysis_dir / "asset_package_counts.txt"
    failures: list[AuditFailure] = []
    if not counts_path.exists():
        return [
            AuditFailure(
                "analysis",
                f"missing {counts_path}",
            )
        ]

    if require_catalog_source or (analysis_dir / "model_catalog.csv").exists():
        failures.extend(audit_bundled_catalog_source(analysis_dir, catalog_path))

    counts = parse_package_counts(counts_path)
    inventory_profiles = tuple(asset_package_profiles)
    covered_package_keys = {
        *(spec.package_key for spec in specs),
        *(spec.package_key for spec in non_catalog_package_specs),
    }
    failures.extend(
        _audit_asset_package_inventory(
            analysis_dir,
            counts,
            inventory_profiles,
            covered_package_keys=covered_package_keys,
        )
    )
    string_evidence = _read_required_texts(
        (
            analysis_dir / "libapp.strings.txt",
            analysis_dir / "libapp.interesting.txt",
            analysis_dir / "native.interesting.txt",
            analysis_dir / "libscene_lfx.strings.txt",
            analysis_dir / "libscene_lfx.interesting.txt",
            analysis_dir / "libwled_lfx.strings.txt",
            analysis_dir / "libwled_lfx.interesting.txt",
            analysis_dir / "liblfx.strings.txt",
            analysis_dir / "liblfx.interesting.txt",
        ),
        failures=failures,
            failure_name="analysis",
    )
    string_evidence_values = _string_evidence_values(string_evidence)
    for spec in specs:
        actual_count = counts.get(spec.package_key)
        if actual_count != spec.expected_package_count:
            failures.append(
                AuditFailure(
                    spec.name,
                    (
                        f"package count for {spec.package_key} is {actual_count!r}, "
                        f"expected {spec.expected_package_count}"
                    ),
                )
            )

        asset_path = analysis_dir / spec.asset_file_name
        if not asset_path.exists():
            failures.append(
                AuditFailure(spec.name, f"missing {asset_path.name}")
            )
            continue

        assets = read_asset_list(asset_path)
        if len(assets) != spec.expected_package_count:
            failures.append(
                AuditFailure(
                    spec.name,
                    (
                        f"{asset_path.name} has {len(assets)} assets, "
                        f"expected {spec.expected_package_count}"
                    ),
                )
            )
        missing = tuple(asset for asset in spec.curated_assets if asset not in assets)
        if missing:
            failures.append(
                AuditFailure(
                    spec.name,
                    (
                        f"{len(missing)} curated asset evidence paths are absent "
                        f"from {asset_path.name}: {', '.join(missing[:5])}"
                    ),
                )
            )
        missing_strings = tuple(
            string for string in spec.curated_strings if string not in string_evidence
        )
        if missing_strings:
            failures.append(
                AuditFailure(
                    spec.name,
                    (
                        f"{len(missing_strings)} curated string anchors are absent: "
                        f"{', '.join(missing_strings[:5])}"
                    ),
                )
            )
    for spec in string_specs:
        missing_strings = tuple(
            string
            for string in spec.curated_strings
            if string not in string_evidence_values
        )
        if missing_strings:
            failures.append(
                AuditFailure(
                    spec.name,
                    (
                        f"{len(missing_strings)} curated string anchors are absent: "
                        f"{', '.join(missing_strings[:5])}"
                    ),
                )
            )
    catalog_evidence = _read_required_texts(
        (
            analysis_dir / "model_catalog.pretty.json",
            analysis_dir / "model_catalog.raw.json",
        ),
        failures=failures,
        failure_name="analysis",
    ).casefold()

    for spec in non_catalog_package_specs:
        actual_count = counts.get(spec.package_key)
        if actual_count != spec.expected_package_count:
            failures.append(
                AuditFailure(
                    spec.name,
                    (
                        f"package count for {spec.package_key} is {actual_count!r}, "
                        f"expected {spec.expected_package_count}"
                    ),
                )
            )

        asset_path = analysis_dir / spec.asset_file_name
        if not asset_path.exists():
            failures.append(AuditFailure(spec.name, f"missing {asset_path.name}"))
            continue
        assets = read_asset_list(asset_path)
        if len(assets) != spec.expected_package_count:
            failures.append(
                AuditFailure(
                    spec.name,
                    (
                        f"{asset_path.name} has {len(assets)} assets, "
                        f"expected {spec.expected_package_count}"
                    ),
                )
            )
        missing_assets = tuple(
            asset for asset in spec.required_assets if asset not in assets
        )
        if missing_assets:
            failures.append(
                AuditFailure(
                    spec.name,
                    (
                        f"{len(missing_assets)} feature-package asset anchors are "
                        f"absent from {asset_path.name}: {', '.join(missing_assets)}"
                    ),
                )
            )

        missing_strings = tuple(
            string for string in spec.required_strings if string not in string_evidence
        )
        if missing_strings:
            failures.append(
                AuditFailure(
                    spec.name,
                    (
                        f"{len(missing_strings)} feature-package string anchors "
                        f"are absent: {', '.join(missing_strings)}"
                    ),
                )
            )

        catalog_hits = tuple(
            term for term in spec.forbidden_catalog_terms if term in catalog_evidence
        )
        if catalog_hits:
            failures.append(
                AuditFailure(
                    spec.name,
                    (
                        "feature package is no longer catalog-absent; found "
                        f"catalog terms: {', '.join(catalog_hits)}"
                    ),
                )
            )
    return failures


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify UniLED APK evidence constants against local BanlanX analysis "
            "artifacts."
        )
    )
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=DEFAULT_ANALYSIS_DIR,
        help=f"Analysis directory, default: {DEFAULT_ANALYSIS_DIR}",
    )
    parser.add_argument(
        "--scene-native-lib",
        type=Path,
        default=None,
        help=(
            "Optional path to libscene_lfx.so for native export auditing. "
            "When omitted, the local extracted APK path is used if present."
        ),
    )
    parser.add_argument(
        "--sp802e-native-lib",
        type=Path,
        default=None,
        help=(
            "Optional path to libwled_lfx.so for SP802E native export auditing. "
            "When omitted, the local extracted APK path is used if present."
        ),
    )
    parser.add_argument(
        "--sp630e-native-lib",
        type=Path,
        default=None,
        help=(
            "Optional path to liblfx.so for SP630E/shared LFX native export "
            "auditing. When omitted, the local extracted APK path is used "
            "if present."
        ),
    )
    parser.add_argument(
        "--blutter-dir",
        type=Path,
        default=None,
        help=(
            "Optional path to BanlanX Blutter output for app-command enum "
            "auditing. When omitted, the local Blutter path is used if present."
        ),
    )
    return parser


def main() -> int:
    """Run the evidence audit."""
    args = _parser().parse_args()
    analysis_dir = args.analysis_dir
    failures = audit_analysis_dir(analysis_dir, require_catalog_source=True)
    scene_native_lib = args.scene_native_lib or default_scene_native_lib_path()
    if scene_native_lib is not None:
        failures.extend(audit_scene_native_exports(scene_native_lib))
        failures.extend(audit_scene_native_code_anchors(scene_native_lib))
    sp802e_native_lib = args.sp802e_native_lib or default_sp802e_native_lib_path()
    if sp802e_native_lib is not None:
        failures.extend(audit_sp802e_native_exports(sp802e_native_lib))
    sp630e_native_lib = args.sp630e_native_lib or default_sp630e_native_lib_path()
    if sp630e_native_lib is not None:
        failures.extend(audit_sp630e_native_exports(sp630e_native_lib))
    blutter_dir = args.blutter_dir or default_blutter_dir_path()
    if blutter_dir is not None:
        failures.extend(audit_blutter_app_command_ids(blutter_dir))
    if failures:
        print(f"APK evidence audit failed for {analysis_dir}")
        for failure in failures:
            print(f"- {failure.name}: {failure.message}")
        return 1

    print(f"APK evidence audit passed for {analysis_dir}")
    for spec in EVIDENCE_SPECS:
        print(
            f"- {spec.name}: package_assets={spec.expected_package_count}, "
            f"curated_assets={len(spec.curated_assets)}, "
            f"curated_strings={len(spec.curated_strings)}"
        )
    for spec in STRING_EVIDENCE_SPECS:
        print(f"- {spec.name}: curated_strings={len(spec.curated_strings)}")
    for spec in NON_CATALOG_FEATURE_PACKAGE_SPECS:
        print(
            f"- {spec.name}: package_assets={spec.expected_package_count}, "
            "catalog=absent, feature_package=present"
        )
    classified_assets = sum(
        profile.expected_asset_count for profile in APK_ASSET_PACKAGE_PROFILES
    )
    print(
        "- asset_package_inventory: "
        f"classified_packages={len(APK_ASSET_PACKAGE_PROFILES)}, "
        f"classified_assets={classified_assets}"
    )
    model_catalog_path = analysis_dir / "model_catalog.csv"
    if model_catalog_path.exists():
        print(
            "- catalog_source: "
            f"rows={len(catalog_rows_from_csv(model_catalog_path))}, "
            "source=model_catalog.csv"
        )
    if scene_native_lib is not None:
        print(
            "- scene_native_exports: "
            f"dynsym={SCENE_NATIVE_DYNSYM_COUNT}, "
            f"paired_api={len(SCENE_NATIVE_PAIRED_API_HANDLER_PAIRS)}, "
            f"ic_only_api={len(SCENE_NATIVE_IC_ONLY_API_HANDLERS)}, "
            f"loop_handlers={len(SCENE_NATIVE_LOOP_HANDLERS)}, "
            f"state_exports={len(SCENE_NATIVE_STATE_EXPORTS)}, "
            f"animation_exports={len(SCENE_NATIVE_ANIMATION_EXPORTS)}, "
            f"drive_exports={len(SCENE_NATIVE_DRIVE_EXPORTS)}, "
            f"persistence_exports={len(SCENE_NATIVE_PERSISTENCE_EXPORTS)}"
        )
        print(
            "- scene_native_code_anchors: "
            f"anchors={len(SCENE_NATIVE_CODE_ANCHORS)}, "
            "thumb_text_hashes=verified"
        )
    if sp802e_native_lib is not None:
        print(
            "- sp802e_native_exports: "
            f"dynsym={SP802E_NATIVE_DYNSYM_COUNT}, "
            f"export_symbols={len(SP802E_NATIVE_EXPORT_SYMBOLS)}, "
            f"detail_anchors={len(SP802E_NATIVE_EXPORT_DETAIL_ANCHORS)}"
        )
    if sp630e_native_lib is not None:
        print(
            "- sp630e_native_exports: "
            f"dynsym={SP630E_NATIVE_DYNSYM_COUNT}, "
            f"export_symbols={len(SP630E_NATIVE_EXPORT_SYMBOLS)}, "
            f"detail_anchors={len(SP630E_NATIVE_EXPORT_DETAIL_ANCHORS)}"
        )
    if blutter_dir is not None:
        print(
            "- blutter_app_command_ids: "
            f"ids={len(BANLANX_APP_COMMAND_ID_HINTS)}, source=objs.txt"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
