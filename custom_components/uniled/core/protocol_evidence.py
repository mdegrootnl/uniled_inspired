"""Protocol evidence metadata for command-backed catalog families."""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import CatalogModel, ProtocolFamily, TransportKind
from .legacy_parity import (
    LegacyUniLEDParityProfile,
    legacy_uniled_parity_profile_for_model,
)

PROTOCOL_EVIDENCE_OLD_UNILED_EXACT = "old_uniled_exact"
PROTOCOL_EVIDENCE_APK_FAMILY_INFERENCE = "apk_catalog_family_inference"
PROTOCOL_EVIDENCE_SP6XX_STYLE = "sp6xx_style_ble_commands"


@dataclass(frozen=True, slots=True)
class ProtocolEvidenceProfile:
    """Evidence summary for why a model is mapped to a command protocol."""

    family: ProtocolFamily
    kind: str
    basis: str
    evidence_hints: tuple[str, ...]
    source_module: str | None = None


def protocol_evidence_profile_for_model(
    model: CatalogModel,
) -> ProtocolEvidenceProfile | None:
    """Return command-protocol evidence for the current catalog model."""
    legacy_profile = legacy_uniled_parity_profile_for_model(model)
    if legacy_profile is not None:
        return _legacy_protocol_evidence(model, legacy_profile)

    if model.family is ProtocolFamily.BANLANX_CUSTOM_5XX:
        return ProtocolEvidenceProfile(
            family=model.family,
            kind=PROTOCOL_EVIDENCE_SP6XX_STYLE,
            basis=(
                "APK custom 5xx records share the SP630E surface and are "
                "mapped through the BanlanX6xx-style BLE command protocol"
            ),
            evidence_hints=_catalog_hints(model)
            + (
                "homeUri=/sp630e",
                "shared SP630E package surface",
                "LAN/cloud evidence remains transport-pending",
            ),
        )

    if model.family in (
        ProtocolFamily.BANLANX_V2,
        ProtocolFamily.BANLANX_V3,
        ProtocolFamily.BANLANX_6XX,
    ):
        return ProtocolEvidenceProfile(
            family=model.family,
            kind=PROTOCOL_EVIDENCE_APK_FAMILY_INFERENCE,
            basis=(
                "APK catalog record belongs to a protocol family with a "
                "ported command implementation, but this exact model was not "
                "an old-UniLED parity entry"
            ),
            evidence_hints=_catalog_hints(model),
        )

    return None


def describe_protocol_evidence_profile(
    profile: ProtocolEvidenceProfile | None,
) -> str | None:
    """Return a compact protocol-evidence diagnostic string."""
    if profile is None:
        return None
    source = (
        ""
        if profile.source_module is None
        else f"; source={profile.source_module}"
    )
    return (
        f"{profile.family.value}; evidence={profile.kind}; "
        f"hints={len(profile.evidence_hints)}{source}"
    )


def _legacy_protocol_evidence(
    model: CatalogModel,
    legacy_profile: LegacyUniLEDParityProfile,
) -> ProtocolEvidenceProfile:
    return ProtocolEvidenceProfile(
        family=model.family,
        kind=PROTOCOL_EVIDENCE_OLD_UNILED_EXACT,
        basis="exact model parity with a ported old-UniLED protocol module",
        source_module=legacy_profile.source_module,
        evidence_hints=_catalog_hints(model)
        + (
            f"command_builders={len(legacy_profile.command_builders)}",
            f"status_parser_hints={len(legacy_profile.status_parser_hints)}",
        ),
    )


def _catalog_hints(model: CatalogModel) -> tuple[str, ...]:
    hints = [
        f"model_id={model.model_id}",
        f"home_uri={model.home_uri or 'root'}",
        f"connect_caps={model.connect_caps}",
        f"spec_functions={model.spec_functions}",
        f"color_cap={model.color_cap}",
        "transports=" + ",".join(transport.value for transport in model.transports),
    ]
    if model.parent_id is not None:
        hints.append(f"parent_id={model.parent_id}")
    if TransportKind.LAN in model.transports:
        hints.append("lan_transport_pending")
    if TransportKind.CLOUD_OPTIONAL in model.transports:
        hints.append("cloud_transport_pending")
    return tuple(hints)
