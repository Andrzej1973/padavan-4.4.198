# WR1200JS ra2 software recovery

Owner selected the software timeout/queue-ownership path on2026-11-12.
Implementation uses the pinned mt76x3 SDK and existing per-station state.

## PS-Poll and delayed TxS

`ra2-ps-retain.h` validates current MAC/TR WCID, BSS index and both wdev
pointers. The ra2 PS-data callback preserves queued-data TIM indication and
leaves PsDeQWaitCnt to the existing AP station-maintenance timeout.
A delayed or repeated callback therefore cannot acknowledge a newer ra2 poll.

The three existing PS-data PID selection sites in `ap/ap_data.c`,
`common/cmm_data.c` and `common/cmm_data_pci.c` retain the ordinary packet PID
for validated ra2 stations. Main/Guest retain their PS-data completion path.
The existing packet-type overrides, including WSC, remain in their normal
order. Normal TxS parsing continues consuming delivered status records.

The SDK timeout advances PsDeQWaitCnt from1 to2 and then0 on two periodic
maintenance passes. This deliberately trades immediate completion-driven
PS-Poll pacing for bounded software pacing. A continuously sleeping client
using PS-Poll can experience increased delivery latency. Active/wake handling
keeps its existing SDK behavior. Physical tests must measure that tradeoff.

## Software OFF and reopen

The MBSS close hook stops ra2 software admission before native station removal.
It closes the beacon-send request under BcnRingLock, then gates matching TR
enqueue/dequeue capabilities under the existing table/IRQ locks and clears
their PS wait/idle counters. Beacon and table locks are acquired separately.
The multicast software queue uses the existing per-WCID `rtmp_tx_swq_exit`.
The WCID_ALL sentinel and values outside the queue API width are rejected.
Invalid multicast ownership retains closed admission and returns a close
error for the existing recovery path.
Native `MbssKickOutStas -> MacTableDeleteEntry -> tr_tb_reset_entry` owns
unicast software queue cleanup and station removal. Hardware-owned packets
continue through normal TX DMA completion and skb release.

The TX admission check rejects data for the closed ra2 BSS. Existing candidate
association/RX admission checks use the same beacon/netdevice state. Reopen
restores the validated multicast TR capabilities before BcnRingLock is taken
and before the vendor beacon-enable publication. Newly associated clients use
the SDK table initializer. Prepared MBSS open rollback gates the restored
capabilities again before beacon revoke/drain. Main/Guest entries retain
their state.

With WR_IOT_PSM_DIAG, a rate-limited `mt76x3: ra2 software-off queues-gated`
marker follows queue gating outside the table/IRQ locks. It records that
software phase. The existing read-only iot-baseline collector includes this
marker alongside bounded wr_ps observations.

Control helper work consists of a bounded TR-table traversal and existing
software queue cleanup. Vendor MBSS close, checked lifecycle recovery, native
DMA reclamation and their scheduling remain part of the full transaction.

## Verification and integration

Host ASan/UBSan tests execute the prepared PS-data PID decisions at all three
sites, delivered/repeated TxS handling, the actual SDK periodic timeout,
software OFF/admission/reopen, invalid ownership and Main/Guest preservation.
SDK locks and queue release are injected in the control-helper fixture.
The prepared-driver CI also executes these checks before module compilation.

This implementation is composed into the isolated peer82 driver candidate.
Optional1038/run43156619976 for b4d73312002e708a85311c1b33903d215a012ec4
passed target compilation on Ubuntu24.04. Independent artifact checks cover
five ELF32 little-endian MIPS modules, module/report hashes, diagnostic
ON/OFF markers and saved compiler-command/object provenance. Prepared-driver
ASan/UBSan fixtures passed in both diagnostic modes. Evidence is recorded in
`../evidence/WR1200JS-IOT-OPTIONAL1038-TARGET-2026-11-12.json`.
Standard1037 separately passed actual image CRC/product/size/MIPS/HNAT checks.
Production RC/controller binding and physical runtime acceptance remain
unfinished. The existing checked close/recovery still tracks beacon DMA/TxS and resource ownership.
The new software stop hook establishes queue/admission state within that path.

Runtime acceptance requires repeated ra2 ON/OFF with Main/Guest traffic,
PS-Poll latency measurements, pending traffic at OFF, DHCP/DNS/firewall checks,
DMA completion accounting, and inspection of recovery outcomes. Device-side
operations require separate owner authorization.

## CLOSE transport continuation

The next isolated candidate connects existing Linux operations10 and13 to the
common 0x89fd private ioctl. RTNL, namespace CAP_NET_ADMIN, MT7603 and fixed64
user copy precede dispatch. A locked exact-three-BSS/current-ra2 check rejects
Main/Guest and changed interface topology. The existing CLOSE decoder and
owner reservation revalidate the original OPEN nonce, epoch, generation and
token before dev_close. Progress accepts an administratively DOWN ra2 and
advances only the matching retained operation.

The RC client sends each request once to fixed ra2 using a CLOEXEC socket.
Invalid input/socket creation failure reports NOT_SUBMITTED. Any ambiguous
submitted CLOSE or descriptor-close failure reports UNCERTAIN. Progress
EAGAIN/EINPROGRESS reports PENDING for a later explicit controller invocation.
A successful syscall reports CALL_COMPLETED. The controller must retain its
identity and isolation ownership through the subsequent lifecycle checks.

Host fixtures execute both generated routes with the actual CLOSE/progress
reply functions and injected executor/syscalls. The existing58 standalone
fixtures and RC source preparation/client compilation pass. MIPS verification
of this transport continuation is pending. Full controller activation and
owner release/reopen integration remain unfinished.
