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
- The protected prefix list is known, for example `192.168.20.0/24`. IPv4 and
  IPv6 prefixes are accepted, comma-separated; spaces around a prefix are
  ignored. A malformed entry refuses the start instead of being skipped.

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

8. Confirm a rejected start leaves nothing behind:

   ```
   wr-vpn-profile up 1 192.168.20.0/24
   ip link show wrvpn1
   ip rule show
   ```

   Run this with a profile address inside the protected prefix. Expected:
   `addresses=conflict`, `cleanup=done`, exit code 8, no `wrvpn1` device and no
   rule with the profile mark. Repeat with an empty prefix argument: the same
   cleanup must run and the protocol must not be configured.

9. Edit only while stopped, and confirm the revision:

   ```
   wr-vpn-profile edit 1 < changed.conf
   wr-vpn-profile export 1
   ```

   Expected: `saved 1 <revision+1>` and the exported file contains the edit.
   Editing a profile that still has a runtime session must return code 4
   (`edit 1 live`) and leave the stored record unchanged.

10. Delete only after stopping, and confirm the tombstone:

   ```
   wr-vpn-profile delete 1
   wr-vpn-profile list
   ```

   Expected: `deleted 1 <revision>`; the profile is gone from `list`; a second
   `delete 1` returns code 5. Deleting a profile that still has a runtime
   session must return code 4 (`delete 1 live`) and leave it untouched.

## If something goes wrong

- Access lost on one port: move the cable to another LAN port; the profile never
  touches the LAN interfaces or the main table.
- Traffic still redirected: `wr-vpn-profile down <id>` removes the rule before
  the routes, so policy cannot outlive the interface.
- DNS broken: set `wrvpn_use_dns=0` and run the service again; it removes the
  aggregation file and reloads dnsmasq.

## Evidence to record

Command outputs from steps 1–10 with keys redacted, the contents of table 20001
before and after, `ip rule show`, the interface addresses, and the router's LAN
reachability from a client. Until that record exists, the profile stays
"implemented and CI-verified", not "verified on the device".
