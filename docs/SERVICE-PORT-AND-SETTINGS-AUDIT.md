# Existing service port and settings-page audit

## Board-scoped capability correction — 2026-10-21

The WR1200JS `watchdog_cpu` enable control is being removed because its
optional `rt_timer_wdg` provider is absent; the built-in MT7621 watchdog is a
separate path and remains untouched. The legacy lifecycle is made inert and
the board default becomes off, while generic defaults and behavior for other
boards remain intact. Source-fixture/navigation checks passed locally. The
final-ROMFS gate and a build containing this change remain pending. See
`evidence/WR1200JS-CPU-WATCHDOG-CAPABILITY-2026-10-21.md`.

Date: 2026-10-11. The comparison uses the project's pinned Padavan 4.4.198
source commit `c25283e915a2a00a763774dd255b14aff997285e` and the Nilabsent
donor commit `14e4fac1ca24ab15278378d3e994db82fc9bcdda`. This is a source review;
the current WR1200JS Linux 4.4.198 image has not been run on the physical router.

## Latest service audit checkpoint — 2026-10-21

### Update — 2026-10-21 16:59 UTC

Reproduced the Privoxy verifier's Apply-response extraction in memory against
the pinned Padavan `web_ex.c` at `c25283e915a2a00a763774dd255b14aff997285e`.
The exact upstream Save/Apply anchor matched; after applying the Privoxy
failure-response replacement and the shared-Wi-Fi `&shared` rewrite, the
current verifier found the Apply call and verified all ordering, callback,
restart-clear and abort conditions. This is stronger than a hand-written
synthetic handler fixture, but it is still not the complete source pipeline or
a final ROMFS run. The new image gate remains required.

### Update — 2026-10-21 16:56 UTC

Ran `python tools/check-target-busybox-map.py`, the repository's pre-build
selector-map gate. It passed the 12 active-service-map coverage fixtures,
including rejection cases for a missing map, omitted selector, missing check
and failed check. It confirmed that all 43 active WR1200JS `INCLUDE` selectors
have an explicit service/component classification, that both Shadowsocks
aliases resolve to the effective package map, and that the SFE/QoS exact-image
gates require their listed modules/configuration. It also confirmed the WPAD
and ZRAM final-ROMFS verifiers are ordered before the exact-image BusyBox audit.
This validates source-level audit coverage only; it does not validate a new
ROMFS, image BusyBox binary, service lifecycle or router runtime.

### Update — 2026-10-21 16:57 UTC

Retrieved the exact #513 Actions job steps and relevant log lines. The run
passed the DNS listener-conflict scenarios, the target dnsmasq combined
DoT/DoH config parse under QEMU, the Stubby lookup check and the exact target
BusyBox shell audit. Its later Privoxy final-image gate failed, so the DoH
packaging gate and subsequent discovery/KMS checks were skipped. This is
partial build/image evidence, not a verified downloadable image or router
runtime acceptance. The detailed boundaries are in
`evidence/WR1200JS-DNS-LISTENER-CONFLICT-GUARD-2026-10-21.md`.

### Update — 2026-10-21 16:53 UTC

Rechecked the current branch locally. `tools/services-nav/check-verifier.py`
passes the service-panel, board-exclusion, active-selector, return-link and VPN
profile-route checks. `tools/check-wr1200js-cpu-watchdog.py` passes the
WR1200JS-specific toggle removal, inert legacy lifecycle, off default,
read-only status retention and navigation exclusion fixture. An in-memory
Privoxy Apply parser fixture passes both the original two-argument call and
the shared-Wi-Fi `&shared` call, retaining the failure callback, pending-restart
clears and abort before success. `git diff --check` reports no whitespace
errors; it emits only existing CRLF normalization warnings in two audit docs.

The final-image verifier was not run: `padavan-4.4/trunk/romfs` is absent in
this checkout. A live GitHub Actions query found no newer firmware run than
#513: #513 is completed with failure after compilation/QEMU and the Privoxy
ROMFS gate; the newest run overall is Agent build failure monitor #125, not a
firmware build. No verified downloadable image or new router runtime evidence
exists for these local changes. Keep the source/image checks open. Next: include
the changes in a permitted WR1200JS image run, inspect its exact artifacts,
then refresh read-only device checks when the executor's SSH restriction is
resolved. No router state was changed.

