"""APK-derived BanlanX cloud profile metadata."""

from __future__ import annotations

from dataclasses import dataclass

from .catalog import CatalogModel, TransportKind

BANLANX_CLOUD_PROVIDER = "banlanx_cloud"

BANLANX_CLOUD_BASE_URLS = (
    "https://app.ledhue.com/spiot2",
    "https://app.ledhue.com/spiot/banlanx2",
    "https://app.ledhue.com/spiot/els/v1",
    "https://app.ledhue.com/spiot/app-link/alexa",
)

BANLANX_CLOUD_AUTH_ENDPOINTS = (
    "/home/device/auth",
    "/home/device/auth/setup",
    "/home/device/auth/change",
    "/home/device/auth/forgot",
    "/home/device/auth/manage",
    "/home/device/auth/reset",
)

BANLANX_CLOUD_ACCOUNT_AUTH_ENDPOINTS = (
    "/auth/refresh-token",
    "/auth/sign-in",
    "/auth/sign-up",
    "/auth/signIn/forgetPassword",
    "/auth/signIn/noAccount",
    "/auth/signIn2",
    "/auth/signUp2",
    "/auth/user/modifyPassword/token",
    "/passcode/sign-up",
    "/user/modify-pwd-token",
    "/user/sign-out",
)

BANLANX_CLOUD_ROOT_DEVICE_ENDPOINTS = (
    "/configureDevice",
    "/device/check-update2",
)

BANLANX_CLOUD_HOME_DEVICE_ENDPOINTS = (
    "/home/device/add",
    "/home/device/fw_new_version",
    "/home/device/ota",
    "/home/device/reset",
)

BANLANX_CLOUD_BTMESH_ENDPOINTS = (
    "/user/btmesh/get",
    "/user/btmesh/update",
)

BANLANX_CLOUD_USER_DEVICE_ENDPOINTS = (
    "/user/device/bind",
    "/user/device/checkOtaProgress",
    "/user/device/connection/cloud/check",
    "/user/device/info",
    "/user/device/post/raw",
    "/user/device/post/update",
    "/user/device/remove",
    "/user/device/rename",
    "/user/device/reorder2",
    "/user/device/time-sync",
)

BANLANX_CLOUD_LOCAL_DEVICE_ENDPOINTS = (
    "/user/local-device/add",
    "/user/local-device/add/batch2",
)

BANLANX_CLOUD_RAW_COMMAND_ENDPOINTS = ("/user/device/post/raw",)

BANLANX_CLOUD_DEVICE_ENDPOINTS = tuple(
    dict.fromkeys(
        (
            *BANLANX_CLOUD_ROOT_DEVICE_ENDPOINTS,
            *BANLANX_CLOUD_HOME_DEVICE_ENDPOINTS,
            *BANLANX_CLOUD_BTMESH_ENDPOINTS,
            *BANLANX_CLOUD_USER_DEVICE_ENDPOINTS,
            *BANLANX_CLOUD_LOCAL_DEVICE_ENDPOINTS,
        )
    )
)

BANLANX_CLOUD_CONTENT_ENDPOINTS = (
    "/banlanx/app/check-update",
    "/banlanx/app/info",
    "/banlanx/app/manuals/getAll",
    "/banlanx/device/manual/sp63xe",
    "/device/manual",
    "/device/manual/detail",
    "/device/scene/image/get",
    "/user/resources",
    "/user/support-ai",
)

BANLANX_CLOUD_VOICE_ENDPOINTS = (
    "/banlanx/user/alexa/enablement/status",
    "/banlanx/user/alexa/link",
    "/banlanx/user/alexa/unlink",
    "https://app.ledhue.com/spiot/app-link/alexa",
    (
        "https://alexa.amazon.com/spa/skill-account-linking-consent"
        "?fragment=skill-account-linking-consent&client_id=2"
    ),
    "https://www.amazon.com/ap/oa?client_id=",
)

