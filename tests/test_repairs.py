"""Repair issue helper tests."""

from __future__ import annotations

import asyncio
import sys
import types
from typing import Any

from custom_components import uniled
from custom_components.uniled.const import (
    CONF_ADDRESS,
    CONF_DEVICE_ID,
    CONF_MODEL,
    CONF_MODEL_ID,
    CONF_TRANSPORT,
    CONFIG_ENTRY_MINOR_VERSION,
    CONFIG_ENTRY_VERSION,
    DOMAIN,
    TRANSPORT_BLE,
    TRANSPORT_MANUAL,
)


class _IssueSeverity:
    ERROR = "error"


class _ConfigEntries:
    def __init__(self) -> None:
        self.updates: list[tuple[Any, dict[str, Any]]] = []
        self.forwarded: list[tuple[Any, tuple[str, ...]]] = []
        self.unloaded: list[tuple[Any, tuple[str, ...]]] = []
        self.forward_error: Exception | None = None
        self.unload_result = True

    def async_update_entry(self, entry: Any, **kwargs: Any) -> None:
        self.updates.append((entry, kwargs))

    async def async_forward_entry_setups(
        self,
        entry: Any,
        platforms: list[str],
    ) -> None:
        self.forwarded.append((entry, tuple(platforms)))
        if self.forward_error is not None:
            raise self.forward_error

    async def async_unload_platforms(
        self,
        entry: Any,
        platforms: list[str],
    ) -> bool:
        self.unloaded.append((entry, tuple(platforms)))
        return self.unload_result


class _Hass:
    def __init__(self) -> None:
        self.config_entries = _ConfigEntries()

    async def async_add_executor_job(self, func: Any, *args: Any) -> Any:
        return func(*args)


def _install_issue_registry(
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]],
    deletes: list[tuple[Any, ...]],
) -> dict[str, Any]:
    def async_create_issue(*args: Any, **kwargs: Any) -> None:
        calls.append((args, kwargs))

    def async_delete_issue(*args: Any, **kwargs: Any) -> None:
        deletes.append(args)

    issue_registry = types.SimpleNamespace(
        IssueSeverity=_IssueSeverity,
        async_create_issue=async_create_issue,
        async_delete_issue=async_delete_issue,
    )
    helpers = types.ModuleType("homeassistant.helpers")
    helpers.issue_registry = issue_registry
    homeassistant = types.ModuleType("homeassistant")
    homeassistant.helpers = helpers
    old_modules = {
        name: sys.modules.get(name)
        for name in (
            "homeassistant",
            "homeassistant.helpers",
            "homeassistant.helpers.issue_registry",
        )
    }
    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.issue_registry"] = issue_registry
    return old_modules


def _restore_modules(old_modules: dict[str, Any]) -> None:
    for name, module in old_modules.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


def _install_fake_coordinator(
    *,
    fail_on_init: bool = True,
    refresh_error: Exception | None = None,
    instances: list[Any] | None = None,
) -> dict[str, Any]:
    module_name = "custom_components.uniled.coordinator"
    old_modules = {module_name: sys.modules.get(module_name)}

    class FakeCoordinator:
        def __init__(self, hass: Any, entry: Any, runtime: Any) -> None:
            if fail_on_init:
                raise AssertionError("invalid setup must not create a coordinator")
            self.hass = hass
            self.entry = entry
            self.runtime = runtime
            self.first_refreshes = 0
            if instances is not None:
                instances.append(self)

        async def async_config_entry_first_refresh(self) -> None:
            self.first_refreshes += 1
            if refresh_error is not None:
                raise refresh_error

        def apply_notification(self, _data: bytes) -> None:
            return None

        def apply_mesh_notification(self, _data: bytes) -> None:
            return None

    fake_module = types.ModuleType(module_name)
    fake_module.UniLEDCoordinator = FakeCoordinator
    sys.modules[module_name] = fake_module
    return old_modules


class _RuntimeData:
    def __init__(self) -> None:
        self.closed = 0

    async def async_close(self) -> None:
        self.closed += 1


def test_create_config_entry_issue_uses_stable_issue_data() -> None:
    """Repair issues use stable IDs and sanitized placeholders."""
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    deletes: list[tuple[Any, ...]] = []
    old_modules = _install_issue_registry(calls, deletes)
    entry = types.SimpleNamespace(entry_id="abc123", title="Kitchen strip")
    try:
        uniled._create_config_entry_issue(
            object(),
            entry,
            "setup_invalid",
            field="model",
            reason="unknown_model",
        )
        uniled._delete_config_entry_issue(object(), entry, "setup_invalid")
    finally:
        _restore_modules(old_modules)

    assert calls[0][0][1:] == (DOMAIN, "setup_invalid_abc123")
    assert calls[0][1]["data"] == {
        "entry_id": "abc123",
        "field": "model",
        "reason": "unknown_model",
    }
    assert calls[0][1]["is_fixable"] is False
    assert calls[0][1]["severity"] == _IssueSeverity.ERROR
    assert calls[0][1]["translation_key"] == "setup_invalid"
    assert calls[0][1]["translation_placeholders"] == {
        "field": "model",
        "reason": "unknown_model",
        "title": "Kitchen strip",
    }
    assert deletes[0][1:] == (DOMAIN, "setup_invalid_abc123")


