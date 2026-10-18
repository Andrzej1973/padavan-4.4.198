# WR1200JS build 441 — final image and BusyBox evidence

- GitHub Actions run: [39096541190](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39096541190)
- Commit: `3e4e1d2d3b58a6234fda8a210dcda89928dffccd`
- Workflow result: success. Its target build, firmware ZIP and image-check jobs
  completed successfully.
- TRX: `WR1200JS_4.4.198.9-441_3e4e1d2d.trx`, 12,619,391 bytes.
- SHA256 independently recomputed after download and inspection:
  `ff41ca457b174afbe3dc2af116e2530cae7bfd0a0c4e6668311287f894e94b8a`.

## Exact image checks

The `target-busybox-audit` artifact reports success and 15/15 checks. Its
inventory covers 57 shell scripts (all syntax checks returned zero, none was
flagged for `command -v` review) and 150 BusyBox applets. The audit identifies
the image BusyBox as 709,260 bytes, SHA256
`9342f78c5619af314873b80a6288512644a1ed3b9f78f4aa36a361c20ab62654`, and the
target BusyBox `.config` SHA256 as
`2dc981d9b6160709aff6a8eb95563cfa23418a61d8bc47eba2233880c4417654`.
I independently extracted `bin/busybox` from this TRX; its size and SHA256
match the audit artifact.

The downloaded TRX contains the Cron, SSH, iPerf3, Privoxy, DoT, DoH and VPN
profile pages. I inspected the archived page and `usr/sbin/httpd` contents:
Cron (`wr_cron_process_state`), SSH (`wr_ssh_process_state`), iPerf3
(`wr_iperf3_process_state`) and Privoxy (`wr_privoxy_process_state`) observer
markers are present in the appropriate shipped page/handler; DoT/DoH refresh
markers and VPN profile-row/action handlers are also present. The target image
contains `/usr/bin/iperf3`, the USB/IP userspace tools and `wrvpn` profile
executables. The workflow reports successful image-check jobs for these
components, including `target-busybox-audit`, `ssh-image-checks`,
`iperf3-image-checks`, `privoxy-image-checks`, `stubby-image-checks`,
`doh-image-checks`, `vpn-profile-image`, `zram-image-checks`,
`zerotier-image-checks`, `usbip-settings-image`, and WAN/radio checks.

## Limits and next work

The audit itself states `runtime_verified: false` and
`whole_service_audit_complete: false`; it covers image shell syntax and bounded
applet probes, not service interactions. This evidence establishes a successful
build and selected image contents only. It does not establish operation on the
physical router, correct service start/stop behavior, WAN performance, browser
behavior, reboot persistence, or complete BusyBox compatibility. The router's
last recorded physical build is #396; do not infer #441 is installed.
