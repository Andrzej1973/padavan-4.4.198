# Hadzhioglu → nilabsent comparison

Experimental branch: `experimental/hadzhioglu-compare`

Sources checked:
- `hadzhioglu/padavan-fw` — `dev`
- `nilabsent/padavan-ng` — `master`

## Batch 1 — `trunk/user/httpd`

### HTTPD file inventory correction

A later direct directory inventory corrected the earlier preliminary observation: **both repositories have the same 25 files in `trunk/user/httpd`**, including `image_tplink.h` and `image_uimage.h`. There is no `image.h` in either current source tree.

**Decision: no image header transfer is required.**

### `httpd/Makefile`

Exists in both, but differs.

Hadzhioglu already uses function/data sections and `--gc-sections`. nilabsent additionally uses `-fvisibility=hidden` and has current board-specific build changes.

**Decision: DO NOT replace nilabsent's Makefile.** Preserve nilabsent's build system and only add a missing object/flag when a specific feature requires it.

### `common.h`, `httpd.c`, `httpd.h`, `https.c`

All exist in both and differ.

**Decision: DO NOT copy wholesale.** Compare individual declarations/functions only when a missing feature is identified.

### `web_ex.c`

The files share the same major infrastructure. One immediately visible difference is the POST buffer:
- Hadzhioglu: `post_buf[32768]`
- nilabsent: `post_buf[262144]`

**Decision: KEEP nilabsent.** This is an enhancement, not a missing Hadzhioglu feature.

### Files observed identical in the first directory sample

`aidisk.c`, `aspbw.c`, `base64.c`, `cgi.c`, `common.c`, `crc32.c`, `ej.c` had matching blob SHAs in both repositories.

**Decision: no action required.**

## Batch 2 — `trunk/user/httpd/variables.c` and VPN integration

A significant difference was found in `variables.c`:

Hadzhioglu has the VPN server/client ACL variables ending with `vpns_rmsk_x`.

nilabsent adds, under `APP_WIREGUARD`:

`vpns_public_x`

This is **nilabsent-only functionality**, not something missing from nilabsent. Do not import the older Hadzhioglu block over it. The corresponding WireGuard support is integrated into `httpd`, `rc`, defaults and build flags.

## Batch 3 — `trunk/user/rc/Makefile`

Both repositories contain the same major rc object set, but nilabsent has important additions:

- `vpn_wireguard.o` when `CONFIG_FIRMWARE_INCLUDE_WIREGUARD` or `CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG` is enabled;
- `-fvisibility=hidden`;
- additional romfs links such as `ntpc_syncnow`, `restart_zapret`, and `update_resolvconf`;
- newer Samba condition handling with `APP_SMBD36`.

**Decision: DO NOT copy Hadzhioglu's Makefile.** nilabsent's is newer and contains functionality required by its WireGuard/AmneziaWG integration.

## Batch 4 — `trunk/user/rc/vpn_wireguard.c`

`vpn_wireguard.c` exists in nilabsent and is not present in the Hadzhioglu source tree searched.

It provides start/stop/restart/reload/update/watchdog handling for WireGuard client/server through `/usr/bin/wgs.sh` and `/usr/bin/wgc.sh`.

**Decision: KEEP nilabsent. DO NOT attempt to import a Hadzhioglu replacement.**

## Batch 5 — AmneziaWG

nilabsent contains a complete AmneziaWG kernel integration under `trunk/linux-3.4.x/net/amneziawg/`, plus build/config integration and userspace tooling. The searched Hadzhioglu tree does not contain this feature.

**Decision: KEEP nilabsent. DO NOT transplant the feature into the comparison branch merely because it is absent in Hadzhioglu.** It is a newer nilabsent feature and is especially relevant to the router's VPN configuration.

## Batch 6 — `trunk/user/rc/common_ex.c`

The first concrete difference in this file is inside `get_eeprom_params()` for TP-Link boards.

Hadzhioglu reads the LAN/2.4 GHz MAC from the `Romfile` partition at `0xf100`; if that read fails, it falls through to the standard Ralink factory offsets.

nilabsent adds a fallback attempt to read the same `0xf100` location from `MTD_PART_NAME_FACTORY` before falling through:

```c
if (i_ret < 0)
    i_ret = flash_mtd_read(MTD_PART_NAME_FACTORY, 0xf100, buffer, ETHER_ADDR_LEN);
```

**Decision: KEEP nilabsent. DO NOT copy the older Hadzhioglu implementation.** This is a board/flash-layout robustness improvement and is not a missing feature.

This also means `common_ex.c` should remain a function-level comparison target; a whole-file replacement could remove nilabsent's TP-Link factory fallback.

## Batch 7 — `trunk/user/rc/firewall_ex.c`

The file has different blob SHAs, but the inspected implementation through the early firewall rule-generation sections is identical between the two trees: protocol conversion, time matching, IP-range conversion, static routes, VPN client rules, MAC filter, URL/webstr filter, low-level filter and virtual-server/NAT generation all match in the inspected ranges.

The file should therefore **not** be replaced wholesale merely because its SHA differs. The remaining tail still needs function-level inspection before declaring the file fully equivalent.

**Decision so far: 🟡 function-level comparison; no transfer candidate identified.**

## Batch 8 — `trunk/user/rc/services.c`

The beginning of `services.c` is functionally equivalent for syslog/klogd/infosvr/crond/networkmap/telnetd/sshd. There is a small implementation difference in `start_syslogd()`:

- Hadzhioglu starts with `-L` unset and enables it dynamically when remote logging is configured.
- nilabsent includes `-L` in the initial argv and always supplies the remote `-R` pair only when a valid remote log address exists.

This does not justify importing the old file.

More importantly, nilabsent contains a dedicated `APP_ZAPRET` service block (`is_zapret_run`, `stop_zapret`, `start_zapret`, `restart_zapret`, `reload_zapret`). A search of the Hadzhioglu tree found no `is_zapret_run` implementation.

**Decision: KEEP nilabsent.** Zapret is nilabsent-only functionality, not a lost Hadzhioglu feature.

## Batch 9 — WebUI `n56u_ribbon_fixed`

The WebUI directories have the same broad structure, and many core pages have identical blob SHAs. Examples already verified include `Advanced_ACL2g_Content.asp`, `Advanced_ACL_Content.asp`, `Advanced_AiDisk_ftp.asp`, `Advanced_AiDisk_others.asp`, `Advanced_AiDisk_samba.asp`, `Advanced_BasicFirewall_Content.asp`, and `Advanced_Console_Content.asp`.

