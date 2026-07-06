# UniLED Next Feature Design Document

Status: draft  
Target: ideal Home Assistant integration for the full BanlanX 3.3.1 device
catalog

## Purpose

UniLED Next should provide a modern Home Assistant integration for the complete
BanlanX/SPLED controller catalog, with local-first control, current Home
Assistant entity behavior, and a maintainable model system that can grow as new
devices appear.

The integration should feel boring in the best way: devices are discovered,
paired, named, controlled, diagnosed, and repaired through Home Assistant
without the user needing to know which protocol family a controller belongs to.

## Goals

- Support every user-facing device name in the BanlanX 3.3.1 device catalog,
  plus guarded autodiscovery for legacy-only old-UniLED devices that are absent
  from the APK.
- Recognize catalog placeholders and test-only entries without exposing them as
  usable Home Assistant devices.
- Prefer local control over BLE or LAN. Use cloud access only when a device has
  no confirmed local path and the user explicitly opts in.
- Present consistent Home Assistant entities across BLE, LAN, mesh, scene UI,
  car-light, fish-tank, and accessory families.
- Preserve useful behavior from the existing UniLED integration while replacing
  brittle Home Assistant-facing code with current APIs.
- Make unsupported or partially understood capabilities visible through
  diagnostics and repairs instead of failing silently.
- Keep model support data-driven so new aliases and sibling models do not need
  custom Python classes when their protocol behavior is shared.

## Non-Goals

- Recreate the vendor mobile UI.
- Require cloud credentials for locally controllable devices.
- Add native sidecars to the Home Assistant runtime.
- Treat a model name match as full support unless the protocol family and
  feature contract are implemented and tested.
- Expose placeholder entries such as `TEST` as real Home Assistant devices.

## Users

- Home Assistant users who own one or more BanlanX/SPLED LED controllers.
- Power users with multi-channel pixel controllers, scene-capable devices, or
  vehicle lighting kits.
- Maintainers who need to add catalog models and protocol families without
  risking regressions in existing devices.

## Device Scope

The target catalog contains 191 records and 153 unique names. The integration
must cover all user-facing names, currently 152 after filtering the explicit
`TEST` placeholder.

Support is organized by family rather than by one class per model.

