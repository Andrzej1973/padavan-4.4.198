# WR1200JS ra2 PSM queue retention

The SDK implementation uses MAC_TABLE_ENTRY.func_tb_idx and an exact wdev
pointer to MBSSID[2] to identify the reserved ra2 BSS. The policy additionally
requires MT7603, three configured BSSs, an existing BSS netdevice and beacon-send request, matching WCID
records, an associated client, sleeping MAC/TR records, queued traffic, a valid
TIM AID and a live StaIdleTimeout interval. It allocates no new per-peer state.

The relevant vendor paths are ap/ap.c station maintenance, tx_rx/txs.c
PsDataTxSHandler and ap/ap_connect.c APUpdateBeaconFrame. The existing periodic
builder reads MBSSID[2].TimBitmaps. Queue aging after PsQIdleCount exceeds2
calls rtmp_tx_swq_exit for the particular station. PsDataTxSHandler clears
PsDeQWaitCnt. ContinueTxFailCnt-based deauthentication already excludes sleeping
stations in the vendor maintenance path.

The localized candidate bypasses that queue-aging flush while the ra2 predicate
matches. It resets the existing idle counter and sets the live TIM bit. The
completion handler sets the same bit when queued sleeping-client traffic is
present, then follows its existing PsDeQWaitCnt accounting. The periodic beacon
updater advertises the live bitmap through its normal TIM serialization. Normal
wake/PS-Poll dequeue and association removal continue owning the buffered data.
The policy expires with the existing station idle deadline. Existing enqueue
limits continue bounding the queue.

PsDataTxSHandler receives a TxS report and Priv, with no packet pointer or
explicit timeout reason. PsDeQWaitCnt is also reset by ordinary maintenance.
Consequently this policy retains queued traffic for qualifying sleeping ra2
clients across completion delays generally. It cannot distinguish only a late
TxS timeout from other causes of queued traffic using these existing fields.
This interpretation is broader than a filter triggered exclusively by timeout.
The patch supplies neither MCU ACK correlation nor a BSS RF retirement receipt.

The code is composed into the isolated peer82 candidate by prepare-driver-api.py.
The helper reads existing SDK state and retains no pointer beyond its invocation.
It checks the stored netdevice pointer without dereferencing its lifetime.
Queue and station access use the surrounding SDK maintenance/callback context.
Full concurrent runtime behavior requires target/device verification.

Host verification extracts the actual patched maintenance block and actual
PsDataTxSHandler, exercising21 conditions with GCC -O2 warnings-as-errors and
ASan/UBSan. It checks queue preservation, TIM marking, completion accounting,
Main/Guest and foreign wdev rejection, idle expiry, AID bounds, WCID mismatch,
empty queues and wake state. Additional boundaries reject null adapters, out-of-range
WCIDs, zero AID and a missing netdevice. Both APPS_RETRIEVE_DONE and
APPS_RETRIEVE_IDLE retain qualified data. A sleep/wake/re-sleep/idle-expiry
sequence confirms that expiry resumes the original queue flush. Active-station
maintenance clears the idle counter without flushing, matching the vendor code.
Source composition rejects repeated preparation.
The peer82 workflow runs this test on its final prepared source before compiling
the entire module and diagnostic variants.

Runtime verification should correlate a known ESP client with its WCID, enter
modem sleep with queued traffic, observe TIM and successful delivery on wake,
repeat across both retrieval states, and inspect queue bounds and station idle
expiry. Verify Main/Guest traffic during the same test. Device operations need
the owner's separate authorization under the current project rules.

Target checkpoint: Ubuntu22 optional1018/run43058250743 at4f80200 completed.
Actual artifact13873798948 contains the baseline MIPS module5910000B,
SHA256 dc8c0d4abf84ac7a5138dc2bcf05176ea9c5cae8b9ec58c870d6ab8b69f7f04e,
and four diagnostic/feature variants with matching report hashes. Generated
helper SHA256 matches this source; prepared ap.c hash matches the compiled
startup source report. The21-case retention fixture and joined periodic/first
beacon fixture passed against prepared sources. This is isolated target-build
evidence, not production installation or proof of concurrent station runtime.
See ../evidence/WR1200JS-IOT-OPTIONAL1018-TARGET-2026-11-11.json. ROM ACK and
safe RF/late-TxS retirement issues remain separate unresolved requirements.

## Delivered lifetime-error telemetry — 2026-11-11

The PS-data callback is registered for PID_PS_DATA/TXS_FORMAT0 in vendor
`tx_rx/txs.c:325-327`. Its supplied report contains WCID and the LE error bit.
The current ra2 predicate and live queued traffic must pass before event6 is
recorded after setting TIM. x records PsQIdleCount and y records enqCount.
With WR_IOT_PSM_DIAG enabled, the rate-limited marker contains
`mt76x3: ra2 txs-le TIM-retained current-association`. Current WCID state can be
observed after WCID reuse, so this marker establishes host TIM retention for
that current association only. ESP device identification requires independent
station identity evidence. NULL adapter/report inputs return before decoding.

The DMA path in vendor `common/cmm_data_pci.c:883-915,1063-1092` chooses a shared
TX queue, advances between TxSwFreeIdx and the hardware TxDmaIdx, unmaps the
packet DMA mapping and releases the packet. `PsDataTxSHandler:129-145` receives
Data and Priv without a packet pointer or ring-cell ownership token. Its
existing action clears PsDeQWaitCnt. An arbitrary WCID-based ring-cell release
can free hardware-owned memory or affect a reused cell. Requeueing a packet
already released by DMA completion requires a separately owned retained copy
and correlation protocol. Those mechanisms remain unimplemented.

The scoped PS queue retention already preserves live queued packets for the
normal wake/PS-Poll path and periodic TIM serialization. Reset/deauth suppression
in this callback has no matching reset/deauth call to intercept. Vendor
`ap/ap.c:2251-2259` already excludes PWR_SAVE from ContinueTxFailCnt eviction.
Safe OFF/reopen, RF retirement and late-report lifetime synchronization remain
unverified. A printk observes execution of the host branch. Acceptance requires
independent completion/isolation and Main/Guest runtime evidence.

The exact incremental C diff is
`../evidence/WR1200JS-RA2-TXS-LE-DIAGNOSTICS.patch`, based on prepared peer82
and its diagnostic header at source0705458. Apply via the repository generators
for builds. The exported diff supports source review and applies to that
prepared base. ASan/UBSan host tests cover diagnostic OFF/ON, LE/non-LE,
NULL inputs, Main/Guest and invalid station states. Target verification for
this new change is pending.
