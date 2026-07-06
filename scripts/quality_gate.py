"""Run UniLED Next local release/readiness checks."""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from fnmatch import fnmatchcase
from pathlib import Path

try:
    from scripts.audit_legacy_uniled import audit_legacy_uniled
    from scripts.build_package import (
        FORBIDDEN_PACKAGE_SUFFIXES,
        iter_package_files,
        validate_package_files,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path.
    from audit_legacy_uniled import audit_legacy_uniled  # type: ignore[no-redef]
    from build_package import (  # type: ignore[no-redef]
        FORBIDDEN_PACKAGE_SUFFIXES,
        iter_package_files,
        validate_package_files,
    )

RUFF_TARGETS = (
    "custom_components/uniled",
    "scripts",
    "tests",
)

PYTEST_DEPENDENCIES = (
    "pytest",
    "pytest-asyncio",
    "pycryptodome",
)

APK_ANALYSIS_DIR = Path("..") / ".codex" / "rev" / "BanlanX_3.3.1-analysis"
APK_EXTRACTED_DIR = (
    Path("..")
    / ".codex"
    / "rev"
    / "BanlanX_3.3.1-extracted"
    / "config.armeabi_v7a-apk"
    / "lib"
    / "armeabi-v7a"
)

CONFIG_STEPS = ("user", "bluetooth_confirm", "zengge_cloud", "reconfigure")
OPTIONS_STEPS = ("zengge_cloud",)
CONFIG_ABORT_KEYS = (
    "already_configured",
    "invalid_address",
    "invalid_host",
    "mesh_not_supported",
    "not_connectable",
    "reconfigure_successful",
    "required",
    "unknown_model",
    "unknown_model_id",
    "unsupported_ble_transport",
    "unsupported_lan_transport",
)
CONFIG_ERROR_KEYS = (
    "invalid_address",
    "invalid_host",
    "invalid_model_id",
    "invalid_mesh_node_id",
    "invalid_mesh_node_type",
    "invalid_mesh_node_wiring",
    "invalid_mesh_uuid",
    "mesh_fetch",
    "mesh_identity_mismatch",
    "mesh_login",
    "mesh_no_devices",
    "mesh_not_supported",
    "required",
    "unknown_model",
    "unknown_model_id",
    "unsupported_ble_transport",
    "unsupported_lan_transport",
    "unsupported_mesh_transport",
    "unsupported_transport",
)
OPTIONS_ERROR_KEYS = (
    "mesh_fetch",
    "mesh_login",
    "mesh_no_devices",
    "mesh_not_supported",
    "required",
    "unsupported_mesh_transport",
)
ISSUE_KEYS = ("migration_failed", "setup_invalid")
LEGACY_SET_STATE_FIELDS = (
    "power",
    "effect",
    "effect_speed",
    "effect_length",
    "effect_direction",
    "effect_loop",
    "effect_play",
    "sensitivity",
    "rgb_color",
    "rgb2_color",
    "rgbw_color",
    "rgbww_color",
    "white",
    "brightness",
    "transition",
    "color_temp_kelvin",
)


class GateError(RuntimeError):
    """Raised when a quality gate fails."""


def run_quality_gate(args: argparse.Namespace) -> int:
    """Run the selected quality gates."""
    project_root = Path(__file__).resolve().parents[1]

    _validate_manifest(project_root)
    _validate_legacy_bluetooth_manifest_coverage(project_root, args.legacy_root)
    _validate_translations(project_root)
    _validate_services(project_root)
    _validate_config_flow_discovery_order(project_root)
    _validate_no_bundled_image_assets(project_root)
    _validate_package_file_list(project_root)
    _check_support_matrix_fresh(project_root)
    _run_legacy_audit(project_root, args.legacy_root)

    if not args.skip_apk_audit:
        _run_apk_audit_if_available(project_root)
    if not args.skip_ruff:
        _run_ruff(project_root)
    if not args.skip_pytest:
        _run_pytest(project_root)

    print("UniLED Next quality gate passed")
    return 0


def _validate_manifest(project_root: Path) -> None:
    manifest_path = project_root / "custom_components" / "uniled" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    _require(manifest.get("domain") == "uniled", "manifest domain must be uniled")
    _require(manifest.get("name"), "manifest name is required")
    _require(manifest.get("version"), "custom integration manifest version is required")
    _require(
        manifest.get("config_flow") is True,
        "manifest must declare config_flow=true",
    )
    _require(
        manifest.get("integration_type") == "hub",
        "manifest integration_type must be hub",
    )
    _require(
        manifest.get("iot_class") == "local_polling",
        "manifest iot_class must be local_polling",
    )
    _require(
        "bluetooth_adapters" in manifest.get("dependencies", ()),
        "manifest must depend on bluetooth_adapters",
    )
    _require(
        "pycryptodome>=3.17" in manifest.get("requirements", ()),
        "manifest must declare pycryptodome for Zengge mesh crypto",
    )
    _validate_bluetooth_matchers(manifest)
    _validate_catalog_bluetooth_manifest_coverage(project_root, manifest)
    print("manifest: ok")


def _validate_translations(project_root: Path) -> None:
    translations_path = (
        project_root / "custom_components" / "uniled" / "translations" / "en.json"
    )
    translations = json.loads(translations_path.read_text(encoding="utf-8"))

    _require(translations.get("title") == "UniLED Next", "translation title mismatch")
    for step in CONFIG_STEPS:
        _require(
            _translation_path(translations, "config", "step", step) is not None,
            f"missing config step translation {step}",
        )
    for step in OPTIONS_STEPS:
        _require(
            _translation_path(translations, "options", "step", step) is not None,
            f"missing options step translation {step}",
        )
    for key in CONFIG_ABORT_KEYS:
        _require(
            _translation_path(translations, "config", "abort", key) is not None,
            f"missing config abort translation {key}",
        )
    for key in CONFIG_ERROR_KEYS:
        _require(
            _translation_path(translations, "config", "error", key) is not None,
            f"missing config error translation {key}",
        )
    for key in OPTIONS_ERROR_KEYS:
        _require(
            _translation_path(translations, "options", "error", key) is not None,
            f"missing options error translation {key}",
        )
    for key in ISSUE_KEYS:
        issue = _translation_path(translations, "issues", key)
        _require(isinstance(issue, dict), f"missing issue translation {key}")
        assert isinstance(issue, dict)
        _require(issue.get("title"), f"missing issue title {key}")
        _require(issue.get("description"), f"missing issue description {key}")

    print("translations: ok")


def _validate_services(project_root: Path) -> None:
    services_path = project_root / "custom_components" / "uniled" / "services.yaml"
    services_text = services_path.read_text(encoding="utf-8")

    _require("set_state:" in services_text, "services.yaml must define set_state")
    fields = _yaml_section_child_keys(services_text, section="fields", indent=4)
    missing = tuple(field for field in LEGACY_SET_STATE_FIELDS if field not in fields)
    extra = tuple(field for field in fields if field not in LEGACY_SET_STATE_FIELDS)
    _require(not missing, f"services.yaml missing set_state fields: {missing}")
    _require(not extra, f"services.yaml has unexpected set_state fields: {extra}")

    print("services: ok")


def _validate_config_flow_discovery_order(project_root: Path) -> None:
    """Validate config-flow ordering for discovery and duplicate guards."""
    config_flow_path = (
        project_root / "custom_components" / "uniled" / "config_flow.py"
    )
    module = ast.parse(config_flow_path.read_text(encoding="utf-8"))

    for method_name in (
        "async_step_user",
        "async_step_bluetooth",
        "async_step_discovery",
    ):
        call_lines = _config_flow_method_call_lines(
            module,
            class_name="UniLEDConfigFlow",
            method_name=method_name,
        )
        compat_line = _first_call_line(
            call_lines,
            "_async_abort_if_compat_unique_id_configured",
        )
        set_unique_line = _first_call_line(call_lines, "async_set_unique_id")
        create_entry_line = _first_call_line(call_lines, "async_create_entry")

        _require(
            compat_line is not None,
            f"{method_name} must check legacy-compatible unique IDs",
        )
        _require(
            set_unique_line is not None,
            f"{method_name} must set a config-flow unique ID",
        )
        _require(
            create_entry_line is not None,
            f"{method_name} must create a config entry after validation",
        )
        assert compat_line is not None
        assert set_unique_line is not None
        assert create_entry_line is not None
        _require(
            compat_line < set_unique_line,
            f"{method_name} must check legacy-compatible IDs before unique ID setup",
        )
        _require(
            compat_line < create_entry_line,
            f"{method_name} must check legacy-compatible IDs before entry creation",
        )

    bluetooth_lines = _config_flow_method_call_lines(
        module,
        class_name="UniLEDConfigFlow",
        method_name="async_step_bluetooth",
    )
    compat_line = _first_call_line(
        bluetooth_lines,
        "_async_abort_if_compat_unique_id_configured",
    )
    confirmation_line = _first_call_line(
        bluetooth_lines,
        "setup_entry_requires_discovery_confirmation",
    )
    _require(
        confirmation_line is not None,
        "Bluetooth discovery must keep the catalog-only confirmation gate",
    )
    assert compat_line is not None
    assert confirmation_line is not None
    _require(
        compat_line < confirmation_line,
        "Bluetooth discovery must dedupe before catalog-only confirmation",
    )
    bluetooth_create_entry_line = _first_call_line(
        bluetooth_lines,
        "async_create_entry",
    )
    _require(
        bluetooth_create_entry_line is not None,
        "Bluetooth discovery must create entries after validation",
    )
    assert bluetooth_create_entry_line is not None
    _require(
        confirmation_line < bluetooth_create_entry_line,
        "Bluetooth discovery must check confirmation before entry creation",
    )

    for method_name in (
        "async_step_bluetooth_confirm",
        "async_step_zengge_cloud",
        "_async_import_zengge_cloud",
    ):
        call_lines = _config_flow_method_call_lines(
            module,
            class_name="UniLEDConfigFlow",
            method_name=method_name,
        )
        guard_line = _first_call_line(
            call_lines,
            "_async_abort_if_setup_unique_id_configured",
        )
        create_entry_line = _first_call_line(call_lines, "async_create_entry")
        _require(
            guard_line is not None,
            f"{method_name} must recheck duplicate IDs before delayed entry creation",
        )
        _require(
            create_entry_line is not None,
            f"{method_name} must create a config entry after delayed validation",
        )
        assert guard_line is not None
        assert create_entry_line is not None
        _require(
            guard_line < create_entry_line,
            f"{method_name} must recheck duplicate IDs before entry creation",
        )

    print("config-flow discovery order: ok")


def _validate_no_bundled_image_assets(project_root: Path) -> None:
    integration_root = project_root / "custom_components" / "uniled"
    image_suffixes = FORBIDDEN_PACKAGE_SUFFIXES - {".pyc", ".pyo"}
    image_assets = tuple(
        path.relative_to(project_root)
        for path in integration_root.rglob("*")
        if path.is_file() and path.suffix.casefold() in image_suffixes
    )
    _require(
        not image_assets,
        "integration must not bundle image/logo assets: "
        + ", ".join(path.as_posix() for path in image_assets),
    )
    print("bundled image assets: none")


def _validate_package_file_list(project_root: Path) -> None:
    files = iter_package_files(project_root)
    validate_package_files(files)
    _require(files, "package file list must not be empty")
    print(f"package file list: ok ({len(files)} files)")


def _validate_bluetooth_matchers(manifest: dict[str, object]) -> None:
    bluetooth = manifest.get("bluetooth")
    _require(isinstance(bluetooth, list) and bluetooth, "bluetooth matchers required")
    assert isinstance(bluetooth, list)

    local_names: list[str] = []
    manufacturer_ids: set[int] = set()
    for matcher in bluetooth:
        _require(isinstance(matcher, dict), "bluetooth matcher must be an object")
        assert isinstance(matcher, dict)
        _require(
            matcher.get("connectable") is True,
            "all bluetooth matchers must be connectable",
        )
        local_name = matcher.get("local_name")
        if isinstance(local_name, str):
            local_names.append(local_name)
            _require(local_name != "SP*", "broad SP* matcher is unsafe")
            _require(
                not _has_pattern(local_name[:3]),
                f"local_name matcher {local_name!r} has wildcard in first 3 chars",
            )
        manufacturer_id = matcher.get("manufacturer_id")
        if isinstance(manufacturer_id, int):
            manufacturer_ids.add(manufacturer_id)

    for required in ("SP1*", "SP3*", "SP5*", "SP6*", "SP7*", "RG4"):
        _require(required in local_names, f"missing bluetooth matcher {required}")
    for required in (0x5053, 5053):
        _require(
            required in manufacturer_ids,
            f"missing BanlanX manufacturer-data matcher {required}",
        )


def _validate_catalog_bluetooth_manifest_coverage(
    project_root: Path,
    manifest: dict[str, object],
) -> None:
    """Validate bounded matchers wake every user-facing BLE/BLE-mesh model."""
    patterns = _bluetooth_local_name_patterns(manifest)
    names = tuple(
        str(model["name"])
        for model in _user_facing_catalog_models(project_root)
        if "ble" in model.get("transports", ())
        or "ble_mesh" in model.get("transports", ())
    )
    missing = tuple(
        name
        for name in names
        if not any(fnmatchcase(name, pattern) for pattern in patterns)
    )
    _require(
        not missing,
        "bluetooth manifest no longer wakes catalog BLE/BLE-mesh names: "
        + ", ".join(missing),
    )
    print(f"catalog bluetooth manifest coverage: ok ({len(names)} names)")


def _validate_legacy_bluetooth_manifest_coverage(
    project_root: Path,
    legacy_root: Path,
) -> None:
    manifest_path = project_root / "custom_components" / "uniled" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    patterns = _bluetooth_local_name_patterns(manifest)
    audit = audit_legacy_uniled(legacy_root)
    missing = tuple(
        name
        for name in audit.legacy_ble_names
        if not any(fnmatchcase(name, pattern) for pattern in patterns)
    )
    _require(
        not missing,
        "bluetooth manifest no longer wakes old-UniLED BLE names: "
        + ", ".join(missing),
    )
    print(
        "legacy bluetooth manifest coverage: "
        f"ok ({len(audit.legacy_ble_names)} names)"
    )


def _bluetooth_local_name_patterns(manifest: dict[str, object]) -> tuple[str, ...]:
    bluetooth = manifest.get("bluetooth")
    assert isinstance(bluetooth, list)
    return tuple(
        matcher["local_name"]
        for matcher in bluetooth
        if isinstance(matcher, dict) and isinstance(matcher.get("local_name"), str)
    )


def _user_facing_catalog_models(project_root: Path) -> tuple[dict[str, object], ...]:
    catalog_path = (
        project_root
        / "custom_components"
        / "uniled"
        / "core"
        / "catalog"
        / "models.json"
    )
    raw_models = json.loads(catalog_path.read_text(encoding="utf-8"))
    _require(isinstance(raw_models, list), "catalog models.json must be a list")
    by_name: dict[str, list[dict[str, object]]] = {}
    for raw in raw_models:
        _require(isinstance(raw, dict), "catalog model rows must be objects")
        assert isinstance(raw, dict)
        name = str(raw.get("name", ""))
        _require(name, "catalog model row missing name")
        by_name.setdefault(name, []).append(raw)

    models: list[dict[str, object]] = []
    for name in sorted(by_name):
        model = sorted(by_name[name], key=_catalog_canonical_sort_key)[0]
        if model.get("support_level") != "filtered":
            models.append(model)
    return tuple(models)


def _catalog_canonical_sort_key(model: dict[str, object]) -> tuple[int, int, int]:
    return (
        int(model.get("support_level") == "filtered"),
        int(model.get("parent_id") is not None),
        int(model["model_id"]),
    )


def _config_flow_method_call_lines(
    module: ast.Module,
    *,
    class_name: str,
    method_name: str,
) -> dict[str, tuple[int, ...]]:
    """Return called names/attributes and line numbers for one method."""
    for statement in module.body:
        if not isinstance(statement, ast.ClassDef) or statement.name != class_name:
            continue
        for item in statement.body:
            if not isinstance(item, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            if item.name != method_name:
                continue
            call_lines: dict[str, list[int]] = {}
            for node in ast.walk(item):
                if not isinstance(node, ast.Call):
                    continue
                name = _call_name(node.func)
                if name is None:
                    continue
                call_lines.setdefault(name, []).append(node.lineno)
            return {
                name: tuple(sorted(lines))
                for name, lines in call_lines.items()
            }
    raise GateError(f"missing {class_name}.{method_name}")


def _call_name(node: ast.AST) -> str | None:
    """Return the function or method name for an AST call node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _first_call_line(
    call_lines: dict[str, tuple[int, ...]],
    call_name: str,
) -> int | None:
    """Return the first line number for a call, if present."""
    lines = call_lines.get(call_name, ())
    return lines[0] if lines else None


def _check_support_matrix_fresh(project_root: Path) -> None:
    expected_path = project_root / "docs" / "SUPPORT_MATRIX.md"
    with tempfile.TemporaryDirectory(prefix="uniled-quality-") as tmp:
        generated_path = Path(tmp) / "SUPPORT_MATRIX.md"
        _run(
            "support-matrix",
            (
                sys.executable,
                "scripts/generate_support_matrix.py",
                "--format",
                "markdown",
                "--output",
                str(generated_path),
            ),
            project_root,
        )
        expected = _normalized_text(expected_path)
        generated = _normalized_text(generated_path)
        _require(
            expected == generated,
            "docs/SUPPORT_MATRIX.md is stale; regenerate it before release",
        )
    print("support-matrix freshness: ok")


def _run_legacy_audit(project_root: Path, legacy_root: Path) -> None:
    _run(
        "legacy-audit",
        (
            sys.executable,
            "scripts/audit_legacy_uniled.py",
            "--legacy-root",
            str(legacy_root),
        ),
        project_root,
    )


def _run_apk_audit_if_available(project_root: Path) -> None:
    analysis_dir = project_root / APK_ANALYSIS_DIR
    if not analysis_dir.exists():
        print(f"apk-audit: skipped, missing {analysis_dir}")
        return

    command: list[str] = [
        sys.executable,
        "scripts/audit_apk_evidence.py",
        "--analysis-dir",
        str(APK_ANALYSIS_DIR),
    ]
    native_overrides = (
        ("--scene-native-lib", "libscene_lfx.so"),
        ("--sp802e-native-lib", "libwled_lfx.so"),
        ("--sp630e-native-lib", "liblfx.so"),
    )
    for option, filename in native_overrides:
        native_path = project_root / APK_EXTRACTED_DIR / filename
        if native_path.exists():
            command.extend((option, str(APK_EXTRACTED_DIR / filename)))

    _run("apk-audit", tuple(command), project_root)


def _run_ruff(project_root: Path) -> None:
    if shutil.which("uv"):
        command = ("uv", "run", "--no-project", "--with", "ruff", "ruff", "check")
    else:
        command = (sys.executable, "-m", "ruff", "check")
    _run("ruff", (*command, *RUFF_TARGETS), project_root)


def _run_pytest(project_root: Path) -> None:
    if shutil.which("uv"):
        command: tuple[str, ...] = ("uv", "run", "--no-project")
        for dependency in PYTEST_DEPENDENCIES:
            command = (*command, "--with", dependency)
        command = (*command, "python", "-m", "pytest", "-q")
    else:
        command = (sys.executable, "-m", "pytest", "-q")
    _run("pytest", command, project_root)


def _run(label: str, command: Sequence[str], cwd: Path) -> None:
    printable = " ".join(command)
    print(f"{label}: {printable}")
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise GateError(f"{label} failed with exit code {result.returncode}")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def _normalized_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _has_pattern(value: str) -> bool:
    return any(char in value for char in "*?[")


def _translation_path(data: object, *path: str) -> object | None:
    value = data
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _yaml_section_child_keys(
    text: str, *, section: str, indent: int
) -> tuple[str, ...]:
    section_prefix = f"{' ' * (indent - 2)}{section}:"
    child_prefix = " " * indent
    keys: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line == section_prefix:
            in_section = True
            continue
        if not in_section:
            continue
        if line and not line.startswith(child_prefix):
            break
        if not line.startswith(child_prefix) or line.startswith(child_prefix + " "):
            continue
        key, separator, _value = line.strip().partition(":")
        if separator and key:
            keys.append(key)
    return tuple(keys)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run UniLED Next readiness gates before HA deployment.",
    )
    parser.add_argument(
        "--legacy-root",
        type=Path,
        default=Path("..") / "uniled",
        help="Detached old UniLED checkout used for parity auditing.",
    )
    parser.add_argument(
        "--skip-apk-audit",
        action="store_true",
        help="Skip local APK evidence audit even if analysis artifacts exist.",
    )
    parser.add_argument(
        "--skip-ruff",
        action="store_true",
        help="Skip Ruff linting.",
    )
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Skip pytest.",
    )
    return parser


def main() -> int:
    """Run the command-line entry point."""
    args = _parser().parse_args()
    try:
        return run_quality_gate(args)
    except GateError as exc:
        print(f"quality gate failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
