# WR1200JS pre-flash baseline — 2026-10-17

Read-only record taken before any decision to flash build 389. Nothing on the
device was changed: no nvram writes, no service restarts, no firmware update.

## Access

- User tunnel enabled; `192.168.20.1:22` and `:80` reachable from the sandbox.
- SSH `ASUS@192.168.20.1` with `~/.ssh/id_ed25519` (dropbear), read-only
  commands only.

## State

| Item | Value |
| --- | --- |
| Kernel | `Linux WR1200JS 4.4.198 #1 SMP Sun Oct 11 11:15:59 UTC 2026 mips` |
| Firmware | `firmver=4.4.198.9` |
| Uptime / load | 5 days 16:54 / 0.03 0.03 0.02 |
| WAN | `eth3` 5.58.139.185/18, default via 5.58.128.1 |
| LAN | `br0` 192.168.20.1/24 |
| Management tunnel | `wg1` 192.168.30.1/24 |
| Services | httpd, dnsmasq, dropbear running |
| WebUI on localhost | `HTTP/1.0 200 OK`, `Server: httpd` |
| Swap | none |
| Memory | 123652 kB total, ~60 MB free |
| `/tmp` | 24 MB tmpfs, ~23 MB free |

The flashed build predates the independent profile manager:
`/usr/sbin/wr-vpn-profile`, `/usr/sbin/wr-vpn-profiles-service` and
`/usr/libexec/wrvpn/action-worker` are absent.

## What this proves

The device is reachable, stable over five days, keeps its LAN/WAN configuration
and the user's management tunnel, and runs the earlier 4.4.198 port.

It does not verify build 389. Device acceptance of the profile manager and the
profile WebUI requires an authorized firmware update followed by the checks in
`docs/VPN-PROFILES-ACCEPTANCE.md`.
