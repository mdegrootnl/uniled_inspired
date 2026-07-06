# UniLED Next Technical Design Document

Status: draft  
Target: ideal Home Assistant integration for the full BanlanX 3.3.1 device
catalog

## Design Principles

- Python is the runtime language for Home Assistant.
- Home Assistant code is a thin shell around a Home Assistant-independent core.
- Protocol families own bytes and device semantics.
- Transports own connectivity and retries.
- The model catalog owns model facts, aliases, limits, and declared
  capabilities.
- APK feature packages that are present without a model-catalog device row are
  tracked separately and must not create Home Assistant entities until catalog
  and protocol evidence exists.
- APK asset-package buckets are exhaustively classified so hidden package
  surfaces are noticed during APK refreshes.
- Home Assistant entities are generated from a normalized feature plan.
- The integration must fail visibly and safely when a model is recognized but
  not yet controllable.

## APK Asset Package Inventory

The APK analysis emits `asset_package_counts.txt` plus one `assets_*.txt` file
per package bucket. The core tracks the complete inventory in
`core/apk_assets.py`: catalog device profiles, non-catalog feature packages,
shared app shell assets, shared device components, root shared assets, and
third-party assets. The audit must fail on unclassified new buckets, missing
classified buckets, shared-package count drift, or dropped representative
shared assets.

This registry is a coverage guard, not an entity source. Only catalog-backed
models and proven protocol profiles create Home Assistant entities.

## Non-Catalog Feature Packages

Some APK packages are real app surfaces but are not device families in the
model catalog. The core tracks these in `core/feature_packages.py`; the APK
evidence audit verifies their package asset count, route/storage anchors, and
continued absence from `model_catalog.raw.json` and `model_catalog.pretty.json`.
Gundam lights currently falls into this category: APK package present, catalog
device absent, command protocol unknown. These profiles are documentation and
diagnostic evidence only, not setup routes or entity plans.

## Architecture

```text
Home Assistant
  config flow, manifest, platforms, diagnostics, repairs
        |
        v
UniLED runtime
  entry runtime data, coordinators, entity planner
        |
        v
Core layer
  catalog, model resolver, feature contract, state model
        |
        +--> protocol families
        |      command builders, notification parsers, effect tables
        |
        +--> transports
               BLE, LAN, mesh, optional cloud
```

The first implementation should keep the core package inside
`custom_components/uniled/core` so HACS installation remains simple. The package
must not import `homeassistant`. If the core later becomes useful outside Home
Assistant, it can move to a separately packaged `uniled-core` distribution.

## Proposed Layout

```text
custom_components/uniled/
  __init__.py
  manifest.json
  config_flow.py
  const.py
  coordinator.py
  diagnostics.py
  repairs.py
  entity.py
  light.py
  number.py
  select.py
  sensor.py
  switch.py
  button.py
  scene.py
  bluetooth.py
  network.py
  translations/
  core/
    __init__.py
    catalog/
      models.json
      schema.py
      registry.py
      generated.py
    apk_assets.py
    cloud.py
    feature_packages.py
    protocols/
      base.py
      framing.py
      banlanx_v2.py
      banlanx_v3.py
      banlanx_60x.py
      banlanx_6xx.py
      banlanx_scene_ui.py
      banlanx_car_lights.py
      banlanx_network.py
      fish_tank.py
      zengge_mesh.py
    session.py
    transports/
      base.py
      ble.py
      lan.py
      cloud.py
    features.py
    state.py
    effects.py
    identity.py
    exceptions.py
```

## Current Home Assistant API Commitments

The Home Assistant shell must use current integration patterns:

- `ConfigEntry.runtime_data` stores the runtime object.
- `async_setup_entry` creates the runtime, validates the connection when
  practical, and forwards platforms with
  `hass.config_entries.async_forward_entry_setups`.
- `async_unload_entry` unloads platforms with
  `hass.config_entries.async_unload_platforms` and closes transports afterward.
- Config entries are changed through `hass.config_entries.async_update_entry`.
- Config flows set unique IDs before creating entries and abort duplicates.
- BLE discovery uses Home Assistant Bluetooth APIs and
  `BluetoothServiceInfoBleak`.
- Light entities declare valid `supported_color_modes` and `color_mode`.
- Color temperature is represented with Kelvin min/max and Kelvin state.
- Integration entity services are registered from integration `async_setup`
  with `homeassistant.helpers.service.async_register_platform_entity_service`.
  Do not use the old platform-local `platform.async_register_entity_service`
  path. The legacy `uniled.set_state` compatibility service targets light
  entities and delegates to runtime command/session helpers, so diagnostic-only
  models without a proven command path remain non-controllable. Its
  `transition` field is accepted for old-UniLED schema parity and is consumed
  only by RG4/Zengge control-payload mesh commands with proven gradual bytes.

## Runtime Types

```python
type UniLEDConfigEntry = ConfigEntry[UniLEDRuntime]

@dataclass(slots=True)
class UniLEDRuntime:
    catalog: ModelCatalog
    device: CoreDevice
    transport: Transport
    coordinator: UniLEDCoordinator
    entity_plan: EntityPlan
    unsubscribers: list[Callable[[], None]]
```

`UniLEDRuntime` is the only object stored in `entry.runtime_data`. The core
device and transport are closed through runtime methods during unload.

## Catalog Model

The catalog is generated into JSON and loaded by the core at startup.

```python
@dataclass(frozen=True, slots=True)
class CatalogModel:
    model_id: int
    name: str
    friendly_name: str
    parent_id: int | None
    family: ProtocolFamily
    transport_caps: int
    spec_functions: int
    color_cap: int
    max_pixel_channels: int | None = None
    max_data_length: int | None = None
    features: Mapping[str, int | bool | str] = field(default_factory=dict)
```

Catalog integrity tests must assert:

- The bundled `models.json` remains reproducible from the APK-derived
  `model_catalog.csv` plus the two explicit legacy-only old-UniLED rows.
- Every user-facing model has exactly one canonical `family`.
- Every duplicate model name maps to one canonical record or explicit variant.
- Runtime diagnostics expose the duplicate-name variant list with enough APK
  fields to recover model-ID-specific behavior later: model ID, parent ID,
  raw `connectCaps`, decoded connect-capability labels, `specFunctions`,
  decoded spec-function bit labels, `colorCap`, decoded color-capability
  labels, transports, feature keys, features, support level, which record is
  the default canonical row, and which record is selected by the config entry.
- Home Assistant diagnostic sensors expose the selected runtime model ID,
  parent ID, raw `connectCaps`, decoded connect-capability labels, raw
  `specFunctions`, decoded spec-function bit labels, raw `colorCap`, decoded
  color-capability labels, APK feature count, APK feature keys, APK feature
  key/value summary, duplicate-record variant count, and duplicate-record
  variant IDs so model-specific APK behavior stays visible outside the raw
  diagnostics download.
- Every parent reference points to an existing model or an allowed virtual
  parent.
- Every model is Full, Limited, Recognized, or Filtered.
- `TEST` is Filtered.

## Model Resolution

Resolution inputs can include:

- BLE local name.
- BLE local name with a safe suffix after a catalog name, for example
  `SP601E_AABB`, when broad Home Assistant manifest matchers have already
  triggered discovery.
- APK catalog friendly labels, which are accepted as setup input but normalized
  back to canonical catalog `name` in config-entry data.
- BLE service UUIDs.
- BLE manufacturer data.
- BLE address.
- LAN discovery payload.
- Manual host plus user-selected model and optional APK `model_id`.
- Previously stored config entry data.

Config-entry data should store both the user-facing model name and APK
`model_id`. Runtime resolution must honor a stored `model_id` when present,
reject mismatches visibly, and use the canonical name-only record only for
legacy entries or setup paths that cannot identify an exact APK row yet.
Manual config flow should accept an optional APK `model_id` and surface
`model_id`-specific errors separately from unknown display names. Runtime setup
errors must carry the same `field`/`reason` shape as setup-data validation so
Home Assistant repairs can point at `model_id` with `unknown_model_id` or
`invalid_model_id` instead of a generic config-entry failure.

Resolution output:

```python
@dataclass(frozen=True, slots=True)
class ResolvedModel:
    catalog: CatalogModel
    support_level: SupportLevel
    identity: DeviceIdentity
    protocol: Protocol
    transport_kind: TransportKind
    confidence: ResolutionConfidence
    warnings: tuple[ResolutionWarning, ...]
```

The config flow may create an entry only when confidence is high enough for the
selected setup path. Low-confidence matches must show a confirmation or require
manual model selection.

## Transport Boundary

```python
class Transport(Protocol):
    kind: TransportKind

    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def request_state(self) -> bytes | None: ...
    async def send(self, payload: bytes, *, response: bool = False) -> bytes | None: ...
    def subscribe(self, callback: Callable[[bytes], None]) -> Callable[[], None]: ...
```

Transports never parse model-specific payloads. They may frame packets if the
framing is transport-specific, but protocol families own command semantics.

The first transport boundary is implemented as a minimal async byte transport:

```python
class CommandTransport(Protocol):
    async def send(self, payload: bytes, *, response: bool = False) -> bytes | None: ...
```

`DeviceSession` in `custom_components/uniled/core/session.py` sits between
Home Assistant entities and transports. It turns high-level command methods into
protocol payloads, sends those payloads through `CommandTransport`, and owns
notification assembler state before handing complete payloads to protocol
parsers.

For refresh, `DeviceSession.refresh_state()` sends the protocol state query and
then accepts either direct response bytes from the transport or a later complete
notification assembled from BLE packets. This matches the old UniLED behavior
of sending a state query and waiting for the notification handler to mark the
update complete, while keeping the core useful for future LAN transports that
may return response bytes directly.

This boundary matches the BanlanX APK evidence: the vendor Flutter bridge uses
byte-oriented BLE calls for write characteristic value and notification
enablement, while model-specific behavior is in Flutter/native protocol data
rather than the Java GATT plugin.

### BLE Transport

- Uses Home Assistant Bluetooth for discovery and BLE device lookup.
- Uses Home Assistant-managed bleak behavior for connections.
- Supports active scanning only when needed.
- Handles write UUID, notify UUID, MTU negotiation, connection backoff, and
  stale connection cleanup.
- Provides push notifications to the protocol parser.

Initial BLE support exists in two layers:

- `custom_components/uniled/core/transports/ble.py` stores tested UUID profile
  facts for the ported legacy families. Current parity profiles use `ffe0` and
  `ffe1`; LED Chord/SP107E also accepts the issue #111 `ffb0` service with
  `ffb1` write/notify fallback, BanlanX v2 accepts the issue #105 `e0ff`
  service with the existing `ffe1` characteristic, BanlanX60X accepts the
  issue #122 `ffb0` service with `ffb1` fallback, and SP6xx additionally
  accepts service `e0ff`.
- The same module stores APK BLE evidence for direct-BLE catalog models. The
  APK exposes Flutter BLE channels such as
  `com.spled.plugins/flutter_ble/main`,
  `com.spled.plugins/flutter_ble/ble_characteristic_value_changed`, and
  `com.spled.plugins/flutter_ble/bluetooth_device_found`; Java bridge methods
  for adapter state, discovery, connection, RSSI, MTU, services,
  characteristics, notification enablement, and characteristic writes; method
  arguments such as `deviceId`, `serviceUuid`, `characteristicUuid`,
  `characteristicWriteType`, `forceWaitResponse`, `services`, and
  `clearPreDiscoveredDevices`; returned fields such as `id`, `name`, `rssi`,
  `serviceData`, `manufacturerData`, `isPrimary`, `supportWriteNoResponse`,
  `supportNotify`, and `value`; and UUID candidates `ff12`, `ff14`, `ff15`,
  `ffe0`, and `ffe1`. The normalized UUID inventory also preserves the exact raw APK
  string rows, including the extractor's trailing `2` artifacts and short
  `FF12`/`FF14`/`FF15`/`ffe0`/`ffe1` anchors, as audit evidence. These are
  diagnostics for unported direct-BLE families, not model-specific command
  profiles until UUID binding, command bytes, and notification parsers are
  proven. Direct-BLE models also expose lightweight diagnostic counts for UUID
  pool size, UUID inventory size, plugin methods, plugin arguments, plugin
  result fields, grouped scan/service/characteristic/RSSI/MTU result fields,
  adapter-state result fields, event payload fields, boolean event channels,
  plugin event hints, plugin contract hints, plugin error-code hints, plugin
  channels, BLE protocol gaps, and issue-backed advertisement fixtures. Those
  fixtures pin exact old-UniLED issue logs for SP63AE `29 10 ...`/`e0ff`, SP617E
  `17 11 ...`/`e0ff`, SP621E `0d 00 ...`/`e0ff`, SP642E `4a 10 ...`/`e0ff`,
  SP611E `10 00 ...`/`e0ff`, SP107E `1a 05 98 9e`/`ffb0`, SP608E
  `05 01 ...`/`ffb0`, and SP542E `5d 10 ...`/`ffe0`. Discovery defaults
  missing `interval` to `0`, `clearPreDiscoveredDevices` to false, and
  `aliveTime` to `10000`, and supplied service UUIDs become Android `ScanFilter`
  entries.
