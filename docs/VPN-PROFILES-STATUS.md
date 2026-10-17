# Independent WireGuard / AmneziaWG profiles — status

Updated 2026-10-17. This page follows `docs/SERVICE-RUNTIME-STATUS-CONTRACT.md`:
every capability is marked with what was actually verified, and the device is
listed as unverified wherever it is.

## What the feature does

A profile is a stored WireGuard or AmneziaWG configuration. It is applied to an
interface the controller owns: protocol configuration first, then addresses,
then routes in the profile's own table with a single `fwmark` rule, and finally
the profile's DNS list as a file for the opt-in dnsmasq step. Nothing touches
the main routing table, and no `from all` rule is created.

Commands (`/usr/sbin/wr-vpn-profile`):

| Command | Effect |
| --- | --- |
| `create <id> <wireguard\|amneziawg>` | Validate stdin and store the profile |
| `list`, `export <id>`, `observe <id>` | Metadata, private export, link state |
| `plan <id>` | Secret-free preview of requested vs observed state |
| `apply <id> [prefixes]` | Protocol, addresses, routes, DNS file |
| `up <id> [prefixes]` | Create the owned link, then `apply` |
| `down <id>` | Remove policy, then release the link |

`/usr/sbin/wr-vpn-profiles-service start|stop|status` drives the list in
`wrvpn_enabled`, passing `wrvpn_protect` as the protected prefixes. `rc` starts
it outside AP mode and stops it with the other services.

## States

| Capability | State | Evidence |
| --- | --- | --- |
| Profile store, locks, tombstones | verified in CI | `check-store`, run 39008382868 |
| Protocol transaction (lock, session CAS, readback) | verified in CI, compiles in the image | `check-config-transaction`; full build `b6ed863` success |
| Rollback to the last applied snapshot | verified in CI | `check-config-transaction` (`mismatch` + `snapshot` cases) |
| Apply preview (`plan`) | verified in CI | `check-plan-report`, run 39008382868 |
| Addresses with protected-prefix refusal | verified in CI | `check-addr-apply`, run 39006804519 |
| Routes in the profile table + `fwmark` rule | verified in CI | `check-route-apply`, run 39007061759 |
| DNS file (atomic, validated) | verified in CI | `check-dns-write`, run 39007655806 |
| Controller order and stop-on-failure | verified in CI | `check-profile-apply`, run 39008382868 |
| `up` / `down` commands | compiles; lifecycle verified separately | build `263bdee` board-port + compile; `check-lifecycle` |
| Service wrapper (`start`/`stop`/`status`) | verified in CI | `check-service`, run 39008382868 |
| `rc` start/stop hook | patched and applied in the image build | build `263bdee`, step `Apply WR1200JS board port` = success |
| DNS aggregation into dnsmasq (opt-in) | file and service verified in CI; rc line applied | `check-service`; same board-port step |
| Real tunnel, routes, DNS, handshake on the device | **not verified** | device unreachable; nothing flashed |

## Known limits

- Hostname endpoints are refused at apply time. `endpoint-pin` can replace them
  with resolved addresses, but nothing calls it yet; numeric endpoints are
  required today.
- "Route all traffic" is not offered: only packets the daemon marks are
  redirected. `priority_main` stays reserved for an explicit opt-in.
- There is no WebUI page for these profiles yet.
- The service is default-off and does nothing while `wrvpn_enabled` is empty.

## Next steps

1. Green full build for the current `main`, then package evidence (TRX, config,
   guide, checksums) as for builds 294–364.
2. Device acceptance in an authorised window: bring one profile up, confirm the
   routes live only in the profile table, confirm DNS only when opted in, and
   confirm the router still answers on its LAN address.
