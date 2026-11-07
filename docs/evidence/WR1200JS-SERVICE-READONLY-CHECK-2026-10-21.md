# WR1200JS services: read-only device check — 2026-10-21

## Outcome

The first attempts were blocked by timeouts, but a later retry connected over
SSH and completed the requested read-only comparison. No router setting,
service, firmware, or network state was changed.

## Checks attempted

- Read-only SSH connection to `ASUS@192.168.20.1` on port 22, with batch mode,
  strict host-key checking, and a 10-second connection timeout. It timed out
  before authentication; no remote command ran.
- Read-only navigation to
  `http://192.168.20.1/Advanced_Services_Content.asp` in a separate hidden
  in-app browser tab. Browser navigation timed out before the page loaded.
- Retried on the next user request: SSH again timed out; a fresh browser-tab
  request returned `ERR_NETWORK_CHANGED` before loading the router page.
- On the following retry, SSH connected and the read-only commands below
  returned current NVRAM, process-list and installed-page source data.

## Current read-only observations

Version fields: `firmver=4.4.198.9`, `extendno=WR1200JS`, with `buildno` and
`productid` empty. This does not identify the exact firmware build number.

| Service | Saved flag | Process observation | Result |
|---|---:|---|---|
| KMS (`vlmcsd`) | `vlmcsd_enable=1` | `vlmcsd -A 30d -R 30d` present (PID 806) | Flag and process agree: enabled/running |
| LLTD | `lltd_enable=0` | no `lld2d` process shown | Flag and process agree: disabled/stopped |
| ASUS Info Discovery | `adsc_enable=0` | no `infosvr` process shown | Flag and process agree: disabled/stopped |

The installed `/www/Advanced_Services_Content.asp` contains service controls
and observed-state rows for KMS, LLTD and ASUS Info Discovery. The served
System navigation remains incomplete: Cron, Watchdog and Discovery link to the
same unanchored `/Advanced_Services_Content.asp`; the nav has no separate KMS
or ASUS Info Discovery link and does not target the service row anchors. The
page does include control anchors `vlmcsd_enable_on_of`, `lltd_enable_on_of`,
and `adsc_enable_on_of`, so direct row destinations could be used. This live
page therefore does not contain the navigation correction recorded in the
current source commit `2e73d22`; the empty build number prevents matching it to
an exact installed build.

## Historical evidence boundary

The earlier device snapshot in
`docs/runtime/WR1200JS-2026-10-18-SERVICE-NAV.md` recorded KMS and SSH processes
present, while iPerf3, Cron, LLTD and ASUS Info Discovery were disabled or
absent. That snapshot is from 2026-10-18 and must not be treated as current
state. The available `artifacts-410/romfs-selected` page also confirms only
that the older image contained KMS, LLTD, and ASUS discovery control anchors.

The local navigation source and verifier were updated earlier in this branch,
and its CI source gate passed. New image/browser verification remains pending:
builds #509–#511 failed later at the QEMU combined-dnsmasq test and have no
verified downloadable image. Details are in
`docs/evidence/WR1200JS-BUILD506-507-VPN-HOOK-2026-10-21.md`.

## Remaining checks

Verify the navigation correction in a newly built image and authenticated
browser. For any later status refresh, keep configured state distinct from
process presence. Do not apply settings, start or stop services, reboot, or
flash firmware during this audit.

## Fresh retry — 2026-10-21

The original address `192.168.20.1` timed out on SSH and the WebUI request did
not load. The device answered at `192.168.30.1`; SSH was allowed only after
using the already trusted host-key identity for `192.168.20.1`, which matched
the alternate address. This avoids treating an unverified SSH host as the
router. The WebUI request at the alternate address rejected the cached browser
credentials, so no authenticated visual page inspection was possible.

Fresh read-only SSH observations at `192.168.30.1`:

- Version fields: `firmver=4.4.198.9`, `extendno=WR1200JS`; `buildno` remains
  empty.
- `vlmcsd_enable=1`; `vlmcsd -A 30d -R 30d` is running (PID 806).
- `lltd_enable=0` and `adsc_enable=0`; neither `lld2d` nor `infosvr` is
  running.
- `crond_enable=0`; no `crond` process is present.
- `/sbin/watchdog` is running (PID 696). No saved `watchdog_enable` value was
  returned by the selected NVRAM-key query, so this check does not establish
  whether that process agrees with the UI setting.
