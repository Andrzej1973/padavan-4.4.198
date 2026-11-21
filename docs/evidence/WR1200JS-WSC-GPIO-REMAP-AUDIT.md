# WSC GPIO and remap aliases — 2026-11-06

Source chain traced in the isolated candidate:

`MlmePeriodicExec` → `WSC_HDR_BTN_MR_HANDLE` → `WSC_HDR_BTN_CheckHandler`
→ `WSC_HDR_BTN_MR_PRESS_FLG_GET` → `GPIOGetValue`.

The identified button poll therefore runs inside the new MLME control reference.
WSC_HDR_BTN_Init/Stop only reset a counter; they do not create a separate button
timer. Symbol searches found no additional C/header GPIOGetValue consumers
outside its definition/prototype and the WSC macro. This is a source finding,
not a claim about all GPIO functions or binary/runtime behavior.

Fresh candidate generation and `check-mcu-wsc-gpio-path.py` passed ASan/UBSan:
the actual header GPIO macro behind the generated MLME wrapper reads each pin
only when admitted; denied calls perform zero GPIO reads. Admission and GPIO
are injected; source assertions check the intermediate WSC call chain. The
fixture is now included in peer82 CI. Temporary candidate/executable scratch
(~14MB) was automatically removed. No target/runtime result yet.

MCU_CFG_BASE is 0x2000 and MCU_PCIE_REMAP_2 adds 0x504. The numerical alias 0x2504
occurs in common/mt_ps.c:MtTriggerMCUINT (save/map/restore). The sole identified
call in MtStartPSRetrieve is commented out. Do not infer general exclusion from
that comment: retain it in the inventory and recheck callers before binding.
The auditor now derives this address from the header and inventories matching
hex literals too: 115 references in 12 C files in the recorded candidate. Small
temporary fixtures passed symbol/numeric/padded/case matching, exclusion of
adjacent 0x25040, and refusal of source drift against the manifest.

Initialization ordering traced: rtmp_init_inf calls MCUSysInit before
RtmpChipOpsEepromHook and NICInitializeAdapter; the latter reaches mt_mac_init,
then mt_mac_pse_init and AsicMacInit/mt7603_init_mac_cr. These particular
synchronous calls follow the proposed scheduler placement, but EFUSE hook
replacement, ATE and other initialization/reset callers still need review.
The scheduler and normal admission remain unbound.