### `Advanced_Services_Content.asp`

This is a particularly useful example of **reorganization rather than loss**.

Hadzhioglu's page contains the Tor, Privoxy and DNSCrypt controls directly in the main Services page (`found_app_tor()`, `found_app_privoxy()`, `found_app_dnscrypt()`, their enable/config rows and handlers).

nilabsent removes those controls from the main page and separates the Services menu into dedicated pages. Its `state.js` explicitly contains:

- `Advanced_Services_DNSCrypt.asp`
- `Advanced_Services_DoH.asp`
- `Advanced_Services_DoT.asp`
- `Advanced_Services_Zapret.asp`
- `Advanced_Services_Proxy.asp`

and its service checks still reference `found_app_tor()` / `found_app_privoxy()`. Therefore the old Tor/Privoxy/DNSCrypt code was not simply lost; the WebUI was reorganized into separate service pages.

**Decision: DO NOT copy Hadzhioglu's `Advanced_Services_Content.asp`.** Keep nilabsent's split WebUI.

### `Advanced_Services_Service7.asp` / `Service8.asp`

`state.js` in both generations contains placeholder menu slots for `Advanced_Services_Service7.asp` and `Advanced_Services_Service8.asp`, but a direct file lookup in the Hadzhioglu tree returned 404 for `Service7`, and the nilabsent tree also returns 404 for `Service7`.

**Decision: NOT a missing-file candidate.** These are menu slots/placeholders, not a file that should be copied.

### USB modem page

`Advanced_Modem_others.asp` exists in nilabsent and remains referenced by its device-map and Makefile. It is therefore not a Hadzhioglu-only page that was dropped.

**Decision: KEEP nilabsent.**

## Batch 10 — WebUI file inventory

A direct filename inventory of `trunk/user/www/n56u_ribbon_fixed` gives:

- Hadzhioglu: 103 top-level entries;
- nilabsent: 110 top-level entries.

After excluding common directory entries (`aidisk`, `bootstrap`, `device-map`, `images`), the **only Hadzhioglu-only file is**:

`Nologin.asp`

The nilabsent-only WebUI files are:

- `Advanced_Services_DNSCrypt.asp`
- `Advanced_Services_DoH.asp`
- `Advanced_Services_DoT.asp`
- `Advanced_Services_Proxy.asp`
- `Advanced_Services_Zapret.asp`
- `jquery.multiSelectDropdown.css`
- `jquery.multiSelectDropdown.js`
- `qrcode.min.js`

The nilabsent-only files are consistent with its expanded/reorganized Services and VPN UI.

### `Nologin.asp`

Hadzhioglu's file is a small static page using `login_state_hook()`, displaying `login_ip_str()` and the `login_hint1/login_hint2` messages. A source search did **not** find a reference to the literal filename `Nologin.asp` in either tree.

**Decision: 🔴 do not copy yet.** It is self-contained, but until a backend redirect/reference to `Nologin.asp` is found, adding it would only add an apparently unused page.

### Directory-level inventory

Direct filename comparison currently gives:

| Directory | Hadzhioglu-only | nilabsent-only |
|---|---:|---:|
| `trunk/user/httpd` | 0 | 0 |
| `trunk/user/rc` | 0 | 1 (`vpn_wireguard.c`) |
| `trunk/user/shared` | 0 | 0 |
| `trunk/user/www/n56u_ribbon_fixed` | 1 (`Nologin.asp`) | 8 |

This is a strong indication that the useful differences are primarily **inside existing files**, not missing standalone files.

## KMS finding

The earlier search for `kms` in nilabsent mostly finds Linux DRM Kernel Mode Setting code. That is unrelated to a Windows KMS server.

The searched Hadzhioglu source tree did not reveal `vlmcsd` or a Windows KMS server. Therefore no KMS server should be copied based on the current evidence. If the KMS server was present in a specific prebuilt Hadzhioglu-based firmware, that build/package must be identified separately.

## Batch 11 — VPN/WebUI function and field inventory

For `vpncli.asp` and `vpnsrv.asp`, comparing extracted JavaScript function names and HTML form-field names found **no function or field present only in Hadzhioglu**.

nilabsent adds substantial VPN functionality, including:

- WireGuard client UI and key generation;
- AmneziaWG parameters;
- WireGuard/OpenVPN configuration import;
- VPN client access-control and IPSet selection;
- WireGuard server fields and client export/QR helpers.

Therefore the much larger nilabsent VPN pages are genuine extensions, not evidence of dropped Hadzhioglu functionality.

For `Advanced_Tweaks_Content.asp` and `Advanced_Scripts_Content.asp`, function and field inventories are identical; the detected content difference is only the `show_menu()` index.

For `Advanced_Console_Content.asp`, the functional code and fields are identical; differences are the menu index and textarea presentation.

For `Advanced_Services_Content.asp`, Hadzhioglu-only fields/functions are exactly the Tor/Privoxy/DNSCrypt controls moved into nilabsent's dedicated Services pages. Searches confirm the same `tor_enable`, `privoxy_enable`, and `dnscrypt_enable` functionality remains in nilabsent.

## Current rule

We are not doing whole-file replacements. The working rule is:

- 🟢 standalone file missing in nilabsent and self-contained → candidate for transfer;
- 🟡 file exists in both → compare functions/definitions and transfer only the required fragment;
- 🔴 older implementation conflicts with newer nilabsent functionality → do not transfer;
- 🔵 nilabsent-only feature → preserve it; it is not a missing Hadzhioglu feature.

No firmware source file has been modified yet. The experimental branch contains only the comparison documentation.


## Batch 12 — top-level `trunk/user` inventory and `radvd`

A direct top-level inventory of `trunk/user` shows one Hadzhioglu-only directory:

`radvd/`

nilabsent has no corresponding `trunk/user/radvd` directory. The Hadzhioglu package contains a full `radvd-2.X` source tree and a Makefile whose `romfs` target installs `radvd` as `/usr/sbin/radvd`.

However, neither Hadzhioglu nor nilabsent's `trunk/user/Makefile` contains a reference to `radvd`. The nilabsent tree does contain PPP IPv6 sample scripts that refer to an external `/usr/sbin/radvd`, and its changelog mentions historical radvd updates, but there is no current `trunk/user/radvd` source package.

