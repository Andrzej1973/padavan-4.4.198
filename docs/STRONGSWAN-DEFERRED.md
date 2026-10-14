# StrongSwan/IPsec deferred from the WR1200JS profile

Owner decision, 2026-10-14: comment out `CONFIG_FIRMWARE_INCLUDE_SSWAN=y` for current WR1200JS test builds and finish this optional service during final firmware work. Keep its source, lifecycle candidate and tests for that later stage. It is not a current port acceptance requirement to complete or activate StrongSwan.

## Dependency findings

In the pinned Padavan source, `trunk/user/Makefile` selects the `strongswan` build directory directly from this selector. `shared/cflags.mk` adds `APP_SSWAN` separately. No StrongSwan-dependent rc/httpd/shared runtime path was found in the inspected source. WireGuard, AmneziaWG, ZeroTier, DoH/Stubby and Wi-Fi have separate selections and integration; none requires the StrongSwan daemon or its private libraries.

StrongSwan consumes shared cryptographic libraries; this does not make those libraries dependent on StrongSwan. The inherited `libs/libssl/Makefile` also adjusts its optional RC2 build flag based on the StrongSwan selector. Keep OpenSSL and the independently selected `CONFIG_FIRMWARE_INCLUDE_XFRM=y` intact. This change excludes the IPsec userspace package, not all kernel IPsec/XFRM facilities or general cryptography.

## Build and device scope

The normal build must accept the commented selector, reject an effectively enabled StrongSwan selector and reject its packaged commands/private libraries when it is excluded. Its positive packaging checker runs only when explicitly selected. Generated manuals include the StrongSwan chapter only for an enabled profile.

The next completed image must confirm exclusion and continued compilation of required features. No exact size or build-time saving is claimed before comparing built artifacts. This profile change does not stop processes, edit existing `/etc/storage/strongswan` files, change VPN tunnels or replace the currently installed router firmware.

Later work remains: managed lifecycle integration, explicitly selected autostart, validated profiles and credentials, firewall/persistence integration, translated capability-gated UI, actual SA/routing state and device acceptance. The current standalone controller is a candidate under isolated tests, not an installed operational service.
