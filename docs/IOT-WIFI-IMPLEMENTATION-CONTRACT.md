# WR1200JS separate IoT Wi-Fi implementation contract

Staging update, 2026-10-18: `45ff19b` reads back all six temporary credential
and address fields after clearing, in addition to the three service gates.
ABI run `39114413340` passed the host sanitizer fixtures and MIPS compilation;
the downloaded `iot-request-stage.txt` confirms PASS. Six injected setters that
return success without changing a clear destination are refused. This does not
enable production activation. Snapshot guard revalidation in `b65acf6` is
still awaiting its own ABI result (`39114663222`).

Approved 2026-10-08. Source inspected at vipshmily/padavan-4.4 commit `c25283e915a2a00a763774dd255b14aff997285e`. This is an implementation contract and partial source audit, not device support proof.

## Current constraints

`trunk/user/rc/ralink.c` declares `i_fphy[2]` and `i_val_mbss[2]` and sets `i_ssid_num = 2` (main plus guest). It emits two-entry NoForwarding, NoForwardingMBCast, HideSSID and HT_MCS lists, and individual guest SSID/password fields. Raising BssidNum alone leaves profile fields incomplete and may introduce out-of-bounds accesses if loops are generalized.

`trunk/user/rc/net_wifi.c` explicitly starts/stops main and guest interfaces and adds the guest interface to `IFNAME_BR`. A third IoT interface needs its own lifecycle and bridge attachment. Existing guest isolation is not evidence of a separate IoT subnet.

Both driver families expose MBSS profile parsing and virtual-AP initialization. Their headers select `MAX_MBSSID_NUM` from chip capability only under `MBSS_SUPPORT`; otherwise it is 1. Beacon array capacity is not proof of effective chip capacity. Trace MT7603E and MT7612E capability initialization and actual build definitions, including AP-client/repeater reservations, before selecting an interface index or advertising three simultaneous SSIDs.

## Required implementation

1. Preserve main and guest network settings. IoT uses a third BSS, initially 2.4 GHz; shares the physical radio channel and width constraints.
2. Extend every relevant profile field consistently: SSID, authentication, cipher, PSK, isolation, hidden status, rate policy and other per-BSS settings. Default OFF retains the existing two-BSS profile where possible.
3. Create an isolated IoT bridge, non-overlapping subnet and scoped DHCP/DNS configuration. Start/stop the third interface with radio and network lifecycle; never attach it to the primary LAN bridge as a convenience.
4. Integrate IPv4 and IPv6 firewall policy, blocking primary-LAN and router-administration access by default while explicitly permitting DHCP/DNS and requested internet traffic. Evaluate hardware offload paths so isolation cannot be bypassed.
5. Add authenticated WebUI enable, SSID/security/password, subnet/status, local QR and explicit controller exceptions. Default WPA2-Personal/AES, runtime OFF. Discovery/mDNS and client isolation require deliberate policies compatible with the user's IoT devices.
6. Verify actual target compilation, image assets, lifecycle and persistence, followed by device tests with primary, guest and IoT simultaneous. Verify DHCP, DNS, inter-network isolation, allowed exceptions, restart behavior and AP-client/repeater compatibility separately.

## Evidence still missing

Effective per-chip third-BSS capacity, complete profile/lifecycle integration, isolated subnet/firewall, WebUI, target build and live-device behavior remain unverified. No router configuration changes are authorized by this audit.

Update 2026-10-18: build #451 run `39114348390` passed the production
Kbuild capacity gate. Downloaded original reports are preserved as
`evidence/WR1200JS-BUILD451-IOT-MT7603.json` and
`evidence/WR1200JS-BUILD451-IOT-MT7612.json`. Both effective commands enable
MBSS. MT7603 has a source/configuration limit of 16; MT7612 has 8 (array
ceiling 16, chip limit 8). The required 2.4 GHz three-BSS source gate passed.
This supersedes the missing effective-source-capacity item above. Both reports
retain `runtime_verified: false`; production activation, live third BSS and
physical isolation/lifecycle acceptance are still missing. Full build #451
was still active when the gate and downloaded reports were inspected.


## Capability initialization traced — 2026-10-08

MT7603 `mt7603_chip_init` calls `mt_bcn_buf_init`; the latter assigns BcnMaxHwNum=16 and BcnMaxNum=16. The header may reduce the array ceiling to 8 under ECONET_ALPHA_RELEASE, which still exceeds three; confirm effective definitions in a target probe.

MT76x2 initialization calls `rlt_bcn_buf_init`. Its MT76x2 branch assigns hardware beacon count 8. With APCLI_SUPPORT it sets BcnMaxNum to 8 minus MAX_MESH_NUM; the inspected header defines MAX_MESH_NUM as 0. This gives a source-level candidate capacity of eight, not proof of eight working networks.

The effective kernel configuration downloaded from successful WR1200JS run 37823022372 enables CONFIG_MT7603E_MBSS_SUPPORT and CONFIG_MT76X2_AP_MBSS. Effective driver preprocessing, target capacity probes and a third-BSS device test remain required. No production profile has been changed by this audit.

