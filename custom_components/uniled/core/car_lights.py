"""APK-derived BanlanX car-light profile metadata."""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import CatalogModel, ProtocolFamily

CAR_LIGHT_PACKAGE = "packages/car_lights"
CAR_LIGHT_PACKAGE_ASSET_COUNT = 58

CAR_LIGHT_ZONES = (
    "Car lights",
    "Chassis lights",
    "Console lights",
    "Door lights",
    "Footsocket lights",
    "Storage lights",
    "Welcome lights",
    "Wheel lights",
)

CAR_LIGHT_TRIGGERS = (
    "Brake light",
    "Brake light blink",
    "Brake light blink new",
    "Fade car light",
    "Flow car light",
    "Left turn signal flow",
    "Right turn signal flow",
    "Turn signal blink",
    "Turn signal blink new",
)

CAR_LIGHT_CONTROL_SURFACES = (
    "Setup",
    "Zone selection",
    "Trigger settings",
    "Color correction",
    "Subdevices management",
    "Device password",
    "Password reset",
    "Settings",
)

CAR_LIGHT_ACCESSORY_ASSETS = (
    "ic_subdevice_manager_outlined",
    "ic_master_slave_sycned",
    "ic_pwd_edit_outlined",
    "reset_device_pwd",
)

CAR_LIGHT_ANIMATION_ASSETS = (
    f"{CAR_LIGHT_PACKAGE}/assets/animations/brake_light.zip",
    f"{CAR_LIGHT_PACKAGE}/assets/animations/brake_light_blink.zip",
    f"{CAR_LIGHT_PACKAGE}/assets/animations/brake_light_blink_new.zip",
    f"{CAR_LIGHT_PACKAGE}/assets/animations/fade_car_light.zip",
    f"{CAR_LIGHT_PACKAGE}/assets/animations/flow_car_light.zip",
    f"{CAR_LIGHT_PACKAGE}/assets/animations/left_turn_signal_light_flow.zip",
    f"{CAR_LIGHT_PACKAGE}/assets/animations/reset_device_pwd.zip",
    f"{CAR_LIGHT_PACKAGE}/assets/animations/right_turn_signal_light_flow.zip",
    f"{CAR_LIGHT_PACKAGE}/assets/animations/turn_signal_light_blink.zip",
    f"{CAR_LIGHT_PACKAGE}/assets/animations/turn_signal_light_blink_new.zip",
)

CAR_LIGHT_TRIGGER_IMAGE_ASSETS = (
    f"{CAR_LIGHT_PACKAGE}/assets/images/astern.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/brake.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/left_turn_signal.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/right_turn_signal.png",
)

CAR_LIGHT_ZONE_IMAGE_ASSETS = (
    f"{CAR_LIGHT_PACKAGE}/assets/images/car_areas.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/car_argb.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/car_chassic.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/car_console.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/car_door.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/car_footsocket.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/car_lights_banner.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/car_rgb.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/car_storage.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/car_wheel.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/chassis_lights.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/new_car.png",
    f"{CAR_LIGHT_PACKAGE}/assets/images/whole_car.png",
)

CAR_LIGHT_SUBDEVICE_HINTS = (
    "subdevice",
    "subdeviceAddr = ",
    "include_added_subdevices",
    "exclude_slave_devices",
    (
        "Removing the master device will reset all sub-devices. "
        "Please proceed with caution!"
    ),
    "The subdevice configuration is not yet complete. Are you sure you want to exit?",
    "Unable to add the subdevice",
    (
        "Secondary devices will chain-react to turn off lights when Primary "
        "loses power."
    ),
)

CAR_LIGHT_SUBDEVICE_FILTERS = (
    "include_added_subdevices",
    "exclude_slave_devices",
)

CAR_LIGHT_PASSWORD_HINTS = (
    "Device password",
    "Set your password",
    "Setup password successfully",
    "Turn on password",
    "Turn off password",
    "Wait for the device password reset...",
    "The password reset timed out. Please try again!",
    '_xxx"(the password is 12345678), and return to "BanlanX".',
)

