# WR1200JS IoT reopen: current evidence and missing boundary

Status: implementation incomplete. OPEN remains fenced after CLOSE. This is a
separate issue from MT7603 ROM MCU ACK reuse. No firmware ACK protection has
been relaxed. These findings describe vendor source and host fixtures, not
observed late-report delivery on the physical WR1200JS.

The pinned source is vipshmily/padavan-4.4 revision
`c25283e915a2a00a763774dd255b14aff997285e`. Paths below are relative to its
`trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/` directory.

| Boundary | Evidence | What remains unproved |
| --- | --- | --- |
| Beacon producer fenced | Staged producer gate, STOP callback rejection | Hardware may still deliver reports submitted earlier |
| Beacon queue flushed | `hw_ctrl/cmm_asic_mt.c:1332–1394` recovery tail | Original vendor timeout continues/re-enables; staged predecessor already hardens this, but neither is a complete late-TxS CLOSE receipt |
| Current PCI parser joined | `common/cmm_data_pci.c:1712,1836,1993` ring lock spans parser | Future RX entries and firmware-generated reports remain possible |
| Andes queue observed empty | `mcu/andes_core.c:361,453–457` dequeue unlocks before callback | Dequeued callback can still be running |
| Active callback ledger empty | Shared transformed `ParseTxSPacket` ledger | Future duplicate/late PID can still arrive |
| Software generation advanced | Staged TxS reservation metadata | Generation is not returned in on-wire TxS |
| Descriptor/report sequence exists | `TXS_D_4` PID8/SN12; TXD SN12/sn_vld | Beacon submission identity and hardware echo/reuse semantics not established |
| API extra references retired | Staged netdev receipt/module handoff | Does not authorize RF buffer reuse, isolation removal or OPEN |

The actual transformed-source ledger fixture demonstrates that an old report
using a reused PID can consume a new reservation even when its software
generation differs. The actual beacon callback fixture demonstrates that STOP
rejects a report, while the same report can mutate reopened state. These are
negative safety witnesses; they do not establish hardware delivery frequency.

The MT_MAC beacon wrapper (`ap/ap_connect.c:105–135`) sets `NSeq=TRUE`,
`TxSPriv=apidx`, WCID0 and beacon queue index, clears the long descriptor and
calls `write_tmac_info`. That builder does not consume `info->NSeq` or explicitly
assign SN/sn_vld. A wrapper flag is insufficient evidence of a usable cookie.
Active source call sites are `ap/ap_connect.c:512,1699`; line835 is commented
out. Header initialization at295/636 calls `MgtMacHeaderInit`, which clears
the header without assigning a unique Sequence. Hardware sequencing remains
unproven.

A safe reopen implementation needs one of these complete arguments:

1. A hardware-defined per-BSS submission fence and checked flush completion,
   followed by a proven report-delivery boundary and both host callback paths
   joined without discarding Main/Guest traffic or MCU responses.
2. A submission identity actually carried through the beacon TXD/report, checked
   before consuming a reservation or changing beacon state, with demonstrated
   uniqueness across wrap, retry, duplication, timeout and reopen.

Neither argument is currently complete. PID/SN width alone, a software
counter, a fixed delay, an empty software queue, a momentary DMA snapshot or
successful module-reference retirement does not supply the missing evidence.
Do not enlarge pools, disable TxS globally, reset the radio, discard shared RX
or change descriptor/firmware semantics speculatively.

Next source investigation: trace the actual beacon frame Sequence field at all
three submission call sites, hardware override controls, and register semantics
of the per-BSS filter/flush. If source cannot establish the required behavior,
obtain MT7603 E1/E2 documentation or a controlled firmware/report capture under
a separately authorized device test. Such a test must cover duplicate and delayed
reports across PID/SN wrap while Main/Guest remain connected.

Reproduction/evidence (host and source only):

- `tools/iot/check-beacon-txs-stop.py`: actual transformed beacon callback,
  STOP immutability and reopened-state negative witness, default and DBG.
- `tools/iot/prepare-beacon-txs-ledger-check.py`: extracts actual transformed
  allocator/parser/ledger; stale PID misattribution and generation exhaustion.
- `tools/iot/check-beacon-flush-timeout.py`: actual vendor flush tail with
  injected MMIO/waits; success and either/both timeout outcomes.
- `docs/evidence/WR1200JS-IOT-TXS-LEDGER-REUSE-WITNESS-2026-11-08.json`
- `docs/evidence/WR1200JS-IOT-BEACON-FLUSH-TIMEOUT-2026-11-08.json`
- `docs/evidence/WR1200JS-IOT-TXS-CORRELATION-SOURCE-2026-11-08.json`
- `docs/evidence/WR1200JS-IOT-TXS-RX-LOCK-BOUNDARY-2026-11-08.json`

Physical runtime acceptance, current bundle target verification, release image
validation and final port acceptance remain separate outstanding requirements.

The original vendor flush negative witness is distinct from the staged
`prepare-beacon-recovery-check.py` hardening, which already returns on timeout
and checks eligibility under the final restart lock. Revalidation of that
existing fix passes; it still does not supply the report-delivery boundary.

## TxS classifier is not a delivery fence (2026-11-09)

A full pinned vendor C/header search finds the two initialization calls in
`chips/mt7603.c:323–324`, implementation in `hw_ctrl/cmm_asic_mt.c:6652–6687`
and declaration in `include/rtmp_chip.h:1466`. The implementation selects
DMA_TCFR1 for Host or DMA_TCFR0 for MCU and changes the destination queue,
aggregation count and filter bitmap. It has no BSS argument, completion poll,
callback join or returned completion receipt. Register definitions are in
`include/mac/mac_mt/wf_dma.h:49–69`: bitmap bits0–6, aggregation bits8–12,
MCU destination bits14–15 / Host destination bit14. The source does not establish
that this bitmap is a per-BSS filter; do not interpret it as one.

MT7603 initializes both aggregation counts to31. This neither proves a bounded
report delay nor that reducing aggregation drains reports already generated.
Consequently this API cannot supply the missing reopen boundary. No classifier
or aggregation register change was made. Durable source hashes/references:
`docs/evidence/WR1200JS-IOT-TXS-CLASSIFIER-SOURCE-2026-11-09.json`.
