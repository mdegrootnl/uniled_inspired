"""Audit old UniLED model evidence against the generated BanlanX catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
DEFAULT_LEGACY_ROOT = WORKSPACE_ROOT / "uniled"

MODEL_NAME_RE = re.compile(r'name\s*=\s*"(?P<name>SP[0-9A-F]{3}E)"')
ID_MAP_NAME_RE = re.compile(r'0x[0-9A-Fa-f]+\s*:\s*"(?P<name>SP[0-9A-F]{3}E)"')
COMMAND_BUILDER_RE = re.compile(
    r"^\s*def\s+(?P<name>build_[A-Za-z0-9_]+)\s*\(",
    re.MULTILINE,
)

IGNORED_OLD_COMMAND_BUILDERS = frozenset({"on_connect"})
GENERAL_OLD_COMMAND_ALIASES = {
    "onoff": "power",
    "white": "white_level",
    "onoff_effect": "onoff_config",
    "onoff_speed": "onoff_config",
    "onoff_pixels": "onoff_config",
}
SOURCE_OLD_COMMAND_ALIASES = {
    "custom_components/uniled/lib/ble/banlanx_6xx.py": {
        # Old UniLED's SP6xx effect command delegates to the same 0x53
        # mode/effect encoder that UniLED Next exposes as light_mode.
        "effect": "light_mode",
    },
}


@dataclass(frozen=True, slots=True)
class LegacyCommandSurface:
    """Command-builder coverage for one old UniLED source module."""

    source_module: str
    old_command_builders: tuple[str, ...]
    covered_builders: tuple[str, ...]
    stubbed_builders: tuple[str, ...]
    missing_builders: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LegacyUniLEDAudit:
    """Result of comparing old UniLED model files with the new catalog."""

    legacy_ble_names: tuple[str, ...]
    legacy_net_names: tuple[str, ...]
    apk_overlap: tuple[str, ...]
    catalog_legacy_names: tuple[str, ...]
    legacy_only_names: tuple[str, ...]
    catalog_legacy_only_names: tuple[str, ...]
    legacy_zengge_mesh_supported: bool
    missing_catalog_flags: tuple[str, ...]
    extra_catalog_flags: tuple[str, ...]
    missing_legacy_only_catalog_names: tuple[str, ...]
    extra_legacy_only_catalog_names: tuple[str, ...]
    legacy_recognized_names: tuple[str, ...]
    zengge_mesh_mismatches: tuple[str, ...]
    migration_mismatches: tuple[str, ...]
    command_surfaces: tuple[LegacyCommandSurface, ...]
    command_surface_mismatches: tuple[str, ...]
    autodiscovery_mismatches: tuple[str, ...]
    entity_identity_mismatches: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return whether the audit found no parity/catalog mismatches."""
        return not (
            not self.legacy_zengge_mesh_supported
            or self.legacy_net_names
            or self.missing_catalog_flags
            or self.extra_catalog_flags
            or self.missing_legacy_only_catalog_names
            or self.extra_legacy_only_catalog_names
            or self.legacy_recognized_names
            or self.zengge_mesh_mismatches
            or self.migration_mismatches
            or self.command_surface_mismatches
            or self.autodiscovery_mismatches
            or self.entity_identity_mismatches
        )