BANLANX_CLOUD_DOCUMENT_URLS = (
    "https://document.ledhue.com/banlanx/about/privacy",
    "https://document.ledhue.com/banlanx/about/user-agreement",
    "https://document.ledhue.com/banlanx/faq/version/8/default",
    "https://document.ledhue.com/banlanx/faq/version/8/default/page/failed-to-config-wifi.html",
    "https://document.ledhue.com/banlanx/faq/version/8/zh/page/failed-to-config-wifi.html2",
    "https://document.ledhue.com/banlanx/faq/version/8/zh2",
)

BANLANX_CLOUD_AUTH_TOKEN_HINTS = (
    "init:token",
    "user:token",
    "user:refresh_token",
    "refresh token request!",
    "refreshToken2",
    "nullToken",
    "setupAuth",
    "serverAuth",
    "resetAuth",
    "ledhue|",
)

BANLANX_CLOUD_DEVICE_IDENTITY_HINTS = (
    "deviceCode",
    "deviceUdids =",
    "device_id = ?",
    "device_key",
    "device_model2",
    "device_name",
    "device_to_group_mapping",
    "device_udid",
    "device_udids2",
    "mobile_device_identifier",
)

BANLANX_CLOUD_HTTP_HEADER_HINTS = (
    "Authorization",
    "Bearer",
    "S-AccessKey",
    "S-AppVer",
    "S-AppVerName2",
    "S-SysCode",
    "S-SysName",
    "S-System",
    "S-Timestamp",
    "content-type:",
    "application/json",
)

BANLANX_CLOUD_SIGNATURE_HINTS = (
    "buildSignature",
    ", buildSignature:",
    ", nonce =",
    "encrypt nonce =",
    "decrypt nonce =",
)

BANLANX_CLOUD_RAW_STRING_HINTS = tuple(
    dict.fromkeys(
        (
            *BANLANX_CLOUD_BASE_URLS,
            *BANLANX_CLOUD_ACCOUNT_AUTH_ENDPOINTS,
            *BANLANX_CLOUD_AUTH_ENDPOINTS,
            *BANLANX_CLOUD_DEVICE_ENDPOINTS,
            *BANLANX_CLOUD_CONTENT_ENDPOINTS,
            *BANLANX_CLOUD_VOICE_ENDPOINTS,
            *BANLANX_CLOUD_DOCUMENT_URLS,
            *BANLANX_CLOUD_AUTH_TOKEN_HINTS,
            *BANLANX_CLOUD_DEVICE_IDENTITY_HINTS,
            *BANLANX_CLOUD_HTTP_HEADER_HINTS,
            *BANLANX_CLOUD_SIGNATURE_HINTS,
        )
    )
)

BANLANX_CLOUD_TRANSPORT_HINTS = (
    "connectCaps=7 maps to BLE, LAN, and optional cloud in the catalog",
    "BanlanX cloud hosts were recovered from Flutter libapp.so strings",
    "Cloud fallback should stay explicit opt-in and never replace local control",
    "MagicHue/Zengge mesh cloud metadata is a separate old-UniLED cloud family",
)

BANLANX_CLOUD_PROTOCOL_GAP_HINTS = (
    "No BanlanX account token or refresh schema has been mapped from Flutter AOT",
    "Header/signature string anchors exist but no signing contract is proven",
    "No /user/device/post/raw JSON envelope or command packet mapping is proven",
    "No cloud device-list, bind, ownership, or local-device lifecycle is ported",
    "Cloud reachability endpoints are not proof of a safe command path",
)

BANLANX_CLOUD_COMMAND_BLOCKERS = (
    "account_token_schema_pending",
    "request_signing_headers_pending",
    "region_reauth_contract_pending",
    "raw_command_json_envelope_pending",
    "device_bind_ownership_lifecycle_pending",
)

BANLANX_CLOUD_APK_STRING_EVIDENCE = (
    "libapp.so strings include https://app.ledhue.com/spiot2",
    "libapp.so strings include https://app.ledhue.com/spiot/banlanx2",
    "libapp.so strings include https://app.ledhue.com/spiot/els/v1",
    "libapp.so strings include /auth account routes and /auth/refresh-token",
    "libapp.so strings include /home/device/auth routes",
    "libapp.so strings include /home/device add/fw/ota/reset routes",
    "libapp.so strings include /user/sign-out and password-token routes",
    "libapp.so strings include /user/device/post/raw",
    "libapp.so strings include /user/device/connection/cloud/check",
    "libapp.so strings include Alexa account-linking and BanlanX Alexa paths",
    "libapp.so strings include document.ledhue.com privacy, agreement, and FAQ URLs",
    "libapp.so strings include user:token and user:refresh_token storage keys",
    "libapp.so strings include refreshToken2, setupAuth, serverAuth, and resetAuth",
    "libapp.so strings include Authorization, Bearer, S-Timestamp, and JSON anchors",
    "libapp.so strings include buildSignature and nonce/encrypt/decrypt anchors",
)


