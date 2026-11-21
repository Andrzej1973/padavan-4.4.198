# WR1200JS handoff to Sol — 2026-10-25

## Role transfer

The owner explicitly requested that all completed work be recorded and that Sol
receive the single-writer role. Sol must first finish IoT and only then verify
the Zapret2 and Modern WebUI work.

This document transfers the role record; it does not prove that a live Sol
account has connected or accepted it. Until Sol records acceptance, no
parallel writer should edit this checkout.

## Repository state

- Branch: `codex/wr1200js-service-webui`
- Firmware-code HEAD being handed off:
  `28b0faf3c6b463d02f273f9f627b192406ac7f91`; the documentation-only handoff
  commit follows it without changing firmware inputs
- `origin/main`: `d1dc0ebaf82af316ad8ba65a01952c229c69e919`
- PR: https://github.com/Andrzej1973/padavan-4.4.198/pull/2 — open,
  mergeable, checks initially unstable.
- Before this handoff, the working tree contained 32 modified tracked files and
  147 untracked entries from IoT and earlier work. They were preserved.

## Zapret2 work

### Source and package

- Pinned upstream commit:
  `4a33055448ce5f4e7acc704e1fbe0d8a8a6aa08d`; verifier covers 253 files and
  2,516,830 bytes.
- Three signed netfilter archives total 927,491 bytes.
- `nfqws2` candidate is 665,004 bytes, MIPS32 and dynamically needs only
  `libc.so.0`.
- The WR1200JS selector is enabled:
  `CONFIG_FIRMWARE_INCLUDE_ZAPRET2=y`.

Build #574 (run `40182780081`, head `31a8f3e`) succeeded, but its ROMFS contained
only `/usr/sbin/nfqws2`; service, Lua assets and WebUI were not yet present.

### Runtime wrapper

`/usr/sbin/zapret2` now provides `start`, `stop`, `restart`, `status` and
`rules`:

- dedicated `ZAPRET2` mangle chain, queue 200;
- `--queue-bypass` for fail-open traffic;
- no `LOG` rule and daemon output redirected away from logs;
- private/loopback destinations returned before queueing;
- WAN-only `POSTROUTING` hook and exact-PID ownership checks;
- strategy and Lua readiness checks;
- strategy size capped at 8192 bytes;
- silent handling of `/proc` exit races;
- boot start only from saved `zapret2_enable=1`, shutdown stop, and firewall/
  netfilter/WAN-firewall reapply.

Required files are `/usr/share/zapret2/zapret-lib.lua`,
`zapret-antidpi.lua`, `zapret-auto.lua` and the upstream MIT notice.

### Classic WebUI

The Services page contains:

- saved factory-off toggle `zapret2_enable`;
- `/etc/storage/zapret2.args` strategy editor;
- separate observed state for `nfqws2`, full TCP/UDP NFQUEUE rules and strategy;
- stale-observation expiry and manual/visible-page refresh;
- Apply validation that rejects an enabled service with an empty strategy;
- EN/UK/RU labels and a service-navigation link.

The state is deliberately not described as proof that bypass or routing works.

### Verification history

- Candidate run `40189818250` on `28b0faf` passed WebUI transformation,
  emitted JavaScript syntax, isolated C handler compilation, service lifecycle
  and candidate ELF checks.
- Build #582 (run `40186605211`) compiled the full firmware. Its only target
  false-check was the verifier's dictionary path (`www/dict/*` instead of
  merged `www/*.dict`).
- Build #583 (run `40187724843`) compiled again. Its only target false-check
  expected a stripped `restart_zapret2` symbol; stable HTTPD markers and
  per-marker diagnostics were corrected in `28b0faf`.
- Build #584 (run `40189820727`) was in progress at handoff on `28b0faf`.
  Sol must inspect/reuse it; do not dispatch a duplicate for the same commit.

No final image containing the complete service and WebUI has yet been accepted.
No TRX from that final image has been downloaded or independently verified.

## Modern WebUI work

- Six owner-supplied PNG references are preserved under
  `docs/design/reference/`; inventory, dimensions and SHA256 are verified.
- The preview now follows the reference two-column dashboard: Internet,
  2.4 GHz, 5 GHz and explicitly unverified IoT on the left; quick services on
  the right; system metrics below.
- Fourteen service tiles match selected build services and point to real Classic
  destinations. They do not execute services or contact the router.
- Desktop and 390×844 layouts have no horizontal overflow.
- Clicking Zapret2 opens the local Classic-unavailable explanation and names
  `Advanced_Services_Content.asp#zapret2_enable_on_of`.
- Production Modern integration remains unstarted and blocked by the project
  order until IoT is complete.

## Device state

The router was not flashed or rebooted. Read-only SSH helper run for `identity`
timed out at `192.168.20.1:22`; no remote command was confirmed to execute.
Zapret2 process/rules, tunnel preservation, traffic effect, reboot persistence
and management access remain runtime-unverified.

## Required next order for Sol

1. Read `AGENTS.md`, project handoff documents and this evidence file.
2. Check current Git/CI, preserve all existing working-tree changes, and record
   role acceptance in `docs/EXECUTION-ROLE.md`.
3. Continue and finish IoT first: checked open/close/reset ownership, recovery
   worker, lock ordering, registry/callback quiescence, PCI remove/probe unwind,
   adapter-release fence, production binding, target build and device tests.
4. After IoT, verify build #584 or its replacement, download and hash the final
   TRX, inspect ROMFS for `nfqws2`, service, Lua, license, page, dictionaries
   and HTTPD routes.
5. Only after separate owner authorization, perform bounded Zapret2 runtime and
   rollback tests with local/VPN recovery available.

Do not flash, reboot, or change ZeroTier without specific current permission.