**Decision: 🟡 investigate, but DO NOT transfer yet.** The package is a plausible legacy IPv6 component, but current source-level evidence does not show that the Hadzhioglu package is actually part of the normal firmware build. Copying the whole daemon without establishing its build/config integration would add unused code and possibly increase image size. The next check is the IPv6 build/config path and runtime references.


## Batch 13 — WR1200JS board/config support

A direct lookup of `trunk/configs/boards/YOUHUA/WR1200JS` produced a major difference:

- **nilabsent:** has a complete WR1200JS board package: `board.h`, `board.mk`, `kernel-3.4.x.config`, `partitions.config`;
- **current Hadzhioglu `dev`:** has no `trunk/configs/boards/YOUHUA/WR1200JS` directory and no YOUHUA board directory at all (only YOUKU appears among similarly named board directories).

The nilabsent WR1200JS partition definition is:

- Bootloader: `0x000000` / `0x30000`
- Config: `0x30000` / `0x10000`
- Factory: `0x40000` / `0x10000`
- Firmware: `0x50000` / `0xF70000`
- Storage: `0xFC0000` / `0x40000`

This matches the WR1200JS MTD layout observed during the router work, so this is not a generic MT7621 profile.

The board header also defines the actual WR1200JS GPIO/features, including reset/WPS/FN1 buttons, power/USB LED GPIOs, dual-band 2x2 radio counts, one Ethernet LED, gigabit PHYs, and one USB port. The board kernel configuration selects MT7621 ASIC, 128 MB RAM, MT7603E 2.4 GHz and MT7612E 5 GHz radios.

The associated `wr1200js.config` template enables several features relevant to the current firmware build, including USB, EXT4, FUSE, swap, XFRM/IPsec, IPSet, SFTP, StrongSwan, AmneziaWG, DNSCrypt, Stubby/DoT, DoH, ADB, EoIP, Zapret/Zapret2; WireGuard, Tor, Privoxy, iPerf3 and ZeroTier are present as optional commented selections in the template.

Git history in nilabsent identifies commit `833734c0b9b48c50ac2ad71fbf6bef6e886c8233` ("firmware: add support for Youhua WR1200JS") from 2018-10-10 and subsequent WR1200JS config updates. The searched current Hadzhioglu history did not return WR1200JS support commits.

**Decision: this is NOT a missing feature to transplant from Hadzhioglu.** It is the opposite: WR1200JS board support is a nilabsent-side feature relative to the currently checked Hadzhioglu `dev`. The board configuration should remain the canonical hardware definition for the WR1200JS branch.

## Batch 14 — current Hadzhioglu GitLab vs nilabsent: real package-level candidates

The earlier GitHub hadzhioglu/padavan-fw tree was too old/incomplete a source for this question. The current Hadzhioglu project is gitlab.com/hadzhioglu/padavan-ng, whose current trunk/user tree contains several packages that are not present as standalone directories in nilabsent/master.

Important current Hadzhioglu-only package candidates compared with nilabsent/master:

| Package | Current Hadzhioglu | nilabsent/master | Preliminary decision |
|---|---|---|---|
| vlmcsd | yes | no | strong candidate; inspect build hooks before transfer |
| ndisc6 | yes | no | likely standalone transfer candidate |
| obfs4 | yes | no | transfer only with build/toolchain dependencies |
| nfqws | yes as a package | no standalone package | do not copy: nilabsent already ships nfqws through zapret/zapret2 |
| mt7621_cpufreq | yes | no | leave aside; user's WR1200JS config has this option commented |
| sysfsutils | yes | no | likely support/dependency package for USB/IP userspace |

### vlmcsd — KMS

Current Hadzhioglu GitLab has a dedicated trunk/user/vlmcsd package. Its current tree records a recent change titled “Auto set _VLMCS srv-record if vlmcsd ON”. This is the KMS/vlmcsd feature that was not visible in the earlier GitHub hadzhioglu/padavan-fw snapshot.

The user's youhua-wr1200js/build.config already contains CONFIG_FIRMWARE_INCLUDE_VLMCSD=y, but the current nilabsent WR1200JS template does not define this symbol and the nilabsent source search does not find vlmcsd or CONFIG_FIRMWARE_INCLUDE_VLMCSD.

Decision: confirmed high-priority candidate for deeper inspection. Do not copy the directory yet: we need the current Hadzhioglu trunk/user/Makefile integration and exact package files, then transplant the minimal package/build hook into the experimental branch.

### ndisc6 / rdisc6

Current Hadzhioglu has a dedicated ndisc6 package and explicitly documents the build option in the directory listing as CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6=y.

The user's build.config has this option enabled. The current nilabsent WR1200JS template has no corresponding option and nilabsent has no trunk/user/ndisc6 directory.

Decision: strong candidate for transfer, subject to checking its Makefile and adding the corresponding build variable minimally.

### obfs4

Current Hadzhioglu has a dedicated obfs4 package and its current tree records an obfs4 package update. The user's WR1200JS config has CONFIG_FIRMWARE_INCLUDE_OBFS4=y.

The current nilabsent WR1200JS template does not define the option and nilabsent has no standalone trunk/user/obfs4 package.

Decision: candidate, but not a blind copy. obfs4 is substantially larger than ndisc6/vlmcsd and depends on its Go build/package arrangement.

### Important config mismatch

The user's build.config is not equivalent to the current nilabsent WR1200JS template.

Active options in the user's config that are absent from the current nilabsent WR1200JS template include:

- CONFIG_FIRMWARE_INCLUDE_USBIP
- CONFIG_FIRMWARE_INCLUDE_SOCAT
- CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6
- CONFIG_FIRMWARE_INCLUDE_OBFS4
- CONFIG_FIRMWARE_INCLUDE_VLMCSD

Several other user-enabled options are present in nilabsent but currently commented there, including CPU sleep, HID, QoS/IMQ/IFB, WireGuard, Tor/GeoIP, Privoxy, iPerf3, ZeroTier, Shadowsocks and image-size optimization.

This does not mean the user's current build is broken or incomplete. It means the configuration file and the current nilabsent board template have diverged, and some symbols may depend on custom or legacy build logic that is not in nilabsent/master.

### Current priority