@dataclass(frozen=True, slots=True)
class BanlanXCloudEndpoint:
    """One APK-recovered BanlanX cloud route or account-link URL."""

    group: str
    path: str
    method: str
    auth: str
    base_url: str
    command_related: bool
    evidence: str


@dataclass(frozen=True, slots=True)
class BanlanXCloudRequestContractHint:
    """One APK-recovered cloud token/header/signature contract hint."""

    category: str
    apk_string: str
    unported_binding_status: str
    blocker: str
    evidence: str


def _cloud_endpoint_specs(
    group: str,
    endpoints: tuple[str, ...],
) -> tuple[BanlanXCloudEndpoint, ...]:
    """Build conservative endpoint inventory rows from literal APK strings."""
    return tuple(
        BanlanXCloudEndpoint(
            group=group,
            path=endpoint,
            method="unknown",
            auth="unproven",
            base_url="unresolved",
            command_related=endpoint in BANLANX_CLOUD_RAW_COMMAND_ENDPOINTS,
            evidence="BanlanX 3.3.1 Flutter libapp.so string",
        )
        for endpoint in endpoints
    )


BANLANX_CLOUD_ENDPOINT_INVENTORY = (
    *_cloud_endpoint_specs("account_auth", BANLANX_CLOUD_ACCOUNT_AUTH_ENDPOINTS),
    *_cloud_endpoint_specs("device_auth", BANLANX_CLOUD_AUTH_ENDPOINTS),
    *_cloud_endpoint_specs("root_device", BANLANX_CLOUD_ROOT_DEVICE_ENDPOINTS),
    *_cloud_endpoint_specs("home_device", BANLANX_CLOUD_HOME_DEVICE_ENDPOINTS),
    *_cloud_endpoint_specs("btmesh", BANLANX_CLOUD_BTMESH_ENDPOINTS),
    *_cloud_endpoint_specs("user_device", BANLANX_CLOUD_USER_DEVICE_ENDPOINTS),
    *_cloud_endpoint_specs("local_device", BANLANX_CLOUD_LOCAL_DEVICE_ENDPOINTS),
    *_cloud_endpoint_specs("content", BANLANX_CLOUD_CONTENT_ENDPOINTS),
    *_cloud_endpoint_specs("voice_assistant", BANLANX_CLOUD_VOICE_ENDPOINTS),
)


def _cloud_request_contract_specs(
    category: str,
    hints: tuple[str, ...],
    blocker: str,
) -> tuple[BanlanXCloudRequestContractHint, ...]:
    """Build conservative request-contract rows from literal APK strings."""
    return tuple(
        BanlanXCloudRequestContractHint(
            category=category,
            apk_string=hint,
            unported_binding_status="unproven",
            blocker=blocker,
            evidence="BanlanX 3.3.1 Flutter libapp.so string",
        )
        for hint in hints
    )


BANLANX_CLOUD_REQUEST_CONTRACT_HINTS = (
    *_cloud_request_contract_specs(
        "token_or_auth_storage",
        BANLANX_CLOUD_AUTH_TOKEN_HINTS,
        "account_token_schema_pending",
    ),
    *_cloud_request_contract_specs(
        "http_header",
        BANLANX_CLOUD_HTTP_HEADER_HINTS,
        "request_signing_headers_pending",
    ),
    *_cloud_request_contract_specs(
        "signature_or_nonce",
        BANLANX_CLOUD_SIGNATURE_HINTS,
        "request_signing_headers_pending",
    ),
)


