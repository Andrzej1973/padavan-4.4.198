# Checked command-ID budget before configuration lifecycle binding

Audited source after `60421c08f5b2a74bf6344ce457e202d8e7a3b31f` and before
any production activation. The MCU checked-sequence ledger accepts IDs 1..15.
Every checked reservation is permanently placed in `retired` at first
allocation, including an allocation that later fails before send. Destruction
releases only its live lease. Timeout also adds quarantine. No ordinary config
success, task completion, host counter or controller recreation may recycle it.

`wr_iot_mcu_boot_retired_boundary` is the only reviewed source transition that
clears `retired`. Before it does so, it requires frozen verified context, ROM
and ring stages, controllers/RX/IRQ/DMA inactive, sender drained, no occupied
or poisoned/quarantined ID, matching radio receipt and empty PSE. It records
the retired mask and radio serial/epoch before clearing. The implementation is
source/host evidence; its silicon/RX epoch proof remains unverified.

Configuration checked commands now include multi-register write/read, channel,
TX-power and EFUSE. EDCA and slot-time consume no checked ID because SDK gives
no response; they instead retain independent unresolved intent. The exact
effective count depends on EEPROM, AP/scan and firmware branch paths and is not
yet bound to a production configuration owner. Therefore success must either
prove the whole path remains within 15 unique checked commands or establish a
new verified boundary before another checked command. Exhaustion is correctly a
failure, not a reason to reset the ledger.

Host fixtures already demonstrate no old successful ACK across thirty attempted
allocations, exhaustion without reuse, timeout quarantine and the negative
control where a host-only reset falsely accepts an old ACK. These tests do not
prove real firmware epochs, target image inclusion or device behavior.
