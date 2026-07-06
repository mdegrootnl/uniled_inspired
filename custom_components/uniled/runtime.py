"""Runtime model for the Home Assistant shell."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from .const import (
    CONF_ADDRESS,
    CONF_CLOUD_PASSWORD,
    CONF_CLOUD_USERNAME,
    CONF_DEVICE_ID,
    CONF_DISCOVERY_CONFIDENCE,
    CONF_DISCOVERY_MATCH,
    CONF_DISCOVERY_SOURCE,
    CONF_HOST,
    CONF_MESH_KEY,
    CONF_MESH_LTK,
    CONF_MESH_NODE_ID,
    CONF_MESH_NODE_TYPE,
    CONF_MESH_NODE_WIRING,
    CONF_MESH_NODES,
    CONF_MESH_PASSWORD,
    CONF_MESH_UUID,
    CONF_MODEL,
    CONF_MODEL_ID,
    CONF_TRANSPORT,
)
from .core import (
    ApkCommandIdHint,
    BanlanXCloudEndpoint,
    BanlanXCloudProfile,
    BanlanXCloudRequestContractHint,
    CarLightProfile,
    CatalogModel,
    ChannelState,
    CommandTransport,
    DeviceSession,
    DeviceState,
    EntityCategoryKind,
    EntityPlan,
    FeatureSpec,
    FishTankProfile,
    LegacyUniLEDParityProfile,
    ModelCatalog,
    NetworkProfile,
    PlatformKind,
    ProtocolEvidenceProfile,
    ProtocolFamily,
    SceneProfile,
    SP630EProfile,
    SupportLevel,
    TransportError,
    TransportKind,
    ZenggeMeshConnection,
    ZenggeMeshSession,
    ZenggeMeshTransport,
    ZenggeNodeContext,
    car_light_accessory_role,
    car_light_command_blockers_for_model,
    car_light_model_role_for_model,
    car_light_ordered_setup_dependencies,
    car_light_profile_for_model,
    car_light_required_controller_model,
    car_light_required_setup_dependencies,
    car_light_setup_dependency_for_model,
    car_light_setup_order,
    car_light_setup_stage,
    cloud_profile_for_model,
    default_catalog,
    describe_car_light_profile,
    describe_cloud_profile,
    describe_fish_tank_profile,
    describe_legacy_uniled_parity_profile,
    describe_network_profile,
    describe_protocol_evidence_profile,
    describe_scene_profile,
    describe_sp630e_profile,
    fish_tank_profile_for_model,
    legacy_uniled_parity_profile_for_model,
    network_profile_for_model,
    plan_for_model,
    protocol_evidence_profile_for_model,
    protocol_for_model,
    scene_profile_for_model,
    sp630e_profile_for_model,
)
from .core.options import (
    SelectOptionMap,
    banlanx6xx_chip_order_values_for_light_type,
    banlanx6xx_default_light_type_for_model,
    banlanx6xx_default_mode_effect_for_light_type,
    banlanx6xx_effect_attributes_for_state,
    banlanx6xx_effect_values_for_light_type,
    banlanx6xx_light_mode_name,
    banlanx6xx_light_mode_values_for_light_type,
    banlanx6xx_light_type_capabilities,
    banlanx6xx_light_type_has_coexistence,
    banlanx6xx_light_type_values_for_model,
    banlanx6xx_model_has_coexistence,
    banlanx6xx_model_has_dynamic_light_type,
    banlanx6xx_model_has_static_effects,
    banlanx6xx_style_family,
    legacy_v23_model_has_white_channel,
    mode_effect_parts,
    mode_effect_value,
    select_option_map,
)
from .core.protocols.banlanx_legacy import LegacyProtocol
from .core.protocols.zengge_mesh import (
    ZENGGE_DEFAULT_MESH_KEY,
    ZENGGE_DEFAULT_MESH_PASS,
    ZENGGE_MESH_ADDRESS_BRIDGE,
    ZENGGE_MESH_ADDRESS_NONE,
    ZENGGE_NODE_KIND_BRIDGE,
    ZENGGE_NODE_KIND_BULB,
    ZENGGE_NODE_KIND_LIGHT,
    ZENGGE_NODE_KIND_PANEL,
    ZENGGE_NODE_KIND_STRIP,
    ZENGGE_STATUS_OFFLINE,
    ZENGGE_STATUS_ONLINE,
    ZenggeCryptoError,
    zengge_node_kind,
)
from .core.transports import (
    BLEEvidenceProfile,
    BLEMeshProfile,
    LANProfile,
    ble_evidence_for_model,
    describe_ble_evidence_profile,
    describe_lan_profile,
    describe_mesh_profile,
    lan_profile_for_model,
    mesh_profile_for_model,
)

_REDACTED = "**REDACTED**"
_REDACT_KEYS = {
    CONF_ADDRESS,
    CONF_CLOUD_PASSWORD,
    CONF_CLOUD_USERNAME,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_MESH_KEY,
    CONF_MESH_LTK,
    CONF_MESH_PASSWORD,
}
_MIN_CCT_KELVIN = 2700
_MAX_CCT_KELVIN = 6500
_BANLANX6XX_STATIC_MODES = {0x01, 0x02}
_BANLANX6XX_DYNAMIC_MODES = {0x03, 0x04}
_BANLANX6XX_SOUND_MODES = {0x05, 0x06}
_BANLANX6XX_WHITE_MODES = {0x02, 0x04, 0x06}
_BANLANX_V23_WHITE_EFFECTS = {
    ProtocolFamily.BANLANX_V2: 0xBF,
    ProtocolFamily.BANLANX_V3: 0xCC,
}
_BANLANX_V23_SOLID_EFFECTS = {
    ProtocolFamily.BANLANX_V2: 0xBE,
    ProtocolFamily.BANLANX_V3: 0x63,
}
_BANLANX_V23_COLORABLE_EFFECTS = {
    ProtocolFamily.BANLANX_V2: frozenset(
        {0xBE, 0xCA, 0xCC, 0xCE, 0xD0, 0xD2, 0xD4, 0xD6}
    ),
    ProtocolFamily.BANLANX_V3: frozenset({0x63, 0x20, 0x21, 0x67}),
}
_COMMAND_NUMBER_KEYS = {
    "effect_speed",
    "effect_level",
    "effect_length",
    "audio_sensitivity",
    "onoff_pixels",
    "segment_count",
    "segment_pixels",
}
_COMMAND_SELECT_KEYS = {
    "audio_input",
    "effect",
    "light_mode",
    "onoff_effect",
    "onoff_speed",
    "on_power",
    "light_type",
    "chip_order",
    "chip_type",
}
_COMMAND_SWITCH_KEYS = {
    "effect_direction",
    "effect_loop",
    "scene_loop",
    "effect_play",
    "coexistence",
}
_COMMAND_BUTTON_KEYS = {"refresh"}
_ZENGGE_PANEL_STATUS_PREFIX = "mesh_panel_"
_ZENGGE_PANEL_STATUS_SUFFIX = "_status"
_BANLANX6XX_STATE_DEPENDENT_COMMAND_KEYS = {
    "audio_input",
    "audio_sensitivity",
    "effect_speed",
    "effect_length",
    "effect_direction",
    "effect_loop",
    "effect_play",
}
_OUTPUT_SCOPED_EFFECT_FAMILIES = {
    ProtocolFamily.BANLANX_601,
    ProtocolFamily.BANLANX_60X,
}
_OUTPUT_SCOPED_SELECT_KEYS = {"chip_order", "effect"}
_OUTPUT_SCOPED_NUMBER_KEYS = {"effect_speed", "effect_length"}
_OUTPUT_SCOPED_SWITCH_KEYS = {"effect_direction"}
_SERVICE_POWER = "power"
_SERVICE_BRIGHTNESS = "brightness"
_SERVICE_TRANSITION = "transition"
_SERVICE_RGB_COLOR = "rgb_color"
_SERVICE_RGB2_COLOR = "rgb2_color"
_SERVICE_RGBW_COLOR = "rgbw_color"
_SERVICE_RGBWW_COLOR = "rgbww_color"
_SERVICE_COLOR_TEMP_KELVIN = "color_temp_kelvin"
_SERVICE_WHITE = "white"
_SERVICE_EFFECT = "effect"
_SERVICE_EFFECT_SPEED = "effect_speed"
_SERVICE_EFFECT_LENGTH = "effect_length"
_SERVICE_EFFECT_DIRECTION = "effect_direction"
_SERVICE_EFFECT_LOOP = "effect_loop"
_SERVICE_EFFECT_PLAY = "effect_play"
_SERVICE_SENSITIVITY = "sensitivity"


class RuntimeSetupError(ValueError):
    """Raised when a config entry cannot be resolved into a runtime."""

    def __init__(
        self,
        message: str,
        *,
        field: str = "runtime",
        reason: str | None = None,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.reason = reason or message


@dataclass(frozen=True, slots=True)
class LightTypeCommandValues:
    """Complete SP6xx light-type command parameters."""

    light_type: int
    chip_order: int
    mode: int
    effect: int
    power: bool
    refresh: bool


@dataclass(slots=True)
class UniLEDRuntime:
    """Runtime data stored on the config entry."""

    catalog: ModelCatalog
    model: CatalogModel
    entity_plan: EntityPlan
    protocol: LegacyProtocol | None
    state: DeviceState
    entry_data: Mapping[str, Any]
    transport: Any | None = None
    session: DeviceSession | None = None
    lan_profile: LANProfile | None = None
    mesh_session: ZenggeMeshSession | None = None
    mesh_connection: ZenggeMeshConnection | None = None
    coordinator: Any | None = None
    notification_assembler: Any | None = None

    @property
    def protocol_ready(self) -> bool:
        """Return whether the model has a core protocol implementation."""
        return self.protocol is not None

    @property
    def session_ready(self) -> bool:
        """Return whether a command transport session is attached."""
        return self.session is not None

    @property
    def mesh_transport_ready(self) -> bool:
        """Return whether a Zengge mesh transport connection is attached."""
        return self.mesh_connection is not None

    @property
    def lan_transport_ready(self) -> bool:
        """Return whether a LAN host transport holder is attached."""
        return self.lan_profile is not None and self.transport is not None

    @property
    def mesh_session_paired(self) -> bool:
        """Return whether a Zengge mesh session key is available."""
        return self.mesh_session is not None and self.mesh_session.paired

    def diagnostic_value(self, key: str) -> Any:
        """Return a diagnostic feature value for the current runtime."""
        if key == "catalog_model":
            return self.model.name
        if key == "catalog_model_id":
            return self.model.model_id
        if key == "catalog_parent_id":
            return self.model.parent_id
        if key == "catalog_connect_caps":
            return self.model.connect_caps
        if key == "catalog_connect_capabilities":
            return _catalog_connect_capabilities(self.model)
        if key == "catalog_spec_functions":
            return self.model.spec_functions
        if key == "catalog_spec_function_bits":
            return _catalog_spec_function_bits(self.model)
        if key == "catalog_color_cap":
            return self.model.color_cap
        if key == "catalog_color_capabilities":
            return _catalog_color_capabilities(self.model)
        if key == "catalog_feature_count":
            return len(self.model.features)
        if key == "catalog_feature_keys":
            return _catalog_feature_keys(self.model)
        if key == "catalog_feature_summary":
            return _catalog_feature_summary(self.model)
        if key == "catalog_variant_count":
            return len(
                [
                    variant
                    for variant in self.catalog.models_for_name(self.model.name)
                    if variant.is_user_facing
                ]
            )
        if key == "catalog_variant_ids":
            return _catalog_variant_ids(self.catalog, self.model)
        if key == "protocol_family":
            return self.model.family.value
        if key == "support_level":
            return self.model.support_level.value
        if key == "support_disposition":
            return support_disposition(self)
        if key == "support_blocker_count":
            return len(support_blockers(self))
        if key == "support_blockers":
            return _format_tuple(support_blockers(self))
        if key == "transport":
            return ", ".join(transport.value for transport in self.model.transports)
        if key == "configured_transport":
            return _configured_transport(self.entry_data)
        if key == "discovery_source":
            return _entry_data_text(self.entry_data, CONF_DISCOVERY_SOURCE)
        if key == "discovery_match":
            return _entry_data_text(self.entry_data, CONF_DISCOVERY_MATCH)
        if key == "discovery_confidence":
            return _entry_data_text(self.entry_data, CONF_DISCOVERY_CONFIDENCE)
        if key == "runtime_transport_state":
            return _runtime_transport_state(self)
        if key == "last_refresh_result":
            return self.state.diagnostics.get("last_refresh_result")
        if key == "effect_type":
            channel = self.state.channel(0)
            return None if channel is None else channel.effect_type
        if key == "legacy_uniled_parity":
            return self.model.legacy_uniled_supported
        if key == "legacy_uniled_parity_profile":
            return describe_legacy_uniled_parity_profile(
                legacy_uniled_parity_profile_for_model(self.model)
            )
        if key == "legacy_uniled_command_count":
            profile = legacy_uniled_parity_profile_for_model(self.model)
            return None if profile is None else len(profile.command_builders)
        if key == "legacy_uniled_status_parser_count":
            profile = legacy_uniled_parity_profile_for_model(self.model)
            return None if profile is None else len(profile.status_parser_hints)
        if key == "legacy_uniled_stubbed_command_count":
            profile = legacy_uniled_parity_profile_for_model(self.model)
            return None if profile is None else len(profile.stubbed_builders)
        if key == "legacy_uniled_parity_gap_count":
            profile = legacy_uniled_parity_profile_for_model(self.model)
            return None if profile is None else len(profile.gap_hints)
        if key == "protocol_evidence_profile":
            return describe_protocol_evidence_profile(
                protocol_evidence_profile_for_model(self.model)
            )
        if key == "protocol_evidence_kind":
            profile = protocol_evidence_profile_for_model(self.model)
            return None if profile is None else profile.kind
        if key == "protocol_evidence_hint_count":
            profile = protocol_evidence_profile_for_model(self.model)
            return None if profile is None else len(profile.evidence_hints)
        if key == "ble_profile":
            return describe_ble_evidence_profile(ble_evidence_for_model(self.model))
        if key == "ble_uuid_binding_status":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else profile.uuid_binding_status
        if key == "ble_known_service_uuid_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.known_service_uuids)
        if key == "ble_known_service_uuids":
            profile = ble_evidence_for_model(self.model)
            return (
                None
                if profile is None
                else _format_tuple(profile.known_service_uuids)
            )
        if key == "ble_known_write_uuid":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else profile.known_write_uuid or "pending"
        if key == "ble_known_notify_uuid":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else profile.known_notify_uuid or "pending"
        if key == "ble_uuid_pool_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.apk_uuid_pool)
        if key == "ble_apk_uuid_pool":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else _format_tuple(profile.apk_uuid_pool)
        if key == "ble_uuid_inventory_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.uuid_inventory)
        if key == "ble_unbound_uuid_candidate_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.unbound_uuid_candidates)
        if key == "ble_unbound_uuid_candidates":
            profile = ble_evidence_for_model(self.model)
            if profile is None:
                return None
            return _format_tuple(
                tuple(
                    candidate.short_name
                    for candidate in profile.unbound_uuid_candidates
                )
            )
        if key == "ble_legacy_uuid_candidate_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.legacy_uuid_candidates)
        if key == "ble_legacy_uuid_candidates":
            profile = ble_evidence_for_model(self.model)
            if profile is None:
                return None
            return _format_tuple(
                tuple(
                    candidate.short_name
                    for candidate in profile.legacy_uuid_candidates
                )
            )
        if key == "ble_plugin_method_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.plugin_methods)
        if key == "ble_plugin_argument_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.plugin_arguments)
        if key == "ble_plugin_result_field_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.plugin_result_fields)
        if key == "ble_scan_result_field_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.scan_result_fields)
        if key == "ble_service_result_field_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.service_result_fields)
        if key == "ble_characteristic_result_field_count":
            profile = ble_evidence_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.characteristic_result_fields)
            )
        if key == "ble_rssi_result_field_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.rssi_result_fields)
        if key == "ble_mtu_result_field_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.mtu_result_fields)
        if key == "ble_adapter_state_result_field_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.adapter_state_result_fields)
        if key == "ble_notification_event_field_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.notification_event_fields)
        if key == "ble_connection_event_field_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.connection_event_fields)
        if key == "ble_device_found_event_field_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.device_found_event_fields)
        if key == "ble_descriptor_uuid_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.descriptor_uuids)
        if key == "ble_boolean_event_channel_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.boolean_event_channels)
        if key == "ble_plugin_event_hint_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.plugin_event_hints)
        if key == "ble_plugin_contract_hint_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.plugin_contract_hints)
        if key == "ble_plugin_error_code_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.plugin_error_hints)
        if key == "ble_plugin_channel_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.plugin_channels)
        if key == "ble_protocol_gap_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.protocol_gap_hints)
        if key == "ble_issue_advertisement_count":
            profile = ble_evidence_for_model(self.model)
            return None if profile is None else len(profile.issue_advertisements)
        if key == "ble_issue_advertisements":
            profile = ble_evidence_for_model(self.model)
            if profile is None:
                return None
            return _format_tuple(
                tuple(
                    f"{advertisement.issue}:{advertisement.model_name}:"
                    f"{advertisement.manufacturer_payload_hex}"
                    for advertisement in profile.issue_advertisements
                )
            )
        if key == "lan_profile":
            return describe_lan_profile(lan_profile_for_model(self.model))
        if key == "lan_host_network_method_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.host_network_methods)
        if key == "lan_host_setup_mode":
            profile = lan_profile_for_model(self.model)
            if profile is None:
                return None
            return "manual_host" if profile.requires_manual_host else "discovery_ready"
        if key == "lan_discovery_plugin_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_discovery_hints)
        if key == "lan_discovery_channel_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_discovery_channels)
        if key == "lan_network_setup_route_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.network_setup_route_hints)
            )
        if key == "lan_network_setup_guide_asset_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.network_setup_guide_assets
                else len(profile.network_setup_guide_assets)
            )
        if key == "lan_network_setup_prompt_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.network_setup_prompts)
        if key == "lan_network_cloud_setup_prompt_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.network_cloud_setup_prompts)
            )
        if key == "lan_multicast_lock_method_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.multicast_lock_methods)
        if key == "lan_bonsoir_method_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.bonsoir_methods)
        if key == "lan_bonsoir_argument_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.bonsoir_arguments)
        if key == "lan_bonsoir_nsd_method_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.bonsoir_nsd_methods)
        if key == "lan_bonsoir_discovery_event_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.bonsoir_discovery_events)
            )
        if key == "lan_bonsoir_service_event_field_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.bonsoir_service_event_fields)
            )
        if key == "lan_bonsoir_service_normalization_hint_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.bonsoir_service_normalization_hints)
            )
        if key == "lan_bonsoir_service_type_flow_hint_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.bonsoir_service_type_flow_hints)
            )
        if key == "lan_bonsoir_txt_query_flow_hint_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.bonsoir_txt_query_flow_hints)
            )
        if key == "lan_discovery_gap_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.discovery_gap_hints)
        if key == "lan_raw_socket_hint_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.raw_socket_hints)
        if key == "lan_discovery_status_hint_count":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else len(profile.discovery_status_hints)
        if key == "lan_udp_socket_timeout_ms":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else profile.udp_socket_timeout_ms
        if key == "lan_udp_receive_buffer_bytes":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else profile.udp_receive_buffer_bytes
        if key == "lan_mdns_txt_query_timeout_ms":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else profile.mdns_txt_query_timeout_ms
        if key == "lan_mdns_txt_record_type":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else profile.mdns_txt_record_type
        if key == "lan_mdns_txt_query_class":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else profile.mdns_txt_query_class
        if key == "lan_mdns_txt_buffer_bytes":
            profile = lan_profile_for_model(self.model)
            return None if profile is None else profile.mdns_txt_buffer_bytes
        if key == "lan_sptech_legacy_model_code_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.sptech_legacy_model_codes
                else len(profile.sptech_legacy_model_codes)
            )
        if key == "lan_sptech_legacy_configuration_code_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if (
                    profile is None
                    or not profile.sptech_legacy_configuration_codes
                )
                else len(profile.sptech_legacy_configuration_codes)
            )
        if key == "lan_sptech_legacy_command_id_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.sptech_legacy_command_ids
                else len(profile.sptech_legacy_command_ids)
            )
        if key == "lan_sptech_legacy_status_chunk_count":
            profile = lan_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.sptech_legacy_status_chunks
                else len(profile.sptech_legacy_status_chunks)
            )
        if key == "mesh_profile":
            return describe_mesh_profile(mesh_profile_for_model(self.model))
        if key == "mesh_route_count":
            profile = mesh_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.route_hints
                else len(profile.route_hints)
            )
        if key == "mesh_provisioning_hint_count":
            profile = mesh_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.provisioning_hints
                else len(profile.provisioning_hints)
            )
        if key == "mesh_provisioning_state_count":
            profile = mesh_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.provisioning_state_hints
                else len(profile.provisioning_state_hints)
            )
        if key == "mesh_sig_mesh_uuid_hint_count":
            profile = mesh_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.sig_mesh_uuid_hints
                else len(profile.sig_mesh_uuid_hints)
            )
        if key == "mesh_app_command_id_count":
            profile = mesh_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.app_command_id_hints
                else len(profile.app_command_id_hints)
            )
        if key == "mesh_control_blocker_count":
            profile = mesh_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.control_blockers
                else len(profile.control_blockers)
            )
        if key == "mesh_apk_asset_evidence_count":
            profile = mesh_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.apk_asset_evidence
                else len(profile.apk_asset_evidence)
            )
        if key == "mesh_apk_package_asset_count":
            profile = mesh_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.package_asset_count
                else profile.package_asset_count
            )
        if key == "mesh_apk_string_evidence_count":
            profile = mesh_profile_for_model(self.model)
            return (
                None
                if profile is None or not profile.apk_string_evidence
                else len(profile.apk_string_evidence)
            )
        if key == "mesh_role":
            return _mesh_role_diagnostic(self)
        if key == "mesh_known_node_count":
            return _zengge_mesh_known_node_count(self)
        if key == "mesh_command_node_count":
            if self.model.family is not ProtocolFamily.ZENGGE_MESH:
                return None
            return len(zengge_mesh_node_ids(self))
        if key == "mesh_strip_node_count":
            return _zengge_mesh_kind_count(self, ZENGGE_NODE_KIND_STRIP)
        if key == "mesh_bulb_node_count":
            return _zengge_mesh_kind_count(self, ZENGGE_NODE_KIND_BULB)
        if key == "mesh_panel_node_count":
            if self.model.family is not ProtocolFamily.ZENGGE_MESH:
                return None
            return len(zengge_mesh_panel_node_ids(self))
        if key == "mesh_bridge_seen":
            return _zengge_mesh_bridge_seen_diagnostic(self)
        if key.startswith(_ZENGGE_PANEL_STATUS_PREFIX):
            return _zengge_mesh_panel_status_diagnostic(self, key)
        if key == "cloud_profile":
            return describe_cloud_profile(cloud_profile_for_model(self.model))
        if key == "cloud_base_url_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.base_urls)
        if key == "cloud_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else _cloud_endpoint_count(profile)
        if key == "cloud_endpoint_inventory_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.endpoint_inventory)
        if key == "cloud_endpoint_group_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.endpoint_groups)
        if key == "cloud_command_related_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return (
                None if profile is None else len(profile.command_related_endpoints)
            )
        if key == "cloud_unresolved_base_url_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.unresolved_base_url_endpoints)
            )
        if key == "cloud_unproven_auth_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.unproven_auth_endpoints)
        if key == "cloud_auth_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.auth_endpoints)
        if key == "cloud_account_auth_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.account_auth_endpoints)
        if key == "cloud_device_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.device_endpoints)
        if key == "cloud_home_device_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.home_device_endpoints)
        if key == "cloud_user_device_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.user_device_endpoints)
        if key == "cloud_local_device_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.local_device_endpoints)
        if key == "cloud_btmesh_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.btmesh_endpoints)
        if key == "cloud_root_device_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.root_device_endpoints)
        if key == "cloud_raw_command_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.raw_command_endpoints)
        if key == "cloud_content_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.content_endpoints)
        if key == "cloud_voice_endpoint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.voice_assistant_endpoints)
        if key == "cloud_document_url_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.document_urls)
        if key == "cloud_auth_token_hint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.auth_token_hints)
        if key == "cloud_device_identity_hint_count":
            profile = cloud_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.device_identity_hints)
            )
        if key == "cloud_http_header_hint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.http_header_hints)
        if key == "cloud_signature_hint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.signature_hints)
        if key == "cloud_request_contract_hint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.request_contract_hints)
        if key == "cloud_token_contract_hint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.token_contract_hints)
        if key == "cloud_header_contract_hint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.header_contract_hints)
        if key == "cloud_signature_contract_hint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.signature_contract_hints)
        if key == "cloud_transport_hint_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.transport_hints)
        if key == "cloud_protocol_gap_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.protocol_gap_hints)
        if key == "cloud_command_blocker_count":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else len(profile.command_blockers)
        if key == "cloud_raw_command_endpoint":
            profile = cloud_profile_for_model(self.model)
            return None if profile is None else _cloud_raw_command_endpoint(profile)
        if key == "car_light_profile":
            return describe_car_light_profile(car_light_profile_for_model(self.model))
        if key == "accessory_role":
            return car_light_accessory_role(self.model)
        if key == "car_light_required_controller":
            if car_light_profile_for_model(self.model) is None:
                return None
            return car_light_required_controller_model(self.model) or "none"
        if key == "car_light_setup_stage":
            return car_light_setup_stage(self.model)
        if key == "car_light_setup_order":
            if car_light_profile_for_model(self.model) is None:
                return None
            setup_order = car_light_setup_order(self.model)
            return "none" if setup_order is None else setup_order
        if key == "car_light_setup_dependency":
            dependency = car_light_setup_dependency_for_model(self.model)
            return None if dependency is None else dependency.relationship
        if key == "car_light_setup_dependency_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.setup_dependencies)
        if key == "car_light_required_setup_dependency_count":
            profile = car_light_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(car_light_required_setup_dependencies(profile))
            )
        if key == "car_light_ordered_setup_model_count":
            profile = car_light_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(car_light_ordered_setup_dependencies(profile))
            )
        if key == "car_light_zone_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.zones)
        if key == "car_light_trigger_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.triggers)
        if key == "car_light_control_surface_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.control_surfaces)
        if key == "car_light_accessory_asset_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.accessory_assets)
        if key == "car_light_animation_asset_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.animation_assets)
        if key == "car_light_trigger_image_asset_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.trigger_image_assets)
        if key == "car_light_zone_image_asset_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.zone_image_assets)
        if key == "car_light_subdevice_hint_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.subdevice_hints)
        if key == "car_light_subdevice_filter_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.subdevice_filters)
        if key == "car_light_password_hint_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.password_hints)
        if key == "car_light_password_flow_state_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.password_flow_states)
        if key == "car_light_password_entry_hint_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.password_entry_hints)
        if key == "car_light_password_policy_hint_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.password_policy_hints)
        if key == "car_light_password_reset_hint_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.password_reset_hints)
        if key == "car_light_trigger_storage_hint_count":
            profile = car_light_profile_for_model(self.model)
            return (
                None if profile is None else len(profile.trigger_storage_hints)
            )
        if key == "car_light_trigger_action_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.trigger_actions)
        if key == "car_light_route_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.route_hints)
        if key == "car_light_setup_requirement_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.setup_requirements)
        if key == "car_light_setup_flow_hint_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.setup_flow_hints)
        if key == "car_light_setup_key_hint_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.setup_key_hints)
        if key == "car_light_app_command_id_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.app_command_id_hints)
        if key == "car_light_model_role_hint_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.model_role_hints)
        if key == "car_light_protocol_gap_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.protocol_gap_hints)
        if key == "car_light_command_blocker_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.command_blockers)
        if key == "car_light_apk_asset_evidence_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_asset_evidence)
        if key == "car_light_apk_package_asset_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else profile.package_asset_count
        if key == "car_light_apk_string_evidence_count":
            profile = car_light_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_string_evidence)
        if key == "fish_tank_profile":
            return describe_fish_tank_profile(fish_tank_profile_for_model(self.model))
        if key == "fish_tank_favorite_slot_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_slots)
        if key == "fish_tank_timer_limit":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else profile.timer_limit
        if key == "fish_tank_light_channel_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.light_channels)
        if key == "fish_tank_control_surface_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.control_surfaces)
        if key == "fish_tank_route_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.route_hints)
        if key == "fish_tank_effect_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.effect_hints)
        if key == "fish_tank_effect_string_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.effect_string_hints)
        if key == "fish_tank_icon_asset_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.icon_assets)
        if key == "fish_tank_image_asset_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.image_assets)
        if key == "fish_tank_channel_asset_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.channel_assets)
        if key == "fish_tank_timer_asset_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.timer_assets)
        if key == "fish_tank_favorite_asset_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_assets)
        if key == "fish_tank_effect_asset_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.effect_assets)
        if key == "fish_tank_workflow_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.workflow_hints)
        if key == "fish_tank_favorite_action_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_action_hints)
        if key == "fish_tank_favorite_store_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_store_hints)
        if key == "fish_tank_favorite_recall_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_recall_hints)
        if key == "fish_tank_favorite_clear_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_clear_hints)
        if key == "fish_tank_favorite_action_type_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_actions)
        if key == "fish_tank_favorite_loop_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_loop_hints)
        if key == "fish_tank_favorite_loop_action_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_loop_actions)
        if key == "fish_tank_firmware_prompt_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.firmware_prompt_hints)
        if key == "fish_tank_timer_slot_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.timer_slots)
        if key == "fish_tank_timer_action_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.timer_actions)
        if key == "fish_tank_timer_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.timer_hints)
        if key == "fish_tank_timer_string_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.timer_string_hints)
        if key == "fish_tank_app_method_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.app_method_hints)
        if key == "fish_tank_app_command_id_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.app_command_id_hints)
        if key == "fish_tank_data_model_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.data_model_hints)
        if key == "fish_tank_favorite_service_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_service_hints)
        if key == "fish_tank_favorite_storage_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_storage_hints)
        if key == "fish_tank_timer_storage_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.timer_storage_hints)
        if key == "fish_tank_brightness_state_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.brightness_state_hints)
        if key == "fish_tank_raw_string_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.raw_string_hints)
        if key == "fish_tank_brightness_string_hint_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.brightness_string_hints)
        if key == "fish_tank_protocol_gap_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.protocol_gap_hints)
        if key == "fish_tank_command_blocker_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.command_blockers)
        if key == "fish_tank_apk_asset_evidence_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_asset_evidence)
        if key == "fish_tank_apk_package_asset_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else profile.package_asset_count
        if key == "fish_tank_apk_string_evidence_count":
            profile = fish_tank_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_string_evidence)
        if key == "scene_profile":
            return describe_scene_profile(scene_profile_for_model(self.model))
        if key == "scene_preset_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.presets)
        if key == "scene_control_surface_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.control_surfaces)
        if key == "scene_route_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.route_hints)
        if key == "scene_mode_icon_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else profile.mode_icon_count
        if key == "scene_mode_effect_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.mode_effects)
        if key == "scene_mode_icon_sample_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.mode_icon_samples)
        if key == "scene_lfx_route_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.lfx_route_hints)
        if key == "scene_timer_route_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.timer_route_hints)
        if key == "scene_app_method_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.app_method_hints)
        if key == "scene_app_command_id_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.app_command_id_hints)
        if key == "scene_storage_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.storage_hints)
        if key == "scene_recent_action_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.recent_actions)
        if key == "scene_favorite_action_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_actions)
        if key == "scene_timer_action_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.timer_actions)
        if key == "scene_diy_action_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.diy_actions)
        if key == "scene_white_brightness_anchor_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.white_brightness_anchors)
        if key == "scene_raw_string_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.raw_string_hints)
        if key == "scene_lfx_data_model_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.lfx_data_model_hints)
        if key == "scene_lfx_frame_field_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.lfx_frame_field_hints)
        if key == "scene_native_handler_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_handler_hints)
        if key == "scene_native_paired_api_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(
                profile.native_paired_api_capabilities
            )
        if key == "scene_native_ic_only_api_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(
                profile.native_ic_only_api_capabilities
            )
        if key == "scene_native_loop_handler_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_loop_handlers)
        if key == "scene_native_library_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_library_hints)
        if key == "scene_native_frame_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_frame_hints)
        if key == "scene_native_opcode_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_opcode_hints)
        if key == "scene_native_state_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_state_hints)
        if key == "scene_native_state_export_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_state_exports)
        if key == "scene_native_color_order_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_color_order_hints)
        if key == "scene_native_pwm_table_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_pwm_table_hints)
        if key == "scene_native_music_effect_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_music_effect_hints)
        if key == "scene_native_pwm_driver_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_pwm_driver_hints)
        if key == "scene_native_animation_export_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_animation_exports)
        if key == "scene_native_drive_export_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_drive_exports)
        if key == "scene_native_persistence_handler_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_persistence_handlers)
        if key == "scene_native_persistence_export_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_persistence_exports)
        if key == "scene_native_persistence_capability_count":
            profile = scene_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.native_persistence_capabilities)
            )
        if key == "scene_native_export_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_export_hints)
        if key == "scene_native_code_anchor_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.native_code_anchors)
        if key == "scene_setup_requirement_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.setup_requirements)
        if key == "scene_catalog_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.catalog_hints)
        if key == "scene_transport_hint_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.transport_hints)
        if key == "scene_protocol_gap_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.protocol_gap_hints)
        if key == "scene_command_blocker_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.command_blockers)
        if key == "scene_apk_asset_evidence_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_asset_evidence)
        if key == "scene_apk_package_asset_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else profile.package_asset_count
        if key == "scene_apk_string_evidence_count":
            profile = scene_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_string_evidence)
        if key == "network_profile":
            return describe_network_profile(network_profile_for_model(self.model))
        if key == "network_surface_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.control_surfaces)
        if key == "network_content_mode_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.content_modes)
        if key == "network_artnet_field_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.artnet_fields)
        if key == "network_port_field_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.port_fields)
        if key == "network_playlist_action_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.playlist_actions)
        if key == "network_matrix_music_control_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.matrix_music_controls)
        if key == "network_lfx_effect_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.regular_lfx_effects)
        if key == "network_lfx_gif_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else profile.lfx_gif_count
        if key == "network_route_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.route_hints)
        if key == "network_regular_lfx_effect_asset_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.regular_lfx_effect_assets)
        if key == "network_lfx_gif_asset_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.lfx_gif_assets)
        if key == "network_app_method_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.app_method_hints)
        if key == "network_app_command_id_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.app_command_id_hints)
        if key == "network_workflow_hint_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.workflow_hints)
        if key == "network_raw_string_hint_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.raw_string_hints)
        if key == "network_import_constraint_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.import_constraints)
        if key == "network_catalog_hint_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.catalog_hints)
        if key == "network_transport_hint_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.transport_hints)
        if key == "network_native_library_hint_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.native_library_hints)
        if key == "network_native_frame_hint_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.native_frame_hints)
        if key == "network_native_lfx_param_hint_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.native_lfx_param_hints)
        if key == "network_native_effect_generator_hint_count":
            profile = network_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.native_effect_generator_hints)
            )
        if key == "network_native_matrix_mode_hint_count":
            profile = network_profile_for_model(self.model)
            return (
                None if profile is None else len(profile.native_matrix_mode_hints)
            )
        if key == "network_native_pixel_helper_hint_count":
            profile = network_profile_for_model(self.model)
            return (
                None if profile is None else len(profile.native_pixel_helper_hints)
            )
        if key == "network_native_export_hint_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.native_export_hints)
        if key == "network_native_export_detail_count":
            profile = network_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.native_export_detail_anchors)
            )
        if key == "network_protocol_gap_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.protocol_gap_hints)
        if key == "network_command_blocker_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.command_blockers)
        if key == "network_apk_asset_evidence_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_asset_evidence)
        if key == "network_apk_package_asset_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else profile.package_asset_count
        if key == "network_apk_string_evidence_count":
            profile = network_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_string_evidence)
        if key == "network_info":
            return _network_info_diagnostic(self)
        if key == "max_data_length":
            return self.model.features.get("maxDataLength")
        if key == "max_pixel_channels":
            return self.model.features.get("maxPixelChannels")
        if key == "custom_effect_slot":
            return _custom_effect_slot_diagnostic(self)
        if key == "sp630e_profile":
            return describe_sp630e_profile(sp630e_profile_for_model(self.model))
        if key == "sp630e_route_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.route_hints)
        if key == "sp630e_control_surface_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.control_surfaces)
        if key == "sp630e_favorite_limit_hint_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.favorite_limit_hints)
        if key == "sp630e_timer_limit":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else profile.timer_limit
        if key == "sp630e_timer_hint_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.timer_hints)
        if key == "sp630e_music_asset_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.music_asset_hints)
        if key == "sp630e_network_hint_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.network_hints)
        if key == "sp630e_remote_hint_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.remote_hints)
        if key == "sp630e_motor_hint_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.motor_hints)
        if key == "sp630e_app_method_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.app_method_hints)
        if key == "sp630e_app_command_id_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.app_command_id_hints)
        if key == "sp630e_data_model_hint_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.data_model_hints)
        if key == "sp630e_native_lfx_hint_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.native_lfx_hints)
        if key == "sp630e_native_export_detail_count":
            profile = sp630e_profile_for_model(self.model)
            return (
                None
                if profile is None
                else len(profile.native_export_detail_anchors)
            )
        if key == "sp630e_catalog_hint_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.catalog_hints)
        if key == "sp630e_protocol_gap_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.protocol_gap_hints)
        if key == "sp630e_apk_asset_evidence_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_asset_evidence)
        if key == "sp630e_apk_package_asset_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else profile.package_asset_count
        if key == "sp630e_apk_string_evidence_count":
            profile = sp630e_profile_for_model(self.model)
            return None if profile is None else len(profile.apk_string_evidence)
        if key == "timer_count":
            if key in self.state.diagnostics:
                return self.state.diagnostics[key]
            return _channel_extra_int_diagnostic(
                self,
                key,
                families=(ProtocolFamily.BANLANX_V2,),
            )
        if key in {"diy_effect_type", "diy_color_count"}:
            return _channel_extra_int_diagnostic(
                self,
                key,
                families=(ProtocolFamily.BANLANX_V3,),
            )
        if key in self.state.diagnostics:
            return self.state.diagnostics[key]
        return None

    def attach_transport(self, transport: CommandTransport) -> DeviceSession:
        """Attach a byte transport and create a command session."""
        if self.protocol is None:
            raise RuntimeSetupError(
                f"{self.model.name} does not have a command protocol yet"
            )
        self.transport = transport
        self.session = DeviceSession(self.protocol, transport)
        self.notification_assembler = self.session.assembler
        self.state.diagnostics["session_ready"] = True
        return self.session

    def attach_lan_transport(
        self,
        transport: Any,
        *,
        host: str | None = None,
        profile: LANProfile | None = None,
    ) -> Any:
        """Attach a LAN host holder without enabling command sessions."""
        profile = profile or lan_profile_for_model(self.model)
        if profile is None:
            raise RuntimeSetupError(f"{self.model.name} does not have a LAN profile")

        host = str(host or self.entry_data.get(CONF_HOST, "")).strip()
        if not host:
            raise RuntimeSetupError("LAN transport attachment requires a host")

        self.transport = transport
        self.lan_profile = profile
        self.state.diagnostics.update(
            {
                "lan_transport_ready": True,
                "lan_manual_host_configured": True,
            }
        )
        return transport

    def attach_zengge_mesh_transport(
        self,
        transport: ZenggeMeshTransport,
        *,
        mesh_uuid: int | None = None,
        address: str | None = None,
        block_encryptor: Any | None = None,
    ) -> ZenggeMeshConnection:
        """Attach a Zengge mesh transport connection."""
        if self.model.family is not ProtocolFamily.ZENGGE_MESH:
            raise RuntimeSetupError(f"{self.model.name} is not a Zengge mesh model")

        address = str(address or self.entry_data.get(CONF_ADDRESS, "")).strip()
        if not address:
            raise RuntimeSetupError("Zengge mesh attachment requires a BLE address")

        profile = mesh_profile_for_model(self.model)
        mesh_uuid = int(
            mesh_uuid
            or self.entry_data.get(CONF_MESH_UUID)
            or (profile.default_mesh_uuid if profile is not None else 0)
        )
        session = ZenggeMeshSession(
            mesh_uuid=mesh_uuid,
            address=address,
            block_encryptor=block_encryptor,
        )
        _register_zengge_entry_nodes(session, self.entry_data, address=address)

        self.transport = transport
        self.mesh_session = session
        self.mesh_connection = ZenggeMeshConnection(session, transport)
        self.state.diagnostics.update(
            {
                "mesh_transport_ready": True,
                "mesh_session_paired": False,
                "mesh_uuid": mesh_uuid,
            }
        )
        return self.mesh_connection

    async def async_close(self) -> None:
        """Close runtime resources."""
        transport = self.transport
        try:
            if transport is not None and hasattr(transport, "close"):
                await transport.close()
        except Exception as ex:  # noqa: BLE001
            self.state.diagnostics["last_close_error"] = str(ex)
        finally:
            self.transport = None
            self.session = None
            self.lan_profile = None
            self.mesh_session = None
            self.mesh_connection = None
            self.coordinator = None
            self.notification_assembler = None


def build_runtime(
    entry_data: Mapping[str, Any],
    *,
    catalog: ModelCatalog | None = None,
) -> UniLEDRuntime:
    """Build runtime data from a config entry data mapping."""
    catalog = catalog or default_catalog()
    model_name = str(entry_data.get(CONF_MODEL, "")).strip()
    if not model_name:
        raise RuntimeSetupError(
            "config entry is missing a model",
            field=CONF_MODEL,
            reason="required",
        )

    model_id = _entry_model_id(entry_data.get(CONF_MODEL_ID))
    model = catalog.resolve_model_label(model_name, model_id=model_id)
    if model is None or not model.is_user_facing:
        if model_id is not None and catalog.resolve_label(model_name) is not None:
            raise RuntimeSetupError(
                f"stored model_id {model_id} does not match UniLED model "
                f"{model_name}",
                field=CONF_MODEL_ID,
                reason="unknown_model_id",
            )
        suffix = f" ({model_id})" if model_id is not None else ""
        raise RuntimeSetupError(
            f"unknown or filtered UniLED model: {model_name}{suffix}",
            field=CONF_MODEL,
            reason="unknown_model",
        )

    protocol = protocol_for_model(model)
    state = DeviceState(
        available=False,
        model=model.name,
        diagnostics={
            "protocol_family": model.family.value,
            "support_level": model.support_level.value,
            "protocol_ready": protocol is not None,
            "session_ready": False,
        },
    )
    return UniLEDRuntime(
        catalog=catalog,
        model=model,
        entity_plan=plan_for_model(model),
        protocol=protocol,
        state=state,
        entry_data=dict(entry_data),
    )


def support_disposition(runtime: UniLEDRuntime) -> str:
    """Return a compact, conservative support-status diagnostic."""
    model = runtime.model
    if model.support_level is SupportLevel.FILTERED:
        return "filtered"

    parts = [
        model.support_level.value,
        f"setup={_local_setup_disposition(model)}",
    ]

    if model.family is ProtocolFamily.ZENGGE_MESH:
        mesh_profile = mesh_profile_for_model(model)
        parts.extend(
            (
                "zengge_mesh_limited",
                "pair_required",
                "node_commands_guarded",
                "panel_status_sensors",
            )
        )
        if mesh_profile is not None:
            parts.extend(mesh_profile.control_blockers)
    elif runtime.protocol is not None:
        parts.extend(("command_protocol_ready", "state_refresh_ready"))
        if model.legacy_uniled_supported:
            parts.append("old_uniled_parity")
        elif model.family is ProtocolFamily.BANLANX_CUSTOM_5XX:
            parts.append("sp6xx_style_ble_commands")
        elif protocol_evidence_profile_for_model(model) is not None:
            parts.append("apk_protocol_inference")
    else:
        parts.extend(("diagnostic_only", "command_protocol_pending"))
        if _has_apk_family_profile(model):
            parts.append("apk_profile_ready")
        if _is_legacy_uniled_only_model(model):
            parts.append("legacy_only_autodiscovery_ready")
            parts.append("legacy_only_command_port_pending")
            parts.append("legacy_only_status_parser_pending")
        ble_profile = ble_evidence_for_model(model)
        if ble_profile is not None and not ble_profile.command_profile_known:
            parts.append("ble_uuid_binding_pending")
        car_light_profile = car_light_profile_for_model(model)
        if (
            car_light_profile is not None
            and not car_light_profile.command_protocol_known
        ):
            parts.extend(car_light_command_blockers_for_model(model))
        if TransportKind.LAN in model.transports:
            parts.append("lan_frame_pending")
            network_profile = network_profile_for_model(model)
            if (
                network_profile is not None
                and not network_profile.command_protocol_known
            ):
                parts.extend(network_profile.command_blockers)
        fish_tank_profile = fish_tank_profile_for_model(model)
        if (
            fish_tank_profile is not None
            and not fish_tank_profile.command_protocol_known
        ):
            parts.extend(fish_tank_profile.command_blockers)
        if TransportKind.BLE_MESH in model.transports:
            parts.append("mesh_frame_pending")
        scene_profile = scene_profile_for_model(model)
        if (
            scene_profile is not None
            and not scene_profile.command_protocol_known
        ):
            parts.extend(scene_profile.command_blockers)
        if model.family is ProtocolFamily.BANLANX_SCENE_MESH:
            mesh_profile = mesh_profile_for_model(model)
            if mesh_profile is not None and mesh_profile.provisioning_hints:
                parts.append("firmware_v1_1_required")
                parts.append("provisioning_frame_pending")
            if mesh_profile is not None and mesh_profile.control_gap_hints:
                parts.append("scene_mesh_routing_pending")

    if runtime.protocol is not None and TransportKind.LAN in model.transports:
        lan_profile = lan_profile_for_model(model)
        parts.append(
            "lan_frame_ready"
            if lan_profile is not None and lan_profile.command_protocol_known
            else "lan_frame_pending"
        )
    if TransportKind.CLOUD_OPTIONAL in model.transports:
        parts.append("cloud_optional")
        cloud_profile = cloud_profile_for_model(model)
        if cloud_profile is not None and not cloud_profile.command_protocol_known:
            parts.extend(cloud_profile.command_blockers)
    required_controller = car_light_required_controller_model(model)
    if required_controller is not None:
        parts.append(f"accessory_dependency={required_controller}")

    return "; ".join(parts)


def support_blockers(runtime: UniLEDRuntime) -> tuple[str, ...]:
    """Return open blockers and requirements from the support disposition."""
    return tuple(
        token
        for token in support_disposition(runtime).split("; ")
        if token.endswith("_pending")
        or token.endswith("_required")
        or token.startswith("accessory_dependency=")
    )


def _local_setup_disposition(model: CatalogModel) -> str:
    """Return local setup transports, excluding optional cloud capability."""
    setup_transports = tuple(
        transport.value
        for transport in model.transports
        if transport is not TransportKind.CLOUD_OPTIONAL
    )
    return ",".join(setup_transports) or "manual"


def _configured_transport(entry_data: Mapping[str, Any]) -> str:
    """Return the normalized transport selected by the config entry."""
    transport = str(entry_data.get(CONF_TRANSPORT, "") or "").strip()
    return transport or "manual"


def _entry_data_text(entry_data: Mapping[str, Any], key: str) -> str | None:
    """Return an optional config-entry text diagnostic."""
    value = str(entry_data.get(key, "") or "").strip()
    return value or None


def _catalog_connect_capabilities(model: CatalogModel) -> str:
    """Return the decoded APK connectCaps capability labels."""
    return ", ".join(model.connect_capabilities) or "none"


def _catalog_spec_function_bits(model: CatalogModel) -> str:
    """Return the decoded APK specFunctions bit labels."""
    return ", ".join(model.spec_function_bits) or "none"


def _catalog_color_capabilities(model: CatalogModel) -> str:
    """Return the decoded APK colorCap labels."""
    return ", ".join(model.color_capabilities) or "none"


def _catalog_feature_keys(model: CatalogModel) -> str:
    """Return the selected APK catalog extra-feature keys."""
    return ", ".join(model.feature_keys) or "none"


def _catalog_feature_summary(model: CatalogModel) -> str:
    """Return selected APK catalog extra-feature key/value pairs."""
    if not model.features:
        return "none"
    return "; ".join(
        f"{key}={model.features[key]}"
        for key in model.feature_keys
    )


def _format_tuple(values: tuple[str, ...]) -> str:
    """Return a comma-separated diagnostic string or none."""
    return ", ".join(values) or "none"


def _catalog_variant_ids(catalog: ModelCatalog, model: CatalogModel) -> str:
    """Return all user-facing APK model IDs for the selected display name."""
    ids = [
        str(variant.model_id)
        for variant in catalog.models_for_name(model.name)
        if variant.is_user_facing
    ]
    return ", ".join(ids) or "none"


def _runtime_transport_state(runtime: UniLEDRuntime) -> str:
    """Return the concrete runtime attachment mode."""
    if runtime.session_ready:
        return "command_session"
    if runtime.mesh_transport_ready:
        if runtime.mesh_session_paired:
            return "mesh_transport_paired"
        return "mesh_transport"
    if runtime.lan_transport_ready:
        return "lan_transport_holder"
    if runtime.transport is not None:
        return "transport_holder"
    return "diagnostic_only"


def _has_apk_family_profile(model: CatalogModel) -> bool:
    """Return whether a recognized family has APK-derived profile diagnostics."""
    return any(
        profile is not None
        for profile in (
            scene_profile_for_model(model),
            sp630e_profile_for_model(model),
            network_profile_for_model(model),
            car_light_profile_for_model(model),
            fish_tank_profile_for_model(model),
            cloud_profile_for_model(model),
        )
    )


def _is_legacy_uniled_only_model(model: CatalogModel) -> bool:
    """Return whether a model is sourced only from detached old UniLED code."""
    return model.home_uri.startswith("/legacy/uniled/")


def runtime_diagnostics(
    runtime: UniLEDRuntime,
    *,
    entry_data: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return sanitized diagnostics for a runtime."""
    data = runtime.entry_data if entry_data is None else entry_data
    default_model = runtime.catalog.resolve_name(runtime.model.name)
    default_model_id = None if default_model is None else default_model.model_id
    return {
        "entry": _redact(data),
        "model": {
            "id": runtime.model.model_id,
            "name": runtime.model.name,
            "family": runtime.model.family.value,
            "support_level": runtime.model.support_level.value,
            "support_disposition": support_disposition(runtime),
            "support_blockers": list(support_blockers(runtime)),
            "connect_caps": runtime.model.connect_caps,
            "connect_capabilities": list(runtime.model.connect_capabilities),
            "spec_functions": runtime.model.spec_functions,
            "spec_function_bits": list(runtime.model.spec_function_bits),
            "color_cap": runtime.model.color_cap,
            "color_capabilities": list(runtime.model.color_capabilities),
            "feature_keys": list(runtime.model.feature_keys),
            "features": dict(runtime.model.features),
            "transports": [transport.value for transport in runtime.model.transports],
            "legacy_uniled_supported": runtime.model.legacy_uniled_supported,
            "legacy_uniled_parity_profile": _legacy_uniled_parity_profile_dict(
                legacy_uniled_parity_profile_for_model(runtime.model)
            ),
            "protocol_evidence_profile": _protocol_evidence_profile_dict(
                protocol_evidence_profile_for_model(runtime.model)
            ),
            "catalog_variants": [
                _catalog_variant_dict(
                    variant,
                    canonical=variant.model_id == default_model_id,
                    selected=variant.model_id == runtime.model.model_id,
                )
                for variant in runtime.catalog.models_for_name(runtime.model.name)
                if variant.is_user_facing
            ],
            "ble_profile": _ble_evidence_profile_dict(
                ble_evidence_for_model(runtime.model)
            ),
            "lan_profile": _lan_profile_dict(lan_profile_for_model(runtime.model)),
            "mesh_profile": _mesh_profile_dict(mesh_profile_for_model(runtime.model)),
            "cloud_profile": _cloud_profile_dict(
                cloud_profile_for_model(runtime.model)
            ),
            "car_light_profile": _car_light_profile_dict(
                car_light_profile_for_model(runtime.model)
            ),
            "car_light_accessory_role": car_light_accessory_role(runtime.model),
            "car_light_model_role": _car_light_model_role_dict(
                car_light_model_role_for_model(runtime.model)
            ),
            "car_light_required_controller": car_light_required_controller_model(
                runtime.model
            ),
            "fish_tank_profile": _fish_tank_profile_dict(
                fish_tank_profile_for_model(runtime.model)
            ),
            "scene_profile": _scene_profile_dict(
                scene_profile_for_model(runtime.model)
            ),
            "sp630e_profile": _sp630e_profile_dict(
                sp630e_profile_for_model(runtime.model)
            ),
            "network_profile": _network_profile_dict(
                network_profile_for_model(runtime.model)
            ),
        },
        "runtime": {
            "protocol_ready": runtime.protocol_ready,
            "session_ready": runtime.session_ready,
            "lan_transport_ready": runtime.lan_transport_ready,
            "mesh_transport_ready": runtime.mesh_transport_ready,
            "mesh_session_paired": runtime.mesh_session_paired,
            "transport_attached": runtime.transport is not None,
            "runtime_transport_state": _runtime_transport_state(runtime),
            "available": runtime.state.available,
            "firmware": runtime.state.firmware,
        },
        "entity_plan": [
            {
                "key": feature.key,
                "platform": feature.platform.value,
                "implemented": feature.implemented,
                "enabled_by_default": feature.enabled_by_default,
            }
            for feature in runtime.entity_plan.features
        ],
        "diagnostics": _json_safe_mapping(runtime.state.diagnostics),
    }


