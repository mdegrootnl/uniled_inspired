# UniLED Next scripts

Use this folder for catalog extraction, support-matrix generation, fixture helpers,
and local APK reverse-engineering helpers.

## Quality Gate

`quality_gate.py` runs the local readiness checks that should pass before
deploying or packaging UniLED Next:

```powershell
python .\scripts\quality_gate.py
```

The gate validates `manifest.json`, translation coverage for config-flow and
repair keys, `services.yaml` coverage for the legacy `set_state` service,
checks config-flow discovery ordering so old-UniLED-compatible duplicate IDs are
blocked before entry creation, catalog-only Bluetooth confirmation is checked
before Bluetooth discovery can create an entry, delayed Bluetooth confirmation
and RG4/Zengge cloud-import entry creation recheck duplicate IDs, checks that
no image/logo assets are bundled, verifies the manual-install package file
list, checks that
`docs/SUPPORT_MATRIX.md` is freshly generated, proves every user-facing
catalog BLE/BLE-mesh model name and all old-UniLED BLE names can still wake the
Home Assistant Bluetooth manifest, runs the old-UniLED parity audit, runs the
APK evidence audit when local analysis artifacts are present, then runs
repo-wide Ruff and pytest. Use `--skip-apk-audit`, `--skip-ruff`, or
`--skip-pytest` only for targeted debugging; the full gate is the
production-readiness baseline.

## Manual Package

`build_package.py` creates a manual-install zip containing only the Home
Assistant custom-component files under `custom_components/uniled`:

```powershell
python .\scripts\build_package.py
python .\scripts\build_package.py --list
```

The package builder pins the Home Assistant entry points, forwarded platform
modules, translations/services files, and generated catalog data while excluding
caches, bytecode, local test artifacts, and image/logo file types. This keeps
APK/BanlanX/SPLED/old-UniLED image evidence as strings in diagnostics and audits
rather than bundled assets.

## Support Matrix

`generate_support_matrix.py` creates a catalog-wide support and evidence matrix
from the bundled APK catalog plus runtime support-disposition logic:

```powershell
python .\scripts\generate_support_matrix.py --format markdown --output .\docs\SUPPORT_MATRIX.md
python .\scripts\generate_support_matrix.py --format json
python .\scripts\generate_support_matrix.py --format csv
```

Run this when changing catalog family assignment, support levels, transport
mapping, legacy parity markers, profile/evidence hooks, or runtime support
disposition text. The checked-in `docs/SUPPORT_MATRIX.md` is generated from
this script and covered by tests so it stays in sync with the current catalog.
The summary intentionally separates raw APK records from canonical user-facing
setup rows, because duplicate display names collapse behind one runtime model
while their model-ID variants remain visible in diagnostics.
It also emits an open support blocker/requirement summary from
`support_disposition` tokens ending in `_pending`, tokens ending in
`_required`, and explicit accessory dependencies. Treat that summary as the
generated backlog for closing diagnostic-only families, LAN/cloud gaps,
BLE-mesh routing gaps, and accessory requirements.

## Legacy UniLED Audit

`audit_legacy_uniled.py` verifies the detached old UniLED checkout against the
new BanlanX APK catalog and parity profiles:

```powershell
python .\scripts\audit_legacy_uniled.py --legacy-root ..\uniled
```

