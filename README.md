# UniLED Next

Clean-start Home Assistant integration for BanlanX / SPLED LED controllers.

## Publication Status

UniLED Next is not ready for broad public/HACS release yet. The 0.1 target is a
limited beta for known devices and careful testers:

- Verified local LAN support for `SP541E` monochrome controllers using the
  recovered SPNet/SPTech path.
- Old-UniLED-compatible BLE support where command/status parity is ported and
  audited.
- RG4/Zengge mesh as limited support where pairing and paired-node controls are
  proven.
- Other BanlanX APK catalog devices as recognized or diagnostic-only until
  packet formats are proven by source evidence, captures, or hardware.

The first release blocker, entity registry default enablement, is now
implemented and verified: every Home Assistant platform honors
`FeatureSpec.enabled_by_default` so planned diagnostics, per-output controls,
scene recalls, and research surfaces stay disabled for normal users. The LAN
startup discovery blocking-I/O risk is also fixed in code and covered by the
release gate; live log confirmation remains part of the final SP541E smoke
test. Command dispatch is serialized at the core session boundaries. A
read-only live HA boundary gate verifies required services/entities without
adding heavy Home Assistant test dependencies to the normal gate. Remaining 0.1
blockers are final SP541E live smoke testing and the post-smoke manifest
version bump. See the detailed [0.1 release plan](docs/RELEASE_0_1_PLAN.md).

This folder intentionally starts without copying the legacy UniLED
implementation. The plan is to rebuild the Home Assistant integration shell
around current Home Assistant APIs, then port protocol families from the
detached `../uniled` tree only when they have tests and device evidence.

Primary goals:

- Support every feasible device family present in the BanlanX 3.3.1 device catalog.
- Keep Home Assistant-facing code modern: `ConfigEntry.runtime_data`, current
  light color APIs, typed config entries, diagnostics, repairs, and test
  coverage.
- Support Bluetooth discovery and manual BLE-by-address setup so catalog BLE
  devices can still be configured when discovery does not fire.
- Use discovery as an evidence pipeline: collect BLE/LAN/mesh/manual
  candidates, score them against catalog and old-UniLED parity evidence, probe
  safely, then generate entities from parsed capabilities.
- Separate protocol engines from Home Assistant entity/platform code.
- Preserve compatibility with the eventual `uniled` domain where practical.

Design docs:

- [Feature Design Document](docs/FDD.md)
- [Technical Design Document](docs/TDD.md)
- [Implementation Status](docs/IMPLEMENTATION_STATUS.md)
- [Discovery And Configuration Approach](docs/DISCOVERY_CONFIGURATION.md)
- [0.1 Release Plan](docs/RELEASE_0_1_PLAN.md)
- [0.1 Beta Installation](docs/INSTALLATION_0_1.md)
- [0.1 Beta Release Notes](docs/RELEASE_NOTES_0_1.md)

Current state:

- Catalog, entity planning, legacy command builders, status parsers,
  notification framing, command sessions, initial BLE transport attachment,
  session-backed state refresh, runtime diagnostics, diagnostic sensors, an
  initial session-backed RGB light with disabled-by-default SP601/SP60x
  per-output lights, a coordinator-backed refresh button, and first
  session-backed number/select/switch command controls are implemented.
  Config-entry migration now normalizes legacy UniLED `ble`, `net`, and `zng`
  entries into the new BLE, LAN, and BLE-mesh schema using Home Assistant's
  current `async_update_entry` migration path. The config flow also exposes a
  current-API reconfigure step for repairing stored BLE addresses, LAN hosts,
  manual IDs, and RG4/Zengge local mesh metadata without changing protocol
  family or mesh identity. Invalid migration/setup entry data now creates a
  non-fixable Home Assistant repair issue with sanitized placeholders so users
  are directed toward reconfigure or remove-and-add instead of silent failure.
  Duplicate APK catalog names are preserved in runtime diagnostics as explicit
  variant records behind the canonical resolved name, so model-ID-specific
  behavior can be recovered later instead of being silently flattened.
  Direct-BLE models also expose BLE evidence diagnostics: proven command
  families report their known UUID profile, while unported BLE families keep
  APK plugin channels, Java BLE methods, and UUID candidates visible without
  enabling command writes.
  SP601E exposes two physical output lights, SP602E exposes four, and SP608E
  exposes eight, preserving old-UniLED model signatures. These controls include
  output-scoped SP601/SP60x effect selection, chip order, effect speed/length,
  and effect direction while the aggregate channel keeps old-UniLED's
  no-effect-list/no-chip-order behavior. SP601 aggregate light writes fan out
  to both outputs, and the old `uniled.set_state` service now keeps
  output-scoped controls from leaking through the aggregate light.
  SP6xx on/off animation,
  power-restore, play/pause, coexistence, light-type, and chip-order controls
  where supported. Old-UniLED chip-order command parity is wired for
  SP601/SP60x output channels and BanlanX2/BanlanX3 command-ready runtimes.
  Old-UniLED timer-count diagnostics are exposed for SP601/SP60x/BanlanX2
  status payloads, and BanlanX2 raw timer records are preserved as hex-encoded
  diagnostics only.
  BanlanX2/BanlanX3 RGB requests now preserve old-UniLED colorability behavior:
  non-colorable current effects are switched to `Solid Color` before the RGB
  payload, while old adjustable/colorable effects are left active. RGB writes
  without explicit brightness also reuse the current parsed color level rather
  than forcing full brightness. RGBW-capable V2/V3 models expose `rgb` plus
  `white`; brightness changes while already in `Solid White` use the
  family-specific white-level payload instead of the color brightness command,
  and direct `Solid White` effect selection mirrors the current white level in
  Home Assistant state. Parsed sound effects follow old UniLED's on/off-only
  HA surface by clearing brightness and preserving the raw color level as
  diagnostics until a later RGB/white write returns the light to a color mode.
  Parsed V2/V3 speed and V2 length are exposed only for dynamic states, so
  static, white, and sound statuses do not leak stale dynamic controls.
  BanlanX3 DIY effect type and color-count status bytes are exposed as
  diagnostic sensors, but DIY color editing remains hidden because old UniLED
  only left comment-level frame notes and the APK strings do not prove a safe
  local edit flow.
  SP52x/SP53x/SP54x
  custom 5xx models now use the same
  SP6xx-style BLE command/status frames with their APK-derived 3600-pixel
  catalog limits. SP6xx status parsing now keeps old-UniLED parity for static
  stored RGB bytes, dynamic/sound live RGB bytes, dynamic CCT bytes, and the
  custom/DIY slot byte exposed as a diagnostic `custom_effect_slot` sensor.
  SP6xx/custom 5xx light control also preserves old-UniLED sound-mode
  brightness behavior by suppressing `0x51` brightness frames in sound color
  and sound white modes and reporting brightness as full from parsed status;
  audio input and sensitivity are parsed only for powered sound statuses, with
  Home Assistant audio controls following that parsed availability, and
  effect-loop state is parsed only for dynamic and sound modes. SP6xx parsed
  speed, length, direction, and play/pause now also follow old-UniLED per-effect
  attributes instead of exposing raw bytes for effects that do not support
  those controls; the corresponding HA controls become unavailable for the
  current effect when the parsed field is unsupported. Effect, light-mode, and
  light-type select commands also clear stale optimistic effect-parameter state
  immediately when the newly selected effect no longer supports it.
  Non-sound white/CCT brightness uses the old `0x51` white selector byte
  instead of the color brightness selector. Dynamic and sound RGB tuning now
  stays brightness-free, matching old UniLED's `0x57` frame behavior, while
  static RGB/RGBW frames reuse the current brightness level unless HA supplies
  a new one. White requests now switch SP6xx-style controllers into the
  matching static, dynamic, or sound white mode before applying a white level;
  sound-white transitions keep the same no-`0x51` suppression. SP6xx light-mode
  selects now use the old coupled `0x53 <mode> <effect>` frame, reusing the
  current effect only when it is valid for the target mode and waiting for
  parsed `light_type` before exposing available options on dynamic-light-type
  models.
  APK strings and assets show the SP630E DIY/favorite surface, but editing or
  saving custom slots remains hidden until those packet flows are proven.
  LAN-capable models now expose explicit LAN profile
  diagnostics from APK/catalog evidence, including network-info codes, payload
  limits, Bonsoir/Android NSD method names, the custom
  `com.spled.plugins/multicast_lock` channel, mDNS `224.0.0.251:5353`, raw
  datagram socket timeout/buffer hints, the universal
  `/device/universal/network/config` setup route, AP/STA Bluetooth/AP setup
  prompts, local-only/cloud-binding warnings, and pending command/discovery
  status.
  Custom 5xx LAN diagnostics now also preserve the SP541E-proven SPNet UDP
  discovery anchors: UDP `6454`, request `53704e65740000200000000002e0`,
  response prefix `53704e6574000021000000000001`, SP541E model byte `0x5c`
  at payload offset `3`, network MAC bytes at payload offsets `5..10`, and the
  `SP541E` response name. SP541E LAN control is implemented over TCP `8587`
  with the `SPTECH\0` frame envelope, 13-byte response header, chunked status
  parser, and brightness-only Home Assistant light surface for mono strips.
  Setup data and Home Assistant discovery can now create a verified SP541E LAN
  entry from that SPNet response plus the source host, using the MAC as the
  legacy-compatible bare config-entry unique ID when present. Direct read-only
  probes are expected to fail with a zero-byte response when another controller
  already owns the strip's TCP session; stop HA/the app before using the
  standalone probe.
  Targeted APK searches found Bonsoir argument keys and generic datagram socket
  plumbing for other LAN families, but no concrete DNS-SD service type,
  model-specific discovery response, or local LAN command frame for SP80x/FT001.
  `network_info` diagnostic sensors now show live runtime network data when
  present, otherwise the APK/catalog query code such as
  `supportGetNetInfo=9; command_protocol_pending`.
  Optional-cloud models now
  expose a separate BanlanX cloud profile diagnostic from APK `libapp.so`
  strings, including `app.ledhue.com` API bases, account auth/lifecycle routes
  such as `/auth/refresh-token`, `/auth/signIn2`, `/auth/signUp2`, and
  `/user/sign-out`, `/home/device/auth/*`, `/home/device` lifecycle routes,
  `/user/device/post/raw`,
  `/user/device/connection/cloud/check`, `/user/local-device` registration,
  `/user/btmesh` metadata, manual/resource routes, Alexa account-linking paths,
  `document.ledhue.com` privacy/agreement/FAQ URLs, and auth-token string hints
  such as `user:token`, `user:refresh_token`, and `refreshToken2`. It also
  separates the 9 endpoint groups, the one command-adjacent endpoint, unresolved
  base/auth bindings, and token/header/signature request-contract hints. That
  profile is diagnostics-only until BanlanX auth, headers, token refresh semantics,
  region routing, device lifecycle, and cloud command envelopes are proven;
  support disposition reports the same five blockers as the cloud profile:
  `account_token_schema_pending`, `request_signing_headers_pending`,
  `region_reauth_contract_pending`, `raw_command_json_envelope_pending`, and
  `device_bind_ownership_lifecycle_pending`.
  SP801E/SP802E now
  also expose APK-derived network-controller profile diagnostics: SP801E maps to the
  `packages/module_sp801e` Art-Net/port/content-creation surface, while SP802E
  maps to the `packages/sp802e` LFX editor with 20 regular LFX effect icons,
  30 GIF previews, and settings route hints. These profiles now preserve
  native method anchors such as
  `getNetworkInfo`, `getArtNetConfig`, `setArtNetConfig`, playlist methods,
  `setLfxMode`, and `setLedPanelLayout`, plus `libwled_lfx.so` LFX/matrix
  symbols, raw SP801E channel/port/playlist labels, raw SP802E LFX/matrix/Wi-Fi
  labels, explicit packet-gap notes, `network_command_blocker_count=7`, and
  support flags for pending discovery/socket, Art-Net/playlist/DXF,
  panel-layout, LFX/status, and matrix-music packet work. The manual
  config flow can now create LAN-host entries for LAN-capable models while
  rejecting BLE-only LAN setup, and runtime setup attaches a diagnostic LAN
  transport holder without sending bytes until packet frames are proven.
  RG4/Zengge-style BLE mesh profile diagnostics now retain old UniLED Telink
  UUIDs, pairing requirements, manufacturer-data
  discovery identity, and
  effect names. The old Telink/Zengge packet crypto, command builders,
  decrypted notification parsers, a core mesh-session scaffold, a tested
  pair/status/command transport contract, and the initial Home Assistant
  Zengge BLE mesh transport class are ported. Mesh diagnostics now record the
  ported command names and the `0xED` effect packet's effect/speed/level
  fields; paired command nodes also expose guarded effect speed and effect
  level number controls that resend the current effect with the edited byte.
  RG4 node-role metadata is exposed both as a compact `mesh_role` diagnostic
  and as structured known/command/panel/bridge node diagnostics.
  RG4 support disposition now names the remaining mesh-control blockers and
  exposes `mesh_control_blocker_count=4`.
  Runtime setup can now attach a
  Zengge mesh connection for RG4 BLE-mesh entries without using the normal
  BanlanX byte-session path. The first refresh can pair using default or custom
  mesh credentials and send the old-UniLED status notification kick, with
  failures kept as diagnostics. Paired known nodes can now appear as Home
  Assistant light entities backed by guarded node-targeted power, brightness,
  RGB, Kelvin CCT, warm-white, and effect commands plus paired-node effect,
  effect-speed, and effect-level controls while preserving old UniLED packet
  vectors, so `RG4`/Zengge mesh is
  cataloged as limited support rather than only recognized. The `mesh_role`
  diagnostic now reports pairing/transport state plus command-node, panel-node,
  and bridge presence from known mesh metadata, and known RGB/CCT panel nodes
  get diagnostic status sensors without enabling non-light commands. Old UniLED
  MagicHue
  cloud mesh import is now captured too:
  the config flow can optionally fetch mesh credentials, LTK, place IDs/names,
  node IDs, node type, node wiring, names, and areas for Bluetooth-discovered
  or manually entered RG4 meshes, and the options flow can refresh the same
  metadata for existing mesh entries without storing MagicHue login
  credentials. Manual RG4 setup accepts a BLE address, mesh UUID, and optional
  node ID/type/wiring when cloud import is not used. SP6xx-style lights expose
  RGBW, RGBWW, white, and Kelvin color temperature behavior when the parsed
  light type supports it. Car-light models now expose APK-derived profile
  diagnostics for zones, trigger animations, route hints, catalog flags, setup
  requirements, and accessory roles: `SP701E` as interior controller,
  `SP702E` as chassis controller, and `SP-MIC` as a wireless microphone
  accessory that requires the chassis controller. The structured setup role
  metadata keeps `SP701E` before `SP702E`, places `SP-MIC` after `SP702E`,
  and now exposes a four-row setup dependency inventory without enabling
  commands. It also preserves the APK primary-controller
  `Ignore` prompt, raw `isPrimary`/`subUni` setup keys, microphone permission
  requirement, secondary-device power-loss warning, and fast-flashing white
  installation-area prompt, plus raw subdevice, password entry/change/policy
  and reset, and
  `sp_trigger` storage labels as diagnostics. Support disposition now names
  pending BLE opcode, status parser, zone command, trigger packet, subdevice
  binding, password flow, and SP-MIC event-packet work before any car-light
  command entities are exposed.
  SP801E/SP802E now expose
  APK-derived network-controller diagnostics for Art-Net, port/playlist
  workflow hints, DXF import limits, SP802E's regular LFX effect names,
  30 GIF LFX preview assets, SP802E native LFX parameter, effect-generator,
  matrix/mode, and pixel-helper anchors, per-model catalog/transport flags,
  and explicit LAN/Art-Net/LFX packet gaps plus support-disposition blockers.
  FT001 now exposes APK-derived fish-tank profile diagnostics for two
  light-channel labels, exact native
  settings/rename/timer/favorite route hints, workflow/effect hints,
  four favorite slots derived from `FavoriteStore/Recall/Clear0-3`,
  favorite-loop labels (`Loop all favorite effects`,
  `Stop looping the favorite effects`, `NextFavoriteChannel`),
  timer-count/exact `You can only add up to 5 timers!` native limit text,
  favorite-effect service/storage
  anchors, shared app setter names, raw effect/timer/brightness string hints
  (`timerConfig`, `raw-brightness-`, `whiteBrightness`, `white_brightness`),
  raw effect string anchors (`waterdrop`, `Flowing Water`, `Spring Water2`,
  `Stromend Water`), the `FishTankLights:fw_prompted_` firmware-prompt key,
  and visible control surfaces such as color palette, color correction,
  brightness, speed,
  windmill, timers, favorites, settings, device rename, and network
  configuration. FT001 remains diagnostics-only because the APK strings do not
  recover a verified BLE opcode table, notification parser, or LAN refresh
  packet; support disposition now names pending BLE opcode, status parser, LAN
  refresh, timer, favorite, effect, and brightness-parser work, with
  `fish_tank_command_blocker_count=7`. Old-UniLED scene recall parity is now
  wired for SP601/SP60x devices
  as nine disabled-by-default Home Assistant scene entities, using the proven
  `AA 2E 01 <slot>` and `88 8E 01 <slot>` recall packets for 0-based slots
  0 through 8. SP601/SP60x status tails also preserve raw timer records and
  SP60x trigger records in hex-encoded diagnostics, but timer/trigger editing
  is intentionally not implemented because those record schemas and write flows
  are not proven. Scene save/editing is also intentionally not implemented
  because the legacy methods were stubs and the APK scene UI protocol is a
  separate, richer surface. Scene UI and scene mesh models now expose APK-derived
  diagnostics for the shared `packages/scene_ui` surface, five preset scene
  folders, visible scene/timer/favorite/color/music/mic control surfaces, route
  hints, LFX creation routes, `setLfx*` app method anchors,
  recent-scene/favorite storage anchors, raw timing-task and white-brightness
  string hints, per-model catalog/transport hints, the SP31XE/SP32XE firmware
  note for one-touch provisioning, the exact scene-mesh 90-second
  provisioning timeout and provisioning-control warning,
  `libscene_lfx.so` IC/PWM handler anchors, the derived 16 paired IC/PWM API
  capabilities, four IC-only API capabilities, loop handlers, frame/opcode/state
  helpers, color-order and LED-type anchors, PWM tables, music/effect routines,
  PWM driver/write helpers, audited animation/self-test and drive-type native
  exports, and all 80 recovered scene mode-effect names as planned disabled
  options. Runtime support disposition now also names the seven shared
  scene command blockers, tracked by `scene_command_blocker_count=7`. Scene
  models remain diagnostics-only until the BLE and BLE-mesh command/status
  packet formats are mapped.
- LAN state refresh, scene effect modeling, per-output entities beyond proven
  SP601/SP60x channel commands, custom 5xx LAN/provisioning behavior,
  car-light and fish-tank command behavior, and hardware validation across
  every wiring type are still under construction.

Useful local references:

- Detached legacy source: `../uniled`
- Production gate: `python .\scripts\quality_gate.py`
- Manual install package: `python .\scripts\build_package.py`
