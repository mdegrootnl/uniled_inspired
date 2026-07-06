# UniLED Next Implementation Status

Last updated: 2026-07-06

## Current Milestone

The current milestone is turning the APK-derived catalog into protocol-backed
Home Assistant entities family by family. The catalog/resolver foundation and
core entity planner are in place; ported legacy BLE families and custom 5xx
SP6xx-style BLE control now have limited command/state support, while unported
families remain recognized and diagnostic-first.

Implemented:

- Generated bundled catalog at
  `custom_components/uniled/core/catalog/models.json`.
- Repeatable generator at `scripts/generate_catalog.py`.
- Repeatable APK evidence audit at `scripts/audit_apk_evidence.py`, verifying
  profile package asset counts, curated evidence paths, raw APK/native string
  anchors, catalog-absent feature-package decisions, setup-guide asset anchors,
  scene native `.dynsym` export anchors and Thumb `.text` code anchors from
  `libscene_lfx.so`, SP802E native LFX `.dynsym` export anchors from
  `libwled_lfx.so`, SP630E/shared native LFX `.dynsym` export anchors from
  `liblfx.so`, bundled catalog freshness against `model_catalog.csv`, and an
  exhaustive 22-bucket APK asset-package inventory against
  `..\.codex\rev\BanlanX_3.3.1-analysis`. Current audited string-anchor
  counts are `sp630e=73`, `scene_ui=268`, `module_sp801e=38`, `sp802e=102`,
  `car_lights=70`, `fish_tank_lights=67`, `accessories=23`, `cloud=97`,
  `lan_network_setup=21`, `ble_plugin_contract=7`,
  `ble_notification_contract=5`, `scene_mesh_provisioning=3`,
  `rg4_provisioning=12`, and `sig_mesh_uuid=6`; the audited SP801E
  module-home setup guide asset
  group has 3 curated assets; the audited scene native export set has
  `.dynsym=378`, 16 paired IC/PWM API handlers, 4 IC-only API handlers,
  2 loop handlers, 5 state exports, 10 animation/self-test exports, and
  5 drive-type exports; the audited scene native code-anchor set verifies
  7 Thumb `.text` function bodies by address, size, SHA-256, and first/last
  bytes; the audited SP802E native export set has
  `.dynsym=186`, 35 matrix/effect/LFX/generator exports, and 6 detail
  anchors; the audited SP630E/shared native export set has `.dynsym=162`,
  34 renderer/music/PWM exports, and 7 detail anchors; the local Blutter HJ
  enum audit verifies 82 BanlanX app-command IDs from the arm64 Dart snapshot,
  including `getNetworkInfo=0x92`, `getArtNetConfig=0x21`,
  `setArtNetConfig=0x22`, `setLfxMode=0x53`, and
  `setLedPanelLayout=0x7e` as app-layer enum evidence, not proven wire
  packet envelopes; the catalog-source audit verifies all 191 bundled catalog
  rows still derive from the APK `model_catalog.csv` plus the two explicit
  legacy-only old-UniLED rows;
- Repeatable old-UniLED parity audit at `scripts/audit_legacy_uniled.py`,
  statically deriving 51 old BLE model names and zero old NET model names from
  the detached `..\uniled` source tree and enforcing that the old `lib/zng`
  Zengge mesh implementation maps to the new RG4/Zengge mesh profile. The audit
  proves the APK overlap is exactly the 49 catalog
  `legacy_uniled_supported` names and that `SP107E` and `SP110E` are
  represented only by separate `/legacy/uniled/...` catalog rows, not by
  BanlanX APK records. It also proves every explicit and inferred old
  direct-BLE config-entry shape migrates to a normalized UniLED Next BLE entry
  for the same model, model ID, and address, and that old Zengge mesh entries
  preserve `zng_mesh_<uuid>` identity while dropping old stored cloud
  credentials. The audit extracts the seven old BLE command-builder surfaces
  and proves every non-stub old command surface is covered by the ported parity
  profiles. `scene_save` remains an explicit old empty stub for
  SP601E/SP60x, the SP6xx old `build_effect_command` surface is covered by
  UniLED Next's mode/effect `light_mode` encoder path, legacy-only `SP107E`/
  `SP110E` are covered by the limited LED Chord/LED Hue parity profiles, and
  the audit now proves all 51 old BLE names still wake Bluetooth manifest
  matchers and resolve through exact-name and safe-suffix discovery as
  `protocol_proven` BLE setup entries that bypass the catalog-only confirmation
  form, while unsafe no-separator near misses such as `SP601EX` stay unknown.
  It also checks RG4 exact-name and
  generic Telink manufacturer-data discovery, including the old
  `zng_mesh_<uuid>` setup identity, with the same no-confirmation
  protocol-proven behavior. The old `mesh_uuid_unique` source anchor for that
  `zng_mesh_<uuid>` base identity is part of the entity-identity audit. RG4
  remains the limited old-UniLED-backed Zengge mesh path with BLE-mesh setup
  and core command/session evidence.
- The current classified APK asset buckets cover 1,218 assets.
- Repeatable support/evidence matrix generator at
  `scripts/generate_support_matrix.py`, with the generated snapshot checked in
  at `docs/SUPPORT_MATRIX.md`. The generator now includes per-row
  `support_blockers` and `support_blocker_count` values plus a support
  blocker/requirement summary aggregated from those rows, so the remaining APK
  device work is visible as counted blockers rather than only as per-model
  prose. Runtime diagnostics expose the same blocker rule through
  `support_blockers` and `support_blocker_count`.
- Discovery/configuration approach documented at
  `docs/DISCOVERY_CONFIGURATION.md`. The standard is evidence-first:
  discovery creates candidates, resolver scoring uses stable identities and
  old-UniLED/APK/probe evidence, safe read-only probes establish capabilities,
  and Home Assistant entities are generated from parsed capabilities rather
  than broad manifest matches. Bluetooth- and SP541E LAN-discovered entries
  now store and expose diagnostic sensors for `discovery_source`,
  `discovery_match`, and `discovery_confidence`, so diagnostics can distinguish
  protocol-backed old-UniLED overlap, verified SPNet LAN setup, and RG4/Zengge
  mesh from catalog-only matches.
- Home Assistant-independent core package under
  `custom_components/uniled/core`.
- Typed catalog schema with protocol family, transport kind, support level,
  model metadata, decoded APK `connectCaps`, `specFunctions`, and `colorCap`
  labels, feature metadata, and legacy parity marker.
- Generated support levels that mark protocol-backed BLE and BLE-mesh families
  as `limited` and keep unported families `recognized`.
- Searchable `ModelCatalog` registry with model ID lookup, name lookup,
  canonical model resolution, user-facing model filtering, and hidden placeholder
  filtering.
- Tests proving catalog counts, support-level assignments, family assignments,
  transport assignments, decoded `connectCaps` parity with generated
  transports, decoded `specFunctions`/`colorCap` coverage for all APK values,
  selected APK feature-key preservation, old UniLED parity candidates, and
  legacy-only old UniLED modules that are intentionally separated from the
  BanlanX APK source.
- Support matrix tests proving the current catalog coverage totals: 191 catalog
  records, 190 user-facing records, 152 canonical user-facing models,
  95 `limited`, 57 `recognized`, 124 BLE routes, 27 BLE-mesh routes,
  41 LAN routes, 39 optional cloud profiles, 52 old-UniLED parity/evidence
  candidates including RG4's Zengge mesh protocol evidence, and 94 normal
  command-protocol-ready models plus RG4's mesh-specific limited path. The
  same tests pin representative open blocker totals, including
  `command_protocol_pending=57`, `scene_command_envelope_pending=50`,
  `lan_frame_pending=40`, `account_token_schema_pending=39`,
  `ble_uuid_binding_pending=30`, and `firmware_v1_1_required=26`.
- Entity planner at `custom_components/uniled/core/planner.py`.
- Planned feature/entity specs for diagnostics, catalog model IDs, catalog
  parent IDs, duplicate-record variant counts, lights, effects, pixel
  configuration, audio controls, scene entities, car-light accessories, network
  info, and mesh roles.
- Home Assistant entity metadata helper at
  `custom_components/uniled/entity_metadata.py`. Command-capable lights,
  numbers, selects, switches, scenes, buttons, and implemented diagnostic
  sensors now get translation keys. Dynamic placeholders preserve output
  channels, scene slots, paired Zengge mesh nodes, and Zengge panel status
  nodes while retaining literal feature names as fallbacks. The same helper now
  derives stable entity unique-ID bases and device-registry identifiers from
  config-entry `unique_id` or normalized setup data instead of volatile
  `entry_id` values, with Bluetooth device-registry connections for BLE and
  BLE-mesh entries.
- Protocol command package under `custom_components/uniled/core/protocols`.
- Legacy parity command builders for `banlanx_601`, `banlanx_60x`,
  `banlanx_v2`, `banlanx_v3`, and `banlanx_6xx`, including old-UniLED
  chip-order command parity for SP601/SP60x output channels,
  SP601/SP60x scene-loop command parity, and BanlanX2/BanlanX3.
- BanlanX3 DIY status diagnostics. The old-UniLED status metadata bytes for
  DIY effect type and DIY color count are now exposed as diagnostic
  `diy_effect_type` and `diy_color_count` sensors; DIY edit/save frames remain
  hidden because the available old-UniLED evidence is comment-level only.
- APK-matched custom 5xx command builder for `banlanx_custom_5xx`, reusing the
  SP6xx-style frame format while preserving its distinct catalog family.
- Structured protocol-evidence diagnostics at
  `core/protocol_evidence.py`. Command-backed families now distinguish exact
  old-UniLED parity, APK catalog family inference, and custom 5xx
  SP6xx-style BLE command mapping in runtime diagnostics, entity plans, and the
  generated support matrix.
- SP6xx-style custom/DIY slot diagnostics. The status byte parsed from the old
  UniLED offset `52` is now exposed as the diagnostic `custom_effect_slot`
  sensor for SP6xx and custom 5xx families, while custom slot edit/save
  commands remain hidden pending packet evidence.
- APK `/sp630e` surface diagnostics for SP6xx and custom 5xx models. The new
  `sp630e_profile` preserves route, control-surface, favorite-limit,
  timer-limit, music-asset, network, remote, motor, method, Blutter app-command
  ID, data-model, shared native LFX, catalog, gap, full package-asset, and APK
  evidence counts from `packages/sp630e` without exposing unproven
  DIY/favorite/timer/remote write flows. The SP630E/shared profile now carries
  35 app-layer command ID anchors for the existing `/sp630e` control surfaces.
  The evidence audit also verifies `liblfx.so` has 162 dynamic symbols, 34
  exported renderer/music/PWM anchors, and 7 pinned symbol details.
- APK asset-package inventory at `core/apk_assets.py`. All 22 package-count
  buckets from `asset_package_counts.txt` are classified as catalog device
  profiles, non-catalog feature packages, shared app shell assets, shared
  device components, root shared assets, or third-party assets. The audit now
  fails if a future APK refresh adds an unclassified package bucket, removes a
  classified bucket, changes a shared-package count, or drops representative
  shared assets.
- RG4/accessories APK diagnostics for the BLE-mesh remote surface. The
  `mesh_profile` now preserves `/device/ble_mesh_rc`,
  `/device/ble_mesh_rc/provisioning_guide`, provisioning callback states,
  exact recovered provisioning strings for the one-touch title, 90-second
  timeout, provisioning-control warning, rapid-flash abnormal state,
  provisioned-device count, provisioner address log, capabilities anchors, PDU
  errors, the six APK-recovered Bluetooth SIG Mesh provisioning/proxy UUID
  strings, Blutter app-command ID hints for composition/provisioner/zone/node
  lookup and group/subgroup/master-heartbeat operations, the full 9-asset
  `packages/accessories` package count, asset paths, and string evidence. A
  disabled planned `mesh_provisioning_state` select exposes the nine
  callback-state labels without exposing unproven one-touch provisioning or
  remote-button event controls. RG4 support disposition now
  reports the remaining control blockers as
  `mesh_remote_event_parser_pending`, `mesh_provisioning_frame_pending`,
  `mesh_group_management_pending`, and
  `mesh_node_management_controls_pending`; the
  matching `mesh_control_blocker_count=4` diagnostic is readiness status only.
  Paired command nodes now expose guarded effect speed and effect level number
  controls by resending the current old-UniLED `0xED` effect packet with the
  edited byte.
- Home Assistant-independent command session and transport boundary at
  `custom_components/uniled/core/session.py` and
  `custom_components/uniled/core/transports`.
- BLE profile facts for ported legacy and custom 5xx families at
  `custom_components/uniled/core/transports/ble.py`.
- APK BLE evidence diagnostics for direct-BLE catalog models at
  `custom_components/uniled/core/transports/ble.py`, including recovered
  Flutter BLE channels, Java bridge methods for adapter/discovery/device
  operations, method arguments, returned scan/service/characteristic/RSSI/MTU
  fields, UUID candidates `ff12`, `ff14`, `ff15`, `ffe0`, and `ffe1`, a normalized
  per-UUID inventory backed by exact APK string anchors, decompiled adapter
  state result fields, scan, connection-state, and notification event payload
  contracts, discovery default/scan-filter behavior, and explicit protocol-gap
  notes for families without a proven command profile. Lightweight diagnostics
  expose UUID binding status, known service UUID count, UUID-pool,
  UUID-inventory, unbound-candidate, legacy-candidate, plugin-method,
  plugin-argument, plugin-result-field, grouped result-field,
  adapter-state-result-field, event-field, boolean-event-channel, event-hint,
  plugin-contract, plugin-error-code, plugin-channel, and BLE protocol-gap
  counts. The three APK-only `ff12`/`ff14`/`ff15` candidates remain
  diagnostics-only until family-specific service/characteristic binding is
  proven.
- LAN profile facts for every LAN-capable catalog model at
  `custom_components/uniled/core/transports/lan.py`, including APK
  `supportGetNetInfo`, `maxDataLength`, host-network method names, discovery
  plugin/channel hints, Bonsoir/Android NSD method arguments, decompiled
  Bonsoir service-type handoff flow, Bonsoir TXT-query flow,
  Android `NsdManager` method names, Bonsoir discovery event names, Bonsoir
  service event fields, Bonsoir service normalization hints,
  multicast-lock method names, the universal
  `/device/universal/network/config` setup route,
  AP/STA network setup prompts, local-only/cloud-binding warnings, mDNS
  group/port/TTL, raw datagram timeout/buffer hints, exact raw-socket and
  discovery-status string anchors, SP801E-specific
  `module_home` setup-guide images (`sp801e_init`, `sp801e_ble`, `sp801e_ap`),
  targeted APK
  discovery-gap notes, and explicit command-protocol-pending status.
  Lightweight diagnostics expose LAN host-network method, discovery-plugin,
  discovery-channel, network-setup route/prompt, SP801E setup-guide asset,
  cloud-setup prompt,
  multicast-lock method, Bonsoir method, Bonsoir argument, Android NSD method,
  Bonsoir discovery event, Bonsoir service event field, Bonsoir service
  normalization, Bonsoir service-type flow, Bonsoir TXT-query flow, discovery-gap,
  UDP raw-socket hint, discovery-status hint, socket timeout, UDP receive
  buffer, mDNS TXT query timeout, TXT record type/query class, and mDNS TXT
  buffer facts.
- Initial Home Assistant-side `UniLEDLANTransport` holder at
  `custom_components/uniled/lan.py`. Runtime setup now attaches this holder for
  host-backed LAN entries and reports `lan_transport_ready` without creating a
  command session or sending LAN bytes while packet frames remain unmapped.
- APK-derived BanlanX cloud profile facts at
  `custom_components/uniled/core/cloud.py` for every `cloud_optional` catalog
  model. The profile records recovered `app.ledhue.com` API bases, grouped
  account-auth/lifecycle endpoints such as `/auth/refresh-token`,
  `/auth/sign-in`, `/auth/signIn2`, `/auth/signUp2`, `/user/sign-out`, and
  password-token routes, plus `/home/device/auth/*`, `/home/device`
  lifecycle, `/user/device`, `/user/local-device`, `/user/btmesh`, root
  device, manual/resource, document URL, and Alexa account-linking endpoints.
  It exposes diagnostic counts for base URLs, grouped endpoints, the 9 endpoint
  inventory groups, the one command-adjacent endpoint, unresolved base URL
  bindings, unproven auth bindings, device-auth/account-auth/content/voice/document
  groups, the split device endpoint buckets, transport/gap hints, auth-token
  hints, HTTP header hints, signature/nonce hints, and split token/header/signature
  request-contract buckets, plus the recovered raw command-adjacent endpoint string
  `/user/device/post/raw`. It also preserves raw `document.ledhue.com`
  privacy/agreement/FAQ URL strings and auth-token string hints such as
  `user:token`, `user:refresh_token`, `refreshToken2`, `setupAuth`,
  `serverAuth`, and `resetAuth`, plus `Authorization`, `Bearer`,
  `S-Timestamp`, `content-type:`, `application/json`, `buildSignature`,
  `, buildSignature:`, `, nonce =`, `encrypt nonce =`, and `decrypt nonce =`
  as request/signature anchors. Explicit gaps remain for auth, headers, region
  routing, ownership/bind lifecycle, and `/user/device/post/raw` command
  envelopes. The profile also exposes five structured cloud command
  blockers for account-token schema, request signing/headers, region/reauth,
  raw-command JSON envelope, and device-bind ownership lifecycle. These 97
  cloud string anchors are enforced by the APK evidence audit. The profile is
  diagnostics-only and separate from the old
  MagicHue/Zengge cloud metadata importer.
- APK-derived network-controller profile facts at
  `custom_components/uniled/core/network.py`, including SP801E's
  `packages/module_sp801e` Art-Net/port/content-creation surface and SP802E's
  `packages/sp802e` LFX editor, settings routes, LED layout route, all 20
  regular LFX effect icon names, all 30 GIF preview assets, diagnostic
  surface/content-mode/LFX-effect/GIF-preview counts, per-model
  catalog/transport hints, SP801E Art-Net field, port field, playlist-action,
  and DXF constraints, SP802E matrix-music setter controls, and explicit
  protocol gaps including the missing concrete DNS-SD service type. A targeted
  APK/Blutter string pass found multicast/raw datagram anchors but no concrete
  `_tcp`/`_udp` service type. The profile
  records full APK package asset counts separately from curated evidence:
  143 assets for `packages/module_sp801e` and 81 assets for `packages/sp802e`.
  It also preserves method/native anchors from `libapp.so` strings:
  `getNetworkInfo`,
  `getArtNetConfig`, `setArtNetConfig`, playlist methods, SP802E network-info
  and LFX setter names, raw SP801E channel/port/playlist storage labels, raw
  SP802E LFX, matrix, GIF-frame, and Wi-Fi state labels, and `libwled_lfx.so`
  matrix/LFX
  symbols including LFX parameter helpers, effect generators, matrix/mode
  helpers, and pixel/frame helpers such as `render_frame` and
  `get_frame_data`. Lightweight
  diagnostics expose network Art-Net field, port field, playlist-action,
  matrix-music-control, route, regular-LFX asset, LFX GIF asset, app-method,
  workflow-hint, raw-string, import-constraint, catalog-hint, transport-hint,
  native-library-hint, native-frame-helper, native-LFX-param,
  native-effect-generator, native-matrix-mode, native-pixel-helper,
  native-export-hint, protocol-gap, APK package-asset, APK asset-evidence, and
  APK string-evidence counts.
- APK-derived car-light profile facts at
  `custom_components/uniled/core/car_lights.py`, including package route hints,
  zone names exposed as a count diagnostic, trigger animation names exposed as
  a count diagnostic, APK route/settings control surfaces exposed as a count
  diagnostic and planned disabled select, animation assets, trigger-image
  assets, zone-image assets, subdevice/password accessory assets, and
  native-string model roles for `SP701E`, `SP702E`, and `SP-MIC`, setup
  requirements, setup-flow prompts, raw setup keys such as `isPrimary` and
  `subUni`, structured setup stages/order for `SP701E` before `SP702E` and
  `SP-MIC` after `SP702E`, subdevice management labels, planned disabled
  subdevice-filter selectors, device-password entry/change/policy and reset
  labels, password-reset procedure hints,
  planned disabled password-flow-state selectors, `sp_trigger` storage hints,
  planned disabled trigger-action selectors, Blutter-recovered app command ID
  hints for `configZoneKeyAddrMapping` (`0x24`), `configTrigger` (`0x36`),
  and `configWelcomeLights` (`0x91`), BLE-only catalog hints, the
  APK-proven `SP-MIC` -> `SP702E` accessory dependency, and explicit
  protocol-gap notes.
  The full `packages/car_lights` asset manifest has 58 assets, tracked
  separately from the curated 47 high-signal evidence assets.
  Lightweight diagnostics expose car-light accessory-asset, animation-asset,
  trigger-image-asset, zone-image-asset, subdevice-hint, subdevice-filter,
  password-hint, password-flow-state, password-entry-hint,
  password-policy-hint, password-reset-hint, trigger-storage-hint,
  trigger-action, control-surface, route,
  setup-requirement, setup-flow-hint, setup-key-hint, model-role-hint,
  app-command-ID, setup-stage, setup-order, required-controller, protocol-gap, APK
  package-asset, APK asset-evidence, and APK string-evidence counts.
  Runtime support disposition now includes car-light command blockers:
  `car_light_ble_opcode_pending`, `car_light_status_parser_pending`,
  `car_light_zone_command_pending`, `car_light_trigger_packet_pending`,
  `car_light_subdevice_binding_pending`, and `car_light_password_flow_pending`;
  SP-MIC also includes `car_light_sp_mic_event_pending`.
  SP-MIC support disposition still includes `accessory_dependency=SP702E`;
  setup eligibility remains BLE so catalog setup coverage is unchanged.