The audit statically derives the old BLE and NET model names, proves the APK
overlap matches `legacy_uniled_supported` catalog flags, and verifies that
`SP107E` and `SP110E` exist only as separate `/legacy/uniled/...` catalog rows.
It also verifies every explicit and inferred old direct-BLE config-entry shape
migrates to a normalized UniLED Next BLE entry for the same model, model ID,
and address, and that old Zengge mesh entries preserve `zng_mesh_<uuid>`
identity while dropping old stored cloud credentials.
It also extracts the seven old BLE `build_*` command surfaces and checks that
every non-stub old command builder is covered by the ported parity profiles.
Empty old stubs such as SP601E/SP60x `scene_save` remain explicit stubs, old
SP6xx effect selection is treated as covered by the current mode/effect
`light_mode` encoder, and SP107E/SP110E are covered by limited LED Chord/LED
Hue parity profiles with hidden config/edit surfaces tracked as gaps.
The audit also checks old entity unique-ID anchors and current compatibility
outputs for raw-address BLE entries, SP601/SP60x master/output entity shapes,
the old RG4/Zengge `zng_mesh_<uuid>` base identity, and RG4/Zengge
`node_<id>` mesh entity shapes so upgrade identity regressions fail the release
gate.
It also validates that every old-UniLED BLE model name still wakes the Home
Assistant Bluetooth manifest and resolves through exact-name and safe-suffix
discovery as a `protocol_proven` BLE setup entry that does not require the
catalog-only confirmation form and reports the raw-address old-UniLED
config-entry IDs that must block duplicate setup. Unsafe no-separator near
misses such as `SP601EX` must stay unknown even if a broad Home Assistant
matcher woke the flow.
When the old Zengge mesh source is present, the same check verifies RG4
exact-name discovery and generic Telink manufacturer-data discovery, including
the old `zng_mesh_<uuid>` setup identity, as protocol-proven mesh setup entries
that do not require confirmation.

## APK Evidence Audit

`audit_apk_evidence.py` verifies checked-in APK evidence ledgers against the
local BanlanX reverse-engineering analysis artifacts. It compares full package
asset counts from `asset_package_counts.txt`, confirms every curated
high-signal evidence path still exists in the matching `assets_*.txt` file,
checks curated raw APK/native string anchors such as routes, app methods,
storage keys, callback names, and native handler symbols, and checks
the exhaustive asset-package classification in `core/apk_assets.py` plus
non-catalog feature-package profiles from `core/feature_packages.py`, such as
`packages/gundam_lights` being present in assets/routes but absent from the
generated model catalog:

```powershell
python .\scripts\audit_apk_evidence.py --analysis-dir ..\.codex\rev\BanlanX_3.3.1-analysis
python .\scripts\audit_apk_evidence.py `
  --analysis-dir ..\.codex\rev\BanlanX_3.3.1-analysis `
  --scene-native-lib ..\.codex\rev\BanlanX_3.3.1-extracted\config.armeabi_v7a-apk\lib\armeabi-v7a\libscene_lfx.so
python .\scripts\audit_apk_evidence.py `
  --analysis-dir ..\.codex\rev\BanlanX_3.3.1-analysis `
  --sp802e-native-lib ..\.codex\rev\BanlanX_3.3.1-extracted\config.armeabi_v7a-apk\lib\armeabi-v7a\libwled_lfx.so
python .\scripts\audit_apk_evidence.py `
  --analysis-dir ..\.codex\rev\BanlanX_3.3.1-analysis `
  --sp630e-native-lib ..\.codex\rev\BanlanX_3.3.1-extracted\config.armeabi_v7a-apk\lib\armeabi-v7a\liblfx.so
```

Run this whenever changing APK package counts or curated evidence lists for
SP630E/SP6xx, scene UI, SP801E, SP802E, car-light, fish-tank, RG4/accessory,
or cloud profiles, when changing curated raw string anchors, when classifying
new asset buckets from an APK refresh, when changing scene native paired/API
handler, state-export, animation-export, or drive-export constants, when
changing SP802E native LFX export constants, when changing SP630E/shared
`liblfx.so` export constants, or when
revisiting catalog-absent feature packages like Gundam
lights. When local extracted APK artifacts include `libscene_lfx.so` or
`libwled_lfx.so` or `liblfx.so`, or when the matching native-library override
is provided, the audit also checks `.dynsym` export counts plus the exact
scene/SP802E/SP630E native symbols used by the integration. A passing audit
proves that the constants
match the local APK analysis ledger and audited native exports; it does not
prove command packets, discovery frames, catalog-device presence, or status
parser offsets. For optional-cloud evidence, the audit checks both the grouped
endpoint inventory and the token/header/signature request-contract hints,
including the `S-*` header anchors recovered from `libapp.so`; these remain
evidence only until the concrete cloud request contract is proven.
Only literal APK/native strings belong in the audited anchor list; explanatory
documentation and translated UI summaries should stay out of the pass/fail
audit. For cloud profiles, the audited anchors cover literal base URLs,
account auth/lifecycle routes such as `/auth/refresh-token`, `/auth/sign-in`,
`/auth/signIn2`, `/auth/signUp2`, `/user/sign-out`, and password-token routes,
`/home/device/auth/*`, mixed `/home/device/*` and `/user/device/*` endpoints,
document URLs, Alexa links, and token/storage strings; they do not prove the
BanlanX account token schema, required headers/signing, region routing, or
`/user/device/post/raw` command envelopes. The structured BanlanX cloud
endpoint inventory is backed by this same audited literal string set and must
keep method, auth, and base URL binding unresolved until a stronger APK or
traffic-capture source proves the request contract.
For BLE profiles, the audited anchors cover the normalized UUID inventory's
raw APK rows for `ff12`, `ff14`, `ff15`, `ffe0`, and `ffe1`, including the
extractor's exact trailing `2` strings and short-name anchors. Those anchors
prove the UUID candidates exist in the APK, not their scene/car/fish/SP802E
service/characteristic roles.