def test_async_migrate_entry_updates_version_and_preserves_unique_id() -> None:
    """Migration applies normalized data without changing old entry unique IDs."""
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    deletes: list[tuple[Any, ...]] = []
    old_modules = _install_issue_registry(calls, deletes)
    hass = _Hass()
    entry = types.SimpleNamespace(
        entry_id="legacy_ble",
        title="Legacy strip",
        unique_id="AA:BB:CC:DD:EE:10",
        data={
            CONF_TRANSPORT: "ble",
            CONF_MODEL: "SP601E",
            CONF_ADDRESS: "AA:BB:CC:DD:EE:10",
        },
    )
    try:
        migrated = asyncio.run(uniled.async_migrate_entry(hass, entry))
    finally:
        _restore_modules(old_modules)

    assert migrated is True
    assert calls == []
    assert deletes[0][1:] == (DOMAIN, "migration_failed_legacy_ble")
    assert hass.config_entries.updates == [
        (
            entry,
            {
                "data": {
                    CONF_MODEL: "SP601E",
                    CONF_MODEL_ID: 1,
                    CONF_ADDRESS: "AA:BB:CC:DD:EE:10",
                    CONF_TRANSPORT: TRANSPORT_BLE,
                },
                "version": CONFIG_ENTRY_VERSION,
                "minor_version": CONFIG_ENTRY_MINOR_VERSION,
            },
        )
    ]
    assert "unique_id" not in hass.config_entries.updates[0][1]
    assert entry.unique_id == "AA:BB:CC:DD:EE:10"


def test_async_migrate_entry_creates_repair_on_invalid_legacy_data() -> None:
    """Unsafe legacy data produces a sanitized migration repair issue."""
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    deletes: list[tuple[Any, ...]] = []
    old_modules = _install_issue_registry(calls, deletes)
    hass = _Hass()
    entry = types.SimpleNamespace(
        entry_id="bad_ble",
        title="Broken legacy strip",
        unique_id="AA:BB:CC:DD:EE:11",
        data={CONF_TRANSPORT: "ble", CONF_MODEL: "SP601E"},
    )
    try:
        migrated = asyncio.run(uniled.async_migrate_entry(hass, entry))
    finally:
        _restore_modules(old_modules)

    assert migrated is False
    assert hass.config_entries.updates == []
    assert deletes == []
    assert calls[0][0][1:] == (DOMAIN, "migration_failed_bad_ble")
    assert calls[0][1]["data"] == {
        "entry_id": "bad_ble",
        "field": CONF_ADDRESS,
        "reason": "required",
    }
    assert calls[0][1]["is_fixable"] is False
    assert calls[0][1]["severity"] == _IssueSeverity.ERROR
    assert calls[0][1]["translation_key"] == "migration_failed"


def test_async_setup_entry_creates_repair_on_invalid_runtime_data() -> None:
    """Invalid stored data creates a setup repair and skips platform forwarding."""
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    deletes: list[tuple[Any, ...]] = []
    old_modules = _install_issue_registry(calls, deletes)
    coordinator_modules = _install_fake_coordinator()
    hass = _Hass()
    entry = types.SimpleNamespace(
        entry_id="bad_setup",
        title="Broken setup",
        unique_id="bad",
        data={CONF_MODEL: "NOPE"},
    )
    try:
        setup_ok = asyncio.run(uniled.async_setup_entry(hass, entry))
    finally:
        _restore_modules(coordinator_modules)
        _restore_modules(old_modules)

    assert setup_ok is False
    assert not hasattr(entry, "runtime_data")
    assert hass.config_entries.updates == []
    assert hass.config_entries.forwarded == []
    assert deletes == []
    assert calls[0][0][1:] == (DOMAIN, "setup_invalid_bad_setup")
    assert calls[0][1]["data"] == {
        "entry_id": "bad_setup",
        "field": CONF_MODEL,
        "reason": "unknown_model",
    }
    assert calls[0][1]["is_fixable"] is False
    assert calls[0][1]["severity"] == _IssueSeverity.ERROR
    assert calls[0][1]["translation_key"] == "setup_invalid"


def test_async_setup_entry_sets_runtime_and_forwards_platforms() -> None:
    """Valid stored data clears setup repairs, refreshes, and forwards platforms."""
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    deletes: list[tuple[Any, ...]] = []
    coordinator_instances: list[Any] = []
    old_modules = _install_issue_registry(calls, deletes)
    coordinator_modules = _install_fake_coordinator(
        fail_on_init=False,
        instances=coordinator_instances,
    )
    hass = _Hass()
    entry = types.SimpleNamespace(
        entry_id="valid_setup",
        title="Bench setup",
        unique_id="manual:SP601E:bench",
        data={
            CONF_MODEL: "SP601E",
            CONF_MODEL_ID: 1,
            CONF_DEVICE_ID: "bench",
            CONF_TRANSPORT: TRANSPORT_MANUAL,
        },
    )
    try:
        setup_ok = asyncio.run(uniled.async_setup_entry(hass, entry))
    finally:
        _restore_modules(coordinator_modules)
        _restore_modules(old_modules)

    assert setup_ok is True
    assert calls == []
    assert deletes[0][1:] == (DOMAIN, "setup_invalid_valid_setup")
    assert len(coordinator_instances) == 1
    coordinator = coordinator_instances[0]
    assert coordinator.first_refreshes == 1
    assert coordinator.runtime is entry.runtime_data
    assert entry.runtime_data.coordinator is coordinator
    assert entry.runtime_data.model.name == "SP601E"
    assert hass.config_entries.forwarded == [(entry, tuple(uniled.PLATFORMS))]