- APK-derived fish-tank profile facts at
  `custom_components/uniled/core/fish_tank.py`, including FT001 package route
  hints, two light-channel labels, timer/favorite/settings/rename workflow
  surfaces, Windmill/springwater effect hints, raw effect string anchors
  (`waterdrop`, `Flowing Water`, `Spring Water2`, `Stromend Water`),
  favorite-loop labels, the `FishTankLights:fw_prompted_` firmware-prompt key,
  `connectCaps=7`,
  `specFunctions=145`, `colorCap=1`, favorite-effect service/storage anchors,
  four favorite slots/actions exposed as count diagnostics, planned disabled
  Store/Recall/Clear favorite-action, Loop/Stop favorite-loop-action, and
  Save/Remove timer-action selects,
  exact native `You can only add up to 5 timers!` limit text exposed as a
  timer-limit diagnostic, shared app
  setter names, raw effect/timer/brightness string hints such as `timerConfig`,
  `newTimerId: 2`, `raw-brightness-`, `whiteBrightness`, and
  `white_brightness`, complete fish-tank asset evidence split into icon,
  image, channel, timer, favorite, and effect buckets, and
  command-protocol-pending status. The full `packages/fish_tank_lights`
  manifest has 30 assets, which matches the curated evidence list. The APK
  evidence audit verifies 67 curated FT001 string anchors, including routes,
  app setter/storage methods, favorite service/storage hints,
  favorite store/recall/clear labels, timer storage hints, favorite-loop
  labels, raw effect labels, timer labels, firmware-prompt storage, and raw
  brightness/white-brightness state labels. Lightweight
  diagnostics expose fish-tank
  light-channel, control-surface, route, effect-hint, effect-string-hint,
  icon-asset, image-asset,
  channel-asset, timer-asset, favorite-asset, effect-asset, workflow-hint,
  favorite-action, favorite store/recall/clear, favorite-action-type,
  favorite-loop-hint, favorite-loop-action, firmware-prompt-hint,
  timer-slot, timer-action, timer-hint, timer-string, app-method,
  app-command-ID,
  data-model-hint, favorite-service, favorite-storage, timer-storage,
  brightness-state, raw-string, brightness-string, protocol-gap, APK
  package-asset, APK asset-evidence, and APK string-evidence counts.
- APK-derived scene profile facts at
  `custom_components/uniled/core/scene.py`, including the shared
  `packages/scene_ui` surface for `banlanx_scene_ui` and
  `banlanx_scene_mesh`, preset scene image folders, visible settings/control
  surfaces, route hints, LFX creation routes, diagnostic preset,
  control-surface, route, mode-icon, mode-effect, and LFX-route counts,
  app-level `setLfx*` method anchors, recent-scene/favorite storage anchors,
  planned disabled recent-scene/favorite/timer/DIY action selectors, raw
  timing-task and white-brightness string hints, planned disabled
  white-brightness anchor selectors, catalog/transport hints, the
  SP31XE/SP32XE firmware V1.1+ one-touch provisioning requirement,
  90-second automatic provisioning timeout, provisioning-control warning,
  `libscene_lfx.so` IC/PWM handler anchors, paired IC/PWM API capability
  groups, IC-only API capability groups, loop handlers, frame/opcode/state
  helper anchors, state export offsets/sizes, native color-order/LED-type
  anchors, PWM table anchors, music/effect routine anchors, PWM driver/write
  helpers, native persistence handler anchors, native-library/export hint
  counts, and
  the 80 recovered `ic_mode_*` mode-icon names as planned disabled
  scene-mode options. The full `packages/scene_ui`
  asset manifest has 204 assets, tracked separately from curated evidence
  paths. The APK evidence audit verifies 224 raw scene string anchors,
  including the universal timer list/config routes, SP31XE/SP32XE firmware
  V1.1, and one-touch provisioning strings.
  Lightweight diagnostics expose scene app-method, storage-hint, recent-action,
  app-command-ID, favorite-action, timer-route, timer-action, DIY-action,
  white-brightness-anchor,
  raw-string, native-handler, native-paired-API, native-IC-only-API,
  native-loop-handler, native-library-hint, native-frame-helper,
  native-opcode-helper, native-state-helper, native-state-export,
  native-color-order,
  native-PWM-table, native-music-effect, native-PWM-driver,
  native-persistence-handler, native-export-hint, setup-requirement,
  catalog-hint, transport-hint, protocol-gap, APK package-asset,
  APK asset-evidence, and APK string-evidence counts.
- BLE mesh profile facts at `custom_components/uniled/core/transports/mesh.py`,
  including old UniLED Telink/Zengge UUIDs, manufacturer IDs, default mesh UUID,
  notification-based status behavior, pairing requirement, effect names,
  command names, the `0xED` effect packet's effect/speed/level fields,
  Blutter app-command ID hints for mesh composition, provisioning, group, and
  node-management intent names, and guarded paired-node speed/level number
  controls plus explicit gaps for
  remote events, panel status, and non-light mesh entities. BanlanX scene-mesh
  records now also
  expose a diagnostics-only mesh profile with the shared `/device/scene_ui`
  route, `packages/scene_ui` package count, exact three-line SP31XE/SP32XE
  one-touch provisioning guide, the same six APK-recovered Bluetooth SIG Mesh
  UUID anchors, the same diagnostics-only mesh app-command ID count, and
  explicit missing frame-map gaps, without exposing RG4 provisioning callback
  controls. Their support disposition now
  includes `firmware_v1_1_required`, `provisioning_frame_pending`, and
  `scene_mesh_routing_pending` while command support stays pending.
- Telink/Zengge mesh advertisement parsing that extracts mesh UUID, node ID,
  and node type from old-UniLED manufacturer-data offsets.
- Telink/Zengge mesh packet helpers at
  `custom_components/uniled/core/protocols/zengge_mesh.py`, porting old UniLED
  AES block reversal, checksum, payload crypting, command packet layout,
  pairing packet, session-key derivation, and CRC16 behavior.
- Old-UniLED-compatible Zengge command builders for status-notification kick,
  fallback status query packet, power, brightness, RGB, CCT, warm white, and
  dynamic effect packets. The dynamic effect builder preserves the old
  `0xED [0xff, effect, speed, level]` shape; tests now pin non-default speed
  and level bytes, and paired command nodes expose guarded speed/level number
  entities by resending the current effect packet with the edited byte.
- Old-UniLED-compatible Zengge notification parsing for decrypted `0xDC`
  status messages. The parser extracts the two five-byte node blocks, maps
  power, brightness, RGB HSV, CCT percentage, dynamic effect state, panel
  status, old-UniLED strip/bulb/panel/bridge role labels, and node diagnostics
  into normalized core state.
- Core-only `ZenggeMeshSession` scaffold that remembers pairing randoms,
  derives and stores session keys, builds encrypted node commands from a paired
  session, registers node metadata, and applies decrypted or encrypted
  notifications. It is deliberately not wired to Home Assistant entities yet.
- Core-only `ZenggeMeshTransport` contract and `ZenggeMeshConnection` adapter
  for the future Home Assistant BLE mesh transport. The contract separates pair
  characteristic writes/reads, status characteristic writes, and encrypted
  command characteristic writes instead of reusing the single-UUID BanlanX BLE
  transport shape, and exposes pass-through methods for the currently ported
  Zengge power, brightness, RGB, CCT, warm-white, and effect commands.
- Initial Home Assistant-side `UniLEDZenggeMeshTransport` class that satisfies
  the pair/status/command characteristic split for Telink/Zengge mesh nodes.
  Runtime setup can attach it as a mesh transport holder without using the
  normal BanlanX byte-session path.
- Runtime-level Zengge mesh attachment. `UniLEDRuntime` can now hold a
  `ZenggeMeshSession` and `ZenggeMeshConnection`, register the discovered node
  context from config-entry data, report mesh transport/paired state in
  diagnostics, and close the mesh transport without setting the normal
  `session_ready` command-entity gate.
- Runtime-level `mesh_role` diagnostics for RG4/Zengge entries now summarize
  transport readiness, pairing state, total known nodes, command-capable node
  count, strip node count, bulb node count, panel node count, and whether a
  bridge node was seen, using only context/parser metadata. The same values are
  now exposed as structured diagnostics: `mesh_known_node_count`,
  `mesh_command_node_count`, `mesh_strip_node_count`,
  `mesh_bulb_node_count`, `mesh_panel_node_count`, and `mesh_bridge_seen`.
- Diagnostic sensors for known Zengge RGB/CCT panel nodes. These preserve old
  UniLED's panel-as-sensor behavior by reporting `Online`/`Offline` from parsed
  notification status blocks without enabling panel commands.
- Runtime-level guarded Zengge node command helpers. Once the mesh connection is
  paired, these helpers can target known command-capable mesh nodes with power,
  brightness, RGB, Kelvin CCT, warm-white, and dynamic effect commands. Unknown
  nodes, bridge nodes, panel nodes, and unpaired sessions are rejected before any
  transport write. Successful writes update only the target node's optimistic
  normalized state and mesh diagnostics. The control-payload-backed helpers
  preserve Home Assistant transition seconds as old-UniLED gradual-transition
  bytes; dynamic effect packets remain unchanged because their payload shape is
  separate.
- Initial Home Assistant light wiring for Zengge mesh nodes. After pairing,
  known command-capable RG4/Zengge nodes become runtime light features and the
  light platform dispatches power, brightness, RGB, color-temperature,
  warm-white, and effect requests through the guarded mesh helpers. Mesh-node
  lights advertise transition support for control-payload-backed commands.
- Initial Home Assistant effect-select wiring for paired Zengge mesh nodes.
  After pairing, known command-capable RG4/Zengge nodes get one effect select
  backed by the old-UniLED effect table and guarded mesh effect command helper.
  Number, switch, remote-trigger, and other non-light mesh entities remain
  pending.
- HA-independent MagicHue/Zengge cloud metadata parser at
  `custom_components/uniled/core/protocols/zengge_cloud.py`. It preserves old
  UniLED country-server routing, endpoint paths, login MD5 password hashing,
  AES-ECB `checkcode` construction, mesh location credentials (`meshKey`,
  `meshPassword`, `meshLTK`, `placeUniID`, `displayName`), and cloud
  `deviceList` node fields (`meshUUID`, `meshAddress`, `deviceType`,
  `wiringType`, name, and area metadata).
- Live MagicHue/Zengge cloud client helper. The core async fetch function uses
  an injected requester, performs the old login, mesh-list, bridge, and
  mesh-device request sequence, then feeds the result into the cloud metadata
  parser.
- Cloud-derived Zengge setup data. `zengge_cloud_setup_entry_data()` converts
  parsed MagicHue mesh metadata into config-entry data with the old
  `zng_mesh_<hex(uuid)>` unique ID shape, redaction-friendly credential fields,
  and a `mesh_nodes` list consumed by runtime setup.
- Cloud-refresh Zengge setup data. `zengge_cloud_update_entry_data()` merges a
  refreshed MagicHue mesh into an existing entry, preserving entry identity and
  unrelated data while replacing stale cloud-owned credentials and node facts.
- Optional config-flow MagicHue import for Bluetooth-discovered RG4/Telink mesh
  entries. Users can skip the cloud step to keep advertisement-only setup, or
  provide MagicHue username/password/country to fetch matching mesh metadata
  before the entry is created.
- The MagicHue/Zengge cloud import is now family-gated to RG4/Zengge mesh
  entries. BanlanX scene-mesh models such as `SP310E` still use the `ble_mesh`
  setup transport, but they create local diagnostic entries directly and keep
  their BanlanX scene/provisioning blockers instead of entering the old-Zengge
  cloud metadata flow.
- Manual RG4/Telink mesh setup. Users can create a BLE-mesh entry from a
  Bluetooth address and mesh UUID, optionally provide node ID/type/wiring for
  cloudless command-light setup, and then use the same optional MagicHue import
  step before entry creation.
- Options-flow MagicHue refresh for existing RG4/Telink mesh entries. It uses
  the current Home Assistant options-flow pattern, fetches matching mesh data by
  stored mesh UUID, updates config entry data through `async_update_entry`, and
  reloads the entry so runtime node contexts are rebuilt while keeping MagicHue
  username/password transient.
- `async_setup_entry` now uses a shared transport-attachment helper that keeps
  normal BLE models on `DeviceSession` while attaching RG4/Zengge entries to the
  mesh connection when a BLE address and Telink mesh profile are available.
- Coordinator mesh-notification routing can forward encrypted Zengge status
  notifications into the mesh session and records decrypt/parse errors in
  diagnostics.
- Zengge mesh credential plumbing. Runtime pairing can now use entry-provided
  `mesh_key` and `mesh_password` values, defaults to old UniLED's
  `ZenggeMesh` / `ZenggeTechnology` credentials when absent, and redacts those
  fields plus cloud `mesh_ltk` from diagnostics.
- Diagnostic Zengge mesh refresh. The first coordinator refresh can attempt
  pairing with the configured/default credentials and send the old-UniLED
  `0x01` status notification kick. Pairing/authentication failures are recorded
  in diagnostics without failing setup or opening command-entity gates.
- Home Assistant-independent normalized state model at
  `custom_components/uniled/core/state.py`.
- Legacy parity status parsers for `banlanx_601`, `banlanx_60x`,
  `banlanx_v2`, `banlanx_v3`, and unencrypted `banlanx_6xx` status packets.
  The SP6xx parser now preserves old-UniLED's split color offsets: static
  color modes read stored RGB from bytes `37..39`, while dynamic/sound color
  modes read live RGB from bytes `47..49`; dynamic white/CCT modes use bytes
  `50..51`. Dev_v3 SPTech custom mode evidence is preserved as `Custom Solid`
  (`0x07`) and `Custom Gradient` (`0x08`) for gradient-capable SPI RGB/RGBW
  light types.
- Custom 5xx status parsing through the same unencrypted SP6xx offset map, with
  diagnostics preserving `banlanx_custom_5xx`.
- Stateful notification frame assemblers for the legacy BLE packet formats:
  `0x53 0x43` headered packets, `0x36 0x38` headered packets, BanlanX3 indexed
  packets, and direct SP6xx frames.
- Home Assistant runtime shell for config-entry model resolution, typed
  `entry.runtime_data`, static coordinator setup, diagnostics, and implemented
  catalog diagnostic sensors.
- First command-capable Home Assistant light platform at
  `custom_components/uniled/light.py`, exposed only for entries with an attached
  `DeviceSession`. SP601 and SP60x now expose the aggregate light plus
  disabled-by-default physical output lights using the old-UniLED channel
  builders, with SP602E limited to four physical outputs and SP608E to eight.
  SP601 aggregate power, brightness, and RGB writes fan out to Output 1 and
  Output 2 because that protocol has no all-output mask; SP60x aggregate light
  writes keep using its all-output mask. Runtime optimistic state mirrors these
  aggregate writes onto the physical output states.
- First command-capable Home Assistant number, select, and switch platforms at
  `custom_components/uniled/number.py`, `custom_components/uniled/select.py`,
  and `custom_components/uniled/switch.py`, exposed only for entries with an
  attached `DeviceSession`.
- First Home Assistant button platform at `custom_components/uniled/button.py`.
  It exposes a diagnostic `refresh` button only when an existing runtime
  refresh path is attached: a normal `DeviceSession` or a Zengge mesh transport.
- Session-backed SP6xx advanced controls for on/off animation effect, on/off
  animation speed, on/off animation pixel count, power-restore behavior,
  effect play/pause, and color/white coexistence where the light type supports
  it.
- Session-backed SP6xx light-type and chip-order configuration controls using
  the old UniLED `0x6A`/`0x6B` command sequence and light-type-specific chip
  order permutations.
- SP6xx RGBW, RGBWW, white-level, CCT, and dynamic-RGB command builders using
  the old UniLED `0x51`, `0x52`, `0x57`, `0x60`, and `0x61` frames.
- Runtime and Home Assistant light parity for old-UniLED SP6xx sound modes:
  brightness requests in sound color `0x05` or sound white `0x06` do not emit
  `0x51` brightness frames and keep local brightness at `0xFF` for SP6xx and
  custom 5xx runtimes. The SP6xx/custom-5xx status parser now mirrors the
  same read-side state: sound color and sound white notifications report
  brightness `0xFF` while preserving raw color and white level bytes. Parsed
  audio input and sensitivity are exposed only when the status is powered and
  currently in a sound mode, matching old UniLED's read-side gate. Home
  Assistant audio-input and sensitivity command entities follow that parsed
  availability while low-level builders remain explicit commands. Parsed
  `effect_loop` is similarly mode-gated and is only exposed for dynamic and
  sound modes.
- Runtime and Home Assistant light parity for old-UniLED SP6xx brightness
  selectors: color-mode brightness uses the `0x51` selector byte `0x00`, while
  white/CCT-mode brightness uses selector byte `0x01` through the white-level
  command path.
- Runtime and Home Assistant light parity for old-UniLED SP6xx RGB tuning:
  static RGB carries brightness inside the `0x52` RGB frame, while dynamic and
  sound RGB use only the brightness-free `0x57` tuning frame even when a HA
  request includes brightness alongside RGB. Static RGB frames reuse the
  current brightness when no new brightness is supplied.
- Runtime and Home Assistant light parity for old-UniLED SP6xx white requests:
  HA white writes first switch color modes to the matching white mode with a
  `0x53` light-mode frame and a light-type-valid effect, then write the
  `0x51` white level unless the resulting mode is sound white.
- Runtime and Home Assistant light support for SP6xx color modes derived from
  parsed light type and coexistence state: RGB, RGBW, RGBWW, WHITE,
  COLOR_TEMP, and BRIGHTNESS.
- Manual config flow that validates selected models against the generated
  catalog and creates entries with stable local identifiers.
- Conservative Bluetooth config-flow step that creates an entry only when the
  advertised name resolves to an exact catalog name, APK friendly label, or a
  safely suffixed catalog name such as `SP601E_AABB`, when BanlanX manufacturer
  data byte `0` resolves to a user-facing APK BLE model, or when a generic
  Telink mesh advertisement can be parsed. The flow delegates Home Assistant
  discovery-object normalization to the Home Assistant-independent setup-data
  helper, so `name`/`local_name`, address, manufacturer data, and connectability
  are tested without importing Home Assistant. It rejects non-connectable
  discoveries because all current BLE and BLE-mesh setup paths require outgoing
  writes.
  Resolved discovery still has to pass the catalog transport gate, so broad
  manifest matches cannot create BLE entries for LAN-only models such as
  `SP801E`, manufacturer-data matches cannot create BLE entries for LAN-only
  catalog rows, and near misses such as `SP601EX` stay unknown. Discovery-created
  BLE and BLE-mesh entries also require a Bluetooth address because runtime
  transport attachment resolves devices by address. Friendly labels are input
  aliases only; config-entry data stores the canonical APK catalog `name`.
  Direct-BLE setup keeps the new `ble:<address>` unique-ID shape, while
  `setup_entry_compatibility_unique_ids()` reports old UniLED raw-address BLE
  IDs and SPNet bare-MAC LAN IDs as duplicate blockers. Config-flow artifact
  tests now guard that manual, Bluetooth discovery, and LAN discovery setup
  paths call the compatibility check before creating entries, that Bluetooth
  discovery checks catalog-only confirmation before creating an entry, and that
  delayed Bluetooth confirmation or RG4/Zengge cloud-import entry creation
  rechecks setup unique IDs immediately before creating an entry. Migrated old
  direct-BLE entries with raw
  address config-entry unique IDs also reuse old entity unique IDs for current
  command lights, effect/audio/chip/mode controls, effect-type diagnostics, and
  SP601/SP60x scene recall entities, including old `master` and `channel_n`
  identity segments. RG4/Zengge mesh entries also reuse old node light and
  panel-status entity unique IDs with decimal `node_<id>` identity segments;
  new mesh effect controls keep UniLED Next IDs because old UniLED did not
  create equivalent entities.
- Bluetooth manifest matchers for bounded catalog name patterns such as
  `SP1*`, `SP3*`, `SP5*`, `SP6*`, `SP7*`, `SP802E`, `LED Strip`,
  `Light Bar`, `Wall Light`, `DynamicBar`, `Car Lights`, `FT001`, `RG4`, and
  `360PhotoB`, plus BanlanX manufacturer-data wake-up matchers for manufacturer
  IDs `20563` (`0x5053`) and `5053`. Tests prove those local-name matchers cover
  all 151 user-facing BLE or BLE-mesh catalog names, including legacy-only
  `SP107E`/`SP110E`, that name-less BanlanX manufacturer-data advertisements can
  wake the Bluetooth flow, that a blanket `SP*` matcher is not present, and that
  every matcher remains `connectable: true`.
