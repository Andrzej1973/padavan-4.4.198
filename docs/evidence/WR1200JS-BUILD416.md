# WR1200JS build 416 evidence

Run: https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39071330705
Commit: `a5e590ba4e952979685b88de90b6b4b727adf4ca`.
All four jobs completed successfully: selection, WR1200JS build
(`117509432967`), downloads and firmware ZIP.

Downloaded distribution artifact `WR1200JS_4.4.198.9-416_a5e590ba_TEST`
contains TRX, requested configuration and SETUP_WR1200JS.txt.
TRX is 12,611,207 bytes, SHA-256
`d9a8da360ba990f226afe3facb06e111d797f8a6d906c9c040ddfb2ee337ddc1`.
The local uImage checker passed six checks; see
`WR1200JS-BUILD416-STRUCTURE.json`. The downloaded config report covers 112
options, with zero mismatches and zero pending options.

7-Zip independently extracted vpncli.asp, httpd and engage.itoggle.css from
the final TRX. Seven checks passed: exact shared green-ON rule once, retained
original OFF sprite, create form, create request URL, compiled create route,
stored-profile table and save-only `started:false` response. Hashes and checks
are in `WR1200JS-BUILD416-ROMFS.json`.

Component CI for creation (`39070916624`) and its actual-JS follow-up
(`39071062648`) completed successfully. They cover boundary/fixture behavior,
not physical tunnel acceptance. Firmware builds 412–415 also completed
successfully when queried during this check.

The user disconnected the management tunnel. No SSH, flash, restart or
router mutation was attempted during this artifact check. Browser appearance,
real HTTP-to-manager integration, new-profile persistence and concurrent
physical WG/AWG runtime acceptance remain unverified. Green toggle color
represents a selected setting, not a daemon-health observation.