| Family | Names | Expected path |
| --- | --- | --- |
| Legacy/simple BLE controllers | `SP601E`, `SP602E`, `SP603E`, `SP608E`, `SP611E`, `SP613E`, `SP614E`, `SP616E`, `SP617E`, `SP620E`, `SP621E`, `SP623E`, `SP624E`, `LED Strip`, `Light Bar`, `Wall Light` | BLE |
| Legacy-only old-UniLED BLE controllers | `SP107E`, `SP110E` | BLE autodiscovery, UUID diagnostics, limited LED Chord/LED Hue command/status support, disabled-by-default chip/segment config controls, and advanced SP107E matrix-column RGB service control now |
| SP63x/SP64x/SP65x BLE controllers | `360PhotoB`, `SP630E`, `SP631E`, `SP632E`, `SP633E`, `SP634E`, `SP635E`, `SP636E`, `SP637E`, `SP638E`, `SP639E`, `SP63AE`, `SP63BE`, `SP63CE`, `SP641E`, `SP642E`, `SP643E`, `SP644E`, `SP645E`, `SP646E`, `SP647E`, `SP648E`, `SP649E`, `SP64AE`, `SP64BE`, `SP64CE`, `SP651E`, `SP652E`, `SP653E`, `SP654E`, `SP655E`, `SP656E`, `SP657E`, `SP658E`, `SP659E`, `SP65AE`, `SP65BE`, `SP65CE` | BLE; `/sp630e` APK surface diagnostics now |
| SP52x/SP53x/SP54x custom controllers | `SP521E`, `SP522E`, `SP523E`, `SP524E`, `SP525E`, `SP526E`, `SP527E`, `SP528E`, `SP529E`, `SP52AE`, `SP52BE`, `SP52CE`, `SP530E`, `SP531E`, `SP532E`, `SP533E`, `SP534E`, `SP535E`, `SP536E`, `SP537E`, `SP538E`, `SP539E`, `SP53AE`, `SP53BE`, `SP53CE`, `SP540E`, `SP541E`, `SP542E`, `SP543E`, `SP544E`, `SP545E`, `SP546E`, `SP547E`, `SP548E`, `SP549E`, `SP54AE`, `SP54BE`, `SP54CE` | SP6xx-style BLE control now; `/sp630e` APK diagnostics now; SP541E SPTech LAN verified; LAN/provisioning still required for the rest |
| Scene UI BLE controllers | `DynamicBar`, `SP551E`, `SP552E`, `SP553E`, `SP554E`, `SP556E`, `SP557E`, `SP558E`, `SP559E`, `SP55BE`, `SP660E`, `SP661E`, `SP662E`, `SP663E`, `SP664E`, `SP665E`, `SP666E`, `SP667E`, `SP668E`, `SP669E`, `SP66AE`, `SP66BE`, `SP66CE`, `SP679E` | BLE; APK scene diagnostics and explicit envelope/status/LFX/timer/favorite/DIY/white-brightness blockers now, commands pending |
| Scene UI mesh controllers | `SP310E`, `SP311E`, `SP312E`, `SP313E`, `SP314E`, `SP315E`, `SP316E`, `SP317E`, `SP318E`, `SP319E`, `SP31AE`, `SP31BE`, `SP31CE`, `SP320E`, `SP321E`, `SP322E`, `SP323E`, `SP324E`, `SP325E`, `SP326E`, `SP327E`, `SP328E`, `SP329E`, `SP32AE`, `SP32BE`, `SP32CE` | BLE mesh; APK scene diagnostics, firmware setup note, and explicit envelope/status/LFX/timer/favorite/DIY/white-brightness blockers now, commands pending |
| Car lights and accessories | `Car Lights`, `SP701E`, `SP702E`, `SP-MIC` | BLE accessory group; APK setup/dependency inventory, animation/image, password entry/change/policy/reset diagnostics, and explicit BLE/status/zone/trigger/subdevice/password/SP-MIC blockers now, commands pending |
| Network/accessory controllers | `SP801E`, `SP802E` | LAN/BLE+LAN; APK Art-Net/LFX diagnostics now, commands pending |
| Fish-tank lighting | `FT001` | BLE, LAN, optional cloud; APK fish-tank profile with asset buckets, effect-string/favorite-loop/firmware-prompt metadata, favorite/timer metadata, raw effect/timer/brightness string hints, and explicit BLE/LAN/timer/favorite/effect/brightness blockers, packet evidence pending |
| BLE mesh remote/control | `RG4` | BLE mesh; limited paired-node light/effect-select/effect-speed/effect-level support after pairing, accessories/provisioning APK diagnostics and explicit remote-event/provisioning/group/node-lifecycle blockers now, non-light mesh controls pending |

## Support Levels

Every catalog name must resolve to one of these states:

- Full: discovery, setup, entities, state refresh, commands, diagnostics, unload,
  reload, and tests are implemented.
- Limited: discovery and safe basic control are implemented, but one or more
  advanced features are intentionally hidden until validated.
- Recognized: the model is identified, diagnostics explain the missing protocol
  work, and no unsafe command entities are exposed.
- Filtered: the catalog entry is known not to be a user-facing device and is
  excluded from setup.

The ideal final state is Full for all user-facing entries. Limited and
Recognized are acceptable only as intermediate release states.

## Feature Requirements

### Discovery And Setup

- Discover connectable BLE devices through Home Assistant Bluetooth.
- Identify RG4/Zengge BLE mesh devices from Telink manufacturer data when the
  advertised name is not a catalog model.
- Offer manual setup for LAN devices by host/IP when discovery is unavailable.
- Validate LAN host/IP setup before creating an entry and reject LAN setup for
  models that do not advertise LAN capability.
- Keep setup coverage catalog-wide: every user-facing APK model that advertises
  BLE, BLE mesh, or LAN must be able to create validated entry data for that
  local transport, with optional-cloud capability tracked separately.
- Prevent duplicate config entries by stable unique ID.
- Validate connectivity during setup before creating an entry whenever the
  transport supports it.
- Preserve the original device name but allow Home Assistant naming rules to
  take over after setup.
