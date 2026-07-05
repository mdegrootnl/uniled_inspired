"""Generate the UniLED Next model catalog from local research artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / ".codex" / "rev" / "BanlanX_3.3.1-analysis" / "model_catalog.csv"
TARGET = (
    ROOT
    / "uniled-next"
    / "custom_components"
    / "uniled"
    / "core"
    / "catalog"
    / "models.json"
)

LEGACY_UNILED_SUPPORTED = {
    "SP601E",
    "SP602E",
    "SP608E",
    "SP611E",
    "SP613E",
    "SP614E",
    "SP616E",
    "SP617E",
    "SP620E",
    "SP621E",
    "SP623E",
    "SP624E",
    "SP630E",
    "SP631E",
    "SP632E",
    "SP633E",
    "SP634E",
    "SP635E",
    "SP636E",
    "SP637E",
    "SP638E",
    "SP639E",
    "SP63AE",
    "SP63BE",
    "SP63CE",
    "SP641E",
    "SP642E",
    "SP643E",
    "SP644E",
    "SP645E",
    "SP646E",
    "SP647E",
    "SP648E",
    "SP649E",
    "SP64AE",
    "SP64BE",
    "SP64CE",
    "SP651E",
    "SP652E",
    "SP653E",
    "SP654E",
    "SP655E",
    "SP656E",
    "SP657E",
    "SP658E",
    "SP659E",
    "SP65AE",
    "SP65BE",
    "SP65CE",
}
LIMITED_SUPPORT_FAMILIES = {
    "banlanx_601",
    "banlanx_60x",
    "banlanx_v2",
    "banlanx_v3",
    "banlanx_6xx",
    "banlanx_custom_5xx",
    "zengge_mesh",
}
LEGACY_UNILED_ONLY_MODELS = (
    {
        "model_id": 0x107E,
        "parent_id": None,
        "name": "SP107E",
        "friendly_name": "SP107E",
        "home_uri": "/legacy/uniled/led_chord",
        "connect_caps": 1,
        "spec_functions": 0,
        "color_cap": 8,
        "family": "legacy_led_chord",
        "transports": ["ble"],
        "support_level": "limited",
        "legacy_uniled_supported": True,
        "features": {},
    },
    {
        "model_id": 0x110E,
        "parent_id": None,
        "name": "SP110E",
        "friendly_name": "SP110E",
        "home_uri": "/legacy/uniled/led_hue",
        "connect_caps": 1,
        "spec_functions": 0,
        "color_cap": 8,
        "family": "legacy_led_hue",
        "transports": ["ble"],
        "support_level": "limited",
        "legacy_uniled_supported": True,
        "features": {},
    },
)


def _int_or_none(value: str) -> int | None:
    if value == "":
        return None
    return int(value)


def _features(row: dict[str, str]) -> dict[str, Any]:
    raw = row["extra"]
    if not raw:
        return {}
    return json.loads(raw)


def _family(name: str, home_uri: str, connect_caps: int) -> str:
    if name == "TEST" or home_uri == "/test":
        return "placeholder"
    if name == "SP601E":
        return "banlanx_601"
    if home_uri in {"/sp801e", "/sp802e"}:
        return "banlanx_network"
    if home_uri == "/car_lights":
        return "banlanx_car_lights"
    if home_uri == "/device/fish_tank_lights":
        return "fish_tank"
    if home_uri == "/device/ble_mesh_rc":
        return "zengge_mesh"
    if home_uri == "/device/scene_ui":
        return "banlanx_scene_mesh" if connect_caps == 8 else "banlanx_scene_ui"
    if home_uri == "/sp630e":
        return "banlanx_custom_5xx" if connect_caps == 7 else "banlanx_6xx"
    if home_uri == "/sp601e" and name in {"SP602E", "SP608E"}:
        return "banlanx_60x"
    if home_uri == "/sp603e":
        return "banlanx_v3"
    if home_uri in {"/sp601e", "/sp611e", "/light_bar"}:
        return "banlanx_v2"
    return "unknown"


def _transports(family: str, connect_caps: int) -> list[str]:
    if family == "placeholder":
        return []
    if connect_caps == 7:
        return ["ble", "lan", "cloud_optional"]
    if family == "banlanx_network" and connect_caps == 3:
        return ["ble", "lan"]
    if family == "banlanx_network":
        return ["lan"]
    if family in {"banlanx_scene_mesh", "zengge_mesh"}:
        return ["ble_mesh"]
    if connect_caps == 8:
        return ["ble_mesh"]
    if connect_caps in {2, 3}:
        return ["lan"]
    return ["ble"]


def _support_level(name: str, family: str) -> str:
    if name == "TEST":
        return "filtered"
    if family in LIMITED_SUPPORT_FAMILIES:
        return "limited"
    return "recognized"


def generate() -> None:
    rows: list[dict[str, Any]] = []
    with SOURCE.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            name = row["name"]
            home_uri = row["homeUri"]
            connect_caps = int(row["connectCaps"])
            family = _family(name, home_uri, connect_caps)
            features = _features(row)
            rows.append(
                {
                    "model_id": int(row["model"]),
                    "parent_id": _int_or_none(row["parent"]),
                    "name": name,
                    "friendly_name": row["friendlyName"],
                    "home_uri": home_uri,
                    "connect_caps": connect_caps,
                    "spec_functions": int(row["specFunctions"]),
                    "color_cap": int(row["colorCap"]),
                    "family": family,
                    "transports": _transports(family, connect_caps),
                    "support_level": _support_level(name, family),
                    "legacy_uniled_supported": name in LEGACY_UNILED_SUPPORTED,
                    "features": features,
                }
            )

    rows.extend(LEGACY_UNILED_ONLY_MODELS)

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    generate()
