# WR1200JS unsupported VPN choices in the service UI — 2026-10-20

## Finding

The WR1200JS profile excludes PPTP, standalone L2TP and OpenVPN. The inherited
VPN client and server pages nevertheless contained PPTP and L2TP choices. Their
OpenVPN fallback removed the third option by numeric position, which becomes
incorrect once the unsupported legacy entries are removed.

## Source correction

`tools/vpn-profiles/prepare-web.py` now removes the PPTP and standalone L2TP
options from both `vpncli.asp` and `vpnsrv.asp` after the board's page copies.
The transform fails closed if either expected option changes or is missing.
The inherited OpenVPN capability gate now removes option value `2` by value
rather than by position, preserving the intended behavior after list changes.
The supported WireGuard/AmneziaWG option remains.

`tools/vpn-profiles/check-web.py`, already run by the WR1200JS build workflow
after page preparation, checks both transformed pages, verifies that the
unavailable choices are absent and the WireGuard/AmneziaWG choice remains, and
exercises the transform on an in-memory fixture.

## Verification and limits

- Python syntax compilation passed for the transformer and checker.
- An in-memory fixture confirmed PPTP/L2TP removal, preservation of OpenVPN
  and WireGuard entries before capability gating, and fail-closed behavior when
  the template no longer contains the expected legacy options.
- The same transform was applied in memory to both current board page sources;
  unsupported choices were absent and the value-based OpenVPN gate and
  WireGuard/AmneziaWG option remained.
- `git diff --check` passed for the changed source files.

The final ROMFS check and browser rendering await a completed firmware build.
This source change does not modify the VPN backend, saved configuration,
service lifecycle or router state. It does not establish VPN runtime behavior.
