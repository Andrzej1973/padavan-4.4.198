# MT7603 lifecycle entry inventory at pinned source revision

Read-only source snapshot: `vipshmily/padavan-4.4` commit
`c25283e915a2a00a763774dd255b14aff997285e`, fetched sparsely outside
the working repository into `%TEMP%\wr1200js-mt76x3-source-audit`.
Searched all C/H files under the pinned `mt76x3` driver for calls to
`MainVirtualIF_open/close`, `MBSS_VirtualIF_Open/Close` and the two public
PDMA/PSE recovery functions. No direct C call to the main or MBSS open/close
functions was found beyond their definitions/prototypes. The main hook and
MBSS hooks are passed to `RtmpOSNetDevAttach`, which assigns them to
`ndo_open`/`ndo_stop` (`os/linux/rt_linux.c:1676-1677`). Normal netdevice
callbacks are serialized by RTNL. This narrows the main-close issue in
evidence 560: the described overlap is not a proven normal ndo race.

Reset entry paths in the pinned driver are less narrow. The debug/private
handlers in `common/cmm_cfg.c:1728,1761` call PDMA/PSE recovery directly.
`common/cmm_mac_pci.c:2151,2432` calls PDMA recovery from PSE and another
PCI path; `:2598` calls PSE recovery from the watchdog path. Periodic MLME
dispatch checks PDMA/PSE watchdogs in `common/mlme.c:1799-1814`, and
`common/rtmp_init_inf.c:731-733` enables both watchdogs at startup.
Therefore reset requests can originate outside netdevice RTNL operations.

The isolated candidate's `tools/iot/reset-admission.inc` replaces the
public reset entry points with a request plus `rtnl_trylock` drain and uses
raw PDMA from raw PSE to avoid recursive public admission. Its assembler
also retries pending reset from the periodic command-thread path in
`tools/iot/prepare-radio-queue-candidate.py`. If `rtnl_trylock` fails while
an ndo callback owns RTNL, a pending request blocks later BSS admission;
periodic retry is present but is contingent on timer/worker lifetime. This
is source evidence, not a guarantee of bounded reset completion or proof
that every direct lower-level reset/PM path uses the public wrappers.

Next: audit actual calls to raw lower-level reset/teardown and PM callbacks,
then prove lifetime and pending-reset drain ordering under failure. Do not
insert a blocking wait into `ndo_stop` solely from the earlier hypothetical
main-close race. No production source, image or router state was changed.
