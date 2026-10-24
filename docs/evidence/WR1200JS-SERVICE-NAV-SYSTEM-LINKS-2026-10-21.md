# WR1200JS service navigation — system-service links

The unified Services navigation previously linked Cron, Watchdog and LLTD
under System, but omitted direct controls for KMS activation and ASUS Info
Discovery. The WR1200JS build config selects `CONFIG_FIRMWARE_INCLUDE_VLMCSD=y`.
An available older ROMFS page (`artifacts-410/romfs-selected`) contains the
`vlmcsd_enable_on_of`, `lltd_enable_on_of` and `adsc_enable_on_of` control
anchors. Those are source/image inspection observations, not a verdict for a
newly built firmware image.

The navigation source now adds localized EN/UK/RU KMS and ASUS Info Discovery
links in System. KMS is conditional on its build selector; the existing LLTD
link is named explicitly so it is distinct from ASUS discovery. The prepared
source/image verifier requires both unconditional discovery links, a KMS link
exactly when selected, and validates every fragment against the target page.

Local navigation fixture, Python syntax, whitespace and older-ROMFS anchor
checks passed. The new final image, authenticated browser navigation, saved
flags versus observed processes, Apply behavior and on-router service responses
remain unverified. No router state was changed.
