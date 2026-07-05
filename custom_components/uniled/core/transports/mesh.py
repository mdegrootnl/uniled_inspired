"""BLE mesh profile facts from old UniLED and the BanlanX catalog."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..catalog import CatalogModel, ProtocolFamily, TransportKind
from ..scene import SCENE_PACKAGE, SCENE_PACKAGE_ASSET_COUNT

TELINK_SERVICE_UUID = "00010203-0405-0607-0809-0a0b0c0d1910"
TELINK_STATUS_UUID = "00010203-0405-0607-0809-0a0b0c0d1911"
TELINK_COMMAND_UUID = "00010203-0405-0607-0809-0a0b0c0d1912"
TELINK_OTA_UUID = "00010203-0405-0607-0809-0a0b0c0d1913"
TELINK_PAIR_UUID = "00010203-0405-0607-0809-0a0b0c0d1914"
TELINK_MANUFACTURER_ID = 529
ZENGGE_MANUFACTURER_ID = 63517
ZENGGE_DEFAULT_MESH_UUID = 0x0211
SIG_MESH_PROVISIONING_SERVICE_UUID = "00001827-0000-1000-8000-00805f9b34fb"
SIG_MESH_PROXY_SERVICE_UUID = "00001828-0000-1000-8000-00805f9b34fb"
SIG_MESH_PROVISIONING_DATA_IN_UUID = "00002adb-0000-1000-8000-00805f9b34fb"
SIG_MESH_PROVISIONING_DATA_OUT_UUID = "00002adc-0000-1000-8000-00805f9b34fb"
SIG_MESH_PROXY_DATA_IN_UUID = "00002add-0000-1000-8000-00805f9b34fb"
SIG_MESH_PROXY_DATA_OUT_UUID = "00002ade-0000-1000-8000-00805f9b34fb"
SIG_MESH_UUID_HINTS = (
    SIG_MESH_PROVISIONING_SERVICE_UUID,
    SIG_MESH_PROXY_SERVICE_UUID,
    SIG_MESH_PROVISIONING_DATA_IN_UUID,
    SIG_MESH_PROVISIONING_DATA_OUT_UUID,
    SIG_MESH_PROXY_DATA_IN_UUID,
    SIG_MESH_PROXY_DATA_OUT_UUID,
)
APK_SIG_MESH_UUID_STRING_EVIDENCE = (
    "00001827-0000-1000-8000-00805f9b34fb2",
    "00001828-0000-1000-8000-00805f9b34fb2",
    "00002ADB-0000-1000-8000-00805F9B34FB2",
    "00002ADC-0000-1000-8000-00805F9B34FB2",
    "00002ADD-0000-1000-8000-00805F9B34FB2",
    "00002ADE-0000-1000-8000-00805F9B34FB2",
)

ZENGGE_EFFECTS = (
    "Seven Color Cross Fade",
    "Red Gradual Change",
    "Green Gradual Change",
    "Blue Gradual Change",
    "Yellow Gradual Change",
    "Cyan Gradual Change",
    "Purple Gradual Change",
    "White Gradual Change",
    "Red/Green Cross Fade",
    "Red/Blue Cross Fade",
    "Green/Blue Cross Fade",
    "Seven Color Strobe",
    "Red Strobe Flash",
    "Green Strobe Flash",
    "Blue Strobe Flash",
    "Yellow Strobe Flash",
    "Cyan Strobe Flash",
    "Purple Strobe Flash",
    "White Strobe Flash",
    "Seven Color Jumping Change",
)

ZENGGE_COMMAND_NAMES = (
    "status_notify",
    "state_query",
    "power",
    "brightness",
    "rgb",
    "color_temp",
    "warm_white",
    "effect",
)
ZENGGE_EFFECT_COMMAND_FIELDS = (
    "command=0xed",
    "payload[0]=0xff device_type",
    "payload[1]=effect",
    "payload[2]=speed",
    "payload[3]=level",
    "old-UniLED default speed=0",
    "old-UniLED default level=100",
)
ZENGGE_CONTROL_GAP_HINTS = (
    "Old UniLED exposed Zengge nodes as light/sensor features only",
    "Effect speed/level controls resend the current effect with the edited byte",
    "Known node metadata from advertisements and MagicHue cloud import is registered",
    "Remote and non-light mesh events still need notification mapping",
)
ZENGGE_CONTROL_BLOCKERS = (
    "mesh_remote_event_parser_pending",
    "mesh_provisioning_frame_pending",
    "mesh_group_management_pending",
    "mesh_node_management_controls_pending",
)
RG4_ACCESSORIES_PACKAGE = "packages/accessories"
RG4_ACCESSORIES_PACKAGE_ASSET_COUNT = 9
RG4_ROUTE_HINTS = (
    "/device/ble_mesh_rc",
    "/device/ble_mesh_rc/provisioning_guide",
)
RG4_PROVISIONING_HINTS = (
    "One-touch provisioning and remote control of zones",
    (
        "Long press the Provisioning button until the indicator light flashes "
        "twice quickly"
    ),
    (
        "2. Provisioning automatically ends after 90 seconds. If there are "
        "still unprovisioned devices nearby, you can long press the button "
        "again to continue provisioning;"
    ),
    (
        "3. During the provisioning process, other devices cannot be "
        "controlled. You can press the provisioning button again to end "
        "provisioning."
    ),
    "If indicator light flashes rapidly, it indicates abnormal provisioning",
    "Indicator breathing means provisioning is in progress",
    "Indicator off means provisioning is complete",
    "Found 1 provisioned device",
    "assigned provisioner unicast address:",
    "Invalid PDU(The provisioning protocol PDU is not recognized by the device.)",
    (
        "Out of Resources(The provisioning protocol cannot be continued due "
        "to insufficient resources in the device.)2"
    ),
)
RG4_EXACT_PROVISIONING_STRING_HINTS = (
    "One-touch provisioning and remote control of zones",
    (
        "2. Provisioning automatically ends after 90 seconds. If there are "
        "still unprovisioned devices nearby, you can long press the button "
        "again to continue provisioning;"
    ),
    (
        "3. During the provisioning process, other devices cannot be "
        "controlled. You can press the provisioning button again to end "
        "provisioning."
    ),
    "If indicator light flashes rapidly, it indicates abnormal provisioning",
    "Found 1 provisioned device",
    "assigned provisioner unicast address:",
    "Invalid PDU(The provisioning protocol PDU is not recognized by the device.)",
    (
        "Out of Resources(The provisioning protocol cannot be continued due "
        "to insufficient resources in the device.)2"
    ),
    "2#onProvisioningCapabilitiesReceived2",
    "ProvisioningCapabilitiesPdu =",
    "provisioner_uuid",
    "provisioningCapabilities",
)
RG4_PROVISIONING_STATE_HINTS = (
    "provisioningStart",
    "provisioningInvite",
    "provisioningPublicKey",
    "provisioningData",
    "provisioningConfirmation",
    "provisioningRandom",
    "provisioningInputComplete",
    "provisioningComplete",
    "provisioningFailed",
)
RG4_APK_ASSET_EVIDENCE = (
    f"{RG4_ACCESSORIES_PACKAGE}/assets/icons/ble_mesh_provisioning.png",
    f"{RG4_ACCESSORIES_PACKAGE}/assets/icons/mesh_group.png",
    f"{RG4_ACCESSORIES_PACKAGE}/assets/icons/mesh_node.png",
    f"{RG4_ACCESSORIES_PACKAGE}/assets/images/fast_provisioning_guide_1.png",
    f"{RG4_ACCESSORIES_PACKAGE}/assets/images/fast_provisioning_guide_2.png",
    f"{RG4_ACCESSORIES_PACKAGE}/assets/images/fast_provisioning_guide_3.png",
    f"{RG4_ACCESSORIES_PACKAGE}/assets/images/rg4_reconnect_guide.png",
    f"{RG4_ACCESSORIES_PACKAGE}/assets/images/rg4_screen_head_bg.png",
    f"{RG4_ACCESSORIES_PACKAGE}/assets/images/rg4_zones_bg.png",
)
RG4_APK_STRING_EVIDENCE = (
    "Catalog records route RG4 to /device/ble_mesh_rc",
    "Native routes expose /device/ble_mesh_rc/provisioning_guide",
    "Native strings expose provisioner_uuid",
    "Native strings expose provisioningCapabilities",
    "Native strings expose one-touch provisioning and zone remote wording",
    "Native strings expose 90-second fast provisioning timeout text",
    "Native strings expose mesh provisioning state callback names",
    (
        "Native strings expose provisioning error labels for Invalid PDU and "
        "Out of Resources"
    ),
)

SCENE_MESH_ROUTE_HINTS = ("/device/scene_ui",)
SCENE_MESH_PROVISIONING_HINTS = (
    (
        "1. SP31XE series requires firmware V1.1 or above, and SP32XE series "
        'requires firmware V1.1 or above to support the "One-touch '
        'Provisioning" function;'
    ),
    (
        "2. Provisioning automatically ends after 90 seconds. If there are "
        "still unprovisioned devices nearby, you can long press the button "
        "again to continue provisioning;"
    ),
    (
        "3. During the provisioning process, other devices cannot be "
        "controlled. You can press the provisioning button again to end "
        "provisioning."
    ),
)
SCENE_MESH_CONTROL_GAP_HINTS = (
    "Scene mesh uses the scene_ui APK package, not the RG4 accessories package",
    "No scene mesh provisioning frame map has been recovered",
    "No scene mesh group, node, or scene-routing command map has been recovered",
)
SCENE_MESH_CONTROL_BLOCKERS = (
    "scene_mesh_provisioning_frame_pending",
    "scene_mesh_group_management_pending",
    "scene_mesh_node_lifecycle_pending",
    "scene_mesh_routing_frame_pending",
)
SCENE_MESH_APK_STRING_EVIDENCE = (
    "Catalog records scene mesh models with connectCaps=8 and /device/scene_ui",
    *SCENE_MESH_PROVISIONING_HINTS,
)


@dataclass(frozen=True, slots=True)
class BLEMeshProfile:
    """Known BLE mesh facts for one catalog model."""

    family: ProtocolFamily
    protocol_name: str
    package: str | None = None
    service_uuid: str | None = None
    status_uuid: str | None = None
    command_uuid: str | None = None
    pair_uuid: str | None = None
    manufacturer_id: int | None = None
    telink_manufacturer_id: int | None = None
    default_mesh_uuid: int | None = None
    requires_pairing: bool = False
    requires_cloud_mesh_credentials: bool = False
    old_uniled_protocol_known: bool = False
    core_command_protocol_known: bool = False
    status_uses_notifications: bool = False
    effect_names: tuple[str, ...] = ()
    command_names: tuple[str, ...] = ()
    effect_command_fields: tuple[str, ...] = ()
    sig_mesh_uuid_hints: tuple[str, ...] = ()
    control_gap_hints: tuple[str, ...] = ()
    control_blockers: tuple[str, ...] = ()
    route_hints: tuple[str, ...] = ()
    provisioning_hints: tuple[str, ...] = ()
    provisioning_state_hints: tuple[str, ...] = ()
    package_asset_count: int = 0
    apk_asset_evidence: tuple[str, ...] = ()
    apk_string_evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BLEMeshAdvertisement:
    """Telink/Zengge mesh identity parsed from BLE manufacturer data."""

    mesh_uuid: int
    node_id: int
    node_type: int

    @property
    def old_uniled_unique_id(self) -> str:
        """Return the mesh unique ID shape used by old UniLED."""
        return f"zng_mesh_{hex(self.mesh_uuid)}"


def mesh_profile_for_model(model: CatalogModel) -> BLEMeshProfile | None:
    """Return known BLE mesh facts for a catalog model."""
    if TransportKind.BLE_MESH not in model.transports:
        return None

    if model.family is ProtocolFamily.ZENGGE_MESH:
        return BLEMeshProfile(
            family=model.family,
            protocol_name="telink_zengge",
            package=RG4_ACCESSORIES_PACKAGE,
            service_uuid=TELINK_SERVICE_UUID,
            status_uuid=TELINK_STATUS_UUID,
            command_uuid=TELINK_COMMAND_UUID,
            pair_uuid=TELINK_PAIR_UUID,
            manufacturer_id=ZENGGE_MANUFACTURER_ID,
            telink_manufacturer_id=TELINK_MANUFACTURER_ID,
            default_mesh_uuid=ZENGGE_DEFAULT_MESH_UUID,
            requires_pairing=True,
            requires_cloud_mesh_credentials=True,
            old_uniled_protocol_known=True,
            core_command_protocol_known=True,
            status_uses_notifications=True,
            effect_names=ZENGGE_EFFECTS,
            command_names=ZENGGE_COMMAND_NAMES,
            effect_command_fields=ZENGGE_EFFECT_COMMAND_FIELDS,
            sig_mesh_uuid_hints=SIG_MESH_UUID_HINTS,
            control_gap_hints=ZENGGE_CONTROL_GAP_HINTS,
            control_blockers=ZENGGE_CONTROL_BLOCKERS,
            route_hints=RG4_ROUTE_HINTS,
            provisioning_hints=RG4_PROVISIONING_HINTS,
            provisioning_state_hints=RG4_PROVISIONING_STATE_HINTS,
            package_asset_count=RG4_ACCESSORIES_PACKAGE_ASSET_COUNT,
            apk_asset_evidence=RG4_APK_ASSET_EVIDENCE,
            apk_string_evidence=RG4_APK_STRING_EVIDENCE,
        )

    if model.family is ProtocolFamily.BANLANX_SCENE_MESH:
        return BLEMeshProfile(
            family=model.family,
            protocol_name="banlanx_scene_mesh",
            package=SCENE_PACKAGE,
            route_hints=SCENE_MESH_ROUTE_HINTS,
            provisioning_hints=SCENE_MESH_PROVISIONING_HINTS,
            sig_mesh_uuid_hints=SIG_MESH_UUID_HINTS,
            control_gap_hints=SCENE_MESH_CONTROL_GAP_HINTS,
            control_blockers=SCENE_MESH_CONTROL_BLOCKERS,
            package_asset_count=SCENE_PACKAGE_ASSET_COUNT,
            apk_string_evidence=SCENE_MESH_APK_STRING_EVIDENCE,
        )

    return None


def telink_mesh_advertisement(
    manufacturer_data: Mapping[int, bytes | bytearray],
) -> BLEMeshAdvertisement | None:
    """Parse old-UniLED Telink mesh identity from manufacturer data."""
    data = manufacturer_data.get(TELINK_MANUFACTURER_ID)
    if data is None:
        return None
    data = bytes(data)
    if len(data) < 10:
        return None
    return BLEMeshAdvertisement(
        mesh_uuid=int.from_bytes(data[:2], byteorder="little"),
        node_id=data[9],
        node_type=data[7],
    )


def describe_mesh_profile(profile: BLEMeshProfile | None) -> str | None:
    """Return a compact diagnostic string for a BLE mesh profile."""
    if profile is None:
        return None

    parts = [
        profile.family.value,
        profile.protocol_name,
        "core_protocol_known"
        if profile.core_command_protocol_known
        else "core_protocol_pending",
    ]
    if profile.requires_pairing:
        parts.append("pairing_required")
    if profile.old_uniled_protocol_known:
        parts.append("old_uniled_protocol_known")
    if profile.service_uuid is not None:
        parts.append(f"service={profile.service_uuid}")
    if profile.effect_names:
        parts.append(f"effects={len(profile.effect_names)}")
    if profile.command_names:
        parts.append(f"commands={len(profile.command_names)}")
    if profile.effect_command_fields:
        parts.append(f"effect_fields={len(profile.effect_command_fields)}")
    if profile.sig_mesh_uuid_hints:
        parts.append(f"sig_mesh_uuids={len(profile.sig_mesh_uuid_hints)}")
    if profile.control_gap_hints:
        parts.append(f"gaps={len(profile.control_gap_hints)}")
    if profile.control_blockers:
        parts.append(f"blockers={len(profile.control_blockers)}")
    if profile.route_hints:
        parts.append(f"routes={len(profile.route_hints)}")
    if profile.provisioning_hints:
        parts.append(f"provisioning={len(profile.provisioning_hints)}")
    if profile.provisioning_state_hints:
        parts.append(f"provisioning_states={len(profile.provisioning_state_hints)}")
    if profile.package_asset_count:
        parts.append(f"package_assets={profile.package_asset_count}")
    if profile.apk_asset_evidence:
        parts.append(f"apk_assets={len(profile.apk_asset_evidence)}")
    if profile.apk_string_evidence:
        parts.append(f"apk_strings={len(profile.apk_string_evidence)}")
    return "; ".join(parts)