def audit_legacy_uniled(legacy_root: Path = DEFAULT_LEGACY_ROOT) -> LegacyUniLEDAudit:
    """Return old-UniLED parity coverage against the bundled catalog."""
    sys.path.insert(0, str(PROJECT_ROOT))
    from custom_components.uniled.core import (
        EntityCategoryKind,
        FeatureSpec,
        PlatformKind,
        ProtocolFamily,
        SupportLevel,
        TransportKind,
        default_catalog,
        legacy_uniled_parity_profile_for_model,
    )
    from custom_components.uniled.core.transports import mesh_profile_for_model
    from custom_components.uniled.entity_metadata import legacy_uniled_unique_id

    catalog = default_catalog()
    legacy_ble_names = old_uniled_ble_model_names(legacy_root)
    legacy_net_names = old_uniled_net_model_names(legacy_root)
    legacy_zengge_mesh_supported = old_uniled_zengge_mesh_supported(legacy_root)
    legacy_only_catalog_names = {
        model.name
        for model in catalog.user_facing_models()
        if _is_legacy_uniled_only_model(model)
    }
    apk_names = set(catalog.user_facing_names) - legacy_only_catalog_names
    apk_overlap = tuple(sorted(legacy_ble_names & apk_names))
    catalog_legacy_names = tuple(
        sorted(
            {
                model.name
                for model in catalog.user_facing_models()
                if model.legacy_uniled_supported
                and not _is_legacy_uniled_only_model(model)
            }
        )
    )
    legacy_only_names = tuple(sorted(legacy_ble_names - apk_names))
    catalog_legacy_only_names = tuple(sorted(legacy_only_catalog_names))
    missing_catalog_flags = tuple(sorted(set(apk_overlap) - set(catalog_legacy_names)))
    extra_catalog_flags = tuple(sorted(set(catalog_legacy_names) - set(apk_overlap)))
    missing_legacy_only_catalog_names = tuple(
        sorted(set(legacy_only_names) - legacy_only_catalog_names)
    )
    extra_legacy_only_catalog_names = tuple(
        sorted(legacy_only_catalog_names - set(legacy_only_names))
    )
    legacy_recognized_names = tuple(
        sorted(
            model.name
            for model in catalog.user_facing_models()
            if model.name in set(apk_overlap)
            and model.support_level is SupportLevel.RECOGNIZED
        )
    )
    zengge_mesh_mismatches: list[str] = []
    if legacy_zengge_mesh_supported:
        rg4 = catalog.resolve_name("RG4")
        if rg4 is None or not rg4.is_user_facing:
            zengge_mesh_mismatches.append("RG4 missing from user-facing catalog")
        else:
            if rg4.family is not ProtocolFamily.ZENGGE_MESH:
                zengge_mesh_mismatches.append(
                    f"RG4 family is {rg4.family.value}, expected zengge_mesh"
                )
            if TransportKind.BLE_MESH not in rg4.transports:
                zengge_mesh_mismatches.append("RG4 missing ble_mesh transport")
            if rg4.support_level is SupportLevel.RECOGNIZED:
                zengge_mesh_mismatches.append("RG4 still recognized-only")
            mesh_profile = mesh_profile_for_model(rg4)
            if mesh_profile is None:
                zengge_mesh_mismatches.append("RG4 missing mesh profile")
            elif not (
                mesh_profile.old_uniled_protocol_known
                and mesh_profile.core_command_protocol_known
            ):
                zengge_mesh_mismatches.append(
                    "RG4 mesh profile missing old-UniLED/core command evidence"
                )
    migration_mismatches = old_uniled_migration_mismatches(
        legacy_ble_names,
        catalog,
        legacy_zengge_mesh_supported=legacy_zengge_mesh_supported,
    )
    parity_profiles = {
        profile.source_module: profile
        for model in catalog.user_facing_models()
        if (profile := legacy_uniled_parity_profile_for_model(model)) is not None
    }
    command_surfaces = old_uniled_command_surfaces(
        legacy_root,
        parity_profiles.values(),
    )
    command_surface_mismatches = tuple(
        f"{surface.source_module}: {', '.join(surface.missing_builders)}"
        for surface in command_surfaces
        if surface.missing_builders
    )
    autodiscovery_mismatches = old_uniled_autodiscovery_mismatches(
        legacy_ble_names,
        catalog,
        legacy_zengge_mesh_supported=legacy_zengge_mesh_supported,
    )
    entity_identity_mismatches = old_uniled_entity_identity_mismatches(
        legacy_root,
        FeatureSpec=FeatureSpec,
        PlatformKind=PlatformKind,
        EntityCategoryKind=EntityCategoryKind,
        legacy_uniled_unique_id=legacy_uniled_unique_id,
    )
    return LegacyUniLEDAudit(
        legacy_ble_names=tuple(sorted(legacy_ble_names)),
        legacy_net_names=tuple(sorted(legacy_net_names)),
        apk_overlap=apk_overlap,
        catalog_legacy_names=catalog_legacy_names,
        legacy_only_names=legacy_only_names,
        catalog_legacy_only_names=catalog_legacy_only_names,
        legacy_zengge_mesh_supported=legacy_zengge_mesh_supported,
        missing_catalog_flags=missing_catalog_flags,
        extra_catalog_flags=extra_catalog_flags,
        missing_legacy_only_catalog_names=missing_legacy_only_catalog_names,
        extra_legacy_only_catalog_names=extra_legacy_only_catalog_names,
        legacy_recognized_names=legacy_recognized_names,
        zengge_mesh_mismatches=tuple(zengge_mesh_mismatches),
        migration_mismatches=migration_mismatches,
        command_surfaces=command_surfaces,
        command_surface_mismatches=command_surface_mismatches,
        autodiscovery_mismatches=autodiscovery_mismatches,
        entity_identity_mismatches=entity_identity_mismatches,
    )


