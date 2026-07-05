"""Catalog loading and model resolution."""

from .registry import ModelCatalog, default_catalog
from .schema import (
    COLOR_CAPABILITY_LABELS,
    SPEC_FUNCTION_BITS,
    CatalogModel,
    ProtocolFamily,
    SupportLevel,
    TransportKind,
    color_capability_names,
    spec_function_bit_names,
)

__all__ = [
    "COLOR_CAPABILITY_LABELS",
    "CatalogModel",
    "ModelCatalog",
    "ProtocolFamily",
    "SPEC_FUNCTION_BITS",
    "SupportLevel",
    "TransportKind",
    "color_capability_names",
    "default_catalog",
    "spec_function_bit_names",
]
