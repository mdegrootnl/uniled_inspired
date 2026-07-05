"""Home Assistant registry audit tests."""

from __future__ import annotations

from scripts.audit_ha_uniled_registry import audit_uniled_registry


def test_audit_uniled_registry_marks_only_unreferenced_old_identifier_rows() -> None:
    """Stale registry rows have old identifiers and no attached entities."""
    config_entries = {
        "data": {
            "entries": [
                {
                    "domain": "uniled",
                    "entry_id": "entry-1",
                    "title": "SP541E",
                    "unique_id": "54:20:24:11:1f:77",
                    "data": {
                        "model": "SP541E",
                        "transport": "lan",
                        "host": "192.168.0.82",
                    },
                }
            ]
        }
    }
    device_registry = {
        "data": {
            "devices": [
                {
                    "id": "old-device",
                    "config_entries": ["entry-1"],
                    "identifiers": [["uniled", "old-entry-row"]],
                    "connections": [["mac", "54:20:24:11:1f:77"]],
                },
                {
                    "id": "current-device",
                    "config_entries": ["entry-1"],
                    "identifiers": [["uniled", "54:20:24:11:1f:77"]],
                    "connections": [["mac", "54:20:24:11:1f:77"]],
                },
                {
                    "id": "old-device-with-entity",
                    "config_entries": ["entry-1"],
                    "identifiers": [["uniled", "entry-id-derived"]],
                    "connections": [["mac", "54:20:24:11:1f:77"]],
                },
                {
                    "id": "old-device-disabled-only",
                    "config_entries": ["entry-1"],
                    "identifiers": [["uniled", "disabled-entry-row"]],
                    "connections": [["mac", "54:20:24:11:1f:77"]],
                },
            ]
        }
    }
    entity_registry = {
        "data": {
            "entities": [
                {
                    "entity_id": "light.raam_strip",
                    "device_id": "current-device",
                },
                {
                    "entity_id": "sensor.legacy_still_attached",
                    "device_id": "old-device-with-entity",
                },
                {
                    "entity_id": "sensor.legacy_disabled",
                    "device_id": "old-device-disabled-only",
                    "disabled_by": "integration",
                },
            ]
        }
    }

    rows = audit_uniled_registry(config_entries, device_registry, entity_registry)
    stale = tuple(row for row in rows if row.stale)
    disabled_only = tuple(row for row in rows if row.held_only_by_disabled_entities)

    assert len(rows) == 4
    assert [row.device_id for row in stale] == ["old-device"]
    assert [row.device_id for row in disabled_only] == ["old-device-disabled-only"]
    assert rows[1].active_entity_ids == ("light.raam_strip",)
    assert rows[2].stale is False
    assert rows[3].disabled_entity_ids == ("sensor.legacy_disabled",)
