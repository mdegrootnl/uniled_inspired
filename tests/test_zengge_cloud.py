"""MagicHue/Zengge cloud metadata parser tests."""

from __future__ import annotations

import asyncio

from custom_components.uniled.core.protocols import (
    MAGICHUE_RPC_GET_BRIDGE,
    MAGICHUE_RPC_GET_MESH,
    MAGICHUE_RPC_GET_MESH_DEVICES,
    MAGICHUE_RPC_USER_LOGIN,
    async_fetch_zengge_cloud_meshes,
    magichue_checkcode,
    magichue_headers,
    magichue_login_payload,
    magichue_server_for_country,
    parse_zengge_cloud_meshes,
)


def _identity_block_encryptor(key: bytes, block: bytes) -> bytes:
    return block


class RecordingMagicHueRequester:
    """Fake async MagicHue requester."""

    def __init__(self) -> None:
        self.calls: list[
            tuple[str, str, dict[str, str], dict[str, str] | None]
        ] = []

    async def __call__(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, str] | None = None,
    ) -> dict:
        self.calls.append((method, url, dict(headers), json))
        if url.endswith(MAGICHUE_RPC_USER_LOGIN):
            return {
                "ok": True,
                "result": {
                    "userId": "user@example.com",
                    "auth_token": "token-1",
                    "deviceSecret": "secret",
                    "nationCode": "US",
                },
            }
        if MAGICHUE_RPC_GET_MESH in url:
            return {
                "ok": True,
                "result": [
                    {
                        "placeUniID": "place-1",
                        "displayName": "Kitchen",
                        "meshKey": "CloudMesh",
                        "meshPassword": "CloudPassword",
                        "meshLTK": "CloudToken",
                    }
                ],
            }
        if MAGICHUE_RPC_GET_BRIDGE in url:
            return {"ok": True, "result": {"bridgeId": "bridge-1"}}
        if "GetMyMeshDeviceItems" in url:
            return {
                "ok": True,
                "result": [
                    {
                        "meshUUID": 0x0211,
                        "meshAddress": 0x44,
                        "deviceType": 2,
                        "wiringType": 4,
                        "displayName": "Counter Strip",
                    }
                ],
            }
        raise AssertionError(f"unexpected request: {method} {url}")


def test_magichue_login_payload_preserves_old_checkcode_shape() -> None:
    """Login payload keeps old UniLED password hash and AES checkcode inputs."""
    payload = magichue_login_payload(
        "user@example.com",
        "secret",
        timestamp="1234567890123",
        block_encryptor=_identity_block_encryptor,
    )

    assert payload == {
        "userID": "user@example.com",
        "password": "5ebe2294ecd0e0f08eab7690d2a6ee69",
        "appSys": "Android",
        "timestamp": "1234567890123",
        "appVer": "",
        "checkcode": "5a473132333435363738393031323301",
    }
    assert magichue_checkcode(
        "1234567890123",
        block_encryptor=_identity_block_encryptor,
    ) == payload["checkcode"]
    assert magichue_headers("token-1")["User-Agent"] == (
        "HaoDeng/1.5.7(ANDROID,10,en-US)"
    )


def test_async_fetch_zengge_cloud_meshes_uses_old_uniled_request_flow() -> None:
    """Live client flow fetches meshes, bridge data, and mesh devices."""
    requester = RecordingMagicHueRequester()

    meshes = asyncio.run(
        async_fetch_zengge_cloud_meshes(
            requester,
            username="user@example.com",
            password="secret",
            country="US",
            mesh_uuid=0x0211,
            timestamp="1234567890123",
            block_encryptor=_identity_block_encryptor,
        )
    )

    assert len(meshes) == 1
    assert meshes[0].mesh_key == "CloudMesh"
    assert meshes[0].nodes[0].node_id == 0x44
    assert meshes[0].nodes[0].node_wiring == 4
    assert [call[0] for call in requester.calls] == ["POST", "POST", "GET", "GET"]
    assert requester.calls[0][1] == (
        "http://usmeshcloud.magichue.net:8081/MeshClouds/"
        "apixp/User001/LoginForUser/ZG"
    )
    assert requester.calls[1][1] == (
        "http://usmeshcloud.magichue.net:8081/MeshClouds/"
        "apixp/MeshData/GetMyMeshPlaceItems/ZG?userId=user%40example.com"
    )
    assert requester.calls[2][1].endswith(
        "apixp/Mqtt/getMasterControlData/ZG?placeUniID=place-1"
    )
    assert requester.calls[3][1].endswith(
        "apixp/MeshData/GetMyMeshDeviceItems/ZG?"
        "placeUniID=place-1&userId=user%40example.com"
    )
    assert requester.calls[0][3] is not None
    assert requester.calls[0][3]["checkcode"] == (
        "5a473132333435363738393031323301"
    )
    assert requester.calls[1][2]["token"] == "token-1"