1. vlmcsd — inspect exact source and Makefile hook
2. ndisc6 — inspect exact source and Makefile hook
3. obfs4 — inspect package and toolchain dependencies
4. sysfsutils — check whether it is required by the nilabsent USB/IP implementation
5. mt7621_cpufreq — leave aside unless we explicitly decide to experiment with CPU frequency

No firmware source code has been copied yet.
## Batch 15 — refine the config-drift candidates

Direct source searches against current nilabsent/master give three especially clear results:

- ndisc6/rdisc6: no current source references or standalone package were found.
- obfs4: no current source references or standalone package were found.
- vlmcsd: no current source references or standalone package were found.

Therefore these three are genuine source-level candidates to recover from current Hadzhioglu, provided their build integration is ported.

Two other user-config options need a different treatment:

- CONFIG_FIRMWARE_INCLUDE_NFQWS: nilabsent already contains nfqws and nfqws2 under trunk/user/zapret/zapret and trunk/user/zapret/zapret2. The Makefiles install them as /usr/bin/nfqws and /usr/bin/nfqws2. Do not transplant the older Hadzhioglu nfqws package.
- CONFIG_FIRMWARE_INCLUDE_USBIP: nilabsent contains the USB/IP kernel and userspace source under Linux staging, so the feature itself exists. The current WR1200JS template simply does not expose the user's old config symbol. Treat this as a build-system/config integration question, not as a missing source package.
- CONFIG_FIRMWARE_INCLUDE_SOCAT: nilabsent contains a socat package, so likewise it is not a missing source package. The missing symbol in the current WR1200JS template needs build-system investigation before any transfer.

sysfsutils is different again: nilabsent's USB/IP userspace README lists sysfsutils >= 2.0.0 as a dependency, while the current nilabsent tree has no standalone sysfsutils package. The current Hadzhioglu tree does. Therefore sysfsutils is a dependency candidate to investigate together with USB/IP, not an independent user feature.

Current highest-value recovery candidates are now: vlmcsd, ndisc6/rdisc6 and obfs4.
## Batch 16 — correction: USBIP and SOCAT are also current Hadzhioglu-only user packages

A fresh direct inventory of nilabsent/master trunk/user has 78 top-level entries and does NOT contain standalone socat or usbip directories.

Current Hadzhioglu GitLab does contain both socat and usbip directories in trunk/user.

Therefore the earlier Batch 14 wording that treated socat as already present in nilabsent was incorrect and is superseded by this batch.

USB/IP needs to be treated as a two-part feature: nilabsent contains the Linux 3.4 USB/IP kernel/userspace source under the kernel staging tree, but it lacks the current Hadzhioglu trunk/user usbip package/build integration. The user config has CONFIG_FIRMWARE_INCLUDE_USBIP=y, so this is a concrete candidate for restoring the user-space build integration, likely together with sysfsutils.

SOCAT is also a current Hadzhioglu user package but has no standalone socat directory in nilabsent/master. The user config has CONFIG_FIRMWARE_INCLUDE_SOCAT=y, so it is another concrete candidate to inspect before the next experimental source commit.

Updated high-priority candidate set for the user's active build.config:

1. vlmcsd / KMS
2. ndisc6 + rdisc6
3. obfs4
4. usbip + sysfsutils
5. socat

NFQWS remains excluded from this transfer list because nilabsent already provides nfqws/nfqws2 through its zapret and zapret2 packages.
mt7621_cpufreq remains excluded for now because the user's option is commented.
## Batch 17 — KMS/vlmcsd integration is a real missing source feature

Using the current `hadzhioglu/padavan-ng` GitHub repository, the comparison found more than the standalone `vlmcsd` package:

- `trunk/user/Makefile` adds `CONFIG_FIRMWARE_INCLUDE_VLMCSD -> vlmcsd`.
- `trunk/user/shared/cflags.mk` adds `-DAPP_VLMCSD`.
- `trunk/user/httpd/common.h` defines the event bit `EVM_RESTART_VLMCSD` and event type `EVT_RESTART_VLMCSD`.
- `trunk/user/shared/notify_rc.h` defines `restart_vlmcsd`.
- `trunk/user/rc/rc.h` declares the start/stop/restart functions.
- `trunk/user/rc/services.c` implements the service lifecycle and starts/stops it with the normal services.
- `trunk/user/rc/rc.c` handles the restart notification and restarts DHCPD as part of KMS configuration changes.
- `trunk/user/rc/services_ex.c` publishes `_VLMCS._tcp` through dnsmasq when `vlmcsd_enable=1`.
- `trunk/user/shared/defaults.c` provides `vlmcsd_enable=0` by default.
- `trunk/user/httpd/variables.c` registers the NVRAM variable and the restart event.
- `trunk/user/httpd/web_ex.c` exposes `found_app_vlmcsd` through the firmware capability hook.
- current Hadzhioglu `Advanced_Services_Content.asp` has a KMS toggle using `vlmcsd_enable` and hides it when `found_app_vlmcsd()` is false.

Current nilabsent/master has none of these `APP_VLMCSD` integration pieces. Therefore KMS is a confirmed source-level functionality gap between current Hadzhioglu and nilabsent, not merely a different package layout.

### Experimental implementation

The experimental branch now contains:

- `overlay/padavan-ng/trunk/user/vlmcsd/Makefile`
- `overlay/padavan-ng/trunk/user/vlmcsd/vlmcsd.sh`
- `overlay/patches/0001-vlmcsd-integration.patch`
- corresponding build hook in `pre-build.sh`

The patch restores the backend/build integration and the firmware capability hook. The WebUI toggle itself is not yet copied; this is intentional until the current nilabsent Services page structure is reconciled with Hadzhioglu's page rather than replacing the newer nilabsent Services UI wholesale.

Local static checks completed: `pre-build.sh` passes `sh -n`, and the three package Makefiles parse successfully with GNU make. No complete firmware build has been run yet.

## Batch 9 — WebUI Advanced_Tweaks_Content.asp / Advanced_Scripts_Content.asp

The full line-level comparison shows these files are structurally identical between Hadzhioglu and nilabsent at the current refs, with only the menu-group indices changed because nilabsent inserted/reordered the Services/System groups in state.js.

For Advanced_Tweaks_Content.asp:
- Hadzhioglu: show_menu(5,8,1);
- nilabsent: show_menu(5,9,1);

For Advanced_Scripts_Content.asp:
- Hadzhioglu: show_menu(5,8,2);
- nilabsent: show_menu(5,9,2);

