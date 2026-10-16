# Existing service port and settings-page audit

Date: 2026-10-11. The comparison uses the project's pinned Padavan 4.4.198
source commit `c25283e915a2a00a763774dd255b14aff997285e` and the Nilabsent
donor commit `14e4fac1ca24ab15278378d3e994db82fc9bcdda`. This is a source review;
the current WR1200JS Linux 4.4.198 image has not been run on the physical router.

## Keep the Padavan baseline intact

## Target BusyBox audit evidence — 2026-10-16

Full run 38845996781 succeeded at 5d04e61. Downloaded report preserved in
evidence/TARGET-BUSYBOX-5D04E61.json records 55 discovered shell scripts,
150 applets, successful target-shell syntax checks and exact hexdump/flock
option/contention probes under QEMU. BusyBox SHA256:
7b31fbd7dd8a138943c4ae2bd378b429d14a16992d1c53e991b64785e51a2e41.
Effective config SHA256:
33e621c275ef4f4667159c616f81afea84c22694d26963bf21c9c7e5f51812f6.
The command builtin is absent. No command -v use remained in these 55 scripts.
This is not proof of all service interactions or physical behavior.

Three files were outside the sh/ash scan: two Lua utilities and usr/bin/detect.sh.
Pinned source confirms detect.sh uses /bin/bash and is invoked by rc WAN and
firewall multi-PPPoE branches. prepare-mwan-shell.py changes its shebang to the
shipped /bin/sh and four let assignments to POSIX arithmetic/plain assignment;
routing/firewall commands are preserved. Exact pinned-source transformation
passed locally. The next target audit includes this helper and an arithmetic
probe; its execution is pending. Lua interpreter/provider checks and the
multi-PPPoE routing/locking/error paths remain open audit work.

### Baseline preservation requirements

The port should preserve the pinned firmware's existing pages, menus,
translations, configuration-save behavior and service controls. New project
pages should extend the existing menu and service lifecycle rather than
replacing the base WebUI or hiding unrelated settings. A selector in a config
is not proof that the selected package has a recipe, runtime integration, or a
usable page.

## DNS services and catalogues

| Component | Source and current profile | Port status / next check |
|---|---|---|
| dnsmasq | Pinned base, always built; receives resolver settings and DHCP DNS requests. | Verify final generated config contains only intended upstreams, no resolver loop, and explicit clock-bootstrap exceptions. The provided log shows routing directives were loaded, but does not prove successful resolution. |
| Stubby / DoT | Project port, selected in WR config, runtime default off. Provider defaults match the existing 3.4 router: Google, Cloudflare and Quad9; `dot.json` supports the provider list. | New image gate must pass; then test catalog load, TLS validation/time bootstrap, actual queries through dnsmasq, clean stop and reboot persistence. |
| DoH (`https_dns_proxy`) | Project port, selected in WR config, runtime default off; `doh.json` supplies provider choices. | New image gate must pass; confirm dnsmasq writes a real newline between generated server directives; exercise enabled and stopped/fail-closed modes. |
| SmartDNS | Pinned base has a `smartdns` build recipe and `Advanced_smartdns.asp`; WR selector is commented. | Reuse the existing base integration when requested; verify the page is preserved and hidden unless the package is included. |
| DNSCrypt | Not registered by the pinned base. Nilabsent provides `dnscrypt-proxy` 1.9.5, its shell service, a CSV list and `Advanced_Services_DNSCrypt.asp`; WR selector is commented. | Optional port is not implemented. The donor's old v1 list format should not be presented as current. Select and build a suitable MIPS/uClibc version, then port recipe, runtime/menu/HTTP fields, resolver catalogue and translations as one feature. Keep default off. |
| DNS forwarder / dnsproxy | Pinned base contains `dns-forwarder` (with an existing page) and `dnsproxy` package sources. | Preserve existing pages and capability gates; check which one the chosen profile actually includes and prevent unintended double-forwarding with DoT/DoH. |

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
security gate. Add an image-content check and, on the next router test, confirm
the menu route and controls through an authenticated local LAN or HTTPS
session. If still absent, inspect the browser console and actual ROMFS page
before adding a duplicate implementation.

The final device check must distinguish:

1. NVRAM configuration backup/restore (`.CFG`),
2. `/etc/storage` file backup/restore (`.TBZ`),
3. manual/automatic NVRAM commit mode and explicit commit,
4. storage-backed traffic history/time persistence.

Verify save/download and restore/upload for both file types, and test that the
selected persistence mode survives a reboot. Do not reset NVRAM or storage as
part of CI or the source audit.

## Next order

1. Finish and inspect the current WR1200JS build, including DoT, DoH, Privoxy
   and inherited Administration/backup-page presence.
2. Audit every selected service and its lists against the actual compiled
   image: build selector, source recipe, dependencies, ROMFS files, menu link,
   translations, lifecycle, persistence and status. Preserve stock features.
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