CAR_LIGHT_PASSWORD_FLOW_STATES = (
    "Set your password",
    "Setup password successfully",
    "Turn on password",
    "Turn off password",
    "Wait for the device password reset...",
    "The password reset timed out. Please try again!",
)

CAR_LIGHT_PASSWORD_ENTRY_HINTS = (
    "Enter your password",
    "Enter new password",
    "Enter new password again",
    "New password2",
    "Repeat password",
    "Show password",
    "Forget password?",
    "Forgot password?",
)

CAR_LIGHT_PASSWORD_POLICY_HINTS = (
    "Change password",
    "Change password successfully2",
    "Inconsistent new password input!",
    (
        "When you turn off your password, you won't be able to prevent other "
        "users from connecting and controlling your device."
    ),
    "The password can consist of numbers, letters or symbols (_ - ! @ # $ & * ~). ",
    (
        "Enter your new password. The password can consist of numbers, letters "
        "or symbols (_ - ! @ # $ & * ~)."
    ),
)

CAR_LIGHT_PASSWORD_RESET_HINTS = (
    "Press and hold the power button for 3 seconds until the indicator "
    "switches from blinking to steady on to reset the password.",
    "When enabled: 5 power cycles reset the device.",
    "Remove and reset device.",
    "Reset password successfully",
)

CAR_LIGHT_TRIGGER_STORAGE_HINTS = (
    (
        "CREATE TABLE sp_trigger "
        "(id INTEGER PRIMARY KEY, device_id INTEGER, trigger_index INTEGER, name TEXT)"
    ),
    "sp_trigger",
    "trigger_id",
    "trigger_index",
    "triggers",
    "Set the lighting effect when the corresponding trigger signal is received",
    "Rename trigger",
)

CAR_LIGHT_TRIGGER_ACTIONS = (
    "Set the lighting effect when the corresponding trigger signal is received",
    "Rename trigger",
)

CAR_LIGHT_ROUTE_HINTS = (
    "/car_lights",
    "/car_lights/new",
    "/car_lights/setup",
    "/car_lights/settings/chassic_lights_trigger",
    "/car_lights/settings/color_correction",
    "/car_lights/settings/subdevices_management",
    "/car_lights/settings2",
)

CAR_LIGHT_APK_ASSET_EVIDENCE = (
    *CAR_LIGHT_ANIMATION_ASSETS,
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_car_lights.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_car_lights_outlined.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_car_trigger_outlined.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_chassis_lights.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_chassis_lights_outlined.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_color_correction_outlined.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_console_lights.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_console_lights_outlined.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_door_lights.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_door_lights_outlined.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_footsocket_lights.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_footsocket_lights_outlined.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_master_slave_sycned.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_pwd_edit_outlined.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_storage_lights.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_storage_lights_outlined.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_subdevice_manager_outlined.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_welcome_lights.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_wheel_lights.png",
    f"{CAR_LIGHT_PACKAGE}/assets/icons/ic_wheel_lights_outlined.png",
    *CAR_LIGHT_TRIGGER_IMAGE_ASSETS,
    *CAR_LIGHT_ZONE_IMAGE_ASSETS,
)

CAR_LIGHT_APK_STRING_EVIDENCE = (
    "SP701E appears in native strings as the interior-light controller",
    "SP702E appears in native strings as the chassis-light controller",
    "SP-MIC appears in native strings as a wireless microphone accessory",
    "Wireless MIC setup requires a Chassis Lamp Controller (SP702E)",
    "Interior lights must be added before chassis lights when both are present",
    "Native strings expose sp_trigger storage, trigger_id, and trigger_index",
    "Native strings expose subdeviceAddr plus include/exclude slave-device filters",
    "Native strings expose device password setup/reset states",
    "Native strings expose password entry, change, and policy labels",
    "Native strings expose button-hold and power-cycle password reset guidance",
    "Native strings expose primary-controller retain/Ignore setup flow",
    "Native strings expose fast-flashing white install-area identification flow",
    "Native strings expose secondary-device power-loss behavior",
)