No unique form fields or JavaScript functions were found on either side in the direct name/function comparison.

Decision: no transfer. The pages are functionally the same; the changed menu index is part of nilabsent's menu layout.

## Batch 10 — WebUI Advanced_Console_Content.asp

The two files have the same functions, form fields and command execution flow. The meaningful differences are different show_menu() indices and minor textarea presentation changes: nilabsent makes the output vertically resizable, uses a different font/line-height, and uses rows=24 instead of 23.

Decision: no transfer. No lost console capability identified.

## Batch 11 — WebUI Advanced_System_Content.asp

The page is nearly identical structurally. nilabsent adds a real WebUI helper ntpSyncNow() which calls /sbin/ntpc_syncnow through the generic sendSystemCmd() mechanism.

A direct search found no corresponding ntpSyncNow() implementation in Hadzhioglu.

Decision: KEEP nilabsent. This is a nilabsent enhancement, not a Hadzhioglu feature to recover.

## Batch 12 — WebUI vpncli.asp

This is a major expansion in nilabsent rather than a loss:
- no Hadzhioglu-only JavaScript functions were found;
- no Hadzhioglu-only form fields were found;
- nilabsent adds OpenVPN configuration import;
- nilabsent adds WireGuard key generation/import;
- nilabsent adds AmneziaWG parameters and key/header-protection fields;
- nilabsent adds VPN client access-control and IPSet selection;
- nilabsent adds WireGuard post-script handling.

The WireGuard option is gated by found_app_wg() and the AmneziaWG option by found_app_awg().

Decision: DO NOT copy the Hadzhioglu file. The nilabsent version is more extensive in this area and is integrated with the current backend.

## Batch 13 — WebUI vpnsrv.asp

No Hadzhioglu-only functions or form fields were found in the direct comparison. nilabsent adds WireGuard server port/private/public/MTU/external-address fields, OpenVPN NCP cipher-list and TLS control options, WireGuard client key generation/export and QR export helpers, plus additional client-management UI.

Decision: DO NOT copy the Hadzhioglu file.

## Important interpretation

The fact that a page is visibly different does not mean the firmware is missing something. The strongest confirmed differences so far are that nilabsent reorganizes the WebUI and adds helpers, substantially extends VPN/AmneziaWG support, and retains some old pages with only menu-index changes. No verified Hadzhioglu-only WebUI feature has yet been found that is absent from nilabsent.

The next target is the full tree of scripts, binaries and config definitions under trunk/user and related build recipes. A service can exist without being exposed as a WebUI page, so this is the next place to look for genuinely missing or optional functionality.


## Batch 14 — `trunk/user/scripts/ld.so.conf` (first real Hadzhioglu-only file)

Directory-level comparison of `trunk/user/scripts` found one file present in Hadzhioglu and absent in nilabsent: `ld.so.conf`.

Hadzhioglu file content is only:

```text
/lib
/usr/lib
```

Hadzhioglu's `scripts/Makefile` installs it as `/etc_ro/ld.so.conf`. nilabsent's `scripts/Makefile` no longer installs this file; instead its newer toolchain has its own `CREATE_LDSO_CONF` machinery and generates a target/sysroot `ld.so.conf` when shared libraries are used.

**Decision: 🟡 do not transfer yet.** The file is genuinely absent, but its two search paths are standard/default on this uClibc target and we have not demonstrated a lost runtime dependency on WR1200JS. Copying it blindly could be redundant. This is the first genuine Hadzhioglu-only file and remains a candidate for runtime validation rather than immediate import.

## Batch 15 — package/directory level

The top-level `trunk/user` directory contains 64 subdirectories in the Hadzhioglu tree and 77 in nilabsent. There is no top-level package directory found only in Hadzhioglu; nilabsent adds packages such as `adb`, `doh_proxy`, `eoip-ctl`, `iperf3`, `redsocks`, `shadowsocks`, `stubby`, `wireguard`, `zapret`, and `zerotier`.

This is strong evidence that the current search should concentrate on individual files inside common packages and on build/config wiring, rather than looking for an entire missing application directory.

## Batch 16 — KMS/VLMCSD clarification

The WR1200JS configuration used in the user's builder contains `CONFIG_FIRMWARE_INCLUDE_VLMCSD=y`. The same option is present in the old WR1200JS build configuration and the current nilabsent-derived WR1200JS configuration.

However, the current `nilabsent/padavan-ng` source tree does not contain a `vlmcsd` source/package directory, and its `trunk/user/Makefile` has no `vlmcsd` build/install directory tied to this option. The current build firmware script also has no `VLMCSD`/`vlmcsd` handling in the searched sections.

Therefore the configuration flag by itself is not evidence that a KMS server is actually built into the image. It appears to be a legacy/inherited option whose implementation came from another Padavan package/builder lineage. This explains why a WR1200JS config can show `CONFIG_FIRMWARE_INCLUDE_VLMCSD=y` while the resulting WebUI/source tree has no KMS implementation.

**Decision: 🔴 do not import arbitrary KMS code from another fork yet.** First identify the exact old source/package that supplied the working `vlmcsd` binary and its startup/WebUI integration. The KMS issue is now separated from the Hadzhioglu-vs-nilabsent source comparison.

## Batch 17 — function-level scan of common `rc` and `httpd` files

Across the differing `rc` files checked so far, no Hadzhioglu-only C function was found. nilabsent-only additions include `restore_app_rules`, `load_ipset_modules`, `reapply_vpn_client`, `ntpc_syncnow_main`, and additional DNSCrypt/DoH/Stubby/Zapret/Tor handling.

Across the differing `httpd` files checked so far, no Hadzhioglu-only C function was found. nilabsent adds functions such as `net_iface_list_hook` and `leases_wireguard_server`.

**Decision: no transfer candidate from these function-name differences.** The remaining work is to inspect semantic differences in the few files that have equal function sets but different implementations, then continue through other common-package directories.


## Batch 18 — package-level file comparison

The common package directories checked so far contain no straightforward Hadzhioglu-only implementation files that are absent from nilabsent.

