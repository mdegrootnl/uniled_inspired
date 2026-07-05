# UniLED Next 0.1 Release Plan

Target: a small, honest, production-quality Home Assistant beta for known-good
devices, not a broad claim that every BanlanX APK device is fully supported.

## Release Position

UniLED Next 0.1 should ship as a tester/early-adopter release for:

- Local `SP541E` LAN controllers using the verified SPNet/SPTech path.
- Old-UniLED-compatible BLE controllers where command/status parity is ported
  and audited.
- RG4/Zengge mesh as limited support where current pairing and paired-node
  controls are proven.
- APK catalog devices that are not protocol-proven as recognized,
  diagnostic-only entries.

It should not be marketed as a full replacement for every BanlanX/SPLED device
yet. The right public promise is: local-first, evidence-based, conservative
setup, strong migration/autodiscovery coverage for old UniLED devices, and
clear diagnostics for unsupported families.

## Current Evidence Baseline

The latest local release gate on 2026-07-05 reports:

- `python scripts\quality_gate.py`: 397 pytest tests passed.
- Legacy UniLED audit: 51 old BLE names, zero old NET names,
  `migration_mismatches=0`, `command_mismatches=0`,
  `autodiscovery_mismatches=0`, and `entity_identity_mismatches=0`.
- APK evidence audit passes against the local BanlanX 3.3.1 analysis artifacts.
- Support matrix totals: 152 canonical user-facing models, 95 limited,
  57 recognized, and 94 command-protocol-ready models.
- SP541E LAN path has live Home Assistant 2026.7 evidence for three local
  monochrome strips, including startup SPNet discovery, MAC identity,
  SPTech TCP control, state refresh, brightness/power service calls, and
  migration/dedupe behavior.
- Entity registry defaults are now wired from `FeatureSpec.enabled_by_default`
  into every Home Assistant platform, with focused tests proving SP541E main
  lights stay enabled while secondary SP601/SP60x surfaces stay disabled.
- SPNet startup discovery now resolves local IPv4 addresses through Home
  Assistant's executor boundary before deriving directed broadcast addresses,
  with direct-runner and pytest coverage proving the async discovery path does
  not call the synchronous address probe in the event loop.
- Command dispatch is serialized at the core session boundaries: direct BLE/LAN
  `DeviceSession` calls lock high-level payload groups and refresh waits, while
  Zengge mesh pair/status/command writes share a transport lock.
- A clearly named optional live HA boundary gate exists for 0.1 because the
  local `pytest-homeassistant-custom-component` dependency stack currently
  fails on Windows ARM64 native builds. The gate uses the HA HTTP API to verify
  services and required entities without printing tokens.
- The manual package builder writes `dist/uniled-next.zip` with 52 validated
  Home Assistant custom-component files and no image/logo assets. 0.1 beta
  install and release-note docs are linked from the README.
- A read-only/reversible HA API pre-smoke against the currently deployed
  integration on 2026-07-05 confirmed all three SP541E light entities can be
  turned on at brightness `77` and restored to their original `off` state.

## 0.1 Scope

### In Scope

- SP541E LAN:
  - Startup SPNet discovery.
  - Manual LAN setup.
  - MAC-backed stable identity and migration compatibility.
  - Power, brightness, state refresh, availability, reload/unload behavior.
  - Clear diagnostic provenance: source, match, confidence, LAN profile.
- Old-UniLED BLE parity:
  - Keep all old-UniLED BLE names discoverable through bounded HA Bluetooth
    matchers.
  - Preserve duplicate checks for old raw-address unique IDs.
  - Preserve migration coverage for old BLE and RG4/Zengge mesh shapes.
  - Keep old-UniLED-compatible command builders/parsers audited.
- Diagnostics-only APK catalog coverage:
  - Recognized models must remain addable only when setup is safe.
  - Do not enable command entities for families with unresolved packet
    blockers.
  - Keep support blockers visible in diagnostics and generated docs.
- Publication readiness:
  - README tells users exactly what is supported.
  - Release notes include known limitations.
  - Manual install package includes only the intended files.
  - No bundled BanlanX/SPLED/old-UniLED image or logo assets.

### Out Of Scope For 0.1

- Broad HACS/public-stable release.
- Complete support for every BanlanX APK device.
- BanlanX cloud login, signing, refresh, bind lifecycle, or raw command posts.
- Scene UI/scene mesh commands.
- Car-light commands, password/subdevice flows, and SP-MIC events.
- FT001 fish-tank commands, timers, favorites, and LAN refresh.
- SP801E/SP802E Art-Net/LFX command support.
- New packet guesses from APK strings without captures or hardware evidence.
- Large runtime module split, except for very low-risk extractions needed to
  land 0.1 safely.

## P0 Ship Blockers

These must be done before tagging 0.1.

Current estimate uses focused engineering weeks, assuming the local HA
environment and the three SP541E strips remain available for live validation.

