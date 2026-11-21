# IoT main-stop contract: Linux 4.4 ndo_stop and RTNL

Read-only source audit on 2026-10-25. No router operation or target build.

## Kernel contract

In upstream [Linux v4.4 `net/core/dev.c`](https://github.com/torvalds/linux/blob/v4.4/net/core/dev.c), `__dev_open` asserts RTNL and returns the `ndo_open` result. `__dev_close_many` also asserts RTNL, calls `ndo_stop` without using its return value, then clears `IFF_UP` and returns zero. The nearby kernel comment states that device close cannot fail. This means a negative return from Padavan `MainVirtualIF_close` cannot keep the interface administratively up or cause an automatic retry.

The isolated MT76x3 candidate in `.iot-local-check/main-open-owner-v12-20261025` still calls `RTMPInfClose`, then void `VIRTUAL_IF_DOWN`, then releases the module pin. The common DOWN dispatcher decrements `VirtualIfCnt` before the physical close and discards the physical result. The checked DOWN helper exists separately but is not bound to this wrapper.

## Consequences for the candidate

1. Main-close intent must be latched under the shared adapter lock before waiting for an admitted ticket or trusting a reference-count match. The host `wr_iot_main_stop_owned` now does this after confirming an owned main record.
2. A failed or unverified last-reference close must keep its registry record in `CLOSING` and keep the module pin. A software close result alone does not prove RF/DMA quiescence. The host `wr_iot_main_stop_complete` requires checked DOWN and physical verification for last-reference pin release; a selective close requires checked DOWN.
3. `ndo_stop` runs under RTNL. A direct ticket wait inside `MainVirtualIF_close` needs a call-chain proof that the ticket can retire without acquiring RTNL. A timeout limits the stall but does not make a dependency cycle safe.
4. No production binding is justified yet: all five family UP/DOWN count writers, ticket retirement/wakeup, physical close readback and an explicit recovery owner must be completed together. An ignored `ndo_stop` return cannot serve as recovery.

Verification: strict C11 `check-main-stop-owned.c` and `check-radio-transition.c` passed; `git diff --check` passed on the touched model files. This is source/host evidence, not a MIPS build or device acceptance.
