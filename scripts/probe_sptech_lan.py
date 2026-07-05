"""Probe SPTech LAN devices with the UniLED Next protocol stack."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from custom_components.uniled.core import DeviceSession, default_catalog  # noqa: E402
from custom_components.uniled.core.protocols import SPTechLANProtocol  # noqa: E402
from custom_components.uniled.core.transports import lan_profile_for_model  # noqa: E402
from custom_components.uniled.lan import (  # noqa: E402
    UniLEDLANTransport,
    lan_device_name,
)

DEFAULT_SP541E_HOSTS = ("192.168.0.82", "192.168.0.99", "192.168.0.160")


async def _probe_host(host: str, *, probe_timeout: float) -> dict[str, Any]:
    catalog = default_catalog()
    model = catalog.resolve_name("SP541E")
    if model is None:
        raise RuntimeError("SP541E is missing from the catalog")
    profile = lan_profile_for_model(model)
    if profile is None:
        raise RuntimeError("SP541E is missing a LAN profile")

    transport = UniLEDLANTransport(
        None,
        host=host,
        name=lan_device_name(model.name, host),
        profile=profile,
        timeout=probe_timeout,
    )
    session = DeviceSession(SPTechLANProtocol(model_name=model.name), transport)
    try:
        state = await session.refresh_state(response_timeout=0)
    except Exception as ex:  # noqa: BLE001
        return {"host": host, "ok": False, "error": f"{type(ex).__name__}: {ex}"}
    finally:
        await transport.close()

    if state is None:
        return {"host": host, "ok": False, "error": "no parsed state returned"}

    channel = state.channels.get(0)
    return {
        "host": host,
        "ok": True,
        "firmware": state.firmware,
        "power": None if channel is None else channel.power,
        "brightness": None if channel is None else channel.brightness,
        "light_mode": None if channel is None else channel.light_mode,
        "effect": None if channel is None else channel.effect,
        "light_type": state.diagnostics.get("light_type"),
        "light_type_name": state.diagnostics.get("light_type_name"),
        "raw": None if state.raw is None else state.raw.hex(),
    }


async def _amain(args: argparse.Namespace) -> int:
    results = [
        await _probe_host(host, probe_timeout=args.timeout)
        for host in args.hosts
    ]
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if all(result["ok"] for result in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "hosts",
        nargs="*",
        default=DEFAULT_SP541E_HOSTS,
        help="SP541E host/IP addresses to probe",
    )
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
