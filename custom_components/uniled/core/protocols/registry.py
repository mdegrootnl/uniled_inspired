"""Protocol registry."""

from __future__ import annotations

from ..catalog import CatalogModel, ProtocolFamily
from .banlanx_legacy import (
    BanlanX2Protocol,
    BanlanX3Protocol,
    BanlanX6xxProtocol,
    BanlanX60xProtocol,
    BanlanX601Protocol,
    BanlanXCustom5xxProtocol,
    LegacyLEDChordProtocol,
    LegacyLEDHueProtocol,
    LegacyProtocol,
)


def protocol_for_model(model: CatalogModel) -> LegacyProtocol | None:
    """Return the current protocol implementation for a model, if any."""
    if model.family is ProtocolFamily.BANLANX_601:
        return BanlanX601Protocol()
    if model.family is ProtocolFamily.BANLANX_60X:
        return BanlanX60xProtocol(channels=_banlanx60x_channels(model))
    if model.family is ProtocolFamily.BANLANX_V2:
        return BanlanX2Protocol(
            model_name=model.name,
            color_cap=model.color_cap,
            spec_functions=model.spec_functions,
        )
    if model.family is ProtocolFamily.BANLANX_V3:
        return BanlanX3Protocol(
            model_name=model.name,
            color_cap=model.color_cap,
            spec_functions=model.spec_functions,
        )
    if model.family is ProtocolFamily.BANLANX_6XX:
        return BanlanX6xxProtocol()
    if model.family is ProtocolFamily.BANLANX_CUSTOM_5XX:
        return BanlanXCustom5xxProtocol()
    if model.family is ProtocolFamily.LEGACY_LED_CHORD:
        return LegacyLEDChordProtocol()
    if model.family is ProtocolFamily.LEGACY_LED_HUE:
        return LegacyLEDHueProtocol()
    return None


def _banlanx60x_channels(model: CatalogModel) -> int:
    """Return the old-UniLED physical channel count for SP60x models."""
    if model.name == "SP602E":
        return 4
    return 8
