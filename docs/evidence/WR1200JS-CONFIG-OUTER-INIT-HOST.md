# Configuration owner in outer init — host/source evidence

The isolated `mcu-config-init-owner` layer binds the task-pinned configuration
owner into `rt28xx_init()` only after a successful `MCUSysInit()`. It snapshots
the boot ticket, calls `wr_iot_mcu_boot_config_begin()`, and routes every
subsequent `err6` path through `wr_iot_mcu_boot_config_finish(..., 0)` before
`MCUSysExit()`.

At the normal end of the function it attempts the matching success finish, but
then deliberately takes `err8`: normal command/data admission remains closed.
This does not open the IoT bootstrap gate or claim that a no-response timing
command completed. If EDCA/slot-time intent is still active, success finish
refuses and the same cleanup path is used.

A fresh isolated candidate was regenerated from the retained baseline through
all layers through `mcu-config-timing` and this new layer. The existing owner
ASan/UBSan fixture passed, including retained-ID refusal, and the new source
ordering check passed: begin follows `MCUSysInit`, every later error reaches
abandon, and success cannot reach normal admission. This is host/source
evidence only; no target compilation, ROMFS/image, firmware runtime, or router
operation occurred. The temporary candidate was automatically removed.
