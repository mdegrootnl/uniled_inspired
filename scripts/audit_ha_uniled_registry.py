"""Audit Home Assistant registry rows for stale UniLED device identities."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from custom_components.uniled.const import DOMAIN  # noqa: E402
from custom_components.uniled.entity_metadata import entry_data_identity  # noqa: E402


@dataclass(frozen=True, slots=True)
class RegistryAuditRow:
    """A UniLED config-entry/device-registry relationship found in HA storage."""

    entry_id: str
    title: str
    expected_identifier: str
    device_id: str
    identifiers: tuple[tuple[str, str], ...]
    connections: tuple[tuple[str, str], ...]
    active_entity_ids: tuple[str, ...]
    disabled_entity_ids: tuple[str, ...]

    @property
    def stale(self) -> bool:
        """Return whether this looks like an obsolete UniLED device row."""
        return (
            (DOMAIN, self.expected_identifier) not in self.identifiers
            and not self.active_entity_ids
            and not self.disabled_entity_ids
        )

    @property
    def held_only_by_disabled_entities(self) -> bool:
        """Return whether only disabled entity-registry rows keep this device."""
        return (
            (DOMAIN, self.expected_identifier) not in self.identifiers
            and not self.active_entity_ids
            and bool(self.disabled_entity_ids)
        )


def audit_uniled_registry(
    config_entries_storage: Mapping[str, Any],
    device_registry_storage: Mapping[str, Any],
    entity_registry_storage: Mapping[str, Any],
) -> tuple[RegistryAuditRow, ...]:
    """Return UniLED device-registry rows with current/stale classification."""
    entries = tuple(_storage_rows(config_entries_storage, "entries"))
    devices = tuple(_storage_rows(device_registry_storage, "devices"))
    entities = tuple(_storage_rows(entity_registry_storage, "entities"))
    active_by_device, disabled_by_device = _entities_by_device_id(entities)

    rows: list[RegistryAuditRow] = []
    for entry in entries:
        if str(entry.get("domain", "")).strip() != DOMAIN:
            continue
        entry_id = str(entry.get("entry_id", "")).strip()
        if not entry_id:
            continue
        expected_identifier = _entry_expected_identifier(entry)
        for device in devices:
            config_entry_ids = {
                str(value).strip() for value in _sequence(device.get("config_entries"))
            }
            if entry_id not in config_entry_ids:
                continue
            device_id = str(device.get("id", "")).strip()
            rows.append(
                RegistryAuditRow(
                    entry_id=entry_id,
                    title=str(entry.get("title", "")).strip(),
                    expected_identifier=expected_identifier,
                    device_id=device_id,
                    identifiers=_pairs(device.get("identifiers")),
                    connections=_pairs(device.get("connections")),
                    active_entity_ids=tuple(
                        sorted(active_by_device.get(device_id, ()))
                    ),
                    disabled_entity_ids=tuple(
                        sorted(disabled_by_device.get(device_id, ()))
                    ),
                )
            )
    return tuple(rows)


def _entry_expected_identifier(entry: Mapping[str, Any]) -> str:
    unique_id = str(entry.get("unique_id", "") or "").strip()
    if unique_id:
        return unique_id
    data = entry.get("data")
    if isinstance(data, Mapping):
        identity = entry_data_identity(data)
        if identity:
            return identity
    return str(entry.get("entry_id", "")).strip()


def _entities_by_device_id(
    entities: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    active_by_device: dict[str, set[str]] = {}
    disabled_by_device: dict[str, set[str]] = {}
    for entity in entities:
        device_id = str(entity.get("device_id", "") or "").strip()
        entity_id = str(entity.get("entity_id", "") or "").strip()
        if device_id and entity_id:
            target = (
                disabled_by_device
                if str(entity.get("disabled_by", "") or "").strip()
                else active_by_device
            )
            target.setdefault(device_id, set()).add(entity_id)
    return active_by_device, disabled_by_device


def _storage_rows(
    storage: Mapping[str, Any],
    key: str,
) -> tuple[Mapping[str, Any], ...]:
    data = storage.get("data")
    if not isinstance(data, Mapping):
        return ()
    rows = data.get(key)
    if not isinstance(rows, Sequence) or isinstance(rows, str):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _pairs(value: Any) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for item in _sequence(value):
        if isinstance(item, Sequence) and not isinstance(item, str) and len(item) >= 2:
            pairs.append((str(item[0]), str(item[1])))
    return tuple(pairs)


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return tuple(value)
    return ()


def _read_storage(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        loaded = json.load(file)
    if not isinstance(loaded, Mapping):
        raise ValueError(f"{path} did not contain a JSON object")
    return loaded


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit HA .storage registry rows for stale UniLED device IDs.",
    )
    parser.add_argument(
        "--storage-dir",
        type=Path,
        required=True,
        help="Path to Home Assistant's .storage directory.",
    )
    parser.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Exit with status 1 when stale UniLED device rows are found.",
    )
    return parser


def main() -> int:
    """Run the registry audit."""
    args = _parser().parse_args()
    rows = audit_uniled_registry(
        _read_storage(args.storage_dir / "core.config_entries"),
        _read_storage(args.storage_dir / "core.device_registry"),
        _read_storage(args.storage_dir / "core.entity_registry"),
    )
    stale_rows = tuple(row for row in rows if row.stale)
    disabled_only_rows = tuple(
        row for row in rows if row.held_only_by_disabled_entities
    )
    print(f"uniled registry rows: {len(rows)}")
    print(f"stale candidate rows: {len(stale_rows)}")
    print(f"disabled-only old rows: {len(disabled_only_rows)}")
    for row in stale_rows:
        print(
            "stale "
            f"entry={row.title or row.entry_id} "
            f"expected={row.expected_identifier} "
            f"device_id={row.device_id} "
            f"identifiers={row.identifiers} "
            f"connections={row.connections}"
        )
    for row in disabled_only_rows:
        print(
            "disabled-only "
            f"entry={row.title or row.entry_id} "
            f"expected={row.expected_identifier} "
            f"device_id={row.device_id} "
            f"disabled_entities={row.disabled_entity_ids}"
        )
    if stale_rows and args.fail_on_stale:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