The active `configs.build/wr1200js.config` was also evaluated against the
navigation capability map. Expected links are Stubby, DoH, WireGuard/AmneziaWG
profiles, ZeroTier, Shadowsocks, Privoxy, WPAD/PAC, HTTP/HTTPS, SSH, Telnet,
iPerf3, Cron, KMS, LLTD discovery and ASUS Info Discovery. EoIP is excluded by
its commented selector; the unsupported `watchdog_cpu` link is excluded by the
WR1200JS board policy. This is the generator's source-level expected menu, not
proof that a final image contains it.

### Update — 2026-10-21 16:38 UTC

Build #513 completed its WR1200JS compiler step and Stubby/QEMU checks, then
failed only the Privoxy `save_failure_apply_order` assertion among the
reported Privoxy predicates. The uploaded artifact showed that all failure
handling markers were present, but `apply_call_found` was false because the
image verifier required the two-argument Apply call even though the subsequent
shared-Wi-Fi transform adds `&shared`. The verifier now recognizes that
transformed spelling and checks it inside the Save/Apply response block while
retaining all failure callback, restart-clear and abort requirements. Its
in-memory transformed-call fixture passed; no subsequent image has verified
the fix yet. #513 produced no verified download. See
`evidence/WR1200JS-BUILD513-SERVICE-AUDIT.md`.

The managed executor's latest SSH attempt was intercepted by its deny-bin
before handshake or authentication. The latest authenticated router snapshot
is still 16:18 UTC; there was no router change.

### Historical live refresh — 2026-10-21 16:18 UTC

This state was superseded by the 16:38 update above.

Firmware build #513 (`39632923432`) is running on source HEAD `8ff6016`.
Its WR1200JS compile job remains in progress; service image gates have not yet
run. The separate Band Steering ABI workflow is not a firmware build. SSH
access is restored at `192.168.20.1`: KMS is enabled/present; LLTD, ASUS
Discovery and Cron are disabled/absent. The saved CPU watchdog flag is on but
`rt_timer_wdg` is absent; the distinct built-in watchdog path exists, though
timer servicing is unverified. Current filtered logs had no matching entries.
Installed navigation still has generic Cron/Watchdog/Discovery links and no
row anchors for those controls. No router state changed. See the latest SSH
check in `evidence/WR1200JS-SERVICE-READONLY-CHECK-2026-10-21.md`.

Firmware run #512 (`39624109819`, source `22431a94`) completed compilation and
passed the combined Stubby dnsmasq configuration check under QEMU using the
temporary guest `/dev/urandom` overlay. It then failed the Privoxy final-image
gate `save_failure_apply_order`; all other checks in the uploaded
`privoxy-image-checks` report passed. The downloads job rejected the incomplete
selected-build set, so the run produced no verified downloadable image. This
is now the blocking item 4 gate. Diagnose it against the exact transformed
`web_ex.c`; retain strict proof that a storage-save failure returns an error,
clears pending restart events, and suppresses the success callback.

Fresh read-only router observations from 2026-10-21 are recorded in
`evidence/WR1200JS-SERVICE-READONLY-CHECK-2026-10-21.md`: KMS enabled/running;
LLTD and ASUS discovery disabled/stopped; Cron disabled with no process; a
`/sbin/watchdog` process exists, but the matching persisted UI flag was not
established. The installed Services page still uses generic System navigation
targets; `buildno` is empty, so installed-image identity is unknown. Browser
authentication to the alternate router address failed; no device state was
changed.

## Keep the Padavan baseline intact

## QoS packaging correction — 2026-10-19

The pinned iproute2 wrapper installed the already-built `/bin/tc` only when
SQM was selected. WR1200JS selects QoS while excluding SQM. Source preparation
now installs `tc` for either selector. GNU Make dry runs cover all selection
combinations and preserve `ip`. Build #492 independently confirms the image
modules, MIPS `tc`, library closure and QEMU version check; see
`evidence/WR1200JS-BUILD492-SERVICE-AUDIT.md`. The
exact-image audit now requires QoS kernel dependencies and executable MIPS
`tc` with its ELF/library closure and `tc -V` under QEMU. This is not acceptance
of QoS policy controls, attached rules, persistence or load behavior; those
remain open. See [QoS evidence](evidence/WR1200JS-QOS-IMAGE-GATE-2026-10-19.md).