- Home Assistant BLE byte transport at `custom_components/uniled/bluetooth.py`
  using current HA Bluetooth lookup plus Bleak characteristic write/notify.
  Direct BLE write/notify targets are now resolved under the expected service
  UUID when Bleak exposes services, matching the APK bridge's required
  `serviceUuid` + `characteristicUuid` calls and avoiding ambiguous same-UUID
  characteristics on unrelated services. The transport also mirrors the APK
  bridge write-mode fallback from decompiled `C2248g.java` and `C2229c.java`:
  explicit response writes wait for `onCharacteristicWrite`, default writes use
  write-without-response when characteristic property `0x04`/Bleak
  `write-without-response` is present, and write-only characteristics fall
  back to response writes.
- Home Assistant Zengge BLE mesh transport class at
  `custom_components/uniled/bluetooth.py` with separate pair, status, and
  command characteristic methods for the Telink UUID set. Runtime setup can
  attach it for address-backed RG4/Zengge entries.
- Protocol registry that maps catalog models to command builders where parity
  behavior exists.
- Tests proving every user-facing model has a safe entity plan, filtered models
  have no entities, pixel limits become configuration numbers, network-info
  models get diagnostics, network-controller profiles get planned surfaces,
  optional-cloud models get cloud-profile diagnostics, scene families get scene
  plans, and legacy UniLED parity candidates are marked.
- Entity metadata tests proving command entity translation keys preserve output
  channel, scene slot, and paired mesh-node context, that implemented
  diagnostic sensors across every user-facing APK model have matching English
  names, and that Zengge panel-status diagnostics use a shared placeholder
  translation key.
- BLE profile tests proving ported families keep known command UUIDs while
  unported direct-BLE families expose only APK UUID/plugin evidence and remain
  command-profile-pending.
- Bluetooth transport tests proving direct BLE writes are service-scoped and
  use the APK's write-without-response versus response-write fallback.
- LAN profile tests proving SP547E/SP548E carry network-info code `37` and
  `maxDataLength=185`, SP541E carries the recovered SPNet UDP discovery
  request/response anchors plus guarded SPTECH TCP candidate facts, custom
  5xx profiles preserve old-UniLED SPTech model-code aliases and configuration
  hints as diagnostics only, SP802E carries network-info code `9`, SP801E
  remains a LAN profile without a network-info code, and BLE-only models do
  not claim LAN facts.
- Setup-data tests proving manual entries keep stable legacy diagnostic IDs,
  LAN entries use host/IP identity, LAN setup rejects BLE-only models, and
  invalid hosts fail before config-entry creation.
- Setup-data coverage tests now walk every user-facing APK model and prove each
  advertised local transport can create valid entry data: 124 BLE setup routes,
  27 BLE-mesh setup routes, and 41 LAN host setup routes. The same guard keeps
  the 39 optional-cloud flags separate from local setup transport creation.
- Runtime support-disposition tests proving representative old-UniLED parity,
  custom 5xx BLE-command-plus-LAN-pending, RG4 mesh-limited, scene UI, scene
  mesh, car-light, SP801E, SP802E, and FT001 models each report an explicit
  command-ready, mesh-limited, or diagnostic-only status with the pending
  evidence categories named.
  A catalog-wide runtime test now also proves all 57 recognized-only APK
  models build diagnostic runtimes, expose their family-specific APK profile
  diagnostics, report `apk_profile_ready`, and keep every command platform
  closed until command protocol evidence exists.
  A second recognized-BLE setup-path test proves all 30 recognized direct-BLE
  models can create BLE setup-entry data, report `configured_transport=ble`,
  and still attach no transport/session or command entities while UUID binding
  and command frames remain pending.
- Setup-data migration tests proving legacy UniLED `ble`, `net`, and `zng`
  entry data normalize into the new BLE, LAN, and BLE-mesh schema without Home
  Assistant imports, including old Zengge mesh IDs and rejecting unsafe
  missing/unsupported legacy shapes.
- Runtime setup tests proving missing models, unknown models, filtered models,
  invalid APK model IDs, and duplicate-name model-ID mismatches fail with
  precise `field`/`reason` metadata for Home Assistant repairs.
- Setup-data reconfigure tests proving local repair updates normalize BLE,
  LAN, legacy `net`, and RG4/Zengge entry data without Home Assistant imports,
  while preserving mesh credentials and rejecting unsafe mesh identity changes.
- Repair helper tests proving config-entry issue IDs, issue data, severity, and
  sanitized translation placeholders without requiring a Home Assistant install.
  They also prove `async_migrate_entry` applies normalized legacy data through
  Home Assistant's `async_update_entry` with version/minor-version updates,
  preserves existing old config-entry unique IDs, deletes stale migration
  issues after success, and creates sanitized non-fixable migration issues
  without updating entries when legacy data is unsafe. Direct setup-hook tests
  prove `async_setup_entry` creates the same sanitized non-fixable issue for
  invalid stored runtime data while skipping runtime storage and platform
  forwarding.
- Mesh profile tests proving RG4 preserves old UniLED Telink/Zengge UUIDs,
  manufacturer IDs, pairing/cloud-credential requirements, notification-based
  status behavior, ported command names, Zengge effect packet fields, and 20
  old UniLED effect names while BanlanX scene mesh remains
  core-protocol-pending.
- Zengge packet tests proving nonce/payload/checksum layout, pair packet,
  session-key derivation, CRC16, and validation behavior with a deterministic
  fake block encryptor so the tests do not require local AES installation.
- Zengge command tests proving old UniLED control payload layout and encrypted
  packet wrapping for power, brightness, RGB, CCT, warm white, effect, fallback
  state query, and status-notification kick behavior, including preserved
  delay/gradual transition bytes for control-payload-backed commands.
- Zengge parser tests proving old UniLED's `0xDC` notification block offsets,
  HSV scaling, CCT percentage conversion, panel/bridge handling, and full
  two-block decrypted message parsing.
- Zengge mesh-session tests proving pair request/reply handling, visible
  authentication/unpaired failures, encrypted command construction from the
  stored session key, and notification state storage with registered node
  context.
- Zengge mesh-connection tests proving the mesh transport boundary writes
  pair, status, and command bytes to distinct characteristic methods while
  preserving old-UniLED packet vectors.
- Bluetooth transport tests proving the Home Assistant Zengge mesh transport
  routes pair, status, and command writes to distinct UUIDs, forwards encrypted
  notifications, closes notifications cleanly, and fails visibly when required
  characteristic UUIDs are absent.
- Runtime tests proving RG4 can attach and pair a Zengge mesh connection, keeps
  normal number/select/switch feature gates closed, creates light features for
  paired known command-capable nodes, and fails mesh attachment without the BLE
  address needed for packet nonces.
- Runtime setup-helper tests proving normal BLE models still attach command
  sessions, while RG4 setup attaches only the mesh transport holder and leaves
  command features hidden until pairing succeeds.
- Runtime credential tests proving custom Zengge mesh name/password values are
  used for pairing, default to old UniLED values when absent, and remain
  redacted in diagnostics.
- Runtime refresh tests proving RG4 diagnostic refresh pairs, sends the status
  kick, records success diagnostics, and records rejected-credential failures
  without raising; known node light features appear only when pairing and node
  eligibility are both true.
- Runtime Zengge command tests proving paired known-node power, brightness, RGB,
  Kelvin CCT, warm-white, and effect commands preserve old UniLED packet
  vectors, update only the targeted mesh node state, and reject unpaired,
  unknown, panel, and bridge targets before command writes.
- Runtime Zengge panel tests proving known RGB/CCT panel nodes create
  diagnostic status sensors, consume old-UniLED notification status blocks as
  `Online`/`Offline`, and remain excluded from command-capable light features.
- Zengge cloud metadata tests proving old UniLED MagicHue country servers,
  endpoint paths, mesh credential fields, place metadata, and device-list node
  fields are parsed into normalized mesh/node metadata. The same tests prove
  the live client helper builds the old login payload, including MD5 password
  hash and AES checkcode input, and performs the login, mesh-list, bridge, and
  device-list request sequence.
- Setup-data tests proving exact-name, safe-suffixed, and BanlanX
  manufacturer-data Bluetooth discovery create direct BLE entries with stored
  provenance, while generic Telink mesh advertisements and parsed MagicHue
  cloud metadata create RG4 BLE-mesh entries using the old UniLED
  `zng_mesh_<uuid>` unique ID shape. Manufacturer-data tests cover the SP542E
  `5d 10 ...` issue evidence, the SP613E `09 10` payload variant, prove
  duplicate SP548E variant `0x94` wins over the ambiguous local name, preserve
  issue-reported SP538E/SP548E `f0` manufacturer payloads, and reject LAN-only
  catalog model IDs. They also prove all 51 old-UniLED BLE names
  resolve from exact-name and safe-suffixed Home
  Assistant-shaped discovery objects as `protocol_proven`, including the 49
  BanlanX APK overlap models and the legacy-only `SP107E`/`SP110E` rows, and
  that each one reports the raw-address old-UniLED config-entry IDs that must
  block duplicate setup. The legacy audit and direct tests also prove all 51
  explicit and inferred old direct-BLE config-entry shapes migrate to
  normalized UniLED Next BLE entries for the same model, model ID, and address.
  Old Zengge mesh migration preserves `zng_mesh_<uuid>` identity from either
  explicit old mesh IDs or mesh UUIDs while dropping old stored cloud
  credentials.
  The production quality gate now also checks every user-facing catalog
  BLE/BLE-mesh model name and those 51 old-UniLED BLE names against the Home
  Assistant Bluetooth manifest matchers, so matcher edits cannot silently break
  catalog or legacy discovery wake-up coverage.
  RG4/Zengge mesh exact-name or manufacturer-data discoveries also autodiscover
  as `protocol_proven`, while BanlanX scene-mesh catalog-only discovery remains
  `discovered_only`. Config-flow discovery now auto-creates only
  protocol-proven Bluetooth entries; discovered-only catalog matches show a
  confirmation form before creating diagnostic-only entries. Non-connectable
  discovery and LAN-only exact-name discovery are rejected before entry
  creation, and addressless BLE or BLE-mesh discoveries do not create unusable
  entries.
- Setup-data and LAN-discovery tests proving SPNet LAN discovery can create a
  verified SP541E LAN entry only from the recovered response prefix, model byte
  `0x5c` at payload offset `3`, and a source host. Live HA-host evidence shows
  the same response carries a network MAC at payload offsets `5..10` and an
  `SP541E` response name; setup uses that MAC as the legacy-compatible bare
  config-entry unique ID when present. The scanner sends limited broadcast plus
  locally derived `/24` directed broadcasts. Unrelated packets, duplicate/noise
  datagrams, missing hosts, unknown model bytes, and LAN-capable models without
  the SP541E/SPTech command path fail visibly before entry creation. The
  quality gate requires translated abort messages for those LAN-discovery
  rejection reasons so failed discovery remains user-readable in Home
  Assistant.
- Setup-data tests proving manual RG4 BLE-mesh setup accepts address plus
  decimal/hex mesh/node fields, preserves the old UniLED mesh unique ID shape,
  allows cloud-only node import, and rejects invalid or non-mesh input before
  entry creation. Separate setup and migration tests prove BanlanX scene-mesh
  models such as `SP310E` keep local `ble_mesh:<address>` identity instead of
  inheriting old Zengge `zng_mesh_<uuid>` identity.
- Protocol tests proving command bytes match old UniLED behavior or the
  APK-matched SP6xx-style custom 5xx behavior for state query, power,
  brightness, RGB color, effect speed/length, direction/loop, audio input, and
  sensitivity where those commands are available.
- Parser tests proving known status byte offsets for the same legacy parity
  families, including old UniLED BanlanX v2 fixture comments and synthetic
  SP6xx/custom 5xx frame validation.
- Notification framing tests proving segmented BLE packets assemble before
  status parsing, including an old SP601E two-packet example from UniLED.
- Runtime tests proving model resolution, parser readiness, implemented
  diagnostic sensor selection, and diagnostics redaction without needing a local
  Home Assistant test install.
- Runtime tests proving command-light eligibility requires an attached session
  and successful light commands update normalized channel state.
- Runtime tests proving number/switch command eligibility requires an attached
  session and successful command controls update normalized channel state.
- Runtime tests proving select command eligibility requires an attached session
  and successful select commands use the old UniLED option maps, including
  legacy chip-order permutations and command dispatch.
- Runtime tests proving SP601/SP60x, BanlanX2, BanlanX3, and fixed-subtype
  SP6xx effect selects use the old UniLED effect names and wire values.
- Runtime and session tests proving SP6xx advanced controls use the old UniLED
  status offsets and command frames for on/off animation, power restore,
  play/pause, and coexistence.
- Runtime and session tests proving SP6xx light-type and chip-order controls
  preserve old UniLED command framing, dynamic option lists, and safe
  mode/effect fallback when a new wiring type cannot use the current mode.
- Protocol, parser, runtime, and session tests proving SP6xx RGBW/RGBWW/CCT
  state and command behavior follow old UniLED offsets and frame choices.
- Runtime tests proving the structured old-UniLED parity profile exposes the
  source old-UniLED BanlanX module, ported command-builder count, parser-hint
  count, and intentional old stub gaps such as SP601/SP60x `scene_save`.
- Runtime tests proving state refresh sends a state query, adopts parsed state,
  preserves runtime diagnostics, and marks no-response devices unavailable.
- BLE profile tests proving the old UniLED UUID profile assignments for
  `ffe0`/`ffe1`, the issue #111 SP107E `ffb0`/`ffb1` fallback, the issue #122
  SP60x `ffb0`/`ffb1` fallback, the issue #105 BanlanX v2 `e0ff` service
  fallback with existing `ffe1` characteristic binding, and the SP6xx/custom
  5xx `e0ff`/`ffe0` service fallback.
  The same tests and APK evidence audit keep the normalized BLE UUID inventory
  tied to exact raw APK anchors while leaving `ff12`/`ff14`/`ff15` unbound for
  scene/car/fish/SP802E families. Runtime BLE diagnostics now also expose
  per-model old-UniLED issue advertisement fixtures, with exact payload/service
  anchors for issue #45 SP63AE, #57 SP617E, #60 SP621E, #78 SP642E, #105
  SP611E, #111 SP107E, #69 SP110E, #120 SP538E/SP548E `ffe1` adverts,
  #122 SP608E, and #132 SP542E.
- Session tests proving command dispatch to a byte transport, response-aware
  state queries, unsupported-command failures before writes, runtime transport
  attachment, direct-response refresh parsing, notification-wait refresh, and
  segmented notification parsing through session state.

Verified catalog facts:

- Catalog records: 191.
- Unique names: 153.
- User-facing catalog records: 190.
- Canonical user-facing names: 152.
- Canonical support-matrix rows: 152.
- User-facing record families differ from canonical family rows where duplicate
  names collapse behind one setup/runtime model. For example,
  `banlanx_scene_ui` has 25 user-facing APK records but 24 canonical rows,
  `banlanx_6xx` has 56 records but 38 canonical rows, `banlanx_custom_5xx`
  has 46 records but 38 canonical rows, and `banlanx_v2` has 19 records but
  8 canonical rows.
- User-facing duplicate-name groups: 24 names with 38 additional APK variant
  records. Runtime diagnostics preserve the full variant list behind each
  resolved name, including `model_id`, `parent_id`, `connectCaps`,
  decoded connect-capability labels, `specFunctions`, decoded spec-function
  bit labels, `colorCap`, decoded color-capability labels, transports,
  feature keys, features, support level, and the default canonical and
  selected-entry markers.
- Limited user-facing names: 95.
- Recognized user-facing names still waiting on protocol work: 57.
- Filtered placeholders: `TEST`.
- Old UniLED parity/evidence candidates tracked: 52 names. This includes
  49 exact BanlanX BLE parity entries, RG4's old-UniLED-backed Zengge mesh
  protocol evidence, and the two legacy-only BLE rows `SP107E` and `SP110E`.
- Legacy-only old UniLED `LED Chord`/`LED Hue` models are cataloged outside
  the APK source as `SP107E` and `SP110E`. They autodiscover as BLE
  `protocol_proven` devices with the old `ffe0`/`ffe1` UUID binding; SP107E
  also accepts the issue #111 `ffb0`/`ffb1` transport fallback. They now have
  limited command/status support. Hidden configuration/edit surfaces such as
  chip type, segment/pixel layout, and the second RGB bank remain explicit
  parity gaps until packet behavior is proven.
- Legacy old-UniLED `lib/net` has no reusable BanlanX LAN model evidence:
  `UNILED_NET_MODELS` is empty, so APK LAN families remain blocked on BanlanX
  packet or native call-flow evidence rather than legacy network parity.
  `scripts/audit_legacy_uniled.py --legacy-root ..\uniled` now checks these
  boundaries directly against the local old-UniLED source tree.

## Support Disposition

Every user-facing catalog name resolves to either `limited` or
`recognized`. `Limited` is currently assigned only to families with command
builders, status parsers, BLE or BLE-mesh profile facts, runtime/entity wiring,
and direct tests. For `zengge_mesh`, this means guarded paired-node light
commands after pairing; non-light mesh entities and broader multi-node controls
remain pending. `Recognized` means the device is cataloged and routable but
still waits for family-specific protocol support.

Some APK records share a user-facing model name. The catalog keeps all records
and sorts them behind one canonical runtime name, so duplicate records such as
`SP665E` (`model_id` 126 and 260) and `SP548E` (`model_id` 99, 105, 147, and
148) remain visible in diagnostics for protocol research and future
model-ID-aware setup. New setup-entry data stores `model_id`; runtime setup
uses that value when present so a duplicate display name can resolve to the
exact APK row. Name-only entries still fall back to the deterministic canonical
record for compatibility. Manual setup exposes an optional APK model ID field
so a user can create non-default duplicate variants such as `SP665E`
`model_id=260`. Runtime setup errors now carry setup-data-style `field` and
`reason` metadata, so stale duplicate IDs create model-ID-specific repair
signals such as `model_id`/`unknown_model_id` or `model_id`/`invalid_model_id`.

Support levels are:

- `recognized`: known catalog model, safe to diagnose and route, not yet
  guaranteed controllable.
- `limited`: tested local controls implemented for a known protocol surface;
  unproven transports or advanced capabilities remain hidden.
- `full`: discovery, setup, state, commands, entities, diagnostics, unload,
  reload, and tests implemented.
- `filtered`: known non-user-facing placeholder.

## Family Map

| Family | Representative names | Transport map |
| --- | --- | --- |
| `banlanx_601` | `SP601E` | BLE |
| `banlanx_60x` | `SP602E`, `SP608E` | BLE |
| `banlanx_v2` | `SP611E`, `SP616E`, `SP617E`, `SP620E`, `SP621E` | BLE |
| `banlanx_v3` | `SP603E`, `SP613E`, `SP614E`, `SP623E`, `SP624E` | BLE |
| `banlanx_6xx` | `SP630E`, `SP648E`, `SP65CE`, `360PhotoB` | BLE |
| `banlanx_custom_5xx` | `SP521E`, `SP530E`, `SP548E`, `SP54CE` | BLE, LAN, optional cloud |
| `banlanx_scene_ui` | `SP551E`, `SP660E`, `SP679E`, `DynamicBar` | BLE |
| `banlanx_scene_mesh` | `SP310E`, `SP320E`, `SP32CE` | BLE mesh |
| `banlanx_car_lights` | `SP701E`, `SP702E`, `SP-MIC`, `Car Lights` | BLE |
| `banlanx_network` | `SP801E`, `SP802E` | LAN, plus BLE for `SP802E` |
| `fish_tank` | `FT001` | BLE, LAN, optional cloud |
| `zengge_mesh` | `RG4` | BLE mesh |

## Current Evidence From Inner Workings

- `connectCaps=1` maps to direct BLE control for the known BLE families.
- `connectCaps=7` maps to BLE plus LAN with optional cloud fallback for custom
  network-capable families.
- `connectCaps=8` maps to BLE mesh or grouped BLE control.
- `SP802E` has `connectCaps=3`, so the catalog treats it as LAN-capable with a
  BLE path as well.
- Old UniLED has a separate Hao Deng/Zengge BLE mesh stack built on Telink
  service `00010203-0405-0607-0809-0a0b0c0d1910`, status characteristic
  `...1911`, command characteristic `...1912`, OTA characteristic `...1913`,
  and pair characteristic `...1914`. It derives mesh IDs from Telink
  manufacturer data and performs a pairing/session-key step before encrypted
  command packets are usable.
- Old UniLED parses Telink manufacturer data with mesh UUID in bytes `0..1`,
  node type in byte `7`, and node ID in byte `9`. The new setup-data helper
  uses those offsets to identify generic Telink advertisements as RG4/Zengge
  mesh entries.
- Old UniLED Zengge status does not use a normal query/response path. The
  manager writes `0x01` to the status characteristic, then waits for encrypted
  notifications and parses two five-byte node status blocks from command
  `0xDC`.
- Each five-byte Zengge node block is `node_id`, connected/status byte,
  brightness percentage, a packed mode/value byte, and value byte. Old UniLED
  reads mode from the high two bits, a secondary value from the low six bits,
  decodes RGB as HSV using `hue/255` and `saturation/63`, and converts CCT
  percentage into the 2800K-6500K range.
- Old UniLED Zengge packets use reversed-key AES-ECB from `pycryptodome`, a
  nonce built from reversed MAC address bytes plus a three-byte sequence, a
  two-byte checksum prefix, and a 15-byte encrypted payload. The new core now
  preserves that packet shape and declares `pycryptodome>=3.17` in the
  integration manifest, matching the old integration requirement.