CAR_LIGHT_SETUP_REQUIREMENTS = (
    (
        'The "Wireless MIC" can only be used as an accessory to the '
        '"Chassis Lamp Controller (SP702E)". '
    ),
    'Please add a "Chassis Lamp Controller (SP702E)" first.',
    (
        "It is not supported to add the interiorl lights when only the chassis "
        "light is available. After removing the chassis light, add the "
        "interiorl light (SP701E) and then add the chassis light (SP702E)."
    ),
    (
        'requires "Microphone" permission to trigger the LED controller\'s '
        "lighting effects in real-time by capturing surrounding sounds."
    ),
    (
        "Secondary devices will chain-react to turn off lights when Primary "
        "loses power."
    ),
)

CAR_LIGHT_ACCESSORY_REQUIRED_CONTROLLERS = {
    "SP-MIC": "SP702E",
}

CAR_LIGHT_SETUP_FLOW_HINTS = (
    'To retain the current device as primary controller, select "Ignore"',
    (
        "If you are unsure about the installation area of the LED controller, "
        "observe which area in the car has LED strips displaying a "
        "fast-flashing white light effect. Please select the corresponding "
        "area in the diagram below."
    ),
)

CAR_LIGHT_SETUP_KEY_HINTS = (
    "isPrimary",
    "subUni",
    " channel is ",
    '" as the primary controller.',
    (
        'Click the "Exit" button below to return to the device discovery page '
        'and connect the device installed in "'
    ),
)

CAR_LIGHT_MODEL_ROLE_HINTS = (
    "Car Lights model_id=65537 family group",
    "SP701E parent_id=65537 interior_controller",
    "SP702E parent_id=65537 chassis_controller",
    "SP-MIC parent_id=65537 wireless_microphone_accessory",
    "SP-MIC required_controller=SP702E",
    "SP701E setup_order=1 before SP702E",
    "SP702E setup_order=2 after SP701E when both are present",
    "Native setup flow exposes isPrimary and subUni keys",
)

CAR_LIGHT_TRANSPORT_HINTS = (
    "connectCaps=1 maps to BLE-only for all car-light catalog records",
    "All car-light records share home_uri=/car_lights",
    "SP701E and SP702E are child models of the Car Lights parent group",
    "SP-MIC is a BLE accessory child model without color/spec function flags",
)

CAR_LIGHT_PROTOCOL_GAP_HINTS = (
    "No old-UniLED car-light implementation was found",
    "No confirmed car-light BLE command opcode table was recovered",
    "No car-light notification/status parser has been mapped",
    "No subdevice binding, password flow, or SP-MIC event packet flow is known",
)

CAR_LIGHT_COMMON_COMMAND_BLOCKERS = (
    "car_light_ble_opcode_pending",
    "car_light_status_parser_pending",
    "car_light_zone_command_pending",
    "car_light_trigger_packet_pending",
    "car_light_subdevice_binding_pending",
    "car_light_password_flow_pending",
)

CAR_LIGHT_SP_MIC_COMMAND_BLOCKERS = (
    *CAR_LIGHT_COMMON_COMMAND_BLOCKERS,
    "car_light_sp_mic_event_pending",
)


@dataclass(frozen=True, slots=True)
class CarLightModelRole:
    """APK catalog/native-string role for one car-light model."""

    role: str
    setup_stage: str
    setup_order: int | None
    required_controller_model: str | None = None
    parent_group_model_id: int | None = 65537


@dataclass(frozen=True, slots=True)
class CarLightSetupDependency:
    """Structured APK setup rule for one car-light catalog model."""

    model_name: str
    relationship: str
    related_model: str | None
    setup_order: int | None
    required: bool
    enforcement_status: str
    evidence: str