- The installed page still has generic System navigation targets for Cron,
  Watchdog and Discovery, while the KMS, LLTD and ASUS Info controls have row
  anchors. Thus the installed navigation mismatch remains confirmed; exact
  build attribution is still unavailable because `buildno` is empty.

No router configuration, process, firmware, or network state was changed.

## Fresh retry — 2026-10-21 16:16 UTC

Both known router addresses were checked again using SSH batch mode, strict
host-key verification and a short connection timeout:

- `192.168.30.1`: TCP/SSH connection timed out.
- `192.168.20.1`: TCP/SSH connection timed out.

No remote shell command ran. The service flags and process list therefore were
not refreshed; the successful observations above remain historical. No router
configuration, process, firmware, or network state was changed. Firmware build
#513 was independently observed running at this time; it does not provide new
device-runtime evidence.

## Fresh SSH connection restored — 2026-10-21 16:18 UTC

SSH to `ASUS@192.168.20.1` succeeded with batch mode and strict host-key
checking. The commands below only read NVRAM, process/module/device-node state,
the served page, and matching current log entries.

| Service/setting | Saved value | Live observation | Read-only result |
|---|---:|---|---|
| KMS | `vlmcsd_enable=1` | `vlmcsd -A 30d -R 30d` present (PID 806) | Enabled and process present |
| LLTD | `lltd_enable=0` | no `lld2d` process | Disabled and process absent |
| ASUS Info Discovery | `adsc_enable=0` | no `infosvr` process | Disabled and process absent |
| Cron | `crond_enable=0` | no `crond` process | Disabled and process absent |
| CPU watchdog module | `watchdog_cpu=1` | no `rt_timer_wdg` in `/proc/modules`; no `/sys/module/rt_timer_wdg` evidence | Configured on, optional module absent |
| Built-in watchdog path | not the `watchdog_cpu` module flag | `/sbin/watchdog` PID 696, `/dev/watchdog`, and `watchdog0` exist | Separate watchdog path present; timer servicing is not proven |

The page's observation endpoint is explicitly for `/sys/module/rt_timer_wdg`;
thus the `/sbin/watchdog` process and built-in watchdog node do not establish
that the optional CPU watchdog module is active. The installed page's System
navigation still points Cron, Watchdog, and Discovery to the bare
`/Advanced_Services_Content.asp` URL. Its Telnet item also lacks an anchor.
Targets `#row_http_proto`, `#row_sshd`, and `#row_iperf3` do exist. KMS, LLTD,
ASUS discovery, Cron and CPU watchdog controls have inner control IDs, but no
matching `row_*` targets in this installed page. The installed image has no
build number in NVRAM, so these findings cannot be attributed to a specific
firmware build.

Filtering the current system log for `vlmcsd`, `lld2d`, `infosvr`, `crond`,
`rt_timer_wdg`, and `watchdog` returned no matching entries. This is only the
current log-buffer result, not proof that these services never logged errors.
Build #513 was still compiling at the time of the refresh; no image evidence
was available. No router setting, process, firmware, or network state was
changed.

## Managed-executor SSH retry — 2026-10-21 16:26 UTC

The managed executor can reach TCP port 22 on `192.168.20.1`, but its command
resolution selects `C:\Users\ANDRZEJ\.sbx-denybin\ssh.bat`/`ssh.cmd` before
Windows OpenSSH. The stub returned `off\r\nexit /b 1`; no SSH handshake,
authentication, or remote command occurred. The installed OpenSSH binary was
not invoked directly. Therefore the successful 16:18 read-only snapshot above
remains the latest router evidence. No router state changed.

At the same time, GitHub firmware run #513 (`39632923432`) remained in
progress. Its pre-build gates passed and the firmware compile step was active;
the final ROMFS/service image gates were still pending. This CI observation
does not update device-runtime state.

## Managed-executor SSH attempt — 2026-10-21 16:33 UTC

A fresh read-only command attempt to `ASUS@192.168.20.1` was intercepted
before SSH could start. The command resolved to the managed deny-bin wrapper,
which returned `off\r\nexit /b 1`. No SSH handshake, authentication, or remote
command occurred; no router state changed. The 16:18 snapshot above remains
the latest authenticated device observation. The workflow result and its
Privoxy failure are documented separately in
`WR1200JS-BUILD513-SERVICE-AUDIT.md`.
