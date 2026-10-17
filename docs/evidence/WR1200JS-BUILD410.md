# WR1200JS build 410 — CI evidence

Verified 2026-10-17 through the authenticated GitHub API.

- Run: https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39068280936
- Commit: `03eb3dad64d8becc0e734b307965cd82e00594c5`.
- Run and WR1200JS build job `117500417015`: completed, success.
- Build job completed at `2026-10-17T21:00:39Z`.
- Firmware ZIP and download-index jobs also completed successfully.

The build job log records successful final ROMFS checks at 20:59:42 UTC:
`www/vpncli.asp` contains `<% wr_vpn_profile_rows(); %>` and
`wr_vpn_action.cgi`; compiled `usr/sbin/httpd` contains both handler/route
names. These checks occur after compilation and all page-copy operations.
This confirms the missing-table packaging regression is covered in staged
ROMFS. It does not prove that the browser renders it correctly on the router.

The same log reports successful unified service navigation EN/UK/RU checks,
the exact target BusyBox VPN service lock fixture, packaged MIPS WG/AWG parser
fixtures, and the shipped manager storage/export/revision tests under
QEMU/PRoot. These are CI checks, not physical VPN lifecycle acceptance.

Published, non-expired artifacts observed through the API:

- `WR1200JS_4.4.198.9-410_03eb3dad_TEST`, ID `12114307586`, 12,570,134 bytes.
- `padavan-linux-4.4.198-wr1200js`, ID `12114512059`, 12,611,659 bytes.
- `vpn-profile-image`, ID `12114193211`, 2,700 bytes.
- `target-busybox-audit`, ID `12114546891`, 4,333 bytes.

## Downloaded artifact verification

Downloaded the firmware distribution, firmware ZIP contents, configuration
report, VPN profile reports and target BusyBox reports with `gh run download`.
The downloaded TRX is 12,608,787 bytes, SHA-256
`6bcd107e894eebe458397299fba76b95b0bf971045a646c6d63ee5a1629bff1d`.
Running `overlay/padavan-4.4/scripts/verify-wr1200js-image.py` locally passed
all six structure checks; its report is `WR1200JS-BUILD410-STRUCTURE.json`.
Size and hash equal the independently downloaded CI image report.

The config report has 112 verified options (110 config and two kernel
selection checks), zero mismatches and zero pending options. The distributed
`wr1200js.config` matches `firmware-requested.config` by SHA-256:
`097785f7be4543245ceefd744e591b8ecd21ef8898522a0c1a469569ca409e5d`.
Both requested Shadowsocks client flags SSREDIR and SSLOCAL are enabled.

The distributed `SETUP_WR1200JS.txt` matches the main artifact's guide:
SHA-256 `fb906f61fc8332400d6865b9b95dc55c2b8439edfb84546f44f66ace319333c3`.
It identifies build 410/03eb3dad and includes 100/300/1000 Mbit network
scenarios and service instructions. The guide report lists 17 guided services.
This verifies inclusion and identity, not that every instruction has been
validated on the physical router.

No flash, reboot, service restart, or live tunnel change was performed.
## Independent final SquashFS inspection

7-Zip 26.00 identified the final TRX SquashFS 4.0/XZ at byte offset 1,981,488
and extracted selected VPN files followed by the complete `www` directory.
Eight assertions on the extracted files passed: table call and action URL in
vpncli.asp; table handler and action route in compiled httpd; client and server
protocol selectors; exact QR renderer and service script bytes against the
checkout. File hashes and these checks are recorded in
`WR1200JS-BUILD410-ROMFS.json` (selected-file snapshot).

Running `tools/services-nav/prepare-unified-nav.py --verify-image` against
the independently extracted web directory and distributed configuration also
passed: navigation destinations exist and EN/UK/RU labels are present.
This closes the final-image packaging check for the overwritten VPN table;
it does not validate browser rendering, authorization or live tunnel actions.

Browser/device runtime acceptance remains open.
The BusyBox report explicitly marks whole-service interaction audit and
physical runtime as incomplete.
