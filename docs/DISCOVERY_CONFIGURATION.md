# Discovery And Configuration Approach

This integration should use discovery as an evidence pipeline, not as a direct
model-name shortcut. The SP541E LAN work proved the pattern:

1. Collect a discovery candidate.
2. Resolve it against catalog and legacy parity evidence.
3. Run only safe protocol probes.
4. Build a capability model from parsed state.
5. Create Home Assistant entities from capabilities, not from static guesses.

## Candidate Sources

Discovery candidates can come from:

- Home Assistant Bluetooth discovery: BLE address, local name, service UUIDs,
  manufacturer data, connectability, and RSSI.
- LAN discovery: SPNet UDP responses where proven, future DNS-SD/TXT evidence
  where proven, router/MAC hints, and manual host/IP fallback.
- Config-entry migration: old UniLED `ble`, `net`, and `zng` data, preserving
  unique IDs whenever a stable BLE address, MAC, mesh UUID, host, or manual
  device ID exists.
- Manual setup: model plus address/host/mesh identity when discovery does not
  fire.
- Optional cloud import: only for metadata and mesh credentials until the
  cloud command contract is proven.

Every candidate should keep an evidence bundle. The config flow should present
the best match and confidence level instead of silently trusting a single name.

## Confidence Levels

Use the same confidence model across BLE, LAN, and mesh:

| Level | Meaning | HA behavior |
|---|---|---|
| `verified` | Tested against real hardware or a live capture with command round-trip evidence | Enable normal control entities |
| `protocol_proven` | Old-UniLED parity or APK/capture evidence proves packet builders and parser fixtures | Enable control entities, expose confidence diagnostics |
| `discovered_only` | Device identity is known, but command/status protocol is not proven | Require manual confirmation before creating diagnostic-only entities |
| `unknown_similar` | Name/prefix resembles a supported family, but no exact match exists | Do not create command entities |

The old UniLED parity families and old-UniLED-backed Zengge/RG4 mesh profile
currently provide the `protocol_proven` floor for the overlapping BanlanX APK
models. SP541E LAN is `verified` for the local house-light hardware.

## Old UniLED Coverage Target

The minimum compatibility target is every old-UniLED device that overlaps the
BanlanX APK catalog and is backed by tested parity code, plus guarded
legacy-only entries for old devices that are absent from the APK:

- SP601/SP60x
- BanlanX v2
- BanlanX v3
- SP6xx/custom-5xx BLE-style command families
- Zengge/RG4-style mesh where old-UniLED packet/session evidence exists

The audit currently finds 51 old BLE model names, zero old NET model names, 49
BanlanX APK overlap names, and the old `lib/zng` Zengge mesh implementation.
The two remaining old BLE names, `SP107E` and `SP110E`, are cataloged as
separate `/legacy/uniled/...` rows. They resolve through BLE autodiscovery with
the old `ffe0`/`ffe1` UUID binding and use `protocol_proven` confidence because
their LED Chord/LED Hue command builders and status parsers are ported from old
UniLED. The old Zengge mesh implementation maps to the APK `RG4` row through
the `zengge_mesh` profile; exact RG4 names and Telink manufacturer-data
discoveries also use `protocol_proven` confidence while still exposing only the
limited, guarded mesh command surface. Legacy-only BLE rows remain separate
from the BanlanX APK catalog because the APK does not contain those records,
and their hidden configuration/edit surfaces stay blocked until packet behavior
is proven.

## Resolver Rules

The resolver should score evidence in this order:

1. Existing config-entry unique ID or migrated legacy identity.
2. Exact BLE local name or safe suffixed local name such as `SP601E_AABB`.
3. Exact LAN discovery model ID where the discovery packet is proven, such as
   SPNet model byte `0x5c` at payload offset `3` for SP541E.
4. Mesh UUID/manufacturer data decoded by a proven mesh parser.
5. Manual user-selected model.
6. Weak prefixes such as `SP5*` only as a config-flow wake-up filter.

Broad manifest matchers must never create entities directly. They only wake the
config flow; catalog transport validation and protocol confidence decide what
is created.

