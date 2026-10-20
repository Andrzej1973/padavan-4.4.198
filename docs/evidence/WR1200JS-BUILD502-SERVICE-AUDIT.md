# WR1200JS build #502 — service/WebUI image checkpoint

GitHub Actions [build #502](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39459625545)
completed successfully on 2026-10-20 for PR source commit
`be140259c6bf65663c378408dd104f60c3009923`. The firmware build job completed,
the selected-board requirement passed, and the firmware/config download package
was uploaded. The run published the `padavan-linux-4.4.198-wr1200js` artifact
(ID `12283716068`) and `padavan-4.4.198-router-downloads` artifact
(ID `12283216992`).

## Item 4 service/WebUI evidence from the final image

The build job passed these relevant final-ROMFS checks:

- Unified service navigation: routes, pages and EN/UK/RU labels.
- Shadowsocks: no CJK UI text in the final page and matching EN/UK/RU keys.
- Administration backup/restore: menu route, `login_safe()` gate, action rows,
  linked handlers, locale keys, browser-harness form behavior and flash-save
  success/error feedback.
- Target BusyBox: image-specific audit gate, VPN/USBIP target-shell fixtures,
  MIPS VPN profile manager probes and the shipped USB/IP settings page checks.
- Stubby: ROMFS/dependency checks and an authenticated DNS-over-TLS resolution
  through the image binaries under QEMU.
- iPerf3: status page, HTTP handler and EN/UK/RU labels. The report explicitly
  leaves an actual client run and throughput unverified.
- KMS and Watchdog: final-ROMFS status rows, handlers and EN/UK/RU help;
  activation and hardware timer servicing remain unverified.
- StrongSwan: the disabled profile and final-ROMFS exclusion check passed, and
  `strongswan-image-checks` was uploaded (ID `12282019711`). This closes the
  missing exclusion-report issue found in build #501.
- WebUI route coverage: all 247 served `/www` files matched effective httpd
  routes. The WAN, ZeroTier and RSSI image verifiers also passed.

## Earlier failed build and correction

Build #500 failed compiling MT76X3 `ft_tlv.c`: `FT_IGTK_ID` was undeclared in
`FT_FTIE_InsertIGTKSubIE`. The follow-up source change
`560ee18` guards the FT IGTK helper by PMF support; builds #501 and #502 then
completed successfully. The separate EoIP report-upload step also lacked a
report after the compile failure, but that was a consequence of the aborted
build, not another compiler error.

## Acceptance boundary and remaining work

These results establish CI build and selected final-image checks only. They do
not establish physical browser rendering, successful Apply/save on the router,
service start/stop behavior, live protocol health, storage/flash recovery or
reboot persistence. The overall target BusyBox/service audit remains open, as
do the affected service-by-service runtime checks. No router state was changed
for this build.

At this checkpoint, builds #503 and #504 were still running. Their results are
not implied by build #502 and must be recorded separately.
