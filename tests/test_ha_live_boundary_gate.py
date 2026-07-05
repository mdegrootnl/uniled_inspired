"""Live Home Assistant boundary gate helper tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from scripts.ha_live_boundary_gate import (
    load_dashboard_session_credentials,
    service_names,
    state_entity_ids,
)


def test_live_boundary_gate_parses_service_names() -> None:
    """Service responses become domain.service names."""
    services = [
        {"domain": "uniled", "services": {"set_state": {}}},
        {"domain": "light", "services": {"turn_on": {}, "turn_off": {}}},
        {"domain": "", "services": {"ignored": {}}},
        {"domain": "bad", "services": []},
    ]

    assert service_names(services) == {
        "uniled.set_state",
        "light.turn_on",
        "light.turn_off",
    }


def test_live_boundary_gate_parses_state_entity_ids() -> None:
    """State responses become entity_id sets."""
    states = [
        {"entity_id": "light.raam_strip"},
        {"entity_id": "sensor.raam_strip_effect_type"},
        {"entity_id": ""},
        {"not_entity_id": "ignored"},
    ]

    assert state_entity_ids(states) == {
        "light.raam_strip",
        "sensor.raam_strip_effect_type",
    }


def test_live_boundary_gate_loads_dashboard_sessions_without_secret_output() -> None:
    """Dashboard session files provide labels and token-bearing credentials."""
    data = {
        "abcdef123456": {
            "tokens": {
                "hassUrl": "http://homeassistant.local:8123",
                "clientId": "http://127.0.0.1:5173/",
                "refresh_token": "secret-refresh",
                "access_token": "secret-access",
            }
        },
        "ignored": {"tokens": {"hassUrl": ""}},
    }

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ha-sessions.json"
        path.write_text(json.dumps(data), encoding="utf-8")

        credentials = load_dashboard_session_credentials(path)

    assert len(credentials) == 1
    assert credentials[0].label == "abcdef12"
    assert credentials[0].url == "http://homeassistant.local:8123"
    assert credentials[0].refresh_token == "secret-refresh"