def old_uniled_migration_mismatches(
    legacy_ble_names: set[str],
    catalog: object,
    *,
    legacy_zengge_mesh_supported: bool,
) -> tuple[str, ...]:
    """Return old-UniLED config entries that no longer migrate safely."""
    from custom_components.uniled.const import (
        CONF_ADDRESS,
        CONF_DEVICE_ID,
        CONF_MESH_UUID,
        CONF_MODEL,
        CONF_MODEL_ID,
        CONF_TRANSPORT,
        TRANSPORT_BLE,
        TRANSPORT_BLE_MESH,
    )
    from custom_components.uniled.setup_data import (
        SetupDataError,
        migrate_legacy_entry_data,
    )

    mismatches: list[str] = []
    for index, name in enumerate(sorted(legacy_ble_names)):
        address = f"AA:BB:CC:22:{index:02X}:00"
        cases = (
            (
                "explicit",
                {
                    CONF_TRANSPORT: "ble",
                    CONF_MODEL: name,
                    CONF_ADDRESS: address,
                },
            ),
            (
                "inferred",
                {
                    CONF_MODEL: name,
                    CONF_ADDRESS: address,
                },
            ),
        )

        model = catalog.resolve_name(name)
        expected_values = {
            CONF_MODEL: name,
            CONF_MODEL_ID: getattr(model, "model_id", None),
            CONF_ADDRESS: address,
            CONF_TRANSPORT: TRANSPORT_BLE,
        }
        for label, entry_data in cases:
            try:
                migrated = migrate_legacy_entry_data(catalog, entry_data)
            except SetupDataError as ex:
                mismatches.append(
                    f"{name} {label}: migration failed at {ex.field} ({ex.reason})"
                )
                continue

            for key, expected in expected_values.items():
                actual = migrated.get(key)
                if actual != expected:
                    mismatches.append(
                        f"{name} {label}: {key} expected {expected!r}, "
                        f"got {actual!r}"
                    )
            extra_keys = tuple(sorted(set(migrated) - set(expected_values)))
            if extra_keys:
                mismatches.append(
                    f"{name} {label}: unexpected migrated keys {extra_keys!r}"
                )

    if legacy_zengge_mesh_supported:
        for label, entry_data, expected_values in (
            (
                "zengge_cloud",
                {
                    CONF_TRANSPORT: "zng",
                    "mesh_id": "zng_mesh_0x211",
                    CONF_MESH_UUID: "0x211",
                    "username": "old@example.com",
                    "password": "do-not-store",
                    "country": "US",
                },
                {
                    CONF_MODEL: "RG4",
                    CONF_MODEL_ID: 44034,
                    CONF_DEVICE_ID: "zng_mesh_0x211",
                    CONF_MESH_UUID: 0x0211,
                    CONF_TRANSPORT: TRANSPORT_BLE_MESH,
                },
            ),
            (
                "zengge_mesh_uuid",
                {
                    CONF_TRANSPORT: "zng",
                    CONF_MESH_UUID: "0x211",
                },
                {
                    CONF_MODEL: "RG4",
                    CONF_MODEL_ID: 44034,
                    CONF_DEVICE_ID: "zng_mesh_0x211",
                    CONF_MESH_UUID: 0x0211,
                    CONF_TRANSPORT: TRANSPORT_BLE_MESH,
                },
            ),
        ):
            try:
                migrated = migrate_legacy_entry_data(catalog, entry_data)
            except SetupDataError as ex:
                mismatches.append(
                    f"{label}: migration failed at {ex.field} ({ex.reason})"
                )
                continue

            for key, expected in expected_values.items():
                actual = migrated.get(key)
                if actual != expected:
                    mismatches.append(
                        f"{label}: {key} expected {expected!r}, got {actual!r}"
                    )
            extra_keys = tuple(sorted(set(migrated) - set(expected_values)))
            if extra_keys:
                mismatches.append(
                    f"{label}: unexpected migrated keys {extra_keys!r}"
                )

    return tuple(mismatches)


