# UniLED Next 0.1 Beta Release Notes

UniLED Next 0.1 is a limited beta for known devices and careful testers.

## Supported In This Beta

- Verified SP541E LAN control for local monochrome strips using SPNet discovery
  and SPTech TCP commands.
- Old-UniLED-compatible BLE model discovery, migration identity, command
  builders, status parsers, and entity surfaces where parity is ported.
- Limited RG4/Zengge mesh support for paired known light nodes.
- Diagnostic-only setup for APK catalog families whose command packets are not
  proven yet.

## Important Limitations

- This is not a broad HACS/public-stable release.
- It does not fully support every BanlanX APK model.
- BanlanX cloud auth/control is diagnostic evidence only.
- Scene UI, car-light, fish-tank, SP801E/SP802E, and non-SP541E LAN command
  families remain blocked on packet evidence or hardware captures.
- The integration keeps the `uniled` domain for migration compatibility.
  Avoiding all old domain-level Home Assistant branding would require a future
  domain migration.
- Full `pytest-homeassistant-custom-component` coverage is deferred because the
  local Windows ARM64 dependency stack currently fails before tests run. The
  0.1 candidate uses the normal local quality gate plus the optional live HA
  boundary gate.

## Release Gate

The current local gate on 2026-07-05 reports `397 passed` plus:

- Ruff clean.
- Manifest, translation, service, config-flow ordering, package, and no-image
  asset checks.
- Fresh support matrix.
- Legacy UniLED parity audit with zero migration, command, autodiscovery, and
  entity-identity mismatches.
- APK evidence audit against the local BanlanX 3.3.1 analysis artifacts.

## Required Live Smoke Before Tagging

- Deploy the 0.1 candidate to Home Assistant.
- Restart Home Assistant.
- Confirm the three known SP541E strips load without setup errors.
- Confirm no SPNet discovery traceback and no blocking-call warning from UniLED.
- Reload one entry.
- Toggle power and brightness on all three strips, then restore original state.
- Run `scripts/audit_ha_uniled_registry.py` and confirm stale old-UniLED device
  rows are only safe cleanup candidates.

## Upgrade Notes

- Old UniLED BLE and RG4/Zengge identities are preserved where equivalent
  surfaces are proven.
- SP541E LAN entries use MAC-backed identity when SPNet discovery or migration
  provides a MAC address.
- Planned diagnostics, per-output controls, scene recalls, and research helpers
  are disabled by default in Home Assistant's entity registry.
