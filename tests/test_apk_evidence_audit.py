"""Tests for local APK evidence audit helpers."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from custom_components.uniled.core.apk_assets import (
    APK_ASSET_PACKAGE_PROFILES,
    APKAssetPackageRole,
    apk_asset_package_keys_by_role,
    apk_asset_package_profile_for_key,
    apk_asset_package_profiles,
)
from custom_components.uniled.core.car_lights import (
    CAR_LIGHT_MODEL_ROLE_HINTS,
    CAR_LIGHT_SETUP_DEPENDENCIES,
)
from custom_components.uniled.core.cloud import (
    BANLANX_CLOUD_ENDPOINT_INVENTORY,
    BANLANX_CLOUD_RAW_STRING_HINTS,
    BANLANX_CLOUD_REQUEST_CONTRACT_HINTS,
)
from custom_components.uniled.core.feature_packages import (
    GUNDAM_PROFILE,
    describe_non_catalog_feature_package_profile,
    non_catalog_feature_package_profiles,
)
from custom_components.uniled.core.network import (
    SP802E_NATIVE_EXPORT_DETAIL_ANCHORS,
    SP802E_NATIVE_EXPORT_SYMBOLS,
)
from custom_components.uniled.core.scene import (
    SCENE_NATIVE_ANIMATION_EXPORTS,
    SCENE_NATIVE_CODE_ANCHORS,
    SCENE_NATIVE_DRIVE_EXPORTS,
    SCENE_NATIVE_IC_ONLY_API_HANDLERS,
    SCENE_NATIVE_LOOP_HANDLERS,
    SCENE_NATIVE_PAIRED_API_HANDLER_PAIRS,
    SCENE_NATIVE_PERSISTENCE_EXPORTS,
    SCENE_NATIVE_STATE_EXPORTS,
)
from custom_components.uniled.core.sp630e import (
    SP630E_NATIVE_EXPORT_DETAIL_ANCHORS,
    SP630E_NATIVE_EXPORT_SYMBOLS,
)
from custom_components.uniled.core.transports.ble import (
    APK_BLE_PLUGIN_CONTRACT_STRING_HINTS,
    APK_BLE_UUID_INVENTORY,
    APK_BLE_UUID_STRING_HINTS,
)
from scripts.audit_apk_evidence import (
    BANLANX_CLOUD_AUDITED_STRING_HINTS,
    EVIDENCE_SPECS,
    NON_CATALOG_FEATURE_PACKAGE_SPECS,
    SCENE_NATIVE_DYNSYM_COUNT,
    SP630E_NATIVE_DYNSYM_COUNT,
    SP802E_NATIVE_DYNSYM_COUNT,
    STRING_EVIDENCE_SPECS,
    audit_analysis_dir,
    audit_scene_native_code_anchor_values,
    audit_scene_native_export_symbols,
    audit_sp630e_native_export_symbols,
    audit_sp802e_native_export_symbols,
)


def _full_profile_assets(spec_index: int) -> tuple[str, ...]:
    spec = EVIDENCE_SPECS[spec_index]
    filler_count = spec.expected_package_count - len(spec.curated_assets)
    return (
        *spec.curated_assets,
        *(
            f"{spec.package}/assets/audit_filler_{index}.txt"
            for index in range(filler_count)
        ),
    )


def _full_non_catalog_assets(spec_index: int) -> tuple[str, ...]:
    spec = NON_CATALOG_FEATURE_PACKAGE_SPECS[spec_index]
    filler_count = spec.expected_package_count - len(spec.required_assets)
    return (
        *spec.required_assets,
        *(
            f"packages/{spec.package_key}/assets/audit_filler_{index}.txt"
            for index in range(filler_count)
        ),
    )


def _full_inventory_assets(profile_key: str) -> tuple[str, ...]:
    profile = apk_asset_package_profile_for_key(profile_key)
    assert profile is not None
    filler_count = profile.expected_asset_count - len(profile.representative_assets)
    return (
        *profile.representative_assets,
        *(
            f"{profile.package_prefix}/assets/audit_filler_{index}.txt"
            for index in range(filler_count)
        ),
    )


def _write_analysis_dir(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    counts = "\n".join(
        f"{profile.expected_asset_count} {profile.key}"
        for profile in APK_ASSET_PACKAGE_PROFILES
    )
    (root / "asset_package_counts.txt").write_text(f"{counts}\n", encoding="utf-8")
    for profile in APK_ASSET_PACKAGE_PROFILES:
        assets = "\n".join(_full_inventory_assets(profile.key))
        (root / profile.asset_file_name).write_text(f"{assets}\n", encoding="utf-8")
    for index, spec in enumerate(EVIDENCE_SPECS):
        assets = "\n".join(_full_profile_assets(index))
        (root / spec.asset_file_name).write_text(f"{assets}\n", encoding="utf-8")
    for index, spec in enumerate(NON_CATALOG_FEATURE_PACKAGE_SPECS):
        assets = "\n".join(_full_non_catalog_assets(index))
        (root / spec.asset_file_name).write_text(f"{assets}\n", encoding="utf-8")
    required_strings = "\n".join(
        string
        for spec in NON_CATALOG_FEATURE_PACKAGE_SPECS
        for string in spec.required_strings
    )
    profile_strings = "\n".join(
        (
            *(
                string
                for spec in EVIDENCE_SPECS
                for string in spec.curated_strings
            ),
            *(
                string
                for spec in STRING_EVIDENCE_SPECS
                for string in spec.curated_strings
            ),
        )
    )
    (root / "libapp.interesting.txt").write_text(required_strings, encoding="utf-8")
    (root / "libapp.strings.txt").write_text(profile_strings, encoding="utf-8")
    (root / "native.interesting.txt").write_text("", encoding="utf-8")
    (root / "libscene_lfx.strings.txt").write_text("", encoding="utf-8")
    (root / "libscene_lfx.interesting.txt").write_text("", encoding="utf-8")
    (root / "libwled_lfx.strings.txt").write_text("", encoding="utf-8")
    (root / "libwled_lfx.interesting.txt").write_text("", encoding="utf-8")
    (root / "liblfx.strings.txt").write_text("", encoding="utf-8")
    (root / "liblfx.interesting.txt").write_text("", encoding="utf-8")
    (root / "model_catalog.pretty.json").write_text("[]", encoding="utf-8")
    (root / "model_catalog.raw.json").write_text("[]", encoding="utf-8")


def _scene_native_symbol_map() -> dict[str, tuple[int, int]]:
    symbols: dict[str, tuple[int, int]] = {}
    for _capability, ic_handler, pwm_handler in SCENE_NATIVE_PAIRED_API_HANDLER_PAIRS:
        symbols[ic_handler] = (0, 1)
        symbols[pwm_handler] = (0, 1)
    for _capability, handler in SCENE_NATIVE_IC_ONLY_API_HANDLERS:
        symbols[handler] = (0, 1)
    for handler in SCENE_NATIVE_LOOP_HANDLERS:
        symbols[handler] = (0, 1)
    for anchor in (
        *SCENE_NATIVE_STATE_EXPORTS,
        *SCENE_NATIVE_ANIMATION_EXPORTS,
        *SCENE_NATIVE_DRIVE_EXPORTS,
    ):
        name, address, size = _native_export_anchor(anchor)
        symbols[name] = (address, size)
    for export in SCENE_NATIVE_PERSISTENCE_EXPORTS:
        symbols[export.symbol] = (export.value, export.size)
    return symbols


def test_cloud_endpoint_inventory_is_backed_by_audited_apk_strings() -> None:
    """Every structured BanlanX cloud endpoint remains literal APK evidence."""
    inventory_paths = tuple(
        endpoint.path for endpoint in BANLANX_CLOUD_ENDPOINT_INVENTORY
    )

    assert len(inventory_paths) == 52
    assert all(path in BANLANX_CLOUD_RAW_STRING_HINTS for path in inventory_paths)
    assert all(
        path in BANLANX_CLOUD_AUDITED_STRING_HINTS for path in inventory_paths
    )
    assert {
        endpoint.group for endpoint in BANLANX_CLOUD_ENDPOINT_INVENTORY
    } == {
        "account_auth",
        "device_auth",
        "root_device",
        "home_device",
        "btmesh",
        "user_device",
        "local_device",
        "content",
        "voice_assistant",
    }
    assert sum(
        1 for endpoint in BANLANX_CLOUD_ENDPOINT_INVENTORY if endpoint.command_related
    ) == 1
    assert all(
        endpoint.base_url == "unresolved"
        for endpoint in BANLANX_CLOUD_ENDPOINT_INVENTORY
    )
    assert all(
        endpoint.auth == "unproven"
        for endpoint in BANLANX_CLOUD_ENDPOINT_INVENTORY
    )
    assert len(BANLANX_CLOUD_AUDITED_STRING_HINTS) == 97


def test_car_light_setup_dependencies_are_backed_by_role_hints() -> None:
    """Structured car-light setup rows stay tied to recovered APK role hints."""
    dependencies = {
        dependency.model_name: dependency
        for dependency in CAR_LIGHT_SETUP_DEPENDENCIES
    }

    assert set(dependencies) == {"Car Lights", "SP701E", "SP702E", "SP-MIC"}
    assert sum(1 for dependency in dependencies.values() if dependency.required) == 1
    assert sum(
        1
        for dependency in dependencies.values()
        if dependency.setup_order is not None
    ) == 2
    assert dependencies["SP-MIC"].related_model == "SP702E"
    assert all(
        dependency.evidence in CAR_LIGHT_MODEL_ROLE_HINTS
        for dependency in dependencies.values()
    )


def test_cloud_request_contract_hints_are_backed_by_audited_apk_strings() -> None:
    """Structured BanlanX cloud request-contract hints stay literal evidence."""
    contract_strings = tuple(
        hint.apk_string for hint in BANLANX_CLOUD_REQUEST_CONTRACT_HINTS
    )

    assert len(contract_strings) == 26
    assert all(string in BANLANX_CLOUD_RAW_STRING_HINTS for string in contract_strings)
    assert all(
        string in BANLANX_CLOUD_AUDITED_STRING_HINTS for string in contract_strings
    )
    assert {
        "account_token_schema_pending",
        "request_signing_headers_pending",
    } == {hint.blocker for hint in BANLANX_CLOUD_REQUEST_CONTRACT_HINTS}
    assert sum(
        1
        for hint in BANLANX_CLOUD_REQUEST_CONTRACT_HINTS
        if hint.category == "token_or_auth_storage"
    ) == 10
    assert sum(
        1
        for hint in BANLANX_CLOUD_REQUEST_CONTRACT_HINTS
        if hint.category == "http_header"
    ) == 11
    assert sum(
        1
        for hint in BANLANX_CLOUD_REQUEST_CONTRACT_HINTS
        if hint.category == "signature_or_nonce"
    ) == 5


def test_ble_uuid_inventory_is_backed_by_audited_apk_strings() -> None:
    """Every structured BLE UUID candidate remains literal APK evidence."""
    uuid_spec = next(
        spec for spec in STRING_EVIDENCE_SPECS if spec.name == "ble_uuid_inventory"
    )

    assert tuple(
        candidate.apk_string for candidate in APK_BLE_UUID_INVENTORY
    ) == APK_BLE_UUID_STRING_HINTS[:5]
    assert uuid_spec.curated_strings == APK_BLE_UUID_STRING_HINTS
    assert len(uuid_spec.curated_strings) == 10


def test_ble_plugin_contract_strings_are_backed_by_apk_strings() -> None:
    """BLE plugin argument/error anchors remain literal APK evidence."""
    contract_spec = next(
        spec for spec in STRING_EVIDENCE_SPECS if spec.name == "ble_plugin_contract"
    )

    assert APK_BLE_PLUGIN_CONTRACT_STRING_HINTS == (
        "serviceUuid",
        "characteristicUuid",
        "value",
        "enabled",
        "timeout",
        "characteristicWriteType",
        "forceWaitResponse",
    )
    assert contract_spec.curated_strings == APK_BLE_PLUGIN_CONTRACT_STRING_HINTS
    assert len(contract_spec.curated_strings) == 7


def _scene_native_code_anchor_map() -> dict[
    str,
    tuple[int, int, bool, str, str, str, str],
]:
    return {
        name: (value, size, True, ".text", sha256, first16, last16)
        for name, value, size, sha256, first16, last16 in SCENE_NATIVE_CODE_ANCHORS
    }


def _native_export_anchor(anchor: str) -> tuple[str, int, int]:
    name, address_and_size = anchor.split("@", 1)
    address, size = address_and_size.split("/", 1)
    return name, int(address, 16), int(size)


def _sp802e_native_symbol_map() -> dict[str, tuple[int, int]]:
    symbols = {symbol: (0, 1) for symbol in SP802E_NATIVE_EXPORT_SYMBOLS}
    for name, address, size in SP802E_NATIVE_EXPORT_DETAIL_ANCHORS:
        symbols[name] = (address, size)
    return symbols


def _sp630e_native_symbol_map() -> dict[str, tuple[int, int]]:
    symbols = {symbol: (0, 1) for symbol in SP630E_NATIVE_EXPORT_SYMBOLS}
    for name, address, size in SP630E_NATIVE_EXPORT_DETAIL_ANCHORS:
        symbols[name] = (address, size)
    return symbols


def test_apk_evidence_audit_accepts_matching_analysis_artifacts() -> None:
    with TemporaryDirectory() as temp_dir:
        analysis_dir = Path(temp_dir)
        _write_analysis_dir(analysis_dir)

        assert audit_analysis_dir(analysis_dir) == []


def test_scene_native_export_audit_accepts_matching_symbols() -> None:
    assert audit_scene_native_export_symbols(
        _scene_native_symbol_map(),
        dynsym_count=SCENE_NATIVE_DYNSYM_COUNT,
    ) == []


def test_scene_native_export_audit_reports_missing_symbol() -> None:
    symbols = dict(_scene_native_symbol_map())
    del symbols["API_PWM_Scene_Set_Handler"]

    failures = audit_scene_native_export_symbols(
        symbols,
        dynsym_count=SCENE_NATIVE_DYNSYM_COUNT,
    )

    assert len(failures) == 1
    assert failures[0].name == "scene_native_exports"
    assert "API_PWM_Scene_Set_Handler" in failures[0].message


def test_scene_native_export_audit_reports_state_export_mismatch() -> None:
    symbols = dict(_scene_native_symbol_map())
    symbols["getStaDat"] = (0x1119E, 256)

    failures = audit_scene_native_export_symbols(
        symbols,
        dynsym_count=SCENE_NATIVE_DYNSYM_COUNT,
    )

    assert len(failures) == 1
    assert failures[0].name == "scene_native_exports"
    assert "getStaDat export is 0x0001119e/256" in failures[0].message


def test_scene_native_export_audit_reports_animation_export_mismatch() -> None:
    symbols = dict(_scene_native_symbol_map())
    symbols["Anim_FacTest_IC_Handler"] = (0x0000F89E, 464)

    failures = audit_scene_native_export_symbols(
        symbols,
        dynsym_count=SCENE_NATIVE_DYNSYM_COUNT,
    )

    assert len(failures) == 1
    assert failures[0].name == "scene_native_exports"
    assert "Anim_FacTest_IC_Handler export is 0x0000f89e/464" in (
        failures[0].message
    )


def test_scene_native_export_audit_reports_drive_export_mismatch() -> None:
    symbols = dict(_scene_native_symbol_map())
    symbols["LED_DRIVE_TYPE"] = (0x000196E4, 8)

    failures = audit_scene_native_export_symbols(
        symbols,
        dynsym_count=SCENE_NATIVE_DYNSYM_COUNT,
    )

    assert len(failures) == 1
    assert failures[0].name == "scene_native_exports"
    assert "LED_DRIVE_TYPE export is 0x000196e4/8" in failures[0].message


def test_scene_native_export_audit_reports_persistence_export_mismatch() -> None:
    symbols = dict(_scene_native_symbol_map())
    symbols["_PWM_Favor_Record_Handler"] = (0x000153D9, 456)

    failures = audit_scene_native_export_symbols(
        symbols,
        dynsym_count=SCENE_NATIVE_DYNSYM_COUNT,
    )

    assert len(failures) == 1
    assert failures[0].name == "scene_native_exports"
    assert "_PWM_Favor_Record_Handler export is 0x000153d9/456" in (
        failures[0].message
    )


def test_scene_native_code_anchor_audit_accepts_matching_values() -> None:
    assert audit_scene_native_code_anchor_values(
        _scene_native_code_anchor_map(),
    ) == []


def test_scene_native_code_anchor_audit_reports_hash_mismatch() -> None:
    values = dict(_scene_native_code_anchor_map())
    value, size, thumb, section, _sha256, first16, last16 = values[
        "hal_App_Opcode_Handler"
    ]
    values["hal_App_Opcode_Handler"] = (
        value,
        size,
        thumb,
        section,
        "0" * 64,
        first16,
        last16,
    )

    failures = audit_scene_native_code_anchor_values(values)

    assert len(failures) == 1
    assert failures[0].name == "scene_native_code_anchors"
    assert "hal_App_Opcode_Handler SHA-256" in failures[0].message


def test_scene_native_code_anchor_audit_reports_section_mismatch() -> None:
    values = dict(_scene_native_code_anchor_map())
    value, size, thumb, _section, sha256, first16, last16 = values[
        "API_IC_Scene_Set_Handler"
    ]
    values["API_IC_Scene_Set_Handler"] = (
        value,
        size,
        thumb,
        ".plt",
        sha256,
        first16,
        last16,
    )

    failures = audit_scene_native_code_anchor_values(values)

    assert len(failures) == 1
    assert failures[0].name == "scene_native_code_anchors"
    assert "API_IC_Scene_Set_Handler maps to" in failures[0].message


def test_sp802e_native_export_audit_accepts_matching_symbols() -> None:
    assert audit_sp802e_native_export_symbols(
        _sp802e_native_symbol_map(),
        dynsym_count=SP802E_NATIVE_DYNSYM_COUNT,
    ) == []


def test_sp802e_native_export_audit_reports_missing_symbol() -> None:
    symbols = dict(_sp802e_native_symbol_map())
    del symbols["set_effect_params"]

    failures = audit_sp802e_native_export_symbols(
        symbols,
        dynsym_count=SP802E_NATIVE_DYNSYM_COUNT,
    )

    assert len(failures) == 1
    assert failures[0].name == "sp802e_native_exports"
    assert "set_effect_params" in failures[0].message


def test_sp802e_native_export_audit_reports_detail_mismatch() -> None:
    symbols = dict(_sp802e_native_symbol_map())
    symbols["set_effect_params"] = (0x0000A4DD, 25)

    failures = audit_sp802e_native_export_symbols(
        symbols,
        dynsym_count=SP802E_NATIVE_DYNSYM_COUNT,
    )

    assert len(failures) == 1
    assert failures[0].name == "sp802e_native_exports"
    assert "set_effect_params export is 0x0000a4dd/25" in failures[0].message


def test_sp630e_native_export_audit_accepts_matching_symbols() -> None:
    assert audit_sp630e_native_export_symbols(
        _sp630e_native_symbol_map(),
        dynsym_count=SP630E_NATIVE_DYNSYM_COUNT,
    ) == []


def test_sp630e_native_export_audit_reports_missing_symbol() -> None:
    symbols = dict(_sp630e_native_symbol_map())
    del symbols["pwmEffect"]

    failures = audit_sp630e_native_export_symbols(
        symbols,
        dynsym_count=SP630E_NATIVE_DYNSYM_COUNT,
    )

    assert len(failures) == 1
    assert failures[0].name == "sp630e_native_exports"
    assert "pwmEffect" in failures[0].message


def test_sp630e_native_export_audit_reports_detail_mismatch() -> None:
    symbols = dict(_sp630e_native_symbol_map())
    symbols["pwmEffect"] = (0x00005436, 612)

    failures = audit_sp630e_native_export_symbols(
        symbols,
        dynsym_count=SP630E_NATIVE_DYNSYM_COUNT,
    )

    assert len(failures) == 1
    assert failures[0].name == "sp630e_native_exports"
    assert "pwmEffect export is 0x00005436/612" in failures[0].message


def test_apk_asset_package_inventory_classifies_every_ledger_bucket() -> None:
    profiles = apk_asset_package_profiles()
    roles = {profile.role for profile in profiles}

    assert profiles == APK_ASSET_PACKAGE_PROFILES
    assert len(profiles) == 22
    assert sum(profile.expected_asset_count for profile in profiles) == 1218
    assert roles == {
        APKAssetPackageRole.CATALOG_DEVICE_PROFILE,
        APKAssetPackageRole.NON_CATALOG_FEATURE_PACKAGE,
        APKAssetPackageRole.SHARED_APP_SHELL,
        APKAssetPackageRole.SHARED_DEVICE_COMPONENT,
        APKAssetPackageRole.ROOT_SHARED_ASSET,
        APKAssetPackageRole.THIRD_PARTY_ASSET,
    }
    assert apk_asset_package_keys_by_role(
        APKAssetPackageRole.CATALOG_DEVICE_PROFILE
    ) == (
        "sp630e",
        "scene_ui",
        "module_sp801e",
        "sp802e",
        "car_lights",
        "fish_tank_lights",
        "accessories",
    )
    assert apk_asset_package_keys_by_role(
        APKAssetPackageRole.NON_CATALOG_FEATURE_PACKAGE
    ) == ("gundam_lights",)
    assert apk_asset_package_profile_for_key("common").summary.startswith(
        "Shared device controls"
    )
    assert apk_asset_package_profile_for_key("missing") is None
    assert apk_asset_package_profile_for_key(
        "assets/images"
    ).asset_file_name == "assets_assets_images.txt"


def test_gundam_profile_is_catalog_absent_feature_package() -> None:
    profiles = non_catalog_feature_package_profiles()
    spec = NON_CATALOG_FEATURE_PACKAGE_SPECS[0]
    description = "\n".join(
        describe_non_catalog_feature_package_profile(GUNDAM_PROFILE)
    )

    assert profiles == (GUNDAM_PROFILE,)
    assert GUNDAM_PROFILE.package == "packages/gundam_lights"
    assert GUNDAM_PROFILE.package_key == "gundam_lights"
    assert GUNDAM_PROFILE.package_asset_count == 177
    assert GUNDAM_PROFILE.asset_file_name == "assets_gundam_lights.txt"
    assert "/device/gundam_lights" in GUNDAM_PROFILE.route_hints
    assert "gundam_lights:effect_multi_colors" in GUNDAM_PROFILE.storage_hints
    assert "gundam" in GUNDAM_PROFILE.catalog_absent_terms
    assert not GUNDAM_PROFILE.command_protocol_known
    assert "catalog device: absent" in description
    assert "command protocol: unknown" in description
    assert spec.expected_package_count == GUNDAM_PROFILE.package_asset_count
    assert spec.required_assets == GUNDAM_PROFILE.required_assets
    assert spec.required_strings == (
        *GUNDAM_PROFILE.route_hints,
        *GUNDAM_PROFILE.storage_hints,
    )
    assert spec.forbidden_catalog_terms == GUNDAM_PROFILE.catalog_absent_terms


def test_apk_evidence_audit_reports_unclassified_asset_package() -> None:
    with TemporaryDirectory() as temp_dir:
        analysis_dir = Path(temp_dir)
        _write_analysis_dir(analysis_dir)
        counts = (
            (analysis_dir / "asset_package_counts.txt")
            .read_text(encoding="utf-8")
            .rstrip()
        )
        (analysis_dir / "asset_package_counts.txt").write_text(
            f"{counts}\n2 hidden_device_package\n",
            encoding="utf-8",
        )

        failures = audit_analysis_dir(analysis_dir)

        assert len(failures) == 1
        assert failures[0].name == "asset_package_inventory"
        assert "unclassified APK package keys" in failures[0].message
        assert "hidden_device_package" in failures[0].message


def test_apk_evidence_audit_reports_missing_shared_package_asset() -> None:
    with TemporaryDirectory() as temp_dir:
        analysis_dir = Path(temp_dir)
        _write_analysis_dir(analysis_dir)
        profile = apk_asset_package_profile_for_key("common")
        assert profile is not None
        assets = "\n".join(
            asset
            for asset in _full_inventory_assets(profile.key)
            if asset != "packages/common/assets/icons/ic_ble_mesh_group.png"
        )
        (analysis_dir / profile.asset_file_name).write_text(
            f"{assets}\n",
            encoding="utf-8",
        )

        failures = audit_analysis_dir(analysis_dir)

        assert len(failures) == 2
        assert all(failure.name == "asset_package_inventory" for failure in failures)
        assert any("has 90 assets" in failure.message for failure in failures)
        assert any(
            "packages/common/assets/icons/ic_ble_mesh_group.png" in failure.message
            for failure in failures
        )


def test_apk_evidence_audit_reports_package_count_mismatch() -> None:
    with TemporaryDirectory() as temp_dir:
        analysis_dir = Path(temp_dir)
        _write_analysis_dir(analysis_dir)
        mismatched_spec = EVIDENCE_SPECS[0]
        counts_path = analysis_dir / "asset_package_counts.txt"
        counts = counts_path.read_text(encoding="utf-8").replace(
            f"{mismatched_spec.expected_package_count} {mismatched_spec.package_key}",
            (
                f"{mismatched_spec.expected_package_count + 1} "
                f"{mismatched_spec.package_key}"
            ),
        )
        counts_path.write_text(counts, encoding="utf-8")

        failures = audit_analysis_dir(analysis_dir)

        assert len(failures) == 1
        assert failures[0].name == mismatched_spec.name
        assert "package count" in failures[0].message


def test_apk_evidence_audit_reports_missing_curated_assets() -> None:
    with TemporaryDirectory() as temp_dir:
        analysis_dir = Path(temp_dir)
        _write_analysis_dir(analysis_dir)
        mismatched_spec = EVIDENCE_SPECS[0]
        missing_asset = mismatched_spec.curated_assets[0]
        remaining_assets = "\n".join(
            (
                *mismatched_spec.curated_assets[1:],
                f"{mismatched_spec.package}/assets/replacement_asset.txt",
                *(
                    f"{mismatched_spec.package}/assets/audit_filler_{index}.txt"
                    for index in range(
                        mismatched_spec.expected_package_count
                        - len(mismatched_spec.curated_assets)
                    )
                ),
            )
        )
        (analysis_dir / mismatched_spec.asset_file_name).write_text(
            f"{remaining_assets}\n",
            encoding="utf-8",
        )

        failures = audit_analysis_dir(analysis_dir)

        assert len(failures) == 1
        assert failures[0].name == mismatched_spec.name
        assert missing_asset in failures[0].message


def test_apk_evidence_audit_reports_missing_curated_strings() -> None:
    with TemporaryDirectory() as temp_dir:
        analysis_dir = Path(temp_dir)
        _write_analysis_dir(analysis_dir)
        missing_string = "FavoriteStore0"
        mismatched_spec = next(
            spec for spec in EVIDENCE_SPECS if missing_string in spec.curated_strings
        )
        remaining_strings = "\n".join(
            (
                *(
                    string
                    for spec in EVIDENCE_SPECS
                    for string in spec.curated_strings
                    if string != missing_string
                ),
                *(
                    string
                    for spec in STRING_EVIDENCE_SPECS
                    for string in spec.curated_strings
                ),
            )
        )
        (analysis_dir / "libapp.strings.txt").write_text(
            f"{remaining_strings}\n",
            encoding="utf-8",
        )

        failures = audit_analysis_dir(analysis_dir)

        assert len(failures) == 1
        assert failures[0].name == mismatched_spec.name
        assert missing_string in failures[0].message


def test_apk_evidence_audit_reports_missing_string_evidence_spec() -> None:
    with TemporaryDirectory() as temp_dir:
        analysis_dir = Path(temp_dir)
        _write_analysis_dir(analysis_dir)
        missing_string = "/home/device/auth"
        mismatched_spec = next(
            spec
            for spec in STRING_EVIDENCE_SPECS
            if missing_string in spec.curated_strings
        )
        remaining_strings = "\n".join(
            (
                *(
                    string
                    for spec in EVIDENCE_SPECS
                    for string in spec.curated_strings
                ),
                *(
                    string
                    for spec in STRING_EVIDENCE_SPECS
                    for string in spec.curated_strings
                    if string != missing_string
                ),
            )
        )
        (analysis_dir / "libapp.strings.txt").write_text(
            f"{remaining_strings}\n",
            encoding="utf-8",
        )

        failures = audit_analysis_dir(analysis_dir)

        assert len(failures) == 1
        assert failures[0].name == mismatched_spec.name
        assert missing_string in failures[0].message


def test_apk_evidence_audit_reports_non_catalog_feature_package_leak() -> None:
    with TemporaryDirectory() as temp_dir:
        analysis_dir = Path(temp_dir)
        _write_analysis_dir(analysis_dir)
        spec = NON_CATALOG_FEATURE_PACKAGE_SPECS[0]
        (analysis_dir / "model_catalog.pretty.json").write_text(
            '[{"name": "Gundam", "home_uri": "/device/gundam_lights"}]',
            encoding="utf-8",
        )

        failures = audit_analysis_dir(analysis_dir)

        assert len(failures) == 1
        assert failures[0].name == spec.name
        assert "catalog-absent" in failures[0].message
