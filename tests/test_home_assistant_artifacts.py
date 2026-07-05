"""Home Assistant artifact consistency tests."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.quality_gate import (
    CONFIG_ABORT_KEYS,
    CONFIG_ERROR_KEYS,
    CONFIG_STEPS,
    ISSUE_KEYS,
    LEGACY_SET_STATE_FIELDS,
    OPTIONS_ERROR_KEYS,
    OPTIONS_STEPS,
    _translation_path,
    _validate_catalog_bluetooth_manifest_coverage,
    _validate_config_flow_discovery_order,
    _validate_legacy_bluetooth_manifest_coverage,
    _yaml_section_child_keys,
)


def test_translations_cover_config_flow_and_repair_keys() -> None:
    """Config flow and repair reason keys have user-facing translations."""
    translations = json.loads(
        Path("custom_components/uniled/translations/en.json").read_text(
            encoding="utf-8"
        )
    )

    assert translations["title"] == "UniLED Next"
    for step in CONFIG_STEPS:
        assert _translation_path(translations, "config", "step", step) is not None
    for step in OPTIONS_STEPS:
        assert _translation_path(translations, "options", "step", step) is not None
    for key in CONFIG_ABORT_KEYS:
        assert _translation_path(translations, "config", "abort", key)
    for key in CONFIG_ERROR_KEYS:
        assert _translation_path(translations, "config", "error", key)
    for key in OPTIONS_ERROR_KEYS:
        assert _translation_path(translations, "options", "error", key)
    for key in ISSUE_KEYS:
        issue = _translation_path(translations, "issues", key)
        assert isinstance(issue, dict)
        assert issue["title"]
        assert issue["description"]


def test_services_yaml_matches_legacy_set_state_fields() -> None:
    """The legacy set_state service advertises every accepted service field."""
    services_text = Path("custom_components/uniled/services.yaml").read_text(
        encoding="utf-8"
    )

    fields = _yaml_section_child_keys(services_text, section="fields", indent=4)

    assert fields == LEGACY_SET_STATE_FIELDS


def test_quality_gate_checks_old_uniled_manifest_coverage() -> None:
    """Release gate fails if old-UniLED BLE names can no longer wake discovery."""
    _validate_legacy_bluetooth_manifest_coverage(
        Path.cwd(),
        Path("..") / "uniled",
    )


def test_quality_gate_checks_catalog_bluetooth_manifest_coverage() -> None:
    """Release gate fails if catalog BLE names can no longer wake discovery."""
    manifest = json.loads(
        Path("custom_components/uniled/manifest.json").read_text(encoding="utf-8")
    )

    _validate_catalog_bluetooth_manifest_coverage(Path.cwd(), manifest)


def test_config_flow_loads_catalog_through_executor() -> None:
    """Config/discovery flows avoid blocking catalog reads on the HA loop."""
    source = Path("custom_components/uniled/config_flow.py").read_text(
        encoding="utf-8"
    )

    assert "default_catalog()" not in source
    assert "async_add_executor_job(default_catalog)" in source


def test_config_flow_checks_legacy_compatible_unique_ids() -> None:
    """Old-UniLED IDs still block duplicate setup before entry creation."""
    _validate_config_flow_discovery_order(Path.cwd())


def test_platform_entities_apply_planner_enabled_defaults() -> None:
    """HA platform entities must honor FeatureSpec.enabled_by_default."""
    platform_files = (
        "button.py",
        "light.py",
        "number.py",
        "scene.py",
        "select.py",
        "sensor.py",
        "switch.py",
    )

    for filename in platform_files:
        source = Path("custom_components/uniled", filename).read_text(
            encoding="utf-8"
        )

        assert "entity_registry_enabled_default" in source, filename
        assert "_attr_entity_registry_enabled_default" in source, filename
