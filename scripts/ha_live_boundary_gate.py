"""Run optional live Home Assistant boundary checks for UniLED Next."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class HALiveGateError(RuntimeError):
    """Raised when a live Home Assistant boundary check fails."""


@dataclass(frozen=True, slots=True)
class HACredentials:
    """Credentials for one Home Assistant API session."""

    url: str
    access_token: str | None = None
    refresh_token: str | None = None
    client_id: str | None = None
    label: str = "env"


def load_dashboard_session_credentials(path: Path) -> tuple[HACredentials, ...]:
    """Load dashboard-style saved HA OAuth sessions without exposing secrets."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise HALiveGateError("dashboard session file must contain an object")

    credentials: list[HACredentials] = []
    for label, value in data.items():
        if not isinstance(value, dict):
            continue
        tokens = value.get("tokens")
        if not isinstance(tokens, dict):
            continue
        url = _optional_text(tokens.get("hassUrl"))
        refresh_token = _optional_text(tokens.get("refresh_token"))
        client_id = _optional_text(tokens.get("clientId"))
        access_token = _optional_text(tokens.get("access_token"))
        if url and (access_token or refresh_token):
            credentials.append(
                HACredentials(
                    url=url,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    client_id=client_id,
                    label=str(label)[:8],
                )
            )
    return tuple(credentials)


def service_names(services: object) -> set[str]:
    """Return ``domain.service`` names from Home Assistant's services response."""
    names: set[str] = set()
    if not isinstance(services, list):
        return names
    for domain_entry in services:
        if not isinstance(domain_entry, dict):
            continue
        domain = _optional_text(domain_entry.get("domain"))
        service_map = domain_entry.get("services")
        if not domain or not isinstance(service_map, dict):
            continue
        for service in service_map:
            names.add(f"{domain}.{service}")
    return names


def state_entity_ids(states: object) -> set[str]:
    """Return entity IDs from Home Assistant's states response."""
    ids: set[str] = set()
    if not isinstance(states, list):
        return ids
    for state in states:
        if not isinstance(state, dict):
            continue
        entity_id = _optional_text(state.get("entity_id"))
        if entity_id:
            ids.add(entity_id)
    return ids


def run_live_gate(
    credentials: tuple[HACredentials, ...],
    *,
    required_services: tuple[str, ...],
    required_entities: tuple[str, ...],
    timeout: float,
) -> dict[str, Any]:
    """Run read-only live HA checks and return a sanitized summary."""
    if not credentials:
        raise HALiveGateError("no Home Assistant credentials were provided")

    errors: list[str] = []
    for credential in credentials:
        try:
            token = credential.access_token
            if credential.refresh_token:
                token = refresh_access_token(credential, timeout=timeout)
            if not token:
                raise HALiveGateError("missing access token")

            config = request_json(
                credential.url,
                "/api/config",
                token,
                timeout=timeout,
            )
            services = request_json(
                credential.url,
                "/api/services",
                token,
                timeout=timeout,
            )
            states = request_json(
                credential.url,
                "/api/states",
                token,
                timeout=timeout,
            )

            available_services = service_names(services)
            missing_services = tuple(
                service
                for service in required_services
                if service not in available_services
            )
            if missing_services:
                raise HALiveGateError(
                    "missing required services: " + ", ".join(missing_services)
                )

            available_entities = state_entity_ids(states)
            missing_entities = tuple(
                entity
                for entity in required_entities
                if entity not in available_entities
            )
            if missing_entities:
                raise HALiveGateError(
                    "missing required entities: " + ", ".join(missing_entities)
                )

            return {
                "url": credential.url,
                "session": credential.label,
                "ha_version": _optional_text(config.get("version"))
                if isinstance(config, dict)
                else None,
                "required_services": required_services,
                "required_entities": required_entities,
            }
        except Exception as ex:  # noqa: BLE001
            errors.append(f"{credential.label}: {ex}")

    raise HALiveGateError("; ".join(errors))


def refresh_access_token(credential: HACredentials, *, timeout: float) -> str:
    """Refresh a Home Assistant access token."""
    if not credential.refresh_token:
        raise HALiveGateError("missing refresh token")
    body = {
        "grant_type": "refresh_token",
        "refresh_token": credential.refresh_token,
    }
    if credential.client_id:
        body["client_id"] = credential.client_id
    response = request_json(
        credential.url,
        "/auth/token",
        token=None,
        method="POST",
        form=body,
        timeout=timeout,
    )
    if not isinstance(response, dict):
        raise HALiveGateError("token refresh returned non-object response")
    access_token = _optional_text(response.get("access_token"))
    if not access_token:
        raise HALiveGateError("token refresh returned no access token")
    return access_token


def request_json(
    base_url: str,
    path: str,
    token: str | None,
    *,
    method: str = "GET",
    form: dict[str, str] | None = None,
    timeout: float,
) -> Any:
    """Make one Home Assistant API request and parse JSON."""
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    data = None
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        raise HALiveGateError(f"HTTP {ex.code} for {path}") from ex
    except urllib.error.URLError as ex:
        raise HALiveGateError(f"request failed for {path}: {ex.reason}") from ex


def credentials_from_args(args: argparse.Namespace) -> tuple[HACredentials, ...]:
    """Build a credential list from CLI args and environment variables."""
    credentials: list[HACredentials] = []
    if args.session_file:
        credentials.extend(load_dashboard_session_credentials(args.session_file))

    url = args.url or os.environ.get("UNILED_HA_URL")
    access_token = args.access_token or os.environ.get("UNILED_HA_ACCESS_TOKEN")
    refresh_token = args.refresh_token or os.environ.get("UNILED_HA_REFRESH_TOKEN")
    client_id = args.client_id or os.environ.get("UNILED_HA_CLIENT_ID")
    if url and (access_token or refresh_token):
        credentials.insert(
            0,
            HACredentials(
                url=url,
                access_token=access_token,
                refresh_token=refresh_token,
                client_id=client_id,
            ),
        )
    return tuple(credentials)


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run read-only live HA boundary checks for UniLED Next.",
    )
    parser.add_argument("--url", help="Home Assistant base URL.")
    parser.add_argument("--access-token", help="Short-lived HA access token.")
    parser.add_argument("--refresh-token", help="Long-lived HA refresh token.")
    parser.add_argument("--client-id", help="HA OAuth client ID for refresh.")
    parser.add_argument(
        "--session-file",
        type=Path,
        help="Dashboard ha-sessions.json file to try, without printing secrets.",
    )
    parser.add_argument(
        "--require-service",
        action="append",
        default=["uniled.set_state"],
        help="Required service in domain.service form. Can be repeated.",
    )
    parser.add_argument(
        "--entity",
        action="append",
        default=[],
        help="Required entity_id to verify in /api/states. Can be repeated.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds.",
    )
    return parser


def main() -> int:
    """Run the command-line entry point."""
    args = _parser().parse_args()
    try:
        summary = run_live_gate(
            credentials_from_args(args),
            required_services=tuple(args.require_service),
            required_entities=tuple(args.entity),
            timeout=args.timeout,
        )
    except HALiveGateError as ex:
        print(f"HA live boundary gate failed: {ex}", file=sys.stderr)
        return 1

    print(
        "HA live boundary gate passed: "
        f"version={summary['ha_version']}, "
        f"services={len(summary['required_services'])}, "
        f"entities={len(summary['required_entities'])}, "
        f"session={summary['session']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