def old_uniled_autodiscovery_mismatches(
    legacy_ble_names: set[str],
    catalog: object,
    *,
    legacy_zengge_mesh_supported: bool,
    manifest_path: Path = PROJECT_ROOT
    / "custom_components"
    / "uniled"
    / "manifest.json",
) -> tuple[str, ...]:
    """Return old-UniLED discovery paths that can no longer resolve safely."""
    from custom_components.uniled.const import (
        CONF_ADDRESS,
        CONF_DEVICE_ID,
        CONF_DISCOVERY_CONFIDENCE,
        CONF_DISCOVERY_MATCH,
        CONF_MESH_NODE_ID,
        CONF_MESH_NODE_TYPE,
        CONF_MESH_UUID,
        CONF_MODEL,
        CONF_TRANSPORT,
        DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
        DISCOVERY_MATCH_EXACT_LABEL,
        DISCOVERY_MATCH_SAFE_SUFFIX,
        DISCOVERY_MATCH_TELINK_MESH,
        TRANSPORT_BLE,
        TRANSPORT_BLE_MESH,
    )
    from custom_components.uniled.setup_data import (
        SetupDataError,
        bluetooth_setup_entry_data_from_discovery,
        setup_entry_compatibility_unique_ids,
        setup_entry_requires_discovery_confirmation,
    )

    mismatches: list[str] = []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bluetooth = manifest.get("bluetooth", ())
    patterns = tuple(
        matcher["local_name"]
        for matcher in bluetooth
        if isinstance(matcher, dict) and isinstance(matcher.get("local_name"), str)
    )
    if "SP*" in patterns:
        mismatches.append("manifest: broad SP* matcher is unsafe")

    for index, name in enumerate(sorted(legacy_ble_names)):
        if not any(fnmatchcase(name, pattern) for pattern in patterns):
            mismatches.append(f"{name}: no Bluetooth manifest local_name matcher")
        for label, advertised_name, expected_match in (
            ("exact", name, DISCOVERY_MATCH_EXACT_LABEL),
            ("safe_suffix", f"{name}_AABB", DISCOVERY_MATCH_SAFE_SUFFIX),
        ):
            address = f"AA:BB:CC:20:{index:02X}:{0 if label == 'exact' else 1:02X}"
            discovery = SimpleNamespace(
                name=advertised_name if label == "exact" else "",
                local_name=advertised_name if label != "exact" else "",
                address=address,
                manufacturer_data={},
                connectable=True,
            )
            try:
                setup = bluetooth_setup_entry_data_from_discovery(
                    catalog,
                    discovery,
                )
            except SetupDataError as ex:
                mismatches.append(
                    f"{name} {label}: setup failed at {ex.field} ({ex.reason})"
                )
                continue

            expected_unique_id = f"ble:{address.casefold()}"
            if setup.unique_id != expected_unique_id:
                mismatches.append(
                    f"{name} {label}: unique_id expected {expected_unique_id!r}, "
                    f"got {setup.unique_id!r}"
                )
            expected_compat_ids = (address, address.casefold())
            if expected_compat_ids[0] == expected_compat_ids[1]:
                expected_compat_ids = (address,)
            actual_compat_ids = setup_entry_compatibility_unique_ids(setup)
            if actual_compat_ids != expected_compat_ids:
                mismatches.append(
                    f"{name} {label}: compatibility IDs expected "
                    f"{expected_compat_ids!r}, got {actual_compat_ids!r}"
                )

            expected_values = {
                CONF_MODEL: name,
                CONF_ADDRESS: address,
                CONF_TRANSPORT: TRANSPORT_BLE,
                CONF_DISCOVERY_MATCH: expected_match,
                CONF_DISCOVERY_CONFIDENCE: DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
            }
            for key, expected in expected_values.items():
                actual = setup.data.get(key)
                if actual != expected:
                    mismatches.append(
                        f"{name} {label}: {key} expected {expected!r}, "
                        f"got {actual!r}"
                    )
            if setup_entry_requires_discovery_confirmation(setup):
                mismatches.append(f"{name} {label}: requires confirmation")

        near_miss = SimpleNamespace(
            name=f"{name}X",
            local_name="",
            address=f"AA:BB:CC:20:{index:02X}:02",
            manufacturer_data={},
            connectable=True,
        )
        try:
            setup = bluetooth_setup_entry_data_from_discovery(catalog, near_miss)
        except SetupDataError as ex:
            if ex.field != CONF_MODEL or ex.reason != "unknown_model":
                mismatches.append(
                    f"{name} near_miss: expected unknown_model at {CONF_MODEL}, "
                    f"got {ex.field} ({ex.reason})"
                )
        else:
            mismatches.append(
                f"{name} near_miss: unsafe no-separator suffix resolved as "
                f"{setup.data.get(CONF_MODEL)!r}"
            )

    if legacy_zengge_mesh_supported:
        if "RG4" not in patterns:
            mismatches.append("RG4: no Bluetooth manifest local_name matcher")
        telink_matcher_found = any(
            isinstance(matcher, dict)
            and matcher.get("manufacturer_id") == 529
            and matcher.get("service_uuid")
            == "00010203-0405-0607-0809-0a0b0c0d1910"
            for matcher in bluetooth
        )
        if not telink_matcher_found:
            mismatches.append("RG4: no Telink manufacturer-data manifest matcher")

        mesh_cases = (
            (
                "rg4_exact",
                SimpleNamespace(
                    name="RG4",
                    local_name="",
                    address="AA:BB:CC:21:00:00",
                    manufacturer_data={},
                    connectable=True,
                ),
                "ble_mesh:aa:bb:cc:21:00:00",
                {
                    CONF_MODEL: "RG4",
                    CONF_ADDRESS: "AA:BB:CC:21:00:00",
                    CONF_TRANSPORT: TRANSPORT_BLE_MESH,
                    CONF_DISCOVERY_MATCH: DISCOVERY_MATCH_EXACT_LABEL,
                    CONF_DISCOVERY_CONFIDENCE: DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
                },
            ),
            (
                "rg4_telink",
                SimpleNamespace(
                    name="Zengge",
                    local_name="",
                    address="AA:BB:CC:21:00:01",
                    manufacturer_data={
                        529: bytes.fromhex("11 02 00 00 00 00 00 23 00 44")
                    },
                    connectable=True,
                ),
                "zng_mesh_0x211",
                {
                    CONF_MODEL: "RG4",
                    CONF_ADDRESS: "AA:BB:CC:21:00:01",
                    CONF_DEVICE_ID: "zng_mesh_0x211",
                    CONF_MESH_UUID: 0x0211,
                    CONF_MESH_NODE_ID: 0x44,
                    CONF_MESH_NODE_TYPE: 0x23,
                    CONF_TRANSPORT: TRANSPORT_BLE_MESH,
                    CONF_DISCOVERY_MATCH: DISCOVERY_MATCH_TELINK_MESH,
                    CONF_DISCOVERY_CONFIDENCE: DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN,
                },
            ),
        )
        for label, discovery, expected_unique_id, expected_values in mesh_cases:
            try:
                setup = bluetooth_setup_entry_data_from_discovery(
                    catalog,
                    discovery,
                )
            except SetupDataError as ex:
                mismatches.append(
                    f"{label}: setup failed at {ex.field} ({ex.reason})"
                )
                continue
            if setup.unique_id != expected_unique_id:
                mismatches.append(
                    f"{label}: unique_id expected {expected_unique_id!r}, "
                    f"got {setup.unique_id!r}"
                )
            for key, expected in expected_values.items():
                actual = setup.data.get(key)
                if actual != expected:
                    mismatches.append(
                        f"{label}: {key} expected {expected!r}, got {actual!r}"
                    )
            if setup_entry_requires_discovery_confirmation(setup):
                mismatches.append(f"{label}: requires confirmation")

    return tuple(mismatches)


