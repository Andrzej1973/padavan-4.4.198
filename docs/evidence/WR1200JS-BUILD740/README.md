# Optional 740: isolated target verification

Run 41852046446 succeeded on exact requested/verified source
61a31856ac4c2f744d1c064d3ffa6927da30e117. Source artifact 13334803314;
IoT driver artifact 13335759478. Independently checked module hashes/MIPS ELF,
actual preprocessor WSC/AP/V2/KTHREAD definitions, defined nonempty WscInit,
WscStop and MBSS handoff functions, baseline-report binding and config hash.
Baseline module 5574520 bytes SHA256
2a801ad25e9dfabe68e59d25f842d7d45546dad8f0ccc5c59f04f551601763df.
Complete isolated WSC module 6183900 bytes SHA256
528eb132b7f2f1d36d0907ff553f1f87e2b010af1cec89899505e77450b749ae.
Report includes six WSC/crypto object hashes and three prepared source hashes.
Compact original reports retained in docs/evidence/WR1200JS-BUILD740 (14890
bytes); remote ZIP/modules read in memory, no local scratch retained or removed
(0 bytes disk reclaimed). Existing unfinished input trees and owner material
remain necessary/preserved. No router access. Standard 739 / ABI also success.

This closes full WSC target compilation for this isolated candidate only.
Baseline and WSC still use LOAD_FW_ONE_TIME; checked radio-off remains the
refusal-sized function in that mode. Reload ASIC TU compiled (1096-byte checked
function), but full reload module, restart response validation, actual firmware
epoch/RX-DMA-IRQ retirement, per-BSS recovery RECONCILE and ordinary callback
binding remain open. Do not install the isolated module or clear quarantine.
Next review full reload configuration and remaining shutdown/recovery contract;
Modern WebUI/Zapret2, final production IoT image and device acceptance remain due.