- `custom_components/uniled/bluetooth.py` is the Home Assistant BLE byte
  transport. It resolves a reachable BLE device by address, establishes a Bleak
  connection through Home Assistant's Bluetooth stack, starts notifications, and
  writes command bytes to the profile write characteristic. When Bleak exposes
  the remote service table, direct BLE write/notify targets are resolved under
  one of the profile's expected service UUIDs before falling back to a raw
  characteristic UUID; this mirrors the APK bridge's service-scoped
  `serviceUuid` + `characteristicUuid` calls and prevents accidental writes to
  an unrelated same-UUID characteristic. The write response flag also mirrors
  the APK bridge: `forceWaitResponse` always waits for `onCharacteristicWrite`;
  otherwise characteristics advertising Android property bit `0x04`/Bleak
  `write-without-response` are written without response, while write-only
  characteristics (`0x08`/`write`) are written with response.

Runtime setup now attaches this BLE transport lazily for address-backed entries
whose model has both a ported protocol and a known BLE profile. The first
coordinator refresh attempts a state query through the attached session; if no
status response arrives, the device remains unavailable with a diagnostic
`last_refresh_result=no_response`. Recognized diagnostic-only entries without
an attached command session must instead remain unavailable with
`last_refresh_result=no_session`, exposed as the Last refresh result
diagnostic sensor.

### LAN Transport

- Supports manual host/IP setup first.
- Adds discovery only after the discovery method is stable.
- Uses asyncio-native sockets or `aiohttp` depending on the protocol.
- Applies command serialization and per-device backoff.
- Keeps optional cloud fallback separate from local LAN control.

LAN profile support exists in
`custom_components/uniled/core/transports/lan.py`. Most LAN-capable models
still use a diagnostic `UniLEDLANTransport` holder from
`custom_components/uniled/lan.py` for configured host entries; that holder only
records the host/profile and refuses `send()` calls until a model-specific LAN
frame is proven. The `SP541E` exception opens an asyncio TCP session on the
profile's SPTech port, serializes commands, reads the 13-byte SPTech response
header plus payload, and feeds the response into `SPTechLANProtocol`. LAN
profiles record APK/catalog facts for LAN-capable models:

- `supportGetNetInfo` codes such as `37` for SP547E/SP548E and `9` for SP802E.
- `maxDataLength` values such as `185` on many custom 5xx models.
- Android host-network methods observed in the APK:
  `wifiBroadcast`, `wifiGatewayAddress`, `wifiState`, `wifiIPAddress`,
  `wifiIPv6Address`, `wifiName`, `wifiBSSID`, and `wifiSubmask`.
- Discovery leads from `network_info_plus`, multicast lock handling, and
  Bonsoir/Android NSD broadcast/discovery code.
- Exact Android/Flutter bridge anchors:
  `dev.fluttercommunity.plus/network_info`,
  `com.spled.plugins/multicast_lock`, `acquire_multicast_lock`,
  `release_multicast_lock`, `held_multicast_lock`, `broadcast.initialize`,
  `broadcast.start`, `broadcast.stop`, `discovery.initialize`,
  `discovery.start`, `discovery.stop`, and Bonsoir arguments `service.name`,
  `service.type`, `service.port`, `service.host`, and `service.attributes`.
- Universal network setup flow anchors from `libapp.so`:
  `/device/universal/network/config`, `Configure device network`,
  `Device network status`, the phone-network prerequisite, AP/STA button
  instructions for Bluetooth and AP setup states, the not-yet-networked
  warning, unavailable-network warning, and cloud/voice-assistant binding
  warnings. These are setup-flow diagnostics, not local command frames.
- SP801E also has three APK setup-guide images in
  `packages/module_home/assets/images/net_config_guide/`:
  `sp801e_init.png`, `sp801e_ble.png`, and `sp801e_ap.png`. These may be
  exposed as the diagnostic `lan_network_setup_guide_asset_count`; they are
  setup evidence only and do not prove a LAN discovery response or command
  frame.
- mDNS/datagram constants recovered from the decompiled Java layer:
  multicast group `224.0.0.251`, mDNS port `5353`, TTL `255`, TXT query
  timeout `2000 ms`, TXT record type `16`, TXT query class `32769`, TXT
  receive buffer `1024 bytes`, generic UDP socket timeout `8000 ms`, and UDP
  receive buffer `2000 bytes`. The TXT query helper encodes
  `service.name`, `service.type`, and `local`, retries on local port `5353`
  after an ephemeral-port timeout, and updates service attributes when the
  parsed TXT map changes.
- Decompiled Bonsoir event marshalling exposes discovery events
  `discoveryStarted`, `discoveryServiceFound`, `discoveryServiceResolved`,
  `discoveryServiceResolveFailed`, `discoveryServiceLost`,
  `discoveryStopped`, `discoveryUndiscoveredServiceResolveFailed`,
  `discoveryTxtResolved`, `discoveryTxtResolveFailed`, and `discoveryError`.
  Event payloads use top-level `id` plus nested `service` fields:
  `service.name`, `service.type`, `service.port`, `service.host`, and
  `service.attributes`. Android NSD service types ending in `.` are trimmed,
  hosts are emitted as `getHostAddress()` strings, TXT byte values are decoded
  as UTF-8, null TXT values become empty strings, and `resolveService` calls are
  serialized through a plugin queue.
- Raw socket and discovery-status anchors recovered from `libapp.so`, including
  `RawDatagramSocket:onDone`, `RawDatagramSocket:onError ->`,
  `Socket_AvailableDatagram`, `_makeDatagram@16069316`, closed-socket and
  socket-bind error strings, `delay stop discovery>>>>>>>`, `reported data:`,
  and `unresolved discovery response from`. These prove socket/discovery
  plumbing only, not a command frame.
- Home Assistant diagnostic sensors expose compact evidence counts/values for
  `lan_host_setup_mode`, `lan_host_network_method_count`,
  `lan_discovery_plugin_count`, `lan_discovery_channel_count`,
  `lan_network_setup_route_count`, model-specific
  `lan_network_setup_guide_asset_count` when present,
  `lan_network_setup_prompt_count`,
  `lan_network_cloud_setup_prompt_count`, `lan_multicast_lock_method_count`,
  `lan_bonsoir_method_count`, `lan_bonsoir_argument_count`,
  `lan_bonsoir_nsd_method_count`,
  `lan_bonsoir_discovery_event_count`,
  `lan_bonsoir_service_event_field_count`,
  `lan_bonsoir_service_normalization_hint_count`,
  `lan_bonsoir_service_type_flow_hint_count`,
  `lan_bonsoir_txt_query_flow_hint_count`, `lan_discovery_gap_count`,
  `lan_raw_socket_hint_count`, `lan_discovery_status_hint_count`,
  `lan_udp_socket_timeout_ms`, `lan_udp_receive_buffer_bytes`,
  `lan_mdns_txt_query_timeout_ms`, `lan_mdns_txt_record_type`,
  `lan_mdns_txt_query_class`, and `lan_mdns_txt_buffer_bytes`.

Targeted APK and Blutter/static string searches have not recovered a concrete
DNS-SD service type (`_tcp`/`_udp`), model-specific TXT attribute schema,
Art-Net payload, SP802E LFX BLE/LAN envelope, or status parser offsets. The
Bonsoir keys and datagram sockets therefore remain discovery plumbing evidence,
not a command protocol for those families.

Until a socket protocol is proven, LAN profiles must report
`command_protocol_known=False` and `discovery_confirmed=False`. Home Assistant
setup should therefore prefer manual host/IP and diagnostics over automatic LAN
control for those models. The `lan_host_setup_mode` diagnostic should report
`manual_host` until discovery is proven. A host-backed runtime may report
`lan_transport_ready=True`, but `session_ready` must remain false and command
entities must stay hidden until the packet protocol is mapped. `SP541E` is the
current exception: its LAN profile reports `command_protocol_known=True` and
`discovery_confirmed=True`, `lan_host_setup_mode` reports `discovery_ready`,
and an attached host runtime reports a command session. Its SPNet setup-data
helper may also create a verified LAN entry from model byte `0x5c` plus the
source host, using the response MAC as the legacy-compatible bare config-entry
unique ID when present. Home Assistant startup discovery feeds matching SPNet
UDP responses into that same config-flow path after sending limited broadcast
plus locally derived `/24` directed broadcasts.

Custom 5xx LAN profiles have one stronger discovery-specific exception:
SP541E live testing and the BanlanX 3.3.1 arm64 Flutter AOT output prove the
SPNet UDP discovery request `53704e65740000200000000002e0` on port `6454` and
response prefix `53704e6574000021000000000001`; the live HA-host response
places the SP541E model ID `0x5c` at payload offset `3`, the network MAC at
payload offsets `5..10`, and the `SP541E` name after the name-length byte. TCP
`8587`, `SPTECH\0`, and the 13-byte response header are now implemented for
SP541E LAN state refresh and basic commands. Live testing proved all three
local mono SP541E strips can be queried and controlled when no other controller
owns the socket; zero-byte read-only responses indicate session contention. Do
not generalize this SPNet/SPTech path to other LAN-capable families without
their own model-byte mapping and command/session evidence.

Old UniLED `origin/dev_v3` and tag `3.0.10-beta.11` add a useful SPTech LAN
recognition table for custom 5xx models: `0x4e` -> `SP530E`, `0x56` ->
`SP538E`, `0x57` -> `SP539E`, `0x63`/`0x69` -> `SP548E`, and `0x64` ->
`SP549E`, plus 16 configuration-code hints for the SP530E PWM/SPI and
SP538E/SP548E/SP539E/SP549E SPI variants. The same dev branch gives those
SPTech NET RGB/RGBW profiles a richer custom-effect surface: custom-solid
effect `0x13` is `Firework`, SP530E uses that richer surface only on its
`0x86`/`0x88` SPI variants, and the fixed SP538E/SP548E `0x06` plus
SP539E/SP549E `0x08` profiles use the gradient-capable SP5XXE mode table.
These are implemented as structured diagnostics, count sensors, and
model-scoped custom 5xx status/select options only. They help support bundles
identify what a future LAN response is probably saying, but they do not make
non-SP541E LAN commands safe. SPNet responses carrying one of these legacy
codes can create a `discovered_only` LAN entry only after config-flow
confirmation, preserving the host/MAC/model evidence while attaching the
guarded diagnostic LAN holder.
Issue #115 adds a separate catalog-model diagnostic path: SPNet responses whose
model byte maps directly to a custom 5xx APK LAN row, such as SP525E model code
`113`, may also create a confirmation-required `discovered_only` LAN entry when
the optional packet name agrees with the catalog row. This preserves discovery
evidence without implying the non-SP541E LAN command/session contract is known.
Setup-data can consume either raw SPNet UDP bytes or a structured SPNet summary
with `model_code`, `mac_address`, `local_name`, and `ip_address`; this pins
old-UniLED issue #91/#123 SP548E model-code `148` reports as the same
catalog-model diagnostic path, still with LAN writes disabled.
The old shared `sptech_model.py` command/status schema is also retained in the
LAN profile: 20 command IDs and eight status chunk decoder labels. These are
diagnostic evidence for future parser/control work, not enabled write support.

The `network_info` diagnostic sensor is intentionally evidence-first. If live
device network data is present in runtime diagnostics, expose that value. Until
the query command is proven, fall back to the APK/catalog code and protocol
status, for example `supportGetNetInfo=9; command_protocol_pending`. SP541E
reports the SPTech LAN protocol as ready separately from these unresolved
network-info query bytes. The SPTech LAN parser now decodes old-UniLED status
chunk `6` as length-prefixed network strings and surfaces
`ssid=<value>; ip=<value>` when a status response includes it; malformed chunk
`6` data records a parse-error diagnostic without dropping the rest of the
status response. The same parser records old-UniLED chunk `7` as the raw
`power_fun_switch` byte when present; empty chunk `7` data records a
parse-error diagnostic and remains read-only. Repeated SPTech chunk types are
preserved so chunk `4` timer records do not collapse by type; timers are exposed
as parsed diagnostic records only. Chunk `5` is parsed into effect layout,
matrix dimensions/layout, strip music segment metadata, and raw matrix-mode
records, again without enabling any write path. The status parser also preserves
the old-UniLED SPTech chip-order byte from the mode/status chunk, and the
protocol now has old-UniLED SPTech frame builders for on/off animation,
coexistence, on-power, static/dynamic RGB, static/dynamic CCT, light-type
reconfiguration, and chip order (`0x08`, `0x0a`, `0x0b`, `0x52`, `0x57`,
`0x60`, `0x61`, `0x6a`, and `0x6b`) for future LAN work; the non-SP541E LAN
runtime guard remains unchanged. SPTech status tails now preserve old-UniLED
DIY solid slot metadata from chunk `2` and DIY solid plus gradient slot
metadata from chunk `3` as diagnostics only; unknown gradient tail bytes are
kept for support bundles, and DIY edit/save commands remain unproven.
Unhandled SPTech chunks are also retained as bounded diagnostic records with
type, index, size, sampled hex, and printable ASCII runs. The current live
chunk `10` capture contains a firmware-looking `V3.0.11` run, but it remains
an unknown firmware/status block until a schema or write path is proven.

