# WR1200JS device readiness and first Linux 4.4 validation

Updated 2026-10-13. A successful build does not establish a working device port.

## Current evidence and authorization

The latest independently downloaded and hashed artifact recorded here is test build 239, `WR1200JS_4.4.198.9-239_3d1e53b1.trx`, SHA256 `6a15fe74692c9896b32e965d3a445cbe4c3149705396f47d0b4c6c63dbc2317f`. See [build 239 evidence](evidence/WR1200JS-BUILD239.md) for profile/guide identity and exact verification limits. Builds 240–242 were still active on the latest check; obtain their current GitHub status and exact artifact identity before selecting a later candidate.

The user deferred installation and requested continued code work. Read-only SSH checks are authorized; flashing, rebooting and enabling disabled DNS services are not authorized by that instruction. Preserve the AmneziaWG tunnel. The latest SSH attempt to `192.168.20.1:22` timed out, so current physical runtime state has not been refreshed. Previous read-only observations on Linux 4.4.198 do not establish runtime behavior of the newly built images.

VPN handshake/interface observation, DNS process-state refresh and ZRAM swap-state refresh now have source/native/image evidence. They still require physical browser and router verification. Process presence does not establish DNS/TLS health; a handshake does not establish routing. Keep the full hardware/configuration/features checklist below open, including reboot persistence and sustained traffic stability. CAKE/SQM is excluded from the requested profile.

## Historical candidate identity — 2026-10-03

The completed reference run [37135784110](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37135784110) produced:
- `WR1200JS_4.4.198.9-100.trx`, 13,301,885 bytes.
- SHA-256 `2c81c722eda04d2b041d5ab630b6e31328b586ad955d02637781de6dcc953aff`.
- Combined archive artifact 11279750208, `padavan-4.4.198-router-downloads`.

See [build evidence](evidence/WR1200JS-BUILD-37135784110.md). These hashes refer to that exact run, not later images sharing its filename. Later commits change initial Privoxy editor rendering and add the FN1 Device Tree node. Runs 37139023256 and 37139282570 were still in progress when this document was prepared; their images must be checked separately.

## Historical access constraints — 2026-10-03

At that observation the router ran the user's working Padavan 3.4 firmware. Access was through an AmneziaWG tunnel; Breed was installed, but physical access and a recovery operator were unavailable. This is historical context, not a current access assessment. Before an authorized installation, establish the actual recovery route and preserve firmware, settings and tunnel configuration privately.

## Read-only baseline report

Use [tools/collect-wr1200js-readiness.sh](../tools/collect-wr1200js-readiness.sh) through the established SSH connection and redirect stdout to a file on the computer. The script only reads runtime state. It does not export NVRAM, dump VPN keys, write GPIOs, mount debugfs, restart services or reboot.

It collects the kernel version, partitions, RAM, routes/interface counters, wireless interfaces, loaded modules, CPU/interrupt/slab state, service process IDs, Device Tree identity/button properties, existing LED brightness/triggers and existing GPIO debug ownership. Missing Device Tree nodes on the old 3.4 firmware are expected and do not establish a hardware fault. Raw GPIO cells are shown as big-endian bytes, not guessed GPIO numbers.

Review reports before sharing: IP/MAC addresses and kernel logs may contain private information. The script has not yet been run on the user's router.

Diagnostic follow-up, 2026-10-13: the collector now uses the router-supported `type` check, includes `/proc/swaps`, reads only the three requested enable switches `stubby_enable`, `doh_enable` and `zram_enable`, and identifies active global custom DNS lines for localhost ports 5453/65053 without printing domain lists or annotations. [CI 38439347604](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38439347604) passed shell syntax and execution of the actual AWK filter for comments, exact ports and unrelated directives. This does not test the script under the installed router shell. The latest attempted collection exited SSH 255 because connection establishment timed out; no runtime report or router change resulted.

## Hardware checks after installation with recovery available

1. Record exact TRX checksum, effective firmware/kernel configs and build commit.
2. Confirm Linux 4.4.198, WebUI/SSH, WAN IPoE, LAN and retained settings.
3. Confirm AmneziaWG restores access, routes and DNS using the existing profile.
4. Verify both radio bands and calibrated MAC addresses. Save boot logs and logs/counters after sustained Wi-Fi traffic. Compilation does not prove the kthread/HWNAT problem resolved.
5. Verify wired routing/NAT and the actual selected acceleration mode separately from Wi-Fi. Confirm retained configuration, DHCP/DNS, backup/restore controls and management access under traffic; do not infer driver support from a visible switch.
6. Confirm reset/WPS/FN1 detection and configured actions with an operator present. Do not test reset or destructive button actions remotely.
7. Confirm power/USB indicators and settings; inspect GPIO6 separately.
8. Verify WPAD PAC handling, Stubby and optional Privoxy editor/save/start/stop behavior. The Privoxy first-enable fix requires an actual browser and LAN-client check.
9. Perform reboot persistence and load/latency checks only with a reachable recovery route.

## GPIO source findings

The pinned 4.4 source discovers button capabilities through `/sys/firmware/devicetree/base/gpio-keys-polled`, not the old board.h GPIO defines. Its gpio-button-hotplug driver maps `KEY_FN_1` to `BUTTON=fn1`, consumed by rc/gpio_btn.c. Commit 684c2f03245968b0d3fe956751f2a5ee14f5d472 adds the previously missing GPIO18 FN1 node; physical polarity and functionality remain unverified.

Power GPIO7 and USB GPIO8 have labels `power` and `usb`, matching the shared LED control names. GPIO6 has label `blue:internet`, absent from that shared lookup. It has not been renamed or assigned new behavior without evidence about its intended function.