@dataclass(frozen=True, slots=True)
class BanlanXCloudProfile:
    """Cloud/API facts recovered from BanlanX APK native strings."""

    provider: str
    model_name: str
    base_urls: tuple[str, ...]
    auth_endpoints: tuple[str, ...]
    account_auth_endpoints: tuple[str, ...]
    device_endpoints: tuple[str, ...]
    home_device_endpoints: tuple[str, ...]
    user_device_endpoints: tuple[str, ...]
    local_device_endpoints: tuple[str, ...]
    btmesh_endpoints: tuple[str, ...]
    root_device_endpoints: tuple[str, ...]
    raw_command_endpoints: tuple[str, ...]
    content_endpoints: tuple[str, ...]
    voice_assistant_endpoints: tuple[str, ...]
    document_urls: tuple[str, ...]
    auth_token_hints: tuple[str, ...]
    device_identity_hints: tuple[str, ...]
    http_header_hints: tuple[str, ...]
    signature_hints: tuple[str, ...]
    catalog_hints: tuple[str, ...]
    transport_hints: tuple[str, ...]
    protocol_gap_hints: tuple[str, ...]
    command_blockers: tuple[str, ...]
    command_protocol_known: bool
    endpoint_inventory: tuple[BanlanXCloudEndpoint, ...]
    request_contract_hints: tuple[BanlanXCloudRequestContractHint, ...]
    apk_string_evidence: tuple[str, ...]

    @property
    def endpoint_groups(self) -> tuple[str, ...]:
        """Return endpoint inventory groups in recovered order."""
        return tuple(
            dict.fromkeys(endpoint.group for endpoint in self.endpoint_inventory)
        )

    @property
    def command_related_endpoints(self) -> tuple[BanlanXCloudEndpoint, ...]:
        """Return endpoints adjacent to device command delivery."""
        return tuple(
            endpoint
            for endpoint in self.endpoint_inventory
            if endpoint.command_related
        )

    @property
    def unresolved_base_url_endpoints(self) -> tuple[BanlanXCloudEndpoint, ...]:
        """Return endpoints whose concrete base URL binding is still unknown."""
        return tuple(
            endpoint
            for endpoint in self.endpoint_inventory
            if endpoint.base_url == "unresolved"
        )

    @property
    def unproven_auth_endpoints(self) -> tuple[BanlanXCloudEndpoint, ...]:
        """Return endpoints whose auth requirement is still unproven."""
        return tuple(
            endpoint
            for endpoint in self.endpoint_inventory
            if endpoint.auth == "unproven"
        )

    @property
    def token_contract_hints(self) -> tuple[BanlanXCloudRequestContractHint, ...]:
        """Return token/storage request-contract hints."""
        return tuple(
            hint
            for hint in self.request_contract_hints
            if hint.category == "token_or_auth_storage"
        )

    @property
    def header_contract_hints(self) -> tuple[BanlanXCloudRequestContractHint, ...]:
        """Return HTTP header request-contract hints."""
        return tuple(
            hint
            for hint in self.request_contract_hints
            if hint.category == "http_header"
        )

    @property
    def signature_contract_hints(self) -> tuple[BanlanXCloudRequestContractHint, ...]:
        """Return signature and nonce request-contract hints."""
        return tuple(
            hint
            for hint in self.request_contract_hints
            if hint.category == "signature_or_nonce"
        )