def old_uniled_entity_identity_mismatches(
    legacy_root: Path,
    *,
    FeatureSpec: object,
    PlatformKind: object,
    EntityCategoryKind: object,
    legacy_uniled_unique_id: object,
) -> tuple[str, ...]:
    """Return mismatches in proven old-UniLED entity identity compatibility."""
    from custom_components.uniled.const import (
        CONF_MODEL,
        CONF_TRANSPORT,
        TRANSPORT_BLE,
        TRANSPORT_BLE_MESH,
    )

    mismatches: list[str] = []
    _verify_old_entity_identity_anchors(legacy_root, mismatches)

    direct_ble = SimpleNamespace(
        unique_id="AA:BB:CC:DD:EE:10",
        entry_id="entry-id",
        data={CONF_MODEL: "SP611E", CONF_TRANSPORT: TRANSPORT_BLE},
    )
    sp601 = SimpleNamespace(
        unique_id="AA:BB:CC:DD:EE:20",
        entry_id="entry-id",
        data={CONF_MODEL: "SP601E", CONF_TRANSPORT: TRANSPORT_BLE},
    )
    mesh = SimpleNamespace(
        unique_id="zng_mesh_0x211",
        entry_id="entry-id",
        data={CONF_MODEL: "RG4", CONF_TRANSPORT: TRANSPORT_BLE_MESH},
    )

    cases = (
        (
            "direct_ble_main_light",
            direct_ble,
            FeatureSpec(
                key="main_light",
                platform=PlatformKind.LIGHT,
                name="Light",
            ),
            "_AA:BB:CC:DD:EE:10_strip",
        ),
        (
            "sp601_output_light",
            sp601,
            FeatureSpec(
                key="output_1_light",
                platform=PlatformKind.LIGHT,
                name="Output 1",
                channel=1,
                implementation_hint="legacy_uniled_output",
            ),
            "_AA:BB:CC:DD:EE:20_channel_1_strip",
        ),
        (
            "sp601_scene",
            sp601,
            FeatureSpec(
                key="scene_0",
                platform=PlatformKind.SCENE,
                name="Scene 1",
                implementation_hint="legacy_uniled",
            ),
            "_AA:BB:CC:DD:EE:20_master_scene_0",
        ),
        (
            "zengge_mesh_node_light",
            mesh,
            FeatureSpec(
                key="mesh_light_44",
                platform=PlatformKind.LIGHT,
                name="Node 68",
                channel=0x44,
                implementation_hint="zengge_mesh_node",
            ),
            "_zng_mesh_0x211_node_68",
        ),
        (
            "zengge_mesh_panel_status",
            mesh,
            FeatureSpec(
                key="mesh_panel_20_status",
                platform=PlatformKind.SENSOR,
                name="Panel 32",
                channel=0x20,
                entity_category=EntityCategoryKind.DIAGNOSTIC,
                implementation_hint="zengge_mesh_panel",
            ),
            "_zng_mesh_0x211_node_32",
        ),
        (
            "zengge_mesh_new_effect_control",
            mesh,
            FeatureSpec(
                key="effect_speed",
                platform=PlatformKind.NUMBER,
                name="Node 68 effect speed",
                channel=0x44,
                implementation_hint="zengge_mesh_node",
            ),
            None,
        ),
    )
    for label, entry, feature, expected in cases:
        actual = legacy_uniled_unique_id(entry, feature)
        if actual != expected:
            mismatches.append(
                f"{label}: expected {expected!r}, got {actual!r}"
            )

    return tuple(mismatches)