## Target BusyBox audit evidence — 2026-10-16

Full build #357 (`61bce23`, run 38950105582) passed the corrected exact-image
WG/AWG server/export/startup fixture and the USB/IP restore fixture. The target
audit artifact was downloaded; identities and coverage are in
`evidence/WG-SERVER-TARGET-BUSYBOX-BUILD357.md`. Network operations in the WG
fixture remain mocked; physical acceptance and multi-profile integration are
open. Host-native import-adapter checks also passed with both pinned protocol
parsers in service CI #125. Neither result establishes simultaneous tunnels.

Build #354 (`d690a6a8`, run 38943263134) report was downloaded independently.
It records 56 shell scripts, 150 applets and all existing gates passing,
including the converted multi-PPPoE helper syntax/arithmetic and readlink probes.
The two Lua utilities remain outside shell coverage. Current BusyBox SHA256:
`df74d5e1056ff06eb7e6a36ebadbf778b3a6ea326d698c9d2e896bd539a6657a`;
effective config SHA256:
`457ac8a14266c8b0cf19a20f8f42e84aff25830faeab234dcd0a6f28c67cf6e4`.
This supersedes the older identity below, not the open interaction/runtime work.

Added an image gate for the shipped WireGuard/AmneziaWG server configuration
and client export functions. `check-wg-server-export.py --target-root` uses the
ROMFS script and BusyBox shell under QEMU with only explicit target applet
providers in PATH. NVRAM and wg operations are synthetic. Cases include shared
AWG parameters, standard WG exclusion, invalid input, 32-bit header boundaries
and numerically duplicate headers. Host scenarios pass; the new target gate
still awaits CI. Server startup, routing and physical behavior remain open.

Runs #355/#356 compiled the firmware and passed the general BusyBox gate, then
failed in this isolated export fixture because its explicit provider PATH
omitted tee. tee is present in the image applet inventory. Added its target
wrapper and an upfront applet inventory check; corrected target execution is
pending. This failure is a harness issue, not evidence that image tee is absent.

Server startup review found a stale-interface path: after successful link
creation, failed MTU/address/configuration could leave a down interface that
made the next start report already started. The server now checks each stage
and attempts deletion on failure only after its own successful create. A
pre-existing interface and failed create do not enter that cleanup path;
failed cleanup is logged and startup still fails. The same fixture exercises
actual startup control flow with mocked ip/wg operations, including every
failure stage and failed deletion. Host cases pass; target BusyBox CI and
actual kernel operations remain unverified. Concurrent lifecycle locking is
not established by this fixture.

Full run 38845996781 succeeded at 5d04e61. Downloaded report preserved in
evidence/TARGET-BUSYBOX-5D04E61.json records 55 discovered shell scripts,
150 applets, successful target-shell syntax checks and exact hexdump/flock
option/contention probes under QEMU. BusyBox SHA256:
7b31fbd7dd8a138943c4ae2bd378b429d14a16992d1c53e991b64785e51a2e41.
Effective config SHA256:
33e621c275ef4f4667159c616f81afea84c22694d26963bf21c9c7e5f51812f6.
The command builtin is absent. No command -v use remained in these 55 scripts.
This is not proof of all service interactions or physical behavior.

At the time of this earlier shell-only scan, three files were outside its
coverage: two Lua utilities and usr/bin/detect.sh.
Pinned source confirms detect.sh uses /bin/bash and is invoked by rc WAN and
firewall multi-PPPoE branches. prepare-mwan-shell.py changes its shebang to the
shipped /bin/sh and four let assignments to POSIX arithmetic/plain assignment;
routing/firewall commands are preserved. Exact pinned-source transformation
passed locally. The next target audit includes this helper and an arithmetic
probe; its execution is pending. Lua image checks are superseded by build #504
as recorded below; multi-PPPoE routing/locking/error paths remain open.

### Lua image audit — build #504

