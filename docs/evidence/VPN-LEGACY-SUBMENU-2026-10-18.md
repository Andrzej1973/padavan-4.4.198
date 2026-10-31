# Legacy VPN submenu correction — 2026-10-18

The user reported that the ZeroTier page showed tabs for ZeroTier and the
misspelled `WIREGUAED`, while the second tab opened an older WireGuard-only
form with blank fields and no visible protocol choice.

## Source finding

The inherited `Advanced_zerotier.asp` and `Advanced_wireguard.asp` pages share
the submenu key `menu5_35_1`. Both linked that tab to `Advanced_wireguard.asp`.
The firmware already has the separate client/profile manager at `vpncli.asp`,
where each saved profile has an explicit WireGuard or AmneziaWG protocol
selector. The old simplified form is not that manager and its blank fields are
not evidence that the profile service is unavailable.

## Source change

`tools/services-nav/prepare-unified-nav.py` now retargets the shared legacy VPN
tab to `/vpncli.asp`, labels it “WireGuard / AmneziaWG profiles” in EN/UK/RU,
and injects the existing shared service navigation into the old
`Advanced_wireguard.asp` page. The selected-tab styling is removed from that
old page because its WireGuard submenu entry now navigates elsewhere. The old
form remains reachable and retains its existing warning/link to the full
profile page. The ZeroTier tab remains linked to its own page.

Review of the pinned base dictionaries found that upstream `EN.footer` defines
`menu5_35_1=WIREGUAED` twice. The previous preparation code rejected duplicate
definitions and would stop before a firmware build. It now replaces the first
entry (the one used by httpd) and removes subsequent copies; UK/RU keys are
inserted when absent. The local fixture covers duplicate normalization, stale
first-match rejection and the exact final dictionary contract. See the pinned
[upstream EN.footer](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/www/dict/EN.footer).

No tunnel profile, saved setting, router state, or service lifecycle was
changed. This is a source-level navigation correction only; no build or
browser-on-device verification was performed. The final-ROMFS verifier now
also checks the inherited ZeroTier/WireGuard submenu points to `/vpncli.asp`,
rejects the old single-protocol destination and stale active-tab styling, and
requires one exact EN/UK/RU dictionary value. A source review of pinned upstream
`ej.c` at `c25283e915a2a00a763774dd255b14aff997285e` showed dictionary lookup
returns the first matching entry (`strncmp` followed by `break`), so checking
only the last duplicate could falsely pass while the router still displayed
`WIREGUAED`. The verifier and fixture now reject a stale first value and every
duplicate, even when a later entry is correct. This catches the runtime lookup
semantics rather than merely inspecting the file's final line. The gate and
fixture changes are local and still need a new CI image. Complete profile
editing and runtime acceptance remain separate open work.

Source reference: [pinned upstream `ej.c`](https://github.com/vipshmily/padavan-4.4/blob/c25283e915a2a00a763774dd255b14aff997285e/trunk/user/httpd/ej.c).

## Existing target-page image evidence — build 478

Build #478 (run `39139346947`, commit `d1dc0eb`) independently confirms that
the target `/vpncli.asp` exists in final ROMFS with the WireGuard/AmneziaWG
protocol selector and profile controls. Its route audit also passed for all
256 served `/www` files against the effective httpd handler table. This proves
the destination page is packaged and routed in that image. Build #478 predates
the submenu retarget and label correction, so it does not prove the old tab
points there; the new submenu verifier is not yet in an image. Router-browser
click-through remains unverified.
