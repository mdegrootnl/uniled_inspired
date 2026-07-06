"""Build Home Assistant-independent entity plans from catalog metadata."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .car_lights import car_light_profile_for_model
from .catalog import CatalogModel, ProtocolFamily, SupportLevel, TransportKind
from .cloud import cloud_profile_for_model
from .fish_tank import fish_tank_profile_for_model
from .legacy_parity import legacy_uniled_parity_profile_for_model
from .network import network_profile_for_model
from .options import (
    banlanx6xx_model_has_coexistence,
    banlanx6xx_model_has_dynamic_light_type,
    banlanx6xx_model_has_light_type_select,
    banlanx6xx_style_family,
    legacy_v23_model_has_audio_controls,
    select_options_for_model,
)
from .protocol_evidence import protocol_evidence_profile_for_model
from .scene import scene_profile_for_model
from .sp630e import sp630e_profile_for_model
from .transports import lan_profile_for_model, mesh_profile_for_model


class PlatformKind(StrEnum):
    """Home Assistant platform kinds used by the integration shell."""

    LIGHT = "light"
    SELECT = "select"
    NUMBER = "number"
    SWITCH = "switch"
    BUTTON = "button"
    SENSOR = "sensor"
    SCENE = "scene"


class EntityCategoryKind(StrEnum):
    """Entity category values independent from Home Assistant imports."""

    CONFIG = "config"
    DIAGNOSTIC = "diagnostic"


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """A planned entity or entity capability."""

    key: str
    platform: PlatformKind
    name: str
    channel: int = 0
    entity_category: EntityCategoryKind | None = None
    enabled_by_default: bool = True
    implemented: bool = False
    options: tuple[str, ...] = ()
    color_modes: tuple[str, ...] = ()
    minimum: int | None = None
    maximum: int | None = None
    step: int | None = None
    unit: str | None = None
    implementation_hint: str | None = None

    @property
    def is_control(self) -> bool:
        """Return whether this feature sends commands to the device."""
        return self.entity_category is not EntityCategoryKind.DIAGNOSTIC


@dataclass(frozen=True, slots=True)
class EntityPlan:
    """The complete entity plan for one catalog model."""

    model: CatalogModel
    features: tuple[FeatureSpec, ...]

    @property
    def family(self) -> ProtocolFamily:
        """Protocol family for the planned model."""
        return self.model.family

    @property
    def support_level(self) -> SupportLevel:
        """Current support disposition."""
        return self.model.support_level

    @property
    def transports(self) -> tuple[TransportKind, ...]:
        """Transports available to this model."""
        return self.model.transports

    def features_for_platform(
        self, platform: PlatformKind
    ) -> tuple[FeatureSpec, ...]:
        """Return features planned for a platform."""
        return tuple(
            feature for feature in self.features if feature.platform is platform
        )

    def has_feature(self, key: str) -> bool:
        """Return whether a feature key is present."""
        return any(feature.key == key for feature in self.features)

    def feature(self, key: str) -> FeatureSpec:
        """Return a single feature by key."""
        for feature in self.features:
            if feature.key == key:
                return feature
        raise KeyError(key)


def plan_for_model(model: CatalogModel) -> EntityPlan:
    """Build the entity plan for a catalog model."""
    if model.support_level is SupportLevel.FILTERED:
        return EntityPlan(model=model, features=())

    features: list[FeatureSpec] = [
        _diagnostic("catalog_model", "Catalog model"),
        _diagnostic("catalog_model_id", "Catalog model ID"),
        _diagnostic("catalog_parent_id", "Catalog parent ID"),
        _diagnostic("catalog_connect_caps", "Catalog connectCaps"),
        _diagnostic("catalog_connect_capabilities", "Catalog connect capabilities"),
        _diagnostic("catalog_spec_functions", "Catalog specFunctions"),
        _diagnostic("catalog_spec_function_bits", "Catalog specFunction bits"),
        _diagnostic("catalog_color_cap", "Catalog colorCap"),
        _diagnostic("catalog_color_capabilities", "Catalog color capabilities"),
        _diagnostic("catalog_feature_count", "Catalog feature count", unit="features"),
        _diagnostic("catalog_feature_keys", "Catalog feature keys"),
        _diagnostic("catalog_feature_summary", "Catalog feature summary"),
        _diagnostic("catalog_variant_count", "Catalog variant count"),
        _diagnostic("catalog_variant_ids", "Catalog variant IDs"),
        _diagnostic("protocol_family", "Protocol family"),
        _diagnostic("support_level", "Support level"),
        _diagnostic("support_disposition", "Support disposition"),
        _diagnostic("support_blocker_count", "Support blocker count"),
        _diagnostic("support_blockers", "Support blockers"),
        _diagnostic("transport", "Transport"),
        _diagnostic("configured_transport", "Configured transport"),
        _diagnostic("discovery_source", "Discovery source"),
        _diagnostic("discovery_match", "Discovery match"),
        _diagnostic("discovery_confidence", "Discovery confidence"),
        _diagnostic("runtime_transport_state", "Runtime transport state"),
        _diagnostic("last_refresh_result", "Last refresh result"),
    ]

    if legacy_uniled_parity_profile_for_model(model) is not None:
        features.append(
            _diagnostic(
                "legacy_uniled_parity",
                "Legacy UniLED parity candidate",
                implementation_hint="legacy_uniled",
            )
        )
        features.extend(
            (
                _diagnostic(
                    "legacy_uniled_parity_profile",
                    "Legacy UniLED parity profile",
                    implementation_hint="legacy_uniled",
                ),
                _diagnostic(
                    "legacy_uniled_command_count",
                    "Legacy UniLED command count",
                    unit="commands",
                    implementation_hint="legacy_uniled",
                ),
                _diagnostic(
                    "legacy_uniled_status_parser_count",
                    "Legacy UniLED status parser count",
                    unit="parsers",
                    implementation_hint="legacy_uniled",
                ),
                _diagnostic(
                    "legacy_uniled_stubbed_command_count",
                    "Legacy UniLED stubbed command count",
                    unit="stubs",
                    implementation_hint="legacy_uniled",
                ),
                _diagnostic(
                    "legacy_uniled_parity_gap_count",
                    "Legacy UniLED parity gap count",
                    unit="gaps",
                    implementation_hint="legacy_uniled",
                ),
            )
        )

    if protocol_evidence_profile_for_model(model) is not None:
        features.extend(
            (
                _diagnostic(
                    "protocol_evidence_profile",
                    "Protocol evidence profile",
                    implementation_hint="protocol_evidence",
                ),
                _diagnostic(
                    "protocol_evidence_kind",
                    "Protocol evidence kind",
                    implementation_hint="protocol_evidence",
                ),
                _diagnostic(
                    "protocol_evidence_hint_count",
                    "Protocol evidence hint count",
                    unit="hints",
                    implementation_hint="protocol_evidence",
                ),
            )
        )

    if TransportKind.BLE in model.transports:
        features.extend(
            (
                _diagnostic("ble_profile", "BLE profile"),
                _diagnostic(
                    "ble_uuid_binding_status",
                    "BLE UUID binding status",
                ),
                _diagnostic(
                    "ble_known_service_uuid_count",
                    "BLE known service UUID count",
                    unit="uuids",
                ),
                _diagnostic(
                    "ble_known_service_uuids",
                    "BLE known service UUIDs",
                ),
                _diagnostic(
                    "ble_known_write_uuid",
                    "BLE known write UUID",
                ),
                _diagnostic(
                    "ble_known_notify_uuid",
                    "BLE known notify UUID",
                ),
                _diagnostic(
                    "ble_uuid_pool_count",
                    "BLE APK UUID pool count",
                    unit="uuids",
                ),
                _diagnostic(
                    "ble_apk_uuid_pool",
                    "BLE APK UUID pool",
                ),
                _diagnostic(
                    "ble_uuid_inventory_count",
                    "BLE APK UUID inventory count",
                    unit="uuids",
                ),
                _diagnostic(
                    "ble_unbound_uuid_candidate_count",
                    "BLE unbound UUID candidate count",
                    unit="uuids",
                ),
                _diagnostic(
                    "ble_unbound_uuid_candidates",
                    "BLE unbound UUID candidates",
                ),
                _diagnostic(
                    "ble_legacy_uuid_candidate_count",
                    "BLE legacy UUID candidate count",
                    unit="uuids",
                ),
                _diagnostic(
                    "ble_legacy_uuid_candidates",
                    "BLE legacy UUID candidates",
                ),
                _diagnostic(
                    "ble_plugin_method_count",
                    "BLE plugin method count",
                    unit="methods",
                ),
                _diagnostic(
                    "ble_plugin_argument_count",
                    "BLE plugin argument count",
                    unit="arguments",
                ),
                _diagnostic(
                    "ble_plugin_result_field_count",
                    "BLE plugin result field count",
                    unit="fields",
                ),
                _diagnostic(
                    "ble_scan_result_field_count",
                    "BLE scan result field count",
                    unit="fields",
                ),
                _diagnostic(
                    "ble_service_result_field_count",
                    "BLE service result field count",
                    unit="fields",
                ),
                _diagnostic(
                    "ble_characteristic_result_field_count",
                    "BLE characteristic result field count",
                    unit="fields",
                ),
                _diagnostic(
                    "ble_rssi_result_field_count",
                    "BLE RSSI result field count",
                    unit="fields",
                ),
                _diagnostic(
                    "ble_mtu_result_field_count",
                    "BLE MTU result field count",
                    unit="fields",
                ),
                _diagnostic(
                    "ble_adapter_state_result_field_count",
                    "BLE adapter-state result field count",
                    unit="fields",
                ),
                _diagnostic(
                    "ble_notification_event_field_count",
                    "BLE notification event field count",
                    unit="fields",
                ),
                _diagnostic(
                    "ble_connection_event_field_count",
                    "BLE connection event field count",
                    unit="fields",
                ),
                _diagnostic(
                    "ble_device_found_event_field_count",
                    "BLE device-found event field count",
                    unit="fields",
                ),
                _diagnostic(
                    "ble_descriptor_uuid_count",
                    "BLE descriptor UUID count",
                    unit="uuids",
                ),
                _diagnostic(
                    "ble_boolean_event_channel_count",
                    "BLE boolean event channel count",
                    unit="channels",
                ),
                _diagnostic(
                    "ble_plugin_event_hint_count",
                    "BLE plugin event hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "ble_plugin_contract_hint_count",
                    "BLE plugin contract hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "ble_plugin_error_code_count",
                    "BLE plugin error code count",
                    unit="codes",
                ),
                _diagnostic(
                    "ble_plugin_channel_count",
                    "BLE plugin channel count",
                    unit="channels",
                ),
                _diagnostic(
                    "ble_protocol_gap_count",
                    "BLE protocol gap count",
                    unit="gaps",
                ),
                _diagnostic(
                    "ble_issue_advertisement_count",
                    "BLE old-UniLED issue advertisement count",
                    unit="adverts",
                ),
                _diagnostic(
                    "ble_issue_advertisements",
                    "BLE old-UniLED issue advertisements",
                ),
            )
        )

    if TransportKind.LAN in model.transports:
        profile = lan_profile_for_model(model)
        features.extend(
            (
                _diagnostic("lan_profile", "LAN profile"),
                _diagnostic(
                    "lan_host_network_method_count",
                    "LAN host network method count",
                    unit="methods",
                ),
                _diagnostic(
                    "lan_host_setup_mode",
                    "LAN host setup mode",
                ),
                _diagnostic(
                    "lan_discovery_plugin_count",
                    "LAN discovery plugin count",
                    unit="plugins",
                ),
                _diagnostic(
                    "lan_discovery_channel_count",
                    "LAN discovery channel count",
                    unit="channels",
                ),
                _diagnostic(
                    "lan_network_setup_route_count",
                    "LAN network setup route count",
                    unit="routes",
                ),
                _diagnostic(
                    "lan_network_setup_prompt_count",
                    "LAN network setup prompt count",
                    unit="prompts",
                ),
                _diagnostic(
                    "lan_network_cloud_setup_prompt_count",
                    "LAN network cloud setup prompt count",
                    unit="prompts",
                ),
                _diagnostic(
                    "lan_multicast_lock_method_count",
                    "LAN multicast-lock method count",
                    unit="methods",
                ),
                _diagnostic(
                    "lan_bonsoir_method_count",
                    "LAN Bonsoir method count",
                    unit="methods",
                ),
                _diagnostic(
                    "lan_bonsoir_argument_count",
                    "LAN Bonsoir argument count",
                    unit="arguments",
                ),
                _diagnostic(
                    "lan_bonsoir_nsd_method_count",
                    "LAN Bonsoir NSD method count",
                    unit="methods",
                ),
                _diagnostic(
                    "lan_bonsoir_discovery_event_count",
                    "LAN Bonsoir discovery event count",
                    unit="events",
                ),
                _diagnostic(
                    "lan_bonsoir_service_event_field_count",
                    "LAN Bonsoir service event field count",
                    unit="fields",
                ),
                _diagnostic(
                    "lan_bonsoir_service_normalization_hint_count",
                    "LAN Bonsoir service normalization hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "lan_bonsoir_service_type_flow_hint_count",
                    "LAN Bonsoir service-type flow hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "lan_bonsoir_txt_query_flow_hint_count",
                    "LAN Bonsoir TXT query flow hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "lan_discovery_gap_count",
                    "LAN discovery gap count",
                    unit="gaps",
                ),
                _diagnostic(
                    "lan_raw_socket_hint_count",
                    "LAN raw socket hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "lan_discovery_status_hint_count",
                    "LAN discovery status hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "lan_udp_socket_timeout_ms",
                    "LAN UDP socket timeout",
                    unit="ms",
                ),
                _diagnostic(
                    "lan_udp_receive_buffer_bytes",
                    "LAN UDP receive buffer",
                    unit="bytes",
                ),
                _diagnostic(
                    "lan_mdns_txt_query_timeout_ms",
                    "LAN mDNS TXT query timeout",
                    unit="ms",
                ),
                _diagnostic(
                    "lan_mdns_txt_record_type",
                    "LAN mDNS TXT record type",
                ),
                _diagnostic(
                    "lan_mdns_txt_query_class",
                    "LAN mDNS TXT query class",
                ),
                _diagnostic(
                    "lan_mdns_txt_buffer_bytes",
                    "LAN mDNS TXT buffer",
                    unit="bytes",
                ),
            )
        )
        if profile is not None and profile.network_setup_guide_assets:
            features.append(
                _diagnostic(
                    "lan_network_setup_guide_asset_count",
                    "LAN network setup guide asset count",
                    unit="assets",
                )
            )
        if profile is not None and profile.sptech_legacy_model_codes:
            features.append(
                _diagnostic(
                    "lan_sptech_legacy_model_code_count",
                    "LAN SPTech legacy model-code count",
                    unit="codes",
                )
            )
        if profile is not None and profile.sptech_legacy_configuration_codes:
            features.append(
                _diagnostic(
                    "lan_sptech_legacy_configuration_code_count",
                    "LAN SPTech legacy configuration-code count",
                    unit="codes",
                )
            )
        if profile is not None and profile.sptech_legacy_command_ids:
            features.append(
                _diagnostic(
                    "lan_sptech_legacy_command_id_count",
                    "LAN SPTech legacy command ID count",
                    unit="commands",
                )
            )
        if profile is not None and profile.sptech_legacy_status_chunks:
            features.append(
                _diagnostic(
                    "lan_sptech_legacy_status_chunk_count",
                    "LAN SPTech legacy status chunk count",
                    unit="chunks",
                )
            )

    if TransportKind.BLE_MESH in model.transports:
        features.append(_diagnostic("mesh_profile", "Mesh profile"))
        mesh_profile = mesh_profile_for_model(model)
        if mesh_profile is not None:
            if mesh_profile.route_hints:
                features.append(
                    _diagnostic(
                        "mesh_route_count",
                        "Mesh APK route count",
                        unit="routes",
                    )
                )
            if mesh_profile.provisioning_hints:
                features.append(
                    _diagnostic(
                        "mesh_provisioning_hint_count",
                        "Mesh provisioning hint count",
                        unit="hints",
                    )
                )
            if mesh_profile.provisioning_state_hints:
                features.extend(
                    (
                        _diagnostic(
                            "mesh_provisioning_state_count",
                            "Mesh provisioning state count",
                            unit="states",
                        ),
                        _planned_select(
                            "mesh_provisioning_state",
                            "Mesh provisioning state",
                            options=mesh_profile.provisioning_state_hints,
                        ),
                    )
                )
            if mesh_profile.sig_mesh_uuid_hints:
                features.append(
                    _diagnostic(
                        "mesh_sig_mesh_uuid_hint_count",
                        "Mesh SIG UUID hint count",
                        unit="uuids",
                    )
                )
            if mesh_profile.app_command_id_hints:
                features.append(
                    _diagnostic(
                        "mesh_app_command_id_count",
                        "Mesh app command ID count",
                        unit="ids",
                    )
                )
            if mesh_profile.control_blockers:
                features.append(
                    _diagnostic(
                        "mesh_control_blocker_count",
                        "Mesh control blocker count",
                        unit="blockers",
                    )
                )
            if mesh_profile.apk_asset_evidence:
                features.append(
                    _diagnostic(
                        "mesh_apk_asset_evidence_count",
                        "Mesh APK asset evidence count",
                        unit="assets",
                    )
                )
            if mesh_profile.package_asset_count:
                features.append(
                    _diagnostic(
                        "mesh_apk_package_asset_count",
                        "Mesh APK package asset count",
                        unit="assets",
                    )
                )
            if mesh_profile.apk_string_evidence:
                features.append(
                    _diagnostic(
                        "mesh_apk_string_evidence_count",
                        "Mesh APK string evidence count",
                        unit="strings",
                    )
                )
            if model.family is ProtocolFamily.ZENGGE_MESH:
                features.extend(
                    (
                        _diagnostic(
                            "mesh_known_node_count",
                            "Mesh known node count",
                            unit="nodes",
                        ),
                        _diagnostic(
                            "mesh_command_node_count",
                            "Mesh command node count",
                            unit="nodes",
                        ),
                        _diagnostic(
                            "mesh_strip_node_count",
                            "Mesh strip node count",
                            unit="nodes",
                        ),
                        _diagnostic(
                            "mesh_bulb_node_count",
                            "Mesh bulb node count",
                            unit="nodes",
                        ),
                        _diagnostic(
                            "mesh_panel_node_count",
                            "Mesh panel node count",
                            unit="nodes",
                        ),
                        _diagnostic(
                            "mesh_bridge_seen",
                            "Mesh bridge seen",
                        ),
                    )
                )

    if cloud_profile_for_model(model) is not None:
        features.extend(
            (
                _diagnostic("cloud_profile", "Cloud profile"),
                _diagnostic(
                    "cloud_base_url_count",
                    "Cloud base URL count",
                    unit="hosts",
                ),
                _diagnostic(
                    "cloud_endpoint_count",
                    "Cloud endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_endpoint_inventory_count",
                    "Cloud endpoint inventory count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_endpoint_group_count",
                    "Cloud endpoint group count",
                    unit="groups",
                ),
                _diagnostic(
                    "cloud_command_related_endpoint_count",
                    "Cloud command-related endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_unresolved_base_url_endpoint_count",
                    "Cloud unresolved base URL endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_unproven_auth_endpoint_count",
                    "Cloud unproven auth endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_auth_endpoint_count",
                    "Cloud auth endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_account_auth_endpoint_count",
                    "Cloud account auth endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_device_endpoint_count",
                    "Cloud device endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_home_device_endpoint_count",
                    "Cloud home device endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_user_device_endpoint_count",
                    "Cloud user device endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_local_device_endpoint_count",
                    "Cloud local device endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_btmesh_endpoint_count",
                    "Cloud BT mesh endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_root_device_endpoint_count",
                    "Cloud root device endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_raw_command_endpoint_count",
                    "Cloud raw command endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_content_endpoint_count",
                    "Cloud content endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_voice_endpoint_count",
                    "Cloud voice endpoint count",
                    unit="endpoints",
                ),
                _diagnostic(
                    "cloud_document_url_count",
                    "Cloud document URL count",
                    unit="urls",
                ),
                _diagnostic(
                    "cloud_auth_token_hint_count",
                    "Cloud auth token hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "cloud_device_identity_hint_count",
                    "Cloud device identity hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "cloud_http_header_hint_count",
                    "Cloud HTTP header hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "cloud_signature_hint_count",
                    "Cloud signature hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "cloud_request_contract_hint_count",
                    "Cloud request contract hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "cloud_token_contract_hint_count",
                    "Cloud token contract hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "cloud_header_contract_hint_count",
                    "Cloud header contract hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "cloud_signature_contract_hint_count",
                    "Cloud signature contract hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "cloud_transport_hint_count",
                    "Cloud transport hint count",
                    unit="hints",
                ),
                _diagnostic(
                    "cloud_protocol_gap_count",
                    "Cloud protocol gap count",
                    unit="gaps",
                ),
                _diagnostic(
                    "cloud_command_blocker_count",
                    "Cloud command blocker count",
                    unit="blockers",
                ),
                _diagnostic(
                    "cloud_raw_command_endpoint",
                    "Cloud raw command endpoint",
                ),
            )
        )

    if "supportGetNetInfo" in model.features:
        features.append(_diagnostic("network_info", "Network information"))

    if "maxDataLength" in model.features:
        features.append(
            _diagnostic(
                "max_data_length",
                "Maximum data length",
                unit="bytes",
            )
        )

    if isinstance(model.features.get("maxPixelChannels"), int):
        features.append(
            _diagnostic(
                "max_pixel_channels",
                "Maximum pixel channels",
                unit="px",
            )
        )

    if banlanx6xx_style_family(model.family):
        features.append(_diagnostic("custom_effect_slot", "Custom effect slot"))

    if model.family in {
        ProtocolFamily.BANLANX_601,
        ProtocolFamily.BANLANX_60X,
        ProtocolFamily.BANLANX_V2,
    }:
        features.append(_diagnostic("timer_count", "Timer count"))

    if model.family is ProtocolFamily.BANLANX_V3:
        features.extend(
            (
                _diagnostic("diy_effect_type", "DIY effect type"),
                _diagnostic("diy_color_count", "DIY color count"),
            )
        )

    if _has_refresh_button(model):
        features.append(
            FeatureSpec(
                key="refresh",
                platform=PlatformKind.BUTTON,
                name="Refresh",
                entity_category=EntityCategoryKind.DIAGNOSTIC,
                enabled_by_default=True,
                implemented=True,
            )
        )

    if protocol_evidence_profile_for_model(model) is not None:
        features.append(_diagnostic("effect_type", "Effect type"))

    if model.color_cap > 0:
        features.append(
            FeatureSpec(
                key="main_light",
                platform=PlatformKind.LIGHT,
                name="Light",
                enabled_by_default=False,
                implemented=False,
                color_modes=_color_modes(model.color_cap),
                implementation_hint=_implementation_hint(model),
            )
        )
        features.extend(_legacy_output_light_features(model))
        features.extend(_lighting_controls(model))

    features.extend(_catalog_config_features(model))
    features.extend(_family_features(model))

    return EntityPlan(model=model, features=tuple(features))


def _has_refresh_button(model: CatalogModel) -> bool:
    return model.family in {
        ProtocolFamily.BANLANX_601,
        ProtocolFamily.BANLANX_60X,
        ProtocolFamily.BANLANX_V2,
        ProtocolFamily.BANLANX_V3,
        ProtocolFamily.BANLANX_6XX,
        ProtocolFamily.BANLANX_CUSTOM_5XX,
        ProtocolFamily.LEGACY_LED_CHORD,
        ProtocolFamily.LEGACY_LED_HUE,
        ProtocolFamily.ZENGGE_MESH,
    }


def _diagnostic(
    key: str,
    name: str,
    *,
    unit: str | None = None,
    implementation_hint: str | None = None,
) -> FeatureSpec:
    return FeatureSpec(
        key=key,
        platform=PlatformKind.SENSOR,
        name=name,
        entity_category=EntityCategoryKind.DIAGNOSTIC,
        enabled_by_default=True,
        implemented=True,
        unit=unit,
        implementation_hint=implementation_hint,
    )


def _planned_config_number(
    key: str,
    name: str,
    *,
    minimum: int,
    maximum: int,
    step: int = 1,
    unit: str | None = None,
    channel: int = 0,
) -> FeatureSpec:
    return FeatureSpec(
        key=key,
        platform=PlatformKind.NUMBER,
        name=name,
        channel=channel,
        entity_category=EntityCategoryKind.CONFIG,
        enabled_by_default=False,
        implemented=False,
        minimum=minimum,
        maximum=maximum,
        step=step,
        unit=unit,
    )


def _planned_select(
    key: str,
    name: str,
    *,
    options: tuple[str, ...] = (),
    category: EntityCategoryKind | None = None,
    channel: int = 0,
) -> FeatureSpec:
    return FeatureSpec(
        key=key,
        platform=PlatformKind.SELECT,
        name=name,
        channel=channel,
        entity_category=category,
        enabled_by_default=False,
        implemented=False,
        options=options,
    )


def _color_modes(color_cap: int) -> tuple[str, ...]:
    return {
        1: ("rgb",),
        2: ("rgbw_or_cct",),
        4: ("addressable_rgb",),
        8: ("addressable_rgbw",),
    }.get(color_cap, ("unknown",))


def _implementation_hint(model: CatalogModel) -> str | None:
    if model.legacy_uniled_supported:
        return "legacy_uniled"
    return None


def _legacy_output_light_features(model: CatalogModel) -> tuple[FeatureSpec, ...]:
    output_count = _legacy_output_channels(model)
    if output_count == 0:
        return ()
    return tuple(
        FeatureSpec(
            key=f"output_{channel}_light",
            platform=PlatformKind.LIGHT,
            name=f"Output {channel}",
            channel=channel,
            enabled_by_default=False,
            implemented=False,
            color_modes=_color_modes(model.color_cap),
            implementation_hint="legacy_uniled_output",
        )
        for channel in range(1, output_count + 1)
    )


def _legacy_output_channels(model: CatalogModel) -> int:
    if model.family is ProtocolFamily.BANLANX_601:
        return 2
    if model.family is ProtocolFamily.BANLANX_60X:
        if model.name == "SP602E":
            return 4
        return 8
    return 0


def _lighting_controls(model: CatalogModel) -> tuple[FeatureSpec, ...]:
    if model.family in {ProtocolFamily.BANLANX_601, ProtocolFamily.BANLANX_60X}:
        return _legacy_output_controls(model)
    if model.family is ProtocolFamily.LEGACY_LED_CHORD:
        return (
            _planned_select(
                "effect",
                "Effect",
                options=select_options_for_model(model, "effect"),
            ),
            _planned_select(
                "light_mode",
                "Light mode",
                options=select_options_for_model(model, "light_mode"),
            ),
            _planned_select(
                "chip_order",
                "Chip order",
                options=select_options_for_model(model, "chip_order"),
                category=EntityCategoryKind.CONFIG,
            ),
            _planned_select(
                "chip_type",
                "Chip type",
                options=select_options_for_model(model, "chip_type"),
                category=EntityCategoryKind.CONFIG,
            ),
            _planned_config_number(
                "segment_count",
                "Segment count",
                minimum=1,
                maximum=64,
            ),
            _planned_config_number(
                "segment_pixels",
                "Segment pixels",
                minimum=1,
                maximum=150,
                unit="px",
            ),
            _planned_config_number(
                "effect_speed",
                "Effect speed",
                minimum=1,
                maximum=186,
            ),
            _planned_config_number(
                "audio_sensitivity",
                "Audio sensitivity",
                minimum=1,
                maximum=165,
            ),
        )
    if model.family is ProtocolFamily.LEGACY_LED_HUE:
        return (
            _planned_select(
                "effect",
                "Effect",
                options=select_options_for_model(model, "effect"),
            ),
            _planned_select(
                "chip_order",
                "Chip order",
                options=select_options_for_model(model, "chip_order"),
                category=EntityCategoryKind.CONFIG,
            ),
            _planned_select(
                "chip_type",
                "Chip type",
                options=select_options_for_model(model, "chip_type"),
                category=EntityCategoryKind.CONFIG,
            ),
            _planned_config_number(
                "segment_pixels",
                "Segment pixels",
                minimum=1,
                maximum=1024,
                unit="px",
            ),
            _planned_config_number(
                "effect_speed",
                "Effect speed",
                minimum=1,
                maximum=186,
            ),
            _planned_switch("effect_loop", "Effect loop"),
        )

    controls = [
        _planned_config_number("effect_speed", "Effect speed", minimum=1, maximum=10),
    ]

    effect_options = select_options_for_model(model, "effect")
    controls.insert(
        0,
        _planned_select(
            "effect",
            "Effect",
            options=effect_options,
        ),
    )

    light_mode_options = select_options_for_model(model, "light_mode")
    if _model_has_light_mode_control(model):
        controls.append(
            _planned_select(
                "light_mode",
                "Light mode",
                options=light_mode_options,
            )
        )

    if model.family in {
        ProtocolFamily.BANLANX_601,
        ProtocolFamily.BANLANX_60X,
        ProtocolFamily.BANLANX_V2,
        ProtocolFamily.BANLANX_V3,
    }:
        controls.append(
            _planned_select(
                "chip_order",
                "Chip order",
                options=select_options_for_model(model, "chip_order"),
                category=EntityCategoryKind.CONFIG,
            )
        )

    length_max = _effect_length_max(model.family)
    if length_max is not None:
        controls.append(
            _planned_config_number(
                "effect_length",
                "Effect length",
                minimum=1,
                maximum=length_max,
            )
        )

    if model.family in {
        ProtocolFamily.BANLANX_601,
        ProtocolFamily.BANLANX_60X,
        ProtocolFamily.BANLANX_6XX,
        ProtocolFamily.BANLANX_CUSTOM_5XX,
    }:
        controls.append(_planned_switch("effect_direction", "Effect direction"))

    if _model_has_effect_loop_control(model):
        controls.append(_planned_switch("effect_loop", "Effect loop"))

    if banlanx6xx_style_family(model.family):
        light_type_options = select_options_for_model(model, "light_type")
        chip_order_options = select_options_for_model(model, "chip_order")
        controls.extend(
            [
                _planned_select(
                    "onoff_effect",
                    "On/off effect",
                    options=select_options_for_model(model, "onoff_effect"),
                ),
                _planned_select(
                    "onoff_speed",
                    "On/off speed",
                    options=select_options_for_model(model, "onoff_speed"),
                ),
                _planned_config_number(
                    "onoff_pixels",
                    "On/off pixels",
                    minimum=1,
                    maximum=600,
                    unit="px",
                ),
                _planned_select(
                    "on_power",
                    "On power",
                    options=select_options_for_model(model, "on_power"),
                ),
                _planned_switch("effect_play", "Effect play"),
            ]
        )
        if banlanx6xx_model_has_light_type_select(model.name):
            controls.append(
                _planned_select(
                    "light_type",
                    "Light type",
                    options=light_type_options,
                    category=EntityCategoryKind.CONFIG,
                )
            )
        if chip_order_options or banlanx6xx_model_has_dynamic_light_type(model.name):
            controls.append(
                _planned_select(
                    "chip_order",
                    "Chip order",
                    options=chip_order_options,
                    category=EntityCategoryKind.CONFIG,
                )
            )
        if banlanx6xx_model_has_coexistence(
            model.name
        ) or banlanx6xx_model_has_dynamic_light_type(model.name):
            controls.append(_planned_switch("coexistence", "Coexistence"))

    return tuple(controls)


def _legacy_output_controls(model: CatalogModel) -> tuple[FeatureSpec, ...]:
    controls: list[FeatureSpec] = []
    effect_options = select_options_for_model(model, "effect")
    chip_order_options = select_options_for_model(model, "chip_order")
    length_max = _effect_length_max(model.family)

    for channel in range(1, _legacy_output_channels(model) + 1):
        controls.extend(
            [
                _planned_select(
                    "effect",
                    f"Output {channel} effect",
                    options=effect_options,
                    channel=channel,
                ),
                _planned_config_number(
                    "effect_speed",
                    f"Output {channel} effect speed",
                    minimum=1,
                    maximum=10,
                    channel=channel,
                ),
                _planned_switch(
                    "effect_direction",
                    f"Output {channel} effect direction",
                    channel=channel,
                ),
                _planned_select(
                    "chip_order",
                    f"Output {channel} chip order",
                    options=chip_order_options,
                    category=EntityCategoryKind.CONFIG,
                    channel=channel,
                ),
            ]
        )
        if length_max is not None:
            controls.append(
                _planned_config_number(
                    "effect_length",
                    f"Output {channel} effect length",
                    minimum=1,
                    maximum=length_max,
                    channel=channel,
                )
            )
        if model.family is ProtocolFamily.BANLANX_601:
            controls.append(
                _planned_config_number(
                    "audio_sensitivity",
                    f"Output {channel} audio sensitivity",
                    minimum=1,
                    maximum=16,
                    channel=channel,
                )
            )

    controls.append(_planned_switch("scene_loop", "Scene loop"))
    return tuple(controls)


def _planned_switch(key: str, name: str, *, channel: int = 0) -> FeatureSpec:
    return FeatureSpec(
        key=key,
        platform=PlatformKind.SWITCH,
        name=name,
        channel=channel,
        enabled_by_default=False,
        implemented=False,
    )


def _effect_length_max(family: ProtocolFamily) -> int | None:
    return {
        ProtocolFamily.BANLANX_601: 150,
        ProtocolFamily.BANLANX_60X: 240,
        ProtocolFamily.BANLANX_V2: 150,
        ProtocolFamily.BANLANX_6XX: 150,
        ProtocolFamily.BANLANX_CUSTOM_5XX: 240,
        ProtocolFamily.BANLANX_SCENE_UI: 240,
        ProtocolFamily.BANLANX_SCENE_MESH: 240,
    }.get(family)


def _catalog_config_features(model: CatalogModel) -> tuple[FeatureSpec, ...]:
    features: list[FeatureSpec] = []

    max_pixels = model.features.get("maxPixelChannels")
    if isinstance(max_pixels, int):
        features.append(
            _planned_config_number(
                "pixel_count",
                "Pixel count",
                minimum=1,
                maximum=max_pixels,
                unit="px",
            )
        )
        features.extend(
            [
                _planned_select(
                    "chip_type",
                    "Chip type",
                    category=EntityCategoryKind.CONFIG,
                ),
                _planned_select(
                    "color_order",
                    "Color order",
                    options=("RGB", "RBG", "GRB", "GBR", "BRG", "BGR"),
                    category=EntityCategoryKind.CONFIG,
                ),
            ]
        )

    if model.family is ProtocolFamily.BANLANX_60X:
        features.append(
            _planned_config_number(
                "audio_sensitivity",
                "Audio sensitivity",
                minimum=1,
                maximum=16,
            )
        )
    elif (
        model.family is not ProtocolFamily.BANLANX_601
        and (
            model.features.get("musicFeature")
            or _model_has_audio_controls(model)
        )
    ):
        audio_options = select_options_for_model(model, "audio_input")
        features.extend(
            [
                _planned_select(
                    "audio_input",
                    "Audio input",
                    options=audio_options,
                ),
                _planned_config_number(
                    "audio_sensitivity",
                    "Audio sensitivity",
                    minimum=1,
                    maximum=16,
                ),
            ]
        )

    if model.features.get("settingFeature") and not banlanx6xx_style_family(
        model.family
    ):
        features.append(
            _planned_select(
                "light_type",
                "Light type",
                category=EntityCategoryKind.CONFIG,
            )
        )

    return tuple(features)


def _family_has_audio_controls(family: ProtocolFamily) -> bool:
    return family in {
        ProtocolFamily.BANLANX_601,
        ProtocolFamily.BANLANX_60X,
        ProtocolFamily.BANLANX_6XX,
        ProtocolFamily.BANLANX_CUSTOM_5XX,
    }


def _model_has_audio_controls(model: CatalogModel) -> bool:
    if model.family in {ProtocolFamily.BANLANX_V2, ProtocolFamily.BANLANX_V3}:
        return legacy_v23_model_has_audio_controls(
            model.family,
            model_name=model.name,
            spec_functions=model.spec_functions,
        )
    return _family_has_audio_controls(model.family)


def _model_has_light_mode_control(model: CatalogModel) -> bool:
    if model.family in {ProtocolFamily.BANLANX_V2, ProtocolFamily.BANLANX_V3}:
        return _model_has_audio_controls(model)
    if banlanx6xx_style_family(model.family):
        return bool(select_options_for_model(model, "light_mode")) or (
            banlanx6xx_model_has_dynamic_light_type(model.name)
        )
    return bool(select_options_for_model(model, "light_mode"))


def _model_has_effect_loop_control(model: CatalogModel) -> bool:
    if model.family in {ProtocolFamily.BANLANX_V2, ProtocolFamily.BANLANX_V3}:
        return not _model_has_audio_controls(model)
    return model.family in {
        ProtocolFamily.BANLANX_6XX,
        ProtocolFamily.BANLANX_CUSTOM_5XX,
    }


def _family_features(model: CatalogModel) -> tuple[FeatureSpec, ...]:
    if model.family in {ProtocolFamily.BANLANX_601, ProtocolFamily.BANLANX_60X}:
        return tuple(
            FeatureSpec(
                key=f"scene_{scene_id}",
                platform=PlatformKind.SCENE,
                name=f"Scene {scene_id + 1}",
                channel=scene_id,
                enabled_by_default=False,
                implemented=False,
                implementation_hint="legacy_uniled",
            )
            for scene_id in range(9)
        )

    if model.family in {
        ProtocolFamily.BANLANX_SCENE_UI,
        ProtocolFamily.BANLANX_SCENE_MESH,
    }:
        profile = scene_profile_for_model(model)
        return (
            _diagnostic("scene_profile", "Scene profile"),
            _diagnostic(
                "scene_preset_count",
                "Scene preset count",
                unit="presets",
            ),
            _diagnostic(
                "scene_control_surface_count",
                "Scene control surface count",
                unit="surfaces",
            ),
            _diagnostic(
                "scene_route_count",
                "Scene route count",
                unit="routes",
            ),
            _diagnostic(
                "scene_mode_icon_count",
                "Scene mode icon count",
                unit="icons",
            ),
            _diagnostic(
                "scene_mode_effect_count",
                "Scene mode effect count",
                unit="effects",
            ),
            _diagnostic(
                "scene_mode_icon_sample_count",
                "Scene mode icon sample count",
                unit="samples",
            ),
            _diagnostic(
                "scene_lfx_route_count",
                "Scene LFX route count",
                unit="routes",
            ),
            _diagnostic(
                "scene_timer_route_count",
                "Scene timer route count",
                unit="routes",
            ),
            _diagnostic(
                "scene_app_method_count",
                "Scene app method count",
                unit="methods",
            ),
            _diagnostic(
                "scene_app_command_id_count",
                "Scene app command ID count",
                unit="ids",
            ),
            _diagnostic(
                "scene_storage_hint_count",
                "Scene storage hint count",
                unit="hints",
            ),
            _diagnostic(
                "scene_recent_action_count",
                "Scene recent action count",
                unit="actions",
            ),
            _diagnostic(
                "scene_favorite_action_count",
                "Scene favorite action count",
                unit="actions",
            ),
            _diagnostic(
                "scene_timer_action_count",
                "Scene timer action count",
                unit="actions",
            ),
            _diagnostic(
                "scene_diy_action_count",
                "Scene DIY action count",
                unit="actions",
            ),
            _diagnostic(
                "scene_white_brightness_anchor_count",
                "Scene white-brightness anchor count",
                unit="anchors",
            ),
            _diagnostic(
                "scene_raw_string_hint_count",
                "Scene raw string hint count",
                unit="strings",
            ),
            _diagnostic(
                "scene_lfx_data_model_hint_count",
                "Scene LFX data-model hint count",
                unit="hints",
            ),
            _diagnostic(
                "scene_lfx_frame_field_hint_count",
                "Scene LFX frame-field hint count",
                unit="fields",
            ),
            _diagnostic(
                "scene_native_handler_count",
                "Scene native handler count",
                unit="handlers",
            ),
            _diagnostic(
                "scene_native_paired_api_count",
                "Scene native paired API count",
                unit="capabilities",
            ),
            _diagnostic(
                "scene_native_ic_only_api_count",
                "Scene native IC-only API count",
                unit="capabilities",
            ),
            _diagnostic(
                "scene_native_loop_handler_count",
                "Scene native loop handler count",
                unit="handlers",
            ),
            _diagnostic(
                "scene_native_library_hint_count",
                "Scene native library hint count",
                unit="hints",
            ),
            _diagnostic(
                "scene_native_frame_hint_count",
                "Scene native frame helper count",
                unit="helpers",
            ),
            _diagnostic(
                "scene_native_opcode_hint_count",
                "Scene native opcode helper count",
                unit="helpers",
            ),
            _diagnostic(
                "scene_native_state_hint_count",
                "Scene native state helper count",
                unit="helpers",
            ),
            _diagnostic(
                "scene_native_state_export_count",
                "Scene native state export count",
                unit="helpers",
            ),
            _diagnostic(
                "scene_native_color_order_hint_count",
                "Scene native color order hint count",
                unit="hints",
            ),
            _diagnostic(
                "scene_native_pwm_table_hint_count",
                "Scene native PWM table hint count",
                unit="tables",
            ),
            _diagnostic(
                "scene_native_music_effect_hint_count",
                "Scene native music effect hint count",
                unit="effects",
            ),
            _diagnostic(
                "scene_native_pwm_driver_hint_count",
                "Scene native PWM driver hint count",
                unit="helpers",
            ),
            _diagnostic(
                "scene_native_animation_export_count",
                "Scene native animation export count",
                unit="exports",
            ),
            _diagnostic(
                "scene_native_drive_export_count",
                "Scene native drive export count",
                unit="exports",
            ),
            _diagnostic(
                "scene_native_persistence_handler_count",
                "Scene native persistence handler count",
                unit="handlers",
            ),
            _diagnostic(
                "scene_native_persistence_export_count",
                "Scene native persistence export count",
                unit="exports",
            ),
            _diagnostic(
                "scene_native_persistence_capability_count",
                "Scene native persistence capability count",
                unit="capabilities",
            ),
            _diagnostic(
                "scene_native_export_hint_count",
                "Scene native export hint count",
                unit="hints",
            ),
            _diagnostic(
                "scene_native_code_anchor_count",
                "Scene native code anchor count",
                unit="anchors",
            ),
            _diagnostic(
                "scene_setup_requirement_count",
                "Scene setup requirement count",
                unit="requirements",
            ),
            _diagnostic(
                "scene_catalog_hint_count",
                "Scene catalog hint count",
                unit="hints",
            ),
            _diagnostic(
                "scene_transport_hint_count",
                "Scene transport hint count",
                unit="hints",
            ),
            _diagnostic(
                "scene_protocol_gap_count",
                "Scene protocol gap count",
                unit="gaps",
            ),
            _diagnostic(
                "scene_command_blocker_count",
                "Scene command blocker count",
                unit="blockers",
            ),
            _diagnostic(
                "scene_apk_asset_evidence_count",
                "Scene APK asset evidence count",
                unit="assets",
            ),
            _diagnostic(
                "scene_apk_package_asset_count",
                "Scene APK package asset count",
                unit="assets",
            ),
            _diagnostic(
                "scene_apk_string_evidence_count",
                "Scene APK string evidence count",
                unit="strings",
            ),
            _planned_select("scene_slot", "Scene slot"),
            _planned_select(
                "scene_preset",
                "Scene preset",
                options=() if profile is None else profile.presets,
            ),
            _planned_select(
                "scene_mode_effect",
                "Scene mode effect",
                options=() if profile is None else profile.mode_effects,
            ),
            _planned_select(
                "scene_surface",
                "Scene surface",
                options=() if profile is None else profile.control_surfaces,
            ),
            _planned_select(
                "scene_recent_action",
                "Scene recent action",
                options=() if profile is None else profile.recent_actions,
            ),
            _planned_select(
                "scene_favorite_action",
                "Scene favorite action",
                options=() if profile is None else profile.favorite_actions,
            ),
            _planned_select(
                "scene_timer_action",
                "Scene timer action",
                options=() if profile is None else profile.timer_actions,
            ),
            _planned_select(
                "scene_diy_action",
                "Scene DIY action",
                options=() if profile is None else profile.diy_actions,
            ),
            _planned_select(
                "scene_white_brightness_anchor",
                "Scene white-brightness anchor",
                options=() if profile is None else profile.white_brightness_anchors,
            ),
            FeatureSpec(
                key="saved_scene",
                platform=PlatformKind.SCENE,
                name="Saved scene",
                enabled_by_default=False,
                implemented=False,
            ),
        )

    profile = sp630e_profile_for_model(model)
    if profile is not None:
        return (
            _diagnostic("sp630e_profile", "SP630E surface profile"),
            _diagnostic(
                "sp630e_route_count",
                "SP630E route count",
                unit="routes",
            ),
            _diagnostic(
                "sp630e_control_surface_count",
                "SP630E control surface count",
                unit="surfaces",
            ),
            _diagnostic(
                "sp630e_favorite_limit_hint_count",
                "SP630E favorite limit hint count",
                unit="hints",
            ),
            _diagnostic(
                "sp630e_timer_limit",
                "SP630E timer limit",
                unit="slots",
            ),
            _diagnostic(
                "sp630e_timer_hint_count",
                "SP630E timer hint count",
                unit="hints",
            ),
            _diagnostic(
                "sp630e_music_asset_count",
                "SP630E music asset count",
                unit="assets",
            ),
            _diagnostic(
                "sp630e_network_hint_count",
                "SP630E network hint count",
                unit="hints",
            ),
            _diagnostic(
                "sp630e_remote_hint_count",
                "SP630E remote hint count",
                unit="hints",
            ),
            _diagnostic(
                "sp630e_motor_hint_count",
                "SP630E motor hint count",
                unit="hints",
            ),
            _diagnostic(
                "sp630e_app_method_count",
                "SP630E app method count",
                unit="methods",
            ),
            _diagnostic(
                "sp630e_app_command_id_count",
                "SP630E app command ID count",
                unit="ids",
            ),
            _diagnostic(
                "sp630e_data_model_hint_count",
                "SP630E data-model hint count",
                unit="hints",
            ),
            _diagnostic(
                "sp630e_native_lfx_hint_count",
                "SP630E native LFX hint count",
                unit="hints",
            ),
            _diagnostic(
                "sp630e_native_export_detail_count",
                "SP630E native export detail count",
                unit="anchors",
            ),
            _diagnostic(
                "sp630e_catalog_hint_count",
                "SP630E catalog hint count",
                unit="hints",
            ),
            _diagnostic(
                "sp630e_protocol_gap_count",
                "SP630E protocol gap count",
                unit="gaps",
            ),
            _diagnostic(
                "sp630e_apk_asset_evidence_count",
                "SP630E APK asset evidence count",
                unit="assets",
            ),
            _diagnostic(
                "sp630e_apk_package_asset_count",
                "SP630E APK package asset count",
                unit="assets",
            ),
            _diagnostic(
                "sp630e_apk_string_evidence_count",
                "SP630E APK string evidence count",
                unit="strings",
            ),
            _planned_select(
                "sp630e_control_surface",
                "SP630E control surface",
                options=profile.control_surfaces,
            ),
        )

    profile = car_light_profile_for_model(model)
    if profile is not None:
        return (
            _diagnostic("car_light_profile", "Car light profile"),
            _diagnostic("accessory_role", "Accessory role"),
            _diagnostic(
                "car_light_required_controller",
                "Car light required controller",
            ),
            _diagnostic(
                "car_light_setup_stage",
                "Car light setup stage",
            ),
            _diagnostic(
                "car_light_setup_order",
                "Car light setup order",
            ),
            _diagnostic(
                "car_light_setup_dependency",
                "Car light setup dependency",
            ),
            _diagnostic(
                "car_light_setup_dependency_count",
                "Car light setup dependency count",
                unit="dependencies",
            ),
            _diagnostic(
                "car_light_required_setup_dependency_count",
                "Car light required setup dependency count",
                unit="dependencies",
            ),
            _diagnostic(
                "car_light_ordered_setup_model_count",
                "Car light ordered setup model count",
                unit="models",
            ),
            _diagnostic(
                "car_light_zone_count",
                "Car light zone count",
                unit="zones",
            ),
            _diagnostic(
                "car_light_trigger_count",
                "Car light trigger count",
                unit="triggers",
            ),
            _diagnostic(
                "car_light_control_surface_count",
                "Car light control surface count",
                unit="surfaces",
            ),
            _diagnostic(
                "car_light_accessory_asset_count",
                "Car light accessory asset count",
                unit="assets",
            ),
            _diagnostic(
                "car_light_animation_asset_count",
                "Car light animation asset count",
                unit="assets",
            ),
            _diagnostic(
                "car_light_trigger_image_asset_count",
                "Car light trigger image asset count",
                unit="assets",
            ),
            _diagnostic(
                "car_light_zone_image_asset_count",
                "Car light zone image asset count",
                unit="assets",
            ),
            _diagnostic(
                "car_light_subdevice_hint_count",
                "Car light subdevice hint count",
                unit="hints",
            ),
            _diagnostic(
                "car_light_subdevice_filter_count",
                "Car light subdevice filter count",
                unit="filters",
            ),
            _diagnostic(
                "car_light_password_hint_count",
                "Car light password hint count",
                unit="hints",
            ),
            _diagnostic(
                "car_light_password_flow_state_count",
                "Car light password flow state count",
                unit="states",
            ),
            _diagnostic(
                "car_light_password_entry_hint_count",
                "Car light password entry hint count",
                unit="hints",
            ),
            _diagnostic(
                "car_light_password_policy_hint_count",
                "Car light password policy hint count",
                unit="hints",
            ),
            _diagnostic(
                "car_light_password_reset_hint_count",
                "Car light password reset hint count",
                unit="hints",
            ),
            _diagnostic(
                "car_light_trigger_storage_hint_count",
                "Car light trigger storage hint count",
                unit="hints",
            ),
            _diagnostic(
                "car_light_trigger_action_count",
                "Car light trigger action count",
                unit="actions",
            ),
            _diagnostic(
                "car_light_route_count",
                "Car light route count",
                unit="routes",
            ),
            _diagnostic(
                "car_light_setup_requirement_count",
                "Car light setup requirement count",
                unit="requirements",
            ),
            _diagnostic(
                "car_light_setup_flow_hint_count",
                "Car light setup flow hint count",
                unit="hints",
            ),
            _diagnostic(
                "car_light_setup_key_hint_count",
                "Car light setup key hint count",
                unit="hints",
            ),
            _diagnostic(
                "car_light_app_command_id_count",
                "Car light app command ID count",
                unit="ids",
            ),
            _diagnostic(
                "car_light_model_role_hint_count",
                "Car light model role hint count",
                unit="hints",
            ),
            _diagnostic(
                "car_light_protocol_gap_count",
                "Car light protocol gap count",
                unit="gaps",
            ),
            _diagnostic(
                "car_light_command_blocker_count",
                "Car light command blocker count",
                unit="blockers",
            ),
            _diagnostic(
                "car_light_apk_asset_evidence_count",
                "Car light APK asset evidence count",
                unit="assets",
            ),
            _diagnostic(
                "car_light_apk_package_asset_count",
                "Car light APK package asset count",
                unit="assets",
            ),
            _diagnostic(
                "car_light_apk_string_evidence_count",
                "Car light APK string evidence count",
                unit="strings",
            ),
            _planned_select(
                "car_light_zone",
                "Car light zone",
                options=profile.zones,
            ),
            _planned_select(
                "car_light_trigger",
                "Car light trigger",
                options=profile.triggers,
            ),
            _planned_select(
                "car_light_control_surface",
                "Car light control surface",
                options=profile.control_surfaces,
            ),
            _planned_select(
                "car_light_subdevice_filter",
                "Car light subdevice filter",
                options=profile.subdevice_filters,
            ),
            _planned_select(
                "car_light_password_flow_state",
                "Car light password flow state",
                options=profile.password_flow_states,
            ),
            _planned_select(
                "car_light_trigger_action",
                "Car light trigger action",
                options=profile.trigger_actions,
            ),
        )

    if model.family is ProtocolFamily.BANLANX_NETWORK:
        profile = network_profile_for_model(model)
        features = [
            _diagnostic("network_profile", "Network controller profile"),
            _diagnostic(
                "network_surface_count",
                "Network surface count",
                unit="surfaces",
            ),
            _diagnostic(
                "network_content_mode_count",
                "Network content mode count",
                unit="modes",
            ),
            _diagnostic(
                "network_artnet_field_count",
                "Network Art-Net field count",
                unit="fields",
            ),
            _diagnostic(
                "network_port_field_count",
                "Network port field count",
                unit="fields",
            ),
            _diagnostic(
                "network_playlist_action_count",
                "Network playlist action count",
                unit="actions",
            ),
            _diagnostic(
                "network_matrix_music_control_count",
                "Network matrix music control count",
                unit="controls",
            ),
            _diagnostic(
                "network_lfx_effect_count",
                "Network LFX effect count",
                unit="effects",
            ),
            _diagnostic(
                "network_lfx_gif_count",
                "Network LFX GIF count",
                unit="previews",
            ),
            _diagnostic(
                "network_route_count",
                "Network route count",
                unit="routes",
            ),
            _diagnostic(
                "network_regular_lfx_effect_asset_count",
                "Network regular LFX effect asset count",
                unit="assets",
            ),
            _diagnostic(
                "network_lfx_gif_asset_count",
                "Network LFX GIF asset count",
                unit="assets",
            ),
            _diagnostic(
                "network_app_method_count",
                "Network app method count",
                unit="methods",
            ),
            _diagnostic(
                "network_app_command_id_count",
                "Network app command ID count",
                unit="ids",
            ),
            _diagnostic(
                "network_workflow_hint_count",
                "Network workflow hint count",
                unit="workflows",
            ),
            _diagnostic(
                "network_raw_string_hint_count",
                "Network raw string hint count",
                unit="strings",
            ),
            _diagnostic(
                "network_import_constraint_count",
                "Network import constraint count",
                unit="constraints",
            ),
            _diagnostic(
                "network_catalog_hint_count",
                "Network catalog hint count",
                unit="hints",
            ),
            _diagnostic(
                "network_transport_hint_count",
                "Network transport hint count",
                unit="hints",
            ),
            _diagnostic(
                "network_native_library_hint_count",
                "Network native library hint count",
                unit="hints",
            ),
            _diagnostic(
                "network_native_frame_hint_count",
                "Network native frame helper count",
                unit="hints",
            ),
            _diagnostic(
                "network_native_lfx_param_hint_count",
                "Network native LFX parameter hint count",
                unit="hints",
            ),
            _diagnostic(
                "network_native_effect_generator_hint_count",
                "Network native effect generator hint count",
                unit="generators",
            ),
            _diagnostic(
                "network_native_matrix_mode_hint_count",
                "Network native matrix mode hint count",
                unit="hints",
            ),
            _diagnostic(
                "network_native_pixel_helper_hint_count",
                "Network native pixel helper hint count",
                unit="helpers",
            ),
            _diagnostic(
                "network_native_export_hint_count",
                "Network native export hint count",
                unit="hints",
            ),
            _diagnostic(
                "network_native_export_detail_count",
                "Network native export detail count",
                unit="anchors",
            ),
            _diagnostic(
                "network_protocol_gap_count",
                "Network protocol gap count",
                unit="gaps",
            ),
            _diagnostic(
                "network_command_blocker_count",
                "Network command blocker count",
                unit="blockers",
            ),
            _diagnostic(
                "network_apk_asset_evidence_count",
                "Network APK asset evidence count",
                unit="assets",
            ),
            _diagnostic(
                "network_apk_package_asset_count",
                "Network APK package asset count",
                unit="assets",
            ),
            _diagnostic(
                "network_apk_string_evidence_count",
                "Network APK string evidence count",
                unit="strings",
            ),
            _planned_select(
                "network_surface",
                "Network controller surface",
                options=() if profile is None else profile.control_surfaces,
            ),
            _planned_select(
                "network_content_mode",
                "Network content mode",
                options=() if profile is None else profile.content_modes,
            ),
        ]
        if profile is not None and profile.artnet_fields:
            features.append(
                _planned_select(
                    "network_artnet_field",
                    "Network Art-Net field",
                    options=profile.artnet_fields,
                )
            )
        if profile is not None and profile.port_fields:
            features.append(
                _planned_select(
                    "network_port_field",
                    "Network port field",
                    options=profile.port_fields,
                )
            )
        if profile is not None and profile.playlist_actions:
            features.append(
                _planned_select(
                    "network_playlist_action",
                    "Network playlist action",
                    options=profile.playlist_actions,
                )
            )
        if profile is not None and profile.matrix_music_controls:
            features.append(
                _planned_select(
                    "network_matrix_music_control",
                    "Network matrix music control",
                    options=profile.matrix_music_controls,
                )
            )
        if profile is not None and profile.regular_lfx_effects:
            features.append(
                _planned_select(
                    "network_lfx_effect",
                    "Network LFX effect",
                    options=profile.regular_lfx_effects,
                )
            )
        features.append(
            FeatureSpec(
                key="identify",
                platform=PlatformKind.BUTTON,
                name="Identify",
                enabled_by_default=False,
                implemented=False,
            )
        )
        return tuple(features)

    profile = fish_tank_profile_for_model(model)
    if profile is not None:
        return (
            _diagnostic("fish_tank_profile", "Fish-tank profile"),
            _diagnostic(
                "fish_tank_favorite_slot_count",
                "Fish-tank favorite slot count",
                unit="slots",
            ),
            _diagnostic(
                "fish_tank_timer_limit",
                "Fish-tank timer limit",
                unit="slots",
            ),
            _diagnostic(
                "fish_tank_light_channel_count",
                "Fish-tank light channel count",
                unit="channels",
            ),
            _diagnostic(
                "fish_tank_control_surface_count",
                "Fish-tank control surface count",
                unit="surfaces",
            ),
            _diagnostic(
                "fish_tank_route_count",
                "Fish-tank route count",
                unit="routes",
            ),
            _diagnostic(
                "fish_tank_effect_hint_count",
                "Fish-tank effect hint count",
                unit="effects",
            ),
            _diagnostic(
                "fish_tank_effect_string_hint_count",
                "Fish-tank effect string hint count",
                unit="strings",
            ),
            _diagnostic(
                "fish_tank_icon_asset_count",
                "Fish-tank icon asset count",
                unit="assets",
            ),
            _diagnostic(
                "fish_tank_image_asset_count",
                "Fish-tank image asset count",
                unit="assets",
            ),
            _diagnostic(
                "fish_tank_channel_asset_count",
                "Fish-tank channel asset count",
                unit="assets",
            ),
            _diagnostic(
                "fish_tank_timer_asset_count",
                "Fish-tank timer asset count",
                unit="assets",
            ),
            _diagnostic(
                "fish_tank_favorite_asset_count",
                "Fish-tank favorite asset count",
                unit="assets",
            ),
            _diagnostic(
                "fish_tank_effect_asset_count",
                "Fish-tank effect asset count",
                unit="assets",
            ),
            _diagnostic(
                "fish_tank_workflow_hint_count",
                "Fish-tank workflow hint count",
                unit="workflows",
            ),
            _diagnostic(
                "fish_tank_favorite_action_count",
                "Fish-tank favorite action count",
                unit="actions",
            ),
            _diagnostic(
                "fish_tank_favorite_store_hint_count",
                "Fish-tank favorite store hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_favorite_recall_hint_count",
                "Fish-tank favorite recall hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_favorite_clear_hint_count",
                "Fish-tank favorite clear hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_favorite_action_type_count",
                "Fish-tank favorite action type count",
                unit="actions",
            ),
            _diagnostic(
                "fish_tank_favorite_loop_hint_count",
                "Fish-tank favorite loop hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_favorite_loop_action_count",
                "Fish-tank favorite loop action count",
                unit="actions",
            ),
            _diagnostic(
                "fish_tank_firmware_prompt_hint_count",
                "Fish-tank firmware prompt hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_timer_slot_count",
                "Fish-tank timer slot count",
                unit="slots",
            ),
            _diagnostic(
                "fish_tank_timer_action_count",
                "Fish-tank timer action count",
                unit="actions",
            ),
            _diagnostic(
                "fish_tank_timer_hint_count",
                "Fish-tank timer hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_timer_string_hint_count",
                "Fish-tank timer string hint count",
                unit="strings",
            ),
            _diagnostic(
                "fish_tank_app_method_count",
                "Fish-tank app method count",
                unit="methods",
            ),
            _diagnostic(
                "fish_tank_app_command_id_count",
                "Fish-tank app command ID count",
                unit="ids",
            ),
            _diagnostic(
                "fish_tank_data_model_hint_count",
                "Fish-tank data-model hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_favorite_service_hint_count",
                "Fish-tank favorite service hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_favorite_storage_hint_count",
                "Fish-tank favorite storage hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_timer_storage_hint_count",
                "Fish-tank timer storage hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_brightness_state_hint_count",
                "Fish-tank brightness state hint count",
                unit="hints",
            ),
            _diagnostic(
                "fish_tank_raw_string_hint_count",
                "Fish-tank raw string hint count",
                unit="strings",
            ),
            _diagnostic(
                "fish_tank_brightness_string_hint_count",
                "Fish-tank brightness string hint count",
                unit="strings",
            ),
            _diagnostic(
                "fish_tank_protocol_gap_count",
                "Fish-tank protocol gap count",
                unit="gaps",
            ),
            _diagnostic(
                "fish_tank_command_blocker_count",
                "Fish-tank command blocker count",
                unit="blockers",
            ),
            _diagnostic(
                "fish_tank_apk_asset_evidence_count",
                "Fish-tank APK asset evidence count",
                unit="assets",
            ),
            _diagnostic(
                "fish_tank_apk_package_asset_count",
                "Fish-tank APK package asset count",
                unit="assets",
            ),
            _diagnostic(
                "fish_tank_apk_string_evidence_count",
                "Fish-tank APK string evidence count",
                unit="strings",
            ),
            _planned_select(
                "fish_tank_light_channel",
                "Fish-tank light channel",
                options=profile.light_channels,
            ),
            _planned_select(
                "fish_tank_control_surface",
                "Fish-tank control surface",
                options=profile.control_surfaces,
            ),
            _planned_select(
                "fish_tank_effect",
                "Fish-tank effect",
                options=profile.effect_hints,
            ),
            _planned_select(
                "fish_tank_favorite_slot",
                "Fish-tank favorite slot",
                options=profile.favorite_slots,
            ),
            _planned_select(
                "fish_tank_favorite_action",
                "Fish-tank favorite action",
                options=profile.favorite_actions,
            ),
            _planned_select(
                "fish_tank_favorite_loop_action",
                "Fish-tank favorite loop action",
                options=profile.favorite_loop_actions,
            ),
            _planned_select(
                "fish_tank_timer_slot",
                "Fish-tank timer slot",
                options=profile.timer_slots,
            ),
            _planned_select(
                "fish_tank_timer_action",
                "Fish-tank timer action",
                options=profile.timer_actions,
            ),
        )

    if model.family is ProtocolFamily.ZENGGE_MESH:
        return (
            _diagnostic("mesh_role", "Mesh role"),
            FeatureSpec(
                key="remote_event",
                platform=PlatformKind.SENSOR,
                name="Remote event",
                entity_category=EntityCategoryKind.DIAGNOSTIC,
                enabled_by_default=False,
                implemented=False,
            ),
        )

    return ()
