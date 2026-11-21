# WR1200JS IoT: evidence required to unblock integration

Checkpoint: 2026-11-10. IoT and the full port are **not completed**.
Current implementation work is blocked on the contracts below, not on another
compiler invocation. Standard971 and optional972 succeeded for66241da;
ABI749 succeeded for5a3caac. Prototype42b8c74 is an offline experiment and is
not installed in firmware. No branch CI run remained active at this checkpoint.

## Missing contracts

| Boundary | Evidence needed | Why current evidence is insufficient |
| --- | --- | --- |
| MCU ACK sequence reuse | For MT7603 E1/E2: reply cardinality/lifetime, or an acknowledged reset/epoch boundary which invalidates every old result before reuse | The four-bit sequence can repeat; a software generation is not echoed. Occupied-slot cleanup, queue snapshots and FW-already-running paths do not establish a new ROM epoch. |
| Per-ra2 queue preparation and stop | Meaning of BCN/BMC/AC flush completion for accepted and in-flight work; ordering against transmission and future status delivery; Main/Guest preservation | BUSY polling documents a register operation, not the complete RF/report boundary. Existing AsicWaitMacTxRxIdle simply returns TRUE. Global CAB flush/radio recovery is outside ordinary scoped toggling. |
| Transition from tracked ra2 reports | A proven initial epoch with no historic non-owning-mode predecessor reports, or retirement of all old tracked non255 ra2 reports | The actual parser fixture shows an injected old non255 report consuming a newer Main reservation. Ignoring255 protects only255; table reinitialization cannot erase hardware history. |

Obtain the relevant vendor specification, source for the invoked ROM routines,
or a reproducible firmware/hardware investigation that establishes these
semantics for the exact silicon/firmware revision. Firmware initializer hashes
and partial disassembly of calls into unavailable ROM are not that contract.
A finite stress run can expose a failure and support regression confidence;
it cannot alone prove an unbounded no-late-response guarantee.

## Implemented and verified without those assumptions

- Checked tracked reservation admission: zero-token ra2 is refused before HAL
  and host-publication confirmation; final-source host test and actual MIPS
  baseline/reload/WSC modules passed in972.
- RC recovery retains normal-shutdown admission; configuration/bridge absence
  cannot replace the strong controller. Actual target objects were inspected.
- The isolated PID255 allocator/parser and selected long-TXD branch pass host
  property tests and conditional negative witnesses. They do not enable a
  submit mode, DMA pacing or RF acceptance.
- Existing producer pin and checked zero-DMA-cell observation support the
  host-buffer ownership boundary. They are not a complete OFF receipt.

## Dependencies which cannot yet be closed

The strong RC activation/stop backend must not report success without its
driver ownership/quiescence contract. It remains unbound. Production network,
DHCP/DNS, firewall and WebUI integration therefore remains incomplete despite
individual candidate objects and host checks. No weak success implementation,
bare DMA_DONE-to-IDLE change or arbitrary grace period may satisfy this gate.

Modern WebUI/Zapret2 review, final TRX/ROMFS/release verification and physical
acceptance remain in the original goal and order. This checkpoint does not
remove those requirements or mark the smaller experimental scope complete.
Device diagnostics, configuration changes and flashing still require the
owner's separate authorization; none was performed here.

## Resume procedure

1. Inspect the supplied contract/source evidence and exact firmware/silicon
   identity. Implement the smallest correction justified by it.
2. Recheck old/non-owning TxS transitions, queue timeouts and generation races,
   ordinary Main/Guest paths and MCU stale-response protection.
3. Build the affected exact source and inspect target/image artifacts. Do not
   repeat already successful runs to manufacture protocol evidence.
4. Complete RC/network/WebUI integration, then separately authorized device
   tests and remaining release stages. Build success is not runtime acceptance.

References: [verification matrix](WR1200JS-IOT-VERIFICATION-MATRIX-2026-11-09.md),
[reopen gap](WR1200JS-IOT-REOPEN-EVIDENCE-GAP.md),
[prototype and witnesses](WR1200JS-IOT-NOOWNER-PID-PROTOTYPE.md),
[972 target evidence](evidence/WR1200JS-IOT-OPTIONAL972-TRACKED-TOKEN-TARGET-2026-11-10.json).

Scratch cleanup checked: downloaded ZIP/modules were inspected in memory;
there is no new extracted firmware/build tree to remove. Source, compact
evidence, the original vendor archive and unrelated unfinished work are kept.