CAR_LIGHT_MODEL_ROLES = {
    "Car Lights": CarLightModelRole(
        role="car_light_family",
        setup_stage="family_group",
        setup_order=None,
        parent_group_model_id=None,
    ),
    "SP701E": CarLightModelRole(
        role="interior_controller",
        setup_stage="interior_before_chassis",
        setup_order=1,
    ),
    "SP702E": CarLightModelRole(
        role="chassis_controller",
        setup_stage="chassis_after_interior_when_both_present",
        setup_order=2,
    ),
    "SP-MIC": CarLightModelRole(
        role="wireless_microphone_accessory",
        setup_stage="accessory_after_sp702e",
        setup_order=None,
        required_controller_model=CAR_LIGHT_ACCESSORY_REQUIRED_CONTROLLERS["SP-MIC"],
    ),
}


CAR_LIGHT_SETUP_DEPENDENCIES = (
    CarLightSetupDependency(
        model_name="Car Lights",
        relationship="parent_group",
        related_model=None,
        setup_order=None,
        required=False,
        enforcement_status="catalog_group_only",
        evidence="Car Lights model_id=65537 family group",
    ),
    CarLightSetupDependency(
        model_name="SP701E",
        relationship="precedes_chassis_when_both_present",
        related_model="SP702E",
        setup_order=1,
        required=False,
        enforcement_status="diagnostic_only",
        evidence="SP701E setup_order=1 before SP702E",
    ),
    CarLightSetupDependency(
        model_name="SP702E",
        relationship="follows_interior_when_both_present",
        related_model="SP701E",
        setup_order=2,
        required=False,
        enforcement_status="diagnostic_only",
        evidence="SP702E setup_order=2 after SP701E when both are present",
    ),
    CarLightSetupDependency(
        model_name="SP-MIC",
        relationship="requires_chassis_controller",
        related_model="SP702E",
        setup_order=None,
        required=True,
        enforcement_status="diagnostic_only",
        evidence="SP-MIC required_controller=SP702E",
    ),
)


@dataclass(frozen=True, slots=True)
class CarLightProfile:
    """Family profile recovered from APK assets and native strings."""

    family: ProtocolFamily
    package: str
    zones: tuple[str, ...]
    triggers: tuple[str, ...]
    control_surfaces: tuple[str, ...]
    accessory_assets: tuple[str, ...]
    animation_assets: tuple[str, ...]
    trigger_image_assets: tuple[str, ...]
    zone_image_assets: tuple[str, ...]
    subdevice_hints: tuple[str, ...]
    subdevice_filters: tuple[str, ...]
    password_hints: tuple[str, ...]
    password_flow_states: tuple[str, ...]
    password_entry_hints: tuple[str, ...]
    password_policy_hints: tuple[str, ...]
    password_reset_hints: tuple[str, ...]
    trigger_storage_hints: tuple[str, ...]
    trigger_actions: tuple[str, ...]
    route_hints: tuple[str, ...]
    setup_requirements: tuple[str, ...]
    required_controller_model: str | None
    setup_flow_hints: tuple[str, ...]
    setup_key_hints: tuple[str, ...]
    model_role: CarLightModelRole | None
    model_role_hints: tuple[str, ...]
    model_setup_dependency: CarLightSetupDependency | None
    setup_dependencies: tuple[CarLightSetupDependency, ...]
    catalog_hints: tuple[str, ...]
    transport_hints: tuple[str, ...]
    protocol_gap_hints: tuple[str, ...]
    command_blockers: tuple[str, ...]
    command_protocol_known: bool
    package_asset_count: int
    apk_asset_evidence: tuple[str, ...]
    apk_string_evidence: tuple[str, ...]


