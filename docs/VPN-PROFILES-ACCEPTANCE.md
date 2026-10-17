# VPN profiles — device acceptance checklist

Use this only after an image with the profile tools is installed and only inside
an authorised test window. Nothing here is proven by CI: host fixtures and
compilation do not show that a tunnel works, and they do not show that the
router still answers on its LAN address.

## Preconditions

- Explicit permission for this session. Flashing and rebooting stay separate
  approvals; this checklist does not include them.
- LAN access to the router is available on more than one port, so a mistake
  cannot lock out every client.
- The profile uses a numeric `Endpoint` (hostname endpoints are refused by the
  controller today) and its `Address` prefix does not overlap the LAN.
- The protected prefix list is known, for example `192.168.20.0/24`.

## Steps and expected results

1. Create the profile and confirm it is stored:

   ```
   wr-vpn-profile create 1 wireguard < profile.conf
   wr-vpn-profile list
   ```

   Expected: `saved 1 <revision>` and one row for id 1. Exit code 0.

2. Preview before touching anything:

   ```
   wr-vpn-profile plan 1
   ```

   Expected: `apply=no-session` before the link exists, numeric `endpoints`,
   the addresses and DNS from the file, and no key material in the output.

3. Bring the profile up with the protected prefixes:

   ```
   wr-vpn-profile up 1 192.168.20.0/24
   ```

   Expected: `up 1 protocol=done addresses=done routes=done dns=done` (or
   `dns=empty` when the profile carries no DNS), exit code 0.

4. Confirm the routing stayed scoped:

   ```
   ip route show table 20001
   ip rule show
   ip -4 addr show dev wrvpn1
   ```

   Expected: the profile's routes only in table 20001; exactly one rule with
   `fwmark 0x57560001` pointing at that table; the profile's addresses on
   `wrvpn1`. The main table must not contain a default route through `wrvpn1`.

5. Confirm LAN access is intact:

   - the router answers on its LAN address from a wired client;
   - a client on a spare LAN port still reaches the WebUI;
   - `ping` to the LAN gateway still works from the router.

6. DNS only when opted in:

   ```
   nvram set wrvpn_use_dns=1; /usr/sbin/wr-vpn-profiles-service start
   cat /etc/storage/dnsmasq/wrvpn.servers
   ```

   Expected: `server=<profile dns>` lines and `127.0.0.1` still first in
   `/etc/resolv.conf`. With `wrvpn_use_dns=0` the file must be absent.

7. Tear down and confirm nothing is left:

   ```
   wr-vpn-profile down 1
   ip route show table 20001
   ip rule show
   ```

   Expected: `down 1 ok`, an empty table (or no such table), no rule with the
   profile mark, and the LAN still reachable.

## If something goes wrong

- Access lost on one port: move the cable to another LAN port; the profile never
  touches the LAN interfaces or the main table.
- Traffic still redirected: `wr-vpn-profile down <id>` removes the rule before
  the routes, so policy cannot outlive the interface.
- DNS broken: set `wrvpn_use_dns=0` and run the service again; it removes the
  aggregation file and reloads dnsmasq.

## Evidence to record

Command outputs from steps 1–7 with keys redacted, the contents of table 20001
before and after, `ip rule show`, the interface addresses, and the router's LAN
reachability from a client. Until that record exists, the profile stays
"implemented and CI-verified", not "verified on the device".