def _verify_old_entity_identity_anchors(
    legacy_root: Path,
    mismatches: list[str],
) -> None:
    """Check the old checkout still contains the identity shapes we preserve."""
    anchors = (
        (
            "custom_components/uniled/config_flow.py",
            ("discovery.address", "async_set_unique_id", "mesh_unique"),
        ),
        (
            "custom_components/uniled/entity.py",
            (
                'self._attr_unique_id = f"_{base_unique_id}"',
                'channel.identity.replace(" ", "_").lower()',
                'self._attr_unique_id = f"{self._attr_unique_id}_{key}"',
            ),
        ),
        (
            "custom_components/uniled/lib/channel.py",
            ('return f"{CHANNEL.lower()}_{self.number}"',),
        ),
        (
            "custom_components/uniled/lib/device.py",
            (
                "return None",
                'return self._name.replace(" ", "_").lower()',
            ),
        ),
        (
            "custom_components/uniled/lib/zng/node.py",
            ('return f"Node {self.number}"',),
        ),
        (
            "custom_components/uniled/lib/zng/manager.py",
            (
                "def mesh_uuid_unique",
                'f"{UNILED_TRANSPORT_ZNG}_mesh_{hex(mesh_uuid)}"',
            ),
        ),
    )
    for relative_path, expected_anchors in anchors:
        path = legacy_root / relative_path
        if not path.exists():
            mismatches.append(f"{relative_path}: missing")
            continue
        text = path.read_text(encoding="utf-8")
        for anchor in expected_anchors:
            if anchor not in text:
                mismatches.append(f"{relative_path}: missing anchor {anchor!r}")


