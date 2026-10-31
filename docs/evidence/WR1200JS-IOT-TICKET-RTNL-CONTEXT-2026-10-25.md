# IoT ticket retirement and RTNL context — 2026-10-25

Read-only audit of the isolated MT76x3 v12 candidate. No production binding,
MIPS build or router action.

## Kernel boundary

Upstream [Linux v4.4 `net/core/dev.c`](https://github.com/torvalds/linux/blob/v4.4/net/core/dev.c)
asserts RTNL in `__dev_open` and `__dev_close_many`. It invokes `ndo_open`
under RTNL. It invokes `ndo_stop` under RTNL, ignores its return and clears
`IFF_UP`. A main-close callback cannot use an error return to ask the kernel
to retry, and a wait inside that callback must account for RTNL dependencies.

## Ticket producers in the current isolated candidate

| Ticket | Source/entry | RTNL evidence | Retirement |
| --- | --- | --- | --- |
| Main START/MAIN_OPEN | `os/linux/rt_main_dev.c`: `pNetDevHook->open = MainVirtualIF_open`; v12 calls `wr_iot_main_open_reserve` | Kernel `ndo_open` holds RTNL | Same wrapper finishes ticket and wakes `wr_iot_ticket_wait` |
| Secondary BSS_OPEN | `ap/ap_mbss_inf.c`: `netDevHook.open = MBSS_VirtualIF_Open`; `include/wr-iot-mbss-open-admission.inc` admits it | Kernel `ndo_open` holds RTNL for this hook | Admission/abort paths finish or retire ticket and wake queue |
| RESET | `include/wr-iot-reset-admission.inc`: `wr_iot_radio_reset_drain` | Uses `rtnl_trylock`; if unavailable, leaves `reset_pending` and returns without admitting a ticket | On admitted reset, finishes ticket and wakes queue before `rtnl_unlock` |

The direct source search found no other C caller of `MBSS_VirtualIF_Open` or
`MainVirtualIF_open` in this candidate. This is current-source coverage, not
proof that future or external callback paths obey the same contract. Other
auxiliary family opens remain legacy and do not yet own radio tickets.

## Implementation consequence

Do not insert `wr_iot_wait_ticket_retired` into `MainVirtualIF_close` while
`ndo_stop` owns RTNL. The current admitted reset owns RTNL until retirement;
main/MBSS `ndo_open` also own RTNL. A wait for a future ticket producer that
needs RTNL would deadlock; a timeout only bounds the stall and still leaves
`ndo_stop` administratively down. A busy or unmatched stop must preserve the
main-down intent, registry record and module/adapter pin, and hand completion
to a separately reviewed owner after the callback returns. That owner must
survive command-worker failure, PCI suspend and removal; the existing periodic
reset retry does not prove such liveness (see
`WR1200JS-IOT-562-RESET-RETRY-WORKER-LIVENESS-2026-10-24.md`).

Next source gate: identify every main-close side effect, then design a
nonblocking close admission plus adapter-lifetime-safe recovery scheduler.
Only after all five UP/DOWN families share count ownership can the checked
DOWN and physical readback gate release the main module pin. The host
`wr_iot_main_stop_complete` is an outcome model, not that scheduler.

The host-only `wr_iot_main_stop_request` now distinguishes invalid main
ownership, a busy ticket with its exact serial, an unmatched state requiring
recovery, and an admitted stop ticket. It latches main-down before reporting
either deferred outcome and never blocks under RTNL. A strict C11 fixture
covers all three refusal classes and the admitted path. This classification
does not queue work or pin adapter lifetime; those remain required for the
production deferred owner.
