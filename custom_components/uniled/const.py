"""Constants for UniLED Next."""

from typing import Final

DOMAIN: Final = "uniled"

CONFIG_ENTRY_VERSION: Final = 4
CONFIG_ENTRY_MINOR_VERSION: Final = 2

CONF_ADDRESS: Final = "address"
CONF_CLOUD_COUNTRY: Final = "cloud_country"
CONF_CLOUD_PASSWORD: Final = "cloud_password"
CONF_CLOUD_SKIP: Final = "cloud_skip"
CONF_CLOUD_USERNAME: Final = "cloud_username"
CONF_DEVICE_ID: Final = "device_id"
CONF_DISCOVERY_CONFIDENCE: Final = "discovery_confidence"
CONF_DISCOVERY_MATCH: Final = "discovery_match"
CONF_DISCOVERY_RESPONSE_HEX: Final = "discovery_response_hex"
CONF_DISCOVERY_SOURCE: Final = "discovery_source"
CONF_HOST: Final = "host"
CONF_MESH_KEY: Final = "mesh_key"
CONF_MESH_LTK: Final = "mesh_ltk"
CONF_MESH_NODES: Final = "mesh_nodes"
CONF_MESH_NODE_ID: Final = "mesh_node_id"
CONF_MESH_NODE_TYPE: Final = "mesh_node_type"
CONF_MESH_NODE_WIRING: Final = "mesh_node_wiring"
CONF_MESH_PASSWORD: Final = "mesh_password"
CONF_MESH_PLACE_ID: Final = "mesh_place_id"
CONF_MESH_PLACE_NAME: Final = "mesh_place_name"
CONF_MESH_UUID: Final = "mesh_uuid"
CONF_MODEL: Final = "model"
CONF_MODEL_ID: Final = "model_id"
CONF_TRANSPORT: Final = "transport"

TRANSPORT_BLE: Final = "ble"
TRANSPORT_BLE_MESH: Final = "ble_mesh"
TRANSPORT_LAN: Final = "lan"
TRANSPORT_MANUAL: Final = "manual"

DISCOVERY_CONFIDENCE_DISCOVERED_ONLY: Final = "discovered_only"
DISCOVERY_CONFIDENCE_PROTOCOL_PROVEN: Final = "protocol_proven"
DISCOVERY_CONFIDENCE_VERIFIED: Final = "verified"

DISCOVERY_MATCH_EXACT_LABEL: Final = "exact_label"
DISCOVERY_MATCH_SAFE_SUFFIX: Final = "safe_suffix"
DISCOVERY_MATCH_SPNET_MODEL_ID: Final = "spnet_model_id"
DISCOVERY_MATCH_TELINK_MESH: Final = "telink_mesh"

DISCOVERY_SOURCE_BLUETOOTH: Final = "bluetooth"
DISCOVERY_SOURCE_LAN: Final = "lan"
