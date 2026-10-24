# IoT Classic — navigation stage, 2026-10-20

## Owner requirement

IoT must work entirely within the original Classic theme. Add a third IoT
destination wherever Classic offers 2.4/5 GHz switching, retaining active
highlighting, navigation back, original styling, responsiveness and existing
Apply behavior. Modern is not a dependency and must not be introduced for
this task. Existing uncommitted changes are preserved. No full firmware
compilation or live router mutation is authorized for this initial stage.

## Inspected structure

Pinned source: vipshmily/padavan-4.4 at
`c25283e915a2a00a763774dd255b14aff997285e`.
Classic uses `trunk/user/www/n56u_ribbon_fixed`, shared `state.js`, Bootstrap
and `main.css`. `state.js` builds the shared radio shortcuts and sidebar.
The network map embeds `device-map/router2g.asp` and `router.asp`.
The Wi-Fi sections are paired pages: Wireless, WGuest, WMode, ACL, WSecurity
and WAdvanced. All twelve retain their original `tabMenu` and Apply forms.
The shared main-network implementation already owns the cross-band settings;
navigation must not write `wr_wifi_shared` or either band's settings.

## Implemented locally

`tools/iot/prepare-classic-navigation.py` installs a shared navigation asset
through Classic state.js, adds an IoT exit to each map radio panel, installs
the Classic IoT destination and EN/UK/RU status text. It checks source anchors
and destination collisions before writing. Repeated preparation rejects
instead of duplicating tabs. It does not overwrite any existing IoT page.

`classic-navigation.js` adds three standard `nav nav-tabs` links above the
existing section tabs on all twelve Wi-Fi pages. Switching between bands
preserves the section (Guest to Guest, Professional to Professional, etc.).
IoT links back to both main settings pages. It also adds a standard
`btn btn-mini` banner shortcut and a sidebar link. Active tabs use the
existing `active` class and `aria-current`. Navigation contains no settings
request, form submission or persistence mechanism.

The map's IoT link uses `target="_top"` to leave the embedded panel and
retain the full Classic shell and return paths. Existing Classic CSS,
radio forms, form action URLs and Apply handlers are not changed. No CSS,
new theme, Modern assets or new network settings writer is added.

## Actual checks

- `node --check tools/iot/classic-navigation.js`: passed.
- `node tools/iot/check-classic-navigation.js`: passed 14 route cases
  (12 Wi-Fi pages, IoT and index), destination and active state assertions,
  existing banner button preservation, sidebar and duplicate-mount checks.
  This uses an in-memory minimal DOM, not a rendered browser.
- Python AST parse of the preparer: passed.
- Preparation against the pinned Classic source tree: passed.
- All twelve prepared source pages retain `/start_apply.htm`, `tabMenu`
  and state.js; both map panels have exactly one top-level IoT exit; no
  Modern dependency appears in that fixture.
- A second preparation rejected with `Classic IoT navigation already
  installed`, as expected. This rejection is a negative check, not a failed
  first installation.

## Not complete / not claimed

The main firmware workflow currently excludes production IoT integration.
`tools/iot/activation.h` explicitly has no installed backend; existing
controller checks use injected operations. The saved request keys include
wr_iot_enable, wr_iot_ssid, wr_iot_psk and subnet/DHCP fields, but that does
not establish authenticated HTTP save/Apply, activation or isolation.

The new destination therefore displays a localized unavailable message.
It deliberately has no fake enable switch, password form, observed status
or Apply button. It is a navigation stage, NOT the requested complete IoT
implementation. The preparer is NOT inserted into the main build workflow
yet, so this interim page cannot silently ship as completed functionality.

Still required: production activation/rollback bindings; authenticated
validated settings using existing ASP/CGI/NVRAM conventions; default-off
third BSS, owned bridge, DHCP/DNS and IPv4/IPv6 isolation; real observed
status and QR; complete shell/target checks; rendered browser checks at
multiple widths; assembled image verification and supervised device tests.
Channel and width are shared with the physical 2.4 GHz radio, not independent
IoT controls. Preserve the current WPA2/AES backend contract rather than
inventing WPA3 support from the reference picture.

No full firmware build was started for this stage. No router configuration,
services, tunnel, radio state or firmware was changed.
