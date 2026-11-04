# Isolated firmware reload verification

Added peer82 reload feature compile after the full WSC feature. Separate CI
kernel copy; pinned wrapper SHA256 4c51b2a7a474c1e081a369562ca8ce28a80e0485a675723335b3106a347141c5
has exactly two LOAD_FW_ONE_TIME flags removed. Baseline and .config unchanged.
Requires complete MIPS module, non-refusal checked-off symbol and effective
reload macros in actual rt_linux, RX, MCU and ASIC translation units, with
source hashes matched to candidate inventory. Report explicitly keeps epoch,
shutdown, production and runtime false. Phase tree removed on exit.
Host checks passed actual MCU/ASIC source selection and wrong-TU rejection,
pinned wrapper preparation, failed-build cleanup and baseline preservation.
These tests use host fixtures, not target compilation. Full target run due.
Source audit confirms MT7603 DownLoadTypeA/Method1. Restart callback status
cannot be routed by blindly enabling radio-only checked mode: it uses a
header status byte/MT_RESTART_DL_RSP and currently allows retransmission.
A separately bounded checked restart path and RX/DMA/IRQ epoch proof remain.
No router action, no new local build trees retained. Keep owner references.

## 2026-11-04 Sol: same-adapter reopen boundary located

Current 4088744 worktree unchanged except owner references before this note.
Optional744/41868468440 is compiling its isolated candidate on a1f7d6d;
standard745/41870986761 on 4088744 remains active; ABI659/41870986771
succeeded at the final live check.
Do not dispatch duplicates or treat 744 as verification of the newer close order.
Source audit of the full-chain input confirms RTMPAllocAdapterBlock is called
at PCI probe (pci_main_dev.c:330), while rt28xx_open reuses pAd, requests IRQ
and calls rt28xx_init (rt_main_dev.c:757-768). MCU-owner init is in adapter
allocation only (rtmp_init.c:290). MCUSysInit initializes controller state,
enables MT FwInit, then calls NICLoadFirmware (mcu.c:48-65).
Consequently terminal construction/reinitialization claims cannot be cleared
merely because ifup is requested: same-adapter reopen requires an explicit
new firmware/RX/ring epoch and correctly staged initialization. No such claim
reset or MCU sequence quarantine reset was implemented in this audit.

Pinned upstream comparison: OpenWrt mt76 commit
0936617dc529ff9da0385221d3fa6de732231177. GitHub API blob contents independently
matched Git blob IDs. mac.c blob fa0bf9a201ce2d43b48981aab75b70ff21ff5c51,
SHA256 2ddca5b165e98034a1bf5cd185b62f9af805d5cf970e79a54b1bff912397995a;
mcu.c blob b231fb2d3752ff06a8c728d9ebf79450888f3af7,
SHA256 ee943c834bb8341d452eb69efc71bc36fbd64cbbddbd0894c73e83396477b7f5.
Watchdog recovery uses worker/NAPI exclusion, queue/RX reset and MAC/DMA
restart; MCU exit sends restart-download and purges its response queue.
Inference: that different transport/lifetime sequence is not a vendor firmware
epoch receipt and cannot justify resetting our claims or importing snippets.
No upstream code installed, no runtime/router access, no new scratch output.
Next design and verify same-adapter reopen across the actual MCU/RX boundary,
while awaiting target evidence for the already published close package.

Primary comparison sources:

- https://github.com/openwrt/mt76/blob/0936617dc529ff9da0385221d3fa6de732231177/mt7603/mac.c
- https://github.com/openwrt/mt76/blob/0936617dc529ff9da0385221d3fa6de732231177/mt7603/mcu.c