- Old UniLED Zengge command payloads use a nine-byte control structure:
  device type, opcode, three value bytes, two-byte delay in tenths of a second,
  and two-byte gradual transition in tenths of a second. The new command
  helpers preserve this layout and map Home Assistant light transition seconds
  to the gradual field only for Zengge control-payload-backed commands.
- Old UniLED Zengge effect names are now retained as profile facts: 20 dynamic
  effects from `Seven Color Cross Fade` through `Seven Color Jumping Change`.
  They are not Home Assistant command entities yet because node entity planning
  and availability handling still need to sit above the runtime mesh helpers.
- The APK registers `network_info_plus` and asks Android for `wifiBroadcast`,
  `wifiGatewayAddress`, `wifiState`, `wifiIPAddress`, `wifiIPv6Address`,
  `wifiName`, `wifiBSSID`, and `wifiSubmask`.
- The APK registers a `com.spled.plugins/multicast_lock` channel with
  `acquire_multicast_lock`, `release_multicast_lock`, and
  `held_multicast_lock`; this is discovery plumbing, not a device command
  protocol by itself.
- The APK contains Bonsoir/Android NSD broadcast/discovery method names:
  `broadcast.initialize`, `broadcast.start`, `broadcast.stop`,
  `discovery.initialize`, `discovery.start`, and `discovery.stop`. The
  decompiled plugin arguments include `service.name`, `service.type`,
  `service.port`, `service.host`, and `service.attributes`. Decompiled Java
  also pins the Android `NsdManager` calls and shows the service type is
  supplied by Dart rather than hard-coded in the Java plugin layer.
- Decompiled Bonsoir event marshalling also confirms the discovery event names,
  top-level event `id`, nested `service.*` payload fields, trailing-dot service
  type trimming, host-address string emission, UTF-8 TXT byte decoding, empty
  string normalization for null TXT values, and serialized Android
  `resolveService` calls.
- The APK's mDNS helper sends TXT queries to multicast group `224.0.0.251` on
  port `5353` with TTL `255`, a 2000 ms query timeout, DNS TXT record type
  `16`, query class `32769`, and a 1024-byte TXT receive buffer. Decompiled
  Java shows the query name is `service.name`, `service.type`, and `local`;
  after an ephemeral-port timeout it retries bound to local port `5353`.
  Its generic UDP data source uses an 8000 ms socket timeout and a 2000-byte
  receive buffer.
- LAN profiles also preserve eight raw socket anchors
  (`RawDatagramSocket:onDone`, `RawDatagramSocket:onError ->`,
  `Socket_AvailableDatagram`, `_makeDatagram@16069316`, address-family,
  closed-socket, and bind-error strings) plus three discovery-status anchors:
  `delay stop discovery>>>>>>>`, `reported data:`, and
  `unresolved discovery response from`.
- Custom 5xx LAN profiles now preserve the SPNet discovery contract recovered
  from the BanlanX 3.3.1 arm64 Flutter AOT output and live SP541E app behavior:
  UDP port `6454`, request `53704e65740000200000000002e0`, response prefix
  `53704e6574000021000000000001`, model byte `0x5c` for SP541E at payload
  offset `3`, network MAC at payload offsets `5..10`, and response name
  `SP541E`. The live phone confirmed the official app opens UDP/6454 on the
  SP541E list and that the selected SP541E reports Wi-Fi (Infra) connected with
  cloud available. A live HA-host UDP probe on 2026-07-05, followed by the
  deployed `async_discover_spnet_devices` helper, received matching SPNet
  responses from all three local SP541E strips, including the expected MAC
  prefixes.
  The same profile now marks SP541E TCP/8587 and `SPTECH\0` as command-proven:
  direct probes succeeded when HA was stopped, and the Home Assistant runtime
  can hold a command session, refresh state, and send power/brightness commands.
  Setup-data helpers can turn the proven SPNet response plus source host into
  a verified SP541E LAN config-entry shape with `discovery_source=lan`,
  `discovery_match=spnet_model_id`, and `discovery_confidence=verified`;
  old-UniLED SPTech model-code matches create confirmation-required
  diagnostic-only LAN entries with `discovery_match=spnet_legacy_model_code`
  and `discovery_confidence=discovered_only`. Non-SPNet packets, missing hosts,
  unknown model bytes, and unsupported LAN families are still rejected before
  entry creation.
  Issue #115 SP525E evidence now adds a third, still diagnostic-only SPNet
  discovery tier: custom 5xx packets whose model byte maps to an APK LAN row
  and whose optional packet name agrees with that row create
  `discovery_match=spnet_catalog_model_id` entries with
  `discovery_confidence=discovered_only`; LAN commands remain guarded behind
  the SP541E-only verified command path. That same guard now accepts structured
  SPNet summary dictionaries when raw UDP bytes are unavailable, covering
  old-UniLED issue #91/#123 `SP548E` model-code `148` logs as
  confirmation-required catalog-model diagnostics.
  Other custom 5xx LAN profiles keep `command_protocol_known=False` until their
  frame/session behavior is proven.
- Old UniLED `origin/dev_v3` and tag `3.0.10-beta.11` preserve SPTech LAN
  recognition aliases in
  `custom_components/uniled/lib/net/sp53x_54xe.py`: model codes `0x4e`
  -> `SP530E`, `0x56` -> `SP538E`, `0x57` -> `SP539E`, `0x63`/`0x69`
  -> `SP548E`, and `0x64` -> `SP549E`, plus 16 configuration-code hints
  covering the SP530E PWM/SPI variants and SP538E/SP548E/SP539E/SP549E SPI
  variants. That dev branch also gives the SPTech NET RGB/RGBW profiles a
  richer custom-effect surface: custom-solid effect `0x13` is `Firework`, and
  SP530E uses that richer surface only on its `0x86`/`0x88` SPI variants,
  while the fixed SP538E/SP548E `0x06` plus SP539E/SP549E `0x08` profiles use
  the gradient-capable SP5XXE mode table. The same old `sptech_model.py` source
  preserves 20 SPTech command IDs (`0x02`, `0x08`, `0x0a`, `0x0b`,
  `0x50`-`0x5a`, `0x5d`, `0x60`, `0x61`, `0x6a`, `0x6b`) and eight response
  chunk decoders for settings, status, extended status, timer, music layout,
  network info, fun switch, and an unknown firmware/status block. UniLED Next
  exposes these as structured LAN diagnostics, count sensors, and model-scoped
  custom 5xx status/select options. If such a SPNet response is seen, config
  flow asks for confirmation before creating a diagnostic-only LAN entry; the
  aliases and command/chunk inventory do not enable LAN writes outside the
  verified SP541E path.
  A separate issue-backed catalog-model diagnostic path covers SP525E
  model-code `113` from old-UniLED issue #115 and structured SP548E
  model-code `148` summaries from old-UniLED issues #91/#123 without treating
  the LAN command protocol as proven.
- `SPTechLANProtocol` now parses old-UniLED status chunk `6` as live network
  info when present. The live SP541E capture includes `Infra` and
  `192.168.0.82`, which now surfaces as the implemented `network_info`
  diagnostic while preserving the raw chunk tail; malformed chunk `6` data
  records a parse-error diagnostic without losing the rest of the state.
- `SPTechLANProtocol` also records old-UniLED status chunk `7` as the raw
  `power_fun_switch` diagnostic byte when present. Empty chunk `7` data records
  a parse-error diagnostic and does not enable a user-facing switch or LAN
  write path.
- SPTech repeated chunk types are now preserved instead of collapsed, matching
  old UniLED's sequential decoder model. Chunk `4` timer records surface as
  parsed read-only diagnostics, and chunk `5` music/effect layout data surfaces
  effect layout, matrix dimensions/layout, strip segment metadata, and raw
  matrix-mode records without enabling layout writes.
- SPTech mode/status parsing now preserves the old-UniLED chip-order byte, and
  the SPTech protocol has old-UniLED frame builders for `0x08`, `0x0a`,
  `0x0b`, `0x52`, `0x57`, `0x60`, `0x61`, `0x6a`, and `0x6b`: on/off
  animation, coexistence, on-power, static/dynamic RGB, static/dynamic CCT,
  light-type reconfiguration, and chip-order. This is protocol evidence for
  future custom 5xx LAN work; non-SP541E LAN writes remain disabled.
- SPTech status-tail parsing now preserves old-UniLED DIY solid slot metadata
  from chunk `2` and DIY solid plus gradient slot metadata from extended chunk
  `3`. The live SP541E capture carries 14 solid slots, four gradient slots, and
  an unknown gradient tail, all retained as diagnostics only; DIY write frames
  are still unproven.
- SPTech unhandled status chunks are now preserved as bounded diagnostics with
  type, index, size, sampled hex, and printable ASCII runs. The live chunk `10`
  sample exposes a `V3.0.11` ASCII run, but remains an unknown firmware/status
  block rather than a modeled entity or command path.
- LAN-capable models now expose `lan_host_setup_mode`, currently
  `discovery_ready` for the verified SP541E/SPNet path and `manual_host` for
  other LAN-capable models, as an implemented diagnostic sensor. This makes the
  discovery gap visible in Home Assistant without implying a mapped LAN command
  protocol.
- The decompiled Java layer contains generic Flutter plugins for Bonsoir/mDNS,
  multicast locking, network-info lookup, and a generic datagram data source,
  but no SP801E/SP802E-specific command encoder. SP80x-specific clues remain in
  Flutter AOT strings and assets.
- Old UniLED does not contain an SP801E/SP802E command implementation, so the
  new integration treats both as APK-profiled, protocol-pending devices for
  now.
- SP801E's APK surface is `packages/module_sp801e` with `/sp801e` as the native
  route string. Assets expose Art-Net settings (`ic_artnet`,
  `img_artnet_config`, `img_artnet_mode`), port configuration, LED layout,
  wiring setup, scene/playlist editing, color correction, graffiti tools, DXF
  import, and create modes for regular effects, image, GIF, graffiti, music,
  text, and video. Native strings expose app-level `getNetworkInfo`,
  `getArtNetConfig`, `setArtNetConfig`, `getPlaylistList`, `addPlaylist`,
  `updatePlaylist`, and `removePlaylist` method names plus
  `ArtNetConfig` fields such as `portActions`, `portUniverseCounts`,
  `protocolVersion`, and `startUniverse`. Visible import text says DXF files
  are limited to no more than 4 ports and 1024 LEDs per port, and the layout
  strings say LED screen pixels cannot exceed 1024.
- SP801E diagnostics also preserve raw storage/query labels from `libapp.so`:
  `channel`, `sp_channel_group`, `channel_index`,
  `device_id = ? AND channel_index = ?`,
  `peripheral_group_id = ? AND channel_id = ?`, `portDriverType`, `portId`,
  `portNo`, `port_id`, `music/playlist`, `scene_playlist_action_bar`, and
  `scene_playlist_action_bar_empty`. These are database/UI anchors, not an
  Art-Net payload map.
  Planned disabled selectors now expose the exact APK field/action anchors:
  `network_artnet_field` (`portActions`, `portUniverseCounts`,
  `protocolVersion`, `startUniverse`), `network_port_field`
  (`channel_index`, `sp_channel_group`, `portDriverType`, `portId`, `portNo`,
  `port_id`), and `network_playlist_action` (`getPlaylistList`, `addPlaylist`,
  `updatePlaylist`, `removePlaylist`).
- SP802E's APK surface is `packages/sp802e` with `/sp802e`,
  `/sp802e/settings`, and `/sp802e/edit_led_layout` route strings. Assets
  expose LFX, material/favorite, regular, animation, GIF, graffiti, image,
  text, rhythm, LED panel layout, DIY gradient, and color-editing surfaces. The
  asset manifest contains 20 regular LFX effect icons (`ic_lfx_black_hole`
  through `ic_lfx_waverly`) and 30 `packages/sp802e/assets/gifs/*.gif`
  previews. These now surface as `network_lfx_effect_count=20` and
  `network_lfx_gif_count=30` diagnostic sensors; SP801E reports zero for those
  LFX-only counts while still exposing its Art-Net/content surface counts.
  Native strings expose LFX and matrix method names such as `setLfxMode`,
  `setLfxSpeed`, `setLfxPixelCount`, `setLfxLoopMode`, `setLfxColor`,
  `setLfxGradient`, `setLedPanelLayout`, and `setMatrixMusicMode`. ELF
  `.dynsym` inspection of `libwled_lfx.so` found 186 named dynamic symbols and
  35 audited matrix/effect/LFX/generator-related exports, including
  `setup_matrix_layout`, `switch_lfx_mode`, `initRegularLfxGenerator`,
  `set_effect_params`, `recover_effect_param`, `render_frame`,
  `get_frame_data`, `setPixelColorXY`, `getPixelColorXY`, `setLineColorXY`,
  `addPixelColorXY`, `fadePixelColorXY`, `sysMatrixW`, `sysMatrixH`,
  `create_horiz_fade_effect_generator`, `create_circle_fade_effect_generator`,
  `create_diamond_fade_effect_generator`, and
  `create_plasma_fade_effect_generator`; `RGBCW` is preserved as a native
  string anchor rather than a `.dynsym` export. A detailed dynsym pass places
  `set_effect_params` at `0x0000a4dd` with a 26-byte exported function body;
  this is a useful disassembly anchor, not a packet payload. SP802E diagnostics
  now preserve six exact native export detail anchors and separate LFX
  parameter/mode-switch anchors (`switch_lfx_mode`,
  `set_effect_params`, `recover_effect_param`, `effect_prj`,
  `Create_effectsTables`, `EFFECT_GENERATOR_CONSTRUCTORS`, `Dyneffect_num`,
  `Rhyeffect_num`), eleven regular-effect generator functions, matrix/mode
  anchors (`setup_matrix_layout`, `mode_2Dmatrix`, `mode_2Dmusicsoap`,
  `mode_2Dmusicsquaredswirl`, `sysMatrixW`, `sysMatrixH`, `staRGBIC`,
  `RGBCW`), and pixel/frame helpers (`render_frame`, `get_frame_data`,
  `setPixelColorXY`, `getPixelColorXY`, `setLineColorXY`, `addPixelColorXY`,
  `fadePixelColorXY`, `fillGradientRGB`, `wled_DrawCircle`).
  These are diagnostics-only disassembly anchors. SP802E diagnostics
  also preserve raw labels such as
  `lfxDurationInLoop`, `lfxLoopMode`, `lfxMode-`, `lfxParams`,
  `lfx_color_sets`, `lfx_colors`, `lfx_gradients`, `lfx_mode_id`,
  `lfx_mode_type`, `gif_lfx_frames`, `led_matrix_info`, `matrixType`,
  `wifiState`, `wifiStrength2`, and `supportGetNetInfo`; the Blutter enum also
  anchors SP802E's planned network-info method as `getNetworkInfo=0x92`. These
  exports confirm matrix/LFX and network-info app anchors, not packet framing.
  The LAN discovery primitives above are generic plugin plumbing; no confirmed
  SP801E/SP802E
  service type, discovery response, local socket frame, Art-Net config payload,
  SP802E BLE/LAN LFX command, status parser, playlist packet, DXF import
  packet, or panel-layout packet has been mapped yet.
  Runtime support disposition now makes those blockers explicit:
  `network_discovery_pending`, `network_socket_frame_pending`, and
  `network_dns_sd_service_pending` are shared; `SP801E` adds
  `network_artnet_config_pending`, `network_playlist_packet_pending`,
  `network_dxf_import_pending`, and `network_panel_layout_pending`; `SP802E`
  adds `network_lfx_packet_pending`, `network_lfx_status_parser_pending`,
  `network_panel_layout_pending`, and `network_matrix_music_pending`.
  The matching `network_command_blocker_count=7` diagnostic is a readiness
  signal only.
  SP802E also exposes a planned disabled `network_matrix_music_control`
  selector with the exact APK setter anchors `setMatrixMusicMode`,
  `setMatrixMusicDotColor`, `setMatrixMusicColColor`,
  `setMatrixMusicColColorType`, and `setMatrixMusicColGradientColor`.
- The BanlanX 3.3.1 APK is a Flutter AOT app. Its Java/Kotlin BLE layer is
  Flutter plugin glue, not model-specific protocol logic.
- Old UniLED's `LED Chord`/`LED Hue` modules (`SP107E`, `SP110E`) are
  legacy-only relative to this BanlanX APK target. Targeted searches across the
  generated catalog, decompiled XAPK resources, extracted assets, and native
  string surfaces found no APK device records or protocol identifiers for those
  names. `ledhue` appears in BanlanX web/app-link branding, not as the old
  `LED Hue` BLE protocol. The new catalog therefore keeps them as separate
  `/legacy/uniled/...` rows with BLE autodiscovery, UUID diagnostics, limited
  LED Chord/LED Hue command builders, and status parsers ported from old
  UniLED. Hidden configuration/edit surfaces remain blocked until stronger
  packet evidence exists.
- The APK places 25 direct-BLE scene UI records (`connectCaps=1`) and 26
  scene-mesh records (`connectCaps=8`) on the shared `/device/scene_ui`
  surface. Scene profile diagnostics now preserve per-model `model_id`,
  `parent_id`, `connectCaps`, `specFunctions`, `colorCap`, transports,
  `maxPixelChannels`, and feature flags where present.
- Scene native strings expose recent-scene/favorite storage and DIY LFX method
  names: `addRecScene`, `getRecSceneList`, `removeRecScene`, `saveDiyLfx`,
  `saveFavoriteEffectList`, `updateFavoriteLfxList`, and `resetLfx`, plus
  `scene_ui:scene_light_info` and `scene_ui:effect_multi_colors`.
- Scene setup text says SP31XE and SP32XE series require firmware V1.1 or
  above for one-touch provisioning. No confirmed scene BLE opcode table,
  notification parser, saved-scene/timer/favorite packet layout, or
  SP31x/SP32x mesh-routing/provisioning frame map has been extracted yet.
- The APK BLE bridge exposes generic byte-oriented BLE plumbing: adapter open,
  close, and state calls; discovery start/stop/list calls with `services`,
  `interval`, `clearPreDiscoveredDevices`, and `aliveTime` arguments; device
  connection, RSSI, MTU, service, characteristic, notification, and write
  calls; scan result fields `id`, `name`, `rssi`, `serviceData`, and
  `manufacturerData`; service result fields `uuid` and `isPrimary`;
  characteristic capability fields `uuid`, `supportWrite`,
  `supportWriteNoResponse`, `supportRead`, `supportNotify`, and
  `supportIndicate`; RSSI result field `rssi`; and MTU result field `value`.
  Discovery defaults missing `interval` to `0`,
  `clearPreDiscoveredDevices` to false, and `aliveTime` to `10000`, turns
  supplied service UUIDs into Android `ScanFilter` entries, and only applies
  scan report delay when the interval is positive and offloaded batching is
  supported.
  This matches the new core split: protocol sessions build/parse bytes while
  transports only move bytes.
- APK BLE writes set the characteristic value, honor explicit
  `characteristicWriteType` and `forceWaitResponse` arguments, otherwise choose
  write-without-response when characteristic property `0x04` is present and
  response writes when only property `0x08` is present. Notification enablement
  writes the standard CCCD descriptor
  `00002902-0000-1000-8000-00805f9b34fb`.
- Old UniLED resolves the notify characteristic from explicit notify UUIDs when
  present, otherwise from the read characteristic, otherwise from the write
  characteristic. For current ported BanlanX families this means `ffe1` is both
  write and notify fallback.
- Old-UniLED issue #122 reports a newer SP608E/BanlanX60X advertisement using
  service UUID `ffb0`, write/notify characteristic `ffb1`, manufacturer ID
  `20563`, and manufacturer payload `05 01 ...`; the BLE profile now treats
  `ffb0`/`ffb1` as a BanlanX60X fallback while leaving unrelated families on
  their existing bindings.
- Old-UniLED issue #111 reports an SP107E/LED Chord advertisement using
  service UUID `ffb0`, manufacturer ID `21301`, and manufacturer payload
  `1a 05 98 9e`; the BLE profile now treats `ffb0`/`ffb1` as an SP107E-only
  fallback while keeping SP110E and unrelated legacy families on their
  existing bindings.
- Old-UniLED issue #105 reports an SP611E/BanlanX v2 advertisement using
  service UUID `e0ff`, manufacturer ID `20563`, and manufacturer payload
  `10 00 21 06 28 00 4e 44`; the BLE profile now treats `e0ff` as a BanlanX
  v2 service fallback while keeping the existing `ffe1` write/notify
  characteristic and command protocol.
- Exact old-UniLED issue advertisements are also preserved as BLE diagnostics:
  issue #45 `SP63AE` has `29 10 32 00 00 00 1a a6` with `e0ff`, issue #57
  `SP617E` has `17 11 41 00 00 00 26 19` with `e0ff`, issue #60 `SP621E`
  has `0d 00 ff 23 06 03 21 f3` with `e0ff`, issue #78 `SP642E` has
  `4a 10 35 00 00 00 15 f5` with `e0ff`, issue #69 `SP110E` has
  `10 00 0c 91` with `ffe0`, issue #120 `SP538E`/`SP548E`
  has model-ID-pinned `56 f0 ...`/`63 f0 ...` payloads with `ffe1`, and
  issue #132 `SP542E` has `5d 10 54 20 24 00 27 16` with `ffe0`.