Direct BLE evidence also includes the decompiled Android plugin call and event
contracts: characteristic discovery requires `serviceUuid`; notification
subscription requires `serviceUuid` and `characteristicUuid` and defaults
`enabled` to false; connection defaults missing `timeout` to zero; MTU requests
require `value`; writes require `serviceUuid`, `characteristicUuid`, and
`value`, default `forceWaitResponse` to false, and map provided
`characteristicWriteType` values to Android write types. Seven argument/default
anchors are audited as `ble_plugin_contract` string evidence; discovery
defaults and cached-device behavior are tracked as Java-decompile-only plugin
contract hints. Event payload facts are tracked separately: discovery emits
`id`, `name`, `rssi`, `serviceData`, and `manufacturerData`; connection state
emits `deviceId` and `connected`; notification emits `deviceId`, `serviceUuid`,
`characteristicUuid`, and `value`, and notification enablement writes the
standard CCCD descriptor
`00002902-0000-1000-8000-00805f9b34fb`. The notification channel and four
payload fields are audited as five `ble_notification_contract` string anchors;
discovery/connection payloads, the CCCD descriptor, and Java-only error codes
remain structured decompiled evidence, not native-string audit anchors. The
recovered BLE error ledger covers adapter-not-open `10000`, adapter unavailable
`10001`, missing cached device `10002`, connection failure `10003`, missing
service `10004`, missing characteristic `10005`, unconnected device `10006`,
generic BLE operation failure `10008`, connection timeout `10012`, and missing
required argument `10013`.
The adapter-state request result has boolean `available` and `discovering`
fields, while adapter-state and discovery-state event channels emit booleans.
Service discovery result maps expose `uuid` and `isPrimary`; characteristic
discovery result maps expose `uuid` plus the five characteristic capability
booleans; RSSI and MTU calls return `rssi` and `value` respectively. These
facts describe the bridge contract only. Start discovery defaults `interval=0`,
`clearPreDiscoveredDevices=False`, and `aliveTime=10000`, optionally filters by
supplied service UUIDs, and uses report delay only when batching is supported.
None of these facts may be used to bind unported `ff12`/`ff14`/`ff15` UUID
candidates or unlock commands without family-specific packet evidence.
The runtime must expose this distinction explicitly: `ble_uuid_binding_status`
summarizes known versus pending service/write/notify bindings,
`ble_known_service_uuid_count` and `ble_known_service_uuids` report proven
service UUIDs, `ble_known_write_uuid` and `ble_known_notify_uuid` show the
primary bound characteristic UUIDs or `pending`, and `ble_apk_uuid_pool`
records the raw APK candidate pool. That pool is split into
`ble_unbound_uuid_candidate_count=3`/`ble_unbound_uuid_candidates` for
`ff12`/`ff14`/`ff15` plus
`ble_legacy_uuid_candidate_count=2`/`ble_legacy_uuid_candidates` for
old-UniLED-backed `ffe0`/`ffe1`.

Optional-cloud catalog models also have APK-derived BanlanX cloud profile facts
in `custom_components/uniled/core/cloud.py`. This module is intentionally
separate from both LAN transport profiles and old-UniLED MagicHue/Zengge cloud
metadata. It records the BanlanX Flutter `libapp.so` endpoint evidence:
`https://app.ledhue.com/spiot2`, `/spiot/banlanx2`, `/spiot/els/v1`,
account auth/lifecycle routes such as `/auth/refresh-token`,
`/auth/sign-in`, `/auth/signIn2`, `/auth/signUp2`, `/user/sign-out`,
password-token routes, `/home/device/auth/*`, `/home/device/add`,
`/home/device/fw_new_version`, `/home/device/ota`, `/home/device/reset`,
`/user/device/post/raw`, `/user/device/connection/cloud/check`,
local-device registration routes, manual/resource routes, and Alexa
account-linking paths. It also records raw
`document.ledhue.com` privacy/agreement/FAQ URL strings and auth-token string
hints including `init:token`, `user:token`, `user:refresh_token`,
`refreshToken2`, `setupAuth`, `serverAuth`, and `resetAuth`, plus HTTP/header
and signature/nonce anchors including `Authorization`, `Bearer`, `S-AccessKey`,
`S-AppVer`, `S-AppVerName2`, `S-SysCode`, `S-SysName`, `S-System`,
`S-Timestamp`, `content-type:`, `application/json`, `buildSignature`,
`, buildSignature:`, `, nonce =`, `encrypt nonce =`, and `decrypt nonce =`,
plus device-identity and schema hints such as `deviceCode`, `deviceUdids =`,
`device_udid`, `device_key`, `device_to_group_mapping`, and
`mobile_device_identifier`. The APK evidence audit verifies these 97 literal
cloud anchors. The same route anchors are exposed as a 52-row
`endpoint_inventory` in diagnostics, grouped
as account auth, device auth, root/home/user/local device, BT mesh, content,
and voice assistant endpoints. Inventory rows intentionally keep HTTP method,
auth requirement, and base URL binding as `unknown`/`unproven`/`unresolved`
until stronger evidence maps each route to a concrete request contract. Until
the BanlanX account token flow, required header/signature contract, token
refresh semantics, region routing, and
`/user/device/post/raw` command envelope are proven, this profile must remain
`command_protocol_known=False` and diagnostics-only. The Home Assistant shell
exposes compact diagnostics for base URL count, grouped endpoint count,
endpoint inventory count, endpoint group count, command-related endpoint count,
unresolved base URL endpoint count, unproven auth endpoint count,
device-auth/account-auth/content/voice/document counts, `/home/device`
lifecycle count, `/user/device` count, local-device registration count,
`/user/btmesh` count, root device-route count, auth-token hint count,
device-identity hint count (`cloud_device_identity_hint_count=10`),
HTTP-header hint count (`cloud_http_header_hint_count=11`), signature hint
count, request-contract hint count (`cloud_request_contract_hint_count=26`),
split token/header/signature contract counts
(`cloud_token_contract_hint_count=10`, `cloud_header_contract_hint_count=11`,
`cloud_signature_contract_hint_count=5`), transport/gap counts, and the recovered
`/user/device/post/raw` path; the path is evidence only, not an enabled cloud
command service. Optional-cloud support disposition also reports
`account_token_schema_pending`, `request_signing_headers_pending`,
`region_reauth_contract_pending`, `raw_command_json_envelope_pending`, and
`device_bind_ownership_lifecycle_pending`, with
`cloud_command_blocker_count=5` tracking those command blockers as
diagnostics.

SP801E/SP802E also have APK-derived network-controller profile facts in
`custom_components/uniled/core/network.py`. These facts are separate from the
LAN transport because they describe the Flutter feature surfaces, not a proven
socket command protocol:

- `SP801E` maps to `packages/module_sp801e`, `/sp801e`, Art-Net settings, port
  configuration, LED layout, scene/playlist editing, graffiti, DXF import, and
  content creation modes for regular effects, image, GIF, graffiti, music,
  text, and video. Native strings also expose `getNetworkInfo`,
  `getArtNetConfig`, `setArtNetConfig`, playlist methods, `ArtNetConfig`
  port/universe fields, an `artnet config` debug label, and DXF import limits
  of no more than 4 ports and 1024 LEDs per port.
  Raw SP801E storage labels such as `channel`, `sp_channel_group`,
  `channel_index`, `portDriverType`, `portId`, `portNo`, `port_id`,
  `music/playlist`, and `scene_playlist_action_bar` are preserved as
  diagnostics only. Planned disabled selectors expose the exact APK strings for
  Art-Net fields (`portActions`, `portUniverseCounts`, `protocolVersion`,
  `startUniverse`), port fields (`channel_index`, `sp_channel_group`,
  `portDriverType`, `portId`, `portNo`, `port_id`), and playlist actions
  (`getPlaylistList`, `addPlaylist`, `updatePlaylist`, `removePlaylist`).
- `SP802E` maps to `packages/sp802e`, `/sp802e`, `/sp802e/settings`, and
  `/sp802e/edit_led_layout`. Its assets expose LFX, material/favorite, regular,
  animation, GIF, graffiti, image, text, rhythm, LED panel layout, DIY
  gradient, and color-editing surfaces, plus 20 regular LFX effect icons and
  30 GIF preview assets. Native strings expose `getNetworkInfo` plus
  LFX/matrix setters such as `setLfxMode`, `setLfxSpeed`,
  `setLfxPixelCount`, `setLfxLoopMode`, `setLfxColor`, `setLfxGradient`,
  `setLedPanelLayout`, and `setMatrixMusicMode`. Planned disabled
  matrix-music controls expose the exact
  setter anchors `setMatrixMusicMode`, `setMatrixMusicDotColor`,
  `setMatrixMusicColColor`, `setMatrixMusicColColorType`, and
  `setMatrixMusicColGradientColor`. ELF `.dynsym` inspection of
  `libwled_lfx.so` found 186 named dynamic symbols and 35 audited
  matrix/effect/LFX/generator-related exports,
  including `setup_matrix_layout`, `switch_lfx_mode`,
  `initRegularLfxGenerator`, `set_effect_params`, `recover_effect_param`,
  `render_frame`, `get_frame_data`, `setPixelColorXY`, `getPixelColorXY`,
  `setLineColorXY`, and regular-effect generator functions. Dedicated
  diagnostics now separate native library/export hints from frame-buffer helper
  anchors such as `addPixelColorXY`, `fadePixelColorXY`, `sysMatrixW`, and
  `sysMatrixH`. They also split LFX parameter/mode-switch anchors
  (`switch_lfx_mode`, `set_effect_params`, `recover_effect_param`,
  `effect_prj`, `Create_effectsTables`, `EFFECT_GENERATOR_CONSTRUCTORS`,
  `Dyneffect_num`, `Rhyeffect_num`), regular-effect generator functions,
  matrix/mode anchors (`setup_matrix_layout`, `mode_2Dmatrix`,
  `mode_2Dmusicsoap`, `mode_2Dmusicsquaredswirl`, `sysMatrixW`, `sysMatrixH`,
  `staRGBIC`, `RGBCW`), and pixel/frame helpers (`render_frame`,
  `get_frame_data`, `setPixelColorXY`, `getPixelColorXY`, `setLineColorXY`,
  `addPixelColorXY`, `fadePixelColorXY`, `fillGradientRGB`,
  `wled_DrawCircle`). Detailed symbol inspection places `set_effect_params` at
  `0x0000a4dd` with a 26-byte exported function body and preserves six exact
  `libwled_lfx.so` detail anchors as structured diagnostics. `RGBCW` is
  preserved as a native string anchor, not a `.dynsym` export. These exports are
  implementation anchors, not BLE/LAN command envelopes. Raw SP802E state
  labels such as `lfxDurationInLoop`, `lfxLoopMode`, `lfxParams`,
  `gif_lfx_frames`, `led_matrix_info`, `matrixType`, `wifiState`, and
  `wifiStrength2` are preserved as diagnostics only.

Both network-controller profiles include an explicit protocol gap noting that
no concrete DNS-SD service type was recovered from the APK string surfaces.
Support disposition also reports the shared blockers
`network_discovery_pending`, `network_socket_frame_pending`, and
`network_dns_sd_service_pending`; `SP801E` adds
`network_artnet_config_pending`, `network_playlist_packet_pending`,
`network_dxf_import_pending`, and `network_panel_layout_pending`, while
`SP802E` adds `network_lfx_packet_pending`,
`network_lfx_status_parser_pending`, `network_panel_layout_pending`, and
`network_matrix_music_pending`. The diagnostic
`network_command_blocker_count=7` is a status summary only, not command
support.

### Mesh Transport

- Owns mesh session setup, group addressing, retries, and device fan-out.
- Exposes each controllable target as a core device or channel where possible.
- Keeps remotes and accessories represented even when they do not create light
  entities.

Initial BLE mesh profile facts exist in
`custom_components/uniled/core/transports/mesh.py`. For RG4/Zengge-style mesh,
old UniLED provides the Telink UUID set:

- service `00010203-0405-0607-0809-0a0b0c0d1910`
- status `00010203-0405-0607-0809-0a0b0c0d1911`
- command `00010203-0405-0607-0809-0a0b0c0d1912`
- OTA `00010203-0405-0607-0809-0a0b0c0d1913`
- pair `00010203-0405-0607-0809-0a0b0c0d1914`

The old Zengge path requires a pairing/session-key step and then encrypted
command packets. It also discovers mesh IDs and node IDs from Telink
manufacturer data. The new core therefore exposes profile diagnostics first and
must not attach the normal BLE byte transport to RG4 as if it used the BanlanX
`ffe1` style protocol.

The APK `packages/accessories` surface is represented in the RG4 mesh profile
as diagnostics only. It preserves `/device/ble_mesh_rc`,
`/device/ble_mesh_rc/provisioning_guide`, fast-provisioning guide assets,
RG4 reconnect/zone images, provisioning callback state names such as
`provisioningStart` through `provisioningFailed`, and native strings including
`provisioner_uuid`, `provisioningCapabilities`, the 90-second provisioning
timeout, provisioning-control warning, rapid-flash abnormal state, provisioned
device count, provisioner address log, capabilities PDU anchor, and
provisioning error labels. The APK evidence audit verifies 12 literal
`rg4_provisioning` anchors. The same APK/native ledgers expose six Bluetooth
SIG Mesh provisioning/proxy UUID string anchors (`1827`, `1828`, and
`2ADB`-`2ADE`); runtime diagnostics normalize these as
`mesh_sig_mesh_uuid_hint_count=6`, but they are not a model-specific packet
sequence. These facts are enough to keep the vendor-app
workflow visible in diagnostics, but they are not packet frames:
one-touch provisioning, zone routing, and remote-button events must stay hidden
until local BLE-mesh payloads or reliable captures prove the command/event map.

