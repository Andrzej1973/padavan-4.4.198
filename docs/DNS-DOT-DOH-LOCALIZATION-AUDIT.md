# DNS, DoT, DoH and service-page audit

Reviewed 2026-10-11 against the WR1200JS Linux 4.4.198 integration and the
read-only settings collected from this project's running Padavan 3.4 router.
The 4.4.198 firmware has not yet been re-flashed for runtime validation.

## Findings and changes

- The existing router's Stubby configuration uses three authenticated DoT
  resolvers: Google (`dns.google`, `8.8.8.8`), Cloudflare
  (`one.one.one.one`, `1.1.1.1`), and Quad9 (`dns.quad9.net`, `9.9.9.9`).
  The prepared 4.4 defaults previously contained only Google. The other two
  entries are now included as factory defaults so the service page is not
  empty after a clean install. Stubby remains disabled by default.
- DoT, DoH and Privoxy pages all used `show_menu(5,6,2)`. The pinned base's
  Services page uses `show_menu(5,7,2)`. Corrected the three custom pages and
  added image checks to prevent the wrong submenu landing again.
- DoH's dnsmasq integration printed `server=127.0.0.1#PORT\\n` with a literal
  backslash and `n` instead of ending the directive with a newline. Corrected
  the C escape and added a source check to the DoH image gate.
- DoT and DoH catalogues are installed as `/www/dot.json` and `/www/doh.json`.
  The image gates already check that these files exist and contain resolvers.
  The pages now report a missing/invalid catalogue visibly and retain manual
  provider entry; the DoT resolver list is still seeded from NVRAM defaults.
- New Stubby, DoH and Privoxy page strings are supplied in EN, UK and RU
  dictionaries. The build integrators append missing keys without overwriting
  existing base translations. Image checks ensure each custom page key exists
  in all three dictionaries.
- DoT and DoH router-DNS modes intentionally fail closed: they do not send
  plaintext DNS if the encrypted resolver is stopped or misconfigured. The
  translated page descriptions now explain this. Both service-enable defaults
  remain `0`; the DoH list defaults to Google HTTPS, but DoH itself stays off.

## DNSCrypt and source comparison

`CONFIG_FIRMWARE_INCLUDE_DNSCRYPT` remains commented in the WR1200JS build
config, as requested. The pinned Padavan base and the reviewed Nilabsent source
contain separate DNSCrypt support and a separate page; this port does not turn
DNSCrypt on or mix it with Stubby/DoH. It is an optional later choice, not a
prerequisite for either encrypted DNS service.

The Stubby package follows the official getdns/Stubby source recipe pinned in
`ports/stubby/PORT-CONTRACT.md`; DoH follows the preserved Nilabsent archive
recorded in `sources/https-dns-proxy.lock.json`. The current changes reuse the
existing target integration and resolver catalogues; they do not replace the
router's DNS architecture or import an unreviewed alternative DNS daemon.

## Verification still required

Local Python syntax and content checks pass for the changed integration and
image-verification scripts, locale-key coverage, menu indexes, DNS newline
escape and the three default resolver pairs. The next full GitHub build must
pass the Stubby, DoH and Privoxy image gates. Then test the UI, catalogue loads,
DNS resolution, service disable/re-enable, reboot and clock-synchronization
behavior on the router with a recovery path available. No router settings were
changed and no flash was performed during this audit.