def test_parse_zengge_cloud_meshes_extracts_credentials_and_nodes() -> None:
    """Old UniLED MagicHue locations become normalized mesh metadata."""
    payload = {
        "ok": True,
        "result": [
            {
                "placeUniID": "place-1",
                "displayName": "Kitchen",
                "meshKey": "CloudMesh",
                "meshPassword": "CloudPassword",
                "meshLTK": "CloudToken",
                "deviceList": [
                    {
                        "meshUUID": 0x0211,
                        "meshAddress": 0x44,
                        "deviceType": 2,
                        "wiringType": 4,
                        "displayName": "Counter Strip",
                    },
                    {
                        "meshUUID": 0x9999,
                        "meshAddress": 0x45,
                        "deviceType": 2,
                        "wiringType": 2,
                        "displayName": "Other Mesh",
                    },
                    {
                        "meshUUID": 0x0211,
                        "meshAddress": 0,
                        "displayName": "Empty Slot",
                    },
                ],
            }
        ],
    }

    meshes = parse_zengge_cloud_meshes(payload, mesh_uuid=0x0211)

    assert len(meshes) == 1
    mesh = meshes[0]
    assert mesh.mesh_uuid == 0x0211
    assert mesh.place_id == "place-1"
    assert mesh.name == "Kitchen"
    assert mesh.mesh_key == "CloudMesh"
    assert mesh.mesh_password == "CloudPassword"
    assert mesh.mesh_ltk == "CloudToken"
    assert len(mesh.nodes) == 1
    assert mesh.nodes[0].node_id == 0x44
    assert mesh.nodes[0].node_type == 2
    assert mesh.nodes[0].node_wiring == 4
    assert mesh.nodes[0].name == "Counter Strip"
    assert mesh.nodes[0].area == "Kitchen"
    assert mesh.nodes[0].mesh_key == "CloudMesh"
    assert mesh.nodes[0].mesh_password == "CloudPassword"
    assert mesh.nodes[0].mesh_ltk == "CloudToken"

    context = mesh.nodes[0].context(address="AA:BB:CC:DD:EE:FF")

    assert context.node_id == 0x44
    assert context.node_type == 2
    assert context.node_wiring == 4
    assert context.name == "Counter Strip"
    assert context.area == "Kitchen"
    assert context.address == "AA:BB:CC:DD:EE:FF"


def test_parse_zengge_cloud_meshes_accepts_single_location_and_hex_strings() -> None:
    """Config-flow-friendly parsed JSON can be a single location mapping."""
    mesh = parse_zengge_cloud_meshes(
        {
            "placeUniID": "place-2",
            "displayName": "Office",
            "meshUUID": "0x211",
            "deviceList": [
                {
                    "meshUUID": "529",
                    "meshAddress": "0x10",
                    "deviceType": "2",
                    "wiringType": "2",
                    "deviceName": "Desk",
                }
            ],
        }
    )[0]

    assert mesh.mesh_uuid == 0x0211
    assert mesh.nodes[0].node_id == 0x10
    assert mesh.nodes[0].node_wiring == 2
    assert mesh.nodes[0].name == "Desk"


def test_parse_zengge_cloud_meshes_rejects_missing_mesh_identity() -> None:
    """Incomplete cloud data stays out of runtime node registration."""
    assert parse_zengge_cloud_meshes({"result": []}) == ()
    assert parse_zengge_cloud_meshes({"deviceList": []}) == ()
    assert parse_zengge_cloud_meshes({"deviceList": [{"meshAddress": 1}]}) == ()


def test_magichue_cloud_constants_match_old_uniled_endpoints() -> None:
    """MagicHue endpoint constants preserve old UniLED cloud routing."""
    assert magichue_server_for_country("US") == (
        "usmeshcloud.magichue.net:8081/MeshClouds/"
    )
    assert magichue_server_for_country("DE") == (
        "eumeshcloud.magichue.net:8081/MeshClouds/"
    )
    assert magichue_server_for_country("??") == (
        "usmeshcloud.magichue.net:8081/MeshClouds/"
    )
    assert MAGICHUE_RPC_USER_LOGIN == "apixp/User001/LoginForUser/ZG"
    assert MAGICHUE_RPC_GET_MESH == "apixp/MeshData/GetMyMeshPlaceItems/ZG?userId="
    assert MAGICHUE_RPC_GET_MESH_DEVICES == (
        "apixp/MeshData/GetMyMeshDeviceItems/ZG?placeUniID=&userId="
    )
    assert MAGICHUE_RPC_GET_BRIDGE == "apixp/Mqtt/getMasterControlData/ZG?placeUniID="