- Provide reconfigure flows for host changes, transport preference, and
  advanced polling/command timing.
- Provide reauthentication only for optional cloud-backed devices.

### Device Identity

- Use stable identifiers based on address, local device ID, or network MAC when
  available.
- Register a Home Assistant device for every controller and accessory that has
  independent availability or control.
- Keep child/accessory devices related to their parent where Home Assistant's
  device registry can represent that relationship.

### Light Control

- Expose `light` entities for each controllable output channel.
- Support on/off, brightness, RGB, RGBW, RGBWW, white-only, color temperature in
  Kelvin, and effect selection according to each model's capabilities.
- Use current Home Assistant color modes. Do not expose legacy mired-only color
  temperature behavior.
- Hide controls that a model cannot perform.
- Preserve multi-channel controllers as separate entities where channels can be
  controlled independently, plus a master entity only when the protocol supports
  safe whole-device control.
- For legacy SP601/SP60x controllers, expose output-specific effect,
  chip-order, speed, length, and direction controls only on physical output
  channels where old UniLED attached those features.

### Effects And Scenes

- Expose effect lists, speed, length, direction, palette, and music reactive
  options when a model supports them.
- Support scene save, scene recall, and scene playlist behavior for models that
  expose scene slots.
- Treat proven legacy scene recall separately from richer scene editing. SP601
  and SP60x expose recall-only Scene 1 through Scene 9 entities from old
  UniLED packet evidence; save/edit and playlist behavior require separate APK
  or device packet proof before exposure.
- For scene UI families, support local scene selection first, then richer scene
  editing after the protocol contract is proven.
- Keep advanced effect rendering local to Python unless a measured need for a
  helper tool appears.
- For BLE mesh devices, expose profile diagnostics before creating controls,
  because mesh pairing/session state is transport-specific and unsafe to fake.

### Pixel And Strip Configuration

- Expose LED chip type, color order, channel count, segment length, total pixel
  count, and light type as `select` or `number` entities only when the protocol
  supports reading and writing them.
- Enforce catalog maximums such as 1800, 2700, 3000, and 3600 pixel limits.
- Validate numeric values before sending commands.
- Provide repairs when stored configuration exceeds a model's known limit.

### Audio And Music Features

- Expose audio source, sensitivity, and music effect controls for devices that
  support them.
- Treat microphone-dependent behavior as local device behavior; Home Assistant
  should not request microphone access.
- Make audio controls unavailable when the hardware accessory or parent device
  is not present.

### Network Features

- Support local LAN setup and reconnect for SP52x/SP53x/SP54x families where
  LAN control is available.
- Support SP801E and SP802E as network/accessory controllers with manual host
  setup first and discovery later if a reliable discovery method is identified.
- Expose network information as diagnostic sensors when the device reports it.
- Expose a LAN profile diagnostic for every LAN-capable model, even before LAN
  command framing is implemented, so users and maintainers can see known
  network-info codes, payload limits, and pending discovery status.
- Keep cloud access off by default.
- Expose a BanlanX cloud profile diagnostic for every catalog model with
  optional cloud transport so users and maintainers can distinguish recovered
  APK endpoint evidence, unresolved request-contract bindings, and categorized
  token/header/signature hints from implemented cloud control.

### Diagnostics And Repairs

- Diagnostics must include sanitized model identity, selected protocol family,
  transport, advertised capabilities, entity plan, last command type, last state
  update age, and unavailable reason.
- Diagnostics must include a support disposition that names whether the model is
  command-ready, mesh-limited, or diagnostic-only and which packet evidence is
  still missing.
- LAN-capable diagnostics must distinguish APK/catalog facts from proven LAN
  command support.
- Optional-cloud diagnostics must distinguish BanlanX `app.ledhue.com` API
  evidence, auth/content/voice/document endpoint groups, split device endpoint
  buckets, document URL strings, and auth-token string hints from proven
  authentication, token refresh, region routing, and command-envelope support.
- BLE mesh diagnostics must distinguish old-UniLED protocol evidence from a
  command-ready core implementation.
- Diagnostics must not include credentials, precise location, Wi-Fi passwords,
  or raw secrets.