## ELF Exports

`inspect_elf_exports.py` inspects `.dynsym` and `.symtab` without requiring
`readelf` or `objdump`. Use `--details` when native library research needs
symbol addresses and byte sizes, and add `--bytes` when a symbol body needs a
stable section/file-offset/SHA-256 anchor:

```powershell
python .\scripts\inspect_elf_exports.py `
  ..\.codex\rev\BanlanX_3.3.1-extracted\config.armeabi_v7a-apk\lib\armeabi-v7a\libscene_lfx.so `
  --table dynsym --contains Handler --details --bytes --sort size --min-size 1
```

The detailed values are research anchors only. They do not prove a BLE/LAN
command envelope, opcode table, or notification parser by themselves.

## Direct Test Runner

`run_direct_tests.py` runs the current no-argument unit tests without requiring
`pytest`. Use it as a local fallback in stripped-down shells, and still prefer
`pytest` once the Home Assistant test dependencies are installed:

```powershell
python .\scripts\run_direct_tests.py
```

The runner intentionally fails on fixture-parameterized tests so the suite does
not silently skip pytest-only coverage.

## Live Home Assistant Boundary Gate

`ha_live_boundary_gate.py` runs optional read-only checks against a real Home
Assistant instance without requiring the full Home Assistant pytest dependency
stack:

```powershell
python .\scripts\ha_live_boundary_gate.py `
  --session-file C:\path\to\ha-sessions.json `
  --require-service uniled.set_state `
  --entity light.raam_strip
```

The script can also read `UNILED_HA_URL`, `UNILED_HA_ACCESS_TOKEN`,
`UNILED_HA_REFRESH_TOKEN`, and `UNILED_HA_CLIENT_ID` from the environment. It
refreshes tokens when needed, but only prints a sanitized pass/fail summary.
Use this as the 0.1 HA-boundary gate when local
`pytest-homeassistant-custom-component` dependencies are unavailable or too
heavy for the normal release gate.

## Home Assistant Registry Audit

`audit_ha_uniled_registry.py` checks copied Home Assistant `.storage` registry
files for stale UniLED device-registry rows after identity migrations:

```powershell
python .\scripts\audit_ha_uniled_registry.py --storage-dir C:\path\to\.storage
```

The audit compares UniLED config-entry `unique_id`/normalized setup identity
against device-registry identifiers and refuses to mark a row stale if any
entity-registry entry still points at it. Use `--fail-on-stale` in local
diagnostics when you want a non-zero exit if safe cleanup candidates exist.
This script reports candidates only; it does not mutate Home Assistant
storage.

## SPTech LAN Probe

`probe_sptech_lan.py` performs read-only SP541E SPTech TCP status probes using
the same parser and transport assumptions as the Home Assistant integration:

```powershell
python .\scripts\probe_sptech_lan.py --timeout 6
python .\scripts\probe_sptech_lan.py --host 192.0.2.55
```

Run it only when Home Assistant and the official app are disconnected from the
target strip. The local SP541E controllers allow only one useful TCP session at
a time; a zero-byte response usually means another controller owns the socket.