def old_uniled_ble_model_names(legacy_root: Path) -> set[str]:
    """Return exact SP model names statically recoverable from old BLE modules."""
    ble_dir = legacy_root / "custom_components" / "uniled" / "lib" / "ble"
    if not ble_dir.exists():
        raise FileNotFoundError(f"old UniLED BLE directory not found: {ble_dir}")

    names: set[str] = set()
    for path in ble_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        names.update(match.group("name") for match in MODEL_NAME_RE.finditer(text))
        names.update(match.group("name") for match in ID_MAP_NAME_RE.finditer(text))
    return names


def old_uniled_net_model_names(legacy_root: Path) -> set[str]:
    """Return exact SP model names statically recoverable from old NET modules."""
    net_dir = legacy_root / "custom_components" / "uniled" / "lib" / "net"
    if not net_dir.exists():
        raise FileNotFoundError(f"old UniLED NET directory not found: {net_dir}")

    names: set[str] = set()
    for path in net_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        names.update(match.group("name") for match in MODEL_NAME_RE.finditer(text))
        names.update(match.group("name") for match in ID_MAP_NAME_RE.finditer(text))
    return names


def old_uniled_zengge_mesh_supported(legacy_root: Path) -> bool:
    """Return whether old UniLED contains the Zengge mesh implementation."""
    zng_dir = legacy_root / "custom_components" / "uniled" / "lib" / "zng"
    manager = zng_dir / "manager.py"
    packetutils = zng_dir / "packetutils.py"
    if not manager.exists() or not packetutils.exists():
        return False

    manager_text = manager.read_text(encoding="utf-8")
    packet_text = packetutils.read_text(encoding="utf-8")
    return (
        "class ZenggeManager" in manager_text
        and "class ZenggeModel" in manager_text
        and "make_command_packet" in packet_text
        and "decrypt_packet" in packet_text
    )


def old_uniled_command_surfaces(
    legacy_root: Path,
    profiles: object,
) -> tuple[LegacyCommandSurface, ...]:
    """Return old-UniLED command coverage for parity profile source modules."""
    surfaces: list[LegacyCommandSurface] = []
    for profile in sorted(profiles, key=lambda item: item.source_module):
        old_builders = old_uniled_command_builders(
            legacy_root,
            profile.source_module,
        )
        covered = set(profile.command_builders) | set(profile.stubbed_builders)
        missing = tuple(
            builder for builder in old_builders if builder not in covered
        )
        surfaces.append(
            LegacyCommandSurface(
                source_module=profile.source_module,
                old_command_builders=old_builders,
                covered_builders=tuple(
                    builder for builder in old_builders if builder in covered
                ),
                stubbed_builders=tuple(
                    builder
                    for builder in old_builders
                    if builder in set(profile.stubbed_builders)
                ),
                missing_builders=missing,
            )
        )
    return tuple(surfaces)


def old_uniled_command_builders(
    legacy_root: Path,
    source_module: str,
) -> tuple[str, ...]:
    """Return normalized command builders from one old UniLED source module."""
    path = legacy_root / Path(source_module)
    if not path.exists():
        raise FileNotFoundError(f"old UniLED source module not found: {path}")

    text = path.read_text(encoding="utf-8")
    builders = {
        mapped
        for match in COMMAND_BUILDER_RE.finditer(text)
        if (builder := _old_command_builder_name(match.group("name"))) is not None
        if (mapped := _map_old_command_builder(source_module, builder)) is not None
    }
    return tuple(sorted(builders))