def car_light_profile_for_model(model: CatalogModel) -> CarLightProfile | None:
    """Return the APK-derived car-light profile for matching models."""
    if model.family is not ProtocolFamily.BANLANX_CAR_LIGHTS:
        return None
    return CarLightProfile(
        family=ProtocolFamily.BANLANX_CAR_LIGHTS,
        package=CAR_LIGHT_PACKAGE,
        zones=CAR_LIGHT_ZONES,
        triggers=CAR_LIGHT_TRIGGERS,
        control_surfaces=CAR_LIGHT_CONTROL_SURFACES,
        accessory_assets=CAR_LIGHT_ACCESSORY_ASSETS,
        animation_assets=CAR_LIGHT_ANIMATION_ASSETS,
        trigger_image_assets=CAR_LIGHT_TRIGGER_IMAGE_ASSETS,
        zone_image_assets=CAR_LIGHT_ZONE_IMAGE_ASSETS,
        subdevice_hints=CAR_LIGHT_SUBDEVICE_HINTS,
        subdevice_filters=CAR_LIGHT_SUBDEVICE_FILTERS,
        password_hints=CAR_LIGHT_PASSWORD_HINTS,
        password_flow_states=CAR_LIGHT_PASSWORD_FLOW_STATES,
        password_entry_hints=CAR_LIGHT_PASSWORD_ENTRY_HINTS,
        password_policy_hints=CAR_LIGHT_PASSWORD_POLICY_HINTS,
        password_reset_hints=CAR_LIGHT_PASSWORD_RESET_HINTS,
        trigger_storage_hints=CAR_LIGHT_TRIGGER_STORAGE_HINTS,
        trigger_actions=CAR_LIGHT_TRIGGER_ACTIONS,
        route_hints=CAR_LIGHT_ROUTE_HINTS,
        setup_requirements=CAR_LIGHT_SETUP_REQUIREMENTS,
        required_controller_model=car_light_required_controller_model(model),
        setup_flow_hints=CAR_LIGHT_SETUP_FLOW_HINTS,
        setup_key_hints=CAR_LIGHT_SETUP_KEY_HINTS,
        model_role=car_light_model_role_for_model(model),
        model_role_hints=CAR_LIGHT_MODEL_ROLE_HINTS,
        model_setup_dependency=car_light_setup_dependency_for_model(model),
        setup_dependencies=CAR_LIGHT_SETUP_DEPENDENCIES,
        catalog_hints=_catalog_hints(model),
        transport_hints=CAR_LIGHT_TRANSPORT_HINTS,
        protocol_gap_hints=CAR_LIGHT_PROTOCOL_GAP_HINTS,
        command_blockers=car_light_command_blockers_for_model(model),
        command_protocol_known=False,
        package_asset_count=CAR_LIGHT_PACKAGE_ASSET_COUNT,
        apk_asset_evidence=CAR_LIGHT_APK_ASSET_EVIDENCE,
        apk_string_evidence=CAR_LIGHT_APK_STRING_EVIDENCE,
    )


def car_light_accessory_role(model: CatalogModel) -> str | None:
    """Return the model role recovered from car-light native strings."""
    role = car_light_model_role_for_model(model)
    if role is None:
        return None
    return role.role


def car_light_model_role_for_model(
    model: CatalogModel,
) -> CarLightModelRole | None:
    """Return the structured APK role for a car-light catalog model."""
    if model.family is not ProtocolFamily.BANLANX_CAR_LIGHTS:
        return None
    return CAR_LIGHT_MODEL_ROLES.get(
        model.name,
        CarLightModelRole(
            role="car_light_device",
            setup_stage="unknown_car_light_device",
            setup_order=None,
        ),
    )


def car_light_setup_dependency_for_model(
    model: CatalogModel,
) -> CarLightSetupDependency | None:
    """Return the structured APK setup dependency row for this model."""
    if model.family is not ProtocolFamily.BANLANX_CAR_LIGHTS:
        return None
    return next(
        (
            dependency
            for dependency in CAR_LIGHT_SETUP_DEPENDENCIES
            if dependency.model_name == model.name
        ),
        None,
    )


def car_light_required_setup_dependencies(
    profile: CarLightProfile,
) -> tuple[CarLightSetupDependency, ...]:
    """Return car-light setup rows that represent a hard app dependency."""
    return tuple(
        dependency
        for dependency in profile.setup_dependencies
        if dependency.required
    )


def car_light_ordered_setup_dependencies(
    profile: CarLightProfile,
) -> tuple[CarLightSetupDependency, ...]:
    """Return car-light setup rows that carry an APK setup order."""
    return tuple(
        dependency
        for dependency in profile.setup_dependencies
        if dependency.setup_order is not None
    )