def _cloud_endpoint_count(profile: BanlanXCloudProfile) -> int:
    """Return the total recovered BanlanX cloud endpoint/path count."""
    return (
        len(profile.auth_endpoints)
        + len(profile.account_auth_endpoints)
        + len(profile.device_endpoints)
        + len(profile.content_endpoints)
        + len(profile.voice_assistant_endpoints)
    )


def _cloud_raw_command_endpoint(profile: BanlanXCloudProfile) -> str | None:
    """Return the recovered raw device-post endpoint, if present."""
    return profile.raw_command_endpoints[0] if profile.raw_command_endpoints else None


def _network_info_diagnostic(runtime: UniLEDRuntime) -> Any:
    """Return live network info or the APK/catalog query evidence."""
    live = runtime.state.diagnostics.get("network_info")
    if live is not None:
        return live

    code = runtime.model.features.get("supportGetNetInfo")
    if code is None or isinstance(code, bool):
        return None

    try:
        code_text = str(int(code))
    except (TypeError, ValueError):
        code_text = str(code)

    profile = lan_profile_for_model(runtime.model)
    protocol_status = (
        "command_protocol_known"
        if profile is not None and profile.command_protocol_known
        else "command_protocol_pending"
    )
    return f"supportGetNetInfo={code_text}; {protocol_status}"


