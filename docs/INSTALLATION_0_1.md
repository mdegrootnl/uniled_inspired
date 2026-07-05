# UniLED Next 0.1 Beta Installation

UniLED Next 0.1 is a limited beta for careful testers. It is not a broad HACS
or public-stable release.

## Before Installing

- Back up Home Assistant.
- Keep a way to restore your current `custom_components/uniled` folder.
- Read `docs/RELEASE_NOTES_0_1.md` and `docs/SUPPORT_MATRIX.md`.
- For old UniLED users, keep the old integration disabled until you are ready
  to test migration behavior.

## Manual Package

Build the manual-install zip from this repository:

```powershell
python .\scripts\quality_gate.py
python .\scripts\build_package.py
```

The zip is written to `dist/uniled-next.zip`. It contains only
`custom_components/uniled` files needed by Home Assistant. It intentionally
does not include BanlanX/SPLED/old-UniLED logo or image assets.

## Install

1. Stop Home Assistant or use a file editor/add-on that can safely replace
   custom component files.
2. Copy the zip contents so Home Assistant has:
   `config/custom_components/uniled`.
3. Restart Home Assistant.
4. Open Settings > Devices & services.
5. Add or reload UniLED.
6. For SP541E LAN strips, prefer discovered entries when they appear. Manual
   LAN setup is the advanced fallback.

## Required Checks Before Tagging 0.1

Run the normal local release gate:

```powershell
python .\scripts\quality_gate.py
```

Run the optional live Home Assistant boundary gate when credentials are
available:

```powershell
python .\scripts\ha_live_boundary_gate.py `
  --session-file C:\path\to\ha-sessions.json `
  --require-service uniled.set_state `
  --require-service light.turn_on `
  --entity light.raam_strip
```

Run the registry audit against copied Home Assistant `.storage` files before
cleaning up stale old-UniLED device rows:

```powershell
python .\scripts\audit_ha_uniled_registry.py --storage-dir C:\path\to\.storage
```

## Troubleshooting

- If SP541E LAN discovery does not appear, use manual LAN setup with the known
  host and verify Home Assistant can reach TCP port `8587`.
- If a light is unavailable, close the vendor app and old integrations. SP541E
  controllers can behave like only one controller owns the useful TCP session.
- If many diagnostic entities exist, check that disabled entities stayed
  disabled by default in Home Assistant's entity registry.
- If Bluetooth discovery does not appear, use manual BLE-by-address setup for
  supported old-UniLED-compatible BLE devices.
- If RG4/Zengge mesh setup fails, verify mesh credentials and keep cloud import
  limited to RG4/Zengge mesh models.