The Blutter-recovered BanlanX app-command enum also gives both mesh profiles 12
diagnostic command-intent anchors:
`getCompositionData=0x02`, `configProvisoner=0x23`,
`configZoneKeyAddrMapping=0x24`, `getMeshNodeUnicastAddress=0x26`,
`identify=0xC0`, `bindGroup=0xC1`, `unbindGroup=0xC2`,
`subscribeSubgroup=0xC3`, `opUnsubscribeSubgroup=0xC4`,
`saveGroupConfig=0xC5`, `assignFrameSyncMaster=0xC7`, and
`toggleMasterSlaveHeartbeat=0xC8`. Runtime exposes these as
`mesh_app_command_id_count=12`. They are app-layer enum IDs only; they do not
prove the BLE-mesh envelope, opcode payload layout, provisioning flow, or event
notifications.

The old packet layer is now ported into
`custom_components/uniled/core/protocols/zengge_mesh.py`. It preserves old
UniLED's reversed-key AES block convention, checksum construction, stream
payload crypting, command packet layout, pairing packet, session-key
derivation, and CRC16 helper. The module imports without AES installed, but
real packet crypto requires `pycryptodome>=3.17`, which the manifest now
declares.

The same module now builds old-UniLED-compatible Zengge command packets for
status notification setup, fallback status query, power, brightness, RGB, CCT,
warm white, and effect selection. The effect packet preserves old UniLED's
`0xED [0xff, effect, speed, level]` payload shape; old UniLED defaulted public
effect changes to `speed=0` and `level=100`. Guarded effect speed and effect
level number entities resend the current effect packet with the edited byte
for paired command nodes. These builders sit below the runtime mesh
connection: they need a paired mesh session key and target node ID, and they do
not by themselves make every RG4 Home Assistant command entity safe to expose.
For the five control-payload-backed commands, the builders preserve the old
delay and gradual-transition fields in tenths of a second. Home Assistant
`transition` is mapped only to the gradual field for power, brightness, RGB,
CCT, and warm-white mesh commands; the separate effect packet does not receive
transition bytes without new packet evidence.

The module also parses old-UniLED-compatible decrypted `0xDC` status
notifications into normalized core state. Each notification contains two
five-byte node blocks with node ID, online status, brightness percentage,
packed mode/value bits, and a value byte. The parser preserves the old HSV
scale (`hue/255`, `saturation/63`), the 2800K-6500K CCT percentage scale,
panel/bridge metadata handling, old-UniLED strip/bulb/panel role labels from
node type `2`/`5`/`35`, and node diagnostics. The mesh session and coordinator
can now feed encrypted notifications into runtime state; Home Assistant entity
availability still needs the node-planning layer.

A core-only `ZenggeMeshSession` now sits above those packet helpers. It stores
pairing randoms, validates pair replies, derives the mesh session key, builds
paired node commands, registers node metadata, and applies decrypted or
encrypted notifications into normalized state. This is not the Home Assistant
BLE mesh transport yet: the transport still needs characteristic-specific
writes for pair/status/command UUIDs, node selection by RSSI, cloud credential
loading, retry behavior, and entity gating.

The required transport shape is now captured as a core-only
`ZenggeMeshTransport` protocol plus a `ZenggeMeshConnection` adapter. Unlike
the existing BanlanX BLE transport, it has distinct methods for the pair
characteristic, status characteristic, and command characteristic. The Home
Assistant/Bleak implementation satisfies that contract and feeds notifications
back into `ZenggeMeshSession.apply_encrypted_notification()`.
The connection adapter now also exposes command methods for power, brightness,
RGB, color temperature, warm white, and dynamic effects, each wrapping the
old-UniLED-compatible packet builders.

The first Home Assistant-side implementation is
`UniLEDZenggeMeshTransport` in `custom_components/uniled/bluetooth.py`. It uses
the Telink/Zengge pair, status, and command UUIDs separately, keeps Home
Assistant/Bleak imports lazy for testability, and forwards encrypted status
notifications into the provided callback. Runtime setup now creates a
`ZenggeMeshSession`, loads mesh credentials, pairs through the separate mesh
connection path, and keeps node commandability separate from normal BanlanX
`DeviceSession` readiness.

`UniLEDRuntime` can now attach a Zengge mesh transport through a separate mesh
path.
That stores a `ZenggeMeshSession` and `ZenggeMeshConnection`, registers any
node ID/type captured during Bluetooth discovery, reports mesh transport and
pairing status in diagnostics, and closes the mesh transport during unload.
It deliberately leaves the normal `session_ready` property false so existing
BanlanX command entities do not mistake RG4 for a single-UUID byte-session
device.

Runtime-level Zengge command helpers now accept an explicit node ID and send
power, brightness, RGB, Kelvin CCT, warm-white, and dynamic effect commands
through the paired mesh connection. They only operate after pairing and only
for known command-capable nodes from discovery context or parsed mesh state;
bridge/panel nodes and unknown IDs are rejected before any transport write.
After a successful write, they update the targeted node's optimistic
`ChannelState` and mesh command diagnostics without setting `session_ready`.
`command_light_features()` now turns paired known command-capable mesh nodes
into runtime light features. The Home Assistant light platform uses those
features to create one mesh node light per known node, with availability tied
to `mesh_session_paired` plus node eligibility. Mesh light turn-on/off dispatch
uses the guarded runtime helpers, while normal BLE lights still use
`DeviceSession`. Mesh-node lights advertise `LightEntityFeature.TRANSITION`
and pass HA transition seconds through the old Zengge gradual field for
control-payload-backed commands only. `command_select_features()` uses the same
mesh gate to expose one paired-node effect select backed by the old-UniLED
effect table and guarded mesh effect command helper; other mesh selects and
switches remain hidden.
The `mesh_role` diagnostic reports transport readiness, pairing state, total
known nodes, command-capable nodes, strip nodes, bulb nodes, panel nodes, and
bridge presence from already-known context/parser metadata, without creating
command entities for non-light mesh roles. The same metadata is also exposed as
structured diagnostic sensors: `mesh_known_node_count`,
`mesh_command_node_count`, `mesh_strip_node_count`, `mesh_bulb_node_count`,
`mesh_panel_node_count`, and `mesh_bridge_seen`. Known RGB/CCT panel nodes now
also create diagnostic status sensors that report old-UniLED `Online`/`Offline`
values from parsed notification blocks.

`async_setup_entry` now routes transport attachment through a shared helper.
Regular BLE protocol-backed models still receive the normal `DeviceSession`;
RG4/Zengge entries with a BLE address receive the mesh transport holder. The
coordinator has a separate encrypted mesh notification callback so paired
sessions can feed decrypted status into normalized state without treating RG4
as a BanlanX `ffe1`-style device.

Mesh credentials are represented as optional `mesh_key` and `mesh_password`
entry data. Runtime pairing defaults to old UniLED's `ZenggeMesh` and
`ZenggeTechnology` values when those fields are absent, but uses entry-provided
credentials when present and redacts them from diagnostics. `mesh_ltk` is also
redacted when present. Cloud login fields `cloud_username` and
`cloud_password` must also be redacted whenever they appear in entry data.

Old UniLED's MagicHue cloud path is captured in
`custom_components/uniled/core/protocols/zengge_cloud.py`. It preserves the
country-server routing, login MD5 password hashing, AES-ECB `checkcode`
construction for `ZG + timestamp`, and the core endpoint paths:
`apixp/User001/LoginForUser/ZG`,
`apixp/MeshData/GetMyMeshPlaceItems/ZG?userId=`,
`apixp/MeshData/GetMyMeshDeviceItems/ZG?placeUniID=&userId=`, and
`apixp/Mqtt/getMasterControlData/ZG?placeUniID=`. Parsed location payloads
retain `meshKey`, `meshPassword`, `meshLTK`, `placeUniID`, and `displayName`;
device-list entries retain `meshUUID`, `meshAddress`, `deviceType`,
`wiringType`, `displayName`, and inherited area/credential data. The live
client function uses an injected async JSON requester so Home Assistant can
provide its shared aiohttp session while tests use a fake requester.

`zengge_cloud_setup_entry_data()` can now convert parsed cloud mesh metadata
into config-entry data. `UniLEDRuntime.attach_zengge_mesh_transport()` consumes
that data by registering cloud node contexts before pairing, so paired node
light features get cloud-provided names and old-UniLED wiring semantics such as
RGB+CCT or RGB+white. Bluetooth-discovered RG4/Telink mesh flows now get an
optional `zengge_cloud` step. Users can skip it to keep advertisement-only
setup, or provide MagicHue username, password, and country so the flow imports
matching mesh metadata before creating the entry. Existing RG4/Telink mesh
entries also get an options-flow refresh path that re-fetches matching
MagicHue metadata and updates only the local mesh credentials/node list; cloud
login credentials remain transient and are not stored. Manual setup can also
create RG4/Telink mesh entries from a BLE address and mesh UUID, with optional
node ID/type/wiring fields for cloudless setups; those entries branch into the
same optional cloud import step before creation. The remaining work is richer
Home Assistant entity planning for cloud-discovered multi-node meshes.

The MagicHue/Zengge cloud path and old UniLED mesh identity are family-gated,
not transport-gated. `ble_mesh` BanlanX scene-mesh models such as `SP310E`
create local diagnostic entries directly, use address-backed
`ble_mesh:<address>` setup identity when manually configured, and keep their
BanlanX scene/provisioning blockers; they must not enter the RG4/Zengge cloud
import/options-refresh flow or receive `zng_mesh_<uuid>` identity just because
they also use a BLE-mesh setup transport.

The first coordinator refresh now performs the diagnostic orchestration step:
if an RG4 mesh connection is attached, it tries to pair using those credentials
and sends the old-UniLED `0x01` status-notification kick. Pair/authentication
failures are stored in diagnostics and do not fail setup. This still stops
short of complete mesh support because remote and other non-light mesh events
still need to be implemented. Paired command nodes expose guarded effect speed
and effect level number controls by resending the current old-UniLED `0xED`
effect packet with the edited byte. RG4 support disposition reports
`mesh_remote_event_parser_pending`, `mesh_provisioning_frame_pending`,
`mesh_group_management_pending`, and
`mesh_node_management_controls_pending`;
`mesh_control_blocker_count=4` is readiness
status only, not support for those non-light controls.

The manufacturer-data identity parser follows old UniLED offsets: bytes `0..1`
are the little-endian mesh UUID, byte `7` is the node/device type, and byte `9`
is the node ID. Bluetooth setup can now create an RG4 diagnostic entry from a
generic Telink advertisement and uses the old UniLED `zng_mesh_<uuid>` unique
ID shape when a mesh UUID is present.

BanlanX scene-mesh models currently have catalog-level routing only. Their
profile diagnostics should stay `core_protocol_pending` until APK or hardware
evidence proves their mesh framing.

### Optional Cloud Transport

- Disabled unless explicitly configured.
- Uses reauthentication flows.
- Stores device mesh credentials only when needed for local control; account
  login credentials should be transient unless a reauth design deliberately
  requires otherwise.
- Never replaces local control for models with working local transport.
- Treats BanlanX cloud endpoint discovery as diagnostic evidence until auth,
  region routing, ownership/bind behavior, and command envelopes are tested.

## Protocol Boundary

```python
class DeviceProtocol(Protocol):
    family: ProtocolFamily

    def plan_features(self, model: CatalogModel) -> EntityPlan: ...
    def build_query_state(self) -> bytes | None: ...
    def build_command(self, intent: CommandIntent) -> bytes | Sequence[bytes]: ...
    def parse_update(self, payload: bytes, state: DeviceState) -> StatePatch: ...
```

Protocol families must not import Home Assistant. They exchange normalized
intents and state patches:

```python
class CommandIntent(Enum):
    TURN_ON = auto()
    TURN_OFF = auto()
    SET_BRIGHTNESS = auto()
    SET_RGB = auto()
    SET_RGBW = auto()
    SET_RGBWW = auto()
    SET_COLOR_TEMP_KELVIN = auto()
    SET_EFFECT = auto()
    SET_EFFECT_SPEED = auto()
    SET_EFFECT_LENGTH = auto()
    SET_AUDIO_INPUT = auto()
    SET_SCENE = auto()
```

## Protocol Families