def _custom_effect_slot_diagnostic(runtime: UniLEDRuntime) -> int | None:
    """Return the old-UniLED SP6xx custom/DIY slot status byte."""
    if not banlanx6xx_style_family(runtime.model.family):
        return None

    return _channel_extra_int_diagnostic(
        runtime,
        "diy_mode",
        families=(runtime.model.family,),
    )


def _channel_extra_int_diagnostic(
    runtime: UniLEDRuntime,
    key: str,
    *,
    families: tuple[ProtocolFamily, ...],
) -> int | None:
    """Return an integer diagnostic from the primary channel extras."""
    if runtime.model.family not in families:
        return None

    channel = runtime.state.channels.get(0)
    if channel is None:
        return None

    value = channel.extra.get(key)
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def apply_runtime_state(
    runtime: UniLEDRuntime,
    state: DeviceState,
) -> DeviceState:
    """Attach runtime metadata to a parsed device state."""
    previous = runtime.state
    state.model = state.model or runtime.model.name
    state.firmware = state.firmware or previous.firmware
    state.available = True
    state.diagnostics = {
        "protocol_family": runtime.model.family.value,
        "support_level": runtime.model.support_level.value,
        "protocol_ready": runtime.protocol_ready,
        "session_ready": runtime.session_ready,
        "lan_transport_ready": runtime.lan_transport_ready,
        "mesh_transport_ready": runtime.mesh_transport_ready,
        "mesh_session_paired": runtime.mesh_session_paired,
        **previous.diagnostics,
        **state.diagnostics,
    }
    runtime.state = state
    if runtime.session is not None:
        runtime.session.state = state
    return state


async def async_refresh_runtime_state(
    runtime: UniLEDRuntime,
    *,
    response_timeout: float = 5.0,
) -> DeviceState:
    """Refresh runtime state from an attached command session."""
    session = runtime.session
    if session is None:
        return mark_runtime_refresh_without_session(runtime)

    state = await session.refresh_state(response_timeout=response_timeout)
    if state is None:
        runtime.state.available = False
        runtime.state.diagnostics["last_refresh_result"] = "no_response"
        return runtime.state

    state.diagnostics["last_refresh_result"] = "ok"
    return apply_runtime_state(runtime, state)


def mark_runtime_refresh_without_session(runtime: UniLEDRuntime) -> DeviceState:
    """Record that a command refresh could not run without a session."""
    runtime.state.available = False
    runtime.state.diagnostics["last_refresh_result"] = "no_session"
    return runtime.state


def zengge_mesh_credentials(runtime: UniLEDRuntime) -> tuple[bytes, bytes]:
    """Return mesh name/password bytes for a Zengge runtime."""
    mesh_name = _credential_bytes(
        runtime.entry_data.get(CONF_MESH_KEY),
        default=ZENGGE_DEFAULT_MESH_KEY,
    )
    mesh_password = _credential_bytes(
        runtime.entry_data.get(CONF_MESH_PASSWORD),
        default=ZENGGE_DEFAULT_MESH_PASS,
    )
    return mesh_name, mesh_password


async def async_pair_zengge_mesh(
    runtime: UniLEDRuntime,
    *,
    session_random: bytes | None = None,
) -> bytes:
    """Pair an attached Zengge mesh connection using entry credentials."""
    if runtime.mesh_connection is None:
        raise RuntimeSetupError("Zengge mesh transport is not attached")
    mesh_name, mesh_password = zengge_mesh_credentials(runtime)
    session_key = await runtime.mesh_connection.pair(
        mesh_name,
        mesh_password,
        session_random=session_random,
    )
    runtime.state.diagnostics["mesh_session_paired"] = runtime.mesh_session_paired
    return session_key


async def async_refresh_zengge_mesh_state(
    runtime: UniLEDRuntime,
    *,
    session_random: bytes | None = None,
) -> DeviceState:
    """Pair and request Zengge mesh status without exposing command entities."""
    connection = runtime.mesh_connection
    if connection is None:
        return runtime.state

    try:
        if not runtime.mesh_session_paired:
            await async_pair_zengge_mesh(runtime, session_random=session_random)
            runtime.state.diagnostics["last_mesh_pair_result"] = "ok"
        await connection.request_status()
        runtime.state.diagnostics["last_mesh_status_request"] = "ok"
        runtime.state.diagnostics["mesh_session_paired"] = runtime.mesh_session_paired
        runtime.state.available = runtime.mesh_session_paired
    except (RuntimeSetupError, TransportError, ZenggeCryptoError) as ex:
        runtime.state.available = False
        runtime.state.diagnostics["last_mesh_pair_result"] = "failed"
        runtime.state.diagnostics["last_mesh_pair_error"] = str(ex)
        runtime.state.diagnostics["mesh_session_paired"] = runtime.mesh_session_paired
    return runtime.state


def zengge_mesh_node_ids(runtime: UniLEDRuntime) -> tuple[int, ...]:
    """Return known command-capable Zengge mesh node IDs."""
    if runtime.model.family is not ProtocolFamily.ZENGGE_MESH:
        return ()
    return tuple(
        sorted(
            node_id
            for node_id in _zengge_mesh_known_node_ids(runtime)
            if _is_zengge_command_node(runtime, node_id)
        )
    )


def zengge_mesh_panel_node_ids(runtime: UniLEDRuntime) -> tuple[int, ...]:
    """Return known Zengge RGB/CCT panel node IDs."""
    if runtime.model.family is not ProtocolFamily.ZENGGE_MESH:
        return ()
    return tuple(
        sorted(
            node_id
            for node_id in _zengge_mesh_known_node_ids(runtime)
            if _is_zengge_panel_node(runtime, node_id)
        )
    )