def test_async_setup_entry_closes_runtime_when_first_refresh_fails() -> None:
    """Failed first refresh closes runtime resources before HA retries setup."""
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    deletes: list[tuple[Any, ...]] = []
    coordinator_instances: list[Any] = []
    old_modules = _install_issue_registry(calls, deletes)
    coordinator_modules = _install_fake_coordinator(
        fail_on_init=False,
        refresh_error=RuntimeError("refresh failed"),
        instances=coordinator_instances,
    )
    hass = _Hass()
    entry = types.SimpleNamespace(
        entry_id="refresh_failed",
        title="Refresh setup",
        unique_id="manual:SP601E:refresh",
        data={
            CONF_MODEL: "SP601E",
            CONF_MODEL_ID: 1,
            CONF_DEVICE_ID: "refresh",
            CONF_TRANSPORT: TRANSPORT_MANUAL,
        },
    )
    try:
        try:
            asyncio.run(uniled.async_setup_entry(hass, entry))
        except RuntimeError as ex:
            assert str(ex) == "refresh failed"
        else:
            raise AssertionError("setup should raise the first-refresh failure")
    finally:
        _restore_modules(coordinator_modules)
        _restore_modules(old_modules)

    assert calls == []
    assert deletes[0][1:] == (DOMAIN, "setup_invalid_refresh_failed")
    assert len(coordinator_instances) == 1
    coordinator = coordinator_instances[0]
    assert coordinator.first_refreshes == 1
    assert coordinator.runtime.coordinator is None
    assert not hasattr(entry, "runtime_data")
    assert hass.config_entries.forwarded == []


def test_async_setup_entry_closes_runtime_when_platform_forwarding_fails() -> None:
    """Failed platform forwarding closes runtime resources before setup retry."""
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    deletes: list[tuple[Any, ...]] = []
    coordinator_instances: list[Any] = []
    old_modules = _install_issue_registry(calls, deletes)
    coordinator_modules = _install_fake_coordinator(
        fail_on_init=False,
        instances=coordinator_instances,
    )
    hass = _Hass()
    hass.config_entries.forward_error = RuntimeError("forward failed")
    entry = types.SimpleNamespace(
        entry_id="forward_failed",
        title="Forward setup",
        unique_id="manual:SP601E:forward",
        data={
            CONF_MODEL: "SP601E",
            CONF_MODEL_ID: 1,
            CONF_DEVICE_ID: "forward",
            CONF_TRANSPORT: TRANSPORT_MANUAL,
        },
    )
    try:
        try:
            asyncio.run(uniled.async_setup_entry(hass, entry))
        except RuntimeError as ex:
            assert str(ex) == "forward failed"
        else:
            raise AssertionError("setup should raise the platform-forwarding failure")
    finally:
        _restore_modules(coordinator_modules)
        _restore_modules(old_modules)

    assert calls == []
    assert deletes[0][1:] == (DOMAIN, "setup_invalid_forward_failed")
    assert len(coordinator_instances) == 1
    coordinator = coordinator_instances[0]
    assert coordinator.first_refreshes == 1
    assert coordinator.runtime.coordinator is None
    assert entry.runtime_data is None
    assert hass.config_entries.forwarded == [(entry, tuple(uniled.PLATFORMS))]


def test_async_unload_entry_closes_runtime_after_platform_unload() -> None:
    """Successful platform unload closes the runtime transport boundary."""
    hass = _Hass()
    runtime = _RuntimeData()
    entry = types.SimpleNamespace(entry_id="unload_ok", runtime_data=runtime)

    unloaded = asyncio.run(uniled.async_unload_entry(hass, entry))

    assert unloaded is True
    assert hass.config_entries.unloaded == [(entry, tuple(uniled.PLATFORMS))]
    assert runtime.closed == 1


def test_async_unload_entry_keeps_runtime_open_when_platform_unload_fails() -> None:
    """Failed platform unload leaves runtime resources open for retry/recovery."""
    hass = _Hass()
    hass.config_entries.unload_result = False
    runtime = _RuntimeData()
    entry = types.SimpleNamespace(entry_id="unload_failed", runtime_data=runtime)

    unloaded = asyncio.run(uniled.async_unload_entry(hass, entry))

    assert unloaded is False
    assert hass.config_entries.unloaded == [(entry, tuple(uniled.PLATFORMS))]
    assert runtime.closed == 0
