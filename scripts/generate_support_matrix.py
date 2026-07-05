"""Generate a catalog-wide UniLED support and evidence matrix."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from custom_components.uniled import runtime as uniled_runtime  # noqa: E402
from custom_components.uniled.const import (  # noqa: E402
    CONF_ADDRESS,
    CONF_HOST,
    CONF_MESH_UUID,
    CONF_MODEL,
    CONF_MODEL_ID,
    CONF_TRANSPORT,
    TRANSPORT_BLE,
    TRANSPORT_BLE_MESH,
    TRANSPORT_LAN,
    TRANSPORT_MANUAL,
)
from custom_components.uniled.core import (  # noqa: E402
    CatalogModel,
    ModelCatalog,
    ProtocolFamily,
    SupportLevel,
    TransportKind,
    car_light_profile_for_model,
    cloud_profile_for_model,
    default_catalog,
    fish_tank_profile_for_model,
    legacy_uniled_parity_profile_for_model,
    network_profile_for_model,
    protocol_evidence_profile_for_model,
    scene_profile_for_model,
    sp630e_profile_for_model,
)
from custom_components.uniled.core.transports import (  # noqa: E402
    ble_evidence_for_model,
    lan_profile_for_model,
    mesh_profile_for_model,
)


@dataclass(frozen=True, slots=True)
class SupportMatrixRow:
    """One canonical user-facing model support row."""

    name: str
    model_id: int
    parent_id: int | None
    family: str
    support_level: str
    transports: tuple[str, ...]
    legacy_uniled: bool
    protocol_ready: bool
    evidence_profiles: tuple[str, ...]
    support_blockers: tuple[str, ...]
    support_blocker_count: int
    support_disposition: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable mapping."""
        return {
            "name": self.name,
            "model_id": self.model_id,
            "parent_id": self.parent_id,
            "family": self.family,
            "support_level": self.support_level,
            "transports": list(self.transports),
            "legacy_uniled": self.legacy_uniled,
            "protocol_ready": self.protocol_ready,
            "evidence_profiles": list(self.evidence_profiles),
            "support_blockers": list(self.support_blockers),
            "support_blocker_count": self.support_blocker_count,
            "support_disposition": self.support_disposition,
        }


def support_matrix_rows(
    catalog: ModelCatalog | None = None,
) -> tuple[SupportMatrixRow, ...]:
    """Return one row for each canonical user-facing catalog model."""
    catalog = catalog or default_catalog()
    rows = [
        _support_matrix_row(catalog, model)
        for model in catalog.user_facing_models()
    ]
    return tuple(sorted(rows, key=lambda row: (row.family, row.name, row.model_id)))


def matrix_summary(
    rows: Iterable[SupportMatrixRow],
    catalog: ModelCatalog | None = None,
) -> dict[str, object]:
    """Return compact support matrix totals."""
    rows = tuple(rows)
    catalog = catalog or default_catalog()
    user_records = tuple(
        model
        for model in catalog.models
        if model.support_level is not SupportLevel.FILTERED
    )
    return {
        "catalog_records": len(catalog.models),
        "unique_names": len(catalog.unique_names),
        "user_facing_records": len(user_records),
        "user_facing_models": len(rows),
        "filtered_records": len(catalog.filtered_models()),
        "record_families": dict(
            sorted(Counter(model.family.value for model in user_records).items())
        ),
        "support_levels": dict(
            sorted(Counter(row.support_level for row in rows).items())
        ),
        "families": dict(sorted(Counter(row.family for row in rows).items())),
        "transports": dict(
            sorted(
                Counter(
                    transport
                    for row in rows
                    for transport in row.transports
                ).items()
            )
        ),
        "legacy_uniled_models": sum(1 for row in rows if row.legacy_uniled),
        "protocol_ready_models": sum(1 for row in rows if row.protocol_ready),
        "support_blockers": support_blocker_counts(rows),
    }


def support_blocker_counts(rows: Iterable[SupportMatrixRow]) -> dict[str, int]:
    """Return unresolved support blockers and requirements by model count."""
    blockers: Counter[str] = Counter()
    for row in rows:
        blockers.update(row.support_blockers)
    return dict(sorted(blockers.items()))