Notable cases:
- `uqmi`: nilabsent adds newer WDA/MBIM/UIM source files and RAW-IP related support; H does not have a unique feature candidate here.
- `usb-modeswitch`: Hadzhioglu has unpacked legacy source files while nilabsent carries newer source as versioned tarballs. This is a packaging/layout difference, not proof of a missing feature.
- `strongswan`: H has only `.gitignore` as an extra top-level file while nilabsent carries the versioned source tarball; no transfer candidate.
- `tor`: H-only `getgeoip.sh` and `mmdb-convert.py` are accompanied in nilabsent by packaged GeoIP databases and newer Tor source; do not copy them blindly.
- `radvd`: H has a Makefile at the package root, but no current corresponding implementation was found by direct search; this needs deeper build-history analysis rather than file copying.
- `hdparm`: H-only `sysfs.h` occurs alongside a substantially reworked/newer nilabsent hdparm source set. No H-only feature has been established.

## Batch 19 — WebUI parameter scan

A parameter-name scan of `httpd/variables.c` and `shared/defaults.c` finds five Hadzhioglu-only DNSCrypt names:

`dnscrypt_resolver`, `dnscrypt_ipaddr`, `dnscrypt_port`, `dnscrypt_force_dns`, `dnscrypt_options`.

These are not currently exposed as an actually missing feature in nilabsent. The nilabsent WebUI instead uses the newer DNSCrypt model with `dnscrypt_resolver0..3`, `dnscrypt_listen_mode`, `dnscrypt_listen_port`, and `dnscrypt_mode`, with the WebUI page `Advanced_Services_DNSCrypt.asp`. So this looks like a parameter-model migration, not a lost service.

The scan also finds a much larger set of nilabsent-only parameters for DoH, DoT/Stubby, Zapret, Tor client/IPSet control, WireGuard and AmneziaWG.

**Decision: do not restore the old DNSCrypt names.** A compatibility migration would only be justified if old NVRAM configurations need to be imported into the new layout.

## Batch 20 — current strongest H-only candidate

At this stage the only simple, genuine H-only runtime file identified is `trunk/user/scripts/ld.so.conf`. Its content is only `/lib` and `/usr/lib`. Because the nilabsent toolchain has its own `CREATE_LDSO_CONF` machinery, it remains a validation candidate rather than a safe unconditional transplant.

No H-only WebUI page, rc source file, httpd source file, service directory, or package implementation with demonstrated lost functionality has yet been found.

## Batch 21 — source baseline clarification

The requested project is hadzhioglu/padavan-ng. The directly accessible GitHub mirror is older than the current GitLab master. Current GitLab trunk/user shows commit 2cece89d from September 2026 and contains later packages such as sysfsutils and usbip. Use the same source revision for exact file-to-file comparisons; use GitLab-current only to detect later Hadzhioglu additions.

## Batch 22 — package candidates rechecked

H-only in the GitHub master package inventory: amneziawg, mt7621_cpufreq, ndisc6, nfqws, obfs4, socat, vlmcsd.
nilabsent-only: firefly, redsocks, samba3, shadowsocks, zapret, zerotier.

Classification:
- vlmcsd: real Windows KMS server integration in Hadzhioglu; nilabsent has no equivalent source integration found. Strong candidate.
- ndisc6: ndisc6/rdisc6 utilities; nilabsent has no standalone package. Good small candidate.
- socat: generic relay/socket utility; nilabsent has no standalone package. Good small candidate.
- obfs4: obfs4proxy package; Hadzhioglu uses a prebuilt Entware IPK, so ABI/runtime validation is required.
- nfqws: functionally covered by nilabsent zapret/nfqws2. Do not copy.
- amneziawg: nilabsent has its own newer integrated implementation. Do not copy.
- mt7621_cpufreq: direct /dev/mem register access; option is commented in WR1200JS config. Keep disabled.

## Batch 23 — active WR1200JS config versus nilabsent build hooks

The experimental WR1200JS config actively enables USBIP, SOCAT, NDISC6_RDISC6, OBFS4 and VLMCSD.
The current nilabsent trunk/user Makefile has no directory hooks for those packages. The experimental pre-build currently adds hooks only for VLMCSD, NDISC6 and SOCAT.
This means the experiment still needs explicit USBIP and OBFS4 build integration if those config options are intended to produce user-space components. This is a build-system issue, not proof that a particular already-built firmware image lacks them.

## Batch 24 — USB/IP

nilabsent already contains the USB/IP kernel subsystem and historical userspace source under Linux staging, including usbipd and the vhci/host drivers.
Current Hadzhioglu GitLab additionally contains dedicated trunk/user/usbip and trunk/user/sysfsutils packages; the GitLab package inventory describes sysfsutils specifically as supporting USB/IP userspace tools. This is a userspace/build integration difference, not a missing kernel feature. Current GitLab source inventory confirms both packages. citeturn994021search0
Decision: investigate a minimal userspace/build port of usbip plus the required sysfsutils library. Do not copy the kernel USB/IP subtree.

## Batch 25 — NFQWS

Current Hadzhioglu has a standalone nfqws package based on Zapret 70.5. nilabsent already builds nfqws/nfqws2 through its zapret package and its zapret.sh supports runtime selection/download and POST_SCRIPT handling.
Decision: no NFQWS transfer.

## Batch 26 — MT7621 CPU frequency utility

Current Hadzhioglu mt7621_cpufreq writes MT7621 clock registers through /dev/mem and supports a requested CPU frequency range of 600–1400 MHz.
The WR1200JS config keeps CONFIG_FIRMWARE_INCLUDE_MT7621_CPUFREQ commented.
Decision: do not port or enable it in this recovery branch.

## Batch 27 — current recovery priorities

1. vlmcsd/KMS
2. ndisc6 + rdisc6
3. socat
4. usbip + sysfsutils
5. obfs4 after ABI/runtime validation

No whole-file replacement has been justified. Continue with minimal build/package integration and semantic comparison.
## Batch 28 — WR1200JS configuration drift

The custom WR1200JS config in this repository is not the same as the current nilabsent WR1200JS template. Several options are deliberately enabled in the custom config while the nilabsent template leaves them disabled or omits their symbols.

Notable active custom options with no corresponding active/default entry in the current nilabsent WR1200JS template are:
- CPU sleep
- USB-HID
- QoS, IMQ and IFB
- IPERF3
- NDISC6/RDISC6
- OBFS4
- SOCAT
- USBIP
- VLMCSD
- TOR and TOR GeoIP/GeoIPv6
- Privoxy
- QRencode
- Redsocks2
- Shadowsocks local/redirection
- ZeroTier