Current Bluetooth setup stores discovery provenance in each discovery-created
entry: `discovery_source=bluetooth`, `discovery_match` (`exact_label`,
`safe_suffix`, or `telink_mesh`), and `discovery_confidence`
(`protocol_proven` for old-UniLED/protocol-backed families and RG4/Zengge mesh,
`discovered_only` for catalog-only unported models). The Home Assistant
Bluetooth flow auto-creates entries only for `protocol_proven` matches;
`discovered_only` matches show a confirmation form before creating
diagnostic-only entities. These provenance fields are also exposed as
implemented diagnostic sensors so support data can show why the entry was
accepted or held as catalog-only. Discovery-object normalization delegates to
the same setup-data helper that the tests use, including `name`/`local_name`,
address, manufacturer data, and connectability fields. Tests now exercise all
51 old-UniLED BLE names through both exact and safe-suffixed Home
Assistant-shaped discovery objects, the two legacy-only `SP107E`/`SP110E` rows
as guarded legacy catalog entries, and RG4/Zengge mesh through exact-name and
Telink manufacturer-data discovery.
New direct-BLE entries keep the `ble:<address>` unique-ID shape, but the config
flow also checks old UniLED's raw-address BLE unique IDs before entry creation.
That lets migrated old UniLED BLE entries block duplicate manual or discovered
entries without changing the current setup identity. When an old direct-BLE
entry is migrated in place, command lights, effect/audio/chip/mode controls,
effect-type diagnostics, and SP601/SP60x scene recall entities reuse old
raw-address entity unique IDs, including old `master` and `channel_n` segments
for multi-output devices.
Migrated RG4/Zengge mesh entries keep old node entity IDs for the node light
and panel-status surfaces old UniLED actually created, using the decimal node
identity shape `_<zng_mesh_uuid>_node_<node_id>`. Newer mesh effect controls
keep UniLED Next IDs because old UniLED did not create equivalent entities.

Current LAN setup can also store provenance for the proven SP541E SPNet path:
`discovery_source=lan`, `discovery_match=spnet_model_id`, and
`discovery_confidence=verified`, exposed through the same diagnostic sensors.
The helper accepts the recovered SPNet response prefix plus model byte `0x5c`
at payload offset `3` only when a source host is available and the resolved
model is the command-proven SP541E/SPTech LAN path; other LAN families remain
manual-host or diagnostic-only until their own discovery and command contracts
are proven. Home Assistant startup now launches one SPNet UDP discovery pass to
limited broadcast plus locally derived `/24` directed broadcasts, then feeds
matching responses into the normal
discovery config-flow source. The startup pass is single-flight: an in-progress
scan is reused, completion or failure clears the stored task handle, and a
failed flow handoff for one SPNet response is logged without dropping later
responses. Live HA-host evidence shows the response also carries the network
MAC at payload offsets `5..10` and an `SP541E` name, so LAN discovery uses the
MAC as the legacy-compatible bare config-entry unique ID when present.
MAC-shaped LAN device IDs are also checked as case-insensitive duplicate
blockers before entry creation, so casing differences in migrated entries do
not create extra SP541E rows. Unrelated packets and non-SP541E model bytes are
still rejected by the setup-data guard.

## Probe Rules

Probes must be safe and reversible:

- Prefer read-only state queries before any write command.
- Serialize commands per device and keep a single transport session where the
  hardware behaves single-client-ish, as SP541E does.
- Treat zero-byte SPTech responses as likely session contention if HA or the
  official app owns the socket.
- Parse the first successful status response into a capability model before
  creating optional controls.
- Disable unavailable dynamic controls rather than exposing stale RGB/effect
  controls on mono or static-only hardware.

## Entity Rules

Home Assistant entities should be generated from normalized capabilities:

- Main light: power plus the color/brightness modes actually supported by the
  parsed state.
- Mode/effect selects: only when the current protocol exposes safe command
  builders and valid option maps.
- Numbers/switches: only when status data proves that speed, length, direction,
  loop, play/pause, sensitivity, or on/off animation settings apply.
- Diagnostics: evidence, support disposition, discovery confidence, and raw
  facts should be diagnostic entities or attributes, not normal controls.

For migrated old-UniLED entities, preserve old unique IDs where practical so
dashboard entity IDs survive upgrades.

## Branding And Assets

Do not copy or bundle original BanlanX/SPLED/old-UniLED logo or image assets in
the integration. APK image paths may appear only as string evidence in
diagnostics and audits.

The current integration keeps the `uniled` domain for migration compatibility.
That means Home Assistant may still associate the domain with any existing
domain-level brand icon supplied outside this repo. Fully removing that
domain-level brand association requires a deliberate domain migration, for
example to `uniled_next`, plus a compatibility/import path for existing
`uniled` config entries.