| Family | Catalog names | Initial source of truth |
| --- | --- | --- |
| `banlanx_601` | SP601E | Existing UniLED behavior plus fixtures |
| `banlanx_60x` | SP602E, SP608E | Existing UniLED behavior plus fixtures |
| `banlanx_v2` | SP611E/SP616E/SP617E/SP620E/SP621E style models and aliases | Existing UniLED behavior plus fixtures |
| `banlanx_v3` | SP603E/SP613E/SP614E/SP623E/SP624E style models and aliases | Existing UniLED behavior plus fixtures |
| `banlanx_6xx` | SP630E-SP65CE and 360PhotoB | Existing UniLED behavior plus catalog limits |
| `banlanx_custom_5xx` | SP521E-SP54CE | APK `/sp630e` surface plus SP6xx-style BLE frames; LAN/provisioning still under research |
| `banlanx_scene_ui` | SP55x, SP66x, DynamicBar | APK scene/LFX profile with diagnostic preset/mode/LFX-route counts, recent/favorite/timer/DIY action anchors, white-brightness anchors, storage/catalog hints, libscene_lfx handler/frame/opcode/state/color-order/PWM/music-effect helpers, and explicit envelope/status/LFX/timer/favorite/DIY/white-brightness blockers; commands pending |
| `banlanx_scene_mesh` | SP31x, SP32x | APK scene/LFX profile with diagnostic preset/mode/LFX-route counts, recent/favorite/timer/DIY action anchors, white-brightness anchors, storage/catalog hints, firmware setup note, shared mesh app-command ID diagnostics, libscene_lfx handler/frame/opcode/state/color-order/PWM/music-effect helpers, and explicit envelope/status/LFX/timer/favorite/DIY/white-brightness blockers; commands pending |
| `banlanx_car_lights` | SP701E, SP702E, SP-MIC | APK car profile with exact setup/dependency strings, four-row setup dependency inventory, structured SP701E -> SP702E setup order, structured SP-MIC -> SP702E accessory dependency, raw `isPrimary`/`subUni` setup-key hints, microphone permission and secondary power-loss hints, primary-controller and install-area setup-flow hints, diagnostic zone/trigger/animation/image counts, subdevice filters, password entry/change/policy/reset flow hints, trigger actions, trigger storage hints, Blutter app-command-ID hints for `configZoneKeyAddrMapping=0x24`, `configTrigger=0x36`, and `configWelcomeLights=0x91`, and explicit BLE/status/zone/trigger/subdevice/password/SP-MIC blockers; commands pending |
| `banlanx_network` | SP801E, SP802E | APK SP801E Art-Net/playlist/DXF and SP802E LFX/GIF/catalog profiles with diagnostic surface/mode/LFX counts plus explicit discovery/socket/Art-Net/LFX/panel-layout blockers; commands pending |
| `fish_tank` | FT001 | APK-derived fish-tank channels, routes, effects, workflow, asset buckets, diagnostic favorite-slot count, exact diagnostic `You can only add up to 5 timers!` limit, optional-cloud endpoint diagnostics, favorite storage, favorite-loop actions, firmware-prompt key, method anchors, raw effect/timer/brightness string hints, and explicit BLE/LAN/timer/favorite/effect/brightness blockers; commands pending |
| `zengge_mesh` | RG4 | Limited old-UniLED mesh support: paired-node lights with strip/bulb role diagnostics, effect select, guarded effect speed/level numbers, shared mesh app-command ID diagnostics, and core packet/session layer plus explicit remote-event/provisioning/group/node-lifecycle blockers; non-light controls pending |

Old UniLED's `LED Chord` and `LED Hue` modules for `SP107E`/`SP110E` are not
part of the BanlanX 3.3.1 APK catalog. Targeted APK/catalog/native string
searches found BanlanX `ledhue` branding URLs but no `SP107E`, `SP110E`,
`LEDCHORD`, or `LEDHUE` device/protocol records. They are therefore represented
as separate legacy-only catalog rows rather than APK-derived rows. BLE
autodiscovery recognizes them with the old `ffe0`/`ffe1` UUID binding; SP107E
also accepts the issue #111 `ffb0`/`ffb1` transport fallback. Limited LED
Chord/LED Hue command builders and status parsers are ported with tests.
SP107E exposes RGB color, effect selection, light-mode selection, effect speed,
and sensitivity controls. SP107E/SP110E also expose disabled-by-default chip
type and segment config controls backed by parsed status diagnostics; the
SP107E secondary/matrix RGB command is exposed through the advanced
`uniled.set_state` `rgb2_color` service field rather than a standalone light
entity.

Legacy scene recall is separate from the APK scene UI family. Old UniLED
implements recall-only saved scenes for `banlanx_601` and `banlanx_60x` with
nine 0-based slots. The new core exposes those slots as disabled-by-default
Home Assistant scene entities after a command session is attached, using
`AA 2E 01 <slot>` for SP601 and `88 8E 01 <slot>` for SP60x. The old scene
save paths were stubs, so save/edit behavior must wait for proven APK scene UI
or device packet evidence.

SP601/SP60x loop state is also scene-loop behavior, not lighting-effect loop.
Old UniLED exposed it as `SceneLoopFeature` with `AA 30 01 <bool>` for SP601
and `88 90 01 <bool>` for SP60x, and the APK string table says these families
do not support lighting effect loop. The integration therefore exposes
`scene_loop` for SP601/SP60x while reserving `effect_loop` for families with a
proven lighting-effect-loop command.

Scene-family diagnostics preserve the APK/native anchors that should guide the
next command-pass:

- Catalog records for `banlanx_scene_ui` and `banlanx_scene_mesh` share
  `/device/scene_ui` and the `packages/scene_ui` asset package.
- The APK exposes scene settings routes plus LFX creation routes:
  `/device/lfx/regular`, `/device/lfx/rhythm`, `/device/lfx/animation`,
  `/device/lfx/gif`, `/device/lfx/graffiti2`, `/device/lfx/image`,
  `/device/lfx/text`, and `/device/scene/image/get`.
- The full 80-entry `ic_mode_*` scene mode asset catalog is preserved as
  human-readable planned `scene_mode_effect` options. The options are APK label
  evidence only until a scene command/status packet map is recovered.
- The scene UI surface list includes a disabled white-brightness option from
  `packages/scene_ui/assets/icons/ic_white_brightness.png` and raw string
  anchors including `raw-brightness-`, `whiteBrightness`, and
  `white_brightness`.
- Native strings expose app-level method anchors including
  `getFrameInfoHandler`, `getPWMFrameInfoHandler`, `setLfxMode`,
  `setLfxSpeed`, `setLfxPixelCount`, `setLfxLoopMode`, `setLfxColor`,
  `setLfxGradient`, `setOnOffLfx`, `setLedPanelLayout`, `setSoundSource`, and
  `setWhiteLightCoexistWithRGB`.
- Native strings also preserve scene/timer/favorite state labels such as
  `recScene`, `removeTimingTask`, `saveTimingTask`, `timing_task`,
  `favoriteLightingEffectIds`, and `favoriteLightingEffectLoopEnabled`.
  They also preserve app-side LFX model/frame labels such as `Lfx(`,
  `LfxColorProps.`, `LfxColorSet{fx: `, `LfxDirection.`,
  `LfxExternParams(`, `LfxLoopMode.2`, `DiyLfx(modeId: `,
  `DiyGradientLfx(modeId: `, `DiyLfxSegment{pixelCount: `,
  `CreativeLfxModeType.2`, `TriggerLfxMode.`, `WLedLfx`, `wrappedLfx`,
  `opCode = `, `opCode: `, `checksum`, `lfxParams`, `lfxMode-`,
  `lfx_mode_id`, `lfx_mode_type`, `lfx_colors`, `lfx_color_sets`,
  `lfx_gradients`, `gif_lfx_frames`, `favLfxModeIds: [`,
  `diyGradientLfx: `, `lfxDurationInLoop: `, `lfxLoopMode: `, and
  `lfx: `.
  Planned disabled selectors expose exact recent-scene actions
  (`addRecScene`, `getRecSceneList`, `removeRecScene`), favorite actions
  (`saveFavoriteEffectList`, `updateFavoriteLfxList`), timer actions
  (`saveTimingTask`, `removeTimingTask`), DIY LFX actions (`saveDiyLfx`,
  `resetLfx`), and white-brightness anchors (`raw-brightness-`,
  `whiteBrightness`, `white_brightness`, `setWhiteLightCoexistWithRGB`).
  These labels are diagnostic anchors only until packet bytes and parser
  offsets are recovered. The LFX labels are exposed separately as
  `scene_lfx_data_model_hint_count=13` and
  `scene_lfx_frame_field_hint_count=16`.
- Scene support disposition reports the shared blockers
  `scene_command_envelope_pending`, `scene_status_parser_pending`,
  `scene_lfx_frame_pending`, `scene_timer_frame_pending`,
  `scene_favorite_frame_pending`, `scene_diy_frame_pending`, and
  `scene_white_brightness_parser_pending` for both scene UI and scene mesh
  families. `scene_command_blocker_count=7` is readiness status only, not
  command support.
- Scene mesh diagnostics preserve the APK setup wording for the SP31XE/SP32XE
  firmware V1.1 requirement and `One-touch Provisioning`, including the
  recovered 90-second automatic provisioning timeout and the warning that other
  devices cannot be controlled during provisioning. They do not reuse RG4's
  provisioning callback-state surface. The scene mesh `mesh_profile` exposes
  only `/device/scene_ui`, the shared `packages/scene_ui` package count, three
  setup hints, the six shared SIG Mesh UUID anchors, the 12 shared mesh
  app-command ID anchors, and missing frame-map gaps until BanlanX scene-mesh
  provisioning/routing packets are recovered. The support disposition repeats
  these blockers as `firmware_v1_1_required`, `provisioning_frame_pending`,
  and `scene_mesh_routing_pending` for every scene-mesh catalog row.
- `libscene_lfx.so` exports 38 IC/PWM API handler symbols, including scene,
  parameter, on/off, interrupt, channel, loop, static-color, color,
  color-temperature, brightness, speed, pixel-length, direction, DIY color,
  on/off animation, WRGB coexistence, reset, pause, palette, and scene-loop
  handlers. It also exports 14 favor/routine/system record/recover and
  LED/default parameter handlers now tracked as native persistence anchors.
  The audited ELF profile also exposes 10 animation/self-test exports
  (`Anim_Calibrate_*`, `Anim_Echo_*`, `Anim_FacTest_*`, on/off animation
  handlers, `pwmOnOffAnimation`, and `WOnOffAnimation`) plus five drive-type
  exports (`IC_DriveRGB`, `IC_DriveW`, `LED_DRIVE_TYPE`, `PWM_DriveRGB`,
  `PWM_DriveW`). These are native research anchors only; they do not prove the
  BLE command envelope or notification parser.
  ELF `.dynsym` inspection found 378 named dynamic symbols and 76
  handler/frame/opcode/LFX-related names. Scene diagnostics now split the API
  surface into 16 paired IC/PWM capabilities (`param_get`, `scene_set`,
  `on_off_set`, `bright_set`, `speed_set`, `loop_set`, `clr_temper_set`,
  `diy_clr_set`, and related setters), four IC-only capabilities
  (`pixel_len_set`, `direction_set`, `pause_set`, `clr_paletter_set`), two
  scene-loop handlers, seven frame helpers (`createFrameHandler`,
  `getFrameInfoHandler`, `getFrameLenHandler`, `getPWMFrameInfoHandler`,
  `getCurrFrameIntv`, `getCurrFrameIntvHandler`, `getChanNumHandler`), nine
  routing/opcode
  helpers (`hal_App_Opcode_Handler`, `hal_pwmCtrl_Handler_R1`,
  `hal_pwmCtrl_Handler_G1`, `hal_pwmCtrl_Handler_B1`,
  `hal_pwmCtrl_Handler_CW1`, `hal_pwmCtrl_Handler_WW1`,
  `hal_WpwmCtrl_Handler_CW1`, `hal_WpwmCtrl_Handler_WW1`,
  `hal_rgbToBus_Handler_01`), and five state helpers (`getStaDat`,
  `syncBriChangeHandler`, `getBitState`, `setBitlOn`, `setBitlOff`).
  State helper exports preserve dynsym offsets and sizes:
  `getStaDat@0x0001119d/256`, `syncBriChangeHandler@0x0001118d/16`,
  `getBitState@0x0000fbe9/16`, `setBitlOn@0x0000fbb9/24`, and
  `setBitlOff@0x0000fbd1/24`.
  The same native profile now separates color-order/LED-type anchors
  (`ONLY_RGB`, `ONLY_PWM`, `RGBCW`, `RGBWC`, `CRGBW`, `CWRGB`), PWM table
  anchors (`PWM_STA_TAB`, `PWM_DYN_TAB`, `PWM_RHY_TAB`, `PWM_DIY_TAB` and
  white-PWM table variants), music/effect routines (`Music_VuMeter`,
  `Music_Spectrum`, `pwmDiyGradient`, `pwmDynGradient`, `pwmRhyBeat`,
  `pwmOnOffAnimation`), and PWM driver/write helpers (`WsetPWM`,
  `WsetPwmBuf`, `setPWM`, `setPwmBuf`, `setCCTBri`, `PWM_DriveRGB`,
  `PWM_DriveW`) as diagnostics-only disassembly anchors.
  Detailed symbol inspection places
  `hal_App_Opcode_Handler` at `0x000130a9` (128 bytes),
  `API_IC_All_Reset_Handler` at `0x00014ec9` (864 bytes),
  `API_PWM_All_Reset_Handler` at `0x00015e05` (524 bytes), and scene write
  handlers `API_IC_Scene_Set_Handler` at `0x00014a91` (292 bytes) and
  `API_PWM_Scene_Set_Handler` at `0x00015ab9` (200 bytes). These are native
  rendering/protocol anchors, not Home Assistant command permission by
  themselves.
- The same `libscene_lfx.so` dynsym audit now preserves 14 exact persistence
  exports for favorites, routines, system recover, LED-type parameters, and
  parameter defaults across IC/PWM drivers. The planner exposes
  `scene_native_persistence_export_count=14` and
  `scene_native_persistence_capability_count=7`. These symbols prove native
  persistence/storage handlers exist, but they still do not prove the BLE
  packet envelope, scene status parser, timer frame, favorite frame, or DIY
  frame layout.