- Old UniLED SP6xx accepts service UUIDs `e0ff` and `ffe0`, with write
  characteristic `ffe1`.
- The APK places SP52x/SP53x/SP54x custom records on the same `/sp630e` app
  surface as SP63x/SP64x/SP65x and exposes the same `ff14`/`ff15` plus
  `ffe0`/`ffe1` UUID strings in that module. The new core therefore treats
  `banlanx_custom_5xx` as an SP6xx-style command/status family for BLE control,
  while keeping a distinct family name because `connectCaps=7`,
  `maxPixelChannels=3600`, `maxDataLength=185`, LAN provisioning, and optional
  cloud behavior are different from the BLE-only SP6xx line.
- The APK exposes a dedicated `packages/car_lights` Flutter feature package
  with zone assets for car, chassis, console, door, footsocket, storage,
  welcome, and wheel lights. It also ships trigger animations for brake, brake
  blink, fade, flow, left/right turn-signal flow, and turn-signal blink.
  Diagnostics now split the 10 animation assets, four trigger image assets
  (`astern`, `brake`, `left_turn_signal`, `right_turn_signal`), and 13 zone or
  setup image assets from the full 58-asset package count.
- Native Flutter strings and route names identify car-light setup and settings
  surfaces: `/car_lights`, `/car_lights/new`, `/car_lights/setup`,
  `/car_lights/settings/chassic_lights_trigger`,
  `/car_lights/settings/color_correction`,
  `/car_lights/settings/subdevices_management`, and `/car_lights/settings2`.
  The spelling `chassic` is in the APK route string.
- Native Flutter strings preserve exact car-light setup/dependency rules:
  `The "Wireless MIC" can only be used as an accessory to the "Chassis Lamp
  Controller (SP702E)".`, `Please add a "Chassis Lamp Controller (SP702E)"
  first.`, and the interior/chassis ordering warning that says to remove the
  chassis light, add `SP701E`, then add `SP702E`. APK prompts also expose the
  microphone permission requirement, secondary-device power-loss chain reaction,
  retaining the current device as primary controller by selecting `Ignore`, and
  identifying the install area by observing the zone with a fast-flashing white
  light effect. Nearby raw setup keys include `isPrimary`, `subUni`,
  ` channel is `, and fragments for returning to discovery to connect the
  device installed in a selected car area. The integration preserves these as
  setup-key diagnostics only, and models expose structured setup roles:
  `SP701E` is setup order 1 (`interior_before_chassis`), `SP702E` is setup
  order 2 (`chassis_after_interior_when_both_present`), and `SP-MIC` is an
  accessory stage after `SP702E`. The profile now also carries a structured
  four-row setup dependency inventory: the `Car Lights` parent group,
  `SP701E` preceding `SP702E` when both are present, `SP702E` following
  `SP701E` in that paired setup, and the one hard app dependency,
  `SP-MIC` requiring `SP702E`. These rows stay diagnostic-only until Home
  Assistant setup orchestration and repair UX are implemented. No
  confirmed car-light BLE command packet shape, notification parser,
  subdevice-binding flow, password entry/change/reset flow, or `SP-MIC` event
  packet shape
  has been extracted yet. Runtime support disposition keeps those missing
  contracts explicit as `car_light_ble_opcode_pending`,
  `car_light_status_parser_pending`, `car_light_zone_command_pending`,
  `car_light_trigger_packet_pending`,
  `car_light_subdevice_binding_pending`, `car_light_password_flow_pending`,
  and, for `SP-MIC`, `car_light_sp_mic_event_pending`; the matching
  `car_light_command_blocker_count` diagnostic is a readiness signal only.
- Car-light diagnostics now preserve raw subdevice labels (`subdevice`,
  `subdeviceAddr = `, `include_added_subdevices`, `exclude_slave_devices`),
  the exact secondary-device power-loss warning,
  password setup/reset labels (`Device password`, `Set your password`,
  `Turn on password`, `Turn off password`, reset wait/timeout strings),
  password entry labels (`Enter your password`, `Enter new password`,
  `Repeat password`, `Show password`, `Forget password?`,
  `Forgot password?`), password change/policy labels (`Change password`,
  `Change password successfully2`, `Inconsistent new password input!`, and
  the APK password character-policy text), and
  trigger storage hints including the `sp_trigger` table, `trigger_id`,
  `trigger_index`, and `triggers`. These labels are evidence anchors only, not
  subdevice binding, password-flow, trigger, or microphone event command
  support.
  Password-reset procedure diagnostics also preserve the APK strings for the
  three-second button hold, five power-cycle reset behavior, remove/reset
  label, and successful reset label.
  Exact APK subdevice filters (`include_added_subdevices`,
  `exclude_slave_devices`), password flow states (`Set your password`,
  `Setup password successfully`, `Turn on password`, `Turn off password`,
  reset wait/timeout strings), and trigger actions (`Set the lighting effect
  when the corresponding trigger signal is received`, `Rename trigger`) now
  populate planned disabled selectors and count diagnostics. Password entry
  and policy labels populate diagnostic counts only.
- Car-light planned control surfaces are derived from APK routes, settings
  pages, zone assets, password labels, and subdevice manager assets:
  `Setup`, `Zone selection`, `Trigger settings`, `Color correction`,
  `Subdevices management`, `Device password`, `Password reset`, and
  `Settings`. `car_light_control_surface_count=8` and the disabled
  `car_light_control_surface` select document the vendor-app surface only; they
  do not prove packet writes.
- The APK exposes a dedicated `packages/fish_tank_lights` feature package for
  `FT001`, whose catalog `home_uri` is `/device/fish_tank_lights` and whose
  `connectCaps=7` map to BLE, LAN, and optional cloud routing in the new
  catalog. Its catalog flags are `model_id=150`, `specFunctions=145`, and
  `colorCap=1`.
- Fish-tank assets expose two light channels (`ic_light_first`,
  `ic_light_second`) and UI surfaces for color palette, color correction,
  brightness, speed, windmill, timers, favorites, settings, device rename, and
  network configuration. Native route strings include
  `/device/fish_tank_lights/settings`, `/settings/rename`,
  `/settings/timer_list2`, `/settings/timer_list/timer_config`, and
  `/favorite/favorite_edit`.
  The 30-asset package is split in diagnostics into 23 icons, seven images,
  two channel assets, four timer assets, two favorite assets, and two effect
  assets.
- Native strings and assets include FT001-oriented effect hints for `Windmill`
  and a native string-table `springwater` label. Additional raw effect string
  anchors preserve `waterdrop`, `Flowing Water`, `Spring Water2`, and
  `Stromend Water`, plus timer/favorite workflow assets for
  add/edit/delete/select/empty states. No confirmed FT001 BLE or LAN command
  packet shape has been extracted yet.
- Command-adjacent FT001/native hints now preserved in diagnostics include
  shared app setter names (`getNetworkInfo`, `setBrightness`, `setLfxColor`,
  `setLfxColorTemp`, `setLfxMode`, `setLfxLoopMode`, `setLfxSpeed`,
  `setSolidColor`, `setSolidColorTemp`) and favorite/update methods
  (`saveFavoriteEffectList`, `updateFavoriteLfxList`, `favoriteLfx`). Favorite
  storage/service strings include
  `FavoriteLightingEffectApiService`, `FavEffectNameEntity`,
  `FavoriteEffectName`, `FavoriteStore0-3`, `FavoriteRecall0-3`,
  `FavoriteClear0-3`, `favoriteLightingEffectIds`, and
  `favoriteLightingEffectLoopEnabled`. Favorite-loop and navigation strings
  also preserve `favoriteLfx`, `NextFavoriteChannel`,
  `Loop all favorite effects`, and `Stop looping the favorite effects`.
- FT001 favorite-slot and timer-limit diagnostics are derived only from native
  labels `FavoriteStore0-3`, `FavoriteRecall0-3`, and `FavoriteClear0-3`.
  `fish_tank_favorite_slot_count` now exposes the four app-visible favorite
  slots as a diagnostic sensor, while the disabled planned
  `fish_tank_favorite_action` select exposes Store/Recall/Clear action types.
  Separate diagnostics also preserve four Store, four Recall, four Clear,
  favorite-loop hint/action, and firmware-prompt labels. The disabled planned
  `fish_tank_favorite_loop_action` select exposes Loop/Stop action types.
  They are not command bytes. Timer diagnostics preserve native
  `idxTimerTaskCount`, `Flutter | D -> idxTimerTaskCount = `, `newTimerId`,
  `Timer interface not supported.`, `saveTimingTask`, `removeTimingTask`,
  `timing_task`, and `You can only add up to 5 timers!`; the disabled planned
  `fish_tank_timer_action` select exposes Save/Remove action types.
  `fish_tank_timer_limit` exposes that APK limit as a diagnostic sensor. Timer
  and favorite selectors remain planned and disabled until packet captures or
  a recovered frame map proves writes.
- FT001 also gets a planned disabled `fish_tank_effect` select populated from
  the APK-visible `Windmill` asset label and raw `springwater` string-table
  hint. These are UI/effect-surface names only, not confirmed effect command
  values.
- FT001 diagnostics now also preserve raw native string anchors
  `newTimerId: 2`, `timerConfig`, `raw-brightness-`, `, whiteBrightness: `,
  `whiteBrightness`, `white_brightness`, `white_brightness INTEGER`,
  `waterdrop`, `Flowing Water`, `Spring Water2`, `Stromend Water`,
  `favoriteLfx`, `NextFavoriteChannel`, `Loop all favorite effects`,
  `Stop looping the favorite effects`, and `FishTankLights:fw_prompted_`.
  These are split into timer-string and brightness-string diagnostics because
  they are shared app clues for timer and brightness state naming, not FT001
  command bytes or parser offsets. The local APK evidence audit verifies these
  anchors plus the FT001 route, app-method, favorite service/storage,
  favorite store/recall/clear, timer storage, favorite-loop, raw effect,
  firmware-prompt, and timer labels against `libapp.strings.txt`.
- The native UUID pool includes `ffe0`/`ffe1` and `ff12`/`ff14`/`ff15`, but no
  FT001-specific UUID binding, BLE opcode table, notification/status parser, or
  LAN endpoint/refresh packet was recovered from APK 3.3.1. FT001 also has no
  `supportGetNetInfo` catalog extra, unlike SP802E and some custom 5xx models.
  Runtime support disposition now makes the command blockers explicit:
  `fish_tank_ble_opcode_pending`, `fish_tank_status_parser_pending`,
  `fish_tank_lan_refresh_pending`, `fish_tank_timer_frame_pending`,
  `fish_tank_favorite_frame_pending`, `fish_tank_effect_packet_pending`, and
  `fish_tank_brightness_parser_pending`. The matching
  `fish_tank_command_blocker_count=7` diagnostic is a readiness signal only.
- The APK exposes a `packages/gundam_lights` feature package with 177 assets.
  `core/feature_packages.py` now tracks it as a first-class non-catalog
  feature-package profile instead of a loose audit-script exception. Exact APK
  anchors include `/device/gundam_lights`,
  `/device/gundam_lights/settings`,
  `/device/gundam_lights/settings/on_off_mode`,
  `/device/gundam_lights/settings/rename`,
  `/device/gundam_lights/settings_more`,
  `gundam_lights:effect_multi_colors`, and asset evidence for beam cannon,
  color correction, exclusive mode, firmware update, on/off mode, remote
  control, and timer icons. The generated raw and pretty model catalogs still
  contain no `gundam` model name or `/device/gundam_lights` catalog record.
  The command protocol is unknown, so the integration must keep this
  feature-package-present/catalog-device-absent and must not invent a Home
  Assistant family without a catalog device or packet evidence.
- The APK exposes a shared `packages/scene_ui` feature package for
  `banlanx_scene_ui` and `banlanx_scene_mesh` catalog families. Scene-family
  catalog records use `/device/scene_ui`; the APK native strings also expose
  `/device/scene_ui/settings`, `/settings/color`, `/settings/more`, and
  `/settings/rename`.
- Scene UI assets include preset scene folders for `christmas`, `dynamic_bar`,
  `eaves`, `esports_181`, and `living_room`, plus 80 `ic_mode_*` mode icons.
  The core preserves the corresponding 80 human-readable mode names as planned
  disabled options and exposes `scene_preset_count=5` and
  `scene_mode_effect_count=80` diagnostics. Visible surfaces include scene
  selection, favorites, timers, pixel count, color settings, white brightness,
  DIY gradient/solid editing, music input, inner/phone microphone modes, PC
  mode, speed, and sensitivity.
- Native strings expose shared LFX creation routes for scene editing:
  `/device/lfx/regular`, `/device/lfx/rhythm`, `/device/lfx/animation`,
  `/device/lfx/gif`, `/device/lfx/graffiti2`, `/device/lfx/image`,
  `/device/lfx/text`, and `/device/scene/image/get`; the route count is
  exposed as `scene_lfx_route_count=8`.
- Native strings expose scene/LFX method anchors including
  `getFrameInfoHandler`, `getFrameLenHandler`, `getPWMFrameInfoHandler`,
  `setLfxMode`, `setLfxSpeed`, `setLfxPixelCount`, `setLfxLoopMode`,
  `setLfxColor`, `setLfxColorTemp`, `setLfxGradient`, `setLfxDir`,
  `setOnOffLfx`, `setLedPanelLayout`, `setSoundSource`, and
  `setWhiteLightCoexistWithRGB`.
- Native strings also expose raw scene/timer/favorite state labels:
  `recScene`, `removeTimingTask`, `saveTimingTask`, `timing_task`,
  `favoriteLightingEffectIds`, `favoriteLightingEffectLoopEnabled`,
  `raw-brightness-`, `whiteBrightness`, and `white_brightness`. These are
  diagnostic anchors only; they do not prove packet bytes, parser offsets, or
  value ranges.
- Native strings also expose app-side LFX data-model and frame-field anchors:
  `Lfx(`, `LfxColorProps.`, `LfxColorSet{fx: `, `LfxDirection.`,
  `LfxExternParams(`, `LfxLoopMode.2`, `DiyLfx(modeId: `,
  `DiyGradientLfx(modeId: `, `DiyLfxSegment{pixelCount: `,
  `CreativeLfxModeType.2`, `TriggerLfxMode.`, `WLedLfx`, `wrappedLfx`,
  `opCode = `, `opCode: `, `checksum`, `lfxParams`, `lfxMode-`,
  `lfx_mode_id`, `lfx_mode_type`, `lfx_colors`, `lfx_color_sets`,
  `lfx_gradients`, `gif_lfx_frames`, `favLfxModeIds: [`,
  `diyGradientLfx: `, `lfxDurationInLoop: `, `lfxLoopMode: `, and
  `lfx: `. These are exposed as `scene_lfx_data_model_hint_count=13` and
  `scene_lfx_frame_field_hint_count=16` diagnostics to guide the command
  envelope research, not to unlock scene writes.
  The profile now splits exact APK anchors into planned disabled selectors for
  recent-scene actions (`addRecScene`, `getRecSceneList`, `removeRecScene`),
  favorite actions (`saveFavoriteEffectList`, `updateFavoriteLfxList`), timer
  actions (`saveTimingTask`, `removeTimingTask`), DIY LFX actions
  (`saveDiyLfx`, `resetLfx`), and white-brightness anchors
  (`raw-brightness-`, `whiteBrightness`, `white_brightness`,
  `setWhiteLightCoexistWithRGB`).
- Scene UI and scene mesh now expose explicit support-disposition blockers for
  the remaining command contracts: `scene_command_envelope_pending`,
  `scene_status_parser_pending`, `scene_lfx_frame_pending`,
  `scene_timer_frame_pending`, `scene_favorite_frame_pending`,
  `scene_diy_frame_pending`, and `scene_white_brightness_parser_pending`.
  The matching `scene_command_blocker_count=7` diagnostic is a readiness
  signal only, not scene command support.
- `libscene_lfx.so` exposes 38 IC/PWM native API handler symbols. In addition
  to `API_IC_Param_Get_Handler`, `API_IC_Scene_Set_Handler`,
  `API_PWM_Param_Get_Handler`, and `API_PWM_Scene_Set_Handler`, the exported
  symbols include on/off, interrupt, channel, loop, static-color, color,
  color-temperature, brightness, speed, pixel-length, direction, DIY color,
  on/off animation, WRGB coexistence, all-reset, pause, and palette handlers.
  The profile now groups the ELF exports into 16 paired IC/PWM API
  capabilities, four IC-only API capabilities, and two scene-loop handlers.
  Native library exports also expose favor/routine/system record and recover
  handlers plus LED-type/default parameter handlers. A local ELF `.dynsym`
  scan of `libscene_lfx.so` found 378 named dynamic symbols and 76
  handler/frame/opcode/LFX-related names. Seven frame helpers are tracked
  separately: `createFrameHandler`, `getFrameInfoHandler`,
  `getFrameLenHandler`, `getPWMFrameInfoHandler`, `getCurrFrameIntv`,
  `getCurrFrameIntvHandler`, and `getChanNumHandler`. Nine routing/opcode
  helpers are tracked separately: `hal_App_Opcode_Handler`,
  `hal_pwmCtrl_Handler_R1`, `hal_pwmCtrl_Handler_G1`,
  `hal_pwmCtrl_Handler_B1`, `hal_pwmCtrl_Handler_CW1`,
  `hal_pwmCtrl_Handler_WW1`, `hal_WpwmCtrl_Handler_CW1`,
  `hal_WpwmCtrl_Handler_WW1`, and `hal_rgbToBus_Handler_01`. Five state
  helpers are tracked separately: `getStaDat`, `syncBriChangeHandler`,
  `getBitState`, `setBitlOn`, and `setBitlOff`, with diagnostic export
  anchors preserving offsets/sizes such as `getStaDat@0x0001119d/256`.
  Color-order and LED-type
  anchors such as `ONLY_RGB`, `ONLY_PWM`, `RGBCW`,
  `RGBWC`, `CRGBW`, and `CWRGB` into a separate diagnostic bucket. PWM table
  anchors such as `PWM_STA_TAB`, `PWM_DYN_TAB`, `PWM_RHY_TAB`, `PWM_DIY_TAB`,
  and the white-PWM table variants are tracked separately from music/effect
  routines such as `Music_VuMeter`, `Music_Spectrum`, `pwmDiyGradient`,
  `pwmDynGradient`, `pwmRhyBeat`, and `pwmOnOffAnimation`. PWM driver and
  write helpers such as `WsetPWM`, `WsetPwmBuf`, `setPWM`, `setPwmBuf`,
  `setCCTBri`, `PWM_DriveRGB`, and `PWM_DriveW` are now separate research
  anchors for disassembly. Scene profile diagnostics now separately expose
  10 audited animation/self-test exports, including IC/PWM calibrate, echo,
  factory-test, and on/off animation handlers, plus 5 drive-type exports:
  `IC_DriveRGB`, `IC_DriveW`, `LED_DRIVE_TYPE`, `PWM_DriveRGB`, and
  `PWM_DriveW`. A detailed dynsym pass places
  `hal_App_Opcode_Handler` at `0x000130a9` with a 128-byte exported function
  body. The largest exported scene handlers include
  `API_IC_All_Reset_Handler` at `0x00014ec9` (864 bytes),
  `API_PWM_All_Reset_Handler` at `0x00015e05` (524 bytes), and
  `_IC_Para_Default_Handler` at `0x000148a5` (488 bytes). Scene write anchors
  include `API_IC_Scene_Set_Handler` at `0x00014a91` (292 bytes) and
  `API_PWM_Scene_Set_Handler` at `0x00015ab9` (200 bytes). These are stronger
  evidence anchors for command/parser research, but no scene-family BLE or
  BLE-mesh packet format has been proven yet.
  The APK audit also maps seven code anchors to Thumb functions in `.text` and
  verifies their body hashes: `hal_App_Opcode_Handler`,
  `API_IC_Scene_Set_Handler`, `API_PWM_Scene_Set_Handler`,
  `API_IC_Param_Get_Handler`, `API_PWM_Param_Get_Handler`,
  `API_IC_All_Reset_Handler`, and `API_PWM_All_Reset_Handler`. These hashes
  pin the native implementation identity for future disassembly work; runtime
  diagnostics include integer and hex addresses for Ghidra cross-reference, but
  they still do not make the scene command envelope known.
  Fourteen favor/routine/system record/recover and LED/default parameter
  handlers are also tracked separately as native persistence anchors.
- Scene UI catalog metadata spans 51 user-facing scene-family records:
  25 direct BLE `banlanx_scene_ui` records and 26 BLE-mesh
  `banlanx_scene_mesh` records. Pixel limits appear as 1800, 2700, and 3000
  depending on subfamily, with four scene UI records not carrying an explicit
  `maxPixelChannels` value.
- Scene UI models carry explicit pixel limits in catalog metadata:
  1800, 2700, or 3000 depending on subfamily.
- SP52x/SP53x/SP54x custom families carry 3600 pixel limits and, for many
  variants, `maxDataLength=185`.
- Old UniLED separates legacy BLE command formats into SP601, SP60x, BanlanX2,
  BanlanX3, and SP6xx paths. The new catalog now preserves those routing
  distinctions instead of flattening them into one legacy BLE family.
