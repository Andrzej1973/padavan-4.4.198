# Band Steering lifecycle integration findings

Pinned source: vipshmily/padavan-4.4 c25283e915a2a00a763774dd255b14aff997285e.

## Verified candidate package

Run37209589878/job111457859216 completed successfully. Actual log reports PASS two MIPS package binaries staged without startup hooks; the same job reports real client/server status and stop acknowledgement PASS. The Makefile builds wr-band-steering and wr-band-steering-ctl and stages exactly those binaries. No production user/Makefile registration or startup hook is installed; no router runtime operation is proven.

## Source paths requiring coordinated lifecycle

- net_wifi.c restart_wifi_wl (717): stops the 5 GHz services/interfaces, regenerates only the 5 GHz profile when need_reload_conf is set, then starts its AP/WDS/AP-client and 802.1X. Cross-band paths are conditional on MT7615/MT7915 DBDC, not the WR1200JS MT7603/MT7612 pair.
- net_wifi.c restart_wifi_rt (764): analogous 2.4 GHz-only profile refresh.
- rc.c initial profile generation (723-724): generates both profiles.
- rc.c shutdown path (840-841): stops both Wi-Fi interfaces.
- rc.c service-event profile generation (1431/1435): independent band refresh paths also need inspection and service coordination.

Therefore adding a simple daemon start after a single restart callback does not establish correct lifecycle. The profile compatibility callback evaluates current NVRAM, while one installed driver profile can still reflect previous settings. Both profiles and both radio initialization states must agree before enabling the daemon.

## Required integration behavior

Retain the normal separate-band paths unchanged while the feature is disabled. With steering selected: serialize settings apply and service activation through rc; request coordinated stop and observe completion before any participating profile/interface changes; treat a STOP acknowledgement as a request only. Missing/dead control endpoint is not proof of driver OFF. Check owner lock and driver state, and define bounded recovery using actual supported reinitialization paths if OFF cannot be established.

Validate main credentials and current AP/radio eligibility for both bands; generate both profiles from one coherent settings snapshot; exclude guest BSS; reinitialize participating radios in the required order; establish listener/owner/daemon startup and await driver ready/enabled responses. On failure keep truthful error state and perform documented cleanup without falsely reporting disabled radios. Audit scheduling, shutdown, radio enable/disable, AP-client changes and independent restart event paths. Preserve unrelated LAN/WAN/VPN settings and existing defaults.

The new feature must remain factory-off. A disabled build must not depend on daemon binaries. Final production inclusion must bundle patched drivers, rc helper, generated ABI layout, daemon, client, lifecycle and capability-gated WebUI together; a passing isolated package build is insufficient. Actual device acceptance is still required.