def zengge_mesh_command_ready(
    runtime: UniLEDRuntime,
    node_id: int | None = None,
) -> bool:
    """Return whether a Zengge mesh command can be sent now."""
    if runtime.model.family is not ProtocolFamily.ZENGGE_MESH:
        return False
    if runtime.mesh_connection is None or not runtime.mesh_session_paired:
        return False
    if node_id is None:
        return bool(zengge_mesh_node_ids(runtime))
    return int(node_id) in zengge_mesh_node_ids(runtime)


def zengge_mesh_light_features(runtime: UniLEDRuntime) -> tuple[FeatureSpec, ...]:
    """Return command-capable Zengge mesh node lights."""
    if not zengge_mesh_command_ready(runtime):
        return ()
    return tuple(
        FeatureSpec(
            key=f"mesh_light_{node_id:02x}",
            platform=PlatformKind.LIGHT,
            name=_zengge_mesh_light_name(runtime, node_id),
            channel=node_id,
            enabled_by_default=True,
            implemented=True,
            color_modes=light_supported_color_modes(runtime, channel=node_id),
            implementation_hint="zengge_mesh_node",
        )
        for node_id in zengge_mesh_node_ids(runtime)
    )


def zengge_mesh_select_features(runtime: UniLEDRuntime) -> tuple[FeatureSpec, ...]:
    """Return command-capable Zengge mesh node selects."""
    if not zengge_mesh_command_ready(runtime):
        return ()
    return tuple(
        FeatureSpec(
            key="effect",
            platform=PlatformKind.SELECT,
            name=f"{_zengge_mesh_light_name(runtime, node_id)} effect",
            channel=node_id,
            enabled_by_default=True,
            implemented=True,
            options=select_options(runtime, "effect", channel=node_id),
            implementation_hint="zengge_mesh_node",
        )
        for node_id in zengge_mesh_node_ids(runtime)
        if select_options(runtime, "effect", channel=node_id)
    )


def zengge_mesh_number_features(runtime: UniLEDRuntime) -> tuple[FeatureSpec, ...]:
    """Return command-capable Zengge mesh node effect number controls."""
    if not zengge_mesh_command_ready(runtime):
        return ()

    features: list[FeatureSpec] = []
    for node_id in zengge_mesh_node_ids(runtime):
        name = _zengge_mesh_light_name(runtime, node_id)
        features.extend(
            (
                FeatureSpec(
                    key="effect_speed",
                    platform=PlatformKind.NUMBER,
                    name=f"{name} effect speed",
                    channel=node_id,
                    entity_category=EntityCategoryKind.CONFIG,
                    enabled_by_default=True,
                    implemented=True,
                    minimum=0,
                    maximum=100,
                    step=1,
                    implementation_hint="zengge_mesh_node",
                ),
                FeatureSpec(
                    key="effect_level",
                    platform=PlatformKind.NUMBER,
                    name=f"{name} effect level",
                    channel=node_id,
                    entity_category=EntityCategoryKind.CONFIG,
                    enabled_by_default=True,
                    implemented=True,
                    minimum=0,
                    maximum=100,
                    step=1,
                    implementation_hint="zengge_mesh_node",
                ),
            )
        )
    return tuple(features)


def zengge_mesh_panel_sensor_features(
    runtime: UniLEDRuntime,
) -> tuple[FeatureSpec, ...]:
    """Return diagnostic sensors for known Zengge panel nodes."""
    return tuple(
        FeatureSpec(
            key=f"{_ZENGGE_PANEL_STATUS_PREFIX}{node_id:02x}"
            f"{_ZENGGE_PANEL_STATUS_SUFFIX}",
            platform=PlatformKind.SENSOR,
            name=_zengge_mesh_panel_name(runtime, node_id),
            channel=node_id,
            entity_category=EntityCategoryKind.DIAGNOSTIC,
            enabled_by_default=True,
            implemented=True,
            implementation_hint="zengge_mesh_panel",
        )
        for node_id in zengge_mesh_panel_node_ids(runtime)
    )


async def set_zengge_mesh_power(
    runtime: UniLEDRuntime,
    node_id: int,
    power: bool,
    *,
    gradual_seconds: float = 0.0,
    sequence: bytes | None = None,
    response: bool = False,
) -> bytes | None:
    """Send a guarded Zengge mesh power command and update optimistic state."""
    connection, node_id = _require_zengge_mesh_command(runtime, node_id)
    result = await connection.send_power(
        node_id,
        power,
        gradual_seconds=gradual_seconds,
        sequence=sequence,
        response=response,
    )
    _apply_zengge_mesh_light_state(runtime, node_id, "power", power=power)
    return result


async def set_zengge_mesh_brightness(
    runtime: UniLEDRuntime,
    node_id: int,
    level: int,
    *,
    gradual_seconds: float = 0.0,
    sequence: bytes | None = None,
    response: bool = False,
) -> bytes | None:
    """Send a guarded Zengge mesh brightness command and update state."""
    connection, node_id = _require_zengge_mesh_command(runtime, node_id)
    result = await connection.send_brightness(
        node_id,
        level,
        gradual_seconds=gradual_seconds,
        sequence=sequence,
        response=response,
    )
    _apply_zengge_mesh_light_state(
        runtime,
        node_id,
        "brightness",
        brightness=level,
    )
    return result


async def set_zengge_mesh_rgb(
    runtime: UniLEDRuntime,
    node_id: int,
    red: int,
    green: int,
    blue: int,
    *,
    gradual_seconds: float = 0.0,
    sequence: bytes | None = None,
    response: bool = False,
) -> bytes | None:
    """Send a guarded Zengge mesh RGB command and update optimistic state."""
    connection, node_id = _require_zengge_mesh_command(runtime, node_id)
    result = await connection.send_rgb(
        node_id,
        red,
        green,
        blue,
        gradual_seconds=gradual_seconds,
        sequence=sequence,
        response=response,
    )
    _apply_zengge_mesh_light_state(runtime, node_id, "rgb", rgb=(red, green, blue))
    return result


async def set_zengge_mesh_color_temp(
    runtime: UniLEDRuntime,
    node_id: int,
    kelvin: int,
    *,
    level: int = 255,
    gradual_seconds: float = 0.0,
    sequence: bytes | None = None,
    response: bool = False,
) -> bytes | None:
    """Send a guarded Zengge mesh color-temperature command."""
    connection, node_id = _require_zengge_mesh_command(runtime, node_id)
    result = await connection.send_cct(
        node_id,
        kelvin,
        level=level,
        gradual_seconds=gradual_seconds,
        sequence=sequence,
        response=response,
    )
    _apply_zengge_mesh_light_state(
        runtime,
        node_id,
        "color_temp",
        brightness=level,
        color_temp_kelvin=kelvin,
    )
    return result


async def set_zengge_mesh_white(
    runtime: UniLEDRuntime,
    node_id: int,
    white: int,
    *,
    gradual_seconds: float = 0.0,
    sequence: bytes | None = None,
    response: bool = False,
) -> bytes | None:
    """Send a guarded Zengge mesh warm-white command."""
    connection, node_id = _require_zengge_mesh_command(runtime, node_id)
    result = await connection.send_white(
        node_id,
        white,
        gradual_seconds=gradual_seconds,
        sequence=sequence,
        response=response,
    )
    _apply_zengge_mesh_light_state(runtime, node_id, "white", white=white)
    return result


async def set_zengge_mesh_effect(
    runtime: UniLEDRuntime,
    node_id: int,
    effect: int,
    *,
    speed: int = 0,
    level: int = 100,
    sequence: bytes | None = None,
    response: bool = False,
) -> bytes | None:
    """Send a guarded Zengge mesh dynamic-effect command."""
    connection, node_id = _require_zengge_mesh_command(runtime, node_id)
    result = await connection.send_effect(
        node_id,
        effect,
        speed=speed,
        level=level,
        sequence=sequence,
        response=response,
    )
    _apply_zengge_mesh_light_state(
        runtime,
        node_id,
        "effect",
        brightness=level,
        effect=effect,
        effect_speed=speed,
        effect_level=level,
    )
    return result


def zengge_mesh_effect_command_values(
    runtime: UniLEDRuntime,
    node_id: int,
    *,
    effect: int | None = None,
    speed: int | None = None,
    level: int | None = None,
) -> tuple[int, int, int]:
    """Return complete Zengge effect command values for partial number edits."""
    state = channel_state(runtime, int(node_id))
    effect_value = effect if effect is not None else state.effect_number
    speed_value = speed if speed is not None else state.effect_speed
    level_value = level if level is not None else _optional_int(
        state.extra.get("effect_level")
    )

    if effect_value is None:
        effect_value = 1
    if speed_value is None:
        speed_value = 0
    if level_value is None:
        if state.effect_type == "dynamic" and state.brightness is not None:
            level_value = min(state.brightness, 100)
        else:
            level_value = 100

    return (
        _byte_value(effect_value, "effect"),
        _byte_value(speed_value, "speed"),
        _byte_value(level_value, "level"),
    )


def _require_zengge_mesh_command(
    runtime: UniLEDRuntime,
    node_id: int,
) -> tuple[ZenggeMeshConnection, int]:
    """Return the mesh connection after validating command preconditions."""
    if runtime.model.family is not ProtocolFamily.ZENGGE_MESH:
        raise RuntimeSetupError(f"{runtime.model.name} is not a Zengge mesh model")
    if runtime.mesh_connection is None:
        raise RuntimeSetupError("Zengge mesh transport is not attached")
    if not runtime.mesh_session_paired:
        raise RuntimeSetupError("Zengge mesh session is not paired")

    node_id = int(node_id)
    if node_id not in zengge_mesh_node_ids(runtime):
        raise RuntimeSetupError(f"Zengge mesh node 0x{node_id:02x} is not known")
    return runtime.mesh_connection, node_id


def _is_zengge_command_node(runtime: UniLEDRuntime, node_id: int) -> bool:
    if node_id == ZENGGE_MESH_ADDRESS_NONE:
        return False
    return _zengge_mesh_node_kind(runtime, node_id) not in {
        ZENGGE_NODE_KIND_BRIDGE,
        ZENGGE_NODE_KIND_PANEL,
    }


def _zengge_mesh_known_node_ids(runtime: UniLEDRuntime) -> tuple[int, ...]:
    """Return all known mesh node IDs from config metadata and parser state."""
    node_ids: set[int] = set()
    if runtime.mesh_session is not None:
        node_ids.update(int(node_id) for node_id in runtime.mesh_session.contexts)

    for channel_id, state in runtime.state.channels.items():
        node_id = _optional_int(state.extra.get("node_id"))
        node_ids.add(int(channel_id) if node_id is None else node_id)

    return tuple(sorted(node_ids))


def _mesh_role_diagnostic(runtime: UniLEDRuntime) -> str | None:
    """Return a compact diagnostic summary for Zengge mesh node roles."""
    if runtime.model.family is not ProtocolFamily.ZENGGE_MESH:
        return None

    node_ids = _zengge_mesh_known_node_ids(runtime)
    command_nodes = zengge_mesh_node_ids(runtime)
    strip_nodes = _zengge_mesh_kind_count(runtime, ZENGGE_NODE_KIND_STRIP)
    bulb_nodes = _zengge_mesh_kind_count(runtime, ZENGGE_NODE_KIND_BULB)
    panel_nodes = zengge_mesh_panel_node_ids(runtime)
    bridge_seen = any(_is_zengge_bridge_node(runtime, node_id) for node_id in node_ids)
    transport = (
        "transport_ready" if runtime.mesh_transport_ready else "transport_pending"
    )
    paired = "paired" if runtime.mesh_session_paired else "unpaired"
    return (
        f"zengge_mesh; {transport}; {paired}; nodes={len(node_ids)}; "
        f"command_nodes={len(command_nodes)}; strip_nodes={strip_nodes}; "
        f"bulb_nodes={bulb_nodes}; panel_nodes={len(panel_nodes)}; "
        f"bridge_seen={bridge_seen}"
    )


def _zengge_mesh_known_node_count(runtime: UniLEDRuntime) -> int | None:
    """Return the count of known Zengge mesh nodes."""
    if runtime.model.family is not ProtocolFamily.ZENGGE_MESH:
        return None
    return len(_zengge_mesh_known_node_ids(runtime))


def _zengge_mesh_kind_count(runtime: UniLEDRuntime, kind: str) -> int | None:
    """Return how many known Zengge nodes currently have one role label."""
    if runtime.model.family is not ProtocolFamily.ZENGGE_MESH:
        return None
    return sum(
        1
        for node_id in _zengge_mesh_known_node_ids(runtime)
        if _zengge_mesh_node_kind(runtime, node_id) == kind
    )


def _zengge_mesh_bridge_seen_diagnostic(runtime: UniLEDRuntime) -> bool | None:
    """Return whether a Zengge bridge node is visible in known node state."""
    if runtime.model.family is not ProtocolFamily.ZENGGE_MESH:
        return None
    return any(
        _is_zengge_bridge_node(runtime, node_id)
        for node_id in _zengge_mesh_known_node_ids(runtime)
    )


def _is_zengge_panel_node(runtime: UniLEDRuntime, node_id: int) -> bool:
    return _zengge_mesh_node_kind(runtime, node_id) == ZENGGE_NODE_KIND_PANEL


def _is_zengge_bridge_node(runtime: UniLEDRuntime, node_id: int) -> bool:
    return _zengge_mesh_node_kind(runtime, node_id) == ZENGGE_NODE_KIND_BRIDGE


def _zengge_mesh_node_kind(runtime: UniLEDRuntime, node_id: int) -> str:
    """Return the normalized old-UniLED role label for one mesh node."""
    if node_id == ZENGGE_MESH_ADDRESS_BRIDGE:
        return ZENGGE_NODE_KIND_BRIDGE

    state = runtime.state.channels.get(node_id)
    if state is not None:
        raw_kind = state.extra.get("node_kind")
        if raw_kind in {
            ZENGGE_NODE_KIND_STRIP,
            ZENGGE_NODE_KIND_BULB,
            ZENGGE_NODE_KIND_LIGHT,
            ZENGGE_NODE_KIND_PANEL,
            ZENGGE_NODE_KIND_BRIDGE,
        }:
            return str(raw_kind)

        state_node_type = _optional_int(state.extra.get("node_type"))
        if state_node_type is not None:
            return zengge_node_kind(state_node_type)

    if runtime.mesh_session is not None:
        context = runtime.mesh_session.contexts.get(node_id)
        if context is not None:
            return zengge_node_kind(context.node_type)

    return ZENGGE_NODE_KIND_LIGHT


def _zengge_mesh_panel_name(runtime: UniLEDRuntime, node_id: int) -> str:
    state = runtime.state.channels.get(node_id)
    name = None if state is None else state.extra.get("node_name")
    if not isinstance(name, str) or not name:
        if runtime.mesh_session is not None:
            context = runtime.mesh_session.contexts.get(node_id)
            name = None if context is None else context.name
    if isinstance(name, str) and name:
        base = name if "panel" in name.lower() else f"{name} panel"
    else:
        base = f"Panel {node_id}"
    return f"{base} status"


def _zengge_mesh_panel_status_diagnostic(
    runtime: UniLEDRuntime,
    key: str,
) -> str | None:
    node_id = _zengge_mesh_panel_status_node_id(key)
    if node_id is None or not _is_zengge_panel_node(runtime, node_id):
        return None

    state = runtime.state.channels.get(node_id)
    if state is None:
        return None
    status = state.extra.get("status")
    if isinstance(status, str) and status:
        return status
    connected = _optional_int(state.extra.get("connected"))
    if connected is None:
        return None
    return ZENGGE_STATUS_ONLINE if connected else ZENGGE_STATUS_OFFLINE


def _zengge_mesh_panel_status_node_id(key: str) -> int | None:
    if not (
        key.startswith(_ZENGGE_PANEL_STATUS_PREFIX)
        and key.endswith(_ZENGGE_PANEL_STATUS_SUFFIX)
    ):
        return None
    node_hex = key[
        len(_ZENGGE_PANEL_STATUS_PREFIX) : -len(_ZENGGE_PANEL_STATUS_SUFFIX)
    ]
    if not node_hex:
        return None
    try:
        return int(node_hex, 16)
    except ValueError:
        return None


def _apply_zengge_mesh_light_state(
    runtime: UniLEDRuntime,
    node_id: int,
    command: str,
    *,
    power: bool | None = None,
    brightness: int | None = None,
    rgb: tuple[int, int, int] | None = None,
    color_temp_kelvin: int | None = None,
    white: int | None = None,
    effect: int | None = None,
    effect_speed: int | None = None,
    effect_level: int | None = None,
) -> ChannelState:
    state = channel_state(runtime, node_id)
    state.extra.setdefault("node_id", node_id)
    if runtime.mesh_session is not None:
        context = runtime.mesh_session.contexts.get(node_id)
        if context is not None:
            state.extra.setdefault("node_kind", zengge_node_kind(context.node_type))
            state.extra.setdefault("node_type", context.node_type)
            state.extra.setdefault("node_wiring", context.node_wiring)
            state.extra.setdefault("node_address", context.address)
            state.extra.setdefault("node_name", context.name)
            state.extra.setdefault("node_area", context.area)

    if power is not None:
        state.power = power
    if brightness is not None:
        state.brightness = brightness
        if brightness > 0:
            state.power = True
    if rgb is not None:
        state.rgb = rgb
        state.power = True
    if color_temp_kelvin is not None:
        state.color_temp_kelvin = color_temp_kelvin
        state.power = True
    if white is not None:
        state.warm_white = white
        state.extra["white_level"] = white
        state.power = True
    if effect is not None:
        state.effect_number = effect
        state.effect = _zengge_effect_name(runtime, effect)
        state.effect_type = "dynamic"
        state.power = True
    if effect_speed is not None:
        state.effect_speed = effect_speed
    if effect_level is not None:
        state.extra["effect_level"] = effect_level

    runtime.state.available = runtime.mesh_session_paired
    runtime.state.diagnostics.update(
        {
            "last_mesh_command": command,
            "last_mesh_command_node_id": node_id,
            "mesh_session_paired": runtime.mesh_session_paired,
        }
    )
    return state


def _zengge_effect_name(runtime: UniLEDRuntime, effect: int) -> str | None:
    profile = mesh_profile_for_model(runtime.model)
    if profile is None or effect < 1 or effect > len(profile.effect_names):
        return None
    return profile.effect_names[effect - 1]


def _register_zengge_entry_nodes(
    session: ZenggeMeshSession,
    entry_data: Mapping[str, Any],
    *,
    address: str,
) -> None:
    registered = False
    nodes = entry_data.get(CONF_MESH_NODES)
    if isinstance(nodes, (list, tuple)):
        for node in nodes:
            if not isinstance(node, Mapping):
                continue
            context = _zengge_context_from_mapping(node, address=address)
            if context is None:
                continue
            session.register_node(context)
            registered = True

    if registered or CONF_MESH_NODE_ID not in entry_data:
        return

    context = _zengge_context_from_mapping(entry_data, address=address)
    if context is not None:
        session.register_node(context)


def _zengge_context_from_mapping(
    data: Mapping[str, Any],
    *,
    address: str,
) -> ZenggeNodeContext | None:
    node_id = _optional_int(data.get(CONF_MESH_NODE_ID))
    if node_id is None:
        return None
    return ZenggeNodeContext(
        node_id=node_id,
        node_type=_optional_int(data.get(CONF_MESH_NODE_TYPE)) or 0,
        node_wiring=_optional_int(data.get(CONF_MESH_NODE_WIRING)) or 0,
        address=address,
        name=_optional_text(data.get("name")),
        area=_optional_text(data.get("area")),
    )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text, 0)
        except ValueError:
            return None
    return None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().casefold()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _required_int(value: Any, field: str) -> int:
    parsed = _optional_int(value)
    if parsed is None:
        raise ValueError(f"{field} must be an integer")
    return parsed


def _byte_value(value: int, field: str) -> int:
    parsed = int(value)
    if parsed < 0 or parsed > 0xFF:
        raise ValueError(f"{field} must be between 0 and 255")
    return parsed


def _byte_tuple(value: Any, length: int, *, field: str) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be a {length}-item list or tuple")
    if len(value) != length:
        raise ValueError(f"{field} must contain {length} values")
    values = tuple(_required_int(item, field) for item in value)
    if any(item < 0 or item > 0xFF for item in values):
        raise ValueError(f"{field} values must be between 0 and 255")
    return values


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _zengge_mesh_light_name(runtime: UniLEDRuntime, node_id: int) -> str:
    state = runtime.state.channels.get(node_id)
    name = None if state is None else state.extra.get("node_name")
    if isinstance(name, str) and name:
        return name

    if runtime.mesh_session is not None:
        context = runtime.mesh_session.contexts.get(node_id)
        if context is not None and context.name:
            return context.name

    kind = _zengge_mesh_node_kind(runtime, node_id)
    if kind == ZENGGE_NODE_KIND_STRIP:
        return f"Strip {node_id}"
    if kind == ZENGGE_NODE_KIND_BULB:
        return f"Bulb {node_id}"

    return f"Node {node_id}"


