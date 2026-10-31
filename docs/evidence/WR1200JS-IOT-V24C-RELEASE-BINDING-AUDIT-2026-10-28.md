# IoT v24c PCI release binding audit — 2026-10-28

This is a source-only review of the isolated
`.iot-local-check/mt7603-pci-recovery-drain-v24c-20261028` candidate. No
production driver, image or router was changed.

The candidate defines `wr_iot_children` in `include/rtmp.h:5175` and only
initializes it in `common/rtmp_init.c:192`. No vendor C caller invokes
`wr_child_teardown_begin`, `wr_child_teardown_close_done` or
`wr_child_teardown_complete`. The host contract therefore cannot prove that
AP-client, WDS, MBSS and monitor callbacks and netdev references are gone.

`pci-retirement-owner.h` defines the ordered receipts `work_joined`,
`children_done`, `main_detached`, `final_work_joined` and `claim_release`, but
the candidate `rt_pci_remove` calls none of them. It still calls
`RtmpRaDevCtrlExit(pAd)` at `os/linux/pci_main_dev.c:564` after local guards.
Those guards do not establish the full `wr_iot_adapter_release_gate` inputs:
registry slots, in-flight registration, callback quiescence and physical
quiescence. A PCI transaction observation alone is not DMA proof.

The next implementation step is to bind **actual checked child-family
completion receipts** to the shared adapter lock, with exact active-family
membership and callback/reference proof, then bind the PCI retirement
receipts before adapter free. A failed child removal and an exhausted main
recovery owner still need a lifetime owner that can finish after the one-shot
`void` PCI remove callback. Do not mark the release gate bound merely by
calling a host predicate with asserted booleans.

Evidence method: bounded `rg` of `wr_iot_children`, all PCI retirement
receipt callers and `RtmpRaDevCtrlExit(pAd)` across the 69-file candidate;
review of `RtmpPhyNetDevExit` child removal calls. No target compile or
runtime test in this audit.