- Old UniLED status layouts for SP601/SP60x expose 11-byte per-channel blocks.
  The new core parses those into channel states and creates an aggregate master
  state when multiple channels are present. It now also preserves old-UniLED
  tail parsing: SP601 reads timer count, complete seven-byte timer records, and
  scene-loop state after the channel blocks, while SP60x reads tail
  sensitivity, timer count, complete seven-byte timer records, four 13-byte
  trigger records, and scene-loop state when enough bytes are present.
  Home Assistant diagnostics hex-encode those raw records; timer/trigger
  editing remains hidden until the record schema and write flow are proven.
- Old UniLED model signatures distinguish SP602E as a 4-output SP60x
  controller and SP608E as an 8-output SP60x controller. The new protocol
  registry preserves that distinction for parser counts, channel validation,
  and Home Assistant output entities.
- Old UniLED delivers SP601, SP60x, and BanlanX2 status through headered,
  possibly segmented BLE notifications. The new core now has strict assemblers
  that validate packet order, message length, and payload length before parsing.
- The SP110E/LED Hue parser accepts the exact issue #40 notification
  `01 65 c4 38 03 00 00 32 69 ff 00 00` as a 12-byte status packet instead
  of waiting for an additional notification.
- Old UniLED BanlanX2 and BanlanX3 status payloads expose the primary channel
  as a single payload with power, brightness, RGB, effect, mode/loop, audio, and
  white tail bytes. The new core preserves the raw numeric values and maps
  effect names for the ported legacy effect tables. Runtime-created V2/V3
  protocol instances now carry the concrete catalog model name, color
  capability, and `spec_functions` bits so non-mic models suppress unsupported
  audio fields, RGB-only models suppress white-tail fields, and sound-effect
  names are not assigned to models whose old-UniLED/APK profile lacks sound
  support. Parsed effect speed and V2 effect length are exposed only for
  singular dynamic effects or auto-dynamic mode; static, white, sound, and
  auto-sound statuses clear those dynamic attributes. Auto-dynamic and
  auto-sound modes force parsed effect type to `Dynamic` and `Sound` like old
  UniLED.
- BanlanX2 status payloads also preserve old-UniLED timer metadata. Bytes
  `12..21` are kept as an opaque timer/status header, byte `22` is the timer
  count when present, and complete seven-byte records from byte `23` are kept
  raw in core diagnostics and hex-encoded in Home Assistant diagnostics. RGBW
  models still use the final two bytes as white-tail levels. Only the timer
  count is exposed as a diagnostic sensor; timer editing remains hidden.
- BanlanX3 status payloads also expose DIY metadata at byte 10 for effect type
  and byte 11 for color count. These bytes are parsed and exposed as
  diagnostics only. Old UniLED comments show tentative `0x1A` DIY color frame
  examples, but no public command builder or verified APK local edit flow has
  been recovered.
- BanlanX3 uses a shorter indexed notification format where only the first
  packet carries the total message length. The new assembler preserves that
  distinction.
- Old UniLED SP6xx status notifications use an unencrypted `0x53` packet frame
  with firmware, light type, power, mode, effect, brightness, RGB, speed,
  length, direction, sensitivity, audio input, on/off animation settings,
  color/white coexistence, power-restore mode, effect play/pause, and DIY-mode
  offsets. The new parser validates the frame, maps light mode/effect names
  when the light type is known, and rejects encoded packets until the decoder is
  proven.
- Old-UniLED issue #67 showed SP530E custom-5xx BLE status arriving as
  zero-based `53 02 00 <total> <index> <length>` fragments whose assembled
  payload is SPTech chunk data. The custom-5xx assembler now accepts that
  fragment shape, and the custom-5xx status parser can decode the assembled
  SPTech settings/status chunks while preserving the direct SP6xx frame path.
- Old UniLED dev_v3 SPTech sources name custom mode `0x07` as `Custom Solid`
  and `0x08` as `Custom Gradient`; uniled-next maps those mode/effect labels
  for the gradient-capable SPTech SPI RGB/RGBW light types `0x86`/`0x88`.
  The model-aware SPTech NET overlay exposes custom-solid `0x13` as `Firework`
  for SP530E only on `0x86`/`0x88`, and for the fixed SP538E/SP548E `0x06`
  plus SP539E/SP549E `0x08` profiles. This improves parsed state and select
  options but does not expose DIY save/edit packet flows.
- Old UniLED also exposes recall-only scene slots for SP601/SP60x devices:
  `SceneAttribute(b)` for slots 0 through 8, displayed as Scene 1 through
  Scene 9. The verified recall packets are `AA 2E 01 <slot>` for SP601 and
  `88 8E 01 <slot>` for SP60x. Legacy scene save methods were stubs, so only
  recall is implemented.
- SP601/SP60x loop control is scene-loop state, not lighting-effect loop. Old
  UniLED exposed this as `SceneLoopFeature` with `AA 30 01 <bool>` for SP601
  and `88 90 01 <bool>` for SP60x, and the APK string table says these
  families do not support lighting effect loop.
- Old UniLED SP6xx sends on/off animation settings with command `0x08` and a
  payload of enable byte, effect, speed, and two-byte pixel count. It sends
  color/white coexistence with `0x0A`, power-restore behavior with `0x0B`, and
  effect play/pause with `0x5D`. The new core validates those values and emits
  the same frames.
- Old UniLED SP6xx changes light type with a multi-command sequence: power off
  when the light is currently on, send `0x6A` with enable byte plus light type
  masked to its low seven bits, send `0x6B` with chip-order index, then send
  `0x53` with a valid mode/effect pair. The new core emits the same sequence
  and adds a state query when it had to move to a fallback mode/effect.
- Old UniLED chip-order lists are generated from permutations of each light
  type's order sequence: `RGB` and `CWX` produce 6 choices, `RGBW` produces 24,
  and `RGBCW` produces 120. The new option layer uses the same permutation
  rules and switches option lists when status or light-type selection changes.
- Old UniLED SP6xx uses `0x52` for static RGB plus level, `0x57` for dynamic
  RGB tuning, `0x51` target `0x01` for white level, `0x61` for static CCT
  cold/warm bytes, and `0x60` for dynamic CCT cold/warm bytes. RGBW commands
  combine RGB plus white-level frames; RGBWW commands combine RGB plus CCT
  frames.
- SP6xx status packets expose color level at byte 35, white level at byte 36,
  static RGB at bytes 37-39, static CCT at bytes 40-41, dynamic RGB at bytes
  47-49, dynamic CCT at bytes 50-51, and the custom/DIY slot byte at byte 52.
  The new parser now preserves RGBW, RGBWW, cold/warm levels, approximate
  Kelvin state for CCT modes, and the custom/DIY slot diagnostic. It also
  mirrors old-UniLED effect-attribute gates: speed, length, direction, and
  play/pause are exposed only when the selected effect in the current
  light-type table is speedable, sizeable, directional, or pausable. SP6xx
  effect-parameter number and switch entities use those parsed values for
  availability, while the packet builders retain old-UniLED-compatible frames
  for explicit command paths. Optimistic state after effect, light-mode, and
  light-type select commands now applies the same gates so stale effect
  parameters do not remain visible while waiting for the next notification.
- Old UniLED sends a state query and then waits for a status notification event
  during BLE updates. The new `DeviceSession.refresh_state()` follows the same
  shape while also accepting transports that return direct response bytes.
- Old UniLED audio input option maps are now preserved in
  `custom_components/uniled/core/options.py`. SP6xx exposes `Int. Mic`,
  `Player`, and `Ext. Mic`; BanlanX2/BanlanX3 expose the same choices only
  when the concrete model's APK `spec_functions` has the `0x02` audio bit.
  This matches old UniLED's `intmic` model split: SP611E/SP616E/SP617E/SP620E,
  SP613E, and SP614E expose audio controls; SP603E/SP621E/SP623E/SP624E do
  not. SP601/SP60x tentative builder maps exist with `Aux In`, but old UniLED
  did not attach an audio-input feature because the parsed input value is
  absent; the new runtime keeps those controls hidden until packet evidence
  proves the feature.
- Old UniLED BanlanX2 and BanlanX3 light mode maps are now preserved as
  `Single FX`, `Cycle Dynamic FX's`, and `Cycle Sound FX's`, but only for the
  same mic/music-capable V2/V3 models. Non-mic V2/V3 models expose
  `effect_loop` instead, matching old UniLED's feature list.
- Runtime-created BanlanX2/BanlanX3 command builders now enforce the same
  concrete profile before transport writes. Non-mic models reject audio input,
  sensitivity, sound-cycle mode, and sound effects; RGB-only models reject RGBW
  chip-order indices and white-only effects. Generic protocol instances remain
  broad for low-level parity tests.
- Runtime and Home Assistant light parity for old-UniLED BanlanX2/BanlanX3 RGB
  colorability: RGB/RGBW requests switch non-colorable current effects to the
  family `Solid Color` effect before sending RGB, while preserving old
  adjustable/colorable effects without an extra prelude.
- Runtime and Home Assistant light parity for old-UniLED RGB level reuse:
  BanlanX2/BanlanX3 RGB frames prefer parsed `color_level`, and static SP6xx
  RGB/RGBW/RGBWW frames reuse current brightness when HA changes color without
  supplying a new brightness.
- RGBW-capable BanlanX2/BanlanX3 models follow old UniLED's HA surface:
  supported light modes are `rgb` plus `white`, not HA `rgbw`. SP617E uses
  `A0 76 02 <white> 00` for white level after selecting `Solid White`
  (`A0 63 01 BF`). SP614E/SP624E use `21 02 <white> FF` after selecting
  `Solid White` (`15 01 CC`). Parsed `Solid White` status maps the white tail
  byte to both `white_level` and brightness. Runtime and Home Assistant light
  writes now preserve old-UniLED's state-dependent brightness routing: once the
  current effect is already `Solid White`, brightness changes send only the
  family white-level payload and do not use the color brightness command.
  Selecting the `Solid White` effect itself also updates the optimistic runtime
  state to white mode and reuses the current white level, defaulting to full
  white when no parsed white level is available.
- BanlanX2/BanlanX3 parsed sound states now preserve old-UniLED's on/off-only
  HA surface. Sound effects and auto-sound light mode report supported color
  mode `onoff`, clear HA brightness, and retain the raw level byte as
  diagnostic `color_level`; RGB/white writes clear that parsed on/off override
  once the device is moved back to a color-capable effect.
- Old UniLED SP601/SP60x expose 41 effect names. The new core preserves those
  names and raw effect IDs, including `Solid`, dynamic effects such as
  `Chasing`, and sound-reactive effects such as `Sound - Full Color Rhythm
  Spectrum`. Old UniLED only returned those effect lists and command payloads
  for physical output channels, so aggregate channel `0` remains effectless.
- Old UniLED BanlanX2 exposes 143 RGB effects plus 18 sound-reactive effects.
  RGBW-capable profiles add `Solid White`. The new core preserves these names
  and IDs, including the legacy typo `Rainbow Metor` for parity.
- Old UniLED BanlanX3 exposes 22 RGB effects plus 3 sound-reactive effects.
  RGBW-capable profiles add `Solid White` at `0xCC`.
- Old UniLED model profiles refine APK catalog facts for effect selection:
  SP617E is BanlanX2 RGBW with sound, SP621E is BanlanX2 RGB without sound,
  SP614E is BanlanX3 RGBW with sound, SP623E is BanlanX3 RGB without sound, and
  SP624E is BanlanX3 RGBW without sound. For other BanlanX2/BanlanX3 catalog
  entries, the `0x02` `spec_functions` bit controls whether sound-reactive
  effects and audio controls are exposed.
- Old UniLED SP6xx effect names are scoped by light mode and by wiring/light
  type. The new core represents fixed submodels as combined `mode - effect`
  labels and sends the proven `0x53 <mode> <effect>` command. The multi-purpose
  `SP630E` now creates a dynamic effect select shell and fills its options from
  the current status packet's light type.
- APK assets under `packages/sp630e` mirror that split with distinct assets for
  light-type setup, dynamic color/white modes, music color/white modes, custom
  favorites, effect loop/play/direction controls, and audio input.
- Runtime diagnostics now expose the shared `/sp630e` APK surface for SP6xx and
  custom 5xx models: 16 route hints, 23 control surfaces, 4 favorite-limit
  hints, exact 5-timer limit and power-off timer-deletion warning text, 19
  music assets, 12 network hints, 7 remote hints, 6 motor hints, 35 app-method
  hints, 35 Blutter-backed app-command ID hints, 8 data-model hints, 27 shared
  native `liblfx.so` renderer hints, 7 protocol gaps, 46 APK asset evidence paths,
  and 10 APK string evidence notes. These are evidence counters only; editable
  DIY, favorite, timer, remote, motor, and native-renderer controls stay hidden
  until command frames are proven.
- SP6xx and custom 5xx `/sp630e` models also expose a disabled planned
  `sp630e_control_surface` select with the 23 APK surface labels. This is a
  planning/evidence surface only and does not send writes.

## Entity Planner Rules

- Every user-facing model gets diagnostic sensors for catalog model, catalog
  model ID, catalog parent ID, raw APK `connectCaps`, decoded APK connect
  capabilities, raw APK `specFunctions`, decoded spec-function bits, raw APK
  `colorCap`, decoded color capabilities, APK feature count, APK feature keys,
  APK feature key/value summary, duplicate-record variant count,
  duplicate-record variant IDs, protocol family, support level, catalog
  transport capabilities, and configured entry transport. `transport`
  describes the resolved local/cloud capabilities for the model,
  while `configured_transport` reports the actual setup route selected by the
  entry, such as `ble`, `lan`, `ble_mesh`, or `manual`.
  `runtime_transport_state` reports the concrete runtime attachment mode:
  command session, mesh transport holder, LAN transport holder, generic
  transport holder, or diagnostic-only.
  `last_refresh_result` reports the last refresh outcome as a diagnostic
  sensor, including `no_session` for recognized diagnostic-only entries,
  `no_response` for attached command sessions that time out, and `ok` for
  adopted parsed state.
  `support_blockers` and `support_blocker_count` report the open
  `_pending`, `_required`, and `accessory_dependency=...` tokens derived from
  `support_disposition`.
- Old UniLED parity candidates get a diagnostic marker and an implementation
  hint so protocol-porting tests can find them.
- Legacy LED Chord/LED Hue config command parity is now ported at the core
  protocol/session layer. `SP107E` covers secondary/matrix RGB, chip type,
  segment count, and segment pixels; `SP110E` covers chip type and segment
  pixels. Home Assistant now exposes the chip type and segment config commands
  as disabled-by-default config entities backed by parsed status diagnostics.
  SP107E secondary/matrix RGB is exposed as the advanced `uniled.set_state`
  `rgb2_color` service field rather than a standalone light entity.
- Color-capable models get a planned `light` entity. The command entity is
  disabled and not marked implemented until the protocol family has command and
  parser tests.
- SP601/SP60x models also get disabled-by-default per-output light plans:
  SP601 exposes Output 1 and Output 2, SP602E exposes Output 1 through Output
  4, and SP608E exposes Output 1 through Output 8. These use
  `legacy_uniled_output` hints and preserve the aggregate `main_light` channel
  as channel `0`. SP601 aggregate light commands are implemented as fan-out
  writes to both physical outputs rather than old-UniLED's channel-0 fallback
  to the last output.
- `maxPixelChannels` creates an implemented `max_pixel_channels` diagnostic
  sensor plus a planned `pixel_count` config number with the exact catalog
  limit: 1800, 2700, 3000, or 3600 pixels. Pixel-count writes remain disabled
  until family-specific command frames are proven.
- Scene UI and scene mesh models get a planned disabled `scene_mode_effect`
  select populated from all 80 APK `ic_mode_*` asset names. These are label and
  asset evidence only, not command values.
- SP601/SP60x get output-scoped effect speed/length controls using safe
  old-UniLED limits, plus output-scoped effect direction and chip-order
  controls. SP601 output effect length is limited to 150; SP60x output effect
  length is limited to 240. The legacy `uniled.set_state` compatibility service
  now applies the same output-scoped guard, so aggregate service calls cannot
  send speed, length, direction, or SP601 sensitivity writes to an arbitrary
  physical output.
- Other ported legacy families get planned effect speed/length controls using
  safe old-UniLED limits. BanlanX2/SP6xx use a maximum effect length of 150.
- Ported legacy families get planned effect loop controls where the protocol
  has a known lighting-effect-loop command. SP601/SP60x instead get an
  aggregate `scene_loop` switch. SP6xx keeps aggregate effect direction;
  SP601/SP60x direction is output-scoped.
- BanlanX2 and BanlanX3 get planned audio input selects, sensitivity numbers,
  and light-mode selects only when the model has the APK `0x02` audio
  capability bit. Non-mic BanlanX2/BanlanX3 models get an effect-loop switch
  instead. SP6xx and custom 5xx keep planned audio controls through their
  family profiles even when the APK catalog does not mark a separate
  `musicFeature`. SP601 sensitivity is output-scoped; SP60x sensitivity is a
  master/tail control. SP601/SP60x audio input remains hidden.
- BanlanX3 models get diagnostic `diy_effect_type` and `diy_color_count`
  sensors from parsed old-UniLED status metadata. DIY edit/save controls remain
  hidden until packet flows are proven beyond old comments and generic APK DIY
  labels.
- SP601/SP60x/BanlanX2 models get diagnostic `timer_count` sensors from parsed
  old-UniLED status bytes. Raw timer and trigger records stay in diagnostics
  only and do not create timer edit controls.
- SP6xx light-mode selects now use old-UniLED mode/effect coupling. Fixed
  SP6xx models expose the light modes from their known light-type profile.
  Dynamic-light-type models such as SP630E, 360PhotoB, and custom 5xx create a
  select shell but keep options empty and the Home Assistant select unavailable
  until parsed status supplies `light_type`.
  Commands send a valid `0x53 <mode> <effect>` pair, keeping the current effect
  only when it belongs to the target mode and otherwise choosing that mode's
  first old-UniLED effect.
- SP601/SP60x get output-scoped chip-order selects; BanlanX2/BanlanX3 get
  aggregate chip-order selects using old UniLED's RGB/RGBW permutation maps
  and wire commands.
- SP601 and SP60x preserve the full 41-entry old UniLED effect map, but runtime
  exposes it only for physical output channels; aggregate channel `0` has no
  effect select, effect list, or chip-order select.
- BanlanX2 and BanlanX3 get planned effect selects using old-UniLED profile
  maps that account for RGB/RGBW and music/non-music variants.
- Fixed SP6xx submodels get planned combined mode/effect selects using old
  UniLED light-type profiles. `SP630E` starts without static planned options
  because the same model can be configured as multiple wiring types; runtime
  entities resolve its options from parsed `light_type` diagnostics.
- SP6xx models get planned on/off animation effect, speed, pixel count,
  power-restore, and effect play/pause controls. Coexistence is planned only for
  fixed RGBW/RGBCCT/RGB-plus-white models and for dynamic light-type models
  (`SP630E` and `360PhotoB`) whose status packet determines whether the current
  wiring type supports it.
- SP6xx models with more than one valid wiring profile get planned light-type
  selects. SP630E and 360PhotoB expose the full 14-profile light-type list;
  fixed CCT/RGBCCT variants with two possible layouts expose their two choices.
  Chip-order selects are planned when the current or fixed light type has a
  known order sequence.
- Pixel-capable models also get planned chip type and color order config
  selectors.
- LAN-capable models get a `lan_profile` diagnostic sensor that reports the
  family, manual-host requirement, known network-info code, max data length,
  APK network/discovery plugin facts, mDNS/socket constants, and whether a LAN
  command protocol has been confirmed.
- Every user-facing model gets a `support_disposition` diagnostic sensor. It
  summarizes safe setup transports, proven command support, RG4/Zengge
  mesh-limited support, diagnostic-only recognized families, pending BLE UUID
  binding, pending LAN frames, pending BLE-mesh frames, scene-family command
  blockers, BanlanX scene-mesh firmware/provisioning/routing blockers, and
  optional-cloud capability without promoting APK-profile evidence into command
  support. The companion `support_blockers` and `support_blocker_count`
  diagnostics expose the same unresolved blocker/requirement tokens used by the
  generated support matrix.
- Optional-cloud models get a `cloud_profile` diagnostic sensor that reports
  BanlanX cloud endpoint, document URL, and auth-token string evidence while
  keeping command support pending until auth, headers, token refresh behavior,
  and command envelopes are proven. The profile also carries a 52-row
  `endpoint_inventory` grouped by APK route family; every row keeps method,
  auth, and base URL binding unresolved until the Flutter/cloud request
  contract is proven. Token/header/signature evidence is also preserved as a
  26-row request-contract hint inventory backed by literal APK strings,
  including `S-AccessKey`, `S-AppVer`, `S-AppVerName2`, `S-SysCode`,
  `S-SysName`, `S-System`, and `S-Timestamp`; all rows remain marked
  unproven and point at the existing account-token or signing-header blockers.
  They also expose
  `cloud_base_url_count`, `cloud_endpoint_count`,
  `cloud_endpoint_inventory_count`, `cloud_endpoint_group_count`,
  `cloud_command_related_endpoint_count`,
  `cloud_unresolved_base_url_endpoint_count`,
  `cloud_unproven_auth_endpoint_count`, `cloud_auth_endpoint_count`,
  `cloud_account_auth_endpoint_count`,
  `cloud_device_endpoint_count`,
  `cloud_home_device_endpoint_count`, `cloud_user_device_endpoint_count`,
  `cloud_local_device_endpoint_count`, `cloud_btmesh_endpoint_count`,
  `cloud_root_device_endpoint_count`, `cloud_raw_command_endpoint_count`,
  `cloud_content_endpoint_count`, `cloud_voice_endpoint_count`,
  `cloud_document_url_count`, `cloud_auth_token_hint_count`,
  `cloud_device_identity_hint_count`, `cloud_http_header_hint_count`,
  `cloud_signature_hint_count`, `cloud_request_contract_hint_count`,
  `cloud_token_contract_hint_count`, `cloud_header_contract_hint_count`,
  `cloud_signature_contract_hint_count`,
  `cloud_transport_hint_count`, `cloud_protocol_gap_count`,
  `cloud_command_blocker_count`, and `cloud_raw_command_endpoint` diagnostics
  from the same APK string evidence. Optional-cloud support disposition now
  uses the same five blockers as the cloud profile:
  `account_token_schema_pending`, `request_signing_headers_pending`,
  `region_reauth_contract_pending`, `raw_command_json_envelope_pending`, and
  `device_bind_ownership_lifecycle_pending` until the missing cloud contracts
  are proven.
