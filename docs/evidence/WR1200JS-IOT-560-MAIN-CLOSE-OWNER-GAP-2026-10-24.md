# IoT transition owner: main close still mutates outside the ticket

After the successful isolated MIPS build `40080616642`, source inspection
found a remaining all-mutator gap in the same candidate. This is a source
finding, not a reproduced device race.

`tools/iot/mbss-open-admission.inc` now reserves a `WR_RADIO_BSS_OPEN`
ticket, observes the main MT7603 configuration outside the short lock, then
rechecks epoch, serial, main readiness and close/reset intent before raw open.
Its ticket prevents **participating** transitions from entering concurrently.

`tools/iot/prepare-radio-adapter-candidate.py` currently inserts
`wr_iot_radio_main_down()` near the start of `MainVirtualIF_close`. That
invalidates the epoch and clears `main_ready`, and the host fixture checks
that it happens before the first main-close mutation. But the generated main
close wrapper does not acquire a `WR_RADIO_CLOSE` or other exclusive ticket,
does not wait for a previously admitted BSS-open owner to retire, and then
continues its `RTMPInfClose` / `VIRTUAL_IF_DOWN` path. This is an uncovered
transition-owner relationship, but **not** evidence that normal netdevice
open and stop race: the pinned `ap/ap_mbss_inf.c:79-80` attaches
`MBSS_VirtualIF_Open/Close` as netdevice hooks, while pinned
`os/linux/rt_linux.c:1676-1677` maps these hooks to `ndo_open/ndo_stop`.
The main hooks use the same mapping. Normal netdevice operations are
serialized under RTNL, so the earlier hypothetical overlap between those
two `ndo` callbacks was stated too broadly. Before changing main close,
inventory direct calls and PM/watchdog/error paths that might enter outside
RTNL or mutate the adapter while an admitted BSS ticket is active. Reset
uses the ticket-aware wrapper in
`tools/iot/reset-admission.inc`, but its coverage of all direct reset and
PM/watchdog callers still requires audit.

The next gate is to map every entry to main close, reset and teardown, and
record whether RTNL or the transition ticket serializes it. For a confirmed
path outside both owners, add a safe admission/deferred-close protocol that
preserves mandatory ndo_stop cleanup and pinned references; do not insert a
blind wait under RTNL or the short lock. Exercise only confirmed reachable
interleavings and compile the assembled target driver. The host fixture and
green MIPS link do not prove complete lifecycle exclusion.

No production driver, firmware image or router state was changed here.
