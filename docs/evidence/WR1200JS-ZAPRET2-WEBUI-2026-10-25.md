# WR1200JS Zapret2 WebUI — 2026-10-25

## Scope

The Zapret2 control is integrated into Padavan Classic **Administration →
Services**. It uses the existing NVRAM, file-storage, notification and service
lifecycle paths. The router was not flashed or rebooted.

## Prepared path

- `zapret2_enable` — saved runtime switch, default `0`;
- `scripts.zapret2.args` — root-managed strategy arguments stored as
  `/etc/storage/zapret2.args`;
- `APP_ZAPRET2` — compile guard derived from
  `CONFIG_FIRMWARE_INCLUDE_ZAPRET2=y`;
- event bit 56 — unique `restart_zapret2` notification;
- rc lifecycle — start at boot only when enabled, stop at shutdown, restart on
  Apply;
- HTTP status — requested setting, process, strategy file and WAN-specific
  NFQUEUE hook are returned separately;
- page — factory-off toggle, strategy editor, manual refresh, 30-second visible
  refresh and 45-second stale-state expiry;
- dictionaries — EN, UK and RU labels for every state.

The Apply handler refuses an enabled switch with an empty strategy. This mirrors
the service-side check, so a checkbox alone cannot report a successful launch.

## Verification

The transformer was executed against the pinned Padavan source commit
`c25283e915a2a00a763774dd255b14aff997285e`. The repository check then reported:

```text
PASS Zapret2 WebUI transformation and emitted script
```

The same prepared tree subsequently accepted the existing DNS, iPerf3, SSH,
Cron and LLTD/ASUS status transforms without anchor conflicts. The emitted
browser block passed `node --check`.

Additional checks cover:

- exact event-bit uniqueness;
- NVRAM key, file field and event descriptor;
- factory-off default;
- compiled-found-app query and restart dispatch markers;
- page toggle, strategy editor, observed-state row and interval refresh;
- all three localized status vocabularies.

## Evidence boundary

This proves source transformation and host script syntax. It does not prove:

- a successful final firmware build;
- that the page renders correctly in a physical browser;
- that enabling starts `nfqws2` on the router;
- that a strategy bypasses any provider;
- that routing, WAN health, tunnel access or reboot persistence remain intact.

Final image and separately authorized device runtime checks remain required.