def _old_command_builder_name(function_name: str) -> str | None:
    builder = function_name.removeprefix("build_")
    if builder in IGNORED_OLD_COMMAND_BUILDERS:
        return None
    if builder.endswith("_command"):
        builder = builder[: -len("_command")]
    if builder in IGNORED_OLD_COMMAND_BUILDERS:
        return None
    return builder


def _map_old_command_builder(source_module: str, builder: str) -> str | None:
    source_aliases = SOURCE_OLD_COMMAND_ALIASES.get(source_module, {})
    return source_aliases.get(
        builder,
        GENERAL_OLD_COMMAND_ALIASES.get(builder, builder),
    )


def _is_legacy_uniled_only_model(model: object) -> bool:
    """Return whether a catalog row was sourced from old UniLED only."""
    return str(getattr(model, "home_uri", "")).startswith("/legacy/uniled/")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit old UniLED model overlap with the BanlanX catalog.",
    )
    parser.add_argument(
        "--legacy-root",
        type=Path,
        default=DEFAULT_LEGACY_ROOT,
        help="Path to the old UniLED checkout, default: ../uniled",
    )
    return parser


def main() -> int:
    """Run the legacy parity audit."""
    args = _parser().parse_args()
    audit = audit_legacy_uniled(args.legacy_root)
    print(
        "Legacy UniLED audit: "
        f"ble={len(audit.legacy_ble_names)}, "
        f"net={len(audit.legacy_net_names)}, "
        f"zengge_mesh={'yes' if audit.legacy_zengge_mesh_supported else 'no'}, "
        f"apk_overlap={len(audit.apk_overlap)}, "
        f"legacy_only={','.join(audit.legacy_only_names) or 'none'}, "
        f"migration_mismatches={len(audit.migration_mismatches)}, "
        f"command_surfaces={len(audit.command_surfaces)}, "
        f"command_mismatches={len(audit.command_surface_mismatches)}, "
        f"autodiscovery_mismatches={len(audit.autodiscovery_mismatches)}, "
        f"entity_identity_mismatches={len(audit.entity_identity_mismatches)}"
    )
    if audit.passed:
        return 0
    if audit.legacy_net_names:
        print(f"Unexpected old NET models: {', '.join(audit.legacy_net_names)}")
    if not audit.legacy_zengge_mesh_supported:
        print("Old Zengge mesh support not found")
    if audit.missing_catalog_flags:
        print(
            "Catalog missing legacy flags: "
            f"{', '.join(audit.missing_catalog_flags)}"
        )
    if audit.extra_catalog_flags:
        print(f"Extra catalog legacy flags: {', '.join(audit.extra_catalog_flags)}")
    if audit.missing_legacy_only_catalog_names:
        print(
            "Catalog missing legacy-only rows: "
            f"{', '.join(audit.missing_legacy_only_catalog_names)}"
        )
    if audit.extra_legacy_only_catalog_names:
        print(
            "Extra catalog legacy-only rows: "
            f"{', '.join(audit.extra_legacy_only_catalog_names)}"
        )
    if audit.legacy_recognized_names:
        print(
            "Legacy overlap still recognized: "
            f"{', '.join(audit.legacy_recognized_names)}"
        )
    if audit.zengge_mesh_mismatches:
        print(
            "Legacy Zengge mesh mismatches: "
            f"{'; '.join(audit.zengge_mesh_mismatches)}"
        )
    if audit.migration_mismatches:
        print(
            "Legacy migration mismatches: "
            f"{'; '.join(audit.migration_mismatches)}"
        )
    if audit.command_surface_mismatches:
        print(
            "Legacy command surface mismatches: "
            f"{'; '.join(audit.command_surface_mismatches)}"
        )
    if audit.autodiscovery_mismatches:
        print(
            "Legacy autodiscovery mismatches: "
            f"{'; '.join(audit.autodiscovery_mismatches)}"
        )
    if audit.entity_identity_mismatches:
        print(
            "Legacy entity identity mismatches: "
            f"{'; '.join(audit.entity_identity_mismatches)}"
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