- The APK audit also verifies seven scene native code anchors by mapping the
  exported Thumb function addresses into `.text` and checking function body
  SHA-256 plus first/last 16 bytes. The anchored bodies are
  `hal_App_Opcode_Handler`, `API_IC_Scene_Set_Handler`,
  `API_PWM_Scene_Set_Handler`, `API_IC_Param_Get_Handler`,
  `API_PWM_Param_Get_Handler`, `API_IC_All_Reset_Handler`, and
  `API_PWM_All_Reset_Handler`. The planner exposes these as
  `scene_native_code_anchor_count=7`. Runtime diagnostics include both integer
  and hex native addresses for direct Ghidra cross-reference. These hashes pin
  the APK implementation for later disassembly, but they do not prove scene
  command packets.

## Feature Contract

The core exposes features in normalized form:

```python
@dataclass(frozen=True, slots=True)
class FeatureSpec:
    key: str
    platform: PlatformKind
    device_class: str | None
    entity_category: EntityCategoryKind | None
    enabled_by_default: bool
    options: tuple[str, ...] = ()
    minimum: int | None = None
    maximum: int | None = None
    step: int | None = None
```

The Home Assistant shell maps `FeatureSpec` to entity descriptions. Entity
creation must be deterministic from `EntityPlan` so tests can snapshot it for
every catalog name.

The initial entity planner is implemented in `custom_components/uniled/core/planner.py`.
It intentionally marks command-capable entities as planned but not implemented
until the Home Assistant runtime can send commands, apply parser output, and
surface availability safely.
Diagnostic entities are marked implemented because they are derived from catalog
and runtime metadata rather than device commands.

## State Model

```python
@dataclass(slots=True)
class DeviceState:
    available: bool
    model: str
    firmware: str | None
    channels: dict[int, ChannelState]
    diagnostics: dict[str, Any]
    last_update: datetime | None

@dataclass(slots=True)
class ChannelState:
    power: bool | None = None
    brightness: int | None = None
    rgb: tuple[int, int, int] | None = None
    rgbw: tuple[int, int, int, int] | None = None
    rgbww: tuple[int, int, int, int, int] | None = None
    color_temp_kelvin: int | None = None
    effect: str | None = None
```

The initial state dataclasses are implemented in
`custom_components/uniled/core/state.py`. Legacy parity parsers currently return
full `DeviceState` snapshots from known status payloads; later coordinator work
can layer smaller state patches on top when push and polling behavior is wired
into Home Assistant.

Status notification frame assembly is implemented in
`custom_components/uniled/core/protocols/framing.py`. The current helpers cover
the old UniLED packet styles for SP601, SP60x, BanlanX2, BanlanX3, and direct
SP6xx frames so the future BLE transport can feed complete payloads into the
protocol parsers. Custom 5xx BLE status also accepts the zero-based fragmented
SP530E envelope shown in old-UniLED issue #67; those fragments assemble into
the same SPTech chunked status payload used by the LAN parser.

SP601/SP60x status parsing follows old UniLED's channel-plus-tail layout. Both
families parse 11-byte per-output blocks and synthesize aggregate power and
brightness. SP601 then reads timer-count/timer-record bytes and scene-loop
state when present. SP60x reads tail sensitivity, timer-count/timer-record
bytes, four 13-byte trigger records, and scene-loop state when present.
Complete timer and trigger records are retained as raw core diagnostics and
hex-encoded at the Home Assistant diagnostics boundary. They remain evidence,
not timer/trigger edit controls, until a real record schema and write flow are
proven.

BanlanX2 status parsing also follows old-UniLED timer comments. Bytes `12..21`
are preserved as an opaque timer/status header, byte `22` is the timer count
when present, and complete seven-byte records are retained from byte `23`.
RGBW-capable V2 models still treat the final two bytes as the white-level tail.
Only `timer_count` is exposed as a diagnostic sensor; timer records stay raw
diagnostics until the schema and write commands are proven.

BanlanX3 status parsing also preserves old-UniLED DIY metadata: byte `10` is
the DIY effect type and byte `11` is the DIY color count when present. These
are exposed as diagnostic `diy_effect_type` and `diy_color_count` sensors for
BanlanX3 models. Old UniLED included comment-level `0x1A` DIY color frame
examples but no public builder, and the APK string surfaces do not prove a
safe local edit/save flow, so DIY editing remains hidden.

SP6xx status parsing follows the old UniLED offset split for color state.
Static color packets use stored RGB bytes `37..39`; dynamic and sound color
modes use live RGB bytes `47..49`; dynamic white/CCT modes use bytes `50..51`.
The old-UniLED custom/DIY mode byte at offset `52` is exposed as a diagnostic
`custom_effect_slot` sensor for SP6xx-style families. The APK exposes SP630E
DIY/favorite strings and assets such as `/sp630e/diy/fav`, `saveDiyLfx`, and
DIY favorite limits, but those labels do not prove local edit/save packet
flows, so custom slot editing remains hidden. Old UniLED dev_v3 SPTech sources
split custom mode `0x07` as `Custom Solid` and `0x08` as `Custom Gradient`;
the latter is mapped for the gradient-capable SPTech SPI RGB/RGBW light types
`0x86`/`0x88`. The model-aware SPTech NET overlay exposes custom-solid `0x13`
as `Firework` for SP530E only on `0x86`/`0x88`, and for the fixed
SP538E/SP548E `0x06` plus SP539E/SP549E `0x08` profiles. Generic
SP630E-style `0x06`/`0x08` profiles remain conservative, so parsed state and
HA selects use recovered mode/effect names without leaking custom 5xx NET-only
effects or exposing DIY persistence controls.
The shared APK `/sp630e` surface is now represented as diagnostic evidence for
both `banlanx_6xx` and `banlanx_custom_5xx`: route, surface, favorite-limit,
timer-limit, music-asset, network, remote, motor, method, Blutter app-command
ID, data-model, shared native LFX, catalog, gap, and APK evidence counts are
exposed from `packages/sp630e` and `liblfx.so`, including 35 app-layer command
ID anchors and the exact native export detail anchor count. These profile
values describe the vendor-app UI, workflow breadth, and native renderer
anchors only; they do not enable DIY/favorite/timer/remote/motor/native-renderer
writes without proven frames.
The local APK evidence audit additionally verifies the extracted `liblfx.so`
surface: 162 dynamic symbols, 34 exported renderer/music/PWM anchors, and
7 pinned detail anchors such as `pwmEffect`, `pwmMusicEffect`,
`Music_Spectrum`, `getBufPixelVals`, `arrangeAppMusicDat`, `lfxParams`, and
`curPWMVals`.
Nonzero SP6xx message-key packets remain unsupported because the legacy decoder
also rejected them and no APK/native or hardware evidence has proven the
decode path. This does not block the plain SP530E custom-5xx BLE fragment shape
from issue #67 because its key byte is zero and its assembled payload is
SPTech-style chunk data, not an encoded SP6xx frame.

## Home Assistant Shell

### Setup

1. Load catalog.
2. Resolve the model from config entry data and current discovery info.
3. Create the transport.
4. Create the protocol family.
5. Query initial state where possible.
6. Build the entity plan.
7. Store `UniLEDRuntime` in `entry.runtime_data`.
8. Forward platforms.
9. Start push subscriptions or polling.

### Unload

1. Stop polling/subscriptions.
2. Unload platforms.
3. Close transport.
4. Clear runtime listeners.

### Platforms

All platforms use shared base entity behavior:

- Device info comes from `DeviceIdentity` and catalog metadata.
- Unique IDs are stable and include device identity, channel, and feature key.
- Availability is derived from `DeviceState.available` and feature-level
  accessory availability.
- Entity category is set for diagnostics/configuration features.

### Light Platform

- `supported_color_modes` is computed from `FeatureSpec` or the currently
  implemented command subset.
- `color_mode` is always one of the supported modes.
- `brightness` and `onoff` are never combined with richer Home Assistant color
  modes such as `rgb`, `rgbw`, `rgbww`, `color_temp`, or `white`.
- Kelvin is used for color temperature.
- Unsupported kwargs are ignored only after logging at debug level.
- Multi-command updates are batched when the protocol supports it.

The initial `light.py` implementation exposes normal command lights only when a
runtime has an attached `DeviceSession`, and exposes Zengge mesh node lights
when the mesh session is paired and the target node is known command-capable.
Recognized models without a ported protocol, attached transport, or eligible
mesh node remain diagnostic-only. The light sends power, brightness, RGB,
RGBW, RGBWW, white-level, and Kelvin color-temperature commands where the
protocol and parsed light type support them, then applies an optimistic
normalized state update after successful sends.
BanlanX2/BanlanX3 effect lists and fixed-subtype SP6xx combined mode/effect
lists are exposed through standard Home Assistant light effect properties when
an old-UniLED parity map is available. SP601/SP60x effect lists are exposed on
physical output lights only, matching old UniLED's no-effect-list/no-command
behavior for aggregate channel `0`. SP601 exposes two disabled-by-default
physical output lights, SP602E exposes four, and SP608E exposes eight, while
the existing aggregate `main_light` remains channel `0`. SP601 aggregate power,
brightness, and RGB commands fan out to Output 1 and Output 2 because the
protocol has no all-output mask; SP60x uses its all-output mask for aggregate
light writes. Output-scoped SP601/SP60x chip-order, effect speed, effect
length, and effect direction entities follow the same channel mapping and stay
guarded from aggregate `uniled.set_state` service calls.
An issue-backed SP630E regression covers old UniLED #121: address-backed
SP630E setup must attach a BLE command session and expose `main_light` even
while RSSI diagnostics are present, so the device cannot regress to a
Signal-strength-only entry.
Broader per-output channel entities and full hardware validation across every
wiring type remain future work.

### Number, Select, Switch, And Button Platforms

The initial `number.py`, `select.py`, `switch.py`, and `button.py`
implementations expose command/action controls only when the required runtime
transport is attached. Number controls currently cover effect speed, effect
length, audio sensitivity, and SP6xx on/off animation pixel count where the
entity plan contains those features. SP601 effect speed, effect length, audio
sensitivity, chip order, and effect direction are output-scoped; SP60x effect
speed, effect length, chip order, and effect direction are output-scoped while
audio sensitivity is a master/tail control. Select controls currently cover
audio input for BanlanX2/BanlanX3/SP6xx/custom 5xx, BanlanX2/BanlanX3 effects,
fixed-subtype SP6xx combined mode/effects, dynamic SP630E/360PhotoB and custom
5xx effects after a status packet identifies the active light type,
old-UniLED chip-order selects for SP601/SP60x output channels and
BanlanX2/BanlanX3, SP6xx on/off animation effect/speed, SP6xx power-restore
mode, SP6xx light-type/chip-order
configuration, light mode for BanlanX2/BanlanX3, and paired-node Zengge mesh
effect selection. Switch controls currently cover effect direction,
SP601/SP60x scene loop, effect loop for families with a proven
lighting-effect-loop command, SP6xx effect play/pause, and SP6xx color/white
coexistence where the protocol family has known commands and the model or
status light type supports the feature. Button controls currently cover a
diagnostic refresh action that delegates to
`UniLEDCoordinator.async_request_refresh()` for normal BLE sessions and
RG4/Zengge mesh transports.
The legacy `uniled.set_state` entity service is restored through current Home
Assistant service registration. It supports command-backed BanlanX power,
brightness, RGB/RGBW/RGBWW, white, Kelvin CCT, effect, effect-parameter,
audio-sensitivity, play/loop, and direction fields by dispatching through the
same runtime helpers as the light, number, select, switch, and mesh platforms.
For SP6xx-style runtimes, brightness writes are suppressed while the parsed
light mode is sound color `0x05` or sound white `0x06`, matching old UniLED's
behavior of ignoring sound-mode brightness changes and reporting full
brightness instead. Status parsing follows the same read-side rule: sound
color and sound white notifications report brightness `0xFF` while retaining
the raw color and white level bytes in state diagnostics. Parsed audio input
and sensitivity are exposed only while the device is powered in sound color or
sound white mode; non-sound and powered-off statuses clear those fields, and
Home Assistant audio-input/sensitivity command entities use those parsed
values for availability while low-level builders remain explicit commands. The
parsed `effect_loop` flag is also mode-gated like old UniLED: dynamic and
sound modes may expose it, while static and custom modes report no loop state.
Effect speed, effect length, direction, and play/pause follow the old-UniLED
per-effect metadata as well: the parser exposes those raw bytes only when the
current light type's effect table marks the selected effect as speedable,
sizeable, directional, or pausable. Non-pausable SPI effects, PWM effects
without size/direction flags, static effects, and non-sizeable sound effects
therefore clear the corresponding state values even when the status packet
contains nonzero bytes. Home Assistant effect-parameter number and switch
entities for SP6xx-style runtimes use that parsed state for availability, so
unsupported controls are present as planned entities but unavailable for the
current effect instead of accepting misleading writes from the UI. Optimistic
state after SP6xx effect, light-mode, or light-type selects applies the same
metadata gate immediately, clearing stale speed, length, direction, play/pause,
and non-loopable loop values before the next status notification arrives.
Outside sound modes, SP6xx brightness follows the old selector split:
color-mode brightness writes use `0x51 ... 00 <level>`, while white/CCT-mode
brightness writes use `0x51 ... 01 <level>` via the white-level command path.
SP6xx RGB writes also follow old-UniLED mode semantics: static RGB uses
`0x52 <red> <green> <blue> <level>`, while dynamic and sound RGB modes use
only `0x57 <red> <green> <blue>` and ignore any brightness bundled with the
same RGB request. Static RGB/RGBW/RGBWW payloads reuse the current brightness
when no new brightness is supplied.
SP6xx-style white requests also preserve old-UniLED mode semantics: if the
controller is in color mode, the runtime sends a `0x53` light-mode command to
the corresponding static, dynamic, or sound white mode before applying white
level. When that transition lands in sound white, the `0x51` level write is
still suppressed.
Standalone SP6xx-style light-mode selects use the same old-UniLED coupling:
the command is always a `0x53 <mode> <effect>` pair. When the target mode
changes, the runtime keeps the current effect only if it is valid for the
target mode and current light type; otherwise it chooses the first effect from
that target mode's old-UniLED list. Fixed SP6xx models expose their light-mode
options from their known light-type profile. Dynamic-light-type models such as
SP630E, 360PhotoB, and custom 5xx create the select shell but keep options empty
and those selects unavailable until parsed status supplies `light_type`.
For RG4/Zengge mesh nodes, the service also accepts `transition` and maps it to
the same old-UniLED gradual field used by HA light transitions.
It deliberately does not unlock diagnostic-only LAN, scene, car-light,
fish-tank, or unported BLE families.