def cloud_profile_for_model(model: CatalogModel) -> BanlanXCloudProfile | None:
    """Return APK-derived BanlanX cloud facts for optional-cloud models."""
    if TransportKind.CLOUD_OPTIONAL not in model.transports:
        return None
    return BanlanXCloudProfile(
        provider=BANLANX_CLOUD_PROVIDER,
        model_name=model.name,
        base_urls=BANLANX_CLOUD_BASE_URLS,
        auth_endpoints=BANLANX_CLOUD_AUTH_ENDPOINTS,
        account_auth_endpoints=BANLANX_CLOUD_ACCOUNT_AUTH_ENDPOINTS,
        device_endpoints=BANLANX_CLOUD_DEVICE_ENDPOINTS,
        home_device_endpoints=BANLANX_CLOUD_HOME_DEVICE_ENDPOINTS,
        user_device_endpoints=BANLANX_CLOUD_USER_DEVICE_ENDPOINTS,
        local_device_endpoints=BANLANX_CLOUD_LOCAL_DEVICE_ENDPOINTS,
        btmesh_endpoints=BANLANX_CLOUD_BTMESH_ENDPOINTS,
        root_device_endpoints=BANLANX_CLOUD_ROOT_DEVICE_ENDPOINTS,
        raw_command_endpoints=BANLANX_CLOUD_RAW_COMMAND_ENDPOINTS,
        content_endpoints=BANLANX_CLOUD_CONTENT_ENDPOINTS,
        voice_assistant_endpoints=BANLANX_CLOUD_VOICE_ENDPOINTS,
        document_urls=BANLANX_CLOUD_DOCUMENT_URLS,
        auth_token_hints=BANLANX_CLOUD_AUTH_TOKEN_HINTS,
        device_identity_hints=BANLANX_CLOUD_DEVICE_IDENTITY_HINTS,
        http_header_hints=BANLANX_CLOUD_HTTP_HEADER_HINTS,
        signature_hints=BANLANX_CLOUD_SIGNATURE_HINTS,
        catalog_hints=(
            f"model_id={model.model_id}",
            f"family={model.family.value}",
            f"connectCaps={model.connect_caps}",
            f"support_level={model.support_level.value}",
            "transports="
            + ",".join(transport.value for transport in model.transports),
        ),
        transport_hints=BANLANX_CLOUD_TRANSPORT_HINTS,
        protocol_gap_hints=BANLANX_CLOUD_PROTOCOL_GAP_HINTS,
        command_blockers=BANLANX_CLOUD_COMMAND_BLOCKERS,
        command_protocol_known=False,
        endpoint_inventory=BANLANX_CLOUD_ENDPOINT_INVENTORY,
        request_contract_hints=BANLANX_CLOUD_REQUEST_CONTRACT_HINTS,
        apk_string_evidence=BANLANX_CLOUD_APK_STRING_EVIDENCE,
    )


def describe_cloud_profile(profile: BanlanXCloudProfile | None) -> str | None:
    """Return a compact diagnostic string for a BanlanX cloud profile."""
    if profile is None:
        return None
    status = (
        "command_protocol_known"
        if profile.command_protocol_known
        else "command_protocol_pending"
    )
    return (
        f"{profile.provider}; bases={len(profile.base_urls)}; "
        f"auth={len(profile.auth_endpoints)}; "
        f"account_auth={len(profile.account_auth_endpoints)}; "
        f"devices={len(profile.device_endpoints)}; "
        f"inventory={len(profile.endpoint_inventory)}; "
        f"endpoint_groups={len(profile.endpoint_groups)}; "
        f"command_related={len(profile.command_related_endpoints)}; "
        f"unresolved_bases={len(profile.unresolved_base_url_endpoints)}; "
        f"unproven_auth={len(profile.unproven_auth_endpoints)}; "
        f"home_devices={len(profile.home_device_endpoints)}; "
        f"user_devices={len(profile.user_device_endpoints)}; "
        f"local_devices={len(profile.local_device_endpoints)}; "
        f"btmesh={len(profile.btmesh_endpoints)}; "
        f"root_devices={len(profile.root_device_endpoints)}; "
        f"raw_commands={len(profile.raw_command_endpoints)}; "
        f"content={len(profile.content_endpoints)}; "
        f"voice={len(profile.voice_assistant_endpoints)}; "
        f"docs={len(profile.document_urls)}; "
        f"tokens={len(profile.auth_token_hints)}; "
        f"device_identity={len(profile.device_identity_hints)}; "
        f"headers={len(profile.http_header_hints)}; "
        f"signatures={len(profile.signature_hints)}; "
        f"request_contracts={len(profile.request_contract_hints)}; "
        f"token_contracts={len(profile.token_contract_hints)}; "
        f"header_contracts={len(profile.header_contract_hints)}; "
        f"signature_contracts={len(profile.signature_contract_hints)}; "
        f"transport={len(profile.transport_hints)}; "
        f"gaps={len(profile.protocol_gap_hints)}; "
        f"blockers={len(profile.command_blockers)}; {status}; "
        f"catalog={len(profile.catalog_hints)}"
    )
