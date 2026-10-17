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

A failed `up` removes its `fwmark` rule and releases the owned link, so a
rejected profile never leaves a half-configured interface behind. Protected
prefixes may be IPv4 or IPv6, separated by commas; spaces around a prefix are
ignored, and a malformed entry refuses the start instead of being skipped.

Commands (`/usr/sbin/wr-vpn-profile`):

| Command | Effect |
| --- | --- |
| `create <id> <wireguard\|amneziawg>` | Validate stdin and store the profile |
| `list`, `export <id>`, `observe <id>` | Metadata, private export, link state |
| `plan <id>` | Secret-free preview of requested vs observed state |
| `apply <id> [prefixes]` | Protocol, addresses, routes, DNS file |
| `up <id> [prefixes]` | Create the owned link, then `apply` |
| `down <id>` | Remove policy, then release the link |
| `delete <id>` | Tombstone an idle profile; refuses a live session |
| `edit <id>` | Validate stdin and replace an idle profile; bumps its revision |

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
| Addresses with IPv4 and IPv6 protected-prefix refusal | verified in CI | `check-addr-apply`, run 39010171751 |
| Protected-prefix parsing (trim, overflow refusal) | verified in CI | `check-protect`, run 39010171751 |
| Routes in the profile table + `fwmark` rule | verified in CI | `check-route-apply`, run 39007061759 |
| DNS file (atomic, validated) | verified in CI | `check-dns-write`, run 39007655806 |
| Controller order and stop-on-failure | verified in CI | `check-profile-apply`, run 39008382868 |
| `up` / `down` commands | compiles; lifecycle verified separately | build `263bdee` board-port + compile; `check-lifecycle` |
| Service wrapper (`start`/`stop`/`status`) | verified in CI | `check-service`, run 39008382868 |
| Stop covers ids left only in runtime state | verified in CI | `check-service`, run 39010171751 |
| Failed `up` cleanup (rule removed, link released) | implemented and compiled in CI; dedicated fixture pending | service run 39010171751 |
| Hostname endpoint pinning in `up` (before the link exists) | implemented; CLI compiles in CI, build 380 pending | `check-endpoint-pin`; service run 39011116079 |
| `delete` tombstone (idle profiles only) | verified in CI | `check-manager`, run 39011116079 |
| `edit` (validate, refuse live, bump revision) | implemented; manager fixture updated | `check-manager` (CI pending) |
| `rc` start/stop hook | patched and applied in the image build | build `263bdee`, step `Apply WR1200JS board port` = success |
| DNS aggregation into dnsmasq (opt-in) | file and service verified in CI; rc line applied | `check-service`; same board-port step |
| Real tunnel, routes, DNS, handshake on the device | **not verified** | device unreachable; nothing flashed |

## Known limits

- `up` resolves hostname endpoints once, before the link exists, and applies a
  numeric copy; the stored record keeps the name. In-place `apply` still
  refuses hostnames because the tunnel may already carry DNS there.
- "Route all traffic" is not offered: only packets the daemon marks are
  redirected. `priority_main` stays reserved for an explicit opt-in.
- There is no WebUI page for these profiles yet.
- The service is default-off and does nothing while `wrvpn_enabled` is empty.
- A DNS-file failure also tears the profile down; `up` returns 0 only when the
  protocol, addresses, routes and (when present) DNS file all succeeded.
- Editing a stored profile bumps its revision. The runtime session keeps the
  revision it was created for, and both the link lifecycle and the transaction
  compare against it, so an updated profile needs `down` and then `up`; an
  in-place apply of a new revision is refused by design, not silently applied.

## Next steps

1. Green full build for the current `main`, then package evidence (TRX, config,
   guide, checksums) as for builds 294–364.
2. Device acceptance in an authorised window: bring one profile up, confirm the
   routes live only in the profile table, confirm DNS only when opted in, and
   confirm the router still answers on its LAN address.