Conversely, the current nilabsent WR1200JS template enables some packages that the custom config leaves off, notably Aria2, Aria2 Web Control, CIFS, FTPD, Minidlna, OpenVPN, SFTP, SMB2, Transmission and XUPNPD.

This confirms that the custom config is a feature-selection profile, not a reliable indicator of what the base source tree supports. The correct next step is to verify each custom-only enabled option against its actual package/build hook.

## Batch 29 — ld.so.conf validation

Hadzhioglu scripts/Makefile installs a small /etc_ro/ld.so.conf containing /lib and /usr/lib. The current nilabsent scripts/Makefile does not install that file.

Current nilabsent nevertheless contains the toolchain-level CREATE_LDSO_CONF mechanism, which generates an ld.so.conf for the toolchain/sysroot when enabled. This does not by itself prove that the firmware runtime rootfs receives the same file.

Decision: keep ld.so.conf as a validation item. Do not copy it merely because the filename is H-only; first verify the generated WR1200JS image's /etc_ro and dynamic-loader behavior.

## Batch 30 — current Hadzhioglu source inventory

Current Hadzhioglu GitLab master is ahead of the older GitHub mirror and currently lists these additional user packages relevant to this comparison: amneziawg, mt7621_cpufreq, ndisc6, nfqws, obfs4, socat, sysfsutils, usbip and vlmcsd. Its current trunk/user page shows commit 2cece89d from September 2026. citeturn302978search0

These current GitLab additions map well to the custom WR1200JS options: NDISC6_RDISC6, OBFS4, SOCAT, USBIP and VLMCSD.

Decision: for exact code transplantation use a fixed source revision; for feature inventory use current Hadzhioglu GitLab master. Do not mix a newer package implementation into a comparison without recording its source revision.

## Batch 31 — USB/IP implementation boundary

nilabsent already contains the USB/IP kernel subsystem and the historical userspace source under drivers/staging/usbip/userspace, including usbipd and the vhci/host components. The missing part is not the kernel driver source.

Current Hadzhioglu adds a dedicated firmware-user package and a sysfsutils package specifically for USB/IP userspace. This makes the most appropriate transfer target the userspace/build integration rather than the kernel subtree.

Decision: 🟡 candidate for a minimal package/build port. Further work should identify the exact Makefile dependency chain and required libraries before changing the experimental branch.

## Batch 32 — package recovery status

Current status after the re-check:
- VLMCSD/KMS: confirmed source-level H feature with full service/backend/WebUI integration; experimental overlay exists but remains unbuilt.
- NDISC6/RDISC6: small standalone H package; good candidate.
- SOCAT: small standalone H package; good candidate.
- USBIP + sysfsutils: current H userspace/build addition; nilabsent kernel capability already present; good candidate for a minimal userspace integration.
- OBFS4: H package downloads a prebuilt Entware binary; candidate, but ABI/runtime validation required.
- NFQWS: already represented by nilabsent Zapret/nfqws2; no transfer.
- AmneziaWG: already represented by nilabsent's newer AWG integration; no transfer.
- MT7621 CPUFREQ: low-level /dev/mem utility and disabled in config; no transfer.

No production firmware source has been replaced. The experimental branch remains the safe comparison/work area.
## Batch 33 — optional packages that are already present in nilabsent

Several options enabled in the custom WR1200JS config are not missing from nilabsent even though its default WR1200JS template leaves them disabled:
- IPERF3: nilabsent has a dedicated iperf3 package and a user Makefile hook.
- QRencode: nilabsent has libqrencode and installs /usr/bin/qrencode; WireGuard uses it for QR output.
- Shadowsocks redirection/local: nilabsent has the shadowsocks package and the corresponding SSREDIR/SSLOCAL build switches.
- redsocks2: nilabsent has a dedicated redsocks package and library dependency wiring.
- ZeroTier: nilabsent has a dedicated zerotier package.

Decision: these are configuration-selection differences, not missing-source problems. Do not import Hadzhioglu code for them.

## Batch 34 — build workflow provenance

The experimental workflow clones the nilabsent repository and then executes the custom pre-build script before building the firmware. Therefore the branch is intentionally a nilabsent base with Hadzhioglu-derived overlays/patches, not a fork that silently replaces the base tree.

The custom WR1200JS config is copied into padavan-ng/trunk/.config. The pre-build script then copies the overlay and applies the VLMCSD patch. This means any Hadzhioglu-only package must have both source files in the overlay and a matching user Makefile hook before the active config option can actually produce that package in the firmware.

Current implemented overlay packages: ndisc6, socat and vlmcsd.
Current not-yet-implemented H-only active package paths: obfs4 and usbip/sysfsutils.

Decision: keep the current architecture. Complete package overlays first, then run a real firmware build and inspect the produced rootfs/image before promoting any change.

## Batch 35 — iPerf3/QRcode conclusion

The active custom options CONFIG_FIRMWARE_INCLUDE_IPERF3 and CONFIG_FIRMWARE_INCLUDE_QRENCODE do not require Hadzhioglu recovery. Their implementation is already in nilabsent, so keeping them enabled is a valid feature-selection choice.

## Batch 36 — Stubby watch item

Current Hadzhioglu GitLab master has a recent httpd change titled 'Add stubby flags support into a WEB-interface' (commit f06555d0, about one month before this review). The current nilabsent tree already has a Stubby service, DoT WebUI page and Stubby NVRAM/service integration, but an exact source-level mapping of the newer Hadzhioglu flags change has not been established yet.

Decision: do not copy anything yet. Treat this as a semantic WebUI comparison target after the package candidates are resolved.
## Batch 37 — correction and current Hadzhioglu padavan-ng scripts comparison

Earlier batches that referred to hadzhioglu/padavan-fw are historical and must not be used as the current padavan-ng baseline. The current comparison baseline for this branch is hadzhioglu/padavan-ng.

A direct trunk/user/scripts inventory of current hadzhioglu/padavan-ng master versus nilabsent/master gives three Hadzhioglu-only files:

- autostart.sh
- banner
- rwfs2ubi.sh

### autostart.sh

The file waits for Internet connectivity by pinging 1.1.1.1 and one.one.one.one, retrying for about 180 seconds, then exits.
The current Hadzhioglu scripts Makefile installs it as /usr/bin/autostart.sh.
A source search did not find a current caller in the inspected H or nilabsent source trees.
Decision: investigate the invocation point first; do not copy yet. The file alone does not establish an automatic runtime feature.