def implemented_sensor_keys(runtime: UniLEDRuntime) -> tuple[str, ...]:
    """Return implemented diagnostic sensor feature keys."""
    return tuple(feature.key for feature in diagnostic_sensor_features(runtime))


def diagnostic_sensor_features(runtime: UniLEDRuntime) -> tuple[FeatureSpec, ...]:
    """Return implemented diagnostic sensors for static and runtime features."""
    return tuple(
        feature
        for feature in runtime.entity_plan.features
        if feature.platform is PlatformKind.SENSOR and feature.implemented
    ) + zengge_mesh_panel_sensor_features(runtime)


def command_light_features(runtime: UniLEDRuntime) -> tuple[FeatureSpec, ...]:
    """Return light features that can send commands right now."""
    if runtime.model.family is ProtocolFamily.ZENGGE_MESH:
        return zengge_mesh_light_features(runtime)
    if not runtime.session_ready:
        return ()
    return tuple(
        _runtime_command_feature(
            feature,
            enabled_by_default=feature.key == "main_light",
        )
        for feature in runtime.entity_plan.features_for_platform(PlatformKind.LIGHT)
        if feature.key == "main_light"
        or feature.implementation_hint == "legacy_uniled_output"
    )


def command_scene_features(runtime: UniLEDRuntime) -> tuple[FeatureSpec, ...]:
    """Return scene features that can send commands right now."""
    if not runtime.session_ready:
        return ()
    return tuple(
        _runtime_command_feature(feature)
        for feature in runtime.entity_plan.features_for_platform(PlatformKind.SCENE)
        if feature.implementation_hint == "legacy_uniled"
    )


def command_button_features(runtime: UniLEDRuntime) -> tuple[FeatureSpec, ...]:
    """Return button features that can trigger runtime actions right now."""
    if not runtime.session_ready and not runtime.mesh_transport_ready:
        return ()
    return tuple(
        feature
        for feature in runtime.entity_plan.features_for_platform(PlatformKind.BUTTON)
        if feature.key in _COMMAND_BUTTON_KEYS and feature.implemented
    )


def command_number_features(runtime: UniLEDRuntime) -> tuple[FeatureSpec, ...]:
    """Return number features that can send commands right now."""
    if runtime.model.family is ProtocolFamily.ZENGGE_MESH:
        return zengge_mesh_number_features(runtime)
    if not runtime.session_ready:
        return ()
    return tuple(
        _runtime_command_feature(feature)
        for feature in runtime.entity_plan.features_for_platform(PlatformKind.NUMBER)
        if feature.key in _COMMAND_NUMBER_KEYS
    )


def command_control_available(
    runtime: UniLEDRuntime,
    key: str,
    *,
    channel: int = 0,
) -> bool:
    """Return whether a command control is usable in the current parsed state."""
    if runtime.model.family is ProtocolFamily.ZENGGE_MESH:
        if key in {"effect_speed", "effect_level"}:
            return zengge_mesh_command_ready(runtime, channel)
        return False
    if not runtime.session_ready:
        return False
    if key in _COMMAND_SELECT_KEYS and not select_options(
        runtime,
        key,
        channel=channel,
    ):
        return False
    if runtime.model.family is ProtocolFamily.LEGACY_LED_CHORD:
        if key == "segment_count":
            return control_value(runtime, "segment_pixels", channel=channel) is not None
        if key == "segment_pixels":
            return control_value(runtime, "segment_count", channel=channel) is not None
    if (
        banlanx6xx_style_family(runtime.model.family)
        and key in _BANLANX6XX_STATE_DEPENDENT_COMMAND_KEYS
    ):
        return control_value(runtime, key, channel=channel) is not None
    return True


def command_select_features(runtime: UniLEDRuntime) -> tuple[FeatureSpec, ...]:
    """Return select features that can send commands right now."""
    if runtime.model.family is ProtocolFamily.ZENGGE_MESH:
        return zengge_mesh_select_features(runtime)
    if not runtime.session_ready:
        return ()
    return tuple(
        _runtime_command_feature(feature)
        for feature in runtime.entity_plan.features_for_platform(PlatformKind.SELECT)
        if feature.key in _COMMAND_SELECT_KEYS
        and _feature_has_select_options(runtime, feature)
    )


def _feature_has_select_options(
    runtime: UniLEDRuntime,
    feature: FeatureSpec,
) -> bool:
    if select_options(runtime, feature.key, channel=feature.channel):
        return True
    return (
        banlanx6xx_style_family(runtime.model.family)
        and (
            (
                feature.key == "chip_order"
                and banlanx6xx_model_has_dynamic_light_type(runtime.model.name)
            )
            or (
                feature.key == "effect"
                and not banlanx6xx_model_has_static_effects(runtime.model.name)
            )
            or (
                feature.key == "light_mode"
                and banlanx6xx_model_has_dynamic_light_type(runtime.model.name)
            )
        )
    )