| Slice | Status | Remaining Engineering Time |
| --- | --- | --- |
| Planner entity defaults | Done | 0 weeks |
| Thin HA integration test layer | Done for 0.1 via optional live gate | 0 weeks |
| Startup blocking-I/O removal | Done; live log check rolls into smoke | 0 weeks |
| Runtime command serialization | Done | 0 weeks |
| Final SP541E live smoke test | Partially pre-smoked; deploy/restart/log check open | 0.25-0.5 weeks |
| Publication metadata/docs/package polish | Mostly done; version bump waits for RC | 0.1-0.25 weeks |

P0 total remaining estimate: 0.35-0.75 engineering weeks. P1 tester polish
adds roughly 2.0-4.0 engineering weeks before a wider tester group. P2
fuller hardware/capture-driven family work is intentionally not bounded for
0.1.

### 1. Honor Planner Entity Defaults

Status: done in the current tree and verified by the 2026-07-05 quality gate.

Problem solved: `FeatureSpec.enabled_by_default` is asserted in the planner,
and HA entities now publish it through
`_attr_entity_registry_enabled_default`.

Why it matters: Some models plan large diagnostic/control surfaces. If HA
enables all of them, normal users get a noisy integration and disabled/planned
features become visible as if they were ready.

Implementation landed:

- Added a shared helper in `entity_metadata.py` that maps
  `FeatureSpec.enabled_by_default` to the HA entity registry default.
- Applied it in every HA entity class:
  - `sensor.py`
  - `light.py`
  - `number.py`
  - `select.py`
  - `switch.py`
  - `scene.py`
  - `button.py`
- Preserved explicitly enabled production surfaces, especially the main SP541E
  light and old-UniLED-compatible aggregate lights.
- Kept planned, diagnostic-heavy, per-output, scene recall, route-surface,
  setup-state, and research-helper entities disabled when the planner says so.

Acceptance criteria met:

- Tests prove at least one disabled planned diagnostic/control feature becomes
  `_attr_entity_registry_enabled_default=False`.
- Tests prove the SP541E main light remains enabled by default.
- Tests prove disabled-by-default SP601/SP60x output lights and scene recall
  entities remain disabled in HA entity objects.
- Quality gate passes.

### 2. Add A Thin HA Integration Test Layer

Status: done for 0.1 through a clearly named optional live HA boundary gate.
A fuller `pytest-homeassistant-custom-component` layer remains P1 because the
local dependency stack currently fails on Windows ARM64/Python native builds
before test code can run.

Problem addressed: most tests intentionally avoid Home Assistant imports. That
is good for protocol work, but 0.1 needs a small set of real HA boundary checks.

Implementation landed:

- Probed `pytest-homeassistant-custom-component`; it currently fails locally
  before tests run because Home Assistant dependencies build native packages
  such as `cryptography`/`orjson` on Windows ARM64.
- Added `scripts/ha_live_boundary_gate.py`, a pure-stdlib optional live gate
  that refreshes/uses HA API credentials without printing secrets.
- Added direct tests for the live-gate parser helpers.
- Ran the live gate read-only against Home Assistant `2026.7.0`, verifying:
  - `uniled.set_state`
  - `light.turn_on`
  - `light.raam_strip`
  - `light.muur_strip`
  - `light.midden_strip`
- Existing local tests continue to cover entity registry enabled defaults,
  diagnostics redaction, and config-flow duplicate/order invariants.

Acceptance criteria met for 0.1:

- A clearly named optional HA gate exists and has passed read-only against the
  target Home Assistant instance.
- The normal release gate remains fast and dependency-light.
- Docs state that this optional gate should pass before a release tag.

Deferred to P1:

- Full `pytest-homeassistant-custom-component` tests for config-flow happy path,
  entity registry defaults inside HA, diagnostics redaction inside HA,
  unload/reload lifecycle, and service registration once the dependency stack
  has a reliable local runner.

### 3. Remove Startup Blocking-I/O Risk

Status: code/test done in the current tree and verified by the 2026-07-05
quality gate. Live Home Assistant log confirmation remains part of the final
SP541E smoke test.

Problem solved: LAN broadcast-address discovery needs local address helpers
that call `socket.getaddrinfo` and a UDP connect probe. The async SPNet
discovery path now resolves those local addresses through an executor boundary
before deriving directed broadcast targets.

Implementation landed:

- Moved local IPv4 address discovery behind `hass.async_add_executor_job`, or
  precompute addresses outside the event loop.
- Kept SPNet datagram send/receive async.
- Added a direct-runner-compatible test proving startup discovery does not call the local
  synchronous address helper directly from the async path.

Acceptance criteria met or assigned:

- Quality gate and focused tests guard the executor boundary.
- Home Assistant restart logs must still be checked during the final SP541E
  smoke test before tagging 0.1.

### 4. Serialize Command Dispatch

Status: done in the current tree and verified by the 2026-07-05 quality gate.

Problem solved: LAN uses a transport lock, but BLE and mesh command paths also
need a shared core-level boundary because HA can call multiple entities
concurrently and many LED controllers behave poorly with overlapping writes.

Implementation landed:

- Added serialization at the `DeviceSession` command boundary so all
  command payload groups for a runtime are sent sequentially.
- Kept `DeviceSession.refresh_state()` under the same lock through direct
  response or notification wait handling so state queries and entity commands
  do not interleave.
- Added mesh command serialization where paired-node commands share a transport,
  covering pair, status, and command characteristic writes.

Acceptance criteria met:

- Tests prove concurrent light/select/number calls serialize transport writes.
- SP541E LAN behavior remains unchanged.
- BLE and mesh transports do not need to implement their own duplicate locks.

### 5. Final SP541E Live Smoke Test

Status: partially pre-smoked against the currently deployed integration. The
final release-candidate deployment, restart, and log review remain open because
the available SSH keys are denied and Samba requires credentials.

Implementation:

- Deploy the 0.1 candidate to Home Assistant.
- Restart HA.
- Confirm the three known SP541E strips load without setup errors.
- Confirm no SPNet discovery traceback and no catalog blocking-call warning.
- Reload one entry.
- Toggle power and brightness on all three strips and restore original state.
- Run `scripts/audit_ha_uniled_registry.py` and confirm stale old-UniLED device
  rows are only safe cleanup candidates.

Acceptance criteria:

- Smoke-test notes are added to `IMPLEMENTATION_STATUS.md` or release notes
  with date, HA version, and result.

Current live evidence:

- Home Assistant API access works reliably through `http://192.168.0.157:8123`.
  The `homeassistant.local` mDNS URL is intermittently slow for token refreshes
  from this Windows host.
- `core_ssh` and `a0d7b954_ssh` can be started through HA services, but
  `hassio.addon_stdin` returns HTTP 500 for both, and SSH public-key auth is
  denied for the available local keys.
- The currently deployed integration passed a reversible API smoke: captured
  `light.raam_strip`, `light.muur_strip`, and `light.midden_strip` as `off`,
  turned all three on at brightness `77`, observed all three report
  `on:77`, then restored all three to `off`.

## P1 Before Wider Tester Group

These are strongly recommended before inviting more users, but should not block
a private 0.1 candidate if P0 is done.

### Better User-Facing Setup

- Keep the current manual setup as an advanced path.
- Add or document transport-specific flows:
  - SP541E LAN discovered/manual host.
  - BLE discovered/manual address.
  - RG4/Zengge mesh advanced setup.
- Hide model IDs, mesh internals, cloud import, and raw device IDs unless the
  user chooses advanced setup.

### Publication Metadata

- Set `manifest.json` version to `0.1.0` only after the final live smoke test.
- Add codeowners before public distribution; keep this non-blocking for a
  private beta if no public repository path is chosen.
- Add repository/docs/issue links if the chosen distribution path supports
  them.
- Decide whether the `uniled` domain remains for migration compatibility or
  whether a future domain migration is required to avoid old branding.

### Docs For Testers

- The 0.1 beta install guide is in `docs/INSTALLATION_0_1.md`.
- The 0.1 beta release notes are in `docs/RELEASE_NOTES_0_1.md`.
- Add a fuller migration guide from old UniLED before a wider tester group.
- Add a troubleshooting guide:
  - BLE discovery does not appear.
  - SP541E LAN discovery does not appear.
  - Device unavailable because another controller owns the socket.
  - Too many disabled diagnostic entities.
  - How to collect logs/captures.

### Runtime Maintainability

`runtime.py` is now large enough to slow future family work. Do not block 0.1
on a large refactor, but stop adding major families until it is split.

Suggested post-0.1 modules:

- `runtime/diagnostics.py`
- `runtime/features.py`
- `runtime/light_state.py`
- `runtime/mesh.py`
- `runtime/support.py`

Acceptance criteria for the split:

- No behavior changes.
- Quality gate stays green after each extraction.
- New family work lands only after the relevant runtime area is isolated.

## P2 After 0.1

- Hardware/capture-driven work for scene UI, scene mesh, car lights, FT001,
  SP801E, SP802E, and non-SP541E LAN.
- BanlanX cloud only after auth, headers/signing, region routing, token
  refresh, bind lifecycle, and raw command envelopes are proven.
- HACS/public-stable packaging after more hardware reports and HA-boundary
  tests.
- Periodic LAN rediscovery only after startup SPNet behavior is boring and
  well-tested.

## 0.1 Release Checklist

1. P0 blockers complete.
2. `python scripts\quality_gate.py` passes.
3. Optional HA-boundary gate passes, if split from the normal gate.
4. Manual install package builds.
5. README has current release scope and known limitations.
6. Support matrix is regenerated and fresh.
7. SP541E live smoke test passes on Home Assistant.
8. No bundled image/logo assets.
9. `manifest.json` version is set to `0.1.0`.
10. Release notes call this a limited beta, not broad full support.

## Stop Rule

Do not spend more time on generic lifecycle polishing before 0.1 unless it is
connected to a failing test, HA warning, live SP541E behavior, entity noise, or
old-UniLED migration/autodiscovery parity.