- SP801E/SP802E get a `network_profile` diagnostic sensor plus disabled
  `network_surface` and `network_content_mode` selectors populated from
  APK-derived Art-Net/LFX feature-surface evidence. SP801E additionally gets
  disabled `network_artnet_field`, `network_port_field`, and
  `network_playlist_action` selectors populated from exact APK strings. SP802E
  gets disabled `network_lfx_effect` and `network_matrix_music_control`
  selectors populated from the 20 regular LFX effect icon names and five
  matrix-music setter strings in the APK. The same APK evidence now exposes
  `network_surface_count`, `network_content_mode_count`,
  `network_artnet_field_count`, `network_port_field_count`,
  `network_playlist_action_count`, `network_matrix_music_control_count`,
  `network_lfx_effect_count`, `network_lfx_gif_count`,
  `network_app_command_id_count`, and `network_native_frame_hint_count`,
  plus SP802E-only
  `network_native_lfx_param_hint_count`,
  `network_native_effect_generator_hint_count`,
  `network_native_matrix_mode_hint_count`, and
  `network_native_pixel_helper_hint_count` diagnostic sensors, plus
  `network_native_export_detail_count` for the exact Ghidra/dynsym anchors.
  These selectors remain hidden from command entities until BLE/LAN payloads
  are proven.
- LAN profile diagnostics also expose `lan_host_setup_mode`: `discovery_ready`
  for the verified SP541E/SPNet path and `manual_host` for the remaining
  LAN-capable APK families. The concrete DNS-SD service type, SP80x/FT001
  discovery responses, and socket command frames remain unproven.
  They also expose Bonsoir NSD method, discovery-event, service-field,
  service-normalization, service-type flow, TXT-query flow, raw-socket,
  discovery-status, mDNS TXT timeout/type/class, and buffer facts from the APK
  without treating those strings as a packet contract.
- Direct BLE diagnostics now expose decompiled plugin call-contract and
  event-contract hint counts. The APK Java bridge requires
  `serviceUuid`/`characteristicUuid` for characteristic operations, defaults
  notification `enabled` to false, defaults connection `timeout` to zero,
  defaults write `forceWaitResponse` to false, and maps provided
  `characteristicWriteType` values to Android write types. Seven
  argument/default anchors are audited as `ble_plugin_contract` string
  evidence, while discovery defaults and cached-device behavior are tracked as
  Java-decompile-only plugin contract hints. The event payloads are now tracked
  separately: discovery emits `id`, `name`, `rssi`, `serviceData`, and
  `manufacturerData`; connection state emits `deviceId` and `connected`;
  characteristic notification emits `deviceId`, `serviceUuid`,
  `characteristicUuid`, and `value`, and notification enablement writes the
  standard CCCD descriptor
  `00002902-0000-1000-8000-00805f9b34fb`. The notification event channel and
  four payload fields are audited as five `ble_notification_contract` string
  anchors; discovery/connection payloads, the CCCD descriptor, and Java-only
  error codes stay in structured diagnostics but outside the native-string
  audit. The recovered BLE plugin error ledger currently covers
  `10000` adapter-not-open, `10001` adapter unavailable, `10002` missing
  cached device, `10003` connection failure, `10004` missing service,
  `10005` missing characteristic, `10006` unconnected device, `10008`
  generic BLE operation failure, `10012` connection timeout, and `10013`
  missing required argument. The adapter-state request result has boolean
  `available` and `discovering` fields, while adapter-state and discovery-state
  event channels emit booleans. Service discovery result maps expose `uuid`
  and `isPrimary`; characteristic discovery result maps expose `uuid` plus the
  five characteristic capability booleans; RSSI and MTU calls return `rssi` and
  `value` respectively. Start discovery defaults `interval=0`,
  `clearPreDiscoveredDevices=False`, and `aliveTime=10000`, optionally filters
  by supplied service UUIDs, and uses report delay only when batching is
  supported. These hints document bridge behavior only and do not bind
  `ff12`/`ff14`/`ff15` to unported families.
  BLE diagnostics now make that explicit with
  `ble_uuid_binding_status`, `ble_known_service_uuid_count`,
  `ble_known_service_uuids`, `ble_known_write_uuid`,
  `ble_known_notify_uuid`, `ble_apk_uuid_pool`,
  `ble_unbound_uuid_candidate_count=3`,
  `ble_unbound_uuid_candidates`, `ble_legacy_uuid_candidate_count=2`,
  and `ble_legacy_uuid_candidates`.
- `supportGetNetInfo` creates a diagnostic network-info sensor. Until a live
  network-info query frame is proven, the sensor reports the catalog/APK code
  such as `supportGetNetInfo=9; command_protocol_pending`; live device
  diagnostics override this placeholder when present.
- SP6xx and custom 5xx models get a diagnostic `custom_effect_slot` sensor for
  the old-UniLED custom/DIY status byte. APK strings expose SP630E DIY/favorite
  surfaces, but edit/save controls remain planned only until packet flows are
  proven.
- SP6xx and custom 5xx models also get a `sp630e_profile` diagnostic sensor
  plus route/surface/favorite-limit/timer/music/network/remote/motor, method,
  app-command-ID, native-LFX, and native export detail count diagnostics from
  the APK `/sp630e` package. They also expose the full 217-asset package count
  separately from the curated 46
  asset-evidence paths. The native renderer evidence is separately audited
  against `liblfx.so` with `.dynsym=162`, 34 exported anchors, and 7 detail
  anchors. These counts explain the vendor-app surface while command support
  remains limited to the proven old-UniLED-compatible BLE frames.
- The same models expose a disabled planned `sp630e_control_surface` select so
  the 23 APK surface labels are visible to the planner without enabling
  unproven DIY, favorite, timer, remote, motor, or network writes.
- `maxDataLength` creates a diagnostic maximum-data-length sensor.
- `musicFeature` creates planned audio input and sensitivity controls.
- Scene UI and scene mesh families get planned scene slot selection and saved
  scene entities, plus diagnostic `scene_preset_count`,
  `scene_mode_effect_count`, `scene_lfx_route_count`,
  `scene_timer_route_count`,
  `scene_app_command_id_count`,
  `scene_recent_action_count`, `scene_favorite_action_count`,
  `scene_timer_action_count`, `scene_diy_action_count`,
  `scene_white_brightness_anchor_count`,
  `scene_lfx_data_model_hint_count`, `scene_lfx_frame_field_hint_count`, and
  `scene_native_paired_api_count`, `scene_native_ic_only_api_count`,
  `scene_native_loop_handler_count`, `scene_native_frame_hint_count`,
  `scene_native_opcode_hint_count`, `scene_native_state_hint_count`,
  `scene_native_state_export_count`, and
  `scene_native_color_order_hint_count`,
  `scene_native_pwm_table_hint_count`,
  `scene_native_music_effect_hint_count`,
  `scene_native_pwm_driver_hint_count`,
  `scene_native_animation_export_count`,
  `scene_native_drive_export_count`, and
  `scene_native_persistence_handler_count`,
  `scene_native_persistence_export_count`,
  `scene_native_persistence_capability_count`, and
  `scene_native_code_anchor_count` sensors from APK assets/routes,
  native strings, and audited `libscene_lfx.so` exports/code bodies. They also expose
  `scene_command_blocker_count=7` from the same profile. Recent/favorite/timer/
  DIY/white-brightness selectors remain disabled pending confirmed command and
  status frames.
- Car-light family models get planned accessory-role and required-controller
  diagnostics plus setup-stage/setup-order diagnostics and disabled zone,
  trigger, control-surface, subdevice-filter, password-flow-state, and
  trigger-action selections. They now also expose APK-proven
  `car_light_zone_count`, `car_light_trigger_count`,
  `car_light_control_surface_count`, `car_light_animation_asset_count`,
  `car_light_trigger_image_asset_count`, `car_light_zone_image_asset_count`,
  `car_light_subdevice_filter_count`,
  `car_light_password_flow_state_count`,
  `car_light_password_entry_hint_count`,
  `car_light_password_policy_hint_count`, `car_light_password_reset_hint_count`,
  `car_light_setup_flow_hint_count`, `car_light_setup_key_hint_count`,
  `car_light_model_role_hint_count`, `car_light_setup_dependency`,
  `car_light_setup_dependency_count`,
  `car_light_required_setup_dependency_count`,
  `car_light_ordered_setup_model_count`, and `car_light_trigger_action_count`
  diagnostic sensors while those controls remain disabled pending confirmed
  command and event frames.
- FT001 gets fish-tank profile, favorite-slot-count, timer-limit, channel,
  control-surface, effect, favorite, timer, asset-bucket, favorite-action,
  favorite-loop-action, firmware-prompt, app-command-ID, and raw-string
  surfaces from APK labels. Channel/effect/favorite/timer/favorite-loop selectors remain
  disabled pending confirmed command frames.
- Mesh remote/control models get mesh-role diagnostics and a planned remote
  event diagnostic. RG4/Zengge mesh-role diagnostics now report
  transport/paired status, command-capable node counts, panel counts, and
  bridge presence, while known RGB/CCT panel nodes expose diagnostic
  `Online`/`Offline` status sensors without enabling non-light commands.
- BLE mesh models get a `mesh_profile` diagnostic sensor that distinguishes
  old-UniLED Telink/Zengge evidence from catalog-only BanlanX scene-mesh
  routing, including ported command names, Zengge effect packet fields, and
  remaining mesh-control gaps/blockers. Both BLE-mesh profiles now expose the
  six APK-recovered Bluetooth SIG Mesh provisioning/proxy UUID anchors as
  `mesh_sig_mesh_uuid_hint_count` and the 12 shared Blutter mesh app-command
  enum IDs as `mesh_app_command_id_count`; these are evidence only and do not
  prove a provisioning frame sequence or command envelope. BanlanX scene mesh
  exposes the three APK
  one-touch provisioning guide lines as setup hints, while RG4 exposes route,
  provisioning hint,
  provisioning state, APK package-asset, APK asset, and APK string evidence
  counts from `packages/accessories`, plus a disabled planned
  `mesh_provisioning_state` select for the nine APK callback-state labels and
  `mesh_control_blocker_count=4` for the still-unimplemented non-light mesh
  contracts.
  Those counts and labels are diagnostics/planner evidence only until packet
  frames for provisioning and remote events are proven.

## Home Assistant Shell Status

Implemented:

- `async_setup_entry` builds a `UniLEDRuntime` from config entry data, creates
  a `UniLEDCoordinator`, attaches any runtime transports, performs the first
  coordinator refresh, then stores the runtime in `entry.runtime_data` and
  forwards the diagnostic sensor, light, number, select, switch, scene, and
  button platforms. If transport attachment, first refresh, or platform
  forwarding fails, setup closes the runtime before re-raising so Home
  Assistant can retry without a stale half-attached runtime.
- `async_unload_entry` unloads platforms and, only after Home Assistant reports
  platform unload success, closes runtime-held transports plus coordinator and
  notification assembler references. If platform unload fails, runtime
  resources stay open for retry/recovery. Runtime close is best-effort across
  command sessions, diagnostic LAN holders, and Zengge mesh holders: transport
  close errors are recorded as `last_close_error`, while runtime references are
  still cleared so reloads cannot reuse stale sessions.
- The setup/unload shape follows the current Home Assistant developer docs:
  typed `ConfigEntry[UniLEDRuntime]`, `entry.runtime_data`,
  `async_forward_entry_setups`, and `async_unload_platforms`.
- `sensor.py` exposes implemented diagnostic sensors generated from the entity
  plan, forwards each feature's native unit where one is defined, and applies
  Home Assistant translation keys for all catalog/profile diagnostic sensor
  names. Dynamic Zengge panel-status diagnostics use a `{node}` placeholder.
- `light.py` exposes aggregate RGB command lights for session-backed entries,
  plus disabled-by-default SP601/SP60x physical output lights that send through
  the same channel-aware `DeviceSession` command builders. SP602E is limited
  to four physical outputs and SP608E to eight. It sends power, brightness,
  RGB, mapped BanlanX2/BanlanX3 effects, output-scoped SP601/SP60x effects,
  and SP6xx combined mode/effect commands through `DeviceSession`.
- `light.py` now exposes dynamic `supported_color_modes` for SP6xx models based
  on parsed light type and coexistence state, and sends RGBW, RGBWW, white, and
  Kelvin color-temperature commands through `DeviceSession` where supported.
  Runtime color-mode normalization also strips Home Assistant-invalid
  `brightness` or `onoff` entries when richer modes such as `rgb` are present,
  covering the old UniLED `{'brightness', 'rgb'}` failure mode reported for
  SP530E/BanlanX controllers. HA artifact tests also pin Kelvin-only color
  temperature usage so the removed legacy `ATTR_COLOR_TEMP` import cannot
  return.
- `number.py` exposes session-backed output-scoped SP601/SP60x effect
  speed/length controls, SP601 output sensitivity, SP60x master sensitivity,
  aggregate controls for other legacy families, and SP6xx on/off animation
  pixel-count controls where those planned features exist.
- `select.py` exposes session-backed audio input controls for BanlanX2,
  BanlanX3, SP6xx, and custom 5xx families, output-scoped SP601/SP60x
  effect/chip-order controls, BanlanX2/BanlanX3 effect and chip-order controls,
  fixed-subtype SP6xx combined mode/effect controls, dynamic SP630E/360PhotoB
  and custom 5xx effect controls once light type is known, SP6xx on/off
  animation effect/speed controls, SP6xx power-restore controls, SP6xx
  light-type/chip-order configuration controls, plus light-mode controls for
  BanlanX2 and BanlanX3.
  Direct runtime tests now prove address-backed APK-inferred command models
  are not downgraded to diagnostics-only setup: `SP603E` attaches a BLE command
  session, exposes the non-sound BanlanX3 effect/chip-order/effect-loop
  surface, and keeps audio controls hidden; `360PhotoB` attaches the SP6xx BLE
  command session, exposes dynamic light-type controls, and surfaces SP6xx
  audio/on-off/effect controls after a parsed light type is known.
  A direct `SP630E` regression covers old UniLED issue #121 by proving the
  setup helper creates a BLE command session and `main_light` alongside RSSI
  diagnostics, instead of loading the device as Signal-strength-only.
  A catalog-wide runtime regression test also proves all 94 command-protocol
  ready BLE models attach a BLE session through the Home Assistant setup helper
  and expose at least one session-backed command light.
- `switch.py` exposes session-backed output-scoped SP601/SP60x effect
  direction, aggregate SP601/SP60x scene loop, aggregate effect loop for
  families with a proven lighting-effect-loop command, SP6xx effect
  direction/play/pause,
  and SP6xx coexistence controls where those planned features exist.
- `button.py` exposes a diagnostic refresh button for protocol-backed BLE
  entries and RG4/Zengge mesh entries after the corresponding refresh transport
  is attached. It uses `UniLEDCoordinator.async_request_refresh()` instead of
  inventing any new device command frame.
- `light.py`, `number.py`, `select.py`, `switch.py`, `scene.py`, and
  `button.py` now share Home Assistant entity translation metadata for exposed
  command entities. Output-scoped controls use `{output}`, recall scenes use
  `{slot}`, and paired Zengge mesh node entities use `{node}` placeholders.
- All entity platforms now share stable Home Assistant entity unique-ID and
  device-registry identity helpers. New entries use the config-entry
  `unique_id`; migrated or older entries derive the same stable identity from
  normalized BLE address, LAN host, SPNet LAN MAC, mesh UUID/device ID, or
  manual device ID. BLE and BLE-mesh entries expose Bluetooth device
  connections, and SPNet LAN entries expose a network-MAC connection from
  either response MAC data or a migrated bare-MAC config-entry `unique_id`, so
  current Home Assistant can keep the device registry tied to the physical
  adapter address.
- The legacy `uniled.set_state` light entity service is restored through the
  current Home Assistant
  `service.async_register_platform_entity_service(...)` API from integration
  `async_setup`. The entity method delegates to a runtime helper that sends
  through `DeviceSession` or guarded paired Zengge mesh commands, maps
  `transition` to proven RG4/Zengge gradual bytes for control-payload-backed
  mesh commands, and returns cleanly for diagnostic-only families without a
  command path.
- `diagnostics.py` returns sanitized model, runtime, entity-plan, and parser
  readiness data, redacting mesh credentials, cloud usernames/passwords, and
  device identifiers where entry data is echoed.
- Runtime diagnostics include a structured old-UniLED parity profile for
  legacy-supported BanlanX models. The profile names the old source module,
  command builders ported into the new core, parser evidence, and old stubbed
  builders that remain intentionally unsupported.
- Runtime diagnostics include a structured LAN profile for LAN-capable models,
  with redacted entry identifiers and explicit pending command/discovery
  protocol flags, plus compact LAN evidence diagnostics for APK host-network,
  discovery, network setup route/prompt, cloud-setup warning, multicast-lock,
  Bonsoir methods/events/service fields/normalization, Android NSD method flow,
  discovery-gap, raw-socket and discovery-status anchors, UDP timeout/buffer,
  mDNS TXT-buffer facts, and
  custom 5xx SPNet/SPTECH discovery-candidate anchors where proven for SP541E.
  Custom 5xx LAN profiles also carry old-UniLED SPTech model/configuration
  code aliases as recognition diagnostics only.
- Runtime diagnostics include a structured BanlanX cloud profile for
  optional-cloud models, including split endpoint groups for device auth,
  account auth/lifecycle, `/home/device`, `/user/device`,
  `/user/local-device`, `/user/btmesh`, root device routes, content, voice,
  document URLs, 10 device-identity/schema hints, 26 token/header/signature
  request-contract hints split into 10 token/storage, 11 HTTP-header, and 5
  signature/nonce rows, 9 endpoint groups, one command-adjacent endpoint, 52
  unresolved base URL bindings, 52 unproven auth bindings, and command-protocol
  gap hints without storing account credentials. The profile now carries 97
  audited cloud anchors,
  including `deviceCode`, `deviceUdids =`,
  `device_udid`, `device_key`, `device_to_group_mapping`, and
  `mobile_device_identifier`; these feed the
  `cloud_device_identity_hint_count` diagnostic but do not make cloud commands
  protocol-ready.
- Runtime diagnostics include a structured BLE mesh profile for mesh-capable
  models, without exposing mesh passwords or marking the core command protocol
  ready prematurely.
- Home Assistant-independent setup data helpers at
  `custom_components/uniled/setup_data.py` validate manual, direct BLE,
  BLE-mesh, and LAN setup entry data without importing Home Assistant.
- The same setup-data helper now validates Bluetooth discovery data without
  importing Home Assistant. Exact catalog names use direct BLE or BLE-mesh
  transport metadata, BanlanX manufacturer data can resolve direct BLE model IDs
  for user-facing BLE catalog rows, and generic Telink mesh advertisements
  resolve to RG4 diagnostic entries.
- `config_flow.py` supports diagnostic/manual catalog model setup, manual
  BLE-by-address setup for BLE-capable models, manual host/IP setup for
  LAN-capable models, manual RG4/Zengge BLE-mesh setup with old UniLED mesh
  identity, manual BanlanX scene-mesh diagnostic setup with local
  `ble_mesh:<address>` identity, exact-name Bluetooth setup, and
  BanlanX direct-BLE plus RG4/Zengge mesh manufacturer-data discovery.
- `config_flow.py` also supports a current Home Assistant reconfigure step for
  repairing BLE address, LAN host, manual device ID, and RG4/Zengge local mesh
  node metadata. It replaces entry data through
  `async_update_reload_and_abort(..., data=...)`, verifies the existing unique
  ID when present, and rejects changing an existing Zengge mesh UUID.
- Config-entry migration is wired through `async_migrate_entry` using the
  current Home Assistant `async_update_entry` API with version/minor-version
  updates. The first migration pass maps legacy UniLED `ble`, `net`, and `zng`
  entries into the new schema, drops old transient MagicHue login credentials,
  preserves Zengge mesh identity when available, and derives address-backed
  BanlanX scene-mesh identity instead of old Zengge identity. Direct tests now
  prove the hook preserves existing old raw-address config-entry unique IDs
  while updating data/version fields, and creates a sanitized migration repair
  issue instead of updating unsafe legacy entries.
