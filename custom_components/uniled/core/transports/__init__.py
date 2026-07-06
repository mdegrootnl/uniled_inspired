"""Transport boundaries for UniLED core sessions."""

from .base import CommandTransport, TransportError
from .ble import (
    BLEEvidenceProfile,
    BLEPluginContractHint,
    BLEProfile,
    BLEUUIDCandidate,
    ble_evidence_for_model,
    ble_profile_for_model,
    describe_ble_evidence_profile,
)
from .lan import (
    LANProfile,
    SpNetDiscoveryResponse,
    SPTechLegacyCommandId,
    SPTechLegacyConfigurationCode,
    SPTechLegacyModelCode,
    SPTechLegacyStatusChunkHint,
    build_spnet_discovery_request,
    describe_lan_profile,
    lan_profile_for_model,
    parse_spnet_discovery_response,
    sptech_legacy_model_name_for_code,
)
from .mesh import (
    BLEMeshAdvertisement,
    BLEMeshProfile,
    describe_mesh_profile,
    mesh_profile_for_model,
    telink_mesh_advertisement,
)

__all__ = [
    "BLEMeshAdvertisement",
    "BLEMeshProfile",
    "BLEEvidenceProfile",
    "BLEPluginContractHint",
    "BLEProfile",
    "BLEUUIDCandidate",
    "CommandTransport",
    "LANProfile",
    "SPTechLegacyCommandId",
    "SPTechLegacyConfigurationCode",
    "SPTechLegacyModelCode",
    "SPTechLegacyStatusChunkHint",
    "SpNetDiscoveryResponse",
    "TransportError",
    "ble_evidence_for_model",
    "ble_profile_for_model",
    "build_spnet_discovery_request",
    "describe_ble_evidence_profile",
    "describe_lan_profile",
    "describe_mesh_profile",
    "lan_profile_for_model",
    "mesh_profile_for_model",
    "parse_spnet_discovery_response",
    "sptech_legacy_model_name_for_code",
    "telink_mesh_advertisement",
]
