# WR1200JS build 458 — service/WebUI and target BusyBox audit checkpoint

Date: 2026-10-18. GitHub Actions run
[`39118907721`](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39118907721),
firmware commit `deead1d5dcd62c13cb126f0caca537bb9b0607e5`, completed with
successful `build (wr1200js)`, `firmware-zip` and `downloads` jobs. This record
captures CI coverage relevant to the ongoing service/WebUI audit; it is not a
device acceptance report.

## Checks that passed in the build job

- Exact image BusyBox/QEMU audit of the discovered shell scripts, including
  shell syntax and bounded applet/options probes.
- VPN profile service lock path, WireGuard server export and USB/IP restore
  orchestration under the selected image BusyBox.
- Stubby image packaging/dependencies and DNS resolution through the image's
  Stubby under QEMU; ZRAM dependency/swap-priority image checks.
- Image checks for Stubby, DoH, Privoxy, iPerf3 and SSH; ZeroTier dependency
  closure, localized status UI/bounded refresh and advanced controls; StrongSwan
  packaged commands/dependency files; RSSI, WAN controls, USB/IP settings and
  EoIP WebUI/controller.
- Inherited settings backup/restore page, WebUI file-to-httpd route coverage,
  translations and model setup guide checks.
- Band Steering ROMFS gates for binaries, daemon integration, diagnostics,
  package closure, and the status page/HTTP observer assets.

The GitHub job step list confirms these checks completed successfully. The
build workflow also published the target BusyBox audit artifact. The report's
declared scope remains image shell syntax and bounded probes; it explicitly
sets `whole_service_audit_complete: false` and `runtime_verified: false`.

## Remaining work

- Create and maintain a selector-driven inventory of each selected service,
  its entry points, command providers, process ownership, lifecycle hooks,
  persistent settings, WebUI route/locales/status adapter, and current evidence.
- Extend exact target BusyBox checks from bounded applet probes to the
  uncovered service lifecycle and failure/recovery paths. Mock hardware and
  destructive effects; do not run live lifecycle operations during the audit.
- Review provider resolution, option/output contracts and error handling for
  every enabled service script and each dependent WAN/LAN/firewall/DNS/storage/
  VPN chain. The 57-script syntax result does not satisfy that review.
- Verify UI settings persistence and observed status on a supervised physical
  device session. Router build #396 remains installed per user confirmation;
  build #458 has not been flashed. No router state was changed by this audit.
- Keep device runtime, radio exchanges, VPN handshake/routing, service
  connectivity and reboot persistence explicitly unverified until observed.

## Follow-up — build 478 administration and navigation gates, 2026-10-18

GitHub Actions build #478 (run `39139346947`, source `d1dc0eb`) also passed
the final-ROMFS settings backup check. Its log states: “Settings backup/restore
page, menu route, secure gate, actions and EN/UK/RU labels are present in
ROMFS”; artifact `settings-backup-image-checks` (ID `12141023552`) was uploaded.
The checker explicitly requires the `login_safe()` gate, administration menu
route, NVRAM and `/etc/storage` backup/restore rows and handlers, and EN/UK/RU
keys. This proves those source elements survived packaging, not that an
authenticated user can successfully upload, restore, commit settings or
recover from the device UI.

The same run passed the final service navigation verifier for routes, pages
and EN/UK/RU labels; see
[the navigation evidence](WR1200JS-SERVICE-NAV-LAYOUT-2026-10-18.md). Build
#478 predates the current local regression fixture and stricter capability
parser. Neither result substitutes for a router browser/session check.

## Interpretation

Build #458 is successful firmware/packaging evidence and establishes that the
listed target-side CI checks passed for that source revision. It does not
establish that every setting saves/restores correctly, that every service starts
or stops correctly, that every displayed state is fresh on the device, or that
all services interoperate. A successful image audit is not full-service or
physical-router acceptance.
