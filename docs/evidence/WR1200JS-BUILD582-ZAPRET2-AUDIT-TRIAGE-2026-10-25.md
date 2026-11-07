# WR1200JS build #582 Zapret2 audit triage — 2026-10-25

## Build result

Run `40186605211`, source head
`598418b679983e597326fe8bb4dd05693161f9aa`, reached and completed the
`Build WR1200JS firmware` step successfully. The job later failed in
`Audit all shipped shell scripts with exact target BusyBox`.

The downstream image/ZeroTier upload failures were consequences of the missing
target-audit report, not separate root causes.

## Exact failing check

The uploaded `target-busybox-audit.json` had one false result:

```text
zapret2_webui_image = false
```

All of these related checks were true:

- `/usr/sbin/zapret2` present and accepted by target BusyBox syntax;
- `/usr/sbin/nfqws2` present with valid ELF dependency closure;
- all three pinned Lua files and MIT license matched expected SHA256;
- service fail-open/Lua-init markers present;
- page toggle, strategy field, observed-state row and refresh interval present;
- compiled HTTPD markers for feature query, status and restart present.

The observer reported `dict_files: []` because the verifier looked under
`www/dict/EN.dict`, while the built ROMFS merges dictionaries as `www/EN.dict`,
`www/UK.dict` and `www/RU.dict`.

## Correction

Commit `08b87c8` changes only the final-image dictionary paths. The correction
does not alter the shipped page/backend/service.

## Evidence boundary

Build #582 does not produce a release candidate because its final gate failed.
The compile success and partial target audit are useful evidence only. No router
flash, reboot, service start or Zapret2 traffic test was performed.
