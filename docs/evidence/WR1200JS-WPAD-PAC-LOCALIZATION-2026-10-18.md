# WR1200JS WPAD/PAC behavior and localization checkpoint

Date: 2026-10-18.

## Source behavior

The WR1200JS WPAD editor stores its PAC text in `/etc/storage/wpad.dat` and
serves that file as `/wpad.dat`, `/wpad.da` and `/proxy.pac` when the optional
WPAD selector is included. The initialization path creates a `DIRECT` PAC only
when no stored file or symlink exists, preserving an existing user file. The
current integration does not advertise a PAC URL through DHCP or DNS; clients
must be configured manually. This is different from automatic WPAD discovery.

The editor remains gated by the image capability and AP mode, and its form
input remains guarded by `login_safe()`. These checks concern source and
packaging behavior; they do not prove successful authenticated saving from a
browser.

## Localization and guide correction

The editor help is now supplied through `WRWpadHelp` in EN, UK and RU. Its text
identifies the served URLs, says that DHCP/DNS do not advertise them, and tells
the user to configure clients manually. The image verifier checks language-
specific phrases as well as the PAC URLs and DHCP/DNS references, so an English
fallback in UK or RU fails the gate.

The generated model guide was corrected to describe PAC hosting rather than
claim automatic proxy discovery. `SETUP_WR1200JS.txt` was regenerated from
`configs.build/wr1200js.config`; `tools/check-router-guide.py` passed. The
Markdown and plain-text guide here are generated source outputs, not proof that
they are present in a published firmware ZIP.

## Evidence boundary and remaining checks

- **Source:** the integration and translation inputs now state the same
  no-auto-advertisement behavior.
- **Local validation:** guide generation and the guide consistency checker
  passed after regeneration.
- **Image/CI:** the language-specific verifier change has not yet run in a
  workflow image. Build #479 was already running before this local edit and
  therefore does not include it.
- **Runtime:** no client auto-discovery, PAC fetch, authenticated save, reboot
  persistence or proxy-routing behavior was tested on the router. No router
  settings were changed.
