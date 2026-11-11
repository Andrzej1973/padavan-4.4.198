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