### banner

The file is only ASCII artwork. The Hadzhioglu scripts Makefile installs /etc_ro/banner, and the H scripts/profile prints it for interactive shells.
Decision: safe optional cosmetic transfer, but it adds no router functionality.

### rwfs2ubi.sh

The script formats a partition named RWFS as UBI/UBIFS, attaches it, creates an rwfs volume and sets mtd_rwfs_mount=1.
The current WR1200JS partition layout used in this project is Bootloader/Config/Factory/Firmware/Storage and has no RWFS partition.
Decision: do not copy to the WR1200JS branch.

### Corrected current script inventory

Path | H-only | WR1200JS decision
--- | --- | ---
trunk/user/scripts/autostart.sh | yes | investigate caller
trunk/user/scripts/banner | yes | optional cosmetic
trunk/user/scripts/rwfs2ubi.sh | yes | not applicable
trunk/user/scripts/ld.so.conf | not treated as a current H-only padavan-ng gap | historical stale note; do not use

This supersedes the earlier padavan-fw-based ld.so.conf and radvd notes for the current padavan-ng comparison.
## Batch 38 — CURRENT padavan-ng WebUI: real H-only controls

A direct current `padavan-ng` comparison of `Advanced_Services_Content.asp` shows a more meaningful difference than the earlier old-repository comparison.

Hadzhioglu has these service variables in this page that nilabsent does not expose on the corresponding WebUI page:
- `vlmcsd_enable` (KMS server)
- `iperf3_enable` (iperf3 server)

For Tor, Privoxy, DNSCrypt, DoH, DoT/Stubby and Zapret, H's monolithic Services page is larger, but nilabsent has reorganized those controls into dedicated service pages. Those are therefore not treated as lost features.

### `iperf3_enable`

This one is different from the moved services. Current Hadzhioglu has:
- `APP_IPERF3` build flag and user package `trunk/user/iperf3`;
- `iperf3_enable` NVRAM variable and default;
- `EVM_RESTART_IPERF3` / `RCN_RESTART_IPERF3` notification wiring;
- start/stop/restart logic in `rc/services.c`;
- `found_app_iperf3()` capability hook in `httpd/web_ex.c`;
- an `Advanced_Services_Content.asp` enable control;
- `iperf3.sh` which starts the server and stops it.

nilabsent already has the `iperf3` binary/package and a `CONFIG_FIRMWARE_INCLUDE_IPERF3` user Makefile hook, but the compared nilabsent `rc`, `variables.c`, `defaults.c` and Services WebUI do not contain the corresponding `iperf3_enable` service control.

**Decision: 🟡 genuine functional candidate.** It is not safe to copy only the ASP row. The minimum complete port is the service script + NVRAM/default + rc notification/service lifecycle + capability hook + a small WebUI addition, while keeping nilabsent's existing iperf3 package.

### `vlmcsd_enable`

The KMS control is the analogous genuine service gap. The experimental branch already contains the minimal backend/package overlay for VLMCSD, but the patch intentionally needs to be reconciled with the current nilabsent service page rather than replacing the entire page.

**Decision: 🟡 continue with the existing minimal KMS port.**

## Batch 39 — `Advanced_System_Content.asp`: three distinct H-only functions

Current Hadzhioglu has three additional system controls that are absent from the compared nilabsent System page and are backed by real code:

### Reboot scheduler

H has `reboot_schedule_enable` and `reboot_schedule` in `httpd/variables.c` and `shared/defaults.c`, a full WebUI editor in `Advanced_System_Content.asp`, and `timecheck_reboot()` inside `rc/watchdog.c`. The watchdog checks the configured seven-day/time bitmap after NTP is ready and calls `sys_exit()` when the configured time matches.

nilabsent has no corresponding variables/defaults/WebUI fields and no `timecheck_reboot()` block.

**Decision: 🟡 genuine feature gap and a good candidate for a later minimal port.** It is more involved than a WebUI-only addition because the runtime watchdog logic is required.

### Four NTP servers instead of two

H `watchdog.c` uses `ntp_server0`, `ntp_server1`, `ntp_server2`, and `ntp_server3` with fallback across all four. H also registers `ntp_server2` and `ntp_server3` and exposes them in the System page.

nilabsent uses only `ntp_server0` and `ntp_server1` in the same NTP selection path.

**Decision: 🟡 genuine backend/UI difference.** A safe port should change only the NTP server array/variables/defaults/UI, not replace the whole watchdog file.

### ZRAM compression selector

H exposes `zram_clzx` in NVRAM and WebUI with LZO/LZ4 choices. nilabsent's `services.c` still reads `zram_clzx` and has the same LZO/LZ4 selection array, but nilabsent's `variables.c`, `defaults.c` and System page do not expose it.

**Decision: 🟢 small candidate.** This is a partial UI/config gap rather than a missing runtime implementation. The existing nilabsent runtime already understands the selector, so only the variable/default/WebUI layer needs careful restoration and testing.

## Batch 40 — current package inventory correction

The current Hadzhioglu `trunk/user/Makefile` explicitly includes `CONFIG_FIRMWARE_INCLUDE_IPERF3 -> iperf3`. The package contains `iperf-3.15`, `iperf3.sh`, and its Makefile. Therefore `iperf3` must be treated as a current Hadzhioglu package-level comparison target even though an earlier top-level inventory pass failed to list it.

For the current GitHub `hadzhioglu/padavan-ng` master, the H-only package set relevant to this branch is:
- `amneziawg`
- `mt7621_cpufreq`
- `ndisc6`
- `nfqws`
- `obfs4`
- `socat`
- `vlmcsd`
- `iperf3`

nilabsent already has its own implementations for iperf3, WireGuard/AmneziaWG-related functions, Zapret/nfqws and several proxy packages. Only genuine missing service/build layers are candidates for recovery.

## Batch 41 — immediate next candidates

The next implementation-safe comparison order is now:
1. `iperf3_enable` service/UI layer, because the binary already exists in nilabsent and the H service code is self-contained.
2. `zram_clzx` WebUI/config layer, because nilabsent already has the runtime selector.
3. Four-server NTP support (`ntp_server2/3`).
4. Reboot scheduler (`reboot_schedule_*`) after checking all watchdog/event interactions.
5. USB/IP userspace + sysfsutils.
6. OBFS4 package/runtime integration.

No existing nilabsent file has been replaced wholesale.