def car_light_required_controller_model(model: CatalogModel) -> str | None:
    """Return the APK setup dependency for car-light accessory models."""
    role = car_light_model_role_for_model(model)
    if role is None:
        return None
    return role.required_controller_model


def car_light_setup_stage(model: CatalogModel) -> str | None:
    """Return the APK setup-stage role for this car-light model."""
    role = car_light_model_role_for_model(model)
    return None if role is None else role.setup_stage


def car_light_setup_order(model: CatalogModel) -> int | None:
    """Return the APK setup order for controller models, when known."""
    role = car_light_model_role_for_model(model)
    return None if role is None else role.setup_order


def car_light_command_blockers_for_model(model: CatalogModel) -> tuple[str, ...]:
    """Return command blockers that still apply to this car-light model."""
    if model.family is not ProtocolFamily.BANLANX_CAR_LIGHTS:
        return ()
    if model.name == "SP-MIC":
        return CAR_LIGHT_SP_MIC_COMMAND_BLOCKERS
    return CAR_LIGHT_COMMON_COMMAND_BLOCKERS


def _catalog_hints(model: CatalogModel) -> tuple[str, ...]:
    """Return model-specific APK catalog facts for diagnostics."""
    parent = "none" if model.parent_id is None else str(model.parent_id)
    transports = ",".join(transport.value for transport in model.transports) or "none"
    hints = [
        f"model_id={model.model_id}",
        f"parent_id={parent}",
        f"connectCaps={model.connect_caps}",
        f"specFunctions={model.spec_functions}",
        f"colorCap={model.color_cap}",
        f"transports={transports}",
    ]
    required_controller = car_light_required_controller_model(model)
    if required_controller is not None:
        hints.append(f"required_controller={required_controller}")
    return tuple(hints)


def describe_car_light_profile(profile: CarLightProfile | None) -> str | None:
    """Return a compact diagnostic string for the car-light profile."""
    if profile is None:
        return None
    status = (
        "command_protocol_known"
        if profile.command_protocol_known
        else "command_protocol_pending"
    )
    model_dependency = (
        profile.model_setup_dependency.relationship
        if profile.model_setup_dependency
        else "none"
    )
    return (
        f"{profile.family.value}; package={profile.package}; "
        f"zones={len(profile.zones)}; triggers={len(profile.triggers)}; "
        f"surfaces={len(profile.control_surfaces)}; "
        f"animations={len(profile.animation_assets)}; "
        f"trigger_images={len(profile.trigger_image_assets)}; "
        f"zone_images={len(profile.zone_image_assets)}; "
        f"subdevices={len(profile.subdevice_hints)}; "
        f"subdevice_filters={len(profile.subdevice_filters)}; "
        f"passwords={len(profile.password_hints)}; "
        f"password_flows={len(profile.password_flow_states)}; "
        f"password_entries={len(profile.password_entry_hints)}; "
        f"password_policies={len(profile.password_policy_hints)}; "
        f"password_resets={len(profile.password_reset_hints)}; "
        f"trigger_storage={len(profile.trigger_storage_hints)}; "
        f"trigger_actions={len(profile.trigger_actions)}; "
        f"requirements={len(profile.setup_requirements)}; "
        f"required_controller={profile.required_controller_model or 'none'}; "
        f"setup_stage="
        f"{profile.model_role.setup_stage if profile.model_role else 'unknown'}; "
        f"setup_flows={len(profile.setup_flow_hints)}; "
        f"setup_keys={len(profile.setup_key_hints)}; "
        f"role_hints={len(profile.model_role_hints)}; "
        f"setup_dependencies={len(profile.setup_dependencies)}; "
        f"required_dependencies={len(car_light_required_setup_dependencies(profile))}; "
        f"ordered_models={len(car_light_ordered_setup_dependencies(profile))}; "
        f"model_dependency={model_dependency}; "
        f"catalog={len(profile.catalog_hints)}; "
        f"gaps={len(profile.protocol_gap_hints)}; "
        f"blockers={len(profile.command_blockers)}; "
        f"package_assets={profile.package_asset_count}; "
        f"{status}; routes={len(profile.route_hints)}"
    )