Build #504's exact-source target BusyBox gate includes
`target_lua_audit.audit_lua` when Lua is selected. The source at the recorded
build commit requires the image MIPS Lua 5.1 interpreter, cjson/nixio shared
module closure, syntax checks for the image Lua scripts, JSON-to-Lua-to-JSON
round-trip, and rejection of malformed inputs under QEMU. GitHub Actions logs
show the aggregate gate passing; its success predicate includes the Lua check.
This closes the image-level Lua interpreter/provider/converter audit for that
image. It does not verify Lua-consuming service behavior, `nixio` operations,
or physical runtime. See `evidence/WR1200JS-BUILD504-SERVICE-AUDIT.md`.

### Baseline preservation requirements

The port should preserve the pinned firmware's existing pages, menus,
translations, configuration-save behavior and service controls. New project
pages should extend the existing menu and service lifecycle rather than
replacing the base WebUI or hiding unrelated settings. A selector in a config
is not proof that the selected package has a recipe, runtime integration, or a
usable page.

## DNS services and catalogues

### Combined Stubby/DoH dnsmasq routing review — 2026-10-21

The WR1200JS config selects both packages, but both factory enable defaults are
off. The Stubby helper inserts `stubby_dnsmasq_config()` into
`start_dns_dhcpd()`; it emits `no-resolv` and a local upstream for enabled
router-DNS modes 1/3. The DoH helper independently inserts
`doh_dnsmasq_config()` into that same function; mode 1 emits `no-resolv` and a
local upstream for each configured HTTPS resolver. Both preserve the existing
domain-scoped NTP bootstrap exception. No mutual-exclusion check was found in
the reviewed integrators or NVRAM schemas.

