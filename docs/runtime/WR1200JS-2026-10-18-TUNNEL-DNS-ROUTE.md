# WR1200JS read-only VPN and DNS route check — 2026-10-18

## Method and limits

Read-only SSH inspection of the live router at `192.168.20.1`. No service,
route, setting, or tunnel was changed. One benign lookup (`example.com`) was
sent through the router's local resolver. Private keys and complete VPN
configuration were not read or recorded. The check describes router-side
state; it cannot inspect DNS or route settings held only on a remote client.

## Observed state

- Device identifies as WR1200JS and runs kernel `4.4.198`; the kernel build
  timestamp was `Sun Oct 18 14:19:00 UTC 2026`.
- Only WireGuard-compatible interface listed was `wg1`; no `wg0` client
  interface was present. `wg1` is UP with `192.168.30.1/24`, listening on
  UDP 10152. The AmneziaWG kernel module is loaded.
- `wg1` has two host-scoped peers; their inner addresses and one recent
  external client endpoint are redacted. The user confirmed that the recent
  peer is their own connection from abroad to the router in Ukraine. It is an
  inbound peer endpoint, not a VPN-provider endpoint. No outbound provider
  endpoint was present in the live peer list.
- The independent profile manager's stored-profile directory
  `/etc/storage/wrvpn` was empty. No client profile with an `Endpoint` or
  `DNS` field was available to inspect on the router.
- Main routing policy had only `local`, `main`, and `default` rules. The
  default route used the ISP gateway on `eth3`; routes to the configured
  public DNS servers and the remote peer's public endpoint also resolved
  through `eth3`, not `wg1`. The WAN gateway and WAN source address are
  redacted.
- Router resolver chain was active: dnsmasq listened on `192.168.20.1:53`
  and forwarded ordinary queries to `127.0.0.1#5453`; Stubby listened on
  `127.0.0.1:5453`. Stubby was configured with DNS-over-TLS upstreams:
  Google `8.8.8.8`, Cloudflare `1.1.1.1`, and Quad9 `9.9.9.9`.
- The socket table showed live TCP connections from the WAN address to
  `8.8.8.8:853` and `9.9.9.9:853`, plus a recent Cloudflare
  `1.1.1.1:853` connection in `TIME_WAIT`. This confirms active DoT transport
  over WAN at the time of inspection.
- dnsmasq had explicit NTP-related exceptions pointing at the ISP DNS server
  (address redacted) and Cloudflare `1.1.1.1`; those exception queries bypass
  Stubby. `vpnc_dns_t` was empty.
- `nslookup example.com 127.0.0.1` succeeded and returned IPv4 and IPv6
  addresses. This verifies a working local lookup at that moment, not an
  end-to-end DNS leak test from a remote VPN client.

## Conclusion

The router itself was **not using an outbound AmneziaWG client tunnel** at
the time of inspection. `wg1` was acting as a server interface for remote
peers, while the router's default route and DNS upstream routes used WAN
`eth3`. For ordinary router/LAN DNS, the configured path was dnsmasq → Stubby
→ Google/Cloudflare/Quad9 over TLS, egressing through the ISP WAN. Thus the
router was not forwarding ordinary DNS queries to the ISP's resolver, but the
encrypted DNS connection itself was not routed through an outbound VPN tunnel.
NTP-specific DNS exceptions do include the ISP resolver.

The user's confirmed connection is the **client-to-router tunnel**: the
client's encrypted WireGuard/AmneziaWG transport reaches the router's public
WAN endpoint (redacted), and the router sends those outer packets through its
ISP gateway on `eth3`. This is separate from the client's inner traffic after
decryption. Whether that inner traffic is forwarded from the router to the
same WAN gateway depends on the client profile's `AllowedIPs`, the router's
forwarding/firewall/NAT state, and any policy routes. The server snapshot
alone does not establish those client-side settings or prove that all client
internet traffic uses the tunnel. The user's description indicates that this
is the intended arrangement; it is not yet a packet-level end-to-end proof.

The screenshot or an external DNS-check page alone cannot establish what DNS
the remote client's own profile uses. To confirm that side, inspect the active
client's local profile fields (`Endpoint`, `AllowedIPs`, `DNS`) and its route
table; do not infer them from the server's peer record. No router change is
needed for this observation.

## Client-side confirmation — 2026-10-18

Read-only Windows checks on the user's laptop showed an active WireGuard
Tunnel adapter, a tunnel-scoped address (redacted), and the router as its DNS
server. The route table contains the router LAN on-link through that tunnel
adapter and a tunnel default route with metric 0; the physical Ethernet
default route has metric 25. This supports the intended full-tunnel route
preference while the adapter is active. The effective public Internet route
was not packet-captured.

`nslookup example.com 192.168.20.1` succeeded. A direct
`nslookup -type=txt whoami.cloudflare 1.1.1.1` timed out twice. This supports
that the client is configured to send ordinary DNS to the router through the
tunnel and that direct DNS to `1.1.1.1` did not answer in this sample; it does
not prove that every application uses the Windows system resolver, rule out
browser DoH, or identify the resolver seen by a public DNS-check service. No
router, tunnel, DNS, or client setting was changed. The complete client
configuration and private keys were not read.