## Lifecycle integration requirements — 2026-10-08

Pinned-source follow-up, 2026-10-18: MT7603
`os/linux/rt_main_dev.c` calls `rt28xx_init` and then `RT28xx_MBSS_Init` in
the main-interface open path. RC `restart_wifi_rt` stops the radio interfaces,
regenerates the 2.4 GHz profile when requested, and reopens main/guest through
`start_wifi_ap_rt`. Merely editing BssidNum or administratively opening an
already-existing ra2 is not evidence that the new virtual interface was created.
The production activation backend must integrate the profile/radio reopen and
observe ra2 identity afterward, retaining the original main/guest profile for
recovery. Existing IoT quiesce hooks clear temporary gates during ordinary
restart; calling that restart blindly inside activation would invalidate staged
state. This interaction still needs a dedicated coordinated activation path.
`594d98b` supplies only the owned-bridge administrative BSS-UP primitive and
host-kernel tests; it does not supply that radio reload/activation path.

The pinned `stop_wifi_all_rt` stops the AP-client, four WDS interfaces, guest and main BSS explicitly. It does not stop a third BSS. `start_wifi_ap_rt` attaches main and guest to `IFNAME_BR`; inserting IoT into this existing bridge loop would violate the isolated-subnet requirement. Radio scheduling, manual radio control, profile regeneration and full LAN restart must all quiesce IoT explicitly.

Activation order:

1. Serialize configuration/profile generation and validate effective router/radio mode, credentials, complete active-subnet inventory, interface identity and ownership. An existing unrelated `br-iot` must cause rejection.
2. Stop and detach the third BSS before changing its profile or network. Confirm it is down; abort on failure.
3. Prepare the complete profile, create/verify the owned IoT bridge with its address, and install IPv4/IPv6 isolation before the BSS can carry traffic.
4. Rebuild DHCP/DNS while retaining main-LAN settings. IoT DHCP must set the existing service's DHCP-used flag even when main-LAN DHCP is disabled. Check configuration and service startup.
5. Attach only the third BSS to the IoT bridge, then enable it. Report active only after interface/bridge/service/firewall observations succeed.

Failure and shutdown order:

- Disable the third BSS first, then detach it. If either fails, retain isolation rules and report failure; do not remove guards from a potentially live interface.
- Rebuild the shared DHCP configuration without IoT, preserving LAN DHCP/DNS. Remove only resources positively owned by IoT.
- Firewall reload, WAN changes and DHCP restart must regenerate the IoT policy before generic accept rules, including the default filter builders and the case where the main firewall is disabled.
- Do not enable IoT in AP-client-only, WDS-only or radio-off modes. Repeater/AP-mode support requires a separate decision and evidence; reject unsupported combinations clearly.

Host evidence so far: run 37832869879 verifies eight IPv4 TCP checks, including WAN replies, LAN/router isolation and blocking a preexisting LAN connection with generic ACCEPT policies. It does not prove production lifecycle, DHCP lease transactions, Wi-Fi driver behavior or target-device runtime. Extended UDP/IPv6 checks are pending.

## Expanded IPv6 isolation packet matrix — 2026-10-18

The disposable host-kernel packet fixture now creates separate IoT, LAN and WAN
IPv6 prefixes and first proves that its TCP/UDP baseline routes work. After
loading the generated IPv6 filter rules it checks router INPUT and forwarded
traffic over TCP and UDP, including IoT-to-LAN/WAN and unsolicited LAN/WAN-to-
IoT paths. The existing IPv4 TCP/UDP and DHCP source-port checks remain in the
same fixture. This is a stronger regression gate for the current policy, which
blocks all IoT IPv6 traffic, but does not implement IPv6 internet access or
prove target-kernel, production-lifecycle, Wi-Fi, or physical-router behavior.
Local Python syntax validation passed; the privileged namespace test requires
Linux CI. The first run, `39102134653`, failed before applying any firewall
rules because the fixture passed an unnecessary fourth argument to its TCP
server helper. The original job log and `build_log.nim` triage confirm this
test-harness error. After that call was fixed, rerun `39102351326` reached the
IPv6 topology baseline but failed connecting from IoT to the LAN TCP listener
(`fd51::2:8082`), still before firewall rules were loaded. The failure is in
test routing setup, so it proves neither a policy pass nor a policy defect.
The fixture now enables forwarding on each routed interface explicitly and
prints route/address/neighbour/sysctl diagnostics if a baseline path fails.
ABI run `39103063444` stopped before the packet test because `sysctl`
interpreted the dot in interface name `eth2.2` as a path separator. The fixture
now writes and reads the exact `/proc/sys/net/ipv6/conf/eth2.2/forwarding`
path. This correction was published as `770a7c5`. ABI rerun `39103236496`
passed setup and policy preparation but failed before firewall installation:
the IoT namespace could not reach the LAN IPv6 listener. The original job log
was reviewed with `build_log.nim`; this is a host-test baseline failure, not
evidence for or against the firewall policy. Routes and forwarding were present;
after the failed connect, diagnostics showed the LAN address/MAC in bridge FDB
and `fd51::2 REACHABLE`, so an absent NDP response alone does not explain the
missing TCP reply. Diagnostics now also capture the reverse route, LAN IPv6
listener via `ss`, and the pre-firewall FORWARD table. No IPv6 packet-policy
conclusion is established yet.