For BanlanX2/BanlanX3, audio-input and sensitivity entities are model-gated by
the APK `spec_functions` `0x02` audio bit, matching old UniLED's `intmic`
profile split. The same bit gates generic V2/V3 sound-reactive effect lists;
SP603E/SP621E/SP623E/SP624E therefore expose only non-sound effects and no
audio controls. That same old-UniLED split also gates mode controls: mic/music
models expose the `light_mode` select, while non-mic models expose an
`effect_loop` switch instead. Protocol instances created by the model registry
carry the concrete catalog profile into the V2/V3 status parser, so parsed
effect names, audio fields, and RGBW white-tail bytes follow the same model
surface as entities and option maps. Those concrete protocol instances also
reject unsupported effect, audio, light-mode, and chip-order command values
before transport writes.
Address-backed APK-inferred command models are tested through the same setup
path as exact old-UniLED parity models. SP603E attaches a BLE command session
and exposes the non-sound BanlanX3 control surface; 360PhotoB attaches the
SP6xx BLE command session and keeps dynamic effect/mode options gated on parsed
`light_type` instead of becoming diagnostics-only.
A catalog-wide setup-helper test covers all 94 command-protocol-ready BLE
models and requires each one to attach a BLE session and expose at least one
session-backed command light.
BanlanX2/BanlanX3 RGB writes preserve old-UniLED colorability semantics:
when the current effect is not one of the family colorable effects, the runtime
first selects `Solid Color` (`0xBE` on V2, `0x63` on V3) and then sends the RGB
payload. Existing colorable effects remain active.
RGB payloads also preserve old-UniLED level semantics: an explicit HA
brightness is used when present, otherwise BanlanX2/BanlanX3 reuse parsed
`color_level` before falling back to brightness/full level.

RGBW-capable BanlanX2/BanlanX3 models intentionally expose Home Assistant
`rgb` and `white` modes rather than HA `rgbw`, matching old UniLED. White mode
is represented by the `Solid White` effect (`0xBF` on V2, `0xCC` on V3) plus a
family-specific white-level command (`A0 76 02 <level> 00` on V2,
`21 02 <level> FF` on V3). When parsed status is already in `Solid White`, the
white tail byte becomes both the white level and HA brightness; brightness
changes in that state send only the family white-level payload rather than the
normal color brightness command or a redundant effect switch. The normal
color-level byte remains available as diagnostic `color_level` state. Directly
selecting the `Solid White` effect also mirrors old UniLED's local state side
effect by reporting white mode and reusing the current parsed white level, or
full white if the level is unknown.
Parsed BanlanX2/BanlanX3 sound effects and auto-sound light mode follow old
UniLED's on/off-only HA surface: supported color modes become `onoff`,
brightness is `None`, and the raw level byte stays available as diagnostic
`color_level`. A later RGB or white command clears that temporary on/off mode
override after selecting an RGB/white-capable effect.
Parsed V2/V3 dynamic attributes follow the same old-UniLED mode gate: speed and
V2 length are exposed only for singular dynamic effects or auto-dynamic mode.
Static color, solid white, singular sound, and auto-sound statuses clear those
dynamic attributes. Auto-dynamic and auto-sound modes also force parsed effect
type to `Dynamic` and `Sound` respectively, even when the raw effect byte still
contains a static effect label.

These platforms are deliberately narrower than the full feature contract. Pixel
count, chip type, color order, scene slot, SP801E/SP802E network surface and
content-mode selectors, SP801E Art-Net/port/playlist selectors, SP802E regular
LFX effect and matrix-music selectors, scene-family mode/effect selection, mesh
remote events, identify, save-scene, and restore-default buttons stay planned
but hidden until read/write protocol behavior is proven for each family.

Recognized APK-profile families still expose lightweight diagnostic counts for
recovered evidence and known gaps. Scene, network, car-light, and fish-tank
profiles expose protocol-gap, APK package-asset, APK asset-evidence, and APK
string-evidence counts so users can tell full vendor-app surface area, curated
evidence anchors, and command readiness apart.
Package asset counts come from `asset_package_counts.txt` in the APK research
artifacts: `/sp630e` has 217 assets, `scene_ui` has 204,
`module_sp801e` has 143, `sp802e` has 81, `car_lights` has 58,
`fish_tank_lights` has 30, and `accessories` has 9.
Scene profiles also expose control-surface, route, mode-icon/sample,
app-method, storage, recent-action, favorite-action, timer-action, DIY-action,
white-brightness-anchor, raw-string, native-handler, native-library,
LFX data-model, LFX frame-field,
native-frame-helper, native-opcode-helper, native-state-helper,
native-animation-export, native-drive-export, native-persistence-handler,
native-export, native-code-anchor, setup-requirement, catalog, and transport
counts.
Network profiles also expose route, regular-LFX asset, LFX GIF asset,
app-method, workflow, raw-string, import-constraint, catalog, transport,
native-library, native-frame, and native-export counts.
Car-light profiles also expose accessory-asset, animation-asset,
trigger-image-asset, zone-image-asset, subdevice/password/trigger storage,
password-entry-hint, password-policy-hint, password-reset-hint, route,
setup-requirement, setup-flow, setup-key, and model-role counts. Car-light
models also expose diagnostic setup stages/order, required-controller values,
`car_light_setup_dependency`, `car_light_setup_dependency_count`,
`car_light_required_setup_dependency_count`, and
`car_light_ordered_setup_model_count`. Fish-tank profiles
also expose light-channel, control-surface, route, effect/workflow,
icon/image/channel/timer/favorite/effect asset, favorite-action,
favorite-store/recall/clear, favorite-action-type, timer-slot/action/hint,
timer-string, app-method, data-model, favorite-service, favorite-storage,
timer-storage, app-command-ID, brightness-state, raw-string, and
brightness-string counts.
Car-light support disposition also reports the shared blockers
`car_light_ble_opcode_pending`, `car_light_status_parser_pending`,
`car_light_zone_command_pending`, `car_light_trigger_packet_pending`,
`car_light_subdevice_binding_pending`, and `car_light_password_flow_pending`;
`SP-MIC` additionally reports `car_light_sp_mic_event_pending`. The matching
`car_light_command_blocker_count` is readiness status, not command support.
FT001 planned action selects expose the app-visible Store/Recall/Clear favorite
action types, Loop/Stop favorite-loop action types, and Save/Remove timer
action types, but they stay disabled until local BLE or LAN packets are proven.
Raw effect-string diagnostics preserve `waterdrop`, `Flowing Water`,
`Spring Water2`, and `Stromend Water`, while firmware diagnostics preserve
`FishTankLights:fw_prompted_`; these are diagnostic/planning evidence only and
must not unlock command entities. FT001 support disposition also reports
`fish_tank_ble_opcode_pending`, `fish_tank_status_parser_pending`,
`fish_tank_lan_refresh_pending`, `fish_tank_timer_frame_pending`,
`fish_tank_favorite_frame_pending`, `fish_tank_effect_packet_pending`, and
`fish_tank_brightness_parser_pending`; the matching
`fish_tank_command_blocker_count=7` diagnostic is readiness status, not
command support.

## Config Flow

Required flow steps:

- `async_step_bluetooth`: handles BLE discovery.
- `async_step_user`: manual setup, including host/IP and model selection.
- `async_step_reconfigure`: host, transport preference, and timing changes.
- `async_step_reauth`: optional cloud credentials only.
- `async_step_import`: migration/import from YAML or legacy entries if needed.

Flow validation:

- Resolve model before entry creation.
- Abort duplicates by unique ID.
- Connect and query when safe.
- If model is Recognized but not controllable, show a clear message and avoid
  creating command entities.

The current manual flow delegates entry-data creation to
`custom_components/uniled/setup_data.py`, which can be tested without a Home
Assistant install. It supports the existing diagnostic/manual path, a direct
BLE-by-address path for catalog models that advertise BLE capability, and a
LAN-host path for catalog models that advertise LAN capability. The BLE path
stores `CONF_ADDRESS`, uses `ble:<address>` as the unique ID, and gives users a
manual fallback when Home Assistant Bluetooth discovery does not see a device.
The manual LAN path stores `CONF_HOST`, uses `lan:<host>` as the unique ID, and
rejects BLE-only models before entry creation. Verified SPNet LAN discovery for
SP541E uses the response MAC as the bare config-entry unique ID when present so
old-UniLED-migrated entries and new discovery entries deduplicate. Neither path
connects or queries during setup unless a proven runtime transport is available
for that family.
This is now an all-catalog invariant: setup-data tests create entry data for
all 122 advertised BLE routes, 27 BLE-mesh routes, and 41 LAN-host routes in
the current APK catalog, while tracking the 39 optional-cloud flags separately
from local setup transports.

The same manual flow now supports BLE-mesh entries for mesh-capable catalog
models. RG4/Zengge manual setup requires a Bluetooth address and a mesh UUID,
uses the old UniLED `zng_mesh_<uuid>` unique ID shape, accepts decimal or hex
mesh/node fields, and then offers the MagicHue import step so cloud credentials
and node metadata can be fetched before the entry is created. BanlanX scene-mesh
manual setup also requires an address and mesh UUID, but its stable setup
identity is the local `ble_mesh:<address>` form and it remains diagnostic-only
until scene-mesh frame routing is proven.

Bluetooth entry-data creation also lives in `setup_data.py`. Exact catalog
names, APK friendly labels, and safely suffixed names such as `SP601E_AABB`
create direct BLE or BLE-mesh entries only when the catalog advertises that
local transport; bounded prefix manifest matches such as `SP1*` and `SP5*`
must still reject LAN-only models like `SP801E` and near misses such as
`SP601EX`. Direct BLE and BLE-mesh discovery entries must also carry a
Bluetooth address; the setup helper no longer falls back to a model-name unique
ID because the runtime transport resolves devices by address.
Generic Telink advertisements can resolve to RG4 when manufacturer data exposes
a mesh UUID, node type, and node ID. Entries with a BLE address plus mesh UUID
can attach the Telink/Zengge session layer, pair, request status, and expose
guarded command-capable light entities when eligible light node metadata is
available. Entries without eligible paired nodes remain diagnostic-only.
BanlanX BLE advertisements can also resolve by manufacturer data when the
manufacturer ID is `0x5053` or legacy decimal `5053` and payload byte `0` maps
to a user-facing APK model with BLE transport. This covers issue evidence such
as `SP542E` reporting manufacturer payload `5d 10 ...`, `SP613E` reporting
`09 10` instead of the old `09 00` pattern, and duplicate `SP548E` variant
`0x94`, plus issue-reported SP538E/SP548E `f0` payloads (`56 f0 ...` and
`63 f0 ...`); such entries store `discovery_match=banlanx_manufacturer_data`
and still pass the normal transport/confidence gates before creation.

Config-entry migration also lives behind the Home Assistant-independent
`setup_data.py` boundary. The first migration pass maps old UniLED transport
values `ble`, `net`, and `zng` into the new `ble`, `lan`, and `ble_mesh`
schema, preserving BLE addresses, LAN hosts, and Zengge mesh IDs/UUIDs when
present. BanlanX scene-mesh migrations with address and mesh UUID derive the
same local `ble_mesh:<address>` identity instead of borrowing Zengge mesh
identity. Old MagicHue username/password fields are deliberately not retained as
stored entry data because the new cloud import flow uses those credentials only
transiently. The Home Assistant hook updates entries through
`hass.config_entries.async_update_entry` with `version` and `minor_version`
instead of mutating `ConfigEntry` directly.

Config-entry reconfiguration uses the same Home Assistant-independent helper
boundary. `reconfigure_entry_data()` validates and normalizes local repair
updates for BLE addresses, LAN hosts, manual IDs, and RG4/Zengge mesh node
metadata, including legacy-shaped entries when enough replacement data is
provided. The Home Assistant flow implements `async_step_reconfigure`, verifies
the existing unique ID when one is present, then calls
`async_update_reload_and_abort(..., data=...)` so the config entry is replaced
and reloaded through Home Assistant's current helper path. This reconfigure
step does not change protocol family, and it rejects changing an existing
Zengge mesh UUID because that would point to a different mesh identity.

