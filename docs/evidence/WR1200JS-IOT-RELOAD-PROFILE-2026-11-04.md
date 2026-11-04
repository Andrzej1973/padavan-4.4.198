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
