# Current Hadzhioglu → nilabsent package candidates

This document supplements `HADZHIOGLU-NILABSENT-COMPARE.md` after re-checking the **current** `hadzhioglu/padavan-ng` tree (GitLab/GitHub mirror) rather than the older `hadzhioglu/padavan-fw` snapshot.

## Important correction

The current Hadzhioglu project is `hadzhioglu/padavan-ng`. Its current `trunk/user` tree contains packages that are not present in `nilabsent/padavan-ng` master. This is different from the earlier comparison against the older `padavan-fw` tree.

## 2. ndisc6/rdisc6 — REAL PACKAGE CANDIDATE

Current Hadzhioglu `trunk/user` contains an `ndisc6` package and the package commit explicitly describes it as enabled with `CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6=y`.

Current nilabsent master has no standalone `trunk/user/ndisc6` package and its current `trunk/user/Makefile` has no ndisc6/rdisc6 build entry.

**Status: 🟡 candidate.**

First determine whether the WR1200JS configuration currently has the option enabled or commented. If disabled, do not add it to the default firmware. If enabled/desired, the package can be transplanted together with its Makefile/config option.

## 3. obfs4 — REAL PACKAGE CANDIDATE

Current Hadzhioglu `trunk/user` contains an `obfs4` package. Its `trunk/user/Makefile` conditionally builds it with `CONFIG_FIRMWARE_INCLUDE_OBFS4`.

Current nilabsent master has no standalone `trunk/user/obfs4` package and its `trunk/user/Makefile` has no obfs4 build entry.

Need to inspect the exact source revision and build/toolchain requirements before transplanting because obfs4 is a Go-based component and can be sensitive to the old MIPS/uClibc toolchain.

## 4. USB/IP — REAL BUILD-INTEGRATION CANDIDATE

Current Hadzhioglu has a `trunk/user/usbip` userspace package and corresponding build rules. It also has a `sysfsutils` package, added specifically for USB/IP userspace tools.

nilabsent already contains USB/IP-related kernel/staging code, so this is not a missing kernel feature. The difference is the user-space package/build integration.

**Status: 🟡 high-value candidate.**

The correct transplant unit is likely:

1. `trunk/user/usbip/`
2. `trunk/user/sysfsutils/`
3. the relevant `trunk/user/Makefile` entries
4. any required config symbols and defaults

Do not copy the kernel USB/IP code from Hadzhioglu over nilabsent; nilabsent already has the relevant kernel side.

## 5. socat — REAL PACKAGE CANDIDATE IN CURRENT HADZHIOGLU

Current Hadzhioglu `trunk/user` contains `socat` and its top-level Makefile conditionally builds it with `CONFIG_FIRMWARE_INCLUDE_SOCAT`.

A direct current nilabsent master lookup shows no `trunk/user/socat/Makefile` and no standalone `trunk/user/socat` package. Therefore the earlier note that nilabsent already contained a socat package was incorrect and is superseded by this document.

**Status: 🟡 candidate.**

First compare the user's current WR1200JS config. If `CONFIG_FIRMWARE_INCLUDE_SOCAT` is enabled there, this is a concrete missing package/build integration.

## 6. radvd — LEGACY/UNCERTAIN

Hadzhioglu contains `trunk/user/radvd`; nilabsent does not. However, current nilabsent PPP IPv6 sample scripts still refer to `/usr/sbin/radvd`, so the runtime expectation exists even though the package source is absent.

**Status: 🟡 investigate before transfer.**

Need to determine whether the firmware obtains radvd from another package or whether this is simply an inherited sample-script reference. Do not copy blindly.

## 7. ld.so.conf — SMALL DIFFERENCE, NOT A FEATURE

Hadzhioglu has `trunk/user/scripts/ld.so.conf`; nilabsent does not. Nilabsent's scripts use newer `CREATE_LDSO_CONF` handling.

**Status: 🔴 do not transfer.**

This is build/runtime infrastructure, not a user feature, and the nilabsent toolchain already has replacement generation logic.

## 8. CPU frequency package — DO NOT ADD YET

Hadzhioglu contains `mt7621_cpufreq`, but the user's current WR1200JS configuration has this option commented.

**Status: 🔴 leave untouched for now.**

It should only become a separate experiment if CPU frequency control is explicitly wanted and tested for thermal/stability behavior.

## Current priority order

2. **USB/IP + sysfsutils** — useful because the kernel side is already present in nilabsent and the missing part is userspace/build integration.
3. **socat** — concrete missing optional package if the WR1200JS config enables it.
4. **ndisc6/rdisc6** — optional IPv6 diagnostics/tools.
5. **obfs4** — optional, but toolchain complexity is higher.
6. **radvd** — investigate provenance before adding.
7. **ld.so.conf** — do not add.
8. **mt7621_cpufreq** — keep out of the current experiment.

## Rule for the experimental branch

No package is copied merely because it is absent from nilabsent. A candidate is imported only after checking:

- config symbol;
- top-level build wiring;
- shared `APP_*`/`SUPPORT_*` definitions;
- runtime/startup scripts;
- WebUI references, if any;
- dependencies;
- image-size impact;
- WR1200JS compatibility.
