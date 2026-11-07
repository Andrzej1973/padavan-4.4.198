# Pending Method1 bootstrap handoff

Source inspected: isolated candidate generated from repository ae122707.

The checked PCI controller initialization clears
`fRTMP_ADAPTER_MCU_SEND_IN_BAND_CMD`. Both AndesDequeueAndKickOutCmdMsgs
and the send-body path reject commands while that flag is clear. Hardware
preparation ends with constructors frozen and does not set the flag. Therefore
calling hardware preparation from Method1 alone cannot complete downloading.

The next implementation must validate the exact private ticket, completed
hardware stage6/state2, controller/RX/IRQ/DMA ownership, ticket-bound retirement
receipt and empty sender before setting the transport flag and releasing only
the private constructor freeze under transition/sender locks. Normal sender
admission and data tasklet/RX fences must remain closed. Failure must block
IRQ rearm before DMA stop and retain uncertain resources. A firmware start
ACK and RUN readback require separate completion before normal admission.

Method1's generic done path also writes SCH_REG4. Its ordering relative to
bootstrap failure masking/stop must be covered when binding this transition.
The existing active-bootstrap init refusal remains until final promotion is
implemented and verified. This document records source analysis, not an
implemented thaw, firmware epoch guarantee or runtime result.

## Promotion audit after loader binding

Generated dd1a301f lifecycle source has MCUSysInit calling MCU_CTRL_INIT,
FwInit, NICLoadFirmware, then AsicDMASchedulerInit(DMA_SCH_LMAC) before
returning to the active-bootstrap refusal in rtmp_init_inf.c. Thus a receipt
at Method1 return alone cannot authorize normal admission: the scheduler
changes again before the current refusal point. Promotion must account for
this post-loader scheduler operation and its failure/readback contract.

The existing refusal must remain until sender release-claim transfer, data
tasklet activation, interrupt-mask expansion and radio START completion are
implemented together. Clearing boot_active alone would expose generic RX/ISR
paths while normal sender ownership remains closed. No promotion was enabled
by this source audit.

Scheduler source detail: hw_ctrl/cmm_asic_mt.c AsicDMASchedulerInit returns
INT32, but MCUSysInit currently ignores its return. It reads MCU_PCIE_REMAP_2,
maps MT_PSE_BASE_ADDR, extracts page count from register0x80120 and restores
the remap; no all-ones validation precedes that extraction. The checked
bootstrap scheduler path must validate saved remap/quota observations and
restore mapping on failure before publishing any receipt. LMAC mode writes
MT_SCH_REG_4=0; effective CONFIG_FPGA_MODE can override the requested mode.
Do not assume the call argument alone proves final LMAC configuration.

The function ends with return TRUE (not NDIS_STATUS_SUCCESS). Its MT7603 E1+
tail writes all16 MT_TXTIME_THD registers to0xfffff and ORs0x40 into
MT_SCH_REG_4 after the earlier LMAC write0. A checked wrapper must preserve
that revision-specific tail and use the correct TRUE-success convention;
requiring final SCH_REG_4==0 would incorrectly reject this SDK path. Derive
expected final bits from exact silicon revision and effective build guards.

Remap serialization investigation: scheduler and AsicGetTemperatureSensor
both directly save/write/restore MCU_PCIE_REMAP_2 in cmm_asic_mt.c. Searching
the generated driver for remap_lock/RemapLock or lock/remap naming found no
dedicated lock. This does not prove serialization is absent elsewhere. Before
adding a lock, audit RTMP_IO macros and MCU/data callback admission, especially
temperature readers; a new wrapper-only lock would not serialize existing
unmodified remap consumers. The draft scheduler must remain unbound meanwhile.

Expanded direct-remap inventory includes common/{ee_efuse,cmm_data_pci,
cmm_mac_pci}.c, hw_ctrl/{mt_gpio,cmm_asic_mt}.c, chips/{mt7603,mt7628,
mt7636}.c, ate/{mt_mac/mt_ate,qa_agent}.c and mac/mt_mac.c. In particular,
cmm_mac_pci.c uses remap in TX-abort/PSE diagnostic/reset sequences. Determine
effective MT7603 build guards and producer ownership for these callers before
choosing shared locking versus an exclusive startup phase. Do not wrap the
entire diagnostic loops in a newly invented spinlock without duration review.

Quota constants in this exact SDK: MAX_BEACON_SIZE512 (rtmp_def.h),
MAX_MCUCMD_SIZE4096, MAX_DATA_SIZE1792, MAX_AMSDU_DATA_SIZE4096,
MAX_BMCAST_SIZE1536 and MAX_BMCAST_COUNT3 (cmm_asic_mt.c). At128-byte pages,
MCU reservation is32, data14 or AMSDU32; beacon reservation is data plus
4*(BssidNum-1) for AP BssidNum>1. At256-byte FPGA pages derive again from the
same constants. The single-group E1 path differs from E2 grouped subtraction.
The local quota helper is not installed; its strict positive group0 policy
still needs confirmation against actual board quotas and effective config.
