# Private reload bootstrap to normal admission: unfinished requirements

Source audit 2026-11-07; no admission implementation or runtime acceptance.

`mcu-boot-open.inc` explicitly returns success for a clean cold sender without
reserving private bootstrap. After a claimed close it either refuses under
LOAD_FW_ONE_TIME or reserves bootstrap. The incomplete promotion discussed
here is the private reload/reopen path, not proof that every cold startup
uses this path. Do not conflate the two in status reports.

The following transitions need one reviewed protocol before removing the
final config-init refusal:

| State | Current source | Required evidence before normal admission |
| --- | --- | --- |
| Config owner | config_finish sets state2, drops task reference | All EEPROM/PHY/config effects accounted for; no active/poisoned journals or unconfirmed effects |
| Firmware response IDs | checked IDs retained until ROM boundary | Sustainable ACK correlation for automatic scan and later operation; no host-only reset |
| Sender | closed, release_claimed and off_done retained from close | Explicit authorized reopen matching historical close and current boot ticket; no constructor init that erases uncertainty |
| Software producers | private MCU-only RX/IRQ bootstrap | Joined data consumers safely recreated/rearmed with old producers excluded; distinguish MCU from normal RX/data ownership |
| Radio transition | WR_RADIO_START remains owned during private init | Preserve serial/epoch and existing finish semantics; no main-ready publication before actual successful startup |
| Peer open | peer remains WR_PEER_OPEN_CONFIG | Commit through existing peer-open transaction only after successful normal initialization; unwind must still retain failed ownership |
| Hardware | filtered MCU IRQ/DMA startup | Reviewed normal mask/ring/RX/TX enable order and failure rollback, target and separately authorized runtime evidence |

Lock order is transition then sender for bootstrap state. Peer matching uses
MacTabLock separately. Any new commit must revalidate tickets after unlocked
hardware work, avoid joins/waits under spinlocks, and remain robust against
reset/PM/close racing the final commit. Merely clearing boot_active, calling
sender_init, or deleting the unconditional final refusal would erase gates
without establishing the above facts.

Next implementation is contingent on solving the config transaction budget
and classifying full config/scan completion. Existing source gates stay closed.
Host tests, target modules, final image inclusion and on-device acceptance
remain separate deliverables.

## Existing main-open acceptance must remain unverified first

`prepare-main-open-owner-candidate.py` finishes the existing start/main-open
ticket with `wr_iot_radio_finish_unverified` and checks
`wr_iot_main_open_accepted`. In `radio-transition.h` that acceptance explicitly
requires phase WR_RADIO_UNVERIFIED, no busy ticket and main_ready false, plus
matching epoch/serial and no reset/PM/retirement intent. A successful private
bootstrap must feed this existing outer protocol; it must not publish READY
itself or retire the same radio ticket a second time. The separate
wr_iot_radio_verify_finish path establishes READY only after reviewed readback
and revalidation. Software initialization success alone is not that proof.