def render_markdown(rows: Iterable[SupportMatrixRow]) -> str:
    """Render support matrix rows as markdown."""
    rows = tuple(rows)
    summary = matrix_summary(rows)
    support_blockers = summary["support_blockers"]
    lines = [
        "# UniLED Next Support Matrix",
        "",
        "Generated from the bundled BanlanX APK catalog, legacy-only old "
        "UniLED rows, and runtime support disposition.",
        "",
        f"- Catalog records: {summary['catalog_records']}",
        f"- Unique model names: {summary['unique_names']}",
        f"- User-facing catalog records: {summary['user_facing_records']}",
        f"- Canonical user-facing models: {summary['user_facing_models']}",
        f"- Filtered records: {summary['filtered_records']}",
        f"- Support levels: {_counter_text(summary['support_levels'])}",
        f"- Canonical families: {_counter_text(summary['families'])}",
        f"- Catalog record families: {_counter_text(summary['record_families'])}",
        f"- Transports: {_counter_text(summary['transports'])}",
        f"- Old UniLED parity/evidence candidates: "
        f"{summary['legacy_uniled_models']}",
        f"- Command-protocol-ready models: {summary['protocol_ready_models']}",
        "",
        "## Open Support Blockers",
        "",
        "Counts are per canonical user-facing model. They aggregate the "
        "same `support_blockers` row values exposed in JSON, CSV, and the "
        "model matrix. Those row values are derived from `support_disposition` "
        "tokens ending in `_pending`, tokens ending in `_required`, and "
        "explicit accessory dependencies.",
        "",
        "| Blocker or requirement | Models |",
        "|---|---:|",
    ]
    for blocker, count in support_blockers.items():
        lines.append(f"| {blocker} | {count} |")

    lines.extend(
        [
            "",
            "## Model Matrix",
            "",
            (
                "| Model | Model ID | Family | Support | Transports | Protocol | "
                "Evidence | Open blockers | Blocker count | Disposition |"
            ),
            "|---|---:|---|---|---|---|---|---|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                (
                    row.name,
                    str(row.model_id),
                    row.family,
                    row.support_level,
                    ", ".join(row.transports),
                    "yes" if row.protocol_ready else "no",
                    ", ".join(row.evidence_profiles) or "none",
                    ", ".join(row.support_blockers) or "none",
                    str(row.support_blocker_count),
                    row.support_disposition,
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def render_csv(rows: Iterable[SupportMatrixRow]) -> str:
    """Render support matrix rows as simple CSV."""
    lines = [
        (
            "name,model_id,parent_id,family,support_level,transports,"
            "legacy_uniled,protocol_ready,evidence_profiles,support_blockers,"
            "support_blocker_count,support_disposition"
        )
    ]
    for row in rows:
        lines.append(
            ",".join(
                _csv_cell(value)
                for value in (
                    row.name,
                    row.model_id,
                    "" if row.parent_id is None else row.parent_id,
                    row.family,
                    row.support_level,
                    "|".join(row.transports),
                    row.legacy_uniled,
                    row.protocol_ready,
                    "|".join(row.evidence_profiles),
                    "|".join(row.support_blockers),
                    row.support_blocker_count,
                    row.support_disposition,
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_json(rows: Iterable[SupportMatrixRow]) -> str:
    """Render support matrix rows and totals as JSON."""
    rows = tuple(rows)
    return (
        json.dumps(
            {
                "summary": matrix_summary(rows),
                "rows": [row.as_dict() for row in rows],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _support_matrix_row(
    catalog: ModelCatalog,
    model: CatalogModel,
) -> SupportMatrixRow:
    runtime = uniled_runtime.build_runtime(_sample_entry_data(model), catalog=catalog)
    evidence = _evidence_profiles(model, protocol_ready=runtime.protocol_ready)
    disposition = uniled_runtime.support_disposition(runtime)
    blockers = uniled_runtime.support_blockers(runtime)
    return SupportMatrixRow(
        name=model.name,
        model_id=model.model_id,
        parent_id=model.parent_id,
        family=model.family.value,
        support_level=model.support_level.value,
        transports=tuple(transport.value for transport in model.transports),
        legacy_uniled=_legacy_uniled_evidence_for_model(model),
        protocol_ready=runtime.protocol_ready,
        evidence_profiles=evidence,
        support_blockers=blockers,
        support_blocker_count=len(blockers),
        support_disposition=disposition,
    )


def _sample_entry_data(model: CatalogModel) -> dict[str, object]:
    data: dict[str, object] = {
        CONF_MODEL: model.name,
        CONF_MODEL_ID: model.model_id,
    }
    if TransportKind.BLE in model.transports:
        data.update(
            {
                CONF_TRANSPORT: TRANSPORT_BLE,
                CONF_ADDRESS: "AA:BB:CC:DD:EE:09",
            }
        )
    elif TransportKind.BLE_MESH in model.transports:
        data.update(
            {
                CONF_TRANSPORT: TRANSPORT_BLE_MESH,
                CONF_ADDRESS: "AA:BB:CC:DD:EE:0A",
                CONF_MESH_UUID: 0x0211,
            }
        )
    elif TransportKind.LAN in model.transports:
        data.update(
            {
                CONF_TRANSPORT: TRANSPORT_LAN,
                CONF_HOST: "192.0.2.55",
            }
        )
    else:
        data.update(
            {
                CONF_TRANSPORT: TRANSPORT_MANUAL,
                "device_id": "manual",
            }
        )
    return data


def _evidence_profiles(
    model: CatalogModel,
    *,
    protocol_ready: bool,
) -> tuple[str, ...]:
    profiles: list[str] = []
    if protocol_ready:
        profiles.append("command_protocol")
        protocol_evidence = protocol_evidence_profile_for_model(model)
        if (
            protocol_evidence is not None
            and protocol_evidence.kind != "old_uniled_exact"
        ):
            profiles.append(protocol_evidence.kind)
    if model.family is ProtocolFamily.ZENGGE_MESH:
        profiles.append("zengge_mesh_core")
    if _legacy_uniled_evidence_for_model(model):
        profiles.append("legacy_uniled")
    if _is_legacy_uniled_only_model(model):
        profiles.append("legacy_uniled_only")
    if ble_evidence_for_model(model) is not None and not _is_legacy_uniled_only_model(
        model
    ):
        profiles.append("ble_apk")
    if lan_profile_for_model(model) is not None:
        profiles.append("lan_apk")
        if (lan_profile := lan_profile_for_model(model)) is not None:
            if lan_profile.command_protocol_known:
                profiles.append("sptech_lan")
    if mesh_profile_for_model(model) is not None:
        profiles.append("mesh_apk")
    if cloud_profile_for_model(model) is not None:
        profiles.append("cloud_apk")
    if sp630e_profile_for_model(model) is not None:
        profiles.append("sp630e_apk")
    if scene_profile_for_model(model) is not None:
        profiles.append("scene_apk")
    if network_profile_for_model(model) is not None:
        profiles.append("network_apk")
    if car_light_profile_for_model(model) is not None:
        profiles.append("car_light_apk")
    if fish_tank_profile_for_model(model) is not None:
        profiles.append("fish_tank_apk")
    return tuple(profiles)


def _legacy_uniled_evidence_for_model(model: CatalogModel) -> bool:
    """Return whether old UniLED provides command/protocol evidence."""
    if _is_legacy_uniled_only_model(model):
        return True
    if legacy_uniled_parity_profile_for_model(model) is not None:
        return True
    mesh_profile = mesh_profile_for_model(model)
    return bool(mesh_profile is not None and mesh_profile.old_uniled_protocol_known)


def _is_legacy_uniled_only_model(model: CatalogModel) -> bool:
    """Return whether a model was sourced only from detached old UniLED."""
    return model.home_uri.startswith("/legacy/uniled/")


def _counter_text(value: object) -> str:
    mapping = value if isinstance(value, dict) else {}
    return ", ".join(f"{key}={mapping[key]}" for key in sorted(mapping))


def _csv_cell(value: object) -> str:
    text = str(value)
    if any(char in text for char in {",", '"', "\n"}):
        return '"' + text.replace('"', '""') + '"'
    return text


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a support/evidence matrix from the bundled catalog."
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "csv", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. Defaults to stdout.",
    )
    return parser


def main() -> int:
    """Run the support matrix generator."""
    args = _parser().parse_args()
    rows = support_matrix_rows()
    if args.format == "json":
        output = render_json(rows)
    elif args.format == "csv":
        output = render_csv(rows)
    else:
        output = render_markdown(rows)

    if args.output is None:
        print(output, end="")
    else:
        args.output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
