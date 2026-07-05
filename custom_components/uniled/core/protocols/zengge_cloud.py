"""MagicHue/Zengge mesh cloud metadata helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

from .zengge_mesh import ZENGGE_MESH_ADDRESS_NONE, ZenggeNodeContext

MAGICHUE_DEFAULT_COUNTRY = "US"
MAGICHUE_RPC_GET_MESH = "apixp/MeshData/GetMyMeshPlaceItems/ZG?userId="
MAGICHUE_RPC_GET_MESH_DEVICES = (
    "apixp/MeshData/GetMyMeshDeviceItems/ZG?placeUniID=&userId="
)
MAGICHUE_RPC_GET_BRIDGE = "apixp/Mqtt/getMasterControlData/ZG?placeUniID="
MAGICHUE_RPC_USER_LOGIN = "apixp/User001/LoginForUser/ZG"
MAGICHUE_USER_AGENT = "HaoDeng/1.5.7(ANDROID,10,en-US)"
MAGICHUE_CHECKCODE_SECRET = b"0FC154F9C01DFA9656524A0EFABC994F"

MAGICHUE_COUNTRY_SERVERS: Mapping[str, str] = {
    "AU": "oameshcloud.magichue.net:8081/MeshClouds/",
    "AL": "ttmeshcloud.magichue.net:8081/MeshClouds/",
    "CN": "cnmeshcloud.magichue.net:8081/MeshClouds/",
    "GB": "eumeshcloud.magichue.net:8081/MeshClouds/",
    "ES": "eumeshcloud.magichue.net:8081/MeshClouds/",
    "FR": "eumeshcloud.magichue.net:8081/MeshClouds/",
    "DE": "eumeshcloud.magichue.net:8081/MeshClouds/",
    "IT": "eumeshcloud.magichue.net:8081/MeshClouds/",
    "JP": "dymeshcloud.magichue.net:8081/MeshClouds/",
    "RU": "eumeshcloud.magichue.net:8081/MeshClouds/",
    "US": "usmeshcloud.magichue.net:8081/MeshClouds/",
}

BlockEncryptor = Callable[[bytes, bytes], bytes]


class ZenggeCloudError(RuntimeError):
    """Raised when MagicHue/Zengge cloud communication fails."""


@dataclass(frozen=True, slots=True)
class ZenggeCloudNode:
    """One mesh node from MagicHue cloud metadata."""

    mesh_uuid: int
    node_id: int
    node_type: int = 0
    node_wiring: int = 0
    name: str | None = None
    area: str | None = None
    mesh_key: str | None = None
    mesh_password: str | None = None
    mesh_ltk: str | None = None

    def context(self, *, address: str | None = None) -> ZenggeNodeContext:
        """Return the runtime mesh-node context for this cloud node."""
        return ZenggeNodeContext(
            node_id=self.node_id,
            node_type=self.node_type,
            node_wiring=self.node_wiring,
            address=address,
            name=self.name,
            area=self.area,
        )


@dataclass(frozen=True, slots=True)
class ZenggeCloudMesh:
    """One MagicHue mesh location with credentials and nodes."""

    mesh_uuid: int
    place_id: str | None = None
    name: str | None = None
    mesh_key: str | None = None
    mesh_password: str | None = None
    mesh_ltk: str | None = None
    nodes: tuple[ZenggeCloudNode, ...] = ()

    def contexts(self, *, address: str | None = None) -> tuple[ZenggeNodeContext, ...]:
        """Return runtime node contexts for all cloud nodes."""
        return tuple(node.context(address=address) for node in self.nodes)


def magichue_server_for_country(country: str | None) -> str:
    """Return the MagicHue mesh cloud server for a country code."""
    code = str(country or MAGICHUE_DEFAULT_COUNTRY).upper()
    return MAGICHUE_COUNTRY_SERVERS.get(
        code,
        MAGICHUE_COUNTRY_SERVERS[MAGICHUE_DEFAULT_COUNTRY],
    )


def magichue_base_url(country: str | None) -> str:
    """Return the HTTP base URL for a MagicHue country code."""
    return f"http://{magichue_server_for_country(country)}"


def magichue_headers(token: str | None = None) -> dict[str, str]:
    """Return old-UniLED-compatible MagicHue request headers."""
    return {
        "User-Agent": MAGICHUE_USER_AGENT,
        "Accept-Language": "en-US",
        "Accept": "application/json",
        "token": token or "",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip",
    }


def magichue_login_payload(
    username: str,
    password: str,
    *,
    timestamp: str,
    block_encryptor: BlockEncryptor | None = None,
) -> dict[str, str]:
    """Build the old MagicHue login payload."""
    return {
        "userID": str(username),
        "password": hashlib.md5(str(password).encode()).hexdigest(),
        "appSys": "Android",
        "timestamp": str(timestamp),
        "appVer": "",
        "checkcode": magichue_checkcode(
            str(timestamp),
            block_encryptor=block_encryptor,
        ),
    }


def magichue_checkcode(
    timestamp: str,
    *,
    block_encryptor: BlockEncryptor | None = None,
) -> str:
    """Return the old MagicHue AES-ECB timestamp checkcode."""
    padded = _pkcs7_pad(("ZG" + str(timestamp)).encode(), 16)
    encrypted = b"".join(
        _encrypt_checkcode_block(
            MAGICHUE_CHECKCODE_SECRET,
            padded[index : index + 16],
            block_encryptor=block_encryptor,
        )
        for index in range(0, len(padded), 16)
    )
    return encrypted.hex()


async def async_fetch_zengge_cloud_meshes(
    requester: Any,
    *,
    username: str,
    password: str,
    country: str = MAGICHUE_DEFAULT_COUNTRY,
    mesh_uuid: int | None = None,
    timestamp: str,
    block_encryptor: BlockEncryptor | None = None,
) -> tuple[ZenggeCloudMesh, ...]:
    """Fetch and parse MagicHue mesh metadata using an injected JSON requester."""
    base_url = magichue_base_url(country)
    login_payload = magichue_login_payload(
        username,
        password,
        timestamp=timestamp,
        block_encryptor=block_encryptor,
    )
    login = await _request_json(
        requester,
        "POST",
        base_url + MAGICHUE_RPC_USER_LOGIN,
        headers=magichue_headers(),
        json=login_payload,
    )
    login_result = _ok_result(login, "login")
    user_id = _required_text(login_result, "userId", "login")
    token = _required_text(login_result, "auth_token", "login")

    mesh_locations = await _fetch_locations(
        requester,
        base_url=base_url,
        user_id=user_id,
        token=token,
    )
    return parse_zengge_cloud_meshes(mesh_locations, mesh_uuid=mesh_uuid)


async def _fetch_locations(
    requester: Any,
    *,
    base_url: str,
    user_id: str,
    token: str,
) -> list[Mapping[str, Any]]:
    headers = magichue_headers(token)
    meshes = await _request_json(
        requester,
        "POST",
        base_url + MAGICHUE_RPC_GET_MESH + quote_plus(user_id),
        headers=headers,
    )
    result = _ok_result(meshes, "mesh fetch")
    if not isinstance(result, list):
        raise ZenggeCloudError("mesh fetch returned no location list")

    locations: list[Mapping[str, Any]] = [
        dict(item) for item in result if isinstance(item, Mapping)
    ]
    for location in locations:
        place_id = _text(location.get("placeUniID"))
        if place_id is None:
            continue
        bridge = await _request_json(
            requester,
            "GET",
            base_url + MAGICHUE_RPC_GET_BRIDGE + quote_plus(place_id),
            headers=headers,
        )
        bridge_result = _optional_ok_result(bridge)
        if bridge_result is not None:
            location["bridge"] = bridge_result

        endpoint = MAGICHUE_RPC_GET_MESH_DEVICES.replace(
            "placeUniID=",
            "placeUniID=" + quote_plus(place_id),
        ).replace("userId=", "userId=" + quote_plus(user_id))
        devices = await _request_json(
            requester,
            "GET",
            base_url + endpoint,
            headers=headers,
        )
        device_result = _ok_result(devices, "mesh device fetch")
        if not isinstance(device_result, list):
            raise ZenggeCloudError("mesh device fetch returned no device list")
        location["deviceList"] = device_result
    return locations


def parse_zengge_cloud_meshes(
    payload: Any,
    *,
    mesh_uuid: int | None = None,
) -> tuple[ZenggeCloudMesh, ...]:
    """Parse old-UniLED MagicHue mesh/location payloads into core metadata."""
    target_mesh_uuid = _optional_int(mesh_uuid)
    meshes: list[ZenggeCloudMesh] = []
    for location in _locations(payload):
        mesh = _parse_location(location, mesh_uuid=target_mesh_uuid)
        if mesh is not None:
            meshes.append(mesh)
    return tuple(meshes)


def _parse_location(
    location: Mapping[str, Any],
    *,
    mesh_uuid: int | None,
) -> ZenggeCloudMesh | None:
    place_id = _text(location.get("placeUniID"))
    name = _text(location.get("displayName") or location.get("name"))
    mesh_key = _text(location.get("meshKey"))
    mesh_password = _text(location.get("meshPassword"))
    mesh_ltk = _text(location.get("meshLTK"))

    nodes: list[ZenggeCloudNode] = []
    for item in _device_list(location):
        node = _parse_node(
            item,
            location_name=name,
            mesh_key=mesh_key,
            mesh_password=mesh_password,
            mesh_ltk=mesh_ltk,
        )
        if node is None:
            continue
        if mesh_uuid is not None and node.mesh_uuid != mesh_uuid:
            continue
        nodes.append(node)

    resolved_mesh_uuid = (
        mesh_uuid
        or _optional_int(location.get("meshUUID"))
        or (nodes[0].mesh_uuid if nodes else None)
    )
    if resolved_mesh_uuid is None:
        return None

    return ZenggeCloudMesh(
        mesh_uuid=resolved_mesh_uuid,
        place_id=place_id,
        name=name,
        mesh_key=mesh_key,
        mesh_password=mesh_password,
        mesh_ltk=mesh_ltk,
        nodes=tuple(nodes),
    )


def _parse_node(
    item: Mapping[str, Any],
    *,
    location_name: str | None,
    mesh_key: str | None,
    mesh_password: str | None,
    mesh_ltk: str | None,
) -> ZenggeCloudNode | None:
    mesh_uuid = _optional_int(item.get("meshUUID"))
    node_id = _optional_int(item.get("meshAddress"))
    if mesh_uuid is None or node_id in {None, ZENGGE_MESH_ADDRESS_NONE}:
        return None

    return ZenggeCloudNode(
        mesh_uuid=mesh_uuid,
        node_id=node_id,
        node_type=_optional_int(item.get("deviceType")) or 0,
        node_wiring=_optional_int(item.get("wiringType")) or 0,
        name=_text(item.get("displayName") or item.get("deviceName")),
        area=_text(item.get("deviceArea") or location_name),
        mesh_key=_text(item.get("meshKey")) or mesh_key,
        mesh_password=_text(item.get("meshPassword")) or mesh_password,
        mesh_ltk=_text(item.get("meshLTK")) or mesh_ltk,
    )


def _locations(payload: Any) -> tuple[Mapping[str, Any], ...]:
    if isinstance(payload, Mapping):
        if "deviceList" in payload or "placeUniID" in payload:
            return (payload,)
        result = payload.get("result")
        if isinstance(result, list):
            return tuple(item for item in result if isinstance(item, Mapping))
        if isinstance(result, Mapping):
            return _locations(result)
        return ()
    if isinstance(payload, list):
        return tuple(item for item in payload if isinstance(item, Mapping))
    return ()


def _device_list(location: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    devices = location.get("deviceList") or location.get("devices") or ()
    if not isinstance(devices, list):
        return ()
    return tuple(item for item in devices if isinstance(item, Mapping))


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text, 0)
        except ValueError:
            return None
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


async def _request_json(
    requester: Any,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str],
    json: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    try:
        response = await requester(method, url, headers=headers, json=json)
    except Exception as ex:
        raise ZenggeCloudError(str(ex)) from ex
    if not isinstance(response, Mapping):
        raise ZenggeCloudError("MagicHue response was not a JSON object")
    return response


def _ok_result(response: Mapping[str, Any], action: str) -> Any:
    if response.get("ok") is True:
        return response.get("result")
    error = _text(response.get("err_msg") or response.get("error")) or "no result"
    raise ZenggeCloudError(f"{action} failed: {error}")


def _optional_ok_result(response: Mapping[str, Any]) -> Any:
    if response.get("ok") is True:
        return response.get("result")
    return None


def _required_text(data: Any, key: str, action: str) -> str:
    if not isinstance(data, Mapping):
        raise ZenggeCloudError(f"{action} returned no result object")
    value = _text(data.get(key))
    if value is None:
        raise ZenggeCloudError(f"{action} did not return {key}")
    return value


def _pkcs7_pad(data: bytes, size: int) -> bytes:
    pad = size - (len(data) % size)
    return data + bytes((pad,)) * pad


def _encrypt_checkcode_block(
    key: bytes,
    block: bytes,
    *,
    block_encryptor: BlockEncryptor | None,
) -> bytes:
    if block_encryptor is not None:
        return bytes(block_encryptor(key, block))
    try:
        from Crypto.Cipher import AES
    except ImportError as ex:
        raise ZenggeCloudError(
            "pycryptodome is required for MagicHue checkcode AES"
        ) from ex
    return AES.new(key, AES.MODE_ECB).encrypt(block)
