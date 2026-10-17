# VPN profile routing and DNS policy (derived, proposed)

Scope: the independent WireGuard/AmneziaWG profiles built from
`tools/vpn-profiles/`. This document derives the route and DNS behaviour from
what the pinned base tree already does, so the controller does not invent a new
network model. Nothing here is implemented beyond the protocol transaction yet.

## What the existing code already establishes

- DNS is centralised. `trunk/user/rc/net_wan.c:1666` `update_resolvconf()`
  rewrites `/etc/resolv.conf`: the first entry is always `nameserver 127.0.0.1`
  (dnsmasq), and it is refilled by `fill_dnsmasq_servers()` before the file is
  replaced.
- VPN-provided DNS is opt-in and separate from WAN DNS. `net_wan.c:1682` reads
  `vpnc_pdns` (0/1/2) and, when non-zero, appends the servers listed in
  `vpnc_dns_t` (`net_wan.c:1694`) before the WAN servers. With `vpnc_pdns != 2`
  the WAN servers are still added, and `8.8.8.8` remains the last resort.
- Routes are per interface. The rc code flushes them with
  `clear_if_route4(<ifname>)` (`net_wan.c:1460`) instead of editing the main
  table blindly.
- Profile resources already reserve the policy-routing identity:
  `resources.h` defines `table = 20000 + id`, `mark = 0x57560000 | id`,
  `priority_main` and `priority_tunnel` (consecutive), plus the DNS file name
  `wrv<id>.dns`.
- The native configuration already carries the mark: `config-plan.c` inserts
  `FwMark = <mark>` into `[Interface]`, so packets from the tunnel daemon can be
  matched by a rule without touching other traffic.

## Proposed policy

1. **Routes go to the profile table, never the main table.** For
   `resources.table`: add the profile's `AllowedIPs`/default as
   `ip route add <prefix> dev <interface> table <table>`.
2. **Only marked traffic is redirected by default.** Add
   `ip rule add fwmark <mark> lookup <table> priority <priority_tunnel>`.
   `priority_main` stays unused until a user explicitly enables "route all
   traffic" for that profile, because a `from all lookup ...` rule would move
   the router's own traffic and is exactly what can cost LAN access.
3. **Addresses are the profile's own.** Each `Address =` line becomes
   `ip address add <cidr> dev <interface>`; nothing is added to the WAN or LAN
   interfaces.
4. **DNS follows the existing opt-in pattern.** The profile's `DNS =` values are
   written to `resources.dns` and appended to dnsmasq as upstreams only when the
   profile's DNS preference is enabled — mirroring `vpnc_pdns`/`vpnc_dns_t`.
   `127.0.0.1` stays first, so clients keep using dnsmasq and losing the tunnel
   cannot leave the router without a resolver.
5. **Teardown is scoped.** Removing a profile deletes its rules, its table
   routes and its address assignments by interface name and table id, the same
   way `clear_if_route4()` limits itself to one interface.

## Invariants the implementation must preserve

- The router's management address and the LAN subnet never leave the main table.
- No rule is added without an `fwmark` until the user opts in, and the opt-in is
  visible in the apply preview.
- DNS `127.0.0.1` is never removed while any interface is up.
- Every change is previewed first (`wr-vpn-profile plan <id>`) and read back
  afterwards; a failure reports the observed state instead of a success.

## Open decisions for the owner

- Whether "route all traffic" is offered per profile at all, and if so whether
  it uses `priority_main` with an `from all` rule or an explicit nftables
  redirect.
- Whether the profile DNS preference should reuse `vpnc_pdns` or get its own
  nvram key, so a static VPN client and a profile cannot fight over it.

Until those are answered, the controller implements points 1–5 with the
conservative defaults above: no global route rule, DNS only when enabled.