The integration manifest includes the existing local-name matchers, BanlanX
manufacturer-data wake-up matchers for manufacturer IDs `20563` (`0x5053`) and
`5053`, and a Telink/Zengge matcher using manufacturer ID `529` plus service UUID
`00010203-0405-0607-0809-0a0b0c0d1910`. Current Home Assistant Bluetooth
discovery supports those matcher keys, and the config flow is still responsible
for filtering and duplicate handling after a matcher fires. Catalog tests prove
the local-name matcher set covers all 151 current user-facing BLE or BLE-mesh
model names, including legacy-only `SP107E`/`SP110E` through the bounded
`SP1*` matcher, while the BanlanX manufacturer-data matchers catch issue-style
advertisements without a useful local name and the Telink matcher catches
generic mesh advertisements that do not expose a catalog model name. All
manifest Bluetooth matchers must remain `connectable: true`, and the setup-data
helper rejects non-connectable discoveries before creating entries because every
current local BLE and BLE-mesh path needs outgoing writes. Do not add a blanket
`SP*` matcher or `manufacturer_data_start` to the Telink/Zengge matcher: the
old-UniLED offsets show bytes `0..1` are the little-endian mesh UUID, so a fixed
prefix would only match selected meshes.

## Diagnostics

Diagnostics output:

- Integration version.
- Config entry version.
- Model name, model ID, family, support level, and support disposition.
- Transport kind, address/host redacted as needed.
- LAN profile facts for LAN-capable models, including whether command framing
  and discovery have been confirmed.
- BLE profile facts for direct-BLE models, including UUID candidates, plugin
  methods, and plugin call-contract hint count.
- Entity plan summary.
- Last update age.
- Last unavailable reason.
- Capability limits.
- Sanitized raw discovery metadata when useful.

Diagnostics must redact credentials and secrets.

The `support_disposition` diagnostic is the compact user-facing summary of the
current implementation state. It must distinguish proven command-ready
families, RG4/Zengge mesh limited support, diagnostic-only recognized families,
safe setup transports, pending BLE UUID binding, pending LAN frames, pending
BLE-mesh frames, scene-family command blockers, BanlanX scene-mesh
firmware/provisioning/routing blockers, and optional-cloud capability. This
lets recognized APK families remain safely addable without implying command
support before packet evidence exists.

The `support_blockers` and `support_blocker_count` diagnostics are the
machine-readable companion to `support_disposition`. They must include only
open blocker/requirement tokens ending in `_pending`, tokens ending in
`_required`, and explicit `accessory_dependency=...` entries, matching the
generated support-matrix blocker aggregation.

The selected-model catalog diagnostics must also expose raw `connectCaps`,
decoded connect-capability labels, raw `specFunctions`, decoded spec-function
bit labels, raw `colorCap`, decoded color-capability labels, APK feature
count, APK feature keys, APK feature key/value summary, duplicate-record
variant count, and duplicate-record variant IDs. A
catalog-wide invariant must keep decoded `connectCaps` flags equal to the
generated transport labels for every user-facing model and must prove every
current APK `specFunctions`/`colorCap` value decodes without losing bits. A
second invariant must pin the current APK feature-key vocabulary so newly
recovered metadata is added deliberately.
The `runtime_transport_state` diagnostic is the companion runtime attachment
summary. It must report `command_session`, `mesh_transport`,
`mesh_transport_paired`, `lan_transport_holder`, `transport_holder`, or
`diagnostic_only` so Home Assistant diagnostics can distinguish a configured
route from an actually attached command path.
The `last_refresh_result` diagnostic is the companion refresh-outcome summary.
It must report `no_session` for recognized diagnostic-only entries that cannot
query state yet, `no_response` when an attached command session times out, and
`ok` after a parsed state response is adopted.
A catalog-wide runtime test covers all 57 recognized-only APK models. It
requires each model to build a runtime, expose its family-specific APK profile
diagnostics, report `apk_profile_ready`, and keep all command platforms closed
until packet evidence promotes the family.
Recognized direct-BLE models also have a setup-entry path guard: all 30 current
recognized BLE models can create BLE setup-entry data, report
`configured_transport=ble`, report `runtime_transport_state=diagnostic_only`,
and attach no transport/session or command entities until UUID binding and
packet frames are proven.

The generated support matrix must expose per-row `support_blockers` and
`support_blocker_count` values for every canonical user-facing model, then
aggregate those row values into the open support blocker/requirement summary.
The row values use the same rule as runtime diagnostics: tokens ending in
`_pending`, tokens ending in `_required`, and explicit accessory dependencies
are counted per canonical user-facing model so the remaining family work stays
machine-readable as protocol support is added.

## Repairs

Repairs should cover:

- Recognized model not yet controllable.
- Stored model no longer matches current discovery.
- LAN host unreachable.
- BLE address changed or stale.
- Deprecated config entry version.
- Pixel count or channel configuration outside catalog limits.
- Optional cloud credentials expired.

Initial repair coverage is intentionally conservative. `async_migrate_entry`
creates a non-fixable `issue_registry` issue when legacy entry data cannot be
normalized safely, and `async_setup_entry` creates the same style of issue when
stored entry data cannot build a runtime. Both issues use sanitized
placeholders only: entry title, failed field, and symbolic reason. Runtime
model-resolution failures preserve the precise stored field/reason, including
duplicate-name `model_id` mismatches. Successful migration or setup deletes the
matching issue. Automatic repair flows should be added only when the integration
can prove a safe fix without guessing protocol family, mesh identity, account
credentials, or device ownership.

## Testing Strategy

### Core Unit Tests

- Catalog schema validation.
- Catalog name resolution for all 153 unique names.
- Filtering behavior for `TEST`.
- Family assignment for every user-facing name.
- Entity plan snapshots for every family.
- Command builder tests for each implemented command.
- Parser tests for each known state update format.
- Color conversion and Kelvin limit tests.
- Pixel limit validation tests.

### Home Assistant Tests

- Config flow discovery, manual setup, duplicate abort, and failed connection.
- `async_setup_entry`, platform forwarding, unload, and reload.
- Typed `entry.runtime_data` population.
- Device registry and entity registry identity.
- Light entity color modes and Kelvin behavior.
- Diagnostics redaction.
- Repairs creation and dismissal.
- Migration from legacy config entry versions.

### Fixture Matrix

Each Full family needs fixtures for:

- Discovery metadata.
- Initial state query/response or notification.
- Power command.
- Brightness command.
- Color command where supported.
- Effect command where supported.
- Error/unavailable behavior.

Each catalog name needs at least:

- Catalog resolution test.
- Entity plan test.
- Support-level assertion.

## Migration From Existing UniLED

- Keep the `uniled` domain unless a future breaking change is deliberately
  chosen.
- Keep config entry migration for legacy transport, address, model, LAN host,
  and Zengge mesh identity data. Old cloud login credentials must not be
  retained as stored entry data.
- Preserve existing entity unique IDs where possible.
- When preservation is unsafe, create a repair that explains the migration path.
- Port legacy protocol code into the core only with unit tests and fixture
  coverage, and only when it matches the BanlanX APK catalog or the project
  explicitly accepts a non-APK legacy device scope.

## Quality Gates

A release candidate must pass:

- `ruff check`.
- `pytest`.
- Home Assistant config flow and entity tests.
- Catalog coverage test proving every user-facing model is assigned.
- Diagnostics redaction test.
- Import test against the minimum supported Home Assistant version.
- Manual smoke test with at least one BLE controller and one LAN-capable device
  when hardware is available.

## Implementation Phases

1. Catalog and core scaffolding: schema, resolver, support levels, family map,
   and coverage tests for all catalog names. Initial implementation exists in
   `custom_components/uniled/core/catalog` and is generated by
   `scripts/generate_catalog.py`. Old-UniLED parity boundaries are guarded by
   `scripts/audit_legacy_uniled.py`, which statically derives 51 old BLE model
   names, zero old NET model names, the exact 49-name APK overlap, and the
   separate legacy-only `SP107E`/`SP110E` catalog rows from the detached
   `../uniled` source tree. The same audit also extracts the seven old BLE
   command-builder surfaces and verifies that every non-stub old command is
   represented by a ported parity profile, with SP601E/SP60x `scene_save`
   tracked as an empty old stub, SP6xx old effect selection covered through
   the current mode/effect `light_mode` encoder, and SP107E/SP110E covered by
   limited LED Chord/LED Hue parity profiles.
2. Entity planner: deterministic feature plans for every user-facing model,
   including diagnostics, planned lights, diagnostic `max_pixel_channels`
   catalog limits, FT001 favorite-slot/timer-limit diagnostics, planned
   pixel-count writes, scene plans, audio controls, accessory roles, and legacy
   UniLED parity markers/profile diagnostics. Initial
   implementation exists in `custom_components/uniled/core/planner.py`.
3. Legacy parity protocol command layer: state query and common command builders
   for SP601, SP60x, BanlanX2, BanlanX3, and SP6xx families, including SP6xx
   on/off animation, power-restore, play/pause, coexistence, light-type,
   chip-order, RGBW, RGBWW, white-level, and CCT commands, plus old-UniLED
   SP601/SP60x output chip-order commands, SP601/SP60x aggregate scene-loop
   commands, and BanlanX2/BanlanX3 chip-order commands.
   `custom_components/uniled/core/legacy_parity.py` records the old source
   modules, ported command builders, parser hints, and intentionally unported
   old stubs such as SP601/SP60x `scene_save`.
   Initial
   implementation exists in
   `custom_components/uniled/core/protocols`.
4. Legacy parity parser layer: normalized `DeviceState` output for proven
   SP601, SP60x, BanlanX2, BanlanX3, and unencrypted SP6xx status payloads.
   Initial implementation exists in `custom_components/uniled/core/state.py`
   and `custom_components/uniled/core/protocols`.
5. Legacy notification framing layer: segmented BLE notification assemblers for
   SP601, SP60x, BanlanX2, BanlanX3, and direct SP6xx frames. Initial
   implementation exists in `custom_components/uniled/core/protocols/framing.py`.
6. Core session layer: high-level command dispatch and notification parsing over
   a minimal async byte transport. Initial implementation exists in
   `custom_components/uniled/core/session.py` and
   `custom_components/uniled/core/transports`.
7. Initial BLE transport: tested BLE profile facts for ported legacy families
   and a Home Assistant Bluetooth byte transport for address-backed entries.
   Initial implementation exists in `custom_components/uniled/core/transports/ble.py`
   and `custom_components/uniled/bluetooth.py`.
8. Modern Home Assistant shell: typed runtime data, config flow, unload/reload,
   diagnostics, and command entities. Initial runtime data, coordinator,
   diagnostics, manual config-flow model resolution, exact-name Bluetooth flow,
   diagnostic sensor platform support, session-backed RGB light support,
   session-backed SP601/SP60x physical output lights, session-backed
   SP601/SP60x scene-loop switches, and session-backed effect
   number/select/switch controls now exist.
9. Proven BLE families: port existing SP60x/SP61x/SP63x-SP65x behavior into
   core protocols with fixtures.
10. Custom 5xx families: initial SP52x/SP53x/SP54x BLE control now reuses the
   SP6xx-style command/status implementation with catalog limits, plus
   dev_v3 SPTech custom solid/gradient mode naming and Firework custom-solid
   effect for model-scoped custom 5xx SPI RGB/RGBW statuses; LAN provisioning,
   network-info queries, and custom payload editing remain open.
11. Scene UI families: implement SP55x/SP66x and SP31x/SP32x command/status
   packets for scene selection, recent scenes, favorites, timers, DIY LFX, and
   mesh routing/provisioning.
12. Network/accessory families: implement SP801E Art-Net config, playlist,
   DXF/panel-layout import flow, SP802E BLE/LAN LFX/status packets, car-light
   subdevice/password/trigger control, microphone accessory behavior, FT001,
   and RG4.
13. Optional cloud fallback: only for models that still lack confirmed local
   control and only behind explicit user opt-in.

## Open Technical Questions

- Which SP52x/SP53x/SP54x commands should prefer BLE directly and which should
  move to LAN after provisioning?
- Whether custom 5xx `supportGetNetInfo=37` maps to an SP6xx-style command or
  to a LAN-only query.
- Which LAN discovery response, local socket frame, or BLE setup packet carries
  SP801E/SP802E network-controller commands and status.
- Which payloads encode SP801E Art-Net config, playlists, DXF import, and
  SP802E LFX/panel-layout operations.
- Whether scene UI models expose enough local state for scene editing or should
  initially expose scene recall only, and which packets carry recent-scene,
  favorite, timer, and DIY LFX storage state.
- Whether `SP-MIC` reports independent state or should be modeled only as an
  SP702E-owned accessory, and which BLE event packets carry microphone input.
- Whether `RG4` should additionally become a device trigger provider for
  remote/control events beyond its paired-node light entities.
- Whether fish-tank-specific controls for `FT001` map cleanly to standard
  `light`, `select`, and `number` entities once a verified BLE/LAN packet
  shape is recovered.
- Whether FT001 `FavoriteStore/Recall/Clear0-3` native labels correspond to
  direct local actions, app-only/cloud actions, or persisted favorite metadata,
  and which packet frames store, recall, clear, and enumerate those slots.
- Which FT001 packets create, edit, delete, and list timer records, and how
  `You can only add up to 5 timers!` and `Timer interface not supported.`
  should map to Home Assistant entities.
- Whether FT001 uses one of the shared native UUID pools (`ffe0`/`ffe1` or
  `ff12`/`ff14`/`ff15`) and how its `specFunctions=145` maps to command
  surfaces.