def effect_channel_allows_commands(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> bool:
    """Return whether an effect command/list is valid for a channel."""
    if runtime.model.family in _OUTPUT_SCOPED_EFFECT_FAMILIES:
        return int(channel) != 0
    return True


def select_channel_allows_options(
    runtime: UniLEDRuntime,
    key: str,
    *,
    channel: int = 0,
) -> bool:
    """Return whether a select option map is valid for a channel."""
    if (
        runtime.model.family in _OUTPUT_SCOPED_EFFECT_FAMILIES
        and key in _OUTPUT_SCOPED_SELECT_KEYS
    ):
        return int(channel) != 0
    return True


def output_scoped_command_allows(
    runtime: UniLEDRuntime,
    key: str,
    *,
    channel: int = 0,
) -> bool:
    """Return whether an output-scoped command may target this channel."""
    if runtime.model.family not in _OUTPUT_SCOPED_EFFECT_FAMILIES:
        return True
    if int(channel) != 0:
        return True
    if key in _OUTPUT_SCOPED_NUMBER_KEYS | _OUTPUT_SCOPED_SWITCH_KEYS:
        return False
    return not (
        runtime.model.family is ProtocolFamily.BANLANX_601
        and key == "audio_sensitivity"
    )


def command_switch_features(runtime: UniLEDRuntime) -> tuple[FeatureSpec, ...]:
    """Return switch features that can send commands right now."""
    if not runtime.session_ready:
        return ()
    return tuple(
        _runtime_command_feature(feature)
        for feature in runtime.entity_plan.features_for_platform(PlatformKind.SWITCH)
        if feature.key in _COMMAND_SWITCH_KEYS
    )


def _runtime_command_feature(
    feature: FeatureSpec,
    *,
    enabled_by_default: bool | None = None,
) -> FeatureSpec:
    """Return a runtime-visible command feature while preserving planner defaults."""
    return replace(
        feature,
        implemented=True,
        enabled_by_default=(
            feature.enabled_by_default
            if enabled_by_default is None
            else enabled_by_default
        ),
    )


async def async_apply_legacy_set_state_service(
    runtime: UniLEDRuntime,
    data: Mapping[str, Any],
    *,
    channel: int = 0,
) -> bool:
    """Apply the old UniLED ``set_state`` light entity service safely."""
    if runtime.model.family is ProtocolFamily.ZENGGE_MESH:
        return await _async_apply_legacy_set_state_mesh(runtime, data, channel=channel)

    session = runtime.session
    if session is None:
        return False

    sent = False
    power = _optional_bool(data.get(_SERVICE_POWER))
    if power is False:
        await session.set_power(False, channel=channel)
        apply_light_command_state(runtime, channel=channel, power=False)
        return True
    if power is True:
        await session.set_power(True, channel=channel)
        apply_light_command_state(runtime, channel=channel, power=True)
        sent = True

    if _SERVICE_EFFECT in data and effect_channel_allows_commands(
        runtime,
        channel=channel,
    ):
        effect = str(data[_SERVICE_EFFECT])
        effect_value = effect_command_value(runtime, effect, channel=channel)
        if isinstance(effect_value, tuple):
            await session.set_light_mode(effect_value[0], effect_value[1])
        else:
            await session.set_effect(effect_value, channel=channel)
        apply_select_command_state(runtime, "effect", effect, channel=channel)
        sent = True

    static_color = light_uses_static_color_command(runtime, channel=channel)
    brightness = _optional_int(data.get(_SERVICE_BRIGHTNESS))
    command_level = color_command_level(runtime, brightness, channel=channel)

    if _SERVICE_RGBWW_COLOR in data:
        red, green, blue, cold, warm = _byte_tuple(
            data[_SERVICE_RGBWW_COLOR],
            5,
            field=_SERVICE_RGBWW_COLOR,
        )
        await session.set_rgbww_color(
            red,
            green,
            blue,
            cold,
            warm,
            channel=channel,
            level=command_level,
            static=static_color,
        )
        apply_light_command_state(
            runtime,
            channel=channel,
            rgbww=(red, green, blue, cold, warm),
            brightness=brightness,
            cct=(cold, warm),
        )
        sent = True
    elif _SERVICE_RGBW_COLOR in data:
        red, green, blue, white = _byte_tuple(
            data[_SERVICE_RGBW_COLOR],
            4,
            field=_SERVICE_RGBW_COLOR,
        )
        await async_ensure_banlanx_v23_rgb_effect(runtime, channel=channel)
        await session.set_rgbw_color(
            red,
            green,
            blue,
            white,
            channel=channel,
            level=command_level,
            static=static_color,
        )
        apply_light_command_state(
            runtime,
            channel=channel,
            rgbw=(red, green, blue, white),
            brightness=brightness,
            white=white,
        )
        sent = True
    elif _SERVICE_COLOR_TEMP_KELVIN in data:
        level = _optional_int(data.get(_SERVICE_WHITE))
        if level is None:
            level = brightness
        if level is None:
            existing = channel_state(runtime, channel).brightness
            level = 0xFF if existing is None else existing
        kelvin = _required_int(
            data[_SERVICE_COLOR_TEMP_KELVIN],
            _SERVICE_COLOR_TEMP_KELVIN,
        )
        cold, warm = cct_levels_for_kelvin(kelvin, level=level)
        await session.set_cct_color(
            cold,
            warm,
            channel=channel,
            static=static_color,
        )
        apply_light_command_state(
            runtime,
            channel=channel,
            brightness=level,
            color_temp_kelvin=kelvin,
            cct=(cold, warm),
        )
        sent = True
    elif _SERVICE_WHITE in data:
        white = _required_int(data[_SERVICE_WHITE], _SERVICE_WHITE)
        switched_sp6xx = await async_ensure_sp6xx_white_mode(
            runtime,
            channel=channel,
        )
        switched_v23 = await async_ensure_banlanx_v23_white_effect(
            runtime,
            channel=channel,
        )
        if suppress_sp6xx_sound_brightness_command(runtime, channel=channel):
            apply_sp6xx_sound_brightness_ignored(runtime, channel=channel)
            sent = sent or switched_sp6xx or switched_v23
        else:
            if banlanx_v23_brightness_uses_white_level(runtime, channel=channel):
                await session.set_white_brightness(white, channel=channel)
            else:
                await session.set_white_level(white, channel=channel)
            apply_light_command_state(
                runtime,
                channel=channel,
                brightness=white,
                white=white,
            )
            sent = True
    elif _SERVICE_RGB_COLOR in data:
        red, green, blue = _byte_tuple(
            data[_SERVICE_RGB_COLOR],
            3,
            field=_SERVICE_RGB_COLOR,
        )
        await async_ensure_banlanx_v23_rgb_effect(runtime, channel=channel)
        if static_color:
            await session.set_rgb_color(
                red,
                green,
                blue,
                channel=channel,
                level=command_level,
            )
        else:
            await session.set_dynamic_rgb_color(red, green, blue, channel=channel)
        apply_light_command_state(
            runtime,
            channel=channel,
            rgb=(red, green, blue),
            brightness=brightness if static_color else None,
        )
        sent = True
    elif brightness is not None:
        if suppress_sp6xx_sound_brightness_command(runtime, channel=channel):
            apply_sp6xx_sound_brightness_ignored(runtime, channel=channel)
        elif banlanx_v23_brightness_uses_white_level(runtime, channel=channel):
            await session.set_white_brightness(brightness, channel=channel)
            apply_light_command_state(
                runtime,
                channel=channel,
                brightness=brightness,
                white=brightness,
            )
            sent = True
        elif (
            sp6xx_brightness_uses_white_level(runtime, channel=channel)
            or (
                "white" in light_supported_color_modes(runtime, channel=channel)
                and light_color_mode(runtime, channel=channel) == "white"
            )
        ):
            await session.set_white_level(brightness, channel=channel)
            apply_light_command_state(
                runtime,
                channel=channel,
                brightness=brightness,
                white=brightness,
            )
            sent = True
        else:
            await session.set_brightness(brightness, channel=channel)
            apply_light_command_state(runtime, channel=channel, brightness=brightness)
            sent = True

    if _SERVICE_RGB2_COLOR in data:
        red, green, blue = _byte_tuple(
            data[_SERVICE_RGB2_COLOR],
            3,
            field=_SERVICE_RGB2_COLOR,
        )
        await session.set_rgb2_color(red, green, blue, channel=channel)
        apply_rgb2_command_state(runtime, red, green, blue, channel=channel)
        sent = True

    if _SERVICE_EFFECT_SPEED in data:
        value = _required_int(data[_SERVICE_EFFECT_SPEED], _SERVICE_EFFECT_SPEED)
        if output_scoped_command_allows(runtime, "effect_speed", channel=channel):
            await session.set_effect_speed(value, channel=channel)
            apply_number_command_state(runtime, "effect_speed", value, channel=channel)
            sent = True
    if _SERVICE_EFFECT_LENGTH in data:
        value = _required_int(data[_SERVICE_EFFECT_LENGTH], _SERVICE_EFFECT_LENGTH)
        if output_scoped_command_allows(runtime, "effect_length", channel=channel):
            await session.set_effect_length(value, channel=channel)
            apply_number_command_state(runtime, "effect_length", value, channel=channel)
            sent = True
    if _SERVICE_SENSITIVITY in data:
        value = _required_int(data[_SERVICE_SENSITIVITY], _SERVICE_SENSITIVITY)
        if output_scoped_command_allows(runtime, "audio_sensitivity", channel=channel):
            await session.set_sensitivity(value, channel=channel)
            apply_number_command_state(
                runtime,
                "audio_sensitivity",
                value,
                channel=channel,
            )
            sent = True
    if _SERVICE_EFFECT_DIRECTION in data:
        value = _optional_bool(data[_SERVICE_EFFECT_DIRECTION])
        if value is None:
            raise ValueError(f"{_SERVICE_EFFECT_DIRECTION} must be a boolean")
        if output_scoped_command_allows(runtime, "effect_direction", channel=channel):
            await session.set_effect_direction(value, channel=channel)
            apply_switch_command_state(
                runtime,
                "effect_direction",
                value,
                channel=channel,
            )
            sent = True
    if _SERVICE_EFFECT_LOOP in data:
        value = _optional_bool(data[_SERVICE_EFFECT_LOOP])
        if value is None:
            raise ValueError(f"{_SERVICE_EFFECT_LOOP} must be a boolean")
        await session.set_effect_loop(value)
        apply_switch_command_state(runtime, "effect_loop", value, channel=channel)
        sent = True
    if _SERVICE_EFFECT_PLAY in data:
        value = _optional_bool(data[_SERVICE_EFFECT_PLAY])
        if value is None:
            raise ValueError(f"{_SERVICE_EFFECT_PLAY} must be a boolean")
        await session.set_effect_play(value, channel=channel)
        apply_switch_command_state(runtime, "effect_play", value, channel=channel)
        sent = True

    return sent


async def _async_apply_legacy_set_state_mesh(
    runtime: UniLEDRuntime,
    data: Mapping[str, Any],
    *,
    channel: int,
) -> bool:
    """Apply the compatibility service to a paired Zengge mesh node."""
    if not zengge_mesh_command_ready(runtime, channel):
        return False

    sent = False
    gradual_seconds = _optional_float(data.get(_SERVICE_TRANSITION)) or 0.0
    if gradual_seconds < 0.0:
        gradual_seconds = 0.0
    power = _optional_bool(data.get(_SERVICE_POWER))
    if power is False:
        await set_zengge_mesh_power(
            runtime,
            channel,
            False,
            gradual_seconds=gradual_seconds,
        )
        return True
    if power is True:
        await set_zengge_mesh_power(
            runtime,
            channel,
            True,
            gradual_seconds=gradual_seconds,
        )
        sent = True

    if _SERVICE_EFFECT in data:
        effect_value = effect_command_value(
            runtime,
            str(data[_SERVICE_EFFECT]),
            channel=channel,
        )
        if isinstance(effect_value, tuple):
            effect_value = effect_value[-1]
        await set_zengge_mesh_effect(runtime, channel, effect_value)
        sent = True

    brightness = _optional_int(data.get(_SERVICE_BRIGHTNESS))
    if _SERVICE_COLOR_TEMP_KELVIN in data:
        kelvin = _required_int(
            data[_SERVICE_COLOR_TEMP_KELVIN],
            _SERVICE_COLOR_TEMP_KELVIN,
        )
        await set_zengge_mesh_color_temp(
            runtime,
            channel,
            kelvin,
            level=0xFF if brightness is None else brightness,
            gradual_seconds=gradual_seconds,
        )
        sent = True
    elif _SERVICE_WHITE in data:
        await set_zengge_mesh_white(
            runtime,
            channel,
            _required_int(data[_SERVICE_WHITE], _SERVICE_WHITE),
            gradual_seconds=gradual_seconds,
        )
        sent = True
    elif _SERVICE_RGB_COLOR in data:
        red, green, blue = _byte_tuple(
            data[_SERVICE_RGB_COLOR],
            3,
            field=_SERVICE_RGB_COLOR,
        )
        await set_zengge_mesh_rgb(
            runtime,
            channel,
            red,
            green,
            blue,
            gradual_seconds=gradual_seconds,
        )
        if brightness is not None:
            await set_zengge_mesh_brightness(
                runtime,
                channel,
                brightness,
                gradual_seconds=gradual_seconds,
            )
        sent = True
    elif brightness is not None:
        await set_zengge_mesh_brightness(
            runtime,
            channel,
            brightness,
            gradual_seconds=gradual_seconds,
        )
        sent = True

    return sent


def channel_state(runtime: UniLEDRuntime, channel: int = 0) -> ChannelState:
    """Return or create normalized channel state for command entities."""
    if channel not in runtime.state.channels:
        runtime.state.channels[channel] = ChannelState(channel_id=channel)
    return runtime.state.channels[channel]


def apply_light_command_state(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
    power: bool | None = None,
    brightness: int | None = None,
    rgb: tuple[int, int, int] | None = None,
    rgbw: tuple[int, int, int, int] | None = None,
    rgbww: tuple[int, int, int, int, int] | None = None,
    white: int | None = None,
    color_temp_kelvin: int | None = None,
    cct: tuple[int, int] | None = None,
) -> ChannelState:
    """Apply an optimistic light command state after a successful send."""
    state = channel_state(runtime, channel)
    _apply_light_state_fields(
        runtime,
        state,
        power=power,
        brightness=brightness,
        rgb=rgb,
        rgbw=rgbw,
        rgbww=rgbww,
        white=white,
        color_temp_kelvin=color_temp_kelvin,
        cct=cct,
    )
    if int(channel) == 0:
        for output_channel in _legacy_aggregate_output_channels(runtime):
            _apply_light_state_fields(
                runtime,
                channel_state(runtime, output_channel),
                power=power,
                brightness=brightness,
                rgb=rgb,
                rgbw=rgbw,
                rgbww=rgbww,
                white=white,
                color_temp_kelvin=color_temp_kelvin,
                cct=cct,
            )
    runtime.state.available = runtime.session_ready
    return state


def apply_rgb2_command_state(
    runtime: UniLEDRuntime,
    red: int,
    green: int,
    blue: int,
    *,
    channel: int = 0,
) -> ChannelState:
    """Apply an optimistic secondary/matrix RGB command state."""
    state = channel_state(runtime, channel)
    state.extra["rgb2"] = (red, green, blue)
    runtime.state.available = runtime.session_ready
    return state


def _apply_light_state_fields(
    runtime: UniLEDRuntime,
    state: ChannelState,
    *,
    power: bool | None = None,
    brightness: int | None = None,
    rgb: tuple[int, int, int] | None = None,
    rgbw: tuple[int, int, int, int] | None = None,
    rgbww: tuple[int, int, int, int, int] | None = None,
    white: int | None = None,
    color_temp_kelvin: int | None = None,
    cct: tuple[int, int] | None = None,
) -> None:
    """Apply light command fields to one channel state."""
    if power is not None:
        state.power = power
    if brightness is not None:
        state.brightness = brightness
        if brightness > 0:
            state.power = True
    if rgb is not None:
        state.rgb = rgb
        _clear_v23_color_mode_override(runtime, state)
        state.power = True
    if rgbw is not None:
        state.rgb = rgbw[:3]
        state.rgbw = rgbw
        state.rgbww = None
        _clear_v23_color_mode_override(runtime, state)
        state.power = True
    if rgbww is not None:
        state.rgb = rgbww[:3]
        state.rgbw = None
        state.rgbww = rgbww
        _clear_v23_color_mode_override(runtime, state)
        state.power = True
    if white is not None:
        state.extra["white_level"] = white
        _clear_v23_color_mode_override(runtime, state)
        if runtime.model.family in _BANLANX_V23_WHITE_EFFECTS:
            state.effect_number = _BANLANX_V23_WHITE_EFFECTS[runtime.model.family]
            state.effect = "Solid White"
            state.effect_type = "Static"
        state.power = True
    if color_temp_kelvin is not None:
        state.color_temp_kelvin = color_temp_kelvin
        state.power = True
    if cct is not None:
        state.cold_white, state.warm_white = cct
        state.power = True


def _legacy_aggregate_output_channels(runtime: UniLEDRuntime) -> tuple[int, ...]:
    """Return physical output channels controlled by the aggregate light."""
    if runtime.model.family is ProtocolFamily.BANLANX_601:
        return (1, 2)
    if runtime.model.family is ProtocolFamily.BANLANX_60X:
        return tuple(range(1, 5 if runtime.model.name == "SP602E" else 9))
    return ()


def light_supported_color_modes(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> tuple[str, ...]:
    """Return HA-independent supported light color modes."""
    if runtime.model.family is ProtocolFamily.ZENGGE_MESH:
        return _zengge_mesh_supported_color_modes(runtime, channel)
    if runtime.model.family in _BANLANX_V23_WHITE_EFFECTS:
        if channel_state(runtime, channel).extra.get("color_mode") == "onoff":
            return ("onoff",)
        if legacy_v23_model_has_white_channel(
            runtime.model.family,
            color_cap=runtime.model.color_cap,
            model_name=runtime.model.name,
        ):
            return ("rgb", "white")
        return ("rgb",)
    if not banlanx6xx_style_family(runtime.model.family):
        return ("rgb",)
    if (
        runtime.state.diagnostics.get("light_type") is None
        and banlanx6xx_model_has_dynamic_light_type(runtime.model.name)
    ):
        return ("rgb",)
    capabilities = set(banlanx6xx_light_type_capabilities(_current_light_type(runtime)))
    if not capabilities:
        return ("rgb",)
    coexistence = _coexistence_value(runtime)
    has_hue = "hue" in capabilities
    has_cct = "cct" in capabilities
    has_white = "white" in capabilities
    if has_hue and has_cct and coexistence:
        return ("rgbww",)
    if has_hue and has_white and not has_cct and coexistence:
        return ("rgbw",)
    modes: list[str] = []
    if has_hue:
        modes.append("rgb")
    if has_cct:
        modes.append("color_temp")
    elif has_white and has_hue:
        modes.append("white")
    elif has_white:
        modes.append("brightness")
    return _normalize_supported_color_modes(tuple(modes) or ("rgb",))


def _normalize_supported_color_modes(modes: tuple[str, ...]) -> tuple[str, ...]:
    """Return HA-valid supported color modes while preserving useful order."""
    supported = tuple(
        dict.fromkeys(
            mode
            for mode in modes
            if mode
            in {
                "brightness",
                "color_temp",
                "onoff",
                "rgb",
                "rgbw",
                "rgbww",
                "white",
            }
        )
    )
    if len(supported) > 1:
        supported = tuple(
            mode for mode in supported if mode not in {"brightness", "onoff"}
        )
    return supported or ("onoff",)


def light_color_mode(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> str:
    """Return the current HA-independent color mode."""
    state = channel_state(runtime, channel)
    supported = light_supported_color_modes(runtime, channel=channel)
    mode = state.extra.get("color_mode")
    if isinstance(mode, str) and mode in supported:
        return mode
    if runtime.model.family is ProtocolFamily.ZENGGE_MESH:
        if state.light_mode_number == 1 and "color_temp" in supported:
            return "color_temp"
        if state.warm_white is not None and "white" in supported:
            return "white"
        return supported[0]
    if (
        runtime.model.family in _BANLANX_V23_WHITE_EFFECTS
        and "white" in supported
        and state.effect_number == _BANLANX_V23_WHITE_EFFECTS[runtime.model.family]
    ):
        return "white"
    if "rgbww" in supported and state.rgbww is not None:
        return "rgbww"
    if "rgbw" in supported and state.rgbw is not None:
        return "rgbw"
    if state.light_mode_number in {0x02, 0x04, 0x06}:
        if "color_temp" in supported:
            return "color_temp"
        if "white" in supported:
            return "white"
        if "brightness" in supported:
            return "brightness"
    if "rgb" in supported:
        return "rgb"
    return supported[0]


def cct_levels_for_kelvin(
    kelvin: int,
    *,
    level: int = 0xFF,
) -> tuple[int, int]:
    """Convert Kelvin to SP6xx cold/warm byte levels."""
    kelvin = max(_MIN_CCT_KELVIN, min(_MAX_CCT_KELVIN, int(kelvin)))
    level = max(0, min(0xFF, int(level)))
    ratio = (kelvin - _MIN_CCT_KELVIN) / (_MAX_CCT_KELVIN - _MIN_CCT_KELVIN)
    cold = round(level * ratio)
    warm = level - cold
    return cold, warm


def cct_kelvin_from_levels(cold: int, warm: int) -> int | None:
    """Convert SP6xx cold/warm levels to an approximate Kelvin value."""
    total = int(cold) + int(warm)
    if total <= 0:
        return None
    ratio = int(cold) / total
    return round(_MIN_CCT_KELVIN + ratio * (_MAX_CCT_KELVIN - _MIN_CCT_KELVIN))


def light_uses_static_color_command(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> bool:
    """Return whether SP6xx RGB/CCT color commands should use static frames."""
    if not banlanx6xx_style_family(runtime.model.family):
        return True
    return channel_state(runtime, channel).light_mode_number in {0x01, 0x02}


def suppress_sp6xx_sound_brightness_command(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> bool:
    """Return whether SP6xx brightness writes should be skipped in sound mode."""
    state = channel_state(runtime, channel)
    return (
        banlanx6xx_style_family(runtime.model.family)
        and state.light_mode_number in _BANLANX6XX_SOUND_MODES
    )


def sp6xx_brightness_uses_white_level(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> bool:
    """Return whether SP6xx brightness should target the white-level selector."""
    if not banlanx6xx_style_family(runtime.model.family):
        return False
    state = channel_state(runtime, channel)
    return state.light_mode_number in _BANLANX6XX_WHITE_MODES


def color_command_level(
    runtime: UniLEDRuntime,
    explicit: int | None,
    *,
    channel: int = 0,
) -> int:
    """Return the level byte old UniLED would include in color frames."""
    if explicit is not None:
        return int(explicit)

    state = channel_state(runtime, channel)
    if runtime.model.family in _BANLANX_V23_SOLID_EFFECTS:
        color_level = state.extra.get("color_level")
        if isinstance(color_level, int):
            return color_level

    if state.brightness is not None:
        return int(state.brightness)
    return 0xFF


def _clear_v23_color_mode_override(
    runtime: UniLEDRuntime,
    state: ChannelState,
) -> None:
    """Clear parsed V2/V3 on/off-only mode after color-capable writes."""
    if runtime.model.family in _BANLANX_V23_WHITE_EFFECTS:
        state.extra.pop("color_mode", None)


def banlanx_v23_brightness_uses_white_level(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> bool:
    """Return whether BanlanX v2/v3 brightness targets the white-level frame."""
    white_effect = _BANLANX_V23_WHITE_EFFECTS.get(runtime.model.family)
    if white_effect is None:
        return False
    if "white" not in light_supported_color_modes(runtime, channel=channel):
        return False
    return channel_state(runtime, channel).effect_number == white_effect


async def async_ensure_banlanx_v23_rgb_effect(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> bool:
    """Switch BanlanX v2/v3 controllers to a colorable effect before RGB."""
    session = runtime.session
    solid = _BANLANX_V23_SOLID_EFFECTS.get(runtime.model.family)
    colorable = _BANLANX_V23_COLORABLE_EFFECTS.get(runtime.model.family)
    if session is None or solid is None or colorable is None:
        return False

    state = channel_state(runtime, channel)
    if state.effect_number in colorable:
        return False

    await session.set_effect(solid, channel=channel)
    state.effect_number = solid
    _clear_v23_color_mode_override(runtime, state)
    option_map = runtime_select_option_map(runtime, "effect", channel=channel)
    state.effect = (
        None if option_map is None else option_map.option_for_value(solid)
    ) or "Solid Color"
    state.effect_type = _effect_type_for_value(runtime.model.family, solid)
    runtime.state.available = runtime.session_ready
    return True


async def async_ensure_banlanx_v23_white_effect(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> bool:
    """Switch BanlanX v2/v3 controllers to solid white before white writes."""
    session = runtime.session
    white_effect = _BANLANX_V23_WHITE_EFFECTS.get(runtime.model.family)
    if session is None or white_effect is None:
        return False
    if "white" not in light_supported_color_modes(runtime, channel=channel):
        return False

    state = channel_state(runtime, channel)
    if state.effect_number == white_effect:
        return False

    await session.set_effect(white_effect, channel=channel)
    state.effect_number = white_effect
    _clear_v23_color_mode_override(runtime, state)
    option_map = runtime_select_option_map(runtime, "effect", channel=channel)
    state.effect = (
        None if option_map is None else option_map.option_for_value(white_effect)
    ) or "Solid White"
    state.effect_type = _effect_type_for_value(runtime.model.family, white_effect)
    runtime.state.available = runtime.session_ready
    return True


async def async_ensure_sp6xx_white_mode(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> bool:
    """Switch SP6xx-style controllers to a white mode when needed."""
    session = runtime.session
    command = _sp6xx_white_mode_command(runtime, channel=channel)
    if session is None or command is None:
        return False

    mode, effect, light_type = command
    await session.set_light_mode(mode, effect)
    state = channel_state(runtime, channel)
    state.light_mode_number = mode
    state.light_mode = banlanx6xx_light_mode_name(mode)
    state.effect_number = effect
    state.effect = _sp6xx_effect_label(
        light_type,
        mode,
        effect,
        model_name=runtime.model.name,
    )
    state.effect_type = _effect_type_for_value(
        runtime.model.family,
        effect,
        mode=mode,
    )
    runtime.state.available = runtime.session_ready
    return True


def _sp6xx_white_mode_command(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> tuple[int, int, int] | None:
    if not banlanx6xx_style_family(runtime.model.family):
        return None

    state = channel_state(runtime, channel)
    current_mode = state.light_mode_number
    if current_mode in _BANLANX6XX_WHITE_MODES:
        return None

    if current_mode in _BANLANX6XX_SOUND_MODES:
        target_mode = 0x06
    elif current_mode in _BANLANX6XX_DYNAMIC_MODES:
        target_mode = 0x04
    else:
        target_mode = 0x02

    light_type = _current_light_type(runtime)
    if light_type is None:
        return None

    try:
        mode, effect, _changed = banlanx6xx_default_mode_effect_for_light_type(
            light_type,
            mode=target_mode,
            effect=state.effect_number,
            model_name=runtime.model.name,
        )
    except (KeyError, ValueError):
        return None

    if mode not in _BANLANX6XX_WHITE_MODES:
        return None
    return mode, effect, light_type


def apply_sp6xx_sound_brightness_ignored(
    runtime: UniLEDRuntime,
    *,
    channel: int = 0,
) -> ChannelState:
    """Mirror old UniLED's full-brightness state when sound brightness is ignored."""
    state = channel_state(runtime, channel)
    state.brightness = 0xFF
    runtime.state.available = runtime.session_ready
    return state


def _channel_or_diagnostic_int(
    runtime: UniLEDRuntime,
    state: ChannelState,
    key: str,
) -> int | None:
    value = state.extra.get(key)
    if isinstance(value, int):
        return value
    value = runtime.state.diagnostics.get(key)
    if isinstance(value, int):
        return value
    return None


def control_value(
    runtime: UniLEDRuntime,
    key: str,
    *,
    channel: int = 0,
) -> int | bool | str | None:
    """Return a normalized command-control value."""
    state = channel_state(runtime, channel)
    if key == "effect_speed":
        return state.effect_speed
    if key == "effect_level":
        value = state.extra.get("effect_level")
        return value if isinstance(value, int) else None
    if key == "effect_length":
        return state.effect_length
    if key == "audio_sensitivity":
        return state.sensitivity
    if key == "onoff_pixels":
        return runtime.state.diagnostics.get("onoff_pixels")
    if key in {"segment_count", "segment_pixels"}:
        return _channel_or_diagnostic_int(runtime, state, key)
    if key == "effect":
        if state.effect is not None:
            return state.effect
        option_map = runtime_select_option_map(runtime, key, channel=channel)
        if option_map is None:
            return None
        effect_number = state.effect_number
        if (
            banlanx6xx_style_family(runtime.model.family)
            and state.light_mode_number is not None
            and effect_number is not None
        ):
            return option_map.option_for_value(
                mode_effect_value(state.light_mode_number, effect_number)
            )
        return option_map.option_for_value(effect_number)
    if key == "audio_input":
        option_map = select_option_map(
            runtime.model.family,
            key,
            color_cap=runtime.model.color_cap,
            model_name=runtime.model.name,
            spec_functions=runtime.model.spec_functions,
        )
        if option_map is None:
            return None
        return option_map.option_for_value(state.audio_input)
    if key == "light_mode":
        option_map = runtime_select_option_map(runtime, key, channel=channel)
        if option_map is None:
            return None
        return option_map.option_for_value(state.light_mode_number)
    if key == "light_type":
        return _light_type_option_value(runtime)
    if key == "chip_order":
        option_map = runtime_select_option_map(runtime, key, channel=channel)
        if option_map is None:
            return None
        return option_map.option_for_value(state.chip_order)
    if key == "chip_type":
        option_map = runtime_select_option_map(runtime, key, channel=channel)
        if option_map is None:
            return None
        return option_map.option_for_value(
            _channel_or_diagnostic_int(runtime, state, key)
        )
    if key in {"onoff_effect", "onoff_speed", "on_power"}:
        return _diagnostic_option_value(runtime, key)
    if key == "effect_direction":
        return state.effect_direction
    if key == "effect_loop":
        return state.effect_loop
    if key == "scene_loop":
        value = runtime.state.diagnostics.get("scene_loop")
        return value if isinstance(value, bool) else state.effect_loop
    if key == "effect_play":
        value = state.extra.get("play")
        return value if isinstance(value, bool) else None
    if key == "coexistence":
        return _coexistence_value(runtime)
    return None


def apply_number_command_state(
    runtime: UniLEDRuntime,
    key: str,
    value: int,
    *,
    channel: int = 0,
) -> ChannelState:
    """Apply an optimistic number command state after a successful send."""
    state = channel_state(runtime, channel)
    if key == "effect_speed":
        state.effect_speed = value
    elif key == "effect_level":
        state.extra["effect_level"] = value
    elif key == "effect_length":
        state.effect_length = value
    elif key == "audio_sensitivity":
        state.sensitivity = value
    elif key == "onoff_pixels":
        runtime.state.diagnostics["onoff_pixels"] = value
    elif key in {"segment_count", "segment_pixels"}:
        state.extra[key] = value
        runtime.state.diagnostics[key] = value
    runtime.state.available = (
        runtime.mesh_session_paired
        if runtime.model.family is ProtocolFamily.ZENGGE_MESH
        else runtime.session_ready
    )
    return state


def select_command_value(
    runtime: UniLEDRuntime,
    key: str,
    option: str,
    *,
    channel: int = 0,
) -> int:
    """Return the raw protocol value for a command select option."""
    option_map = runtime_select_option_map(runtime, key, channel=channel)
    if option_map is None:
        raise ValueError(f"{runtime.model.family} has no {key} options")
    return option_map.value_for_option(option)


def effect_command_value(
    runtime: UniLEDRuntime,
    option: str,
    *,
    channel: int = 0,
) -> int | tuple[int, int]:
    """Return the protocol payload value for an effect option."""
    raw_value = select_command_value(runtime, "effect", option, channel=channel)
    if banlanx6xx_style_family(runtime.model.family):
        return mode_effect_parts(raw_value)
    return raw_value


def onoff_command_values(
    runtime: UniLEDRuntime,
    *,
    effect: int | None = None,
    speed: int | None = None,
    pixels: int | None = None,
) -> tuple[int, int, int]:
    """Return a complete SP6xx on/off animation tuple for partial edits."""
    return (
        _diagnostic_int(runtime, "onoff_effect", effect, default=1),
        _diagnostic_int(runtime, "onoff_speed", speed, default=2),
        _diagnostic_int(runtime, "onoff_pixels", pixels, default=1),
    )


def light_type_command_values(
    runtime: UniLEDRuntime,
    light_type: int,
    *,
    channel: int = 0,
) -> LightTypeCommandValues:
    """Return a complete SP6xx light-type command tuple."""
    state = channel_state(runtime, channel)
    chip_order = _chip_order_for_light_type(runtime, light_type, channel=channel)
    mode, effect, changed = banlanx6xx_default_mode_effect_for_light_type(
        light_type,
        mode=state.light_mode_number,
        effect=state.effect_number,
        model_name=runtime.model.name,
    )
    return LightTypeCommandValues(
        light_type=light_type,
        chip_order=chip_order,
        mode=mode,
        effect=effect,
        power=state.power is True,
        refresh=changed,
    )


def light_mode_command_values(
    runtime: UniLEDRuntime,
    mode: int,
    *,
    channel: int = 0,
) -> tuple[int, int] | None:
    """Return the SP6xx mode/effect tuple for a light-mode select command."""
    if not banlanx6xx_style_family(runtime.model.family):
        return None
    if (
        banlanx6xx_model_has_dynamic_light_type(runtime.model.name)
        and runtime.state.diagnostics.get("light_type") is None
    ):
        return None
    light_type = _current_light_type(runtime)
    if light_type is None:
        return None
    state = channel_state(runtime, channel)
    mode, effect, _changed = banlanx6xx_default_mode_effect_for_light_type(
        light_type,
        mode=mode,
        effect=state.effect_number,
        model_name=runtime.model.name,
    )
    return mode, effect


def select_options(
    runtime: UniLEDRuntime,
    key: str,
    *,
    channel: int = 0,
) -> tuple[str, ...]:
    """Return current option labels for a runtime select feature."""
    option_map = runtime_select_option_map(runtime, key, channel=channel)
    return () if option_map is None else option_map.options


def runtime_select_option_map(
    runtime: UniLEDRuntime,
    key: str,
    *,
    channel: int = 0,
) -> SelectOptionMap | None:
    """Return the select option map for current model and parsed state."""
    if not select_channel_allows_options(
        runtime,
        key,
        channel=channel,
    ):
        return None

    if runtime.model.family is ProtocolFamily.ZENGGE_MESH and key == "effect":
        profile = mesh_profile_for_model(runtime.model)
        if profile is not None and profile.effect_names:
            return SelectOptionMap(
                key,
                {
                    index: name
                    for index, name in enumerate(profile.effect_names, start=1)
                },
            )

    option_map = select_option_map(
        runtime.model.family,
        key,
        color_cap=runtime.model.color_cap,
        model_name=runtime.model.name,
        spec_functions=runtime.model.spec_functions,
    )
    if option_map is not None:
        return option_map
    if key == "effect" and banlanx6xx_style_family(runtime.model.family):
        light_type = runtime.state.diagnostics.get("light_type")
        values = banlanx6xx_effect_values_for_light_type(
            light_type,
            model_name=runtime.model.name,
        )
        if values is not None:
            return SelectOptionMap(key, values)
    if key == "light_mode" and banlanx6xx_style_family(runtime.model.family):
        light_type = runtime.state.diagnostics.get("light_type")
        if light_type is None and banlanx6xx_model_has_dynamic_light_type(
            runtime.model.name
        ):
            return None
        light_type = _current_light_type(runtime)
        values = banlanx6xx_light_mode_values_for_light_type(
            light_type,
            model_name=runtime.model.name,
        )
        if values is not None:
            return SelectOptionMap(key, values)
    if key == "chip_order" and banlanx6xx_style_family(runtime.model.family):
        light_type = _current_light_type(runtime)
        values = banlanx6xx_chip_order_values_for_light_type(light_type)
        if values is not None:
            return SelectOptionMap(key, values)
    return None


def _zengge_mesh_supported_color_modes(
    runtime: UniLEDRuntime,
    channel: int,
) -> tuple[str, ...]:
    state = runtime.state.channels.get(channel)
    if state is not None:
        modes = state.extra.get("supported_color_modes")
        if isinstance(modes, (tuple, list, set)):
            raw_supported = tuple(
                mode
                for mode in modes
                if mode in {"brightness", "rgb", "color_temp", "white"}
            )
            if raw_supported:
                return _normalize_supported_color_modes(raw_supported)

    context = None
    if runtime.mesh_session is not None:
        context = runtime.mesh_session.contexts.get(channel)
    if context is not None:
        if context.node_wiring == 4:
            return ("rgb", "color_temp")
        if context.node_wiring == 2:
            return ("rgb", "white")

    return ("brightness",)


def apply_select_command_state(
    runtime: UniLEDRuntime,
    key: str,
    option: str,
    *,
    channel: int = 0,
) -> ChannelState:
    """Apply an optimistic select command state after a successful send."""
    state = channel_state(runtime, channel)
    raw_value = select_command_value(runtime, key, option, channel=channel)
    if key == "audio_input":
        state.audio_input = raw_value
    elif key == "effect":
        state.effect = option
        if banlanx6xx_style_family(runtime.model.family):
            mode, effect = mode_effect_parts(raw_value)
            state.light_mode = banlanx6xx_light_mode_name(mode)
            state.light_mode_number = mode
            state.effect_number = effect
            state.effect_type = _effect_type_for_value(
                runtime.model.family,
                effect,
                mode=mode,
            )
            _apply_sp6xx_effect_parameter_state(
                runtime,
                state,
                light_type=_current_light_type(runtime),
                mode=mode,
                effect=effect,
            )
        else:
            state.effect_number = raw_value
            state.effect_type = _effect_type_for_value(runtime.model.family, raw_value)
            _apply_banlanx_v23_effect_light_state(runtime, state, raw_value)
    elif key == "light_mode":
        command = light_mode_command_values(runtime, raw_value, channel=channel)
        if command is None:
            state.light_mode = option
            state.light_mode_number = raw_value
            state.effect_loop = raw_value != 0
        else:
            mode, effect = command
            light_type = _current_light_type(runtime)
            state.light_mode = banlanx6xx_light_mode_name(mode)
            state.light_mode_number = mode
            state.effect_number = effect
            state.effect = (
                None
                if light_type is None
                else _sp6xx_effect_label(
                    light_type,
                    mode,
                    effect,
                    model_name=runtime.model.name,
                )
            )
            state.effect_type = _effect_type_for_value(
                runtime.model.family,
                effect,
                mode=mode,
            )
            _apply_sp6xx_effect_parameter_state(
                runtime,
                state,
                light_type=light_type,
                mode=mode,
                effect=effect,
            )
    elif key == "light_type":
        command = light_type_command_values(runtime, raw_value, channel=channel)
        runtime.state.diagnostics["light_type"] = raw_value
        state.chip_order = command.chip_order
        state.light_mode_number = command.mode
        state.light_mode = banlanx6xx_light_mode_name(command.mode)
        state.effect_number = command.effect
        state.effect = _sp6xx_effect_label(
            raw_value,
            command.mode,
            command.effect,
            model_name=runtime.model.name,
        )
        state.effect_type = _effect_type_for_value(
            runtime.model.family,
            command.effect,
            mode=command.mode,
        )
        _apply_sp6xx_effect_parameter_state(
            runtime,
            state,
            light_type=raw_value,
            mode=command.mode,
            effect=command.effect,
        )
        if command.power:
            state.power = False
    elif key == "chip_order":
        state.chip_order = raw_value
    elif key == "chip_type":
        state.extra["chip_type"] = raw_value
        runtime.state.diagnostics["chip_type"] = raw_value
    elif key in {"onoff_effect", "onoff_speed", "on_power"}:
        runtime.state.diagnostics[key] = raw_value
    runtime.state.available = runtime.session_ready
    return state


def _apply_sp6xx_effect_parameter_state(
    runtime: UniLEDRuntime,
    state: ChannelState,
    *,
    light_type: int | None,
    mode: int,
    effect: int,
) -> None:
    """Clear stale SP6xx effect parameters unsupported by the selected effect."""
    if not banlanx6xx_style_family(runtime.model.family):
        return
    attributes = banlanx6xx_effect_attributes_for_state(
        light_type,
        mode,
        effect,
        model_name=runtime.model.name,
    )
    if attributes is None or not attributes.speedable:
        state.effect_speed = None
    if attributes is None or not attributes.sizeable:
        state.effect_length = None
    if attributes is None or not attributes.directional:
        state.effect_direction = None
    if attributes is None or not attributes.pausable:
        state.extra["play"] = None
    if mode not in {0x03, 0x04, 0x05, 0x06}:
        state.effect_loop = None


def _apply_banlanx_v23_effect_light_state(
    runtime: UniLEDRuntime,
    state: ChannelState,
    effect: int,
) -> None:
    """Mirror old UniLED's HA light-state side effects for V2/V3 effects."""
    white_effect = _BANLANX_V23_WHITE_EFFECTS.get(runtime.model.family)
    if white_effect is None or effect != white_effect:
        return
    if "white" not in light_supported_color_modes(runtime, channel=state.channel_id):
        return

    white_level = state.extra.get("white_level")
    if not isinstance(white_level, int):
        white_level = 0xFF
        state.extra["white_level"] = white_level
    state.brightness = white_level


def _effect_type_for_value(
    family: ProtocolFamily,
    value: int,
    *,
    mode: int | None = None,
) -> str:
    if family.value in {"banlanx_601", "banlanx_60x"}:
        if value == 0x19:
            return "Static"
        if value >= 0x65:
            return "Sound"
        return "Dynamic"
    if family.value == "banlanx_v2":
        if value in {0xBE, 0xBF}:
            return "Static"
        if value >= 0xC9:
            return "Sound"
        return "Dynamic"
    if family.value == "banlanx_v3":
        if value in {0x63, 0xCC}:
            return "Static"
        if 0x65 <= value < 0xCC:
            return "Sound"
        return "Dynamic"
    if banlanx6xx_style_family(family):
        if mode is None:
            mode, value = mode_effect_parts(value)
        if mode in {0x01, 0x02}:
            return "Static"
        if mode in {0x05, 0x06}:
            return "Sound"
        return "Dynamic"
    if value == 0:
        return "Static"
    return "Dynamic"


def apply_switch_command_state(
    runtime: UniLEDRuntime,
    key: str,
    value: bool,
    *,
    channel: int = 0,
) -> ChannelState:
    """Apply an optimistic switch command state after a successful send."""
    state = channel_state(runtime, channel)
    if key == "effect_direction":
        state.effect_direction = value
    elif key == "effect_loop":
        state.effect_loop = value
    elif key == "scene_loop":
        state.effect_loop = value
        runtime.state.diagnostics["scene_loop"] = value
    elif key == "effect_play":
        state.extra["play"] = value
    elif key == "coexistence":
        runtime.state.diagnostics["coexistence"] = 1 if value else 0
    runtime.state.available = runtime.session_ready
    return state


def apply_scene_command_state(
    runtime: UniLEDRuntime,
    scene: int,
    *,
    channel: int = 0,
) -> None:
    """Apply optimistic state after a successful scene recall."""
    runtime.state.diagnostics["scene"] = int(scene)
    runtime.state.diagnostics["scene_channel"] = int(channel)
    runtime.state.available = runtime.session_ready


def _diagnostic_option_value(runtime: UniLEDRuntime, key: str) -> str | None:
    option_map = select_option_map(
        runtime.model.family,
        key,
        color_cap=runtime.model.color_cap,
        model_name=runtime.model.name,
    )
    if option_map is None:
        return None
    return option_map.option_for_value(runtime.state.diagnostics.get(key))


def _light_type_option_value(runtime: UniLEDRuntime) -> str | None:
    values = banlanx6xx_light_type_values_for_model(runtime.model.name)
    if values is None:
        return None
    value = runtime.state.diagnostics.get("light_type")
    if value is None and banlanx6xx_model_has_dynamic_light_type(runtime.model.name):
        return None
    option_map = SelectOptionMap("light_type", values)
    return option_map.option_for_value(_current_light_type(runtime))


def _diagnostic_int(
    runtime: UniLEDRuntime,
    key: str,
    override: int | None,
    *,
    default: int,
) -> int:
    if override is not None:
        return int(override)
    value = runtime.state.diagnostics.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coexistence_value(runtime: UniLEDRuntime) -> bool | None:
    raw_value = runtime.state.diagnostics.get("coexistence")
    light_type = runtime.state.diagnostics.get("light_type")
    if light_type is not None:
        if not banlanx6xx_light_type_has_coexistence(light_type):
            return None
    elif not banlanx6xx_model_has_coexistence(runtime.model.name):
        return None
    if raw_value is None:
        return None
    return bool(raw_value)


def _current_light_type(runtime: UniLEDRuntime) -> int | None:
    value = runtime.state.diagnostics.get("light_type")
    if value is not None:
        return int(value)
    return banlanx6xx_default_light_type_for_model(runtime.model.name)


def _chip_order_for_light_type(
    runtime: UniLEDRuntime,
    light_type: int,
    *,
    channel: int,
) -> int:
    selected_values = banlanx6xx_chip_order_values_for_light_type(light_type)
    if selected_values is None:
        return 0
    selected_map = SelectOptionMap("chip_order", selected_values)
    current_light_type = _current_light_type(runtime)
    current_values = banlanx6xx_chip_order_values_for_light_type(current_light_type)
    state = channel_state(runtime, channel)
    if current_values is not None and state.chip_order is not None:
        current_label = SelectOptionMap(
            "chip_order",
            current_values,
        ).option_for_value(state.chip_order)
        if current_label in selected_map.options:
            return selected_map.value_for_option(current_label)
    return 0


def _sp6xx_effect_label(
    light_type: int,
    mode: int,
    effect: int,
    *,
    model_name: str | None = None,
) -> str | None:
    values = banlanx6xx_effect_values_for_light_type(
        light_type,
        model_name=model_name,
    )
    if values is None:
        return None
    return values.get(mode_effect_value(mode, effect))


def _redact(data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(key): _REDACTED if str(key) in _REDACT_KEYS else value
        for key, value in data.items()
    }


def _json_safe_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return diagnostics data using only JSON-safe value shapes."""
    return {str(key): _json_safe_value(value) for key, value in data.items()}


def _json_safe_value(value: Any) -> Any:
    """Convert binary parser diagnostics into stable diagnostic strings."""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, (tuple, list)):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, set):
        return sorted((_json_safe_value(item) for item in value), key=str)
    return value


def _catalog_variant_dict(
    model: CatalogModel,
    *,
    canonical: bool,
    selected: bool,
) -> dict[str, Any]:
    return {
        "id": model.model_id,
        "parent_id": model.parent_id,
        "name": model.name,
        "friendly_name": model.friendly_name,
        "home_uri": model.home_uri,
        "connect_caps": model.connect_caps,
        "connect_capabilities": list(model.connect_capabilities),
        "spec_functions": model.spec_functions,
        "spec_function_bits": list(model.spec_function_bits),
        "color_cap": model.color_cap,
        "color_capabilities": list(model.color_capabilities),
        "feature_keys": list(model.feature_keys),
        "family": model.family.value,
        "support_level": model.support_level.value,
        "transports": [transport.value for transport in model.transports],
        "legacy_uniled_supported": model.legacy_uniled_supported,
        "features": dict(model.features),
        "canonical": canonical,
        "selected": selected,
    }


def _entry_model_id(value: Any) -> int | None:
    if value in (None, ""):
        return None
    model_id = _optional_int(value)
    if model_id is None:
        raise RuntimeSetupError(
            "config entry has an invalid model_id",
            field=CONF_MODEL_ID,
            reason="invalid_model_id",
        )
    return model_id


def _credential_bytes(value: Any, *, default: bytes) -> bytes:
    if value is None or value == "":
        return default
    if isinstance(value, bytes):
        return value
    return str(value).encode()


def _legacy_uniled_parity_profile_dict(
    profile: LegacyUniLEDParityProfile | None,
) -> dict[str, Any] | None:
    """Return structured old-UniLED parity diagnostics."""
    if profile is None:
        return None
    return {
        "family": profile.family.value,
        "source_module": profile.source_module,
        "command_builders": list(profile.command_builders),
        "status_parser_hints": list(profile.status_parser_hints),
        "stubbed_builders": list(profile.stubbed_builders),
        "gap_hints": list(profile.gap_hints),
    }


def _protocol_evidence_profile_dict(
    profile: ProtocolEvidenceProfile | None,
) -> dict[str, Any] | None:
    """Return structured command-protocol evidence diagnostics."""
    if profile is None:
        return None
    return {
        "family": profile.family.value,
        "kind": profile.kind,
        "basis": profile.basis,
        "source_module": profile.source_module,
        "evidence_hints": list(profile.evidence_hints),
    }


def _car_light_profile_dict(
    profile: CarLightProfile | None,
) -> dict[str, Any] | None:
    if profile is None:
        return None
    data: dict[str, Any] = {
        "family": profile.family.value,
        "package": profile.package,
        "zones": list(profile.zones),
        "triggers": list(profile.triggers),
        "control_surfaces": list(profile.control_surfaces),
        "accessory_assets": list(profile.accessory_assets),
        "animation_assets": list(profile.animation_assets),
        "trigger_image_assets": list(profile.trigger_image_assets),
        "zone_image_assets": list(profile.zone_image_assets),
        "subdevice_hints": list(profile.subdevice_hints),
        "subdevice_filters": list(profile.subdevice_filters),
        "password_hints": list(profile.password_hints),
        "password_flow_states": list(profile.password_flow_states),
        "password_entry_hints": list(profile.password_entry_hints),
        "password_policy_hints": list(profile.password_policy_hints),
        "password_reset_hints": list(profile.password_reset_hints),
        "trigger_storage_hints": list(profile.trigger_storage_hints),
        "trigger_actions": list(profile.trigger_actions),
        "route_hints": list(profile.route_hints),
        "setup_requirements": list(profile.setup_requirements),
        "setup_flow_hints": list(profile.setup_flow_hints),
        "setup_key_hints": list(profile.setup_key_hints),
        "app_command_id_hints": _apk_command_id_hint_dicts(
            profile.app_command_id_hints
        ),
        "model_role": _car_light_model_role_dict(profile.model_role),
        "model_role_hints": list(profile.model_role_hints),
        "model_setup_dependency": _car_light_setup_dependency_dict(
            profile.model_setup_dependency
        ),
        "setup_dependencies": [
            _car_light_setup_dependency_dict(dependency)
            for dependency in profile.setup_dependencies
        ],
        "required_setup_dependencies": [
            _car_light_setup_dependency_dict(dependency)
            for dependency in car_light_required_setup_dependencies(profile)
        ],
        "ordered_setup_dependencies": [
            _car_light_setup_dependency_dict(dependency)
            for dependency in car_light_ordered_setup_dependencies(profile)
        ],
        "catalog_hints": list(profile.catalog_hints),
        "transport_hints": list(profile.transport_hints),
        "protocol_gap_hints": list(profile.protocol_gap_hints),
        "command_blockers": list(profile.command_blockers),
        "command_protocol_known": profile.command_protocol_known,
        "package_asset_count": profile.package_asset_count,
        "apk_asset_evidence": list(profile.apk_asset_evidence),
        "apk_string_evidence": list(profile.apk_string_evidence),
    }
    if profile.required_controller_model is not None:
        data["required_controller_model"] = profile.required_controller_model
    return data


def _car_light_model_role_dict(role: Any | None) -> dict[str, Any] | None:
    if role is None:
        return None
    return {
        "role": role.role,
        "setup_stage": role.setup_stage,
        "setup_order": role.setup_order,
        "required_controller_model": role.required_controller_model,
        "parent_group_model_id": role.parent_group_model_id,
    }


def _car_light_setup_dependency_dict(
    dependency: Any | None,
) -> dict[str, Any] | None:
    if dependency is None:
        return None
    return {
        "model_name": dependency.model_name,
        "relationship": dependency.relationship,
        "related_model": dependency.related_model,
        "setup_order": dependency.setup_order,
        "required": dependency.required,
        "enforcement_status": dependency.enforcement_status,
        "evidence": dependency.evidence,
    }


def _fish_tank_profile_dict(
    profile: FishTankProfile | None,
) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        "family": profile.family.value,
        "package": profile.package,
        "light_channels": list(profile.light_channels),
        "control_surfaces": list(profile.control_surfaces),
        "route_hints": list(profile.route_hints),
        "effect_hints": list(profile.effect_hints),
        "effect_string_hints": list(profile.effect_string_hints),
        "workflow_hints": list(profile.workflow_hints),
        "favorite_slots": list(profile.favorite_slots),
        "favorite_action_hints": list(profile.favorite_action_hints),
        "favorite_store_hints": list(profile.favorite_store_hints),
        "favorite_recall_hints": list(profile.favorite_recall_hints),
        "favorite_clear_hints": list(profile.favorite_clear_hints),
        "favorite_actions": list(profile.favorite_actions),
        "favorite_loop_hints": list(profile.favorite_loop_hints),
        "favorite_loop_actions": list(profile.favorite_loop_actions),
        "firmware_prompt_hints": list(profile.firmware_prompt_hints),
        "timer_limit": profile.timer_limit,
        "timer_slots": list(profile.timer_slots),
        "timer_hints": list(profile.timer_hints),
        "timer_string_hints": list(profile.timer_string_hints),
        "timer_actions": list(profile.timer_actions),
        "catalog_hints": list(profile.catalog_hints),
        "app_method_hints": list(profile.app_method_hints),
        "app_command_id_hints": _apk_command_id_hint_dicts(
            profile.app_command_id_hints
        ),
        "data_model_hints": list(profile.data_model_hints),
        "favorite_service_hints": list(profile.favorite_service_hints),
        "favorite_storage_hints": list(profile.favorite_storage_hints),
        "timer_storage_hints": list(profile.timer_storage_hints),
        "brightness_state_hints": list(profile.brightness_state_hints),
        "raw_string_hints": list(profile.raw_string_hints),
        "brightness_string_hints": list(profile.brightness_string_hints),
        "icon_assets": list(profile.icon_assets),
        "image_assets": list(profile.image_assets),
        "channel_assets": list(profile.channel_assets),
        "timer_assets": list(profile.timer_assets),
        "favorite_assets": list(profile.favorite_assets),
        "effect_assets": list(profile.effect_assets),
        "transport_hints": list(profile.transport_hints),
        "protocol_gap_hints": list(profile.protocol_gap_hints),
        "command_blockers": list(profile.command_blockers),
        "command_protocol_known": profile.command_protocol_known,
        "package_asset_count": profile.package_asset_count,
        "apk_asset_evidence": list(profile.apk_asset_evidence),
        "apk_string_evidence": list(profile.apk_string_evidence),
    }


def _scene_profile_dict(
    profile: SceneProfile | None,
) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        "family": profile.family.value,
        "package": profile.package,
        "presets": list(profile.presets),
        "control_surfaces": list(profile.control_surfaces),
        "route_hints": list(profile.route_hints),
        "lfx_route_hints": list(profile.lfx_route_hints),
        "timer_route_hints": list(profile.timer_route_hints),
        "mode_icon_count": profile.mode_icon_count,
        "mode_effects": list(profile.mode_effects),
        "mode_icon_samples": list(profile.mode_icon_samples),
        "app_method_hints": list(profile.app_method_hints),
        "app_command_id_hints": _apk_command_id_hint_dicts(
            profile.app_command_id_hints
        ),
        "storage_hints": list(profile.storage_hints),
        "recent_actions": list(profile.recent_actions),
        "favorite_actions": list(profile.favorite_actions),
        "timer_actions": list(profile.timer_actions),
        "diy_actions": list(profile.diy_actions),
        "white_brightness_anchors": list(profile.white_brightness_anchors),
        "raw_string_hints": list(profile.raw_string_hints),
        "lfx_data_model_hints": list(profile.lfx_data_model_hints),
        "lfx_frame_field_hints": list(profile.lfx_frame_field_hints),
        "native_handler_hints": list(profile.native_handler_hints),
        "native_paired_api_capabilities": list(
            profile.native_paired_api_capabilities
        ),
        "native_ic_only_api_capabilities": list(
            profile.native_ic_only_api_capabilities
        ),
        "native_loop_handlers": list(profile.native_loop_handlers),
        "native_library_hints": list(profile.native_library_hints),
        "native_frame_hints": list(profile.native_frame_hints),
        "native_opcode_hints": list(profile.native_opcode_hints),
        "native_state_hints": list(profile.native_state_hints),
        "native_state_exports": list(profile.native_state_exports),
        "native_color_order_hints": list(profile.native_color_order_hints),
        "native_pwm_table_hints": list(profile.native_pwm_table_hints),
        "native_music_effect_hints": list(profile.native_music_effect_hints),
        "native_pwm_driver_hints": list(profile.native_pwm_driver_hints),
        "native_animation_exports": list(profile.native_animation_exports),
        "native_drive_exports": list(profile.native_drive_exports),
        "native_persistence_handlers": list(profile.native_persistence_handlers),
        "native_persistence_exports": [
            {
                "capability": export.capability,
                "driver": export.driver,
                "symbol": export.symbol,
                "value": export.value,
                "size": export.size,
            }
            for export in profile.native_persistence_exports
        ],
        "native_persistence_capabilities": list(
            profile.native_persistence_capabilities
        ),
        "native_export_hints": list(profile.native_export_hints),
        "native_code_anchors": [
            {
                "name": name,
                "value": value,
                "value_hex": f"0x{value:08x}",
                "size": size,
                "sha256": sha256,
                "first16": first16,
                "last16": last16,
            }
            for name, value, size, sha256, first16, last16
            in profile.native_code_anchors
        ],
        "setup_requirements": list(profile.setup_requirements),
        "catalog_hints": list(profile.catalog_hints),
        "transport_hints": list(profile.transport_hints),
        "protocol_gap_hints": list(profile.protocol_gap_hints),
        "command_blockers": list(profile.command_blockers),
        "command_protocol_known": profile.command_protocol_known,
        "package_asset_count": profile.package_asset_count,
        "apk_asset_evidence": list(profile.apk_asset_evidence),
        "apk_string_evidence": list(profile.apk_string_evidence),
    }


def _sp630e_profile_dict(
    profile: SP630EProfile | None,
) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        "family": profile.family.value,
        "package": profile.package,
        "route_hints": list(profile.route_hints),
        "control_surfaces": list(profile.control_surfaces),
        "favorite_limit_hints": list(profile.favorite_limit_hints),
        "timer_limit": profile.timer_limit,
        "timer_hints": list(profile.timer_hints),
        "music_asset_hints": list(profile.music_asset_hints),
        "network_hints": list(profile.network_hints),
        "remote_hints": list(profile.remote_hints),
        "motor_hints": list(profile.motor_hints),
        "app_method_hints": list(profile.app_method_hints),
        "app_command_id_hints": _apk_command_id_hint_dicts(
            profile.app_command_id_hints
        ),
        "data_model_hints": list(profile.data_model_hints),
        "native_lfx_hints": list(profile.native_lfx_hints),
        "native_export_detail_anchors": _native_export_anchor_dicts(
            profile.native_export_detail_anchors
        ),
        "catalog_hints": list(profile.catalog_hints),
        "protocol_gap_hints": list(profile.protocol_gap_hints),
        "command_protocol_known": profile.command_protocol_known,
        "package_asset_count": profile.package_asset_count,
        "apk_asset_evidence": list(profile.apk_asset_evidence),
        "apk_string_evidence": list(profile.apk_string_evidence),
    }


def _network_profile_dict(
    profile: NetworkProfile | None,
) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        "family": profile.family.value,
        "package": profile.package,
        "route_hints": list(profile.route_hints),
        "control_surfaces": list(profile.control_surfaces),
        "content_modes": list(profile.content_modes),
        "artnet_fields": list(profile.artnet_fields),
        "port_fields": list(profile.port_fields),
        "playlist_actions": list(profile.playlist_actions),
        "matrix_music_controls": list(profile.matrix_music_controls),
        "supports_artnet": profile.supports_artnet,
        "supports_lfx": profile.supports_lfx,
        "panel_layout_supported": profile.panel_layout_supported,
        "regular_lfx_effects": list(profile.regular_lfx_effects),
        "regular_lfx_effect_assets": list(profile.regular_lfx_effect_assets),
        "lfx_gif_count": profile.lfx_gif_count,
        "lfx_gif_assets": list(profile.lfx_gif_assets),
        "app_method_hints": list(profile.app_method_hints),
        "app_command_id_hints": _apk_command_id_hint_dicts(
            profile.app_command_id_hints
        ),
        "workflow_hints": list(profile.workflow_hints),
        "raw_string_hints": list(profile.raw_string_hints),
        "import_constraints": list(profile.import_constraints),
        "catalog_hints": list(profile.catalog_hints),
        "transport_hints": list(profile.transport_hints),
        "protocol_gap_hints": list(profile.protocol_gap_hints),
        "command_blockers": list(profile.command_blockers),
        "native_library_hints": list(profile.native_library_hints),
        "native_frame_hints": list(profile.native_frame_hints),
        "native_lfx_param_hints": list(profile.native_lfx_param_hints),
        "native_effect_generator_hints": list(
            profile.native_effect_generator_hints
        ),
        "native_matrix_mode_hints": list(profile.native_matrix_mode_hints),
        "native_pixel_helper_hints": list(profile.native_pixel_helper_hints),
        "native_export_hints": list(profile.native_export_hints),
        "native_export_detail_anchors": _native_export_anchor_dicts(
            profile.native_export_detail_anchors
        ),
        "command_protocol_known": profile.command_protocol_known,
        "package_asset_count": profile.package_asset_count,
        "apk_asset_evidence": list(profile.apk_asset_evidence),
        "apk_string_evidence": list(profile.apk_string_evidence),
    }


def _apk_command_id_hint_dicts(
    hints: tuple[ApkCommandIdHint, ...],
) -> list[dict[str, Any]]:
    return [
        {
            "name": hint.name,
            "ordinal": hint.ordinal,
            "command_id": hint.command_id,
            "command_id_hex": hint.command_id_hex,
            "source": hint.source,
        }
        for hint in hints
    ]


def _native_export_anchor_dicts(
    anchors: tuple[tuple[str, int, int], ...],
) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "address": address,
            "address_hex": f"0x{address:08x}",
            "size": size,
        }
        for name, address, size in anchors
    ]


def _lan_profile_dict(profile: LANProfile | None) -> dict[str, Any] | None:
    if profile is None:
        return None
    data: dict[str, Any] = {
        "family": profile.family.value,
        "network_info_code": profile.network_info_code,
        "max_data_length": profile.max_data_length,
        "command_protocol_known": profile.command_protocol_known,
        "discovery_confirmed": profile.discovery_confirmed,
        "requires_manual_host": profile.requires_manual_host,
        "host_network_methods": list(profile.host_network_methods),
        "apk_discovery_hints": list(profile.apk_discovery_hints),
        "apk_discovery_channels": list(profile.apk_discovery_channels),
        "network_setup_route_hints": list(profile.network_setup_route_hints),
        "network_setup_prompts": list(profile.network_setup_prompts),
        "network_cloud_setup_prompts": list(
            profile.network_cloud_setup_prompts
        ),
        "multicast_lock_methods": list(profile.multicast_lock_methods),
        "bonsoir_methods": list(profile.bonsoir_methods),
        "bonsoir_arguments": list(profile.bonsoir_arguments),
        "bonsoir_nsd_methods": list(profile.bonsoir_nsd_methods),
        "bonsoir_discovery_events": list(profile.bonsoir_discovery_events),
        "bonsoir_service_event_fields": list(
            profile.bonsoir_service_event_fields
        ),
        "bonsoir_service_normalization_hints": list(
            profile.bonsoir_service_normalization_hints
        ),
        "bonsoir_service_type_flow_hints": list(
            profile.bonsoir_service_type_flow_hints
        ),
        "bonsoir_txt_query_flow_hints": list(
            profile.bonsoir_txt_query_flow_hints
        ),
        "discovery_gap_hints": list(profile.discovery_gap_hints),
        "raw_socket_hints": list(profile.raw_socket_hints),
        "discovery_status_hints": list(profile.discovery_status_hints),
        "mdns_multicast_group": profile.mdns_multicast_group,
        "mdns_port": profile.mdns_port,
        "mdns_ttl": profile.mdns_ttl,
        "mdns_txt_query_timeout_ms": profile.mdns_txt_query_timeout_ms,
        "mdns_txt_record_type": profile.mdns_txt_record_type,
        "mdns_txt_query_class": profile.mdns_txt_query_class,
        "udp_socket_timeout_ms": profile.udp_socket_timeout_ms,
        "udp_receive_buffer_bytes": profile.udp_receive_buffer_bytes,
        "mdns_txt_buffer_bytes": profile.mdns_txt_buffer_bytes,
    }
    if profile.network_setup_guide_assets:
        data["network_setup_guide_assets"] = list(
            profile.network_setup_guide_assets
        )
    if profile.spnet_discovery_known:
        data["spnet_discovery_known"] = profile.spnet_discovery_known
        data["spnet_udp_port"] = profile.spnet_udp_port
        data["spnet_discovery_request"] = profile.spnet_discovery_request.hex()
        data["spnet_response_prefix"] = profile.spnet_response_prefix.hex()
        data["spnet_evidence"] = list(profile.spnet_evidence)
    if profile.sptech_tcp_port is not None:
        data["sptech_tcp_port"] = profile.sptech_tcp_port
        data["sptech_magic"] = profile.sptech_magic.hex()
        data["sptech_status_query"] = profile.sptech_status_query.hex()
        data["sptech_response_header_bytes"] = (
            profile.sptech_response_header_bytes
        )
        data["sptech_candidate_evidence"] = list(
            profile.sptech_candidate_evidence
        )
    if profile.sptech_legacy_model_codes:
        data["sptech_legacy_model_codes"] = [
            {
                "code": candidate.code,
                "code_hex": candidate.code_hex,
                "model_name": candidate.model_name,
                "source": candidate.source,
            }
            for candidate in profile.sptech_legacy_model_codes
        ]
        data["sptech_legacy_model_code_evidence"] = list(
            profile.sptech_legacy_model_code_evidence
        )
    if profile.sptech_legacy_configuration_codes:
        data["sptech_legacy_configuration_codes"] = [
            {
                "code": candidate.code,
                "code_hex": candidate.code_hex,
                "label": candidate.label,
                "model_names": list(candidate.model_names),
                "source": candidate.source,
            }
            for candidate in profile.sptech_legacy_configuration_codes
        ]
    if profile.sptech_legacy_command_ids:
        data["sptech_legacy_command_ids"] = [
            {
                "name": candidate.name,
                "command_id": candidate.command_id,
                "command_id_hex": candidate.command_id_hex,
                "category": candidate.category,
                "source": candidate.source,
            }
            for candidate in profile.sptech_legacy_command_ids
        ]
    if profile.sptech_legacy_status_chunks:
        data["sptech_legacy_status_chunks"] = [
            {
                "chunk_type": candidate.chunk_type,
                "chunk_type_hex": candidate.chunk_type_hex,
                "label": candidate.label,
                "source": candidate.source,
            }
            for candidate in profile.sptech_legacy_status_chunks
        ]
        data["sptech_legacy_protocol_evidence"] = list(
            profile.sptech_legacy_protocol_evidence
        )
    return data


def _ble_evidence_profile_dict(
    profile: BLEEvidenceProfile | None,
) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        "family": profile.family.value,
        "command_profile_known": profile.command_profile_known,
        "known_service_uuids": list(profile.known_service_uuids),
        "known_write_uuid": profile.known_write_uuid,
        "known_notify_uuid": profile.known_notify_uuid,
        "uuid_binding_status": profile.uuid_binding_status,
        "apk_uuid_pool": list(profile.apk_uuid_pool),
        "uuid_inventory": [
            {
                "uuid": candidate.uuid,
                "short_name": candidate.short_name,
                "apk_string": candidate.apk_string,
                "known_usage": candidate.known_usage,
                "unported_binding_status": candidate.unported_binding_status,
                "evidence": candidate.evidence,
            }
            for candidate in profile.uuid_inventory
        ],
        "unbound_uuid_candidates": [
            candidate.short_name for candidate in profile.unbound_uuid_candidates
        ],
        "legacy_uuid_candidates": [
            candidate.short_name for candidate in profile.legacy_uuid_candidates
        ],
        "plugin_channels": list(profile.plugin_channels),
        "plugin_methods": list(profile.plugin_methods),
        "plugin_arguments": list(profile.plugin_arguments),
        "plugin_result_fields": list(profile.plugin_result_fields),
        "scan_result_fields": list(profile.scan_result_fields),
        "service_result_fields": list(profile.service_result_fields),
        "characteristic_result_fields": list(profile.characteristic_result_fields),
        "rssi_result_fields": list(profile.rssi_result_fields),
        "mtu_result_fields": list(profile.mtu_result_fields),
        "adapter_state_result_fields": list(profile.adapter_state_result_fields),
        "notification_event_fields": list(profile.notification_event_fields),
        "connection_event_fields": list(profile.connection_event_fields),
        "device_found_event_fields": list(profile.device_found_event_fields),
        "descriptor_uuids": list(profile.descriptor_uuids),
        "boolean_event_channels": list(profile.boolean_event_channels),
        "plugin_event_hints": [
            {
                "channel": hint.channel,
                "fields": list(hint.fields),
                "behavior": hint.behavior,
                "evidence": hint.evidence,
            }
            for hint in profile.plugin_event_hints
        ],
        "plugin_contract_hints": [
            {
                "method": hint.method,
                "required_arguments": list(hint.required_arguments),
                "default_arguments": list(hint.default_arguments),
                "behavior": hint.behavior,
                "error_code": hint.error_code,
                "evidence": hint.evidence,
            }
            for hint in profile.plugin_contract_hints
        ],
        "plugin_error_hints": [
            {
                "code": hint.code,
                "meaning": hint.meaning,
                "trigger": hint.trigger,
                "evidence": hint.evidence,
            }
            for hint in profile.plugin_error_hints
        ],
        "protocol_gap_hints": list(profile.protocol_gap_hints),
        "issue_advertisements": [
            {
                "issue": advertisement.issue,
                "model_name": advertisement.model_name,
                **(
                    {"model_id": advertisement.model_id}
                    if advertisement.model_id is not None
                    else {}
                ),
                "manufacturer_id": advertisement.manufacturer_id,
                "manufacturer_payload_hex": (
                    advertisement.manufacturer_payload_hex
                ),
                "service_uuid": advertisement.service_uuid,
                "evidence": advertisement.evidence,
            }
            for advertisement in profile.issue_advertisements
        ],
    }


def _mesh_profile_dict(profile: BLEMeshProfile | None) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        "family": profile.family.value,
        "protocol_name": profile.protocol_name,
        "package": profile.package,
        "service_uuid": profile.service_uuid,
        "status_uuid": profile.status_uuid,
        "command_uuid": profile.command_uuid,
        "pair_uuid": profile.pair_uuid,
        "manufacturer_id": profile.manufacturer_id,
        "telink_manufacturer_id": profile.telink_manufacturer_id,
        "default_mesh_uuid": profile.default_mesh_uuid,
        "requires_pairing": profile.requires_pairing,
        "requires_cloud_mesh_credentials": profile.requires_cloud_mesh_credentials,
        "old_uniled_protocol_known": profile.old_uniled_protocol_known,
        "core_command_protocol_known": profile.core_command_protocol_known,
        "status_uses_notifications": profile.status_uses_notifications,
        "effect_count": len(profile.effect_names),
        "command_names": list(profile.command_names),
        "effect_command_fields": list(profile.effect_command_fields),
        "sig_mesh_uuid_hints": list(profile.sig_mesh_uuid_hints),
        "app_command_id_hints": _apk_command_id_hint_dicts(
            profile.app_command_id_hints
        ),
        "control_gap_hints": list(profile.control_gap_hints),
        "control_blockers": list(profile.control_blockers),
        "route_hints": list(profile.route_hints),
        "provisioning_hints": list(profile.provisioning_hints),
        "provisioning_state_hints": list(profile.provisioning_state_hints),
        "package_asset_count": profile.package_asset_count,
        "apk_asset_evidence": list(profile.apk_asset_evidence),
        "apk_string_evidence": list(profile.apk_string_evidence),
    }


def _cloud_profile_dict(
    profile: BanlanXCloudProfile | None,
) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        "provider": profile.provider,
        "model_name": profile.model_name,
        "base_urls": list(profile.base_urls),
        "auth_endpoints": list(profile.auth_endpoints),
        "account_auth_endpoints": list(profile.account_auth_endpoints),
        "device_endpoints": list(profile.device_endpoints),
        "home_device_endpoints": list(profile.home_device_endpoints),
        "user_device_endpoints": list(profile.user_device_endpoints),
        "local_device_endpoints": list(profile.local_device_endpoints),
        "btmesh_endpoints": list(profile.btmesh_endpoints),
        "root_device_endpoints": list(profile.root_device_endpoints),
        "raw_command_endpoints": list(profile.raw_command_endpoints),
        "content_endpoints": list(profile.content_endpoints),
        "voice_assistant_endpoints": list(profile.voice_assistant_endpoints),
        "endpoint_groups": list(profile.endpoint_groups),
        "command_related_endpoint_paths": [
            endpoint.path for endpoint in profile.command_related_endpoints
        ],
        "unresolved_base_url_endpoint_paths": [
            endpoint.path for endpoint in profile.unresolved_base_url_endpoints
        ],
        "unproven_auth_endpoint_paths": [
            endpoint.path for endpoint in profile.unproven_auth_endpoints
        ],
        "endpoint_inventory": [
            _cloud_endpoint_dict(endpoint)
            for endpoint in profile.endpoint_inventory
        ],
        "request_contract_hints": [
            _cloud_request_contract_hint_dict(hint)
            for hint in profile.request_contract_hints
        ],
        "token_contract_hint_strings": [
            hint.apk_string for hint in profile.token_contract_hints
        ],
        "header_contract_hint_strings": [
            hint.apk_string for hint in profile.header_contract_hints
        ],
        "signature_contract_hint_strings": [
            hint.apk_string for hint in profile.signature_contract_hints
        ],
        "document_urls": list(profile.document_urls),
        "auth_token_hints": list(profile.auth_token_hints),
        "device_identity_hints": list(profile.device_identity_hints),
        "http_header_hints": list(profile.http_header_hints),
        "signature_hints": list(profile.signature_hints),
        "catalog_hints": list(profile.catalog_hints),
        "transport_hints": list(profile.transport_hints),
        "protocol_gap_hints": list(profile.protocol_gap_hints),
        "command_blockers": list(profile.command_blockers),
        "command_protocol_known": profile.command_protocol_known,
        "apk_string_evidence": list(profile.apk_string_evidence),
    }


def _cloud_endpoint_dict(endpoint: BanlanXCloudEndpoint) -> dict[str, Any]:
    return {
        "group": endpoint.group,
        "path": endpoint.path,
        "method": endpoint.method,
        "auth": endpoint.auth,
        "base_url": endpoint.base_url,
        "command_related": endpoint.command_related,
        "evidence": endpoint.evidence,
    }


def _cloud_request_contract_hint_dict(
    hint: BanlanXCloudRequestContractHint,
) -> dict[str, Any]:
    return {
        "category": hint.category,
        "apk_string": hint.apk_string,
        "unported_binding_status": hint.unported_binding_status,
        "blocker": hint.blocker,
        "evidence": hint.evidence,
    }