## Source-level radio capacity diagnostic — 2026-10-18

The WR1200JS build workflow now has a diagnostic step after the production
build that records separate MT7612/MT76x2 and MT7603/MT76x3 evidence under the
`wr1200js-iot-radio-capacity` artifact. `tools/iot/check-capacity.py` uses each
radio's actual Kbuild `.cmd` and target compiler, checks the effective MBSS and
beacon-array macros, verifies that `MAX_MBSSID_NUM` consults the chip limit,
follows the pinned chip initializer, and records the nested source commit plus
SHA-256 hashes for the source files it inspected. It reports the
source/configuration BSS limit while keeping
`runtime_verified: false`; it does not enable IoT or prove three simultaneous
working SSIDs.

The initial IoT contract is 2.4 GHz only, so the firmware build workflow now
treats the MT7603/mt76x3 three-BSS source/config result as a required gate. An
absent, unavailable, or insufficient probe fails that post-build step. The
MT7612/mt76x2 5 GHz result remains diagnostic until 5 GHz IoT is in scope.
This gate establishes source/config capacity only; it does not activate the
third BSS or count as runtime/device acceptance.

Local synthetic Kbuild fixtures exercised the MT76x2 and MT7603 paths and
reported source/configuration limits of eight and sixteen BSS respectively.
These fixture results only validate the diagnostic's parsing and reporting.
The probe has not yet run against a real target build.

The ABI workflow now includes `tools/iot/check-capacity-selftest.py` to exercise
both radio parsers and the required-capacity failure case with host synthetic
Kbuild trees before downloading the large target toolchain. On 2026-10-18,
`py -3 tools/iot/check-capacity-selftest.py` passed twice with exit code 0
in an approved elevated execution context on Windows. It reported
`PASS IoT capacity probe MT76x2/MT7603 source checks and required-limit failure`.
The ordinary sandbox still denied nested temporary-directory creation; this
was an execution-permission issue, not a failed capacity assertion. These
successful host fixtures do not establish target radio capacity or runtime
acceptance; the updated workflow result remains pending.
The self-test also checks absent and ambiguous Kbuild command files and an
unavailable compiler in both diagnostic and required modes. All six negative
cases passed locally on 2026-10-18: unavailable evidence keeps capacity and
runtime verification false, emits a JSON reason, and fails the required gate.
The report now distinguishes `effective_source_config_bss_limit` (the minimum
of the array ceiling and chip source limit with MBSS enabled) from the raw
chip limit. A passing MT7603 fixture with a sixteen-entry chip limit and an
eight-entry array verifies that the effective value and console limit are eight.
This remains source/configuration evidence rather than working-SSID capacity.
The ABI workflow also compiles the prepared `services_ex.c` to
`iot-services-ex-mips.o` with the
WR1200JS MIPS compiler. Its include paths follow the pinned RC/shared Makefiles
and include the Linux kernel headers; the WR1200JS Ralink board header is staged
directly beside `rc.h` by the preparation step. In ABI run `39113907911`
for `52c802b`, the `Prepare pinned RC IoT bridge and owned radio-stop hook`
step completed successfully, including whole-object `services_ex.c` MIPS
compilation. Earlier run `39113649278` failed because kernel include paths
overrode the target sysroot's errno header; using `-idirafter` and staging
UAPI headers corrected that integration gate. The overall run passed and its
downloaded object/hash identity was independently verified; see
[ABI evidence](evidence/IOT-ABI-52C802B.md). Firmware linking of this IoT
candidate and physical runtime remain unconfirmed.

The separate ABI workflow [run `39104700313`](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39104700313) completed successfully for `dd1e98c`. Its `band-steering-mips-abi` artifact contains compiled MIPS RC objects for the staged IoT bridge, profile, DHCP, network, request-stage, and request-snapshot code, as well as passing host DHCP/DNS and IPv4/IPv6 firewall fixtures. This is source-preparation/ABI evidence, not a production firmware image. The artifact's `iot-rc-source.json` says
`activation_integrated: false`, `writer_journal_lifecycle_bound: false`,
`dnsmasq_service_rollback_complete: false`, and that DHCP protocol readiness
is pending. The source does install a journal binding inside the conditional
DNS restart transaction; the report's false lifecycle value is conservative
because the production IoT activation path does not set that gate and not all
DNS-related writers are covered. Main firmware build
[#448](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/39104625566)
(`5dd2c80`) explicitly excluded `wr-iot-profile.c` and the `wr-iot` RC
directory; its success applies only to that non-IoT scope. Production
integration, complete service rollback, Wi-Fi behavior, and physical-router
acceptance remain open.