- Initial Home Assistant repair issue creation is wired for unsafe config-entry
  data. Migration failures and runtime setup failures create non-fixable,
  sanitized repair issues with entry title, failed field, and symbolic reason;
  successful migration/setup deletes the matching issue. Invalid stored setup
  data is tested at the actual `async_setup_entry` hook so platform forwarding
  cannot happen after a runtime resolution failure. Valid stored setup data is
  also tested at the hook: it clears stale setup issues, links the coordinator,
  performs the first refresh once, stores runtime data, and forwards the
  configured Home Assistant platforms. Additional setup-failure tests prove
  first-refresh and platform-forwarding failures close the runtime before
  re-raising, without leaving stale runtime data. Direct unload tests prove
  platform unload is requested for the same platform list, runtime resources
  close only after unload succeeds, and failed platform unload leaves runtime
  resources open for Home Assistant retry/recovery. Runtime close tests prove
  diagnostic LAN holders are closed and transport close errors still clear
  runtime session/coordinator references while recording `last_close_error`.
- `manifest.json` includes BanlanX manufacturer-data wake-up matchers for IDs
  `20563` (`0x5053`) and `5053`, plus a narrow Telink/Zengge BLE matcher using
  both manufacturer ID `529` and service UUID
  `00010203-0405-0607-0809-0a0b0c0d1910`, matching current Home Assistant
  Bluetooth manifest matcher support. Catalog coverage tests also prove the
  local-name matchers cover every current user-facing BLE or BLE-mesh model
  name, the BanlanX manufacturer matchers remain present for issue-style
  name-less advertisements, and every Bluetooth matcher stays connectable. The
  Telink matcher deliberately avoids `manufacturer_data_start` because
  manufacturer bytes `0..1` carry the variable mesh UUID.
- Runtime can attach a `DeviceSession` when a command protocol exists. The
  session owns high-level command dispatch, command results, and notification
  parsing state. Runtime diagnostics expose this as
  `runtime_transport_state=command_session`.
- Address-backed entries with a known BLE profile now get a lazy BLE transport
  attached during setup. The first coordinator refresh now sends a state query,
  parses direct response bytes when present, or waits briefly for a complete
  status notification.
- Address-backed RG4/Zengge mesh entries now get the Zengge mesh transport
  holder attached during setup. The coordinator can attempt pairing and send
  the old status-notification kick. Paired known command-capable nodes can now
  expose light entities and guarded effect selects; broader mesh controls
  remain outstanding. Runtime diagnostics expose the unpaired holder as
  `runtime_transport_state=mesh_transport` and the paired state as
  `mesh_transport_paired`.
- Host-backed LAN entries now get a LAN transport attached during setup. Most
  unproven LAN models still use a diagnostic/runtime holder that closes cleanly
  and refuses command sends until a model-specific LAN packet protocol is
  mapped. SP541E LAN entries use the SPTech TCP transport and expose
  `runtime_transport_state=command_session`.
  HA 2026.7 live testing caught and fixed a startup SPNet discovery API
  mismatch: flow handoff now uses the literal current Home Assistant
  discovery source string instead of a removed `data_entry_flow` constant.
  The startup SPNet discovery task is also guarded as a single in-flight
  background pass: repeated starts reuse the current task, completion or
  failure clears the stored task handle, and one failed config-flow handoff
  logs the affected host without dropping later discovered SP541E candidates.
  Integration setup, entry setup, migration, config flows, discovery flows, and
  options flows now load the bundled catalog through Home Assistant's executor
  so the cached catalog is not first read from disk inside the event loop. A
  Home Assistant artifact test guards `config_flow.py` against direct
  `default_catalog()` calls.
  Runtime setup-helper tests cover the LAN-only `SP801E`, BLE+LAN `SP802E`,
  optional-cloud `FT001`, and protocol-backed custom 5xx LAN shapes explicitly.
  Catalog/setup/runtime tests also cover APK friendly-label resolution for
  `FT001` and safe suffixed BLE local-name discovery such as `SP601E_AABB`.
  Decompiled Bonsoir Java confirms that `discovery.initialize` stores a
  Dart-supplied session type as the Android NSD service type,
  `discovery.start` passes that value to `NsdManager.discoverServices`,
  `resolveService` rebuilds an `NsdServiceInfo` from service name/type,
  `broadcast.initialize` stores `service.type`, and `broadcast.start`
  registers service type, port, host, and TXT attributes through
  `NsdManager.registerService`. It also confirms `discoveryServiceFound`
  schedules a secondary TXT-record query and updates service attributes when
  the parsed TXT map changes. The event bridge emits discovery start/stop,
  found/resolved/lost, TXT-resolved/TXT-failed, and discovery-error events with
  `id` plus nested `service.*` fields; it trims trailing-dot service types,
  emits host addresses as strings, decodes TXT bytes as UTF-8, normalizes null
  TXT values to empty strings, and serializes Android `resolveService` calls.
  A targeted APK/Blutter pass found multicast/raw datagram anchors but no
  concrete `_tcp`/`_udp` DNS-SD service type. The concrete BanlanX DNS-SD
  service type and TXT schema remain unrecovered; the only non-manual LAN
  discovery/setup path currently proven is the SP541E startup SPNet UDP scan
  plus source-host helper.

Not implemented yet:

- Car-light command builders, notification parsers, and Home Assistant command
  entities. The profile and accessory roles are implemented as diagnostics only.
- FT001 fish-tank command builders, notification parsers, LAN refresh, timer
  entities, and Home Assistant command entities. The profile is implemented as
  diagnostics only.
- Scene UI/scene mesh command builders, notification parsers, saved-scene
  entity behavior, BLE-mesh/group behavior, and Home Assistant command
  entities. The profile is implemented as diagnostics only.
- Hardware-validated BLE setup behavior across every ported profile.
- Live initial state queries for unported LAN families and unported BLE
  families. SP541E LAN state refresh is implemented and live-tested.
- Custom/scene command-capable effect selects, per-output entities beyond the
  proven SP601/SP60x physical outputs, and hardware-validated
  white/color-temperature behavior across every SP6xx wiring type.
- Automatic repair flows and richer repair coverage beyond initial invalid
  migration/setup issue creation.
- Home Assistant startup SPNet LAN scanning is implemented for the verified
  SP541E path. A safe UDP discovery pass from the Windows dev host did not
  receive responses on 2026-07-05, but the same packet sent from the Home
  Assistant host and through the deployed discovery helper received all three
  live SP541E responses with source host, model byte `0x5c`, MAC, and response
  name. The deployed setup helper now returns the same bare-MAC unique IDs as
  the migrated old-UniLED entries (`54:20:24:11:1f:77`,
  `56:20:24:06:d6:ee`, and `56:20:24:06:d9:d6`), preventing duplicate
  config entries when startup discovery sees already-migrated strips. The
  compatibility pre-check also treats MAC-shaped LAN `device_id` values as
  case-insensitive duplicate blockers before entry creation. Startup discovery
  task tests prove one in-flight SPNet scan is reused, successful and failed
  scans clear their stored task handle, and a failed handoff for one candidate
  does not stop later SP541E candidates from being handed to the config flow.
  Broader
  DNS-SD/mDNS, SP80x/FT001/custom LAN discovery, periodic rescans, and
  non-SP541E LAN command paths are not implemented yet; for other LAN models,
  setup attaches only the guarded diagnostic holder.
- BanlanX cloud login, reauth, device ownership/bind behavior, and
  `/user/device/post/raw` command envelopes are not implemented.

## 0.1 Publication Track

The next milestone is a limited 0.1 beta, not broad full-catalog support. The
release scope is SP541E LAN, old-UniLED-compatible BLE parity, limited
RG4/Zengge mesh, and diagnostic-only handling for unproven APK catalog devices.
The detailed plan is maintained in `docs/RELEASE_0_1_PLAN.md`.

The highest-priority blocker from the current technical review, Home Assistant
entity registry default enablement, is now implemented. Planner features carry
`FeatureSpec.enabled_by_default`, and the HA entity classes publish that value
through `_attr_entity_registry_enabled_default` so normal users are not flooded
with planned diagnostics or disabled research controls. The 2026-07-05 quality
gate covers this through entity-metadata, runtime, and HA artifact tests.

The startup blocking-I/O risk for SPNet LAN address discovery is also fixed in
code: the async discovery path now resolves local IPv4 addresses through
`hass.async_add_executor_job` when Home Assistant is available, falling back to
`run_in_executor` outside HA, and tests prove the synchronous address probe is
not called directly from the async path.

Runtime command dispatch is now serialized at the core session boundaries.
`DeviceSession` locks high-level command payload groups and keeps state refresh
locked through direct response or notification handling; `ZenggeMeshConnection`
locks pair, status, and command characteristic writes so paired-node commands
cannot overlap on the shared mesh transport.

The HA-boundary test slice is satisfied for 0.1 by a clearly named optional
live gate because `pytest-homeassistant-custom-component` currently fails to
install locally before tests run on Windows ARM64 native dependencies.
`scripts/ha_live_boundary_gate.py` uses the HA HTTP API without printing
tokens. A read-only run against Home Assistant `2026.7.0` verified
`uniled.set_state`, `light.turn_on`, and the three known SP541E light entities.

Publication docs/package polish is mostly complete: the README links the 0.1
install guide and release notes, and `python scripts\build_package.py` writes
`dist/uniled-next.zip` with 53 validated Home Assistant custom-component files
and no bundled image/logo assets.

Live HA API smoke on 2026-07-05 progressed without deploying the latest local
candidate: using `http://192.168.0.157:8123` and refreshed dashboard
credentials, `light.raam_strip`, `light.muur_strip`, and `light.midden_strip`
were captured as `off`, turned on at brightness `77`, observed as `on:77`, and
restored to `off`. This proves the currently deployed SP541E service path is
healthy, but it is not the final 0.1 candidate smoke because deployment/restart
and log review are still blocked by access. `core_ssh` and `a0d7b954_ssh` can
be started through HA services, but available local SSH keys are denied and
`hassio.addon_stdin` returns HTTP 500 for both add-ons; Samba is present but
anonymous listing is denied.

Remaining 0.1 blockers are one final SP541E live Home Assistant smoke test and
the post-smoke `manifest.json` version bump to `0.1.0`. The current P0 estimate
is 0.35-0.75 engineering weeks, with another 2.0-4.0 engineering weeks of P1
tester polish before a wider tester group.

## Next Build Targets

1. LAN-first house-light target: three local `SP541E` monochrome LED strips.
   The canonical APK row is model `92`, family `banlanx_custom_5xx`,
   transports `ble`, `lan`, and `cloud_optional`, with `maxDataLength=185`.
   Live Home Assistant 2026.7.0 registry/state checks confirm the three strips
   are registered as `SPLED (BanlanX)` `PWM Mono (Wi-Fi) Controller` devices,
   hardware `SP541E`, firmware `V3.0.11`, with MAC device-registry connections
   and MAC-derived UniLED entity unique IDs. The working light surface is
   brightness-only: the strip entities support Home Assistant `brightness`
   color mode, report `light_type=1 CH PWM - Single Color` and
   `light_mode=Static White`, and expose `Static White`, `Dynamic White`, and
   `Sound - White` mode options. Effect speed, effect length, and effect
   direction entities exist but are unavailable while these mono units are in
   static-white/off states.
   The SPTech LAN contract is now implemented: UDP discovery evidence uses port
   `6454`, request `53704e65740000200000000002e0`, response prefix
   `53704e6574000021000000000001`, SP541E model code `0x5c` at payload offset
   `3`, MAC bytes at payload offsets `5..10`, and response name `SP541E`; TCP
   control uses port `8587`; commands are wrapped in `SPTECH\0`
   (`53505445434800`) followed by command, key, two zero bytes, and a two-byte
   big-endian payload length. The read-only state query is
   `53505445434800020000000000` and expects a 13-byte response header plus a
   chunked payload. With Home Assistant
   stopped, the standalone probe successfully queried all three strips, parsed
   firmware, power, brightness, static white mode, and mono `light_type`, and
   pinned a live parser fixture. Zero-byte state-query responses are now treated
   as session contention when HA or the official app already owns the socket.
   Live deployment against Home Assistant `2026.7.0` is verified. The new
   component migrates the legacy UniLED version-3 entries under config-entry
   schema version `4`, avoids broad Bluetooth manifest matchers such as `SP*`,
   preserves legacy MAC-derived unique IDs for `light.raam_strip`,
   `light.muur_strip`, and `light.midden_strip`, attaches `SPTechLANProtocol`
   to SP541E LAN runtimes, and uses the async TCP `UniLEDLANTransport`.
   A follow-up HA 2026.7 deployment fixed the SPNet discovery source constant
   and moved bundled-catalog preload into Home Assistant's executor; recent
   logs no longer show the SPNet discovery traceback or catalog blocking-call
   warning after restart.
   Runtime diagnostics reported `runtime_transport_state=command_session` and
   `last_refresh_result=ok` for all three entries, HA held established TCP
   sessions to all three strips, and reversible Home Assistant service calls
   changed brightness/power and restored the original states.
   Current light entities are attached to MAC-backed `BanlanX`/`SP541E` device
   rows with `("uniled", <mac>)` identifiers and network-MAC connections.
   Live registry inspection found older old-UniLED device-registry rows held by
   legacy entity-registry entries for audio sensitivity, audio input,
   effect-loop, effect-play, and effect-type. The SP541E compatibility unique-ID
   map now claims those equivalent entities too, and UniLED Next exposes
   `effect_type` as a diagnostic sensor for command-protocol-backed models so
   old `sensor.<name>_effect_type` rows can move onto the current MAC-backed
   device row on reload. After redeploy/restart, the live registry audit
   reported three safe stale device-row candidates, one per SP541E strip, and
   zero disabled-only blockers. The `scripts/audit_ha_uniled_registry.py`
   helper remains the safe way to verify whether old device rows are
   unreferenced cleanup candidates before any explicit cleanup.
2. Port old UniLED BLE protocol families that match BanlanX APK catalog records
   into Home Assistant-independent core modules and mark matching models
   `limited` or `full` only with tests.
3. Implement Home Assistant setup around the catalog resolver:
   manual model setup, Bluetooth discovery routing, typed runtime data, unload,
   diagnostics, and repairs.
4. Research and document command/state behavior for:
   `banlanx_custom_5xx`, `banlanx_scene_ui`, `banlanx_scene_mesh`,
   `banlanx_car_lights`, `banlanx_network`, `fish_tank`, and remaining
   non-light `zengge_mesh` surfaces.
5. Promote support level family by family as protocol commands, parsers, entity
   plans, and tests land.

## Protocol Command And Parser Status

Implemented in the core command layer:

- `banlanx_601`: state query, power, brightness, RGB color, physical-output
  effect, effect speed, effect length, effect direction, scene loop, audio
  input, sensitivity, chip order, and nine-slot scene recall.
- `banlanx_60x`: state query, power, brightness, RGB color, physical-output
  effect, effect speed, effect length, effect direction, scene loop, audio
  input, sensitivity, chip order, and nine-slot scene recall.
- `banlanx_v2`: state query, power, brightness, RGB color, effect, light mode,
  effect speed, effect length, effect loop, audio input, sensitivity, chip
  order.
- `banlanx_v3`: state query, power, brightness, RGB color, effect, light mode,
  effect speed, effect loop, audio input, sensitivity, chip order.
- `banlanx_6xx`: framed state query, power, brightness, static RGB color,
  dynamic RGB color, RGBW color, RGBWW color, white level, CCT cold/warm color,
  light mode/effect, effect speed, effect length, effect direction, effect loop,
  audio input, sensitivity, on/off animation configuration, color/white
  coexistence, power-restore behavior, effect play/pause, light-type
  configuration, and chip-order configuration.

Implemented in the core parser layer:

- `banlanx_601`: 11-byte channel status blocks, aggregate master state, raw
  seven-byte timer-record diagnostics, and tail scene-loop parsing.
- `banlanx_60x`: 11-byte channel status blocks with two-byte effect length,
  aggregate master state, tail sensitivity, raw seven-byte timer-record
  diagnostics, raw 13-byte trigger-record diagnostics, and tail scene-loop
  parsing after the old-UniLED trigger records.
- `banlanx_v2`: single-payload power, loop/mode, effect, chip order,
  brightness, speed, length, RGB, model-gated audio input/sensitivity,
  timer-count and raw seven-byte timer-record diagnostics, and model-gated
  white tail bytes.
- `banlanx_v3`: single-payload power, brightness, speed, chip order, effect,
  mode, RGB, model-gated sensitivity/audio input, DIY metadata, and model-gated
  white tail bytes.
- `banlanx_6xx`: unencrypted framed status packets with firmware, power,
  light type, mode, effect, brightness, RGB, speed, length, direction,
  sensitivity, audio input, on/off animation settings, color/white coexistence,
  power-restore behavior, effect play/pause, DIY metadata, and light-type-aware
  effect names. Chip order and light type are preserved as raw values and
  resolved to select options in the runtime layer. RGBW/RGBWW/CCT status bytes
  are now preserved when the parsed light type supports those channels.
- `zengge_mesh`: decrypted `0xDC` notification messages with two five-byte
  node blocks, including online/offline status, power, brightness, RGB HSV,
  CCT Kelvin, dynamic effect marker, old-UniLED strip/bulb/panel/bridge role
  metadata, and node diagnostics. These facts now feed the core mesh session
  and guarded paired-node light entities after pairing plus role-count and
  panel-status diagnostic sensors; remote and other non-light mesh event
  behavior still needs live-device evidence.

Implemented in the notification assembly layer:

- `banlanx_601`: `0x53 0x43` headered segmented notifications.
- `banlanx_60x`: `0x36 0x38` headered segmented notifications.
- `banlanx_v2`: `0x53 0x43` headered segmented notifications.
- `banlanx_v3`: indexed initial/continuation notifications.
- `banlanx_6xx`: direct packet pass-through to the SP6xx frame parser.

Implemented in the session layer:

- High-level command methods for state query, power, brightness, RGB color,
  dynamic RGB color, RGBW color, RGBWW color, white level, CCT color, effect,
  light mode, effect speed, effect length, direction, effect loop, scene loop,
  audio input,
  sensitivity, SP6xx on/off animation configuration, coexistence, power-restore
  behavior, effect play/pause, light-type configuration, chip-order
  configuration, and recall-only scene slots for legacy SP601/SP60x families.
- Home Assistant scene platform wiring for session-backed SP601/SP60x scene
  recall. Scene entities are disabled by default and expose only legacy recall,
  not scene save/edit behavior.
- Home Assistant light platform wiring for session-backed SP601/SP60x physical
  outputs. Output entities are disabled by default and preserve the old-UniLED
  aggregate channel behavior for the existing main light.
- Sequential dispatch of one or more protocol payloads through a minimal async
  byte transport.
- Response-aware state query support.
- State refresh that can parse direct response bytes or wait for a complete
  notification after sending a query.
- Session-owned notification assembler state so segmented BLE notifications can
  be parsed across callbacks.

Not implemented yet:

- LAN byte movement, service discovery, and command framing outside the
  verified SP541E SPTech path. BLE now exists for the ported legacy profiles
  and custom 5xx SP6xx-style profiles; SP541E LAN control is live-tested, while
  other LAN families still have profile facts and guarded host holders only.
- Home Assistant entity wiring for scene-family effect selects,
  identify/save/restore buttons, saved-scene editing/playlists, and richer
  light capabilities beyond the
  initial session-backed RGB light, SP601/SP60x physical output lights, effect
  number/select/switch controls, and legacy SP601/SP60x recall scenes. The safe
  refresh button is implemented.
- Hardware verification of Home Assistant BLE notification callbacks across the
  ported device families.
- Encoded/encrypted SP6xx status packet decoding. Old UniLED also rejected
  nonzero SP6xx message-key packets, so this still needs APK/native or hardware
  evidence before implementation.
- Human-readable effect-name tables beyond
  SP601/SP60x/BanlanX2/BanlanX3/fixed-SP6xx and mode-specific feature gating
  in the new core parser output.
- BanlanX3 DIY color edit/save command coverage. The current integration
  exposes old-UniLED DIY status metadata as diagnostics, but the local command
  frames are not implemented from comment-only evidence.
- Scene UI, car-light, network, fish-tank, and BanlanX scene-mesh command or
  session integration. Zengge/RG4 now has profile facts, discovery identity,
  packet crypto helpers, command packet builders, decrypted notification
  parsers, an initial characteristic-specific HA transport class,
  setup/runtime attachment, pairing/status refresh, guarded runtime node
  commands, initial paired-node light entities, parsed cloud metadata, and
  optional Bluetooth-discovery/manual/options cloud import, but not non-light
  mesh entities or complete multi-node Home Assistant controls.
- Custom 5xx LAN/provisioning and any LAN command behavior beyond the verified
  SP541E SPTech path, SP6xx-style BLE command/status surface, and model-scoped
  dev_v3 SPTech NET effect mapping.
- Network-info query command bytes. `supportGetNetInfo` values are now tracked
  and exposed as diagnostics, but no query frame should be sent until
  APK/native or hardware evidence proves the command path.
- Editable/favorite SP6xx custom slot behavior. The current integration
  exposes the old-UniLED custom/DIY status byte as diagnostics, but local
  edit/save/favorite packet flows are still unproven.

## Verification Commands

The latest local verification run on 2026-07-06 used the full release gate and
covered 452 pytest tests with 0 failures.

```powershell
python scripts\quality_gate.py
```