- Repairs must guide the user through unsupported model, stale address, host
  changed, optional cloud auth expired, and deprecated config migration cases.

### Availability

- A device should become unavailable when state cannot be refreshed within the
  configured timeout.
- BLE devices should recover when Home Assistant sees fresh advertisements.
- LAN devices should retry with backoff and avoid flooding the network.
- Accessory entities should reflect parent availability.

## Home Assistant Entity Model

| Entity type | Use |
| --- | --- |
| `light` | Primary channel control, master channel when supported |
| `select` | Effect, audio input, chip type, light type, color order, scene slot |
| `number` | Brightness-like tuning, speed, length, sensitivity, pixel count, segment length |
| `switch` | Effect loop, direction toggles, music mode toggles, optional feature toggles |
| `button` | Identify, refresh, save scene, restore defaults where safe |
| `sensor` | Firmware, model, protocol family, signal, network info, unavailable reason |
| `scene` | Saved device scenes when Home Assistant scene semantics fit |

## User Stories

- As a user, I can add a nearby BLE controller from Home Assistant discovery and
  immediately control the lights that the controller actually supports.
- As a user, I can add a LAN controller by host/IP and receive a clear error if
  the device cannot be reached.
- As a user with a multi-output controller, I can control each output channel
  independently without losing whole-device controls.
- As a user with scene-capable hardware, I can recall saved scenes and adjust
  basic effect parameters from Home Assistant.
- As a user with scene-capable hardware before command support lands, I can
  see the APK-derived scene profile, catalog limits, transport class, and
  command-protocol gap status clearly.
- As a user with SP801E/SP802E before command support lands, I can see
  Art-Net/LFX profile facts, transport class, import limits, and
  command-protocol gap status clearly.
- As a user with an optional-cloud model before cloud support lands, I can see
  the APK-derived BanlanX cloud hosts, account-auth/device-auth/device/voice
  route groups, unresolved base/auth endpoint bindings, document/help URLs,
  token/header/signature contract hints, and why cloud commands are still
  disabled.
- As a user with a car-light kit, I can see interior, chassis, microphone
  accessory, the SP-MIC -> SP702E controller dependency, setup-order/dependency
  inventory,
  animation/image asset coverage, password entry/change/policy/reset evidence,
  and
  missing-command-protocol status clearly.
- As a maintainer, I can add a new model alias by editing catalog data and tests
  when the protocol family is already known.
- As a maintainer, I can add a new protocol family without changing Home
  Assistant entities except through the shared feature contract.

## Acceptance Criteria

- Every user-facing catalog name resolves to a family and support level.
- Every Full model has at least one protocol fixture test and one catalog
  resolution test.
- Every family has at least one Home Assistant setup test.
- The integration uses typed config entry runtime data.
- Setup, unload, reload, and migration are covered by tests.
- Light entities set valid `supported_color_modes` and `color_mode`.
- Color temperature support uses Kelvin attributes.
- BLE discovery uses Home Assistant Bluetooth APIs and avoids broad false
  positive matching where stronger matchers exist.
- Diagnostics can be downloaded for any configured entry.
- Diagnostics for APK-profiled families distinguish full package asset counts,
  curated evidence counts, protocol gaps, and command readiness.
- Repairs exist for unsupported model, stale connection data, and migration
  issues.
- Cloud access is optional and never required for a locally controllable model.

## Open Product Decisions

- Whether optional cloud-backed devices should be included in the first public
  release or held until all local families are complete.
- Whether scene editing should be exposed as Home Assistant entities, services,
  or a separate advanced panel.
- Which BLE and BLE-mesh packets implement scene selection, recent scenes,
  favorites, timers, DIY LFX, and SP31x/SP32x provisioning/routing.
- Whether mesh remotes such as `RG4` should also create device triggers or
  non-light control/diagnostic entities alongside paired-node light entities.
- Whether `SP-MIC` should be an SP702E-owned accessory with sensors only, or an
  entity-bearing device when paired with car-light models.
- Which BLE packets implement car-light subdevice binding, password flow,
  trigger selection, and microphone accessory events.
- Which LAN or BLE packets implement SP801E Art-Net config, SP801E playlist
  editing, SP802E LFX control, panel layout, DXF import, and status refresh.