Both router-DNS modes intentionally contribute encrypted upstreams to the same
dnsmasq server pool; they are not an exclusive choice. The WR1200JS build pins
dnsmasq 2.90 from Padavan source commit
[`c25283e`](https://github.com/vipshmily/padavan-4.4/commit/c25283e915a2a00a763774dd255b14aff997285e).
Its [`forward.c`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/dnsmasq/dnsmasq-2.90/src/forward.c)
keeps eligible upstreams in a shared server array: without `--all-servers`,
normal forwarding may start with one server, retry or move to another on
failure, and periodically forward to all eligible servers; `--strict-order`
changes that policy. Therefore both services can answer DNS, but dnsmasq does
not guarantee a stable preference for DoT versus DoH. Do not claim either
service is the sole path while both modes are active.

Both snippets currently emit `no-resolv` and the same NTP-only bootstrap
exceptions, so the combined file contains duplicate directives. Factory
enable defaults remain off; default listener ports (Stubby 5453, DoH 5053–5056)
do not overlap. A shared listener guard has now been added to both lifecycle
helpers. It refuses to start the service being applied when the other enabled
service has a configured resolver on the same port and overlapping bind
address (including wildcard binds); DoH's per-resolver port offsets are
considered. This is a runtime guard, not yet browser-side prevalidation. A
host/target-shell fixture covers same-address collision, a later DoH resolver,
distinct specific addresses, wildcard overlap, default ranges and disabled
DoH. The final DoH-side specific-address case was corrected before validation.
All 17 host fixture scenarios passed under Git for Windows `sh.exe`, including
invalid peer modes/ports and a Stubby system port. Sandbox shell startup failed
with Win32 error 5; an approved run outside the sandbox succeeded. The Stubby
configuration-generator fixture and syntax checks of seven shell files passed.
The startup script, guard and dnsmasq emitter now enforce the form's existing
1024..65535 Stubby port range without rewriting saved settings. Invalid
listeners retain `no-resolv`. The image runner's DoH guard source reference was
corrected to the shared dns-common directory. Build #513 then passed the target
BusyBox listener-conflict fixture, parsed the combined emitted DoT/DoH config
with the image dnsmasq under QEMU, and completed an authenticated DoT lookup
through the image Stubby binary. The Stubby image gate also passed. Its later
DoH image-packaging/source-identity gate was skipped after the earlier Privoxy
gate failed, so the DoH ROMFS binary and installed guard identity are not
confirmed by #513. The C-emitter fixture separately compiles and exercises the
actual two emitters alone and together, and checks prepared-source call sites;
it proves configuration generation and syntax acceptance only, not live
DoH/DoT routing or upstream preference. Native GCC compilation passed ten
cases (four combined/individual modes and six Stubby port boundaries). The
2026-10-18 read-only router sample showed strict-mode Stubby enabled and DoH
disabled; the installed firmware identity remains unknown.

Keep the combined mode supported as a pool of encrypted upstreams, and keep
service-specific preference/failover acceptance open until target runtime
measurements are available. The source guard addresses configured DoT/DoH
listener overlap only. The #513 target parser/BusyBox checks do not replace the
skipped DoH-specific ROMFS gate or physical runtime checks.

| Component | Source and current profile | Port status / next check |
|---|---|---|
| dnsmasq | Pinned base, always built; receives resolver settings and DHCP DNS requests. | Build #513's target dnsmasq parsed the combined emitted DoT/DoH config under QEMU. Verify the live generated file from current NVRAM has only intended upstreams, no loop, and explicit time-bootstrap exceptions; parsing does not prove successful routing/resolution on the router. |
| Stubby / DoT | Project port, selected in WR config, runtime default off. Provider defaults match the existing 3.4 router: Google, Cloudflare and Quad9; `dot.json` supports the provider list. | Build #513 passed the Stubby final-ROMFS/ELF gate and authenticated DoT lookup using image binaries under QEMU; target BusyBox audit and listener-guard cases also passed. Device acceptance remains open: catalog load, TLS/time bootstrap, queries through dnsmasq, clean stop and reboot persistence. |
| DoH (`https_dns_proxy`) | Project port, selected in WR config, runtime default off; `doh.json` supplies provider choices. | Build #504 passed its DoH image/ELF dependency gate. Build #513's combined-config parser passed, but its DoH package/guard source-identity gate was skipped after the Privoxy failure. On-router checks remain: package/ROMFS, generated dnsmasq config, enabled queries, clean stop, fail-closed behavior and reboot persistence. |
| SmartDNS | Pinned base has a `smartdns` build recipe and `Advanced_smartdns.asp`; WR selector is commented. | Reuse the existing base integration when requested; verify the page is preserved and hidden unless the package is included. |
| DNSCrypt | Not registered by the pinned base. Nilabsent provides `dnscrypt-proxy` 1.9.5, its shell service, a CSV list and `Advanced_Services_DNSCrypt.asp`; WR selector is commented. | Optional port is not implemented. The donor's old v1 list format should not be presented as current. Select and build a suitable MIPS/uClibc version, then port recipe, runtime/menu/HTTP fields, resolver catalogue and translations as one feature. Keep default off. |
| DNS forwarder / dnsproxy | Pinned base contains `dns-forwarder` (with an existing page) and `dnsproxy` package sources. | Preserve existing pages and capability gates; check which one the chosen profile actually includes and prevent unintended double-forwarding with DoT/DoH. |

Detailed local test output and evidence limits are recorded in
`evidence/WR1200JS-DNS-LISTENER-CONFLICT-GUARD-2026-10-21.md`.

The attached syslog screenshot is consistent with dnsmasq being configured to
send ordinary DNS to local DoT `127.0.0.1:5453` and a second local service at
`127.0.0.1:65053`, while using direct DNS exceptions for NTP/time domains. The
`127.0.0.1 refused to do a recursive query` message warrants checking the
request's destination and active listeners; it does not, by itself, identify
which local service refused it. Keep the time-domain bootstrap exception
explicit and narrow, and verify that encrypted DNS has no silent plaintext
fallback.

## Tor and Zapret sources

The pinned 4.4 base does not provide Tor or Zapret package directories or their
build registration. Nilabsent is a useful port donor:

- Tor recipe at the reviewed commit targets `tor-0.4.9.9`, carries patch and
  GeoIP data files, and has separate optional GeoIP/GeoIPv6 installation. Its
  GeoIPv6 install path is conditional on IPv6. Preserve the user's existing
  Stage 2 decision: keep TOR, GeoIP, GeoIPv6 and OBFS4 out of the Stage 1
  WR1200JS image until baseline device acceptance.
- Zapret's donor package has separate Zapret and Zapret2 build targets, service
  script, configuration, and strategy datasets. These are not just two config
  switches: they require their userspace tools, netfilter/kernel dependencies,
  config files, lifecycle and WebUI to be ported together. Keep them deferred
  and disabled in the Stage 1 image.
- Resolver and strategy datasets are versioned inputs. Before porting them,
  record the donor revision, data-file hashes, licenses and refresh/update
  method; do not silently fetch a floating list in a supposedly reproducible
  build.

## Backup, restore and persistent storage page

The pinned base already includes `Advanced_SettingBackup_Content.asp`, lists it
in the Administration submenu in `state.js`, and copies the complete stock
WebUI directory into ROMFS before removing board-inapplicable pages. The page
contains the NVRAM factory-reset, save and upload rows and the `/etc/storage`
reset, backup and restore rows seen in the user's screenshot, plus commit mode,
write-now, traffic-history and system-time persistence controls.

Those action rows start hidden and JavaScript reveals them only when
`login_safe()` is true. In the HTTP daemon, that condition requires an active
login from a safe local address; HTTPS authentication is also accepted when
HTTPS is compiled. **Inference:** access over the Amnezia tunnel may have been
outside the safe-address check, which would hide backup/restore buttons while
leaving the page visible. The source has not been modified to weaken this
security gate. Build #504 now provides the image-content check below. On the
next router test, confirm the menu route and controls through an authenticated
local LAN or HTTPS session. If still absent, inspect the browser console and
actual ROMFS page before adding a duplicate implementation.

Build #504 completed the image-content portion: its final-ROMFS verifier found
the page, Administration menu route, secure-session gate and EN/UK/RU labels;
the browser-logic fixture passed checks for safe-session actions, uploads,
downloads, cancellation and save feedback. This is synthetic CI/image evidence.
The authenticated physical-browser check and actual `.CFG`/`.TBZ` backup and
restore operations remain open.

The final device check must distinguish:

1. NVRAM configuration backup/restore (`.CFG`),
2. `/etc/storage` file backup/restore (`.TBZ`),
3. manual/automatic NVRAM commit mode and explicit commit,
4. storage-backed traffic history/time persistence.

Verify save/download and restore/upload for both file types, and test that the
selected persistence mode survives a reboot. Do not reset NVRAM or storage as
part of CI or the source audit.

## Next order

1. **Completed for build #504:** inspect DoT, DoH, Privoxy and inherited
   Administration/backup-page presence. The #505 VPN selector fix is newer
   than #504 and still needs final-ROMFS verification in a later build.
2. Audit every selected service and its lists against the actual compiled
   image: build selector, source recipe, dependencies, ROMFS files, menu link,
   translations, lifecycle, persistence and status. Preserve stock features.
   Start with the selected Stubby/DoH configuration and lifecycle paths, then
   continue through the remaining enabled services. The source-level/mock
   coverage of #247 is indexed in
   `evidence/WR1200JS-SERVICE-STATE-CHECKS-247.md`; it does not substitute for
   final-image or device evidence.
3. Make the commented DNSCrypt option a genuinely buildable optional port,
   using Nilabsent's page and runtime as the starting point but choosing a
   maintained and target-compatible source/list version.
4. Only after WR1200JS baseline device acceptance, continue the already-deferred
   Tor and Zapret/Zapret2 ports; keep their heavy datasets optional.
5. Runtime-verify DNS behavior, backup/restore controls and reboot persistence
   only when the router is back on 4.4 and a recoverable test window is agreed.

## Build 194 publication correction

The firmware compiled, but the Stubby image gate rejected invalid UTF-8 in
Advanced_Services_DoT.asp. Of the 21 files published in commit 56ba1f8,
only that HTML file differed unexpectedly from its local Git blob hash.
The corrected HTML is published as explicit base64 bytes, with returned
Git blob SHA checked against the local SHA before updating main. DoH and
Privoxy image gates were skipped after the Stubby failure; they are not
claimed as passing. Keep strict decoding and all image checks enabled.

## Target BusyBox readlink canonicalization — 2026-10-16

Full run [38922347945](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38922347945)
failed the synthetic USB/IP restore success path. Exact target stderr advertises
`Usage: readlink FILE`; `readlink -f` fails after valid VID/PID/serial preflight.
Affected paths include USB/IP restore uniqueness and device-policy mounted/swap/
NIC/modem guards, which all need canonical paths. Pinned base disables
`CONFIG_FEATURE_READLINK_FOLLOW`; DoH previously enabled the applet alone.
The new WR preparation enables READLINK and FEATURE_READLINK_FOLLOW explicitly.
Target CI verifies effective flags and actual canonical symlink output, then
reruns restore. Fix implemented; new target execution and hardware acceptance
remain unverified. No host realpath fallback or weakened guard introduced.
