# WR1200JS device readiness and first Linux 4.4 validation

Updated 2026-10-03. A successful build does not establish a working device port.

## Candidate identity

The completed reference run [37135784110](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/37135784110) produced:
- `WR1200JS_4.4.198.9-100.trx`, 13,301,885 bytes.
- SHA-256 `2c81c722eda04d2b041d5ab630b6e31328b586ad955d02637781de6dcc953aff`.
- Combined archive artifact 11279750208, `padavan-4.4.198-router-downloads`.

See [build evidence](evidence/WR1200JS-BUILD-37135784110.md). These hashes refer to that exact run, not later images sharing its filename. Later commits change initial Privoxy editor rendering and add the FN1 Device Tree node. Runs 37139023256 and 37139282570 were still in progress when this document was prepared; their images must be checked separately.

## Current access constraints

The router runs the user's working Padavan 3.4 firmware. Access is through an AmneziaWG tunnel; Breed is installed, but physical access and a recovery operator are unavailable. No flash operation or reboot is performed by this procedure. Before a first 4.4 installation, establish an actual recovery route and preserve the current firmware, settings and tunnel configuration privately.

## Read-only baseline report

Use [tools/collect-wr1200js-readiness.sh](../tools/collect-wr1200js-readiness.sh) through the established SSH connection and redirect stdout to a file on the computer. The script only reads runtime state. It does not export NVRAM, dump VPN keys, write GPIOs, mount debugfs, restart services or reboot.

It collects the kernel version, partitions, RAM, routes/interface counters, wireless interfaces, loaded modules, CPU/interrupt/slab state, service process IDs, Device Tree identity/button properties, existing LED brightness/triggers and existing GPIO debug ownership. Missing Device Tree nodes on the old 3.4 firmware are expected and do not establish a hardware fault. Raw GPIO cells are shown as big-endian bytes, not guessed GPIO numbers.

Review reports before sharing: IP/MAC addresses and kernel logs may contain private information. The script has not yet been run on the user's router.

## Hardware checks after installation with recovery available

1. Record exact TRX checksum, effective firmware/kernel configs and build commit.
2. Confirm Linux 4.4.198, WebUI/SSH, WAN IPoE, LAN and retained settings.
3. Confirm AmneziaWG restores access, routes and DNS using the existing profile.
4. Verify both radio bands and calibrated MAC addresses. Save boot logs and logs/counters after sustained Wi-Fi traffic. Compilation does not prove the kthread/HWNAT problem resolved.
5. Verify USB and required existing services, including VLMCSD.
6. Confirm reset/WPS/FN1 detection and configured actions with an operator present. Do not test reset or destructive button actions remotely.
7. Confirm power/USB indicators and settings; inspect GPIO6 separately.
8. Verify WPAD PAC handling, Stubby and optional Privoxy editor/save/start/stop behavior. The Privoxy first-enable fix requires an actual browser and LAN-client check.
9. Perform reboot persistence and load/latency checks only with a reachable recovery route.

## GPIO source findings

The pinned 4.4 source discovers button capabilities through `/sys/firmware/devicetree/base/gpio-keys-polled`, not the old board.h GPIO defines. Its gpio-button-hotplug driver maps `KEY_FN_1` to `BUTTON=fn1`, consumed by rc/gpio_btn.c. Commit 684c2f03245968b0d3fe956751f2a5ee14f5d472 adds the previously missing GPIO18 FN1 node; physical polarity and functionality remain unverified.

Power GPIO7 and USB GPIO8 have labels `power` and `usb`, matching the shared LED control names. GPIO6 has label `blue:internet`, absent from that shared lookup. It has not been renamed or assigned new behavior without evidence about its intended function.